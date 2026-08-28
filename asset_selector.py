"""
asset_selector.py — Selector inteligente de assets (Pexels) basado en SceneBrief.

Capa de inteligencia entre SceneBrief y Pexels:
  SceneBrief → queries → Pexels candidatos → filtros → ranking → mejor candidato

NO descarga automáticamente. Solo selecciona y rankea.
NO usa IA visual ni vision models todavía.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

from scene_brief import SceneBrief, NarrativeRole


# ─────────────────────────────────────────────
# Pesos de scoring (calibrables)
# ─────────────────────────────────────────────

WEIGHTS = {
    "narrative_relevance": 25,
    "action_match": 20,
    "composition": 15,
    "technical_quality": 10,
    "text_space": 10,
    "emotional_fit": 5,
    "continuity": 5,
    "diversity": 5,
}
# penalties are subtracted from total, not weighted

# ─────────────────────────────────────────────
# Diccionarios de mapeo emoción → acción observable
# ─────────────────────────────────────────────

EMOTION_TO_ACTION = {
    "agotamiento": ["sitting down heavily", "placing keys slowly", "leaning against wall",
                    "staring at phone", "rubbing eyes", "exhaling deeply"],
    "ansiedad": ["wringing hands", "checking phone repeatedly", "pacing",
                 "fidgeting with objects", "looking at clock"],
    "esperanza": ["opening window", "looking at sunrise", "smiling softly",
                  "stepping outside", "reaching toward light"],
    "tristeza": ["sitting alone", "looking at rain", "holding old photo",
                 "staring at empty cup", "walking slowly"],
    "culpa": ["looking down", "avoiding eye contact", "covering face",
              "turning away", "clenching fists"],
    "libertad": ["walking forward", "arms open wide", "looking at horizon",
                 "removing constraint", "stepping into light"],
    "confianza": ["steady hands", "firm handshake", "standing tall",
                  "looking straight ahead", "placing hand on heart"],
    "soledad": ["empty chair", "single cup on table", "person at window",
                "walking alone on street", "sitting on bench"],
    "relación": ["two phones on table", "person typing message", "looking at photo",
                 "sitting on bed edge", "two cups one untouched"],
    "perdón": ["open hands on table", "releasing object", "turning page",
               "walking away calmly", "placing flower"],
    "dolor": ["hand on chest", "head in hands", "gripping armrest",
              "looking at old wound", "leaning forward"],
}

# ─────────────────────────────────────────────
# Action keywords (verbos observables)
# ─────────────────────────────────────────────

ACTION_KEYWORDS = {
    "escribir": ["typing", "writing", "texting", "messaging"],
    "borrar": ["deleting", "erasing", "removing"],
    "esperar": ["waiting", "sitting", "checking time", "looking around"],
    "caminar": ["walking", "stepping", "moving forward"],
    "mirar": ["looking", "staring", "gazing", "watching"],
    "sostener": ["holding", "gripping", "clutching", "carrying"],
    "abrir": ["opening", "uncovering", "revealing"],
    "cerrar": ["closing", "covering", "hiding"],
    "sentar": ["sitting", "resting", "settling"],
    "parar": ["standing", "rising", "getting up"],
    "llorar": ["crying", "tears", "wiping eyes"],
    "pensar": ["thinking", "contemplating", "reflecting", "staring into distance"],
    "hablar": ["talking", "speaking", "conversing"],
    "callar": ["silence", "still", "quiet", "motionless"],
    "soltar": ["releasing", "letting go", "dropping gently"],
    "apilar": ["stacking", "organizing", "arranging"],
    "frotar": ["rubbing", "wringing", "clenching"],
}

# ─────────────────────────────────────────────
# Penalties anti-slop
# ─────────────────────────────────────────────

PENALTIES = {
    "looking_at_camera": -15,
    "stock_pose": -10,
    "corporate_handshake": -20,
    "pointing_at_camera": -15,
    "ad_smile": -10,
    "too_generic": -8,
    "too_dark": -5,
    "excessive_bokeh": -3,
    "confusing_composition": -5,
    "subject_cut_off": -8,
    "repeated_scene": -12,
}


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────

@dataclass
class AssetCandidate:
    """Candidato de video de Pexels con metadata completa."""
    id: int | str = 0
    url: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    orientation: str = "portrait"
    fps: float = 0.0
    file_size: int = 0
    thumbnail: str = ""
    quality: str = ""
    source: str = "pexels"

    # Campos derivados (llenados por el sistema)
    query_used: str = ""
    orientation_match: bool = False

    @classmethod
    def from_pexels(cls, data: dict) -> AssetCandidate:
        """Crea desde un dict de search_videos_raw()."""
        return cls(
            id=data.get("id", 0),
            url=data.get("url", ""),
            duration=data.get("duration", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            orientation=data.get("orientation", "portrait"),
            fps=data.get("fps", 0),
            file_size=data.get("file_size", 0),
            thumbnail=data.get("thumbnail", ""),
            quality=data.get("quality", ""),
            source=data.get("source", "pexels"),
        )


@dataclass
class AssetScore:
    """Score detallado de un candidato contra un SceneBrief."""
    total: float = 0.0             # 0-100
    narrative_relevance: float = 0.0  # 0-25
    action_match: float = 0.0         # 0-20
    composition: float = 0.0          # 0-15
    technical_quality: float = 0.0    # 0-10
    text_space: float = 0.0           # 0-10
    emotional_fit: float = 0.0        # 0-5
    continuity: float = 0.0           # 0-5
    diversity: float = 0.0            # 0-5
    penalties: float = 0.0            # negativo
    reasons: list[str] = field(default_factory=list)

    def compute_total(self):
        """Recalcula el total desde los componentes."""
        raw = (self.narrative_relevance + self.action_match +
               self.composition + self.technical_quality +
               self.text_space + self.emotional_fit +
               self.continuity + self.diversity)
        self.total = max(0.0, min(100.0, raw + self.penalties))
        return self.total


@dataclass
class AssetSelection:
    """Resultado de la selección de assets para una escena."""
    selected: AssetCandidate | None = None
    ranked_candidates: list[tuple[AssetCandidate, AssetScore]] = field(default_factory=list)
    rejected_candidates: list[tuple[AssetCandidate, str]] = field(default_factory=list)
    query_used: str = ""
    queries_tried: list[str] = field(default_factory=list)
    confidence: float = 0.0
    status: str = "ok"  # ok | low_confidence | no_candidates | no_key
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serializa a dict plano."""
        d = {
            "selected_id": self.selected.id if self.selected else None,
            "selected_url": self.selected.url if self.selected else None,
            "confidence": self.confidence,
            "status": self.status,
            "queries_tried": self.queries_tried,
            "query_used": self.query_used,
            "reasons": self.reasons,
            "ranked_count": len(self.ranked_candidates),
            "rejected_count": len(self.rejected_candidates),
        }
        if self.ranked_candidates:
            d["top_scores"] = [
                {"id": c.id, "score": s.total, "reasons": s.reasons[:3]}
                for c, s in self.ranked_candidates[:3]
            ]
        return d


