"""
V2-05 — EDITORIAL_ORCHESTRATOR: capa de integración editorial.

Convierte "Hagamos un <TEMA> sobre X" en un recorrido completo:

    IDEA → FORMAT → EDITORIAL PLAN → SCENE BRIEFS → ASSET SELECTION
           → TEXT LAYOUT → (scene_dicts listos para el renderer existente)

Usa las cuatro capas V2 (SceneBrief, ShortPlan/LongFormPlan, AssetSelector,
TextLayout) a través de v2_bridge, SIN tocar ni refactorizar el pipeline
de render. Mantiene compatibilidad hacia atrás.

Abstracción ContentPlan:
    ContentPlan
        ├── ShortPlan        (reutiliza short_director.ShortPlan)
        └── LongFormPlan     (nuevo, representado aquí)

Restricciones:
- No se hardcodea ningún tema concreto.
- Las narraciones son INYECTADAS por el llamador (en producción vienen de
  Gemini vía generar_textos.py) o, en modo scaffold determinista para tests,
  generadas por generate_scene_narrations().
- No genera videos finales: corta en la generación de scene_dicts + layouts,
  listos para que el pipeline existente los renderice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scene_brief import (
    SceneBrief,
    SceneType,
    NarrativeRole,
    PreferredSource,
    MotionType,
    TransitionType,
)
from short_director import (
    ShortPlan,
    generate_hook_options,
    select_best_hook,
    build_scene,
    validate_plan,
    plan_to_dict,
    plan_to_json,
)
from asset_selector import select_asset, AssetSelection, generate_queries
from text_layout import compute_layout, validate_layout, TextLayout
from v2_bridge import (
    scene_brief_to_render_scene_dict,
    scene_brief_to_text_layout_request,
    platform_to_text_layout_platform,
)

WARM_STYLE = "bright airy natural, cinematic still"

# Arcos narrativos por formato
SHORT_ARC = [
    NarrativeRole.HOOK,
    NarrativeRole.PROBLEM,
    NarrativeRole.AGITATION,
    NarrativeRole.PSYCHOLOGY,
    NarrativeRole.SOLUTION,
    NarrativeRole.HOPE,
    NarrativeRole.CALLOUT,
]

LONG_ARC = [
    NarrativeRole.HOOK,
    NarrativeRole.REALITY,
    NarrativeRole.PROBLEM,
    NarrativeRole.PSYCHOLOGY,
    NarrativeRole.PSYCHOLOGY,
    NarrativeRole.PSYCHOLOGY,
    NarrativeRole.SOLUTION,
    NarrativeRole.BIBLICAL_GROUNDING,
    NarrativeRole.HOPE,
    NarrativeRole.CALLOUT,
]


# ────────────────────────────────────────────────
# Contenido por rol (scaffold genérico, no por tema)
# ────────────────────────────────────────────────

_NARRATION_FRAMES = {
    NarrativeRole.HOOK: (
        "¿Alguna vez has sentido que {idea}?",
        "{idea_corta}",
        "Si {idea}, esto es para ti.",
    ),
    NarrativeRole.PROBLEM: (
        "La mayoría piensa que el problema es el cansancio, pero {idea}.",
        "Cuando {idea}, todo parece más pesado.",
        "No estás sola: {idea}.",
    ),
    NarrativeRole.AGITATION: (
        "Y mientras tanto, {idea}. Y eso tiene un costo.",
        "El problema es que {idea}, aunque no lo veas a la primera.",
        "{idea}, y ese es el detalle que casi nadie ve.",
    ),
    NarrativeRole.PSYCHOLOGY: (
        "Hay un patrón en esto: {idea}. Y reconocerlo es el primer paso.",
        "Esto no es falta de voluntad, es un patrón: {idea}.",
        "Tu mente busca una salida, pero {idea}.",
    ),
    NarrativeRole.SOLUTION: (
        "La solución empieza por un paso pequeño: {idea}.",
        "Puedes cambiar esto. El camino es {idea}.",
        "No hace falta una gran revolución, solo {idea}.",
    ),
    NarrativeRole.BIBLICAL_GROUNDING: (
        "Nadie está llamado a vivir atrapado. {idea}.",
        "Hay algo más grande que este cansancio: {idea}.",
        "Somos más que nuestro agotamiento: {idea}.",
    ),
    NarrativeRole.REALITY: (
        "Y también es verdad que {idea}.",
        "La realidad es que {idea}.",
        "Seamos honestos: {idea}.",
    ),
    NarrativeRole.HOPE: (
        "Hay una salida, y empieza hoy: {idea}.",
        "Y aun así, hay esperanza: {idea}.",
        "El descanso es posible: {idea}.",
    ),
    NarrativeRole.LOOP: (
        "Porque {idea}, y por eso estás aquí.",
        "Y recuerda: {idea}.",
    ),
    NarrativeRole.EMPHASIS: (
        "{idea}.",
        "¡{idea}!",
    ),
    NarrativeRole.CALLOUT: (
        "Si esto te resonó, compártelo con quien lo necesite.",
        "Compártelo con alguien que necesite escucharlo.",
        "Sígueme para más contenido como este.",
    ),
    NarrativeRole.PAYOFF: (
        "{idea}.",
        "Y eso lo cambia todo.",
    ),
    NarrativeRole.BRIDGE: (
        "Y entonces, {idea}.",
        "Pero déjame explicarte por qué: {idea}.",
    ),
}


def _pick_frame(role: NarrativeRole, index: int) -> str:
    frames = _NARRATION_FRAMES.get(role, ("{idea}",))
    return frames[index % len(frames)]


def generate_scene_narrations(topic: str, central_idea: str, roles: list[NarrativeRole]) -> dict[str, str]:
    """Genera textos de narración deterministas (scaffold) para roles dados.

    En producción esto se reemplaza por los textos aprobados de Gemini
    (generar_textos.py) inyectados vía build_editorial_plan(..., narrations=...).
    Es genérico: no menciona ningún tema concreto y usa tuteo.
    """
    out: dict[str, str] = {}
    role_counts: dict[str, int] = {}
    for role in roles:
        role_counts.setdefault(role.value, 0)
        idx = role_counts[role.value]
        role_counts[role.value] += 1
        template = _pick_frame(role, idx)
        out[role.value] = template.format(idea=central_idea, idea_corta=central_idea)
    return out


# ────────────────────────────────────────────────
# Editorial plan builder
# ────────────────────────────────────────────────


@dataclass
class EditorialEmission:
    """Resultado de la cadena editorial: listo para el renderer existente."""
    plan: Any                      # ShortPlan | LongFormPlan
    briefs: list[SceneBrief]
    format_name: str               # "short" | "youtube"
    canvas_width: int
    canvas_height: int
    scene_dicts: list[dict]        # listos para hacer_(shorts|videos_youtube)
    acom_layouts: list[TextLayout] = field(default_factory=list)
    asset_selections: list[AssetSelection] = field(default_factory=list)
    media_direction: Any = None    # MediaDirection (V2-FINAL) o None

    def to_report(self) -> dict:
        rep = {
            "format": self.format_name,
            "resolution": f"{self.canvas_width}x{self.canvas_height}",
            "n_scenes": len(self.briefs),
            "total_duration_s": round(
                sum(b.duration for b in self.briefs), 1
            ),
            "scene_dicts": len(self.scene_dicts),
            "layouts": len(self.acom_layouts),
            "assets": len(self.asset_selections),
            "status": "ok",
        }
        if self.media_direction is not None:
            rep["media_direction"] = self.media_direction.to_report()
        return rep


def _resolve_resolution(format_name: str) -> tuple[int, int]:
    if "youtube" in format_name.lower() or "16" in format_name:
        return 1920, 1080
    return 1080, 1920


def _narrations_for_roles(roles: list, narrations: dict | None, topic: str, central_idea: str) -> dict:
    """Resuelve narraciones: inyectadas o scaffold."""
    if narrations:
        return narrations
    return generate_scene_narrations(topic, central_idea, roles)


# Acción observable sugerida por rol narrativo (emoción en acción, no en cara).
# Genérico, no ligado a ningún tema.
_ROLE_ACTION = {
    NarrativeRole.HOOK: "pausing to think, looking out a window",
    NarrativeRole.PROBLEM: "rubbing tired eyes, dropping shoulders",
    NarrativeRole.AGITATION: "closing eyes, taking a slow breath",
    NarrativeRole.PSYCHOLOGY: "writing a note, erasing a line",
    NarrativeRole.SOLUTION: "opening a book, placing a hand on a table",
    NarrativeRole.BIBLICAL_GROUNDING: "lacing hands together, looking up softly",
    NarrativeRole.REALITY: "setting down a cup, sitting still",
    NarrativeRole.HOPE: "walking toward light, stepping out a door",
    NarrativeRole.LOOP: "returning to a seat, holding a warm cup",
    NarrativeRole.EMPHASIS: "holding a still frame, steady gaze forward",
    NarrativeRole.CALLOUT: "passing something to another hand",
    NarrativeRole.PAYOFF: "resting chin on hand, small nod",
    NarrativeRole.BRIDGE: "turning the page, moving between rooms",
}

_ROLE_SETTING = {
    NarrativeRole.HOOK: "a calm home space with soft natural light",
    NarrativeRole.PROBLEM: "a quiet bedside at dawn",
    NarrativeRole.AGITATION: "a still kitchen with morning light",
    NarrativeRole.PSYCHOLOGY: "a desk with paper and a small lamp",
    NarrativeRole.SOLUTION: "a bright window with a chair",
    NarrativeRole.BIBLICAL_GROUNDING: "an open window with gentle light",
    NarrativeRole.REALITY: "a simple living room in daylight",
    NarrativeRole.HOPE: "an open doorway to daylight",
    NarrativeRole.LOOP: "the same calm room, now at rest",
    NarrativeRole.EMPHASIS: "a focused close interior",
    NarrativeRole.CALLOUT: "a warm inviting interior",
    NarrativeRole.PAYOFF: "a soft corner with a plant",
    NarrativeRole.BRIDGE: "a hallway between two lit rooms",
}


def _role_action(role: NarrativeRole) -> str:
    return _ROLE_ACTION.get(role, "settling into a calm, still pose")


def _role_setting(role: NarrativeRole) -> str:
    return _ROLE_SETTING.get(role, "a calm home space with soft natural light")


def build_editorial_plan(
    *,
    topic: str,
    central_idea: str,
    format_name: str = "short",
    audience: str = "mujeres 35-64 que buscan bienestar genuino",
    promise: str = "",
    cta: str = "",
    narrations: dict | None = None,
    extra_scenes: list[SceneBrief] | None = None,
    roles_override: list[NarrativeRole] | None = None,
    motion: MotionType = MotionType.ZOOM_IN,
    preferred_source: PreferredSource = PreferredSource.AI,
    narrative_director: bool = True,
) -> tuple[Any, list[SceneBrief]]:
    """Construye el plan editorial (ShortPlan o LongFormPlan) + sus SceneBriefs.

    Returns:
        (plan, briefs)
    """
    is_long = ("youtube" in format_name.lower() or "16" in format_name)

    roles = roles_override or (LONG_ARC if is_long else SHORT_ARC)
    narr = _narrations_for_roles(roles, narrations, topic, central_idea)

    # Hook
    hook_options = generate_hook_options(topic, central_idea)
    best_hook = select_best_hook(hook_options, topic).text

    # CTA por defecto genérico (tuteo)
    if not cta:
        cta = "Si esto te resonó, compártelo con quien lo necesite."

    # Construir escenas
    briefs: list[SceneBrief] = []
    idx = 1
    for role in roles:
        narration = narr.get(role.value, central_idea)
        if role == NarrativeRole.HOOK:
            narration = best_hook if not narr.get(role.value) else narr.get(role.value, best_hook)
        if role == NarrativeRole.CALLOUT:
            narration = cta

        brief = build_scene(
            scene_id=f"e{idx:02d}",
            role=role,
            narration=narration,
            emotional_core=narrations.get("__emotional_core", "") if narrations else "",
            visual_event=central_idea,
            action="",
            setting=_role_setting(role),
            symbol=None,
            subject="",
            continuity_group="main_narrative" if not is_long else "long_narrative",
            preferred_source=preferred_source,
            motion=motion,
            transition=TransitionType.FADE,
        )
        briefs.append(brief)
        idx += 1

    if extra_scenes:
        briefs.extend(extra_scenes)

    # V2.1.1 — Narrative Visual Director: cada escena recibe un visual_event
    # específico y observable derivado de su narración + rol (en vez de repetir
    # central_idea), y el prompt final via compose_prompt(). Se escribe de vuelta
    # en el SceneBrief para que llegue REALMENTE al renderer (ai_prompt/visual_event).
    if narrative_director:
        from narrative_visual_director import (
            NarrativeVisualDirector, _light_for, _camera_for, _composition_for,
            _GENERIC_DEFAULT_LIGHT, _GENERIC_DEFAULT_CAMERA,
        )
        try:
            directed = NarrativeVisualDirector().direct_plan(briefs)
            # Aspect para el Proveedor Adapter (16:9 para youtube/16, 9:16 resto)
            canvas_ar = "16:9" if is_long else "9:16"
            _HUMAN_TYPES = {"person", "hands", "interaction", "detail"}
            for brief, d in zip(briefs, directed):
                if d.representation_type.value:
                    brief.subject_priority = brief.subject_priority or d.strategy.subject_type
                brief.visual_event = d.visual_event
                brief.action = brief.action or d.strategy.action
                brief.symbol = brief.symbol or d.symbol
                # Reflejar en los campos del brief los valores coherentes que ya
                # entran en el prompt (luz por rol, cámara por plano, composición
                # formato-neutra) para que NO queden los defaults idénticos.
                # Misma lógica de reemplazo de default que _compose.
                light_ = brief.lighting or ""
                if not light_ or light_ == _GENERIC_DEFAULT_LIGHT:
                    brief.lighting = _light_for(brief.narrative_role)
                cam_ = brief.camera or ""
                if not cam_ or cam_ == _GENERIC_DEFAULT_CAMERA:
                    brief.camera = _camera_for(d.strategy.shot_type)
                brief.composition = brief.composition or _composition_for(d.strategy.shot_type)
                brief.ai_prompt = d.prompt
                # V2.4 — PROVEEDOR ADAPTER: adapta el prompt base (brief neutral)
                # al formato (16:9/9:16 + espacio de texto) y al realismo humano
                # SOLO cuando la escena gira en torno a una persona. Separa
                # "qué quiero ver" (compose_prompt) de "cómo se lo comunico al
                # generador" (build_quality_prompt) sin tocar el pipeline legacy.
                from visual_quality_engine import build_quality_prompt
                has_human = d.representation_type.value in _HUMAN_TYPES
                brief.ai_prompt = build_quality_prompt(
                    d.prompt, canvas_ar=canvas_ar, has_human=has_human,
                )
        except Exception:
            # si la dirección fallara por cualquier motivo, no romper el plan:
            # quedan los visual_events base (central_idea) y se sigue adelante.
            pass

    # Duraciones
    total_dur = round(sum(b.duration for b in briefs), 1)
    target_dur = total_dur if not is_long else max(480.0, total_dur)

    if is_long:
        plan: Any = LongFormPlan(
            topic=topic,
            central_idea=central_idea,
            audience=audience,
            tone="hopeful",
            goal="bienestar_emocional",
            narrative_structure=[r.value for r in roles],
            scenes=briefs,
            cta=cta,
            target_duration=target_dur,
        )
    else:
        plan = ShortPlan(
            topic=topic,
            central_idea=central_idea,
            audience=audience,
            hook=best_hook,
            narrative_arc=roles,
            scenes=briefs,
            cta=cta,
            target_duration=total_dur,
            promise=promise or central_idea,
        )

    return plan, briefs


# ────────────────────────────────────────────────
# LongFormPlan (16:9 horizontal)
# ────────────────────────────────────────────────


@dataclass
class LongFormPlan:
    """Plan editorial para contenido largo/16:9.

    Representa: tema, idea central, audiencia, tono, objetivo,
    estructura narrativa, escenas, CTA, duración objetivo.
    """
    topic: str = ""
    central_idea: str = ""
    audience: str = "mujeres 35-64 que buscan bienestar genuino"
    tone: str = "hopeful"
    goal: str = "bienestar_emocional"
    narrative_structure: list[str] = field(default_factory=list)
    scenes: list[SceneBrief] = field(default_factory=list)
    cta: str = ""
    target_duration: float = 0.0

    def estimate_total_duration(self) -> float:
        return round(sum(s.duration for s in self.scenes), 1)

    def narrative_roles_used(self) -> list[str]:
        return [s.narrative_role.value for s in self.scenes]

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "central_idea": self.central_idea,
            "audience": self.audience,
            "tone": self.tone,
            "goal": self.goal,
            "narrative_structure": self.narrative_structure,
            "scenes": [s.to_dict() for s in self.scenes],
            "cta": self.cta,
            "target_duration": self.target_duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LongFormPlan":
        return cls(
            topic=data.get("topic", ""),
            central_idea=data.get("central_idea", ""),
            audience=data.get("audience", cls.audience),
            tone=data.get("tone", "hopeful"),
            goal=data.get("goal", "bienestar_emocional"),
            narrative_structure=data.get("narrative_structure", []),
            scenes=[SceneBrief.from_dict(s) for s in data.get("scenes", [])],
            cta=data.get("cta", ""),
            target_duration=data.get("target_duration", 0.0),
        )

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "LongFormPlan":
        import json
        return cls.from_dict(json.loads(text))


def validate_long_plan(plan: LongFormPlan) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not plan.topic:
        errors.append("Falta topic")
    if not plan.central_idea:
        errors.append("Falta central_idea")
    if not plan.scenes:
        errors.append("Faltan escenas")
    if len(plan.scenes) > 14:
        warnings.append(f"Demasiadas escenas ({len(plan.scenes)})")
    if not plan.cta:
        warnings.append("Falta CTA")
    for s in plan.scenes:
        v = s.validate()
        if not v["valid"]:
            errors.append(f"Escena {s.scene_id}: {v['errors']}")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "total_duration": plan.estimate_total_duration(),
            "scene_count": len(plan.scenes),
            "roles_used": plan.narrative_roles_used(),
        },
    }


# ────────────────────────────────────────────────
# Asset selection por escena
# ────────────────────────────────────────────────


def select_assets_for_briefs(
    briefs: list[SceneBrief],
    *,
    fetch_fn=None,
    use_real_fetch: bool = True,
) -> list[AssetSelection]:
    """Selecciona assets para cada SceneBrief (asset_selector sin duplicar scoring).

    use_real_fetch=False → sin red (los tests pasan fetch_fn mock).

    V2.7: construye `continuity_context` a partir de las selecciones previas
    (representacion/fuente ya usadas) para que la diversidad entre escenas
    influya en el scoring de asset_selector (era un parámetro muerto).
    """
    selections: list[AssetSelection] = []
    previous: list = []
    used_sources: list[str] = []
    for brief in briefs:
        continuity_context = {"last_sources": list(used_sources)}
        sel = select_asset(brief, previous_assets=previous,
                           continuity_context=continuity_context,
                           fetch_fn=fetch_fn)
        selections.append(sel)
        if sel.selected:
            previous.append(sel.selected)
            used_sources.append(sel.selected.orientation)
    return selections


# ────────────────────────────────────────────────
# End-to-end producción editorial
# ────────────────────────────────────────────────


def produce_editorial(
    *,
    topic: str,
    central_idea: str,
    format_name: str = "short",
    audience: str = "mujeres 35-64 que buscan bienestar genuino",
    promise: str = "",
    cta: str = "",
    narrations: dict | None = None,
    extra_scenes: list[SceneBrief] | None = None,
    roles_override: list[NarrativeRole] | None = None,
    motion: MotionType = MotionType.ZOOM_IN,
    preferred_source: PreferredSource = PreferredSource.AI,
    asset_fetch_fn=None,
    use_real_asset_fetch: bool = False,
    enable_media_director: bool = True,
    enable_media_intelligence: bool = True,
    requested_topic: str | None = None,
    requested_idea: str | None = None,
    enforce_topic_lock: bool = True,
) -> EditorialEmission:
    """Recorre la cadena completa para un tema dado.

    IDEA → plan → briefs → MEDIA DIRECTOR → assets → layouts → scene_dicts.

    TOPIC LOCK: si `enforce_topic_lock`, valida que el plan construido responda
    a la idea SOLICITADA (requested_topic/requested_idea; por defecto `topic`/
    `central_idea`). Si el contenido del plan no contiene anclas de esa idea,
    eleva TopicLockError y detiene la producción ANTES de gastar assets/
    proveedores. El sistema puede mejorar título/guion/imagen, pero NO sustituir
    el tema central entregado por el usuario.
    """
    w = 1920 if ("youtube" in format_name.lower() or "16" in format_name) else 1080
    h = 1080 if w == 1920 else 1920

    plan, briefs = build_editorial_plan(
        topic=topic,
        central_idea=central_idea,
        format_name=format_name,
        audience=audience,
        promise=promise,
        cta=cta,
        narrations=narrations,
        extra_scenes=extra_scenes,
        roles_override=roles_override,
        motion=motion,
        preferred_source=preferred_source,
    )

    if enforce_topic_lock:
        from topic_lock import assert_topic_locked
        assert_topic_locked(
            requested_topic=requested_topic or topic,
            requested_idea=requested_idea or central_idea,
            plan=plan,
        )

    # V2-FINAL — MEDIA DIRECTOR: decide por escena el tipo de medio (AI_IMAGE/
    # VIDEO_STOCK/PHOTO_STOCK) y el motion, con diversidad como factor suave
    # (calidad manda, variedad como desempate). Se aplica AL brief para que el
    # render scene_dict use la fuente y el motion correctos.
    media_direction = None
    if enable_media_director:
        from media_director import direct_media, preferred_source_for
        media_direction = direct_media(briefs)
        for brief, sm in zip(briefs, media_direction.scenes):
            brief.preferred_source = preferred_source_for(sm.medium)
            brief.motion = sm.motion

    # V2.7 — INTELIGENCIA VISUAL DE MEDIOS (aditivo, sin red): enriquece cada
    # brief con VisualKeywords y la estrategia de fuente. No cambia el
    # preferred_source ya decidido por el media_director; expone la info
    # estructurada para el informe y alimenta las queries de stock desde el
    # evento (subordinadas a la narrativa, no al revés).
    if enable_media_intelligence:
        from media_intelligence import (
            derive_visual_keywords, build_media_source_strategy,
        )
        for brief in briefs:
            kw = derive_visual_keywords(brief)
            brief.visual_keywords = kw.to_dict()
            strat = build_media_source_strategy(brief)
            brief.media_strategy = strat.to_dict()
            # Queries de stock derivadas del evento (solo si el brief no trae
            # las suyas): así select_asset parte del evento, no de traducciones
            # crudas, y conserva early-stop/máx-cuotas de asset_selector.
            if kw.stock_keywords and not brief.pexels_queries:
                brief.pexels_queries = list(kw.stock_keywords)

    # Assets
    selections = select_assets_for_briefs(
        briefs, fetch_fn=asset_fetch_fn, use_real_fetch=use_real_asset_fetch
    )

    # Layouts + scene_dicts
    layouts: list[TextLayout] = []
    scene_dicts: list[dict] = []
    for i, brief in enumerate(briefs):
        req = scene_brief_to_text_layout_request(
            brief, format_name=format_name, canvas_width=w, canvas_height=h
        )
        layout = compute_layout(req)
        layouts.append(layout)
        scene_dicts.append(scene_brief_to_render_scene_dict(brief, index=i))

    return EditorialEmission(
        plan=plan,
        briefs=briefs,
        format_name=format_name,
        canvas_width=w,
        canvas_height=h,
        scene_dicts=scene_dicts,
        acom_layouts=layouts,
        asset_selections=selections,
        media_direction=media_direction,
    )
