"""media_director.py — MEDIA DIRECTOR (V2-FINAL)

Decide, para cada escena, QUÉ tipo de medio usar (AI_IMAGE / VIDEO_STOCK /
PHOTO_STOCK) y QUÉ motion, a partir de la narrativa de la escena y de la
diversidad de medios YA usados en el resto del video.

PRINCIPIO (del usuario, requisitos 21-25):
  - La DIVERSIDAD DE MEDIOS es un FACTOR de ranking, NO una cuota rígida
    (nada de "una foto cada 3 escenas" ni "50/50").
  - La CALIDAD manda: si el mejor medio para la escena es claramente superior
    (p.ej. AI_IMAGE 8.5 frente a VIDEO_STOCK 5.2), NO se fuerza diversidad.
  - La diversidad SOLO modifica la decisión cuando los candidatos son
    comparables (p.ej. AI_IMAGE 8.2 vs VIDEO_STOCK 8.0 → se puede favorecer
    el video para variar).
  - También se vela por la diversidad de REPRESENTACIÓN (PERSON / HANDS /
    OBJECT / ENVIRONMENT / INTERACTION / DETAIL / SYMBOLIC / TEXTUAL_OBJECT),
    con la misma regla: calidad primero, variedad como desempate.

Salida: MediaDirection con, por escena, medium + fit_score + motion +
representación + motivo, y las secuencias media_sequence y
representation_sequence para el informe.

Es ADITIVO y SIN red: no baja nada, solo decide. El render real lo hace
render_adapter (que baja la foto/video/imagen según el medio decidido).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from scene_brief import SceneBrief, NarrativeRole, MotionType, PreferredSource

# Representación del sujeto (qué protagoniza la escena).
class Representation(str, Enum):
    PERSON = "person"
    HANDS = "hands"
    OBJECT = "object"
    ENVIRONMENT = "environment"
    INTERACTION = "interaction"
    DETAIL = "detail"
    SYMBOLIC = "symbolic"
    TEXTUAL_OBJECT = "textual_object"


class MediumType(str, Enum):
    AI_IMAGE = "ai_image"
    VIDEO_STOCK = "video_stock"
    PHOTO_STOCK = "photo_stock"


# Referencia de representación hacia los campos del SceneBrief (subject_priority
# viene del Narrative Visual Director cuando aplica).
_SUBJECT_PRIORITY_MAP = {
    "person": Representation.PERSON,
    "mano": Representation.HANDS, "hands": Representation.HANDS,
    "manos": Representation.HANDS,
    "objeto": Representation.OBJECT, "object": Representation.OBJECT,
    "ambiente": Representation.ENVIRONMENT, "environment": Representation.ENVIRONMENT,
    "interaccion": Representation.INTERACTION, "interaction": Representation.INTERACTION,
    "detalle": Representation.DETAIL, "detail": Representation.DETAIL,
    "simbolico": Representation.SYMBOLIC, "symbolic": Representation.SYMBOLIC,
    "objeto_textual": Representation.TEXTUAL_OBJECT,
    "textual": Representation.TEXTUAL_OBJECT,
}


# Señales en el brief que indican que la escena necesita IA SI O SI (no hay
# stock confiable): escena específica, no reproducible con stock genérico.
_AI_REQUIRED_HINTS = (
    "same man", "the same", "same woman", "misma persona", "personaje",
    "retrato", "caracter", "continuity", "protagonista",
)
# Roles donde el texto manda y conviene composición controlada (limpieza de
# espacio para el texto): conviene AI o PHOTO (foto real limpia), menos video
# ruidoso.
_TEXT_FRONT_ROLES = {
    NarrativeRole.HOOK, NarrativeRole.CALLOUT, NarrativeRole.EMPHASIS,
    NarrativeRole.PAYOFF,
}


def _repr_of_brief(brief: SceneBrief) -> Representation:
    prio = (brief.subject_priority or "").strip().lower()
    if prio:
        for k, v in _SUBJECT_PRIORITY_MAP.items():
            if prio == k or k in prio:
                return v
    low = (brief.visual_event or "").lower()
    # heurística simple por contenido, todos los casos atienden la regla de
    # "no mirar a cámara": preferir objetos/ambiente/manos a rostros.
    if any(w in low for w in ("manos", "hand", "fingers", "pushing", "typing",
                              "writing", "erasing", "holding", "gripping")):
        return Representation.HANDS
    if any(w in low for w in ("ventana", "window", "room", "cocina", "kitchen",
                              "desk", "escritorio", "habitacion", "interior",
                              "hall", "door", "puerta")):
        return Representation.ENVIRONMENT
    if any(w in low for w in ("taza", "cup", "libro", "book", "carta", "letter",
                              "foto", "photo", "planta", "plant", "zapatilla",
                              "shoe", "calendario", "calendar", "reloj")):
        return Representation.OBJECT
    if any(w in low for w in ("mirando", "looking", "sujeta", "sostiene",
                              "entrega", "passes", "comparte", "ofrece")):
        return Representation.INTERACTION
    if "persona" in low or "mujer" in low or "hombre" in low or "woman" in low:
        return Representation.PERSON
    return Representation.ENVIRONMENT


# ─────────────────────────────────────────────
# Fit por medio (0-10, calidad prevista de ese medio para la escena)
# ─────────────────────────────────────────────

def _medium_fit(brief: SceneBrief, medium: MediumType) -> float:
    """Score 0-10 de qué tan bien encaja cada medio con la narrativa."""
    low = (brief.visual_event or "").lower()
    ai_prompt = (brief.ai_prompt or "").lower()
    role = brief.narrative_role

    # Base
    if medium == MediumType.AI_IMAGE:
        base = 6.5
    elif medium == MediumType.VIDEO_STOCK:
        base = 6.0
    else:  # PHOTO_STOCK
        base = 6.0

    # ¿La escena/exige IA por especificidad o por continuidad de personaje?
    need_ai = any(h in (ai_prompt or low) for h in _AI_REQUIRED_HINTS)

    if medium == MediumType.AI_IMAGE:
        if need_ai:
            base += 2.5          # no hay stock de un personaje concreto
        # acción muy específica (no reproducible con stock genérico) => IA
        if "pushing" in low or "erasing" in low or "writing" in low \
           or "specific" in low or "bespoke" in low or "exact" in low:
            base += 1.2
        if role in _TEXT_FRONT_ROLES:
            base += 0.6          # composición controlada para el texto
        # facilidad humana: IA con prompt de bienestar => alta
        if "persona" in low or "mujer" in low or "hombre" in low or "woman" in low:
            base += 0.4
        return min(10.0, base)

    # STOCK (video o foto): solo encaja si la escena es alcanzable con stock.
    if need_ai:
        return 2.0               # stock no puede reproducir un personaje fijo

    # Escena genérica/atmósfera (b-roll) => stock encaja bien.
    atmos = any(w in low for w in ("light", "luces", "sol", "sun", "morning",
                                   "amanecer", "atardecer", "ventana", "window",
                                   "café", "té", "mug", "cup", "planta", "plant",
                                   "libro", "book", "hojas", "leaves", "flor",
                                   "flower", "paisaje", "landscape", "cielo",
                                   "nube", "cloud", "road", "camino"))
    generic = not low or len(low.split()) < 5

    if atmos or generic:
        # video vs foto: video suma movimiento emocional; foto suma quietud.
        if medium == MediumType.VIDEO_STOCK:
            base += 1.5
        else:
            base += 1.0
    else:
        # escena con acción/objeto específico de la historia => stock flojo
        base -= 1.5

    # Roles de texto: photo limpia ok, video ruidoso menos
    if role in _TEXT_FRONT_ROLES:
        if medium == MediumType.PHOTO_STOCK:
            base += 0.7
        elif medium == MediumType.VIDEO_STOCK:
            base -= 0.4

    # foto vs video: quietud para payoff/esperanza; movimiento para agitación/b-roll
    if role in (NarrativeRole.PAYOFF, NarrativeRole.HOPE, NarrativeRole.CALLOUT):
        if medium == MediumType.PHOTO_STOCK:
            base += 0.5
    if role in (NarrativeRole.AGITATION, NarrativeRole.PSYCHOLOGY):
        if medium == MediumType.VIDEO_STOCK:
            base += 0.4

    return min(10.0, max(0.0, base))


# Motion por medio/acción (el medio define qué motion es posible)
def _motion_for(brief: SceneBrief, medium: MediumType) -> MotionType:
    action = (brief.action or brief.visual_event or "").lower()
    if medium == MediumType.VIDEO_STOCK:
        # el propio video aporta el movimiento; el Ken Burns debe ser estático
        return MotionType.STATIC
    if medium == MediumType.PHOTO_STOCK:
        # es un estático: dar un Ken Burns suave y coherente con la acción
        # dirección explícita primero (pan left/right), antes de la acción genérica
        if "left" in action or "izquierda" in action:
            return MotionType.PAN_LEFT
        if any(w in action for w in ("mirando", "looking", "camina", "walk",
                                     "mira hacia", "hacia")) or \
           any(w in action for w in ("pan", "derecha", "right")):
            return MotionType.PAN_RIGHT
        if brief.narrative_role in (NarrativeRole.HOPE, NarrativeRole.PAYOFF,
                                    NarrativeRole.CALLOUT):
            return MotionType.ZOOM_OUT   # abrir: esperanza/soltar
        return MotionType.ZOOM_IN        # por defecto: intimidad
    # AI_IMAGE: se respeta el motion del brief (ya dirigido por escena)
    return brief.motion or MotionType.ZOOM_IN


@dataclass
class SceneMedia:
    scene_id: str
    medium: MediumType
    fit_score: float
    motion: MotionType
    representation: Representation
    reasoning: str


@dataclass
class MediaDirection:
    scenes: list[SceneMedia] = field(default_factory=list)
    media_sequence: list[str] = field(default_factory=list)
    representation_sequence: list[str] = field(default_factory=list)

    def to_report(self) -> dict:
        return {
            "media_sequence": list(self.media_sequence),
            "representation_sequence": list(self.representation_sequence),
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "medium": s.medium.value,
                    "fit_score": round(s.fit_score, 2),
                    "motion": s.motion.value,
                    "representation": s.representation.value,
                    "reasoning": s.reasoning,
                }
                for s in self.scenes
            ],
        }


def _apply_diversity(medium: MediumType, recent_media: list[str],
                     other_fit: float, chosen_fit: float) -> float:
    """Bonus de diversidad SÓLO cuando la calidad es comparable.

    Regla: si el medio elegido ya se usó mucho seguido Y el 2º mejor medio
    tiene un fit DENTRO del margen (comparables), dar un pequeño bonus que lo
    empuja. Si los fit difieren mucho, la calidad SIMPRE gana (sin bonus).
    """
    MARGIN = 0.45
    if not recent_media:
        return 0.0
    rep = recent_media.count(medium.value)
    total = len(recent_media)
    # Evitar 3+ seguidos del mismo medio cuando hay alternativa comparable
    tail = recent_media[-2:] if len(recent_media) >= 2 else []
    consecutive = all(m == medium.value for m in tail)
    if (rep >= 2 or consecutive) and (chosen_fit - other_fit) <= MARGIN:
        return 0.35
    return 0.0


def direct_media(briefs: list[SceneBrief], *, top2_margin: float = 0.45) -> MediaDirection:
    """Asigna medio + motion + representación a cada escena (greedy secuencial)."""
    out = MediaDirection()
    recent_media: list[str] = []
    recent_repr: list[str] = []
    reps = [_repr_of_brief(b) for b in briefs]

    for i, brief in enumerate(briefs):
        media: list[tuple[MediumType, float]] = [
            (m, _medium_fit(brief, m)) for m in MediumType
        ]
        media.sort(key=lambda x: x[1], reverse=True)
        # diversidad compara 1º vs 2º
        best_m, best_f = media[0]
        alt_m, alt_f = media[1] if len(media) > 1 else (best_m, best_f)
        bonus = _apply_diversity(best_m, recent_media, alt_f, best_f)
        if bonus > 0 and (best_f - alt_f) <= top2_margin:
            best_m, best_f = alt_m, best_f  # favorece variedad, mantiene fit
        else:
            best_f = best_f  # calidad manda

        motion = _motion_for(brief, best_m)
        reasoning = _reason(brief, best_m, best_f, bonus)

        recent_media.append(best_m.value)
        recent_repr.append(reps[i].value)
        out.media_sequence.append(best_m.value)
        out.representation_sequence.append(reps[i].value)
        out.scenes.append(SceneMedia(
            scene_id=brief.scene_id,
            medium=best_m,
            fit_score=best_f,
            motion=motion,
            representation=reps[i],
            reasoning=reasoning,
        ))

    return out


def _reason(brief: SceneBrief, medium: MediumType, fit: float, bonus: float) -> str:
    parts = [f"fit {medium.value}={fit:.1f}"]
    if bonus > 0:
        parts.append("diversidad: 2º medio comparable favorecido")
    else:
        parts.append("calidad manda")
    return "; ".join(parts)


# ─────────────────────────────────────────────
# Devolver el PreferredSource / claves del scene_dict
# ─────────────────────────────────────────────

def preferred_source_for(medium: MediumType) -> PreferredSource:
    if medium == MediumType.VIDEO_STOCK:
        return PreferredSource.STOCK
    if medium == MediumType.PHOTO_STOCK:
        return PreferredSource.PHOTO_STOCK
    return PreferredSource.AI


def medium_to_render_keys(medium: MediumType) -> dict:
    """Claves del scene_dict que el render debe usar para este medio."""
    if medium == MediumType.VIDEO_STOCK:
        return {"stock": True}
    if medium == MediumType.PHOTO_STOCK:
        return {"photo_stock": True}
    return {}


if __name__ == "__main__":
    import json
    from editorial_orchestrator import build_editorial_plan
    plan, briefs = build_editorial_plan(topic="el descanso", central_idea="el cansancio no se cura con más cansancio")
    d = direct_media(briefs)
    print(json.dumps(d.to_report(), ensure_ascii=False, indent=2))
