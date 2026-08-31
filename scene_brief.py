"""
scene_brief.py — Contrato común para escenas del pipeline audiovisual.

SceneBrief es la estructura de datos que conecta:
  Director Editorial → Director Visual → Asset Selector → Render → QA

Diseñado para ser compatible con:
  - director_visual.py (compose_prompt, direct)
  -Escenas existentes (dict plano en SHORTS/VIDEOS/*_scenes.py)
  - El render actual (hacer_video_caverna.py, hacer_video_youtube.py)

NO reemplaza ningún sistema existente. Es una capa nueva que puede
convivir con el código actual mientras se migra incrementalmente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ─────────────────────────────────────────────
# Enums para valores controlados
# ─────────────────────────────────────────────

class SceneType(str, Enum):
    """Tipos de escena según su función narrativa."""
    SHORT = "short"
    LONG = "long"
    TRANSITION = "transition"
    INTRO = "intro"
    OUTRO = "outro"
    EMPHASIS = "emphasis"


class NarrativeRole(str, Enum):
    """Rol narrativo de la escena dentro del video."""
    HOOK = "hook"              # Gancho inicial (primeros 3s)
    PROBLEM = "problem"        # Plantea el problema
    AGITATION = "agitation"    # Consecuencia / intensificación
    SOLUTION = "solution"      # Resolución / método
    PAYOFF = "payoff"          # Cierre satisfactorio
    LOOP = "loop"              # Enganche para re-ver
    BRIDGE = "bridge"          # Conexión entre secciones
    EMPHASIS = "emphasis"      # Punto fuerte / énfasis
    CALLOUT = "callout"        # CTA / llamada a la acción
    REALITY = "reality"        # Verdad directa sin adornos
    PSYCHOLOGY = "psychology"  # Comprensión del patrón humano
    BIBLICAL_GROUNDING = "biblical_grounding"  # Conexión con la fe
    HOPE = "hope"              # Esperanza — luz al final del túnel


class PreferredSource(str, Enum):
    """Fuente preferida para el fondo visual de la escena."""
    AI = "ai"                  # Imagen generada por IA
    STOCK = "stock"            # Video stock de Pexels
    PHOTO_STOCK = "photo_stock"  # Foto stock de Pexels (V2-FINAL)
    AI_VIDEO = "ai_video"     # Video generado por IA
    LOCAL = "local"            # Archivo local existente
    COMMONS = "commons"        # Wikimedia Commons fallback


class MotionType(str, Enum):
    """Tipos de movimiento de cámara (Ken Burns)."""
    ZOOM_IN = "zoom-in"
    ZOOM_OUT = "zoom-out"
    PAN_RIGHT = "pan-right"
    PAN_LEFT = "pan-left"
    PAN_DOWN = "pan-down"
    STATIC = "static"
    NONE = "none"


class TransitionType(str, Enum):
    """Tipos de transición entre escenas."""
    FADE = "fade"
    CUT = "cut"
    DISSOLVE = "dissolve"
    BLUR = "blur"
    FLASH = "flash"
    BLACK = "black"


# ─────────────────────────────────────────────
# Dataclass principal
# ─────────────────────────────────────────────

@dataclass
class SceneBrief:
    """
    Contrato de escena para el pipeline audiovisual.

    Contiene toda la información necesaria para que cada capa del pipeline
    (dirección visual, selección de assets, render, QA) pueda trabajar
    con una estructura única y validada.

    Ejemplo mínimo válido::

        SceneBrief(
            scene_id="e01",
            narration="Tu cansancio no viene de lo que haces.",
            visual_event="Mujer dejando una taza sobre la mesa después de una conversación difícil",
            action="dejar la taza lentamente",
            setting="cocina cálida por la mañana",
        )
    """

    # ── IDENTIDAD ──
    scene_id: str = ""
    scene_type: SceneType = SceneType.SHORT
    narrative_role: NarrativeRole = NarrativeRole.BRIDGE

    # ── NARRACIÓN ──
    narration: str = ""
    emotional_core: str = ""

    # ── VISUAL ──
    visual_event: str = ""
    subject: str = ""
    action: str = ""
    setting: str = ""
    symbol: str = ""
    subject_priority: str = ""

    # ── CÁMARA ──
    shot: str = ""
    composition: str = ""
    camera: str = ""
    camera_motion: MotionType = MotionType.ZOOM_IN

    # ── LUZ / ESTÉTICA ──
    lighting: str = ""
    color: str = ""
    visual_style: str = ""
    style_family: str = ""

    # ── FUENTES ──
    preferred_source: PreferredSource = PreferredSource.AI
    fallback_source: PreferredSource = PreferredSource.COMMONS
    pexels_queries: list[str] = field(default_factory=list)
    ai_prompt: str = ""

    # ── MONTAJE ──
    duration: float = 0.0
    transition: TransitionType = TransitionType.FADE
    motion: MotionType = MotionType.ZOOM_IN

    # ── TEXTO ──
    on_screen_text: list[str] = field(default_factory=list)
    text_space: str = ""

    # ── CONTINUIDAD / QA ──
    continuity_group: str = ""
    visual_risks: dict[str, str] = field(default_factory=dict)
    visual_priority: int = 0

    # ── V2.7 INTELIGENCIA VISUAL DE MEDIOS (opcional, no rompe V2.6) ──
    # Dict serializable con la información estructural derivada para esta escena.
    # Lo puebla media_intelligence.py (visual keywords + estrategia de fuente).
    visual_keywords: dict = field(default_factory=dict)   # VisualKeywords.to_dict()
    media_strategy: dict = field(default_factory=dict)    # MediaSourceStrategy.to_dict()
    selected_source: str = ""                             # fuente efectiva (descubrimiento+score)

    # ── METADATA ──
    language: str = "es"
    locale: str = "es-419"
    register: str = "neutro"

    # ─────────────────────────────────────────
    # Validación
    # ─────────────────────────────────────────

    def validate(self) -> dict[str, Any]:
        """
        Valida el SceneBrief y devuelve un reporte estructurado.

        Returns:
            dict con keys: valid (bool), errors (list), warnings (list)
        """
        errors: list[str] = []
        warnings: list[str] = []

        # ── ERRORS (bloquean) ──
        if not self.visual_event or not self.visual_event.strip():
            errors.append("visual_event vacío")
        if not self.action or not self.action.strip():
            errors.append("action vacío")
        if not self.setting or not self.setting.strip():
            errors.append("setting vacío")
        if self.duration <= 0:
            errors.append("duration <= 0")

        valid_sources = {s.value for s in PreferredSource}
        if self.preferred_source.value not in valid_sources:
            errors.append(f"preferred_source inválido: {self.preferred_source}")
        if self.fallback_source.value not in valid_sources:
            errors.append(f"fallback_source inválido: {self.fallback_source}")

        # ── WARNINGS (no bloquean) ──
        if not self.emotional_core or not self.emotional_core.strip():
            warnings.append("emotional_core ausente")
        if not self.symbol or not self.symbol.strip():
            warnings.append("symbol ausente")
        if not self.pexels_queries:
            warnings.append("pexels_queries vacías")
        if not self.ai_prompt or not self.ai_prompt.strip():
            warnings.append("ai_prompt ausente")
        if not self.composition or not self.composition.strip():
            warnings.append("composition ausente")
        if not self.lighting or not self.lighting.strip():
            warnings.append("lighting ausente")
        if not self.camera or not self.camera.strip():
            warnings.append("camera ausente")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    # ─────────────────────────────────────────
    # Serialización
    # ─────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Convierte a dict plano (serializable)."""
        d = asdict(self)
        # Convert enums a sus values
        for key in ("scene_type", "narrative_role", "preferred_source",
                     "fallback_source", "camera_motion", "motion", "transition"):
            val = d[key]
            if isinstance(val, Enum):
                d[key] = val.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SceneBrief:
        """Reconstruye un SceneBrief desde un dict."""
        if not data:
            return cls()

        # Mapear enums de forma segura
        def _safe_enum(enum_cls, value):
            if value is None:
                return None
            try:
                return enum_cls(value)
            except (ValueError, KeyError):
                return None

        # Extraer campos conocidos, ignorar extras
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {}
        for k, v in data.items():
            if k in known_fields:
                filtered[k] = v

        # Parsear enums
        if "scene_type" in filtered:
            e = _safe_enum(SceneType, filtered["scene_type"])
            if e:
                filtered["scene_type"] = e
            else:
                del filtered["scene_type"]
        if "narrative_role" in filtered:
            e = _safe_enum(NarrativeRole, filtered["narrative_role"])
            if e:
                filtered["narrative_role"] = e
            else:
                del filtered["narrative_role"]
        if "preferred_source" in filtered:
            e = _safe_enum(PreferredSource, filtered["preferred_source"])
            if e:
                filtered["preferred_source"] = e
            else:
                del filtered["preferred_source"]
        if "fallback_source" in filtered:
            e = _safe_enum(PreferredSource, filtered["fallback_source"])
            if e:
                filtered["fallback_source"] = e
            else:
                del filtered["fallback_source"]
        if "camera_motion" in filtered:
            e = _safe_enum(MotionType, filtered["camera_motion"])
            if e:
                filtered["camera_motion"] = e
            else:
                del filtered["camera_motion"]
        if "motion" in filtered:
            e = _safe_enum(MotionType, filtered["motion"])
            if e:
                filtered["motion"] = e
            else:
                del filtered["motion"]
        if "transition" in filtered:
            e = _safe_enum(TransitionType, filtered["transition"])
            if e:
                filtered["transition"] = e
            else:
                del filtered["transition"]

        return cls(**filtered)

    def to_json(self, indent: int = 2) -> str:
        """Serializa a JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> SceneBrief:
        """Deserializa desde JSON."""
        return cls.from_dict(json.loads(text))

    # ─────────────────────────────────────────
    # Compatibilidad con director_visual.py
    # ─────────────────────────────────────────

    def to_compose_dict(self) -> dict[str, Any]:
        """
        Genera el dict que compose_prompt() de director_visual.py espera.

        Mapeo de campos SceneBrief → compose_prompt():
          visual_event  → visual_event
          symbol        → symbol
          setting       → setting
          lighting      → light
          camera        → camera
          action        → action (si difiere de visual_event)
          color         → color
          composition   → composition
          text_space    → text_space
          visual_style  → style
          subject_priority → subject_priority
          visual_risks  → risks
          style_family  → style_family
          emotional_core → emotional_core (requerido pero no incluido en prompt)
        """
        d: dict[str, Any] = {
            "emotional_core": self.emotional_core or "general wellbeing",
            "visual_event": self.visual_event,
            "symbol": self.symbol or "a simple everyday object",
            "setting": self.setting,
            "light": self.lighting or "soft natural window light",
            "camera": self.camera or "Medium shot on Sony A7IV, 50mm f/1.8",
        }

        # Campos opcionales — solo incluir si tienen contenido
        if self.action and self.action != self.visual_event:
            d["action"] = self.action
        if self.color:
            d["color"] = self.color
        if self.composition:
            d["composition"] = self.composition
        if self.text_space:
            d["text_space"] = self.text_space
        if self.visual_style:
            d["style"] = self.visual_style
        if self.subject_priority:
            d["subject_priority"] = self.subject_priority
        if self.visual_risks:
            d["risks"] = self.visual_risks
        if self.style_family:
            d["style_family"] = self.style_family

        return d

    # ─────────────────────────────────────────
    # Compatibilidad con escenas existentes
    # ─────────────────────────────────────────

    @classmethod
    def from_scene_dict(cls, data: dict[str, Any]) -> tuple[SceneBrief, list[str]]:
        """
        Convierte una escena existente (dict plano) a SceneBrief.

        Mapeo de campos del dict de escena → SceneBrief:
          text / prompt  → narration
          ai / prompt    → ai_prompt
          q              → pexels_queries (keywords)
          motion         → motion
          light          → lighting (bool → str)
          style          → visual_style
          static_text    → on_screen_text
          stock          → preferred_source
          stock_video    → preferred_source (LOCAL)
          ai_video       → preferred_source (AI_VIDEO)

        Returns:
            (SceneBrief, warnings) — warnings si faltan campos importantes
        """
        warnings: list[str] = []
        d = dict(data)  # copia

        # Narración
        narration = d.pop("text", "") or d.pop("narration", "")

        # Prompt de imagen
        ai_prompt = d.pop("ai", "") or d.pop("prompt", "")

        # Keywords para fallback
        q_raw = d.pop("q", "")
        pexels_queries = []
        if isinstance(q_raw, str) and q_raw.strip():
            pexels_queries = [k.strip() for k in q_raw.split() if k.strip()]
        elif isinstance(q_raw, list):
            pexels_queries = list(q_raw)

        # Motion
        motion_str = d.pop("motion", "zoom-in")
        motion = MotionType.ZOOM_IN
        try:
            motion = MotionType(motion_str)
        except (ValueError, KeyError):
            warnings.append(f"motion desconocido: {motion_str}")

        # Light → lighting
        light = d.pop("light", None)
        lighting = ""
        if light is True:
            lighting = "bright airy natural light"
        elif isinstance(light, str):
            lighting = light

        # Estilo
        visual_style = d.pop("style", "") or d.pop("estilo", "")

        # Texto en pantalla
        on_screen_text = d.pop("static_text", [])
        if isinstance(on_screen_text, str):
            on_screen_text = [on_screen_text]

        # Fuente preferida
        preferred_source = PreferredSource.AI
        if d.pop("stock", False):
            preferred_source = PreferredSource.STOCK
        elif d.pop("ai_video", False):
            preferred_source = PreferredSource.AI_VIDEO
        elif d.pop("stock_video", None):
            preferred_source = PreferredSource.LOCAL

        # ID
        scene_id = d.pop("id", "")

        # Duration (si existe)
        duration = d.pop("duration", 0.0)

        # Construir SceneBrief
        brief = cls(
            scene_id=scene_id,
            narration=narration,
            ai_prompt=ai_prompt,
            pexels_queries=pexels_queries,
            motion=motion,
            lighting=lighting,
            visual_style=visual_style,
            on_screen_text=on_screen_text,
            preferred_source=preferred_source,
            duration=duration,
        )

        # Warnings por campos faltantes
        if not brief.visual_event and not brief.ai_prompt:
            warnings.append("ni visual_event ni ai_prompt — no hay dirección visual")
        if not brief.setting:
            warnings.append("setting ausente")
        if not brief.action:
            warnings.append("action ausente")
        if not brief.emotional_core:
            warnings.append("emotional_core ausente")

        return brief, warnings


# ─────────────────────────────────────────────
# Función de conveniencia
# ─────────────────────────────────────────────

def scene_brief_from_dict(data: dict[str, Any]) -> SceneBrief:
    """
    Convierte un dict de escena existente a SceneBrief.

    Alias cómodo para SceneBrief.from_scene_dict() que descarta warnings.
    Para debugging, usar SceneBrief.from_scene_dict() directamente.
    """
    brief, _warnings = SceneBrief.from_scene_dict(data)
    return brief


def example_brief() -> SceneBrief:
    """
    Devuelve un SceneBrief de ejemplo basado en una escena real del canal.
    Útil para testing y documentación.
    """
    return SceneBrief(
        scene_id="e01",
        scene_type=SceneType.SHORT,
        narrative_role=NarrativeRole.HOOK,
        narration="Tu cansancio no viene de lo que haces.",
        emotional_core="agotamiento silencioso que no se va con descanso",
        visual_event="Mujer dejando lentamente una taza sobre la mesa después de una conversación difícil",
        subject="mujer adulta alrededor de 30",
        action="dejar la taza lentamente",
        setting="cocina cálida con luz de ventana por la mañana",
        symbol="una taza de té recién tomado",
        subject_priority="OBJETO",
        shot="medium shot",
        composition="text left third, subject right of center",
        camera="Sony A7IV, 50mm f/1.8, Portra 400",
        camera_motion=MotionType.ZOOM_IN,
        lighting="soft natural window light from the left, warm tones",
        color="warm amber and cream palette",
        visual_style="bright airy natural, cinematic still",
        style_family="C_objeto_narrativo_central",
        preferred_source=PreferredSource.AI,
        fallback_source=PreferredSource.COMMONS,
        pexels_queries=["hands tea", "morning window"],
        ai_prompt="Close-up of a woman's hand gently placing a ceramic tea cup on a wooden kitchen table. Morning sunlight streams through a window. Warm amber tones. Shallow depth of field.",
        duration=5.0,
        transition=TransitionType.FADE,
        motion=MotionType.ZOOM_IN,
        text_space="left third reserved for text overlay",
        visual_risks={"anatomical_risk": "LOW", "fusion_risk": "LOW"},
    )


# ─────────────────────────────────────────────
# Compatibilidad con director_visual.py
# ─────────────────────────────────────────────

def compose_prompt_from_brief(brief: SceneBrief) -> str:
    """
    Genera el prompt inglés usando director_visual.compose_prompt().

    Esta función NO duplica lógica — delega directamente en
    director_visual.compose_prompt() pasando el dict compatible.

    Raises:
        ValueError: si falta algún campo requerido por compose_prompt().
    """
    try:
        from director_visual import compose_prompt
    except ImportError:
        raise ImportError(
            "director_visual.py no está en el path. "
            "Asegurate de que esté en el mismo directorio o en PYTHONPATH."
        )

    d = brief.to_compose_dict()
    return compose_prompt(d)


def direct_from_brief(brief: SceneBrief, include_brain: bool = False) -> dict:
    """
    Genera la dirección visual completa desde un SceneBrief.

    Construye la dirección estructurada (PASO 1) y genera el prompt
    (PASO 2) usando compose_prompt(). NO usa direct() porque esa
    función está diseñada para escenas hardcodeadas con campo "final".

    Returns:
        dict con emotional_core, visual_event, symbol, body_language,
        environment, camera, light, message, prompt.
    """
    try:
        from director_visual import compose_prompt, DIRECTOR_BRAIN
    except ImportError:
        raise ImportError(
            "director_visual.py no está en el path. "
            "Asegurate de que esté en el mismo directorio o en PYTHONPATH."
        )

    # PASO 1 — Dirección estructurada
    result = {
        "emotional_core": brief.emotional_core or "general wellbeing",
        "visual_event": brief.visual_event,
        "symbol": brief.symbol or "a simple everyday object",
        "body_language": brief.action,
        "environment": brief.setting,
        "camera": brief.camera or "Medium shot on Sony A7IV, 50mm f/1.8",
        "light": brief.lighting or "soft natural window light",
        "message": brief.emotional_core,
    }

    # Campos opcionales
    if brief.subject_priority:
        result["subject_priority"] = brief.subject_priority
    if brief.action:
        result["action"] = brief.action
    if brief.setting:
        result["setting"] = brief.setting
    if brief.color:
        result["color"] = brief.color
    if brief.composition:
        result["composition"] = brief.composition
    if brief.text_space:
        result["text_space"] = brief.text_space
    if brief.visual_style:
        result["style"] = brief.visual_style
    if brief.visual_risks:
        result["risks"] = brief.visual_risks

    # PASO 2 — Prompt via compose_prompt()
    d = brief.to_compose_dict()
    result["prompt"] = compose_prompt(d)

    if include_brain:
        result["director_brain"] = DIRECTOR_BRAIN

    return result