# ─────────────────────────────────────────────
# Generación de queries
# ─────────────────────────────────────────────

def generate_queries(brief: SceneBrief) -> list[str]:
    """
    Genera 3-5 queries de búsqueda Pexels desde un SceneBrief.

    Estrategia:
    1. action + setting (observable)
    2. visual_event simplificado
    3. sujeto + acción
    4. emoción → acción observable
    5. pexels_queries existentes (si las hay)

    NO usa emociones abstractas como queries.
    """
    queries = []
    action = brief.action.strip() if brief.action else ""
    setting = brief.setting.strip() if brief.setting else ""
    subject = brief.subject.strip() if brief.subject else ""
    visual_event = brief.visual_event.strip() if brief.visual_event else ""
    emotional_core = brief.emotional_core.strip() if brief.emotional_core else ""

    # Q1: action + setting (si ambos existen)
    if action and setting:
        setting_simple = _simplify_setting(setting)
        queries.append(f"{_translate_action(action)} {setting_simple}".strip())

    # Q2: visual_event simplificado
    if visual_event:
        simplified = _simplify_visual_event(visual_event)
        if simplified:
            queries.append(simplified)

    # Q3: subject + action
    if subject and action:
        queries.append(f"{_translate_subject(subject)} {_translate_action(action)}".strip())

    # Q4: emoción → acción observable
    if emotional_core:
        emotion_words = _extract_emotion_words(emotional_core)
        for emo in emotion_words:
            actions = EMOTION_TO_ACTION.get(emo, [])
            if actions:
                queries.append(actions[0])
                break

    # Q5: pexels_queries existentes
    for q in (brief.pexels_queries or []):
        if q.strip() and q.strip() not in queries:
            queries.append(q.strip())

    # Deduplicar manteniendo orden
    seen = set()
    unique = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower not in seen and len(q_lower) > 2:
            seen.add(q_lower)
            unique.append(q)

    return unique[:5] if unique else ["person thinking"]


