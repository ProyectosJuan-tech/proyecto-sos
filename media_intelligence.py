"""media_intelligence.py — V2.7 INTELIGENCIA VISUAL DE MEDIOS

Tres capacidades aditivas, SIN red y deterministas, que viven ENCIMA de las
capas existentes (no las duplican):

  1. VISUAL KEYWORDS INTELLIGENCE
     Convierte cada escena narrativa en información visual utilizable:
     sujetos, objetos, acciones, lugares, situación, emoción visual, símbolos,
     keywords de búsqueda para stock y conceptos descriptivos para IA.
     Las keywords están SUBORDINADAS al evento narrativo (no al revés): se
     derivan del visual_event + subject/action/setting/symbol/role.

  2. MEDIA SOURCE INTELLIGENCE
     Decide qué fuente conviene para cada escena (AI / PHOTO_STOCK /
     VIDEO_STOCK) a partir del contenido narrativo. Reutiliza el fit de
     `media_director._medium_fit` para NO duplicar la heurística de calidad.
     Produce una estrategia con `preferred_source` + `alternatives` + `reason`.

  3. CANDIDATE SELECTION INTELLIGENCE
     Cuando una fuente devuelve varios candidatos, los puntúa y elige el mejor
     reutilizando `asset_selector.score_candidate` (scoring 0-100 por dimensión)
     + diversidad respecto de escenas anteriores. Separa claramente los pasos:
     descubrir candidatos → puntuar → seleccionar → (el Quality Gate sigue siendo
     la última defensa de calidad; aquí NO se reemplaza).

PRINCIPIO DE CONSUMO:
  Esta capa NO agrega llamadas externas. La búsqueda de candidatos sigue usando
  el caché Pexels + early-stop + máximo de queries de `asset_selector`.
  Si ya hay suficientes candidatos buenos, detiene la búsqueda.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from scene_brief import SceneBrief, PreferredSource, NarrativeRole


# ─────────────────────────────────────────────
# 1) VISUAL KEYWORDS INTELLIGENCE
# ─────────────────────────────────────────────

# Vocabulario ligero ES↔EN para etiquetar el evento visible. No es NLP; sirve
# para agrupar los términos del evento en categorías estructurales útiles.
_PERSON_TERMS = (
    "mujer", "hombre", "persona", "ella", "él", "woman", "man", "person",
    "ella", "padre", "madre", "niño", "niña", "chica", "chico", "girl", "boy",
)
_HANDS_TERMS = (
    "manos", "mano", "dedos", "hand", "hands", "fingers", "escribir", "writing",
    "teclear", "typing", "sostener", "holding", "gripping", "borrar", "eras",
    "pasar hojas", "turning pages", "agarra", "garra",
)
_OBJECT_TERMS = (
    "taza", "cup", "mug", "libro", "book", "carta", "letter", "tarjeta", "card",
    "teléfono", "phone", "celular", "smartphone", "móvil", "agenda", "planner",
    "calendario", "calendar", "reloj", "watch", "bolso", "bag", "shopping",
    "compra", "planta", "plant", "flor", "flower", "zapatilla", "shoe", "vaso",
    "glass", "mesa", "table", "teclado", "keyboard", "notas", "notes", "lista",
    "list", "bolígrafo", "pen", "boli", "pantalla", "screen", "bolsas", "bags",
    "cajas", "boxes", "paquetes", "packages", "cama", "bed", "mensaje", "message",
    "línea", "line", "papel", "paper", "lámpara", "lamp", "sillón", "silla",
    "chair", "palmas", "palma", "palms", "silla", "mesa de luz",
)
_ACTION_TERMS = (
    "revis", "check", "mirar", "looking", "leer", "reading", "escribir",
    "writing", "teclear", "typing", "comprar", "buy", "shopping", "borrar",
    "eras", "repet", "repeat", "llenar", "fill", "vaciar", "empty", "levantar",
    "dejar", "camina", "walk", "sentarse", "sit", "sentada", "cocinar", "cook",
    "beber", "drink", "esperar", "wait",
)
_PLACE_TERMS = (
    "cocina", "kitchen", "habitación", "bedroom", "habitacion", "sala", "living",
    "ventana", "window", "casa", "home", "oficina", "office", "desk", "escritorio",
    "café", "cafe", "cafetería", "mesa", "mesa de luz", "balcón", "balcony",
    "calle", "street", "cocina", "interior", "room", "hall", "pasillo", "corredor",
)
_SYMBOL_TERMS = (
    "vacío", "empty", "vacía", "símbolo", "symbol", "metáfora", "metaphor",
    "luz", "light", "sombra", "shadow", "puerta", "door", "camino", "path",
    "ventana cerrada", "espejo", "mirror", "reloj", "cruces", "muro", "wall",
)
_EMOTION_TERMS = (
    "vacío", "empty", "vacía", "cansancio", "fatiga", "agot", "triste", "sad",
    "ansiosa", "ansioso", "ansiedad", "frustra", "frustrated", "alivio",
    "relief", "calma", "calm", "esperanza", "hope", "light", "serenidad",
    "nostalgia", "melancol", "angustia", "sola", "solo", "alone", "inquietud",
)


@dataclass
class VisualKeywords:
    """Representación visual estructurada de una escena narrativa."""
    subjects: list[str] = field(default_factory=list)
    hands: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    places: list[str] = field(default_factory=list)
    situation: str = ""
    visual_emotion: str = ""
    symbols: list[str] = field(default_factory=list)
    stock_keywords: list[str] = field(default_factory=list)   # frases de búsqueda EN
    ai_concepts: list[str] = field(default_factory=list)      # conceptos para IA

    def to_dict(self) -> dict:
        return {
            "subjects": self.subjects,
            "hands": self.hands,
            "objects": self.objects,
            "actions": self.actions,
            "places": self.places,
            "situation": self.situation,
            "visual_emotion": self.visual_emotion,
            "symbols": self.symbols,
            "stock_keywords": self.stock_keywords,
            "ai_concepts": self.ai_concepts,
        }


def _match_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    low = (text or "").lower()
    hits = []
    for t in terms:
        if t in low and t not in hits:
            hits.append(t)
    return hits


def _split_phrases(event: str) -> list[str]:
    """Divide el evento en frases cortas (subordinado al evento)."""
    out = []
    for part in (event or "").split(","):
        for sub in part.replace(" y ", ", ").replace(" and ", ", ").split(", "):
            sub = sub.strip().strip(".").strip()
            if len(sub) > 2:
                out.append(sub)
    return out or ([event] if event else [])


def derive_visual_keywords(brief: SceneBrief) -> VisualKeywords:
    """Deriva VisualKeywords desde un SceneBrief (subordinado al evento)."""
    event = (brief.visual_event or "").strip()
    subject = (brief.subject or "").strip()
    action = (brief.action or "").strip()
    setting = (brief.setting or "").strip()
    symbol = (brief.symbol or "").strip()
    role = brief.narrative_role
    blend = " ".join([event, subject, action, setting, symbol])

    kw = VisualKeywords()
    kw.situation = event or action or ""

    kw.subjects = _match_terms(blend, _PERSON_TERMS)
    kw.hands = _match_terms(blend, _HANDS_TERMS)
    kw.objects = _match_terms(blend, _OBJECT_TERMS)
    kw.actions = _match_terms(blend, _ACTION_TERMS)
    kw.places = _match_terms(blend, _PLACE_TERMS)
    kw.symbols = _match_terms(blend, _SYMBOL_TERMS)
    emo = _match_terms(blend, _EMOTION_TERMS)
    kw.visual_emotion = emo[0] if emo else ""

    # Keywords de búsqueda para stock: frases EN cortas, de la acción + objeto/campo.
    kw.stock_keywords = _stock_keywords(event, subject, action, setting, kw)

    # Conceptos descriptivos para generación IA: el evento tal cual, enriquecido.
    ai = event
    if setting and setting not in ai:
        ai = f"{ai}, {setting}"
    kw.ai_concepts = [ai] if ai else ["empty calm room"]
    if symbol and symbol not in ai:
        kw.ai_concepts.append(symbol)

    return kw


def _stock_keywords(event, subject, action, setting, kw) -> list[str]:
    """Genera frases de búsqueda Pexels subordinadas al evento. EN, cortas."""
    keys = []
    # Base: acción continua + sujeto/objeto implicado.
    low_event = (event or "").lower()
    low_action = (action or "").lower()

    # Comportamiento repetitivo / gestos de manos.
    if kw.hands or kw.actions or any(w in low_event for w in
                                     ("revis", "repeat", "erasing", "rewriting",
                                      "typing", "check", "borr", "reescrib")):
        if "phone" in low_event or "celular" in low_event or "móvil" in low_event:
            keys.append("woman checking phone distractedly")
        if ("repeat" in low_event or "repet" in low_event or "rewrit" in low_event
                or "borr" in low_event or "reescrib" in low_event
                or "lista" in low_event):
            keys.append("hands rewriting notes")
            keys.append("person repeating same task")
            keys.append("erasing and rewriting a list")
        if "check" in low_event or "revis" in low_event:
            keys.append("woman checking phone")
    if "agenda" in low_event or "planner" in low_event or "calendario" in low_event:
        keys.append("full day planner close up")
        keys.append("agenda busy schedule")
    if "compr" in low_event or "shopping" in low_event or "bolsa" in low_event:
        keys.append("shopping bags stack")
        keys.append("retail therapy")
    if "taza" in low_event or "cup" in low_event or "té" in low_event:
        keys.append("hand holding warm cup")
    if "ventana" in low_event or "window" in low_event:
        keys.append("woman looking out window")
    if "sola" in low_event or "alone" in low_event or "vac" in low_event:
        keys.append("person sitting alone")
    if "cama" in low_event or "bed" in low_event:
        keys.append("empty bed seen from doorway soft light")
    if "mensaje" in low_event or "message" in low_event or "línea" in low_event:
        keys.append("hand writing message on paper")
        keys.append("erasing a line on paper")
    if "palma" in low_event or "palms" in low_event or "abiert" in low_event or "releasing" in low_event:
        keys.append("open palms empty releasing")
    if "lámpara" in low_event or "lamp" in low_event or "papel" in low_event:
        keys.append("desk lamp on paper")
    if "puerta" in low_event and ("luz" in low_event or "light" in low_event):
        keys.append("open doorway to soft light")

    # Fallback CONTEXTUAL (no plantilla fija): deriva del lugar/situación/símbolos
    # de la escena para que cada arquetipo se diferencie, no una frase repetida.
    if not keys:
        if kw.places:
            keys.append(f"{kw.places[0]} interior calm details")
        if kw.symbols and any(w in " ".join(kw.symbols) for w in ("luz", "puerta", "vac")):
            keys.append("open doorway with soft light")
        elif kw.subjects or kw.hands:
            keys.append("person in quiet home honest moment")
        else:
            keys.append("quiet home still objects")

    keys = list(dict.fromkeys([k for k in keys if k]))
    return keys


# ─────────────────────────────────────────────
# 2) MEDIA SOURCE INTELLIGENCE
# ─────────────────────────────────────────────
from media_director import MediumType, _medium_fit, preferred_source_for


@dataclass
class MediaSourceStrategy:
    """Estrategia de fuente para una escena."""
    preferred_source: str = "ai"
    alternatives: list[str] = field(default_factory=list)
    reason: str = ""
    fit_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "preferred_source": self.preferred_source,
            "alternatives": list(self.alternatives),
            "reason": self.reason,
            "fit_scores": {k: round(v, 2) for k, v in self.fit_scores.items()},
        }


def build_media_source_strategy(brief: SceneBrief) -> MediaSourceStrategy:
    """Estrategia de fuente desde el contenido narrativo (sin red).

    Reutiliza media_director._medium_fit para el fit de calidad y arma el
    preferred + alternativas + razón. Es la MISMA heurística que usa el
    media_director, expuesta aquí como estrategia por escena.
    """
    fits = {m.value: _medium_fit(brief, m) for m in MediumType}
    order = sorted(fits.items(), key=lambda kv: kv[1], reverse=True)
    preferred_val = order[0][0] if order else "ai_image"
    alternatives = [v for v, _ in order[1:]] if len(order) > 1 else []

    pref = "ai"
    if preferred_val == "photo_stock":
        pref = "photo_stock"
    elif preferred_val == "video_stock":
        pref = "stock"

    alt_out = []
    for v in alternatives:
        if v == "photo_stock":
            alt_out.append("photo_stock")
        elif v == "video_stock":
            alt_out.append("stock")
        else:
            alt_out.append("ai")

    reason = _strategy_reason(brief, preferred_val, fits)
    return MediaSourceStrategy(
        preferred_source=pref,
        alternatives=[a for a in alt_out if a != pref],
        reason=reason,
        fit_scores=fits,
    )


def _strategy_reason(brief: SceneBrief, preferred_val: str, fits: dict) -> str:
    role = brief.narrative_role
    event = (brief.visual_event or "").lower()
    subj = (brief.subject or "").lower()

    if preferred_val == "ai_image":
        if any(h in event for h in ("símbolo", "symbol", "metáfora", "metaphor",
                                    "espejo", "light", "puerta", "door",
                                    "vacío", "vacía")):
            return "concepto simbólico específico difícil de encontrar en stock"
        if any(h in (event, subj) for h in ("personaje", "same woman", "same man",
                                            "the same", "retrato", "protagonista")):
            return "personaje/continuidad que el stock no puede reproducir"
        if role in (NarrativeRole.HOOK, NarrativeRole.CALLOUT, NarrativeRole.PAYOFF):
            return "composición controlada para el texto (gancho/CTA)"
        return "escena específica con mejor resultado por IA"
    if preferred_val == "video_stock":
        if any(w in event for w in ("camina", "walk", "correr", "run", "lluvia",
                                    "rain", "atardecer", "amanecer", "ventana",
                                    "window", "movimiento", "movement", "tráfico")):
            return "acción cotidiana con movimiento natural (b-roll)"
        return "ambiente/atmósfera donde el video stock aporta emoción"
    if preferred_val == "photo_stock":
        return "situación realista/genérica que una foto limpia resume"
    return "preferencia por defecto (IA)"


# ─────────────────────────────────────────────
# 3) CANDIDATE SELECTION INTELLIGENCE
# ─────────────────────────────────────────────

@dataclass
class Candidate:
    """Candidato unificado (video/photo) con su score."""
    id: Any = 0
    url: str = ""
    source: str = "pexels"
    kind: str = "video"          # video | photo
    orientation: str = "portrait"
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    query_used: str = ""


def _candidate_from_row(row: dict, kind: str, expected_orientation: str) -> "AssetCandidateLike":
    """Convierte un row de search_photos_raw / search_videos_raw a AssetCandidate
    con `orientation_match` setado según la orientación esperada de la escena
    (necesario para que asset_selector puntúe bien la composición)."""
    from asset_selector import AssetCandidate
    if kind == "photo":
        ac = AssetCandidate(
            id=row.get("id", 0),
            url=row.get("url", ""),
            duration=row.get("duration", 0) or 0.0,
            width=row.get("width", 0),
            height=row.get("height", 0),
            orientation=row.get("orientation", "portrait"),
            fps=0.0,
            file_size=row.get("file_size", 0),
            thumbnail=row.get("thumbnail", ""),
            quality="",
            source="pexels",
        )
    else:
        ac = AssetCandidate.from_pexels(row)
    ac.orientation_match = (ac.orientation == expected_orientation)
    return ac


def select_best_candidate(
    brief: SceneBrief,
    strategy: MediaSourceStrategy,
    rows: list[dict],
    *,
    kind: str = "video",
    previous_assets: list | None = None,
    continuity_context: dict | None = None,
) -> Candidate | None:
    """Puntúa una lista de candidatos (rows) y devuelve el mejor. Sin red.

    Pasos separados y explícitos: DISCOVER (rows ya descargados por el caller)
    → SCORE (asset_selector.score_candidate) → SELECT (mejor por score).
    La IA y el Quality Gate corren DESPUÉS, en el render (aquí no se toca).
    """
    if not rows:
        return None
    from asset_selector import score_candidate
    expected = brief_locale_orientation(brief)
    best = None
    for row in rows:
        ac = _candidate_from_row(row, kind, expected)
        s = score_candidate(ac, brief, previous_assets, continuity_context)
        cand = Candidate(
            id=ac.id,
            url=ac.url,
            source="pexels",
            kind=kind,
            orientation=ac.orientation,
            score=s.total,
            reasons=list(s.reasons),
        )
        if best is None or cand.score > best.score:
            best = cand
    return best


def brief_locale_orientation(brief: SceneBrief) -> str:
    """Devuelve la orientación esperada para la escena según el texto/lugar."""
    return "portrait"
