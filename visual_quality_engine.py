"""V2.1 — VISUAL QUALITY ENGINE.

Mejora la calidad VISUAL y NARRATIVA de TODOS los videos futuros (9:16 y 16:9)
con reglas GENERALES y reutilizables. NO soluciona un video específico, NO
hardcodea un tema, NO hace correcciones escena por escena.

Principios de diseño:
- Determinismo: las reglas de composición, anti-slop, mismatch y control de
  regeneración son PURAS (sin red/API) → tests deterministas.
- Visión opcional e inyectable: el QA visual real (visual_critic / ver_imagen)
  se conecta como `critic_fn`; si no se provee, el scoring cae a reglas.
- NO toca el renderer legacy: este módulo se REUSA, se envuelve. El pipeline
  existente queda intacto (regla V2 PASO 10).

Dimensiones del VisualQualityScore (concepto, general):
  composition, framing, subject_visibility, text_space, human_realism,
  skin_realism, anatomy, facial_quality, photographic_realism,
  visual_coherence, diversity, technical_quality

Todas las dimensiones son float 0..10. Una anomalía grave (hands/anatomy
critical, ojos/rostro, etc.) puede reducir drásticamente el total.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ─────────────────────────────────────────────
# Modelo de puntaje — VisualQualityScore
# ─────────────────────────────────────────────
@dataclass
class VisualQualityScore:
    """Puntaje de calidad visual con dimensiones 0..10."""

    dimensions: dict[str, float] = field(default_factory=dict)
    hard_anomalies: list[str] = field(default_factory=list)   # reducen fuerte
    soft_issues: list[str] = field(default_factory=list)
    total: float = 0.0
    passed_threshold: bool = False
    source: str = "rule"          # "rule" | "vision" | "hybrid"

    DIMENSIONS: tuple[str, ...] = (
        "composition", "framing", "subject_visibility", "text_space",
        "human_realism", "skin_realism", "anatomy", "facial_quality",
        "photographic_realism", "visual_coherence", "diversity",
        "technical_quality",
    )

    def __post_init__(self):
        if not self.dimensions:
            self.dimensions = {k: 0.0 for k in self.DIMENSIONS}

    def compute_total(self, hard_penalty: float = 4.0) -> float:
        """Promedio de dimensiones, menos N por cada anomalía grave."""
        t = sum(self.dimensions.values()) / max(1, len(self.dimensions))
        t -= hard_penalty * len(self.hard_anomalies)
        self.total = round(max(0.0, min(10.0, t)), 2)
        return self.total

    @property
    def passed(self) -> bool:
        return self.passed_threshold

    def to_dict(self) -> dict:
        return {
            "dimensions": self.dimensions,
            "hard_anomalies": self.hard_anomalies,
            "soft_issues": self.soft_issues,
            "total": self.total,
            "passed_threshold": self.passed_threshold,
            "source": self.source,
        }


ALL_DIMS = VisualQualityScore.DIMENSIONS


# ─────────────────────────────────────────────
# Composición 16:9 / 9:16 — reglas geométricas puras
# ─────────────────────────────────────────────
@dataclass
class CompositionSpec:
    """Descripción de la composición deseada; usada por las reglas.

    Todas las coordenadas en fracciones del canvas (0..1).
    """
    canvas_ar: str = "16:9"          # "16:9" | "9:16"
    subject_box: tuple | None = None # (x0,y0,x1,y1) en fracciones
    focal_point: tuple | None = None # (x,y) dónde pone el ojo primero
    headroom: float = 0.0            # espacio sobre el sujeto (si es persona)
    text_zone: tuple = (0.0, 0.72, 1.0, 1.0)  # zona de texto (en fracciones)
    margins: tuple = (0.08, 0.08, 0.08, 0.08) # l,t,r,b en fracciones

    # Safe-zone ideal por aspecto (restricción de UI sin texto pegado a bordes)
    MIN_EDGE = 0.06
    TEXT_SAFE_VERTICAL = 0.70        # texto a partir del 70% (9:16)
    TEXT_SAFE_HORIZONTAL_BOTTOM = 0.74  # franja inferior 16:9


def _inside(box, margins):
    l, t, r, b = margins
    x0, y0, x1, y1 = box
    if isinstance((l,), (int, float)) and not isinstance(l, (int, float)):
        pass
    # margins puede ser tupla
    return (x0 >= l and y0 >= t and x1 <= (1 - r) and y1 <= (1 - b))


def check_subject_scale(subject_box, min_scale=0.12, max_scale=0.85):
    """El sujeto debe ocupar una fracción razonable del canvas.

    PROBLEMA A: un sujeto gigante (>= max_scale) produce composición rota y
    puede empujar el texto. Uno diminuto no es legible.
    """
    if not subject_box:
        return 7.0, "sin subject_box (no penalizable)"
    w = subject_box[2] - subject_box[0]
    h = subject_box[3] - subject_box[1]
    area = w * h
    if area > max_scale:
        return 2.0, f"subject escala {area:.2f} > {max_scale} (demasiado grande)"
    if area < min_scale:
        return 4.0, f"subject escala {area:.2f} < {min_scale} (demasiado pequeño)"
    return 9.5, f"subject escala {area:.2f} OK"


def check_margins(subject_box, margins):
    """El sujeto no debe cortarse contra los bordes (headroom + safe zones)."""
    if not subject_box:
        return 7.0, "sin subject_box"
    if _inside(subject_box, margins):
        return 9.5, "dentro de márgenes"
    # ¿qué borde cruza?
    reasons = []
    if subject_box[0] < margins[0]:
        reasons.append("pega izquierda")
    if subject_box[1] < margins[1]:
        reasons.append("pega arriba (sin headroom)")
    if subject_box[2] > (1 - margins[2]):
        reasons.append("pega derecha")
    if subject_box[3] > (1 - margins[3]):
        reasons.append("pega abajo")
    return 4.0 if not reasons else 3.0, ("; ".join(reasons) if reasons else "fuera")


def check_text_space(subject_box, text_zone, canvas_ar):
    """El sujeto no debe invadir la zona reservada al texto."""
    if not subject_box:
        return 7.0, "sin subject_box"
    sx0, sy0, sx1, sy1 = subject_box
    zx0, zy0, zx1, zy1 = text_zone
    overlap_y = not (sy1 <= zy0 or sy0 >= zy1)
    overlap_x = not (sx1 <= zx0 or sx0 >= zx1)
    if overlap_x and overlap_y:
        return 2.5, "sujeto invade zona de texto"
    # si el texto está abajo, el sujeto no debe extenderse a esa franja
    if canvas_ar == "9:16" and sy1 > zy0:
        return 4.0, "sujeto se acerca a la zona de karaoke"
    return 9.5, "sujeto respeta zona de texto"


def check_focus(focal_point, canvas_ar):
    """El sujeto/foco principal debe quedar en zona de interés (no clavado al borde)."""
    if not focal_point:
        return 7.0, "sin focal_point"
    x, y = focal_point
    if canvas_ar == "9:16":
        # en vertical, el foco suele estar en tercio medio-superior
        ok = (0.2 <= x <= 0.8) and (0.2 <= y <= 0.78)
    else:
        ok = (0.15 <= x <= 0.85) and (0.15 <= y <= 0.72)
    return (9.5, "foco en zona de interés") if ok else (3.5, f"foco fuera de zona ({x:.2f},{y:.2f})")


def score_composition_16x9(subject_box=None, focal_point=None, margins=None,
                           text_zone=None):
    """Composición horizontal (PROBLEMA A / PASO 6):
    subject scale + crop + focal area + text-safe + balance + headroom + margins.
    """
    margins = margins or CompositionSpec().margins
    text_zone = text_zone or CompositionSpec().text_zone
    score, issues = 0.0, []
    s, why = check_subject_scale(subject_box)
    score += s * 0.30; issues.append(f"scale:{why}")
    s, why = check_margins(subject_box, margins)
    score += s * 0.25
    if "pega arriba" in why or "sin headroom" in why:
        issues.append("headroom")
    s, why = check_focus(focal_point, "16:9")
    score += s * 0.20; issues.append(f"focus:{why}")
    s, why = check_text_space(subject_box, text_zone, "16:9")
    score += s * 0.25; issues.append(f"text:{why}")
    return round(min(10.0, score), 2), issues


def score_composition_9x16(subject_box=None, focal_point=None, margins=None,
                           text_zone=None):
    """Composición vertical (PASO 7): sujeto legible, espacio texto, safe zones,
    escala natural. Prioriza manos/rostro cuando relevantes."""
    margins = margins or CompositionSpec().margins
    text_zone = text_zone or CompositionSpec().text_zone
    score, issues = 0.0, []
    s, why = check_subject_scale(subject_box, min_scale=0.10, max_scale=0.88)
    score += s * 0.30; issues.append(f"scale:{why}")
    s, why = check_margins(subject_box, margins)
    score += s * 0.25; issues.append(f"margins:{why}")
    s, why = check_focus(focal_point, "9:16")
    score += s * 0.20; issues.append(f"focus:{why}")
    s, why = check_text_space(subject_box, text_zone, "9:16")
    score += s * 0.25; issues.append(f"text:{why}")
    return round(min(10.0, score), 2), issues


def smart_crop_geometry(img_w, img_h, target_ar="16:9", focal=None):
    """Computa el rectángulo de crop que acerca el asset al aspect target
    PRIORIZANDO el punto focal/composición en vez de recortar al centro ciego.

    PROBLEMA A: build_bg hace center-crop ciego. Este devuelve el crop box
    (x0,y0,x1,y1) eligiendo el lado de más "materia" según el focal.

    No modifica la imagen: solo computa geometría (determinista). El caller
    decide el crop (o este módulo ofrece apply_crop()).
    """
    t = 16 / 9 if target_ar == "16:9" else 9 / 16
    src = img_w / img_h
    focal = tuple(focal) if focal else None

    if src > t:
        # más ancho de lo necesario → recortar horizontal
        nw = int(img_h * t)
        if focal and 0 <= focal[0] < 1:
            # alinear crop al focal (x)
            cx = focal[0] * img_w
            x0 = int(max(0, min(img_w - nw, cx - nw // 2)))
        else:
            x0 = (img_w - nw) // 2
        return (x0, 0, x0 + nw, img_h)
    else:
        # más alto de lo necesario → recortar vertical (PROBLEMA A en 16:9 desde 9:16)
        nh = int(img_w / t)
        if focal and 0 <= focal[1] < 1:
            cy = focal[1] * img_h
            y0 = int(max(0, min(img_h - nh, cy - nh // 2)))
        else:
            y0 = (img_h - nh) // 2
        return (0, y0, img_w, y0 + nh)


def apply_crop(img, box):
    """Recorta img PIL usando un crop box de smart_crop_geometry()."""
    from PIL import Image
    x0, y0, x1, y1 = box
    return img.crop((int(x0), int(y0), int(x1), int(y1)))


def default_subject_box_from_prompt(prompt_text, canvas_ar):
    """Heurística determinista: estima un subject_box razonable desde el prompt
    cuando no hay datos de visión. NO sustituye al QA visual; da un default."""
    p = (prompt_text or "").lower()
    d = {
        "close-up": (0.18, 0.18, 0.78, 0.62),
        "extreme close-up": (0.25, 0.20, 0.75, 0.55),
        "wide shot": (0.10, 0.30, 0.90, 0.80),
    }
    for k, box in d.items():
        if k in p:
            return box
    return (0.15, 0.25, 0.85, 0.78)


# ─────────────────────────────────────────────
# Human realism — reglas + heurísticas de prompt + API de visión
# ─────────────────────────────────────────────
_ANATOMY_KW = [
    "hands", "fingers", "held", "holding", "embracing", "embrace",
    "clasped", "interlaced", "palms", "gripping", "touching", "fist",
    "pointing", "handshake", "hug", "hugging", "arms around",
]
_FACE_KW = ["face", "eyes", "portrait", "looking at camera", "front-facing",
            "smiling", "teeth", "close-up of her face", "close-up of his face"]
_SKIN_HARD_KW = ["porcelain", "doll", "plastic skin", "flawless", "airbrushed",
                 "wax", "mannequin", "perfect skin", "smooth skin", "barbie"]
_SKIN_GOOD_KW = ["natural skin texture", "pores", "skin texture", "imperfections",
                 "small blemishes", "realistic skin", "natural skin tones",
                 "fine lines", "visible pores", "textured skin"]
_FUSION_KW = ["plants", "plant", "flowers", "vines", "leaves", "garden", "blossoming"]


def anatomy_risk(prompt_text=""):
    """Nivel de riesgo anatómico según el prompt (manos/dedos/abrazos).

    high: interacción compleja cuerpo-objeto / ambas manos / dedos.
    medium: una mano en acción simple.
    low: sin manos o acción que no pide anatomía fina.
    """
    p = (prompt_text or "").lower()
    count = sum(1 for kw in _ANATOMY_KW if kw in p)
    complex_kw = ["embracing", "embrace", "clasped", "interlaced", "hugging",
                  "hug", "handshake", "arms around", "fingers", "both hands"]
    if any(k in p for k in complex_kw) or count >= 3:
        return "high"
    if count >= 1:
        return "medium"
    return "low"


def face_risk(prompt_text=""):
    """Nivel de riesgo facial (ojos/rostro/retrato).

    Respeta la negación natural ("no faces visible", "faces not seen") que
    usa el canal: esas NO elevan el riesgo facial.
    """
    p = (prompt_text or "").lower()
    # negación de rostro visible → LOW
    if re.search(r"(no|without|not)\s+(faces?|any faces?)\s+(visible|seen|shown|not visible)", p) \
            or "no faces visible" in p or "without any faces" in p or "no faces" in p:
        return "low"
    if any(k in p for k in ("eyes", "looking at camera", "front-facing",
                            "close-up of her face", "close-up of his face",
                            "smiling", "teeth")):
        return "high"
    if any(k in p for k in ("face", "portrait", "looks at camera")):
        return "medium"
    return "low"


def skin_risk_word(prompt_text=""):
    """Detecta léxico de piel MUÑECA vs piel REAL en el prompt."""
    p = (prompt_text or "").lower()
    hard = sum(1 for k in _SKIN_HARD_KW if k in p)
    good = sum(1 for k in _SKIN_GOOD_KW if k in p)
    if hard and not good:
        return "hard"
    if hard or not good:
        return "warning"
    return "ok"


def human_realism_rule_score(prompt_text=""):
    """Estimación de regla del realismo humano desde el prompt.

    Combina anatomía (hands/anatomy = crítico), rostro/ojos (high) y piel
    (medium/high). Reduce el score cuando el riesgo es alto y el prompt NO lo
    contrarresta con realismo explícito.
    """
    prompt_text = prompt_text or ""
    p = prompt_text.lower()
    score = 7.0

    a = anatomy_risk(prompt_text)
    if a == "high":
        score -= 2.5
    elif a == "medium":
        score -= 1.0

    f = face_risk(prompt_text)
    if f == "high":
        score -= 1.5
    elif f == "medium":
        score -= 0.5

    sk = skin_risk_word(prompt_text)
    if sk == "hard":
        score -= 2.5
    elif sk == "warning":
        score -= 0.8

    # refuerzo positivo por realismo explícito
    if any(k in p for k in _SKIN_GOOD_KW):
        score += 1.2
    if "natural skin texture" in p:
        score += 0.6
    if "imperfections" in p or "small blemishes" in p:
        score += 0.5
    if "real person" in p or "candid" in p or "authentic" in p:
        score += 0.8

    return round(max(0.0, min(10.0, score)), 2)


def fusion_risk(prompt_text=""):
    """Fusion FLUX persona+plantas/tejidos (problema B/anatomía)."""
    p = (prompt_text or "").lower()
    if any(k in p for k in _FUSION_KW) and any(k in p for k in
                                              ("woman", "man", "person", "her", "his")):
        return "high"
    return "low"


# ─────────────────────────────────────────────
# Anti-slop — motivos visuales repetidos
# ─────────────────────────────────────────────
DEFAULT_SLOP_MOTIFS = {
    "person looking out window": ["looking out the window", "looks out the window",
                                  "by the window", "gazing out the window"],
    "sad person sitting": ["sad person sitting", "sitting alone and sad",
                           "sad woman sitting", "sad man sitting"],
    "hands on table": ["hands on the table", "hands on a table", "hands resting on table"],
    "coffee + notebook": ["coffee and notebook", "coffee next to a notebook",
                          "coffee and journal", "latte and notebook"],
    "person walking alone": ["walking alone", "walks alone", "walking by herself",
                             "walking by himself"],
    "generic plant": ["a plant", "a potted plant", "generic plant", "small plant"],
    "silhouette facing horizon": ["silhouette facing the horizon", "silhouette looking at the horizon",
                                  "silhouette on the hill", "silhouette against the sky"],
}


def count_slop(prompt_texts, motif_map=None):
    """Cuenta cuántos motivos slop distintos detección en una lista de prompts."""
    motif_map = motif_map or DEFAULT_SLOP_MOTIFS
    counts: dict[str, int] = {}
    for pt in prompt_texts:
        p = (pt or "").lower()
        for name, variants in motif_map.items():
            if any(v in p for v in variants):
                counts.setdefault(name, 0)
                counts[name] += 1
    return counts


def anti_slop_penalty(prompt_texts, motif_map=None):
    """Devuelve (penalización, lista de motivos repetidos).

    Un motivo usado una vez es aceptable; repetido en varias escenas es slop.
    """
    counts = count_slop(prompt_texts, motif_map)
    repeated = {k: v for k, v in counts.items() if v > 1}
    penalty = sum(v - 1 for v in repeated.values())
    return penalty, repeated


# ─────────────────────────────────────────────
# Visual / text mismatch (PASO 8)
# ─────────────────────────────────────────────
_STOP = set("de del la el los las un una y o pero porque por para en con a al se le lo que como esto esto aquel esta este estas estos".split())

# Léxico bilingüe ES/EN de conceptos narrativos para detectar mismatch real
# (el texto es ES y la imagen/prompt es EN). General, no por tema.
_CONCEPTS = {
    "person": ["persona", "mujer", "hombre", "person", "woman", "man", "gente",
               "ella", "él", "alguien", "gente"],
    "landscape": ["paisaje", "playa", "horizonte", "silueta", "beach", "landscape",
                  "horizon", "silhouette", "nature", "bosque", "mont", "ciudad",
                  "city", "campo"],
    "hands": ["mano", "manos", "hand", "hands", "dedos", "fingers"],
    "writing": ["escribir", "escribiendo", "write", "writing", "escribir", "nota"],
    "rest": ["descansar", "descanso", "rest", "resting", "sleep", "dormir", "pausa"],
    "work": ["trabajo", "trabajar", "work", "working", "producir", "tarea"],
    "talking": ["hablar", "conversación", "talk", "talking", "conversation",
                "conversando", "dialogo"],
    "alone": ["solo", "sola", "alone", "by herself", "by himself", "solitario"],
}

# Micro-acciones humanas concretas (señal de coherencia narrativa en el visual).
_MICRO_ACTION = [
    "hesitating", "hesitates", "pausing", "paused", "before sending",
    "sending a message", "typing", "answering", "writing", "reading",
    "talking", "speaking", "thinking", "reflect", "resting", "listening",
    "drinking tea", "sipping", "cooking", "cleaning", "mending", "repairing",
    "watering", "taking notes", "meditando", "duda", "dudando", "escribiendo",
    "escribir", "conversando", "temando", "sostiene la taza", "dejando la taza",
]
# Motivos ambientales GENÉRICOS: sin micro-acción humana concreta → mismatch
# cuando el texto pide una acción (el "persona caminando por la playa" del pitch).
_GENERIC_AMBIENT = [
    "beach", "playa", "landscape", "paisaje", "horizon", "horizonte",
    "silhouette", "silueta", "walking alone", "caminando sola", "caminando solo",
    "empty room", "nature", "bosque", "campo", "city street at night",
]


def _concept_present(text, concept):
    t = (text or "").lower()
    return any(w in t for w in _CONCEPTS.get(concept, []))


def _tokens(text):
    return {w for w in re.findall(r"[a-záéíóúñ]+", (text or "").lower()) if w not in _STOP and len(w) > 2}


def _contains_any_hardword(text, words):
    t = (text or "").lower()
    return any(w in t for w in words)


def score_narrative_match(scene_text, visual_event, asset_desc="", motion=""):
    """Penaliza cuando el texto y la imagen NO cuentan lo mismo.

    PALO 8 conceptual:
      - El texto (ES) y el visual event (EN) cuentan un momento. Si el texto
        espera una PERSONA y el visual es un PAISAJE genérico sin sujeto, o la
        acción NO aparece, hay mismatch.
      - El match NO se mide por belleza: se mide por coherencia narrativa
        entre texto, visual event, asset y motion.

    Devuelve (score 0..10, razones, mismatch_bool). Determinista.
    """
    reasons = []
    st = _tokens(scene_text)
    ve_txt = visual_event or ""
    ve = _tokens(ve_txt)

    overlap_base = len(st & ve)
    overlap = max(overlap_base, 0)

    score = 6.0
    if overlap >= 2:
        score += 2.0
        reasons.append(f"solapamiento temático {overlap}")
    elif overlap == 1:
        score += 0.5
        reasons.append("solapamiento temático débil")
    else:
        # ES↔EN no comparten léxico literal; NO penalizar doble (ver conceptos)
        reasons.append("sin solapamiento literal (ES/EN, se evalúa por conceptos)")

    # 1) El texto espera una persona y la imagen es un paisaje sin sujeto
    expects_person = _concept_present(scene_text, "person")
    visual_is_person = _concept_present(ve_txt, "person")
    visual_is_landscape = _concept_present(ve_txt, "landscape")
    if expects_person and visual_is_landscape and not visual_is_person:
        score -= 2.5
        reasons.append("texto espera persona, imagen es paisaje (mismatch narrativo)")

    # 2) Sin visual_event / sin acción propuesta
    if not ve_txt:
        score -= 1.5
        reasons.append("sin visual_event (imagen no propone acción)")

    # 3) Coherencia de acción concepto a concepto (ES ↔ EN)
    action_concepts = ("writing", "rest", "work", "talking", "hands")
    hit = miss = 0
    for concept in action_concepts:
        if _concept_present(scene_text, concept):
            if _concept_present(ve_txt, concept):
                hit += 1
            else:
                miss += 1
                reasons.append(f"texto menciona '{concept}' pero el visual no")
    if hit:
        score += min(2.0, 0.7 * hit)
        reasons.append(f"{hit} conceptos de acción coherentes entre texto y visual")
    if miss:
        score -= miss

    # 4) Persona coherente: el texto habla de gente y el visual muestra gente
    if expects_person and visual_is_person:
        score += 1.0
        reasons.append("texto y visual coinciden en sujeto humano")

    # 5) Micro-acción concreta vs ambient genérico (núcleo del mismatch del pitch)
    vlow = ve_txt.lower()
    has_micro = any(w in vlow for w in _MICRO_ACTION)
    is_generic_ambient = any(w in vlow for w in _GENERIC_AMBIENT)
    text_action_oriented = any(
        _concept_present(scene_text, c) for c in
        ("writing", "rest", "work", "talking", "hands")
    ) or any(w in (scene_text or "").lower() for w in ("medir", "enviar", "palabra", "decid", "duda", "pregunt"))
    if text_action_oriented and is_generic_ambient and not has_micro:
        score -= 2.5
        reasons.append("visual es ambiente genérico sin la acción que pide el texto")
    elif has_micro:
        score += 1.5
        reasons.append("visual muestra una micro-acción humana concreta (coherente)")

    # 4) Motion desalineado con un momento contemplativo/quieto (heuristic)
    if motion:
        m = motion.lower()
        quiet_scene = _concept_present(ve_txt, "rest") or _concept_present(ve_txt, "writing")
        if quiet_scene and m in ("zoom-in-fast", "pan-right") :
            score -= 0.8
            reasons.append("motion acelerado sobre escena contemplativa")

    score = max(0.0, min(10.0, score))
    mismatch = score < 6.0
    return round(score, 2), reasons, mismatch


# ─────────────────────────────────────────────
# Regeneración (PASO 4)
# ─────────────────────────────────────────────
@dataclass
class RegenerationResult:
    ok: bool
    attempts: int
    scores: list[float]
    reject_reasons: list[str]
    final_path: str | None
    used_fallback: bool = False
    fallback_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "attempts": self.attempts,
            "scores": self.scores,
            "reject_reasons": self.reject_reasons,
            "final_path": self.final_path,
            "used_fallback": self.used_fallback,
            "fallback_reason": self.fallback_reason,
        }


class RegenerationEngine:
    """GENERATE → VISUAL QA → SCORE → si < threshold REGENERATE → máx N
    intentos → FALLBACK. Sin loops infinitos. Inyectable para tests."""
    def __init__(self, threshold: float = 6.5, max_attempts: int = 3,
                 fallback="skip"):
        self.threshold = threshold
        self.max_attempts = max(1, int(max_attempts))
        self.fallback = fallback  # "skip" | "commons" | path-to-img

    def evaluate(self, image_path):
        """Encapsula la QA. Por defecto usa visual_critic (visión real).
        Subclases/tests pueden inyectar evaluadores deterministas."""
        try:
            from visual_critic import critique
            res = critique(image_path, mode="gen", min_score=self.threshold,
                           save_sidecar=False, require_cta=False)
            score = res.get("score") if res.get("score") is not None else 0.0
            reasons = res.get("hard_fails", []) + res.get("soft_issues", [])
            return score, reasons
        except Exception as e:  # noqa: BLE001
            return 0.0, [f"critic error: {e}"]

    def run(self, generate_fn, *, attempt_seed_spread=7):
        """Ejecuta el ciclo. generate_fn(attempt) → (path|None, motivo_opcional).

        attempt 0..N-1. Actualiza el seed/spread por intento para variar.
        Devuelve RegenerationResult.
        """
        scores, reasons = [], []
        for attempt in range(self.max_attempts):
            try:
                path = generate_fn(attempt)
            except Exception as e:  # noqa: BLE001
                reasons.append(f"generate error en intento {attempt}: {e}")
                scores.append(0.0)
                continue
            if not path:
                reasons.append(f"generate devolvió None en intento {attempt}")
                scores.append(0.0)
                continue
            score, why = self.evaluate(path)
            scores.append(score)
            if why:
                reasons.append(f"intento {attempt} score={score:.1f}: {why[:120]}")
            else:
                reasons.append(f"intento {attempt} score={score:.1f}")
            if score >= self.threshold:
                return RegenerationResult(
                    ok=True, attempts=attempt + 1, scores=scores,
                    reject_reasons=reasons, final_path=path,
                    used_fallback=False)
        # agotados los intentos → fallback
        return RegenerationResult(
            ok=False, attempts=self.max_attempts, scores=scores,
            reject_reasons=reasons, final_path=None,
            used_fallback=True, fallback_reason=str(self.fallback))


# ─────────────────────────────────────────────
# Prompt — human realism + composición (PASO 5, 6, 7)
# ─────────────────────────────────────────────
HUMAN_REALISM_ANCHOR = (
    "Real human skin with natural texture, visible pores, subtle tonal variation "
    "and small imperfections; no doll-like plastic skin."
)

REPRESENTATION_ANCHOR = (
    "Contemporary Western everyperson, realistically diverse and context-appropriate "
    "for the setting; natural, unscripted, non-clone appearance."
)


def build_quality_prompt(base_prompt, *, canvas_ar="16:9", has_human=True,
                         human_representation=None):
    """Envuelve un prompt base con anclas de realismo humano y composición por
    aspecto. Compacto (no una lista interminable), respeta el framework
    SUJETO→ACCIÓN→ENTORNO→LUZ→CÁMARA del canal.

    base_prompt: prompt cinematográfico (de compose_prompt u otro).
    """
    parts = [base_prompt.rstrip(".")]

    if has_human:
        if human_representation:
            parts.append(human_representation.strip().rstrip("."))
        else:
            parts.append(REPRESENTATION_ANCHOR.rstrip("."))
        parts.append(HUMAN_REALISM_ANCHOR.rstrip("."))
    else:
        parts.append("Cinematic landscape or object still, no people in frame, realistic texture and natural light")

    if canvas_ar == "16:9":
        parts.append(
            "Horizontal 16:9 cinematic composition, subject well proportioned within "
            "the frame, balanced negative space, subject clear of the lower text band, "
            "comfortable headroom and margins.")
    else:
        parts.append(
            "Vertical 9:16 composition, subject legible and naturally scaled, ample "
            "space in the upper area, subject clear of the lower text band.")

    return ". ".join(p.rstrip(".") for p in parts) + "."


def human_representation_for(setting="", message="", avoid_ethnocentrism=True):
    """Preferencia humana CONTEXTUAL (PROBLEMA C): diversa, contemporánea,
    occidental cuando el contexto lo sugiera. NO es exclusión étnica: elige
    por contexto narrativo, no clona, no presume etnia del idioma."""
    s = (setting or "").lower()
    if any(k in s for k in ("latin", "mexico", "andes", "peruvian", "chilean",
                            "mexican", "guadalajara", "bogota", "buenos aires",
                            "latina", "latino", "españa", "espana", "madrid")):
        return ("Latin woman in her 30s with warm brown skin, contemporary western "
                "style, natural unscripted appearance.")
    if any(k in s for k in ("africa", "kenya", "lagos", "nairobi", "ghana")):
        return ("West African woman with natural dark skin, contemporary western "
                "style, natural unscripted appearance.")
    if any(k in s for k in ("asia", "tokyo", "seoul", "india", "mumbai", "korea", "japan")):
        return ("East Asian woman with natural skin texture, contemporary western "
                "style, natural unscripted appearance.")
    # default contextual: occidental contemporáneo diverso
    return ("Contemporary western everyperson, natural and unscripted, "
            "realistic diverse appearance matched to the setting.")


# ─────────────────────────────────────────────
# Orquestrador — VisualQualityEngine
# ─────────────────────────────────────────────
class VisualQualityEngine:
    """Combina todas las reglas V2.1 en un solo score por escena/video.

    Uso conceptual:
        eng = VisualQualityEngine(aspect="16:9")
        score = eng.assess(scene_prompt=..., scene_text=...,
                           img_w=1920, img_h=1080)
    """

    def __init__(self, aspect="16:9", critic_fn=None, threshold=6.5,
                 max_attempts=3):
        self.aspect = aspect
        self.critic_fn = critic_fn      # opcional: visión real
        self.regen = RegenerationEngine(threshold, max_attempts)

    def _vision_dimension(self, image_path, dimension):
        """Delega UNA dimensión al crítico visual si está conectado."""
        if not self.critic_fn or not image_path or not os.path.exists(image_path):
            return None
        try:
            res = self.critic_fn(image_path)
            dims = res.get("dimensions", {}) or {}
            if dimension in dims:
                return dims[dimension]
        except Exception:  # noqa: BLE001
            return None
        return None

    def assess(self, *, scene_prompt="", scene_text="", img_w=0, img_h=0,
               image_path=None, visuals_list=None, subject_box=None,
               focal_point=None, has_human=True):
        """Devuelve un VisualQualityScore."""
        dims = {k: 5.0 for k in ALL_DIMS}
        hard, soft = [], []

        # Composición por aspecto (determinista)
        if self.aspect == "16:9":
            c, issues = score_composition_16x9(subject_box, focal_point)
        else:
            c, issues = score_composition_9x16(subject_box, focal_point)
        dims["composition"] = c
        dims["framing"] = c * 0.9 + 1.0
        dims["subject_visibility"] = (c * 0.8 + 2.0) if subject_box else 5.0
        dims["text_space"] = (9.5 if subject_box else 7.0)

        # Realismo humano (regla + visión opcional)
        hr = human_realism_rule_score(scene_prompt)
        dims["human_realism"] = hr
        dims["skin_realism"] = max(3.0, hr - 0.5)
        anat = anatomy_risk(scene_prompt)
        if anat == "high":
            dims["anatomy"] = 3.0
            hard.append("anatomy:hands_high_risk")   # PROBLEMA B — anomalía grave
        elif anat == "medium":
            dims["anatomy"] = 6.0
            soft.append("anatomy:hands_medium_risk")
        else:
            dims["anatomy"] = 8.5
        fq = face_risk(scene_prompt)
        dims["facial_quality"] = 8.5 if fq == "low" else (6.0 if fq == "medium" else 4.5)
        if fq == "high":
            soft.append("facial_quality:face/eyes_high_risk")
        if skin_risk_word(scene_prompt) == "hard":
            dims["skin_realism"] = 2.5
            hard.append("skin_porcelain_language")    # PROBLEMA D
        dims["photographic_realism"] = hr * 0.85 + 1.5

        # Coherencia / diversidad
        dims["visual_coherence"] = 7.0
        if visuals_list:
            pen, rep = anti_slop_penalty(visuals_list)
            dims["diversity"] = max(2.0, 8.0 - pen)
            if rep:
                soft.append(f"anti_slop:{rep}")
        else:
            dims["diversity"] = 7.0

        # Técnica: si hay dimensión, evaluamos overlap del canvas (PROBLEMA A)
        dims["technical_quality"] = 7.0
        if img_w and img_h:
            ar = img_w / img_h
            want = 16 / 9 if self.aspect == "16:9" else 9 / 16
            if abs(ar - want) > 0.05:
                dims["technical_quality"] = 4.0
                hard.append(f"aspect_mismatch:{img_w}x{img_h} para {self.aspect}")

        # Narrativa (mismatch)
        nm, _, mismatch = score_narrative_match(
            scene_text, scene_prompt)
        dims["visual_coherence"] = (dims["visual_coherence"] + nm) / 2
        if mismatch:
            hard.append("visual_text_mismatch")

        score = VisualQualityScore(
            dimensions={k: round(float(v), 2) for k, v in dims.items()},
            hard_anomalies=hard, soft_issues=soft)
        score.compute_total()
        score.passed_threshold = score.total >= self.regen.threshold
        score.source = "rule"
        return score


def audience_defaults():
    """Preferencias por defecto de la audiencia del canal (mujeres 35-64).
    Devuelve anclas de prompt que se pueden inyectar en build_quality_prompt."""
    return {
        "humans_more_natural": True,
        "comfortable_environments": True,
        "warm_luminance": True,
    }