def _simplify_setting(setting: str) -> str:
    """Extrae la palabra clave del setting."""
    setting_lower = setting.lower()
    for keyword in ["cocina", "kitchen"]:
        if keyword in setting_lower:
            return "at home"
    for keyword in ["habitación", "bedroom", "cama"]:
        if keyword in setting_lower:
            return "at home"
    for keyword in ["sala", "living room"]:
        if keyword in setting_lower:
            return "at home"
    for keyword in ["pasillo", "hallway"]:
        if keyword in setting_lower:
            return "indoors"
    for keyword in ["mesa", "table"]:
        if keyword in setting_lower:
            return "at table"
    for keyword in ["calle", "street", "acera"]:
        if keyword in setting_lower:
            return "outdoors"
    for keyword in ["lluvia", "rain"]:
        if keyword in setting_lower:
            return "rain"
    for keyword in ["ventana", "window"]:
        if keyword in setting_lower:
            return "near window"
    for keyword in ["oficina", "office"]:
        if keyword in setting_lower:
            return "at office"
    return "indoors"


def _translate_action(action: str) -> str:
    """Traduce acciones en español a keywords Pexels en inglés."""
    action_lower = action.lower()
    for spanish, english_keys in ACTION_KEYWORDS.items():
        if spanish in action_lower:
            return english_keys[0]
    # Fallback: tomar las primeras 2-3 palabras significativas
    words = [w for w in action.split() if len(w) > 3]
    return " ".join(words[:2]) if words else "person"


def _translate_subject(subject: str) -> str:
    """Traduce sujetos a keywords Pexels."""
    subject_lower = subject.lower()
    if any(w in subject_lower for w in ["mujer", "woman", "chica"]):
        return "woman"
    if any(w in subject_lower for w in ["manos", "hands"]):
        return "hands"
    if any(w in subject_lower for w in ["hombre", "man", "chico"]):
        return "person"
    if any(w in subject_lower for w in ["persona", "person"]):
        return "person"
    return "person"


def _simplify_visual_event(event: str) -> str:
    """Convierte visual_event en una query simple y observable."""
    event_lower = event.lower()
    # Buscar patrones comunes
    for pattern, replacement in [
        ("mujer sentada", "woman sitting"),
        ("mujer escribiendo", "woman writing"),
        ("mujer caminando", "woman walking"),
        ("mujer abriendo", "woman opening"),
        ("mujer mirando", "woman looking"),
        ("mujer sosteniendo", "woman holding"),
        ("manos abiertas", "open hands"),
        ("mano dejando", "hand placing"),
        ("persona sentada", "person sitting"),
        ("persona escribiendo", "person writing"),
        ("persona caminando", "person walking"),
    ]:
        if pattern in event_lower:
            return replacement
    # Fallback: primeras palabras clave
    words = event_lower.split()
    keywords = [w for w in words if len(w) > 4 and w not in
                ("una", "uno", "el", "la", "lo", "los", "las", "de", "del",
                 "en", "con", "por", "para", "que", "se", "sus")]
    return " ".join(keywords[:4]) if keywords else ""


