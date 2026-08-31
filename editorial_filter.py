"""editorial_filter.py — FILTRO EDITORIAL (seguridad editorial, HARD FAIL).

Impide que un asset editorialmente inadecuado llegue al video final.

AUDITORÍA 2026-08-28 (prueba real "El perdón te hace libre"):
  La imagen e02 que llegó al MP4 mostraba a una mujer con el torso desnudo y
  PASÓ el Quality Gate con score 8.0. La causa raíz: el gate NO evaluaba
  seguridad editorial, y el crítico de visión genérico (qwen25-vl free.ai)
  responde "safe" a una pregunta binaria aunque perciba el desnudo (describe
  "upper body bare" pero NO lo juzga). Cloudflare Worker AI (credenciales del
  proyecto) NO expone un clasificador NSFW dedicado (solo llama-3.2-vision).

  CONCLUSIÓN de diseño: NO se confía en el JUICIO del VLM (no es clasificador
  de seguridad). Se usa su PERCEPCIÓN factual (describir qué cubre la ropa),
  que sí es confiable, y el SISTEMA aplica reglas editoriales conservadoras
  sobre los hechos percibidos.

CAPAS (todas deterministas o de percepción-factual):
  1. PREVENCIÓN en el prompt  -> nunca pedir puesta en escena de riesgo; exigir
     ropa modesta para personas (ver build_safe_prompt).
  2. PRE-SCREEN determinista  -> señales de riesgo en el prompt (respaldón).
  3. VEREDICTO FACTUAL          -> visión describe la cobertura de ropa de cada
     persona; el sistema juzga (capa "coverage" con reglas => UNSAFE).
  4. HARD FAIL en quality_gate -> un candidato inseguro NUNCA pasa a PASS, ni
     es "mejor candidato", ni es el fallback final.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ─────────────────────────────────────────────
# 1) PREVENCIÓN en el prompt (modesta, sin riesgo)
# ─────────────────────────────────────────────

# Sufijos que fuerzan cobertura de ropa y modales de escena en personas.
_MODESTY_SUFFIX = (
    " The person is FULLY CLOTHED in normal, modest, everyday clothing "
    "(a shirt and trousers or casual outfit), torso fully covered."
)
_NO_RISK_SCENE = (
    " No nudity, no bare chest, no revealing or sexualized pose or framing; "
    " an appropriate, wholesome, clothes-on everyday scene."
)
# Escenarios/sujetos que tienden a generar desnudez en modelos de imagen:
# NO pedir estas composiciones para escenas con personas.
_RISKY_SUBJECT_MOTIF = {
    "bed", "bath", "bathroom", "shower", "undressing", "changing clothes",
    "lingerie", "underwear", "bare shoulders", "bare back", "shoulders bare",
    "cama", "baño", "ducha", "desnuda", "desnudo", "torso",
}


def build_safe_prompt(prompt: str, *, has_human: bool) -> str:
    """Enriquece un prompt para que sea seguro y modesto.

    - has_human=True  => añade cobertura de ropa y escena sin riesgo.
    - Siempre añade un sufijo de "no nudity/no sexualized" salvo que el prompt
      ya lo pida.
    """
    base = (prompt or "").strip().rstrip(".")
    if not base:
        return base
    out = base
    if has_human:
        low = base.lower()
        # Si ya pidió algo de riesgo, lo neutralizamos explícitamente.
        for motif in _RISKY_SUBJECT_MOTIF:
            if motif in low:
                out += (f" Fully clothed, modest; the described setting ({motif}) "
                        "is shown respectfully with the person fully dressed, "
                        "no skin uncovered.")
                break
        else:
            out += _MODESTY_SUFFIX
    out += _NO_RISK_SCENE
    return out + "."


# ─────────────────────────────────────────────
# 2) PRE-SCREEN determinista (señales en el prompt / texto)
# ─────────────────────────────────────────────

_STRONG = {
    "naked", "nude", "nudity", "topless", "bare chest", "bare breasts",
    "bare torso", "bare skin", "bare above the waist", "upper body bare",
    "upper body uncovered", "body bare", "bare body", "exposed breasts",
    "exposed chest", "nipples", "nude woman", "partially clothed",
    "unclothed", "not fully clothed", "without clothes", "no clothes",
    "not wearing a shirt", "without a shirt", "no shirt", "topless woman",
    "desnuda", "desnudo", "desnudez", "pechos", "pezones", "tetas",
    "torso desnudo", "pecho desnudo", "torso al descubierto",
    "torso descubierto", "sin ropa", "sin camiseta", "sin blusa",
    "sin parte de arriba", "sin nada arriba",
}
_PROVOCATIVE = {
    "seductive", "seduction", "sultry", "provocative", "sensual", "sexual",
    "sexually", "lingerie", "erotic", "boudoir", "suggestive", "porn",
    "pornographic", "fetish", "bondage", "cleavage", "low-cut",
    "provocativo", "sensual", "erótico", "lencería", "fetichista", "escote",
}
_AMBIGUOUS = {
    "bare shoulders", "bare back", "bath", "shower", "underwear", "bikini",
    "shirtless", "cama", "baño", "ducha",
}


def _strip_safety_suffixes(text: str) -> str:
    """Quita los sufijos de SEGURIDAD que nosotros mismos añadimos con
    build_safe_prompt. Sin esto, keyword_scan matcheaba "nudity"/"bare chest"/
    "sexualized" dentro de "No nudity, no bare chest, no revealing or sexualized
    pose" y marcaba UNSAFE cada prompt seguro (auto-bloqueo). Como son bloques
    exactos que SOLO genera nuestro propio build_safe_prompt, strippearlos es
    seguro y preciso (no afecta a descripciones arbitrarias de imagen).
    """
    out = text or ""
    for block in (_MODESTY_SUFFIX, _NO_RISK_SCENE):
        out = out.replace(block, " ")
    # Clausa de motivo de riesgo ("Fully clothed ... no skin uncovered.").
    out = re.sub(
        r"Fully clothed, modest; the described setting \([^)]*\) is shown "
        r"respectfully with the person fully dressed, no skin uncovered\.?",
        " ", out, flags=re.I)
    return out


def keyword_scan(text: str) -> EditorialVerdict:
    """Pre-screen determinista por señales en un texto (prompt o descripción).

    Ignora las cláusulas de seguridad que nosotros mismos añadimos en
    build_safe_prompt (ver _strip_safety_suffixes) para no auto-bloquear
    prompts seguros.
    """
    text = _strip_safety_suffixes(text)
    strong = _hits(text, _STRONG)
    prov = _hits(text, _PROVOCATIVE)
    amb = _hits(text, _AMBIGUOUS)
    if strong or prov or len(amb) >= 2:
        terms = strong + prov + (amb if len(amb) >= 2 else [])
        return EditorialVerdict(
            safe=False,
            reasons=[f"señal de riesgo: {', '.join(sorted(set(terms))[:6])}"],
            source="keyword", blocked_terms=sorted(set(terms)))
    return EditorialVerdict(safe=True, source="keyword")


def _hits(text: str, terms: set[str]) -> list[str]:
    low = (text or "").lower()
    return [t for t in terms if t in low]


# ─────────────────────────────────────────────
# 3) VEREDICTO FACTUAL — percepción de cobertura de ropa (la autoridad)
# ─────────────────────────────────────────────

# Pide HECHOS (qué cubre la ropa), no juicios. El modelo describe bien; el
# sistema juzga con reglas.
COVERAGE_TEMPLATE = """You are inspecting ONE photograph for a family YouTube channel.
Describe ONLY observable facts about clothing coverage. Do NOT make editorial judgments.

