"""
V2-05 — V2_BRIDGE: adaptadores entre la capa editorial (V2-01..V2-04)
y el pipeline de render existente.

Objetivo: conectar las cuatro capas de V2 (SceneBrief, Director Editorial,
Asset Intelligence, Text Layout) con el renderer actual SIN duplicar lógica
ni refactorizar el pipeline. Mantiene compatibilidad hacia atrás.

Diseño:
- Los enums de text_layout.py (NarrativeRole, Platform, Position) son copias
  independientes de los de scene_brief.py, pero COMPARTEN los mismos string
  values. Los adaptadores traducen por valor de string, nunca por identidad
  de tipo.
- SceneBrief → scene_dict plano (el que consume la cadena de render).
- Los SceneBrief no se hardcodean a ningún tema específico.

Ningún módulo toca ni modifica el pipeline existente; solo produce dicts
que el pipeline ya sabe consumir.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from scene_brief import (
    SceneBrief,
    SceneType,
    NarrativeRole as SBNarrativeRole,
    PreferredSource,
    MotionType,
    TransitionType,
)
from text_layout import (
    TextLayoutRequest,
    NarrativeRole as TLNarrativeRole,
    Platform as TLPlatform,
    Position as TLPosition,
    Alignment as TLAlignment,
)


# ────────────────────────────────────────────────
# Mapeos de enums (por valor de string compartido)
# ────────────────────────────────────────────────

# Traducción de NarrativeRole scene_brief → text_layout, por string value.
# Todos los valores de text_layout existen en scene_brief.
_TL_ROLE_BY_VALUE: dict[str, TLNarrativeRole] = {r.value: r for r in TLNarrativeRole}
# scene_brief tiene roles extra (PAYOFF) que text_layout no conoce → caen a HOOK-likes.
_TL_ROLE_FALLBACK = TLNarrativeRole.BRIDGE


def role_to_text_layout_role(role: SBNarrativeRole) -> TLNarrativeRole:
    """Traduce un NarrativeRole de scene_brief al de text_layout.

    text_layout no define PAYOFF; PAYOFF cae a un rol de texto neutro.
    El resto mapea 1:1 por valor de string.
    """
    if isinstance(role, str):
        role = SBNarrativeRole(role)
    return _TL_ROLE_BY_VALUE.get(role.value, _TL_ROLE_FALLBACK)


# Mapeo NarrativeRole → posición de texto recomendada.
_ROLE_TO_POSITION: dict[str, TLPosition] = {
    "hook": TLPosition.LOWER,
    "problem": TLPosition.CENTER,
    "agitation": TLPosition.CENTER,
    "psychology": TLPosition.CENTER,
    "solution": TLPosition.CENTER,
    "biblical_grounding": TLPosition.UPPER,
    "reality": TLPosition.UPPER,
    "hope": TLPosition.LOWER,
    "callout": TLPosition.LOWER,
    "loop": TLPosition.LOWER,
    "emphasis": TLPosition.CENTER,
    "bridge": TLPosition.CENTER,
    "payoff": TLPosition.CENTER,
}


def role_to_position(role: SBNarrativeRole) -> TLPosition:
    return _ROLE_TO_POSITION.get(
        role.value if not isinstance(role, str) else role,
        TLPosition.CENTER,
    )


# Mapeo Platform (formato de salida) → Platform de text_layout.
def platform_to_text_layout_platform(format_name: str) -> TLPlatform:
    fmt = (format_name or "short").lower()
    if "youtube" in fmt or "horizontal" in fmt or "16" in fmt:
        return TLPlatform.YOUTUBE_HORIZONTAL
    if "facebook" in fmt or "fb" in fmt:
        return TLPlatform.FACEBOOK_VERTICAL
    return TLPlatform.SHORT_VERTICAL


# ────────────────────────────────────────────────
# Escenas para render (SceneBrief → scene_dict plano)
# ────────────────────────────────────────────────

# Mapeo PreferredSource → claves del dict de escena existente.
_SOURCE_TO_KEYS: dict[str, list[str]] = {
    "ai": ["ai"],
    "ai_video": ["ai_video"],
    "stock": ["stock"],
    "photo_stock": ["photo_stock"],
    "local": ["stock_video"],
    "commons": ["q"],
}


def _resolve_source_keys(brief: SceneBrief) -> list[str]:
    """Qué claves del scene_dict debe activar una fuente preferida."""
    src = brief.preferred_source
    return _SOURCE_TO_KEYS.get(
        src.value if hasattr(src, "value") else str(src).lower(),
        ["ai"],
    )


def _motion_to_str(motion: MotionType | str) -> str:
    # MotionType extends str, así que hay que detectar el enum ANTES que el str
    # para devolver el valor plano ("zoom-in") y no el miembro del enum.
    if isinstance(motion, MotionType):
        return motion.value
    if isinstance(motion, str):
        return motion
    return "zoom-in"


def _transition_to_dict(trans: TransitionType | str) -> dict:
    style = trans.value if hasattr(trans, "value") else str(trans)
    mapping = {
        "cut": {"style": "cut", "dur": 0.0},
        "dissolve": {"style": "fade", "dur": 0.5},
        "blur": {"style": "blur", "dur": 0.6},
        "flash": {"style": "flash", "dur": 0.5},
        "black": {"style": "black", "dur": 0.6},
        "fade": {"style": "fade", "dur": 0.5},
    }
    return mapping.get(style, {"style": "fade", "dur": 0.5})


def scene_brief_to_render_scene_dict(
    brief: SceneBrief,
    *,
    index: int = 0,
    ai_prompt_override: str | None = None,
) -> dict[str, Any]:
    """Convierte un SceneBrief a un scene_dict plano legible por la cadena
    de render existente (hacer_video_caverna / hacer_video_youtube).

    No inventa reglas por tema: usa exclusivamente los campos del SceneBrief.
    """
    d: dict[str, Any] = {
        "id": brief.scene_id or f"e{index:02d}",
        "text": brief.narration,
    }

    # Fuentes visuales según preferred_source / fallback_source
    source_keys = _resolve_source_keys(brief)
    if "ai" in source_keys:
        d["ai"] = ai_prompt_override or brief.ai_prompt or brief.visual_event
    if "q" in source_keys:
        d["q"] = brief.pexels_queries[0] if brief.pexels_queries else brief.setting
    if "stock" in source_keys:
        d["stock"] = True
        if brief.pexels_queries:
            d["q"] = brief.pexels_queries[0]
    if "photo_stock" in source_keys:
        d["photo_stock"] = True
        if brief.pexels_queries:
            d["q"] = brief.pexels_queries[0]
    if "ai_video" in source_keys:
        d["ai_video"] = True
        if brief.ai_prompt:
            d["av"] = brief.ai_prompt
    if "stock_video" in source_keys:
        d["stock_video"] = f"e{index:02d}.mp4"

    # Fallback Commons si preferred no trajo query y hay fallback commmons
    fb = brief.fallback_source
    fb_val = fb.value if hasattr(fb, "value") else str(fb)
    if "q" not in d and fb_val == "commons" and brief.pexels_queries:
        d["q"] = brief.pexels_queries[0]

    # Cámara
    motion = _motion_to_str(brief.motion)
    if motion and motion != "none":
        d["motion"] = motion
    # Transición
    if brief.transition:
        d["trans"] = _transition_to_dict(brief.transition)

    # Texto en pantalla (si el guion provee texto estático)
    if brief.on_screen_text:
        d["static_text"] = brief.on_screen_text

    return d


# ────────────────────────────────────────────────
# Text Layout (SceneBrief → TextLayoutRequest)
# ────────────────────────────────────────────────


def scene_brief_to_text_layout_request(
    brief: SceneBrief,
    *,
    format_name: str = "short",
    canvas_width: int = 1080,
    canvas_height: int = 1920,
) -> TextLayoutRequest:
    """Construye un TextLayoutRequest a partir de un SceneBrief.

    Usa la narración como texto, el rol narrativo para tamaño/posición,
    y el formato para el preset de plataforma de text_layout.
    """
    platform = platform_to_text_layout_platform(format_name)

    # Ajustes por formato por defecto
    if platform == TLPlatform.YOUTUBE_HORIZONTAL:
        safe = {"top": 120, "bottom": 160, "left": 200, "right": 200}
        max_width = 1920 - 200 - 200
        pref = 64
        # El lienzo 16:9, salvo que el llamador pase dims explícitas de 1920x1080
        if canvas_width < 1920 or canvas_height > 1600:
            canvas_width, canvas_height = 1920, 1080
    else:
        safe = {"top": 120, "bottom": 192, "left": 90, "right": 90}
        max_width = 1080 - 90 - 90
        pref = 76
        if canvas_width > 1500 or canvas_height < 1500:
            canvas_width, canvas_height = 1080, 1920

    role = role_to_text_layout_role(brief.narrative_role or SBNarrativeRole.BRIDGE)
    position = role_to_position(brief.narrative_role or SBNarrativeRole.BRIDGE)

    return TextLayoutRequest(
        text=brief.narration,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        safe_area=safe,
        preferred_font_size=pref,
        min_font_size=56,
        max_font_size=120,
        max_width=max_width,
        preferred_position=position,
        alignment=TLAlignment.CENTER,
        narrative_role=role,
        platform=platform,
    )
