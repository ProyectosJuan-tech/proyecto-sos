"""
V2.1.1 — NARRATIVE VISUAL DIRECTOR.

Capa pequeña y GENERAL de dirección narrativa visual.

Responde: "¿Qué debería estar viendo el espectador mientras escucha esta frase?"
y NO "¿Qué imagen bonita puedo poner aquí?".

Cadena:
    NARRACIÓN → FUNCIÓN NARRATIVA → INTENCIÓN VISUAL → VISUAL EVENT ESPECÍFICO
        → COMPOSE PROMPT → ASSET/GENERACIÓN → IMAGEN

NO es un pipeline nuevo ni un renderer. NO toca el pipeline legacy:
conecta la capa V2 (editorial_orchestrator) para que cada escena derive un
visual_event OBSERVABLE y ESPECÍFICO desde su narración + rol narrativo, en
vez de repetir central_idea.

PRINCIPIO:
    No ilustrar emoción abstracta cuando puede representarse una ACCIÓN,
    INTERACCIÓN, OBJETO, ENTORNO, PERSONA o METÁFORA observable.
    Preferencia: ACCIÓN > INTERACCIÓN > OBJETO > ENTORNO > PERSONA > METÁFORA
    (no absoluta — la narrativa decide).

DIVERSIDAD:
    Puede elegir PERSON / HANDS / OBJECT / ENVIRONMENT / INTERACTION /
    DETAIL / SYMBOLIC / TEXTUAL_OBJECT. No todas las escenas muestran persona.

ANTI-REPETICIÓN:
    Dentro de un video evita repetir visual_event / tipo / acción / objeto /
    composición, salvo que la repetición sea deliberada (keep_allowed=True).

Este módulo es DETERMINISTA: no hace redes ni generación externa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re

from scene_brief import NarrativeRole, compose_prompt_from_brief


# ─────────────────────────────────────────────
# Tipos de representación
# ─────────────────────────────────────────────

class RepresentationType(str, Enum):
    PERSON = "person"                # persona como sujeto central
    HANDS = "hands"                  # manos en acción (detalle humano)
    OBJECT = "object"               # objeto narrativo protagónico
    ENVIRONMENT = "environment"     # espacio / atmósfera (puede no haber persona)
    INTERACTION = "interaction"     # dos o más personas / persona-objeto en relación
    DETAIL = "detail"               # primer plano de un detalle
    SYMBOLIC = "symbolic"           # metáfora visual simbólica
    TEXTUAL_OBJECT = "textual_object"  # carta / nota / mensaje / texto


# ─────────────────────────────────────────────
# Función narrativa → estrategia visual base
# ─────────────────────────────────────────────

@dataclass
class VisualStrategy:
    """Estrategia visual derivada del rol narrativo. Reutiliza SceneBrief."""
    subject_type: str                      # person / hands / object / ...
    action: str                            # acción observable en inglés
    setting: str                           # entorno base
    shot_type: str                         # close-up / medium / wide / ...
    symbolic_level: str = "low"            # low / medium / high
    default_event: str = ""                # evento observable por defecto del rol


_ROLE_STRATEGIES: dict[NarrativeRole, VisualStrategy] = {
    NarrativeRole.HOOK: VisualStrategy(
        subject_type="interaction",
        action="pausing mid-task, glancing up toward a doorway",
        setting="a familiar home space with soft natural light",
        shot_type="medium",
        symbolic_level="low",
        default_event="a person pauses mid-task and glances toward an open doorway, curious",
    ),
    NarrativeRole.PROBLEM: VisualStrategy(
        subject_type="person",
        action="rubbing tired eyes, shoulders dropping",
        setting="a quiet bedside at dawn",
        shot_type="medium",
        symbolic_level="low",
        default_event="a person sits at the edge of a bed at dawn, rubbing tired eyes",
    ),
    NarrativeRole.AGITATION: VisualStrategy(
        subject_type="hands",
        action="rewriting and erasing the same line repeatedly",
        setting="a still kitchen with morning light",
        shot_type="close-up",
        symbolic_level="medium",
        default_event="hands rewrite and erase the same line of a note over and over",
    ),
    NarrativeRole.PSYCHOLOGY: VisualStrategy(
        subject_type="detail",
        action="hand hovering over a message, then deleting it",
        setting="a desk with paper and a small lamp",
        shot_type="close-up",
        symbolic_level="medium",
        default_event="a hand hovers over a written message, then deletes the line",
    ),
    NarrativeRole.SOLUTION: VisualStrategy(
        subject_type="object",
        action="placing a small object down with intention",
        setting="a bright window with a chair",
        shot_type="medium",
        symbolic_level="low",
        default_event="a hand sets a small object down firmly on a table beside a chair",
    ),
    NarrativeRole.BIBLICAL_GROUNDING: VisualStrategy(
        subject_type="object",
        action="fingers resting on an open page",
        setting="an open window with gentle light",
        shot_type="close-up",
        symbolic_level="high",
        default_event="fingers rest on an open page of a worn book in gentle window light",
    ),
    NarrativeRole.REALITY: VisualStrategy(
        subject_type="environment",
        action="a full morning routine carrying on quietly",
        setting="a simple living room in daylight",
        shot_type="wide",
        symbolic_level="low",
        default_event="an ordinary living room carries on quietly in flat daylight, unglamorous",
    ),
    NarrativeRole.HOPE: VisualStrategy(
        subject_type="environment",
        action="stepping toward an open, light-filled doorway",
        setting="an open doorway to daylight",
        shot_type="wide",
        symbolic_level="medium",
        default_event="a figure steps toward an open doorway filled with daylight",
    ),
    NarrativeRole.CALLOUT: VisualStrategy(
        subject_type="textual_object",
        action="a simple message resting on a table",
        setting="a warm inviting interior",
        shot_type="medium",
        symbolic_level="low",
        default_event="a short handwritten note rests plainly on a wooden table",
    ),
    NarrativeRole.LOOP: VisualStrategy(
        subject_type="interaction",
        action="returning to the same chair and holding a warm cup",
        setting="the same calm room, now at rest",
        shot_type="medium",
        symbolic_level="low",
        default_event="a person returns to the same chair and holds a warm cup, back where it began",
    ),
    NarrativeRole.EMPHASIS: VisualStrategy(
        subject_type="detail",
        action="a held still frame, steady gaze forward",
        setting="a focused close interior",
        shot_type="close-up",
        symbolic_level="high",
        default_event="a held still frame: a steady gaze, everything else out of focus",
    ),
    NarrativeRole.PAYOFF: VisualStrategy(
        subject_type="person",
        action="chin resting on hand, a small nod",
        setting="a soft corner with a plant",
        shot_type="medium",
        symbolic_level="low",
        default_event="a person rests their chin on one hand and gives a small, settled nod",
    ),
    NarrativeRole.BRIDGE: VisualStrategy(
        subject_type="environment",
        action="turning the page and moving between rooms",
        setting="a hallway between two lit rooms",
        shot_type="wide",
        symbolic_level="medium",
        default_event="a hallway connects two lit rooms, a page turning between moments",
    ),
}


# ─────────────────────────────────────────────
# Léxico general de señales OBSERVABLES (en inglés la salida)
# ─────────────────────────────────────────────
# Cue = palabra clave en español del scene_text → micro-event observado.
# Son genéricos (psicología / hábitos / fe), no por tema concreto.

_CUES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"mensaje|enviar|borrar\s+(un\s+)?mensaje|whatsapp"),
     "interaction",
     "a hand types a message, hesitates, then deletes it before pressing send"),
    (re.compile(r"escribir|escribe|nota|anotar|lista|borrador"),
     "detail",
     "a hand writes and crosses out a short line on a page, over and over"),
    (re.compile(r"llamar|llamada|tel[eé]fono"),
     "interaction",
     "a phone rings on the table; a hand reaches for it, then stops"),
    (re.compile(r"cafe|caf[eé]|taza"),
     "hands",
     "two hands wrap around a warm cup, holding it without drinking"),
    (re.compile(r"libro|p[aá]gina|leer|biblia|escritura|salmo"),
     "object",
     "fingers rest on an open page, tracing a single sentence"),
    (re.compile(r"puerta|salir|entrar|umbral|abrir"),
     "environment",
     "a door stands slightly open, light spilling through the gap"),
    (re.compile(r"ventana|ventanal|mirar\s+por"),
     "environment",
     "a silhouette stands at a window, looking out toward the light"),
    (re.compile(r"caminar|camino|dar\s+un\s+paso|paso"),
     "person",
     "a person walks slowly toward a lit doorway, pausing at the threshold"),
    (re.compile(r"sentarse|silla|esperar|espera"),
     "person",
     "a person sits still, hands folded, waiting without checking the clock"),
    (re.compile(r"respirar|respiraci[oó]n|aliento|pausa"),
     "detail",
     "a slow breath as a hand lets go of the edge of the table"),
    (re.compile(r"perd[oó]n|disculpa|carta|nota\s+deja"),
     "interaction",
     "two people sit across a table; one leaves a folded note and walks away"),
    (re.compile(r"limpiar|lavar|platos|ordenar|limpi[oó]"),
     "hands",
     "hands stack dishes carefully, one on another, so quietly nothing breaks"),
    (re.compile(r"descanso|dormir|acostar|almohada|cama"),
     "environment",
     "an empty bed seen from the doorway, quiet and still in soft light"),
    (re.compile(r"agotad|cansanci|fatiga|pesado"),
     "person",
     "a person sinks into a chair, letting out a long, heavy breath"),
    (re.compile(r"l[ií]mite|frontera|no\s+puedo|basta"),
     "object",
     "a hand draws a clear line on paper and leaves it, unresolved"),
    (re.compile(r"apego|control|soltar|dejar\s+ir"),
     "symbolic",
     "open palms rest flat on a table, empty, as if releasing something"),
]

_FALLBACK_EVENT = (
    "a quiet, ordinary moment in soft natural light: a small action that "
    "carries the meaning of the sentence without words"
)


# ─────────────────────────────────────────────
# Derive visual event
# ─────────────────────────────────────────────

def _match_cue(scene_text: str) -> tuple[RepresentationType, str] | None:
    low = scene_text.lower()
    for pattern, rtype, event in _CUES:
        if pattern.search(low):
            return RepresentationType(rtype), event
    return None


def derive_visual_event(
    scene_text: str,
    narrative_role: NarrativeRole | str,
    previous_events: list[str] | None = None,
    content_context: str | None = None,
    keep_allowed: bool = False,
) -> tuple[str, RepresentationType]:
    """Deriva un visual_event OBSERVABLE y ESPECÍFICO desde la narración.

    Args:
        scene_text: narración de la escena (español).
        narrative_role: rol narrativo.
        previous_events: eventos visuales ya usados en este video.
        content_context: contexto del contenido (sin uso obligatorio).
        keep_allowed: True conserva la repetición aun ya usada (deliberada).

    Returns:
        (visual_event_en, representation_type)
    """
    if isinstance(narrative_role, str):
        try:
            narrative_role = NarrativeRole(narrative_role)
        except ValueError:
            narrative_role = NarrativeRole.PSYCHOLOGY

    text = (scene_text or "").strip()

    # 0) Sin información suficiente → fallback SEGURO y EXPLÍCITO (nunca
    #    central_idea, nunca un loop). Observable y simbólico-neutral.
    if not text:
        return _FALLBACK_EVENT, RepresentationType.SYMBOLIC

    # 1) Señal observable desde el texto (relación con la narración).
    cue = _match_cue(text)

    prev = list(previous_events or [])

    if cue is not None:
        rtype, event = cue
        # Anti-repetición: si el mismo evento (o tipo+acción) ya se usó y no
        # está permitido, rotamos a otro tipo de representación del rol.
        if not keep_allowed:
            bases = _event_bases(event)
            if _any_reused(bases, prev):
                event, rtype = _rotate_avoiding(event, rtype, narrative_role, prev)
        return event, rtype

    # 2) Sin señal en el texto: marco observable del rol (aún así NO repite
    #    central_idea, y es un evento específico del rol).
    strat = _ROLE_STRATEGIES.get(narrative_role) or _ROLE_STRATEGIES[NarrativeRole.PSYCHOLOGY]
    event = strat.default_event
    rtype = RepresentationType(strat.subject_type)

    if not keep_allowed and not prev:
        return event, rtype

    if not keep_allowed:
        bases = _event_bases(event)
        if _any_reused(bases, prev):
            event, rtype = _rotate_avoiding(event, rtype, narrative_role, prev)

    return event, rtype


def _event_bases(event: str) -> set[str]:
    """Tokens estables del evento para detectar repetición de acción/objeto."""
    stop = {
        "a", "an", "the", "of", "and", "in", "on", "to", "at", "with", "its",
        "from", "toward", "then", "before", "as", "for", "over", "hand", "hands",
    }
    toks = [t for t in re.findall(r"[a-zA-Z']+", event.lower()) if t not in stop and len(t) > 2]
    return {" ".join(toks[-4:])} | set(toks[-2:])


def _any_reused(bases: set[str], previous_events: list[str]) -> bool:
    for ev in previous_events:
        if bases & _event_bases(ev):
            return True
    return False


def _rotate_avoiding(
    event: str,
    rtype: RepresentationType,
    role: NarrativeRole,
    previous_events: list[str],
) -> tuple[RepresentationType, str]:
    """Cambia de tipo de representación para romper la repetición injustificada.

    Recorre TODOS los tipos alternativos en orden estable y devuelve el primero
    cuyo evento no repita el de previous_events. Garantiza término y rompe
    repeticiones consecutivas mientras haya alternativas disponibles.
    """
    strat = _ROLE_STRATEGIES.get(role) or _ROLE_STRATEGIES[NarrativeRole.PSYCHOLOGY]
    # orden canónico de tipos, girando para empezar "lo más cerca" del actual
    order = [
        RepresentationType.PERSON,
        RepresentationType.HANDS,
        RepresentationType.OBJECT,
        RepresentationType.ENVIRONMENT,
        RepresentationType.INTERACTION,
        RepresentationType.DETAIL,
        RepresentationType.SYMBOLIC,
        RepresentationType.TEXTUAL_OBJECT,
    ]
    if rtype in order:
        k = order.index(rtype)
        order = order[k + 1:] + order[:k + 1]

    candidates: list[tuple[RepresentationType, str]] = []
    for t in order:
        if t == rtype:
            continue
        candidates.append((t, _alternate_event(t, strat, role)))
    if not candidates:
        candidates = [(rtype, event)]

    for t, alt in candidates:
        if not _any_reused(_event_bases(alt), previous_events) and alt != event:
            return alt, t
    # todas las alternativas ya usadas: devolver la primera distinta al actual
    for t, alt in candidates:
        if alt != event:
            return alt, t
    return event, rtype


def _alternate_event(rtype: RepresentationType, strat: VisualStrategy, role: NarrativeRole) -> str:
    alt_by_type = {
        RepresentationType.DETAIL: "a close detail that stands for the moment: a single object, half-finished",
        RepresentationType.INTERACTION: "two people share a quiet, unspoken moment across a table",
        RepresentationType.ENVIRONMENT: "the room itself tells the story: empty corners, soft light, stillness",
        RepresentationType.OBJECT: "one ordinary object anchors the scene, carrying the meaning without words",
        RepresentationType.SYMBOLIC: "a small symbolic gesture: a line drawn, a door ajar, an open palm",
        RepresentationType.HANDS: "only the hands in frame, moving through a familiar, patient action",
        RepresentationType.TEXTUAL_OBJECT: "a short handwritten phrase rests on the table, plain and final",
        RepresentationType.PERSON: "a person, seen from behind, holds the pose of the moment",
    }
    return alt_by_type.get(rtype, strat.default_event)


# ─────────────────────────────────────────────
# Director principal
# ─────────────────────────────────────────────

@dataclass
class DirectedScene:
    """Resultado de la dirección narrativa para una escena."""
    scene_id: str
    narrative_role: NarrativeRole
    visual_event: str
    representation_type: RepresentationType
    strategy: VisualStrategy
    prompt: str
    symbol: str = "a simple everyday object"
    fallback_used: bool = False


@dataclass
class NarrativeVisualDirector:
    """Dirige la intención visual de cada escena según su función narrativa."""

    def direct_brief(self, brief, keep_allowed: bool = False) -> DirectedScene:
        """Dirige UN SceneBrief: devuelve la intención + prompt (no muta el brief)."""
        event, rtype = derive_visual_event(
            scene_text=brief.narration,
            narrative_role=brief.narrative_role,
            previous_events=None,  # la rotación cross-scene la maneja direct_plan
            keep_allowed=keep_allowed,
        )
        strat = _ROLE_STRATEGIES.get(brief.narrative_role) or _ROLE_STRATEGIES[NarrativeRole.PSYCHOLOGY]
        return DirectedScene(
            scene_id=brief.scene_id,
            narrative_role=brief.narrative_role,
            visual_event=event,
            representation_type=rtype,
            strategy=strat,
            symbol=brief.symbol or _symbol_from_event(event, rtype),
            prompt=_compose(brief, event, strat, rtype),
            fallback_used=not (brief.narration or "").strip(),
        )

    def direct_plan(self, briefs, force_reuse: set[str] | None = None,
                    keep_allowed_role: set[str] | None = None) -> list[DirectedScene]:
        """Dirige un PLAN completo aplicando anti-repetición entre escenas."""
        force_reuse = set(force_reuse or [])
        keep_roles = set(keep_allowed_role or [])
        prev: list[str] = []
        out: list[DirectedScene] = []
        for brief in briefs:
            role = brief.narrative_role
            bond = _matches(brief, force_reuse)
            keep = (bond is not None) or (role.value in keep_roles)
            if bond is not None:
                # repetición DELIBERADA: reutilizar exactamente ese evento previo
                event = bond
                rtype = RepresentationType.INTERACTION
            else:
                event, rtype = derive_visual_event(
                    scene_text=brief.narration,
                    narrative_role=role,
                    previous_events=prev,
                    keep_allowed=keep,
                )
            strat = _ROLE_STRATEGIES.get(role) or _ROLE_STRATEGIES[NarrativeRole.PSYCHOLOGY]
            res = DirectedScene(
                scene_id=brief.scene_id,
                narrative_role=role,
                visual_event=event,
                representation_type=rtype,
                strategy=strat,
                symbol=brief.symbol or _symbol_from_event(event, rtype),
                prompt=_compose(brief, event, strat, rtype),
                fallback_used=not (brief.narration or "").strip(),
            )
            prev.append(event)
            out.append(res)
        return out


def _matches(brief, force_reuse: set[str]) -> str | None:
    n = (brief.narration or "").lower()
    for ref in force_reuse:
        if ref and ref.lower() in n:
            return ref
    return None


def _symbol_for_strategy(rtype: RepresentationType) -> str:
    return {
        RepresentationType.PERSON: "a quiet human gesture that carries the moment",
        RepresentationType.HANDS: "two hands in a patient, familiar action",
        RepresentationType.OBJECT: "one ordinary, meaningful object",
        RepresentationType.ENVIRONMENT: "the room and the light it holds",
        RepresentationType.INTERACTION: "a shared glance across a table",
        RepresentationType.DETAIL: "a small, telling detail",
        RepresentationType.SYMBOLIC: "an open palm, a door ajar, a written line",
        RepresentationType.TEXTUAL_OBJECT: "a short handwritten phrase on paper",
    }.get(rtype, "a simple everyday object")


# ─────────────────────────────────────────────
# BRIEF COHERENCE (V2.4): luz por rol, cámara por plano, acción/símbolo
# coherentes con el evento. El prompt base describe el FRAMING de la escena
# (formato-neutro); la adaptación por formato (16:9/9:16 + espacio de texto) la
# hace el Proveedor Adapter (build_quality_prompt) al final del flujo.
# ─────────────────────────────────────────────

_LIGHT_BY_ROLE: dict[str, str] = {
    "hook": "soft morning window light through a sheer curtain",
    "problem": "dim cool bedside light at dawn, low and quiet",
    "agitation": "overcast diffused daylight, flat and slightly cooler",
    "psychology": "warm pool of desk-lamp light falling on paper",
    "solution": "bright clear morning light from a window",
    "hopeful": "luminous warm daylight spilling through an open door",
    "hope": "luminous warm daylight spilling through an open door",
    "biblical_grounding": "gentle window light falling on an open page",
    "reality": "flat honest daylight, unglamorous and true",
    "callout": "soft warm inviting evening light",
    "loop": "calm settled evening light in a now-quiet room",
    "emphasis": "focused low light with a single clear highlight",
    "payoff": "soft comfortable light with gentle shadows",
    "bridge": "light passing between two adjoining rooms",
}

_CAMERA_BY_SHOT: dict[str, str] = {
    "close-up": "single sitting, 85mm f/1.8, shallow depth of field",
    "medium": "50mm f/2, natural depth, at eye level",
    "wide": "35mm f/2.8, environmental, lots of air around the subject",
    "long": "35mm f/2.8, environmental establishing frame",
}


# Marcadores de default GEÉRICOS que build_scene() hornea en cada brief.
# Si el brief trae estos valores exactos significa que nadie los eligió: la capa
# auto (V2.4) los sustituye por luz por rol + cámara por plano. Cualquier OTRO
# valor (una luz/cámara deliberada de un SceneBrief manual) se respeta.
_GENERIC_DEFAULT_LIGHT = "soft natural window light"
_GENERIC_DEFAULT_CAMERA = "Medium shot on Sony A7IV, 50mm f/1.8"


def _light_for(role) -> str:
    r = role.value if hasattr(role, "value") else str(role)
    return _LIGHT_BY_ROLE.get(r, "soft natural window light")


def _camera_for(shot_type: str) -> str:
    return _CAMERA_BY_SHOT.get(shot_type, "50mm f/2, natural depth, at eye level")


def _symbol_from_event(event: str, rtype: RepresentationType) -> str:
    """Símbolo ALINEADO con el evento (no el genérico del tipo), para que la
    frase 'The story is carried by <símbolo>' no contradiga el evento."""
    e = (event or "").lower()
    if any(w in e for w in ("door", "doorway", "threshold", "step")):
        return "a half-open door with light on the other side"
    if any(w in e for w in ("window", "outside the window")):
        return "the light at the window"
    if any(w in e for w in ("table", "desk", "counter")):
        return "the still object resting on the table"
    if any(w in e for w in ("bed", "pillow", "blanket")):
        return "the rumpled bed left untouched"
    if any(w in e for w in ("book", "page", "reading", "open page", "bible")):
        return "the open page and the finger resting on it"
    if any(w in e for w in ("hand", "hands", "finger", "grip")):
        return "two hands in a patient, familiar action"
    if any(w in e for w in ("note", "message", "writing", "line", "letter", "phrase")):
        return "the half-finished line on the page"
    if any(w in e for w in ("cup", "coffee", "tea")):
        return "the warm cup held without drinking"
    if any(w in e for w in ("room", "corner", "living room", "kitchen")):
        return "the room itself and the quiet it holds"
    if any(w in e for w in ("plate", "dish", "dishes")):
        return "the careful stack of clean dishes"
    if any(w in e for w in ("phone", "ring")):
        return "the phone left unanswered"
    return _symbol_for_strategy(rtype)


def _compose(brief, event: str, strat: VisualStrategy, rtype: RepresentationType) -> str:
    """Compone el prompt final reutilizando compose_prompt() vía SceneBrief.

    V2.4: el brief que llega a compose_prompt() lleva luz por rol, cámara por
    plano, acción y símbolo COHERENTES con el evento (no los defaults idénticos
    ni las acciones genéricas de rol que contradecían el evento), y una
    composición FORMATO-NEUTRA (el framing lo adapta el Proveedor Adapter).
    """
    import dataclasses
    # Acción coherente: la del estrategia (mismo beat que el evento) es la
    # correcta; solo se usa brief.action si el llamador dio una explícita.
    action = (brief.action or "").strip() or strat.action
    # Luz/cámara: si el brief viene con los defaults genéricos que hornea
    # build_scene (o vacío), se sustituyen por luz por rol / cámara por plano.
    _light = (brief.lighting or "").strip()
    if not _light or _light == _GENERIC_DEFAULT_LIGHT:
        _light = _light_for(brief.narrative_role)
    _cam = (brief.camera or "").strip()
    if not _cam or _cam == _GENERIC_DEFAULT_CAMERA:
        _cam = _camera_for(strat.shot_type)
    clone = dataclasses.replace(
        brief,
        visual_event=event,
        action=action,
        setting=brief.setting or strat.setting,
        lighting=_light,
        camera=_cam,
        composition=brief.composition or _composition_for(strat.shot_type),
        symbol=brief.symbol or _symbol_from_event(event, rtype),
        subject_priority=brief.subject_priority or strat.subject_type,
    )
    try:
        return compose_prompt_from_brief(clone)
    except Exception:
        # fallback seguro y explícito si compose_prompt falla
        return f"{strat.setting.rstrip('.')}. {event}"


def _composition_for(shot_type: str) -> str:
    """Framing FORMATO-NEUTRO de la escena (qué plan, dónde está el sujeto).

    El espacio de texto por FORMATO (9:16 / 16:9) lo añade el Proveedor Adapter
    (build_quality_prompt) al final; aquí NO se hardcodea 'lower text band' que
    en 16:9 es la zona equivocada (vertical-only).
    """
    return {
        "close-up": "close-up, subject clearly framed in the lower part, air above",
        "medium": "medium shot, subject off-center with balanced negative space",
        "wide": "wide environmental shot, subject small but clear, balanced negative space",
    }.get(shot_type, "medium shot, subject off-center with balanced negative space")
