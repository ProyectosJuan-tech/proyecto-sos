"""
short_director.py — Director Editorial para Shorts.

Transforma un TEMA en un PLAN NARRATIVO estructurado (ShortPlan)
que produce SceneBriefs listos para el pipeline visual.

El Director Editorial NO genera imágenes.
NO selecciona Pexels.
NO genera prompts finales de IA visual.
NO renderiza video.

Su responsabilidad: TEMA → INTENCIÓN → ARCO → ESCENAS → SceneBrief.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

from scene_brief import (
    SceneBrief, SceneType, NarrativeRole, PreferredSource,
    MotionType, TransitionType,
)


# ─────────────────────────────────────────────
# Constantes editoriales
# ─────────────────────────────────────────────

# Palabras por minuto para estimación de duración (español conversacional)
WORDS_PER_MINUTE = 160

# Rangos de duración por tipo de short
DURATION_RANGES = {
    "corto": (8, 15),    # 8-15 segundos
    "medio": (30, 60),   # 30-60 segundos
    "largo": (60, 90),   # 60-90 segundos
}

# Palabras prohibidas (autoayuda/guru)
PROHIBIDAS = [
    "ley de atracción", "manifest", "vibra", "riqueza", "millonario",
    "lotería", "fórmula mágica", "secreto", "mente sobre materia",
    "pensar bonito", "hazte rico", "abundancia", "universo te escucha",
]

# Roles narrativos disponibles
NARRATIVE_ROLES = {
    NarrativeRole.HOOK: "Gancho inicial — captura atención en los primeros 3s",
    NarrativeRole.PROBLEM: "Problema — plantea lo que el espectador siente",
    NarrativeRole.AGITATION: "Escalada — consecuencia concreta y honesta",
    NarrativeRole.PSYCHOLOGY: "Psicología — comprensión del patrón humano",
    NarrativeRole.SOLUTION: "Giro — reencuadre que cambia la perspectiva",
    NarrativeRole.BIBLICAL_GROUNDING: "Fundamento bíblico — conexión con la fe",
    NarrativeRole.REALITY: "Realidad — verdad directa sin adornos",
    NarrativeRole.HOPE: "Esperanza — luz al final del túnel",
    NarrativeRole.CALLOUT: "CTA — llamada a la acción coherente",
    NarrativeRole.BRIDGE: "Puente — conexión entre secciones",
    NarrativeRole.EMPHASIS: "Énfasis — punto fuerte deliberado",
    NarrativeRole.LOOP: "Loop — cierra el bucle con el inicio",
}

# Arco emocional por defecto
DEFAULT_ARC = [
    NarrativeRole.HOOK,
    NarrativeRole.PROBLEM,
    NarrativeRole.AGITATION,
    NarrativeRole.PSYCHOLOGY,
    NarrativeRole.SOLUTION,
    NarrativeRole.BIBLICAL_GROUNDING,
    NarrativeRole.REALITY,
    NarrativeRole.HOPE,
    NarrativeRole.CALLOUT,
]


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class HookStrategy(str, Enum):
    """Estrategias de gancho para el primer segundo."""
    IDENTIFICATION = "identification"    # "¿Te pasó que...?"
    TENSION = "tension"                  # "Hay algo que nadie te dice sobre..."
    AFFIRMATION = "affirmation"          # "Dios no te pide que..."
    REFRAME = "reframe"                  # "Tu X no viene de Y..."
    QUESTION = "question"               # "¿Cuánto tiempo llevas...?"


class ArcPhase(str, Enum):
    """Fases del arco emocional."""
    ENTRADA = "entrada"
    RECONOCIMIENTO = "reconocimiento"
    TENSION = "tension"
    GIRO = "giro"
    SENTIDO = "sentido"
    ESPERANZA = "esperanza"
    CIERRE = "cierre"


class Platform(str, Enum):
    """Plataforma destino."""
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    BOTH = "both"


class Tone(str, Enum):
    """Tono editorial."""
    EMPATHETIC = "empathetic"        # Cálido, comprensivo
    DIRECT = "direct"                # Firme, sin vueltas
    REFLECTIVE = "reflective"        # Pausado, contemplativo
    HOPEFUL = "hopeful"              # Luminoso, orientado a futuro
    COMBINED = "combined"            # Mezcla según la escena


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────

@dataclass
class HookOption:
    """Una opción de gancho evaluada internamente."""
    strategy: HookStrategy
    text: str
    rationale: str = ""
    score: float = 0.0  # 0-1, el Director evalúa internamente


@dataclass
class ShortPlan:
    """
    Plan editorial completo para un Short.

    Contiene la intención, el arco narrativo, las escenas (SceneBriefs)
    y toda la metadata necesaria para que el pipeline visual produzca
    el video.
    """
    # ── IDENTIDAD ──
    topic: str = ""
    central_idea: str = ""
    audience: str = "mujeres 35-64 que buscan bienestar genuino"
    tone: Tone = Tone.EMPATHETIC
    language: str = "es"
    locale: str = "neutral_hispanic"
    register: str = "conversational"
    voseo: bool = False
    regionalisms: bool = False
    platform: Platform = Platform.BOTH

    # ── PROMESA ──
    promise: str = ""           # Qué promete al espectador
    target_duration: float = 0.0  # Duración objetivo en segundos

    # ── HOOK ──
    hook: str = ""              # El gancho seleccionado
    hook_strategy: HookStrategy = HookStrategy.IDENTIFICATION
    hook_options: list[HookOption] = field(default_factory=list)

    # ── ARCO ──
    narrative_arc: list[NarrativeRole] = field(default_factory=list)

    # ── ESCENAS ──
    scenes: list[SceneBrief] = field(default_factory=list)

    # ── CTA ──
    cta: str = ""
    cta_type: str = "empathetic"  # empathetic | direct | thematic

    # ── NOTAS ──
    notes: str = ""

    def estimate_total_duration(self) -> float:
        """Estima duración total sumando duraciones de escenas."""
        total = sum(s.duration for s in self.scenes)
        return round(total, 1)

    def narrative_roles_used(self) -> list[str]:
        """Devuelve los narrative_role usados en las escenas."""
        return [s.narrative_role.value for s in self.scenes]

    def continuity_groups(self) -> list[str]:
        """Devuelve los continuity_group únicos."""
        seen = set()
        groups = []
        for s in self.scenes:
            if s.continuity_group and s.continuity_group not in seen:
                seen.add(s.continuity_group)
                groups.append(s.continuity_group)
        return groups


# ─────────────────────────────────────────────
# Funciones de estimación
# ─────────────────────────────────────────────

def estimate_scene_duration(text: str, role: NarrativeRole = NarrativeRole.BRIDGE) -> float:
    """
    Estima la duración de una escena en segundos.

    Heurística: palabras / palabras_por_minuto * 60 + overhead por rol.
    El hook y el CTA tienen overhead adicional (pausas, énfasis).
    """
    words = len(text.split())
    base = (words / WORDS_PER_MINUTE) * 60

    # Overhead por rol narrativo
    overhead = {
        NarrativeRole.HOOK: 1.5,      # Pausa inicial, impacto
        NarrativeRole.CALLOUT: 2.0,   # CTA más pausado
        NarrativeRole.LOOP: 1.0,      # Cierre deliberado
        NarrativeRole.EMPHASIS: 1.5,  # Énfasis = pausa
    }

    base += overhead.get(role, 0.5)
    return round(max(base, 2.0), 1)


def estimate_total_duration(scenes: list[SceneBrief]) -> float:
    """Estima duración total de una lista de escenas."""
    return round(sum(s.duration for s in scenes), 1)


# ─────────────────────────────────────────────
# Generación de hooks
# ─────────────────────────────────────────────

def generate_hook_options(topic: str, central_idea: str) -> list[HookOption]:
    """
    Genera 3 opciones de gancho para un tema.

    El Director evalúa internamente y selecciona la mejor.
    Las opciones se generan según las estrategias del spec.
    """
    options = []

    # HOOK A — Identificación
    options.append(HookOption(
        strategy=HookStrategy.IDENTIFICATION,
        text=f"¿Te pasó que {central_idea.lower()}?",
        rationale="Conexión directa con la experiencia del espectador",
    ))

    # HOOK B — Tensión
    options.append(HookOption(
        strategy=HookStrategy.TENSION,
        text=f"Hay algo que nadie te dice sobre {topic.lower()}.",
        rationale="Crea curiosidad y tensión narrativa",
    ))

    # HOOK C — Afirmación/Revelación
    options.append(HookOption(
        strategy=HookStrategy.AFFIRMATION,
        text=f"Dios no te pide que permanezcas en lo que te destruye.",
        rationale="Revelación que invierte expectativas con fe",
    ))

    return options


def select_best_hook(options: list[HookOption], topic: str) -> HookOption:
    """
    Selecciona el mejor hook de las opciones disponibles.

    Criterios: impacto emocional, claridad, brevedad.
    Para temas de fe + psicología, AFFIRMATION suele ser más fuerte.
    """
    # Heurística simple: AFFIRMATION > IDENTIFICATION > TENSION
    # para temas que combinan fe y vida real
    priority = {
        HookStrategy.AFFIRMATION: 3,
        HookStrategy.REFRAME: 3,
        HookStrategy.IDENTIFICATION: 2,
        HookStrategy.QUESTION: 2,
        HookStrategy.TENSION: 1,
    }

    for opt in options:
        opt.score = priority.get(opt.strategy, 1) / 3.0
        # Bonus por brevedad
        if len(opt.text.split()) <= 8:
            opt.score += 0.1

    return max(options, key=lambda o: o.score)


# ─────────────────────────────────────────────
# Construcción de escenas
# ─────────────────────────────────────────────

def build_scene(
    scene_id: str,
    role: NarrativeRole,
    narration: str,
    emotional_core: str = "",
    visual_event: str = "",
    action: str = "",
    setting: str = "",
    symbol: str | None = None,
    subject: str = "",
    composition: str = "",
    camera: str = "",
    lighting: str = "",
    visual_style: str = "",
    continuity_group: str = "",
    on_screen_text: list[str] | None = None,
    preferred_source: PreferredSource = PreferredSource.AI,
    motion: MotionType = MotionType.ZOOM_IN,
    transition: TransitionType = TransitionType.FADE,
    style_family: str = "",
    **kwargs,
) -> SceneBrief:
    """
    Construye un SceneBrief con duración estimada automáticamente.

    Es el único punto de construcción de escenas — centraliza
    la lógica de estimación de duración.
    """
    duration = estimate_scene_duration(narration, role)

    return SceneBrief(
        scene_id=scene_id,
        scene_type=SceneType.SHORT,
        narrative_role=role,
        narration=narration,
        emotional_core=emotional_core,
        visual_event=visual_event or narration,
        action=action,
        setting=setting,
        symbol=symbol,
        subject=subject,
        composition=composition,
        camera=camera or "Medium shot on Sony A7IV, 50mm f/1.8",
        lighting=lighting or "soft natural window light",
        visual_style=visual_style or "bright airy natural, cinematic still",
        style_family=style_family,
        preferred_source=preferred_source,
        motion=motion,
        transition=transition,
        duration=duration,
        on_screen_text=on_screen_text or [],
        continuity_group=continuity_group,
    )


# ─────────────────────────────────────────────
# Generación de plan de relación destructiva (ejemplo)
# ─────────────────────────────────────────────

def plan_relacion_destructiva() -> ShortPlan:
    """
    Genera un ShortPlan de prueba para:
    'Dios no te pide que permanezcas atrapado en una relación destructiva.'

    Este es el caso de prueba principal del spec.
    """
    topic = "relación destructiva"
    central_idea = "Dios no te pide que permanezcas atrapado en una relación destructiva"

    # Generar y seleccionar hook
    hook_options = generate_hook_options(topic, central_idea)
    best_hook = select_best_hook(hook_options, topic)

    # Definir arco narrativo
    arc = [
        NarrativeRole.HOOK,
        NarrativeRole.PROBLEM,
        NarrativeRole.AGITATION,
        NarrativeRole.PSYCHOLOGY,
        NarrativeRole.SOLUTION,
        NarrativeRole.BIBLICAL_GROUNDING,
        NarrativeRole.REALITY,
        NarrativeRole.HOPE,
        NarrativeRole.CALLOUT,
    ]

    # Construir escenas
    scenes = [
        # HOOK
        build_scene(
            scene_id="e01",
            role=NarrativeRole.HOOK,
            narration="Dios no te pide que permanezcas atrapado en una relación destructiva.",
            emotional_core="alivio — alguien lo dice en voz alta",
            visual_event="Mujer sentada en el borde de una cama, sosteniendo el teléfono con ambas manos, mirando al vacío antes de responder un mensaje.",
            action="sostener el teléfono sin abrir el mensaje",
            setting="habitación con luz tenue, tarde nublada",
            symbol="el teléfono con un mensaje sin leer",
            continuity_group="relationship_home",
            motion=MotionType.ZOOM_IN,
        ),

        # PROBLEMA
        build_scene(
            scene_id="e02",
            role=NarrativeRole.PROBLEM,
            narration="Hay una diferencia enorme entre amar a alguien y perderte a ti misma por quedarte.",
            emotional_core="reconocimiento —命名 lo que ya siente",
            visual_event="Mujer borrando un mensaje que escribió, escribiendo otro más corto, volviendo a borrar.",
            action="escribir y borrar un mensaje",
            setting="misma habitación, luz cambia ligeramente",
            symbol="el mensaje borrado en la pantalla",
            continuity_group="relationship_home",
            motion=MotionType.ZOOM_IN,
        ),

        # ESCALADA
        build_scene(
            scene_id="e03",
            role=NarrativeRole.AGITATION,
            narration="Cuando toleras lo que te duele, tu cuerpo lo registra aunque tu mente lo justifique.",
            emotional_core="conexión entre tolerancia y daño real",
            visual_event="Mujer frotándose las manos nerviosamente mientras espera en una sala de estar vacía.",
            action="frotarse las manos con ansiedad",
            setting="sala de estar con muebles sobrios, luz lateral",
            symbol="las manos frotándose",
            continuity_group="relationship_home",
            motion=MotionType.ZOOM_IN,
        ),

        # PSICOLOGÍA
        build_scene(
            scene_id="e04",
            role=NarrativeRole.PSYCHOLOGY,
            narration="Hay un patrón: das, das, das, y cuando pones un límite, te hacen sentir que eres tú la que cambió.",
            emotional_core="identificación del patrón — el espectador se ve",
            visual_event="Mujer apilando platos en la cocina, uno sobre otro, con cuidado exagerado para no hacer ruido.",
            action="apilar platos con cuidado exagerado",
            setting="cocina silenciosa, luz de ventana filtrada",
            symbol="los platos apilados con cuidado",
            continuity_group="relationship_home",
            motion=MotionType.ZOOM_IN,
        ),

        # GIRO
        build_scene(
            scene_id="e05",
            role=NarrativeRole.SOLUTION,
            narration="Pero si Dios es amor, ¿qué clase de amor te pide que desaparezcas para que otro esté bien?",
            emotional_core="pregunta que invierte la lógica de culpa",
            visual_event="Mujer deteniéndose en seco mientras camina por un pasillo, mirando una foto en la pared.",
            action="detenerse y mirar una foto",
            setting="pasillo de casa, luz natural suave",
            symbol="la foto en la pared — un recuerdo de quién era antes",
            continuity_group="relationship_home",
            motion=MotionType.ZOOM_IN,
        ),

        # FUNDAMENTO BÍBLICO
        build_scene(
            scene_id="e06",
            role=NarrativeRole.BIBLICAL_GROUNDING,
            narration="La Biblia dice: «Conócerte a ti mismo». Eso no significa soportar todo. Significa saber quién eres ante Dios.",
            emotional_core="fundamento — la fe no es excusa para el sufrimiento",
            visual_event="Manos abiertas sobre una mesa de madera, como si estuvieran soltando algo invisible.",
            action="abrir las manos lentamente sobre la mesa",
            setting="mesa de madera rústica, luz cálida de atardecer",
            symbol="las manos abiertas — soltar",
            continuity_group="reflection",
            motion=MotionType.ZOOM_IN,
            style_family="C_objeto_narrativo_central",
        ),

        # REALIDAD
        build_scene(
            scene_id="e07",
            role=NarrativeRole.REALITY,
            narration="Perdonar no significa volver al mismo lugar donde te lastimaron.",
            emotional_core="verdad directa que quita la culpa",
            visual_event="Mujer caminando por una acera bajo la lluvia, sin paraguas, con paso firme.",
            action="caminar bajo la lluvia sin paraguas",
            setting="calle residencial, lluvia ligera, tarde gris",
            symbol="la lluvia — limpieza, no castigo",
            continuity_group="reflection",
            motion=MotionType.ZOOM_IN,
        ),

        # ESPERANZA
        build_scene(
            scene_id="e08",
            role=NarrativeRole.HOPE,
            narration="Hay una vida después de aceptar que el amor verdadero no te pide que te destruyas.",
            emotional_core="esperanza concreta — existe algo mejor",
            visual_event="Mujer abriendo una ventana cerrada, la luz del sol entra de golpe.",
            action="abrir la ventana de par en par",
            setting="habitación que se ilumina al abrir la ventana",
            symbol="la ventana — apertura, libertad",
            continuity_group="hope",
            motion=MotionType.ZOOM_IN,
        ),

        # CTA
        build_scene(
            scene_id="e09",
            role=NarrativeRole.CALLOUT,
            narration="Si conoces a alguien que necesita escuchar esto, compártelo.",
            emotional_core="conexión — compartir es cuidar",
            visual_event="Mano dejando una taza de té sobre una mesa, al lado de un libro abierto.",
            action="dejar la taza junto al libro",
            setting="mesa con luz de ventana, ambiente cálido",
            symbol="la taza y el libro — calma y sabiduría",
            continuity_group="hope",
            motion=MotionType.ZOOM_IN,
            on_screen_text=["COMPÁRTELO"],
        ),
    ]

    # Calcular duración total
    total_duration = estimate_total_duration(scenes)

    return ShortPlan(
        topic=topic,
        central_idea=central_idea,
        audience="mujeres 35-64 que buscan bienestar genuino",
        tone=Tone.COMBINED,
        language="es",
        locale="neutral_hispanic",
        register="conversational",
        voseo=False,
        regionalisms=False,
        platform=Platform.BOTH,
        promise="Dios no te pide que te destruyas por amor",
        target_duration=total_duration,
        hook=best_hook.text,
        hook_strategy=best_hook.strategy,
        hook_options=hook_options,
        narrative_arc=arc,
        scenes=scenes,
        cta="Si conoces a alguien que necesita escuchar esto, compártelo.",
        cta_type="empathetic",
    )


# ─────────────────────────────────────────────
# Validación
# ─────────────────────────────────────────────

def validate_plan(plan: ShortPlan) -> dict[str, Any]:
    """
    Valida un ShortPlan completo.

    Returns:
        dict con valid (bool), errors (list), warnings (list), stats (dict)
    """
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict[str, Any] = {}

    # ── ERRORS ──
    if not plan.topic or not plan.topic.strip():
        errors.append("topic vacío")
    if not plan.central_idea or not plan.central_idea.strip():
        errors.append("central_idea vacía")
    if not plan.hook or not plan.hook.strip():
        errors.append("hook vacío")
    if not plan.scenes:
        errors.append("no hay escenas")
    if not plan.cta or not plan.cta.strip():
        errors.append("cta vacío")

    # Escenas inválidas
    for i, scene in enumerate(plan.scenes):
        result = scene.validate()
        for err in result["errors"]:
            errors.append(f"escena {scene.scene_id or i}: {err}")

    # Duración total
    total = plan.estimate_total_duration()
    if total <= 0 and plan.scenes:
        errors.append("duración total <= 0")
    elif total > 0:
        stats["total_duration"] = total
        stats["scene_count"] = len(plan.scenes)
        avg = total / len(plan.scenes) if plan.scenes else 0
        stats["avg_scene_duration"] = round(avg, 1)

    # Demasiadas escenas para un short
    if len(plan.scenes) > 14:
        warnings.append(f"demasiadas escenas ({len(plan.scenes)}) — considerar reducir")

    # ── WARNINGS ──
    if not plan.emotional_core_present():
        warnings.append("ninguna escena tiene emotional_core definido")

    # Escenas repetitivas
    visual_events = [s.visual_event for s in plan.scenes if s.visual_event]
    if len(visual_events) != len(set(visual_events)):
        warnings.append("hay visual_event repetidos")

    # Narrations vacías
    empty_narrations = [s.scene_id for s in plan.scenes if not s.narration.strip()]
    if empty_narrations:
        warnings.append(f"narrations vacías en: {empty_narrations}")

    # Sin giro cuando el tema lo necesita
    roles_used = [s.narrative_role.value for s in plan.scenes]
    if NarrativeRole.SOLUTION.value not in roles_used and NarrativeRole.PSYCHOLOGY.value in roles_used:
        warnings.append("tiene psychology pero no SOLUTION — el tema podría necesitar un giro")

    # CTA demasiado largo
    if plan.cta and len(plan.cta.split()) > 20:
        warnings.append(f"CTA demasiado largo ({len(plan.cta.split())} palabras)")

    # Verificar voseo
    all_text = " ".join(s.narration for s in plan.scenes) + " " + (plan.cta or "")
    voseo_markers = ["vos ", "sos ", "tenés", "querés", "decime", "seguime", "comentá", "suscribite"]
    found_voseo = [m for m in voseo_markers if m in all_text.lower()]
    if found_voseo:
        warnings.append(f"voseo detectado: {found_voseo}")

    # Verificar palabras prohibidas
    found_prohibidas = [p for p in PROHIBIDAS if p in all_text.lower()]
    if found_prohibidas:
        errors.append(f"palabras prohibidas: {found_prohibidas}")

    stats["roles_used"] = plan.narrative_roles_used()
    stats["continuity_groups"] = plan.continuity_groups()

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


# ─────────────────────────────────────────────
# Serialización
# ─────────────────────────────────────────────

def plan_to_dict(plan: ShortPlan) -> dict[str, Any]:
    """Convierte ShortPlan a dict plano serializable."""
    # Serializar escenas por separado (son dataclasses)
    scenes_dicts = [s.to_dict() for s in plan.scenes]

    # Serializar hook_options por separado
    hooks_dicts = [
        {"strategy": h.strategy.value, "text": h.text,
         "rationale": h.rationale, "score": h.score}
        for h in plan.hook_options
    ]

    # Construir dict manualmente para evitar problemas con asdict + Enums
    d = {
        "topic": plan.topic,
        "central_idea": plan.central_idea,
        "audience": plan.audience,
        "tone": plan.tone.value,
        "language": plan.language,
        "locale": plan.locale,
        "register": plan.register,
        "voseo": plan.voseo,
        "regionalisms": plan.regionalisms,
        "platform": plan.platform.value,
        "promise": plan.promise,
        "target_duration": plan.target_duration,
        "hook": plan.hook,
        "hook_strategy": plan.hook_strategy.value,
        "hook_options": hooks_dicts,
        "narrative_arc": [r.value for r in plan.narrative_arc],
        "scenes": scenes_dicts,
        "cta": plan.cta,
        "cta_type": plan.cta_type,
        "notes": plan.notes,
    }
    return d


def plan_from_dict(data: dict[str, Any]) -> ShortPlan:
    """Reconstruye ShortPlan desde un dict."""
    if not data:
        return ShortPlan()

    d = dict(data)

    # Parsear enums
    def _safe_enum(cls, val):
        if val is None:
            return None
        try:
            return cls(val)
        except (ValueError, KeyError):
            return None

    if "tone" in d:
        e = _safe_enum(Tone, d["tone"])
        if e:
            d["tone"] = e
        else:
            del d["tone"]
    if "hook_strategy" in d:
        e = _safe_enum(HookStrategy, d["hook_strategy"])
        if e:
            d["hook_strategy"] = e
        else:
            del d["hook_strategy"]
    if "platform" in d:
        e = _safe_enum(Platform, d["platform"])
        if e:
            d["platform"] = e
        else:
            del d["platform"]

    # Parsear narrative_arc
    if "narrative_arc" in d:
        parsed = []
        for r in d["narrative_arc"]:
            nr = _safe_enum(NarrativeRole, r)
            parsed.append(nr if nr else r)
        d["narrative_arc"] = parsed

    # Parsear scenes
    if "scenes" in d:
        d["scenes"] = [SceneBrief.from_dict(s) for s in d["scenes"]]

    # Parsear hook_options
    if "hook_options" in d:
        hooks = []
        for h in d["hook_options"]:
            hs = _safe_enum(HookStrategy, h.get("strategy"))
            hooks.append(HookOption(
                strategy=hs or HookStrategy.IDENTIFICATION,
                text=h.get("text", ""),
                rationale=h.get("rationale", ""),
                score=h.get("score", 0.0),
            ))
        d["hook_options"] = hooks

    # Filtrar campos conocidos
    known = {f.name for f in ShortPlan.__dataclass_fields__.values()}
    filtered = {k: v for k, v in d.items() if k in known}

    return ShortPlan(**filtered)


def plan_to_json(plan: ShortPlan, indent: int = 2) -> str:
    """Serializa ShortPlan a JSON."""
    return json.dumps(plan_to_dict(plan), ensure_ascii=False, indent=indent)


def plan_from_json(text: str) -> ShortPlan:
    """Deserializa ShortPlan desde JSON."""
    return plan_from_dict(json.loads(text))


# ─────────────────────────────────────────────
# Helper — emotional_core_present
# ─────────────────────────────────────────────

def _emotional_core_present(self) -> bool:
    """Verifica si al menos una escena tiene emotional_core."""
    return any(s.emotional_core.strip() for s in self.scenes)

# Patch para ShortPlan
ShortPlan.emotional_core_present = _emotional_core_present


# ─────────────────────────────────────────────
# CLI — ejemplo de prueba
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("DIRECTOR EDITORIAL — Ejemplo de prueba")
    print("=" * 60)
    print()

    plan = plan_relacion_destructiva()

    print(f"TEMA: {plan.topic}")
    print(f"IDEA CENTRAL: {plan.central_idea}")
    print(f"HOOK ({plan.hook_strategy.value}): {plan.hook}")
    print(f"TONO: {plan.tone.value}")
    print(f"PLATAFORMA: {plan.platform.value}")
    print(f"PROMESA: {plan.promise}")
    print()

    print("ARCO NARRATIVO:")
    for i, role in enumerate(plan.narrative_arc):
        role_val = role.value if isinstance(role, Enum) else role
        print(f"  {i+1}. {role_val}")
    print()

    print(f"ESCENAS ({len(plan.scenes)}):")
    for s in plan.scenes:
        print(f"  [{s.scene_id}] {s.narrative_role.value} ({s.duration}s)")
        print(f"    NARRACIÓN: {s.narration[:80]}...")
        print(f"    VISUAL: {s.visual_event[:80]}...")
        if s.symbol:
            print(f"    SÍMBOLO: {s.symbol}")
        print()

    total = plan.estimate_total_duration()
    print(f"DURACIÓN ESTIMADA TOTAL: {total}s")
    print()

    # Validar
    result = validate_plan(plan)
    print(f"VALIDACIÓN: {'PASS' if result['valid'] else 'FAIL'}")
    print(f"  Errores: {len(result['errors'])}")
    print(f"  Warnings: {len(result['warnings'])}")
    if result['errors']:
        for e in result['errors']:
            print(f"    ERROR: {e}")
    if result['warnings']:
        for w in result['warnings']:
            print(f"    WARN: {w}")
    print()
    print(f"STATS: {json.dumps(result['stats'], indent=2, ensure_ascii=False)}")