def _extract_emotion_words(text: str) -> list[str]:
    """Extrae palabras de emoción de un texto."""
    text_lower = text.lower()
    found = []
    for emo in EMOTION_TO_ACTION:
        if emo in text_lower:
            found.append(emo)
    return found


# ─────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────

def score_candidate(
    candidate: AssetCandidate,
    brief: SceneBrief,
    previous_assets: list[AssetCandidate] | None = None,
    continuity_context: dict | None = None,
) -> AssetScore:
    """
    Evalúa un candidato contra un SceneBrief.

    Devuelve AssetScore con desglose y total 0-100.
    """
    score = AssetScore()
    reasons = []

    # ── NARRATIVE RELEVANCE (0-25) ──
    nr = _score_narrative_relevance(candidate, brief)
    score.narrative_relevance = nr
    if nr >= 20:
        reasons.append(f"alta relevancia narrativa ({nr:.0f})")
    elif nr >= 10:
        reasons.append(f"relevancia moderada ({nr:.0f})")
    else:
        reasons.append(f"baja relevancia narrativa ({nr:.0f})")

    # ── ACTION MATCH (0-20) ──
    am = _score_action_match(candidate, brief)
    score.action_match = am
    if am >= 15:
        reasons.append(f"acción bien coincidente ({am:.0f})")
    elif am < 8:
        reasons.append(f"acción débil ({am:.0f})")

    # ── COMPOSITION (0-15) ──
    comp = _score_composition(candidate, brief)
    score.composition = comp
    if comp >= 12:
        reasons.append(f"buena composición ({comp:.0f})")

    # ── TECHNICAL QUALITY (0-10) ──
    tq = _score_technical(candidate)
    score.technical_quality = tq

    # ── TEXT SPACE (0-10) ──
    ts = _score_text_space(candidate, brief)
    score.text_space = ts
    if brief.text_space and ts >= 7:
        reasons.append(f"buen espacio para texto ({ts:.0f})")

    # ── EMOTIONAL FIT (0-5) ──
    ef = _score_emotional_fit(candidate, brief)
    score.emotional_fit = ef

    # ── CONTINUITY (0-5) ──
    cont = _score_continuity(candidate, brief, continuity_context)
    score.continuity = cont

    # ── DIVERSITY (0-5) ──
    div = _score_diversity(candidate, previous_assets)
    score.diversity = div
    if div < 2 and previous_assets:
        reasons.append("poca diversidad vs escenas anteriores")

    # ── PENALTIES ──
    pen, pen_reasons = _compute_penalties(candidate, brief, previous_assets)
    score.penalties = pen
    reasons.extend(pen_reasons)

    score.reasons = reasons
    score.compute_total()
    return score


def _score_narrative_relevance(candidate: AssetCandidate, brief: SceneBrief) -> float:
    """Evalúa si el candidato cuenta visualmente lo que la escena necesita."""
    score = 5.0  # base

    # Orientación correcta = bonus
    if candidate.orientation == "portrait":
        score += 3.0

    # Duración adecuada
    if brief.duration > 0:
        ratio = candidate.duration / brief.duration
        if 0.8 <= ratio <= 2.0:
            score += 3.0
        elif ratio > 2.0:
            score += 1.0

    # Presencia de palabras clave del visual_event en la query usada
    if candidate.query_used:
        query_lower = candidate.query_used.lower()
        event_words = brief.visual_event.lower().split() if brief.visual_event else []
        matches = sum(1 for w in event_words if w in query_lower and len(w) > 3)
        score += min(matches * 2, 8)

    # Setting compatibility
    setting_lower = brief.setting.lower() if brief.setting else ""
    if candidate.query_used:
        q = candidate.query_used.lower()
        if any(k in setting_lower for k in ["cocina", "kitchen"]) and "home" in q:
            score += 3.0
        if any(k in setting_lower for k in ["lluvia", "rain"]) and "rain" in q:
            score += 3.0
        if any(k in setting_lower for k in ["ventana", "window"]) and "window" in q:
            score += 3.0

    return min(25.0, score)