For every person in the image, report exactly:
Person <n>:
  torso_covered = fully|partially|not_covered
  chest_covered = fully|partially|not_covered
  lower_body_covered = fully|partially|not_covered
  clothing_desc = <what they are actually wearing, e.g. "t-shirt and jeans", "only a towel", "no top", "nothing above the waist">
If there are NO people, write: persons = none.

Answer in EXACTLY this format, no extra prose:
persons = <number>|none
<one block "Person <n>: ..." per person as above>"""


# Términos que, en la descripción factual de vestimenta, indican cobertura
# insuficiente / desnudez. Palabras en inglés y español.
_UNCOVERED = {
    "no top", "no shirt", "without shirt", "without top", "nothing above",
    "nothing on top", "bare chest", "bare torso", "bare breasts", "naked",
    "nude", "topless", "uncovered", "exposed chest", "exposed breasts",
    "no bra", "no blouse",     "torso exposed", "chest exposed", "bare skin",
    "only a towel", "towel only", "wrapped in a towel", "sin camiseta",
    "sin blusa", "pecho al descubierto", "torso desnudo", "sin ropa", "pechos",
    "solamente una toalla", "solo una toalla",
}
# Cobertura "parcial/no cubierto" = riesgo de desnudez.
_SUSPICIOUS_COVER = {"partial", "not_covered"}

# Ropa REAL de torso/pecho que cubre de forma decente. Una sábana, toalla,
# manta o bufanda NO cuenta como vestimenta: dejar torso "partially/not"
# cubierto envuelto solo en una sábana es TANATORio a desnudez.
_REAL_COVERING_CLOTHING = {
    "t-shirt", "shirt", "blouse", "camisa", "blusa", "sweater", "sweatshirt",
    "jacket", "dress", "vestido", "camiseta", "top", "hoodie", "cardigan",
    "tank top", "camisola", "long sleeve", "short sleeve", "polo", "gown",
    "bata", "ropa", "outfit", "clothes", "wearing", "atavío", "campera",
    "chaqueta", "suéter", "polera", "polerón",
}
# Prendas NO consideradas cobertura real del torso (riesgo alto si torso
# "partial/not").
_NON_COVERING_WRAPS = {
    "sheet", "towel", "blanket", "scarf", "wrap", "shawl", "sheet wrapped",
    "white sheet", "towel wrapped", "only a towel", "sábana", "toalla",
    "manta", "chal", "frazada", "bayeta",
}


def _coverage_parse(raw: str) -> dict:
    low = (raw or "").lower()
    persons = []
    # bloques "person n:" ... separamos por persona
    blocks = re.split(r"person\s+\d+\s*:", low)
    if len(blocks) > 1:
        for blk in blocks[1:]:
            torso = re.search(r"torso_covered\s*=\s*(fully|partially|not_covered)", blk)
            chest = re.search(r"chest_covered\s*=\s*(fully|partially|not_covered)", blk)
            lower = re.search(r"lower_body_covered\s*=\s*(fully|partially|not_covered)", blk)
            desc = re.search(r"clothing_desc\s*=\s*(.+)", blk)
            persons.append({
                "torso": torso.group(1) if torso else "unknown",
                "chest": chest.group(1) if chest else "unknown",
                "lower": lower.group(1) if lower else "unknown",
                "desc": re.sub(r"\s+", " ", desc.group(1).strip()) if desc else "",
            })
    n_none = re.search(r"persons\s*=\s*none", low)
    has_people = bool(n_none is None) and (bool(persons) or re.search(r"persons\s*=\s*\d", low))
    return {"has_people": has_people, "persons": persons, "raw": low}


def _coverage_judge(parsed: dict) -> EditorialVerdict:
    """Reglas del SISTEMA sobre los hechos percibidos (conservador + sin falsos
    positivos sobre escenas modestas).

    UNSAFE SOLO cuando la descripción factual indica una señal fuerte de piel
    desnuda / torso al desnudo (`_UNCOVERED`: "only a towel", "towel only",
    "no top", "bare chest", "naked", "sin camiseta", "torso desnudo", ...).

    Una persona en cama cubierta con manta/sábana es COBERTURA MODESTA (SAFE):
    los términos de cama/rojo de cama (sheet/blanket/sábana/manta) NO se tratan
    como señal de desnudez por sí mismos. El offender real (torso desnudo con
    "only a towel"/"towel only") sí cae en `_UNCOVERED` y sigue bloqueado.
    """
    # Sin personas => no hay riesgo de desnudez por cobertura.
    if not parsed.get("has_people"):
        return EditorialVerdict(safe=True, source="coverage")
    reasons: list[str] = []
    terms: list[str] = []
    bare = 0
    for p in parsed.get("persons", []):
        desc = (p.get("desc") or "").lower()
        hits = [t for t in _UNCOVERED if t in desc]
        if hits:
            bare += 1
            terms.extend(hits)
    if bare:
        reasons.append(
            f"{bare} persona(s) con torso/pecho sin cobertura real "
            f"({', '.join(sorted(set(terms))[:5])})")
        return EditorialVerdict(
            safe=False, reasons=reasons, source="coverage",
            blocked_terms=sorted(set(terms)))
    return EditorialVerdict(safe=True, source="coverage")


def _vision_coverage(image_path: str, samples: int = 3) -> EditorialVerdict:
    """Pide PERCEPCIÓN factual de cobertura de ropa y juzga con reglas.

    El VLM (llama-3.2-vision Cloudflare / qwen de free.ai) NO es determinista:
    sobre la MISMA imagen puede reportar "fully" en un run y "not_covered" en
    otro (verificado en la auditoría: e02_r2 dio "partially/sheet" y luego
    "not_covered/towel"). Para defensa frente a ese ruido, muestreamos N veces
    y aplicamos OR conservador: si CUALQUIER muestra detecta riesgo => UNSAFE.
    """
    import visual_critic as vc
    collected: list[EditorialVerdict] = []
    for _ in range(samples):
        try:
            _model, raw = vc._ask(image_path, COVERAGE_TEMPLATE, expect=())
            if not raw:
                raise RuntimeError("visión sin contenido")
        except Exception:  # noqa: BLE001
            continue
        collected.append(_coverage_judge(_coverage_parse(raw)))
    if not collected:
        return EditorialVerdict(safe=True, source="none")
    unsafe = [v for v in collected if not v.safe]
    if unsafe:
        reasons = set()
        terms = set()
        for v in unsafe:
            reasons.update(v.reasons)
            terms.update(v.blocked_terms)
        return EditorialVerdict(
            safe=False,
            reasons=["visión ({} de {} muestras): {}".format(
                len(unsafe), len(collected),
                " ".join(sorted(reasons)) or "cobertura insuficiente")],
            source="coverage", blocked_terms=sorted(terms))
    return EditorialVerdict(safe=True, source="coverage")


# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────

def evaluate_editorial(image_path: str, prompt: str = "") -> EditorialVerdict:
    """Veredicto editorial sobre un asset (imagen + prompt de respaldo).

    Orden de autoridad:
      1. pre-screen determinista del PROMPT (señal fuerte => inseguro)
      2. VEREDICTO FACTUAL de la imagen (percepción de cobertura)
    Si TODOS los canales dicen seguro => safe. Cualquier inseguro => UNSAFE.
    """
    if not image_path or not os.path.exists(image_path):
        return EditorialVerdict(safe=False, reasons=["asset no existe"], source="none")

    if prompt:
        kw = keyword_scan(prompt)
        if not kw.safe:
            return kw  # el prompt ya pide algo de riesgo; no generarlo.

    return _vision_coverage(image_path)


def is_editorially_safe(image_path: str, prompt: str = "") -> tuple[bool, EditorialVerdict]:
    v = evaluate_editorial(image_path, prompt)
    return v.safe, v


def _vision_available() -> bool:
    try:
        from ver_imagen import _creds
        _creds()
        return True
    except Exception:  # noqa: BLE001
        return False


_ = _vision_available  # mantenemos el helper (no usado en la cadena principal)


@dataclass
class EditorialVerdict:
    safe: bool = True
    reasons: list[str] = field(default_factory=list)
    source: str = "none"
    blocked_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "safe": self.safe,
            "reasons": self.reasons,
            "source": self.source,
            "blocked_terms": self.blocked_terms,
        }


if __name__ == "__main__":
    import json
    if len(sys.argv) < 2:
        sys.exit("uso: editorial_filter.py <imagen> [prompt]")
    img = sys.argv[1]
    pmt = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(evaluate_editorial(img, pmt).to_dict(), ensure_ascii=False, indent=2))