def _score_action_match(candidate: AssetCandidate, brief: SceneBrief) -> float:
    """Evalúa si la acción del candidato coincide con la acción de la escena."""
    score = 3.0  # base

    action_lower = brief.action.lower() if brief.action else ""
    query_lower = candidate.query_used.lower() if candidate.query_used else ""

    # Buscar verbs en action y query
    for spanish, english_keys in ACTION_KEYWORDS.items():
        if spanish in action_lower:
            for ek in english_keys:
                if ek in query_lower:
                    score += 12.0  # match fuerte
                    return min(20.0, score)
            # No encontró el verbo exacto
            score += 2.0
            break

    # Bonus por	query que contieneacción traducida
    if query_lower:
        translated = _translate_action(brief.action)
        if translated and translated in query_lower:
            score += 8.0

    return min(20.0, score)


def _score_composition(candidate: AssetCandidate, brief: SceneBrief) -> float:
    """Evalúa calidad composicional del candidato."""
    score = 5.0

    # Resolución adecuada
    if candidate.width >= 1080 and candidate.height >= 1920:
        score += 5.0
    elif candidate.width >= 720:
        score += 2.0

    # FPS adecuado
    if candidate.fps >= 24:
        score += 2.0

    # Profundidad (proxy: resolución alta = mejor calidad)
    if candidate.width >= 1920:
        score += 3.0

    return min(15.0, score)


def _score_technical(candidate: AssetCandidate) -> float:
    """Evalúa calidad técnica básica."""
    score = 3.0
    if candidate.quality == "hd":
        score += 3.0
    if candidate.fps >= 24:
        score += 2.0
    if candidate.file_size > 0:
        # No demasiado grande (100MB max)
        if candidate.file_size < 100_000_000:
            score += 2.0
    return min(10.0, score)


def _score_text_space(candidate: AssetCandidate, brief: SceneBrief) -> float:
    """Evalúa si hay espacio para texto en pantalla."""
    if not brief.text_space:
        return 7.0  # neutral si no se especifica

    score = 5.0
    # Videos verticales tienen más espacio vertical para texto
    if candidate.orientation == "portrait":
        score += 3.0
    # Resolución alta = más espacio para texto nítido
    if candidate.height >= 1920:
        score += 2.0

    return min(10.0, score)


def _score_emotional_fit(candidate: AssetCandidate, brief: SceneBrief) -> float:
    """Evalúa si la emoción del candidato encaja con la escena."""
    if not brief.emotional_core:
        return 3.0

    score = 2.0
    emotional_lower = brief.emotional_core.lower()

    # Keywords positivos en la query
    positive_words = ["calm", "peaceful", "quiet", "gentle", "soft", "warm", "light"]
    negative_words = ["dark", "storm", "cry", "pain", "angry", "tense"]

    query_lower = candidate.query_used.lower() if candidate.query_used else ""

    for w in positive_words:
        if w in query_lower:
            if any(e in emotional_lower for e in ["esperanza", "calma", "paz", "confianza"]):
                score += 2.0
                break

    for w in negative_words:
        if w in query_lower:
            if any(e in emotional_lower for e in ["dolor", "tristeza", "culpa", "ansiedad"]):
                score += 2.0
                break

    return min(5.0, score)


def _score_continuity(
    candidate: AssetCandidate,
    brief: SceneBrief,
    context: dict | None,
) -> float:
    """Evalúa continuidad con escenas del mismo grupo."""
    if not context or not brief.continuity_group:
        return 3.0  # neutral

    score = 3.0
    # Si hay contexto del grupo, verificar compatibilidad
    group = brief.continuity_group
    prev_group = context.get("last_group", "")
    if group == prev_group:
        # Mismo grupo = favorecer consistencia visual
        prev_orientation = context.get("last_orientation", "")
        if candidate.orientation == prev_orientation:
            score += 2.0

    return min(5.0, score)


def _score_diversity(
    candidate: AssetCandidate,
    previous_assets: list[AssetCandidate] | None,
) -> float:
    """Evalúa diversidad vs escenas anteriores."""
    if not previous_assets:
        return 5.0  # primera escena, máxima diversidad

    score = 5.0

    # Verificar si el candidato es muy similar a los anteriores
    for prev in previous_assets[-3:]:  # últimas 3 escenas
        # Mismo sujeto (query similar)
        if prev.query_used and candidate.query_used:
            prev_words = set(prev.query_used.lower().split())
            curr_words = set(candidate.query_used.lower().split())
            overlap = len(prev_words & curr_words)
            if overlap >= 3:
                score -= 2.0

        # Mismo tipo de plano
        if prev.orientation == candidate.orientation:
            score -= 0.5

    return max(0.0, min(5.0, score))


def _compute_penalties(
    candidate: AssetCandidate,
    brief: SceneBrief,
    previous_assets: list[AssetCandidate] | None,
) -> tuple[float, list[str]]:
    """Computa penalizaciones anti-slop."""
    total_penalty = 0.0
    reasons = []

    # Repetición de escena
    if previous_assets:
        for prev in previous_assets[-3:]:
            if prev.id == candidate.id:
                total_penalty += PENALTIES["repeated_scene"]
                reasons.append("candidato repetido de escena anterior")
                break

    # Pexels no da metadata de pose/rostro — estas penalizaciones
    # se activarán cuando haya vision model
    # Por ahora solo penalizamos por resolución muy baja
    if candidate.width < 720 or candidate.height < 1280:
        total_penalty += 5
        reasons.append("resolución baja (< 720p)")

    return total_penalty, reasons


# ─────────────────────────────────────────────
# Confidence
# ─────────────────────────────────────────────

def compute_confidence(score: AssetScore, total_candidates: int) -> float:
    """
    Calcula confidence del candidato seleccionado.

    Criterios:
    - score.total como base
    - Bonus por tener varios candidatos (selección competitiva)
    - Penalty si hay pocos candidatos
    """
    base = score.total / 100.0  # normalizar a 0-1

    # Bonus por competencia
    if total_candidates >= 5:
        bonus = 0.05
    elif total_candidates >= 3:
        bonus = 0.02
    else:
        bonus = -0.05

    # Penalty si el score es bajo
    if base < 0.5:
        penalty = -0.1
    else:
        penalty = 0.0

    confidence = max(0.0, min(1.0, base + bonus + penalty))
    return round(confidence, 2)


def confidence_label(confidence: float) -> str:
    """Devuelve una etiqueta descriptiva de la confidence."""
    if confidence >= 0.90:
        return "muy_fuerte"
    elif confidence >= 0.70:
        return "bueno"
    elif confidence >= 0.50:
        return "usable_pero_dudoso"
    else:
        return "material_debil"


# ─────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────

def select_asset(
    brief: SceneBrief,
    previous_assets: list[AssetCandidate] | None = None,
    continuity_context: dict | None = None,
    fetch_fn=None,
) -> AssetSelection:
    """
    Selecciona el mejor asset Pexels para un SceneBrief.

    Args:
        brief: SceneBrief con la información de la escena
        previous_assets: assets ya seleccionados (para diversidad)
        continuity_context: info del grupo de continuidad
        fetch_fn: función para buscar en Pexels (default: search_videos_raw)

    Returns:
        AssetSelection con el mejor candidato, ranking, y metadata
    """
    # Importar fetch_fn por defecto
    if fetch_fn is None:
        try:
            from pexels_stock import search_videos_raw, available
            if not available():
                return AssetSelection(
                    status="no_key",
                    reasons=["no hay clave Pexels disponible"],
                )
            fetch_fn = search_videos_raw
        except ImportError:
            return AssetSelection(
                status="no_key",
                reasons=["pexels_stock.py no disponible"],
            )

    # Generar queries
    queries = generate_queries(brief)

    if not queries:
        return AssetSelection(
            status="no_candidates",
            reasons=["no se pudieron generar queries"],
            queries_tried=[],
        )

    # Buscar candidatos para cada query
    all_candidates: list[AssetCandidate] = []
    for q in queries:
        raw_results = fetch_fn(q, per_page=10)
        for raw in raw_results:
            c = AssetCandidate.from_pexels(raw)
            c.query_used = q
            c.orientation_match = (c.orientation == "portrait")
            all_candidates.append(c)

    if not all_candidates:
        return AssetSelection(
            status="no_candidates",
            reasons=["Pexels no devolvió candidatos para ninguna query"],
            queries_tried=queries,
        )

    # Filtro técnico básico
    valid = []
    rejected = []
    for c in all_candidates:
        rejection_reason = _technical_rejection(c, brief)
        if rejection_reason:
            rejected.append((c, rejection_reason))
        else:
            valid.append(c)

    if not valid:
        return AssetSelection(
            status="no_candidates",
            reasons=["todos los candidatos fallaron el filtro técnico"],
            queries_tried=queries,
            rejected_candidates=rejected,
        )

    # Ranking
    scored: list[tuple[AssetCandidate, AssetScore]] = []
    for c in valid:
        s = score_candidate(c, brief, previous_assets, continuity_context)
        scored.append((c, s))

    scored.sort(key=lambda x: x[1].total, reverse=True)

    # Seleccionar el mejor
    best_candidate, best_score = scored[0]
    confidence = compute_confidence(best_score, len(valid))

    status = "ok"
    if confidence < 0.50:
        status = "low_confidence"

    return AssetSelection(
        selected=best_candidate,
        ranked_candidates=scored,
        rejected_candidates=rejected,
        query_used=best_candidate.query_used,
        queries_tried=queries,
        confidence=confidence,
        status=status,
        reasons=best_score.reasons,
    )


def _technical_rejection(candidate: AssetCandidate, brief: SceneBrief) -> str | None:
    """Devuelve razón de rechazo técnico o None si es válido."""
    if candidate.duration < 3.0:
        return f"duración insuficiente ({candidate.duration}s)"
    if candidate.width < 480:
        return f"resolución muy baja ({candidate.width}x{candidate.height})"
    if not candidate.url:
        return "sin URL"
    return None


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    from scene_brief import NarrativeRole, MotionType

    print("=" * 60)
    print("ASSET SELECTOR — Test de prueba")
    print("=" * 60)

    brief = SceneBrief(
        scene_id="test_01",
        narrative_role=NarrativeRole.HOOK,
        narration="Dios no te pide que permanezcas atrapado en una relación destructiva.",
        emotional_core="alivio — alguien lo dice en voz alta",
        visual_event="Mujer sentada en el borde de una cama, sosteniendo el teléfono con ambas manos.",
        subject="mujer",
        action="sostener el teléfono sin abrir el mensaje",
        setting="habitación con luz tenue, tarde nublada",
        text_space="upper",
        duration=5.6,
    )

    print(f"Escena: {brief.visual_event[:60]}...")
    print()

    queries = generate_queries(brief)
    print("Queries generadas:")
    for i, q in enumerate(queries):
        print(f"  {i+1}. {q}")
    print()

    print("Buscando en Pexels...")
    selection = select_asset(brief)

    print(f"Estado: {selection.status}")
    print(f"Confidence: {selection.confidence} ({confidence_label(selection.confidence)})")
    print(f"Queries intentadas: {len(selection.queries_tried)}")
    print(f"Candidatos encontrados: {len(selection.ranked_candidates)}")
    print(f"Candidatos rechazados: {len(selection.rejected_candidates)}")

    if selection.selected:
        print(f"\nSELECCIONADO: ID={selection.selected.id}")
        print(f"  URL: {selection.selected.url[:80]}...")
        print(f"  Orientación: {selection.selected.orientation}")
        print(f"  Duración: {selection.selected.duration}s")
        print(f"  Resolución: {selection.selected.width}x{selection.selected.height}")
        print(f"  Query: {selection.query_used}")

        print("\nTOP 3 CANDIDATOS:")
        for i, (c, s) in enumerate(selection.ranked_candidates[:3]):
            print(f"  {i+1}. Score={s.total:.1f} | {c.orientation} | {c.duration}s | {c.width}x{c.height}")
            print(f"     Query: {c.query_used}")
            for r in s.reasons[:3]:
                print(f"     • {r}")
    else:
        print("\nNo se seleccionó ningún candidato.")
        for r in selection.reasons:
            print(f"  • {r}")
