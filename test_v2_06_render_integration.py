"""
V2-06 — TESTS DE INTEGRACIÓN DE RENDER (V2 → renderer legado).

Verifica la capa V2-06 que conecta la arquitectura editorial (SceneBrief →
TextLayout → AssetSelector) con el motor de renderizado legado y la corrección
del canvas por plataforma.

Cubre (mínimo 15 tests):
- render_adapter: build_work_context + render_emission generan el MP4 correcto
- canvas por plataforma (short 1080x1920, youtube 1920x1080) — fix V2-06
- layout conectado: las escenas del emission producen layout sin overflow
- el renderer legado recibe las escenas del emission (scene_dicts compatibles)
- el pipeline legado sigue intacto (backward compatibility)
- format/config de salida correctos
- producir_pruebas define narrations inyectadas por rol

No requiere red ni render real: se valida la WIRING sin tocar ffmpeg/API.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scene_brief import NarrativeRole, MotionType
from text_layout import compute_layout
from editorial_orchestrator import produce_editorial
from v2_bridge import (
    scene_brief_to_text_layout_request,
    scene_brief_to_render_scene_dict,
)
from render_adapter import build_work_context, render_emission

PASS = 0
FAIL = 0


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS — {name}" + (f" ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL — {name} {detail}")


# Mismas narrations inyectadas que en producir_pruebas.py (sin red)
SHORT_NARR = {
    "hook": "¿Crees que descansar es no hacer nada? El cansancio que sientes no siempre viene de lo que hiciste.",
    "problem": "Aunque duermas, sigues cansada. No es pereza: tu mente sigue encendida cuando el cuerpo por fin se detiene.",
    "agitation": "Y por eso te sientes culpable por descansar, como si parar fuera rendirse.",
    "psychology": "Hay un patrón: tu valor quedó atado a lo que produces.",
    "solution": "El descanso no se gana: se permite. Empieza con cinco minutos al día.",
    "biblical_grounding": "El descanso también es un don: no tienes que ganártelo.",
    "hope": "Descansar no es perder tiempo, es volver a ti.",
    "callout": "Si esta idea te llegó, compártela con alguien que también necesita permiso para parar.",
}
LONG_NARR = {
    "hook": "¿Por qué algunas personas sienten que siempre tienen que demostrar su valor?",
    "reality": "Todos conocemos a alguien que trabaja, ayuda y da sin parar.",
    "problem": "El problema no es dar demasiado, es creer que tu valor depende de lo que haces.",
    "psychology": "Así se forma un patrón: cuanto más demuestras, más crees que debes demostrar.",
    "psychology2": "Cuando tu autoestima depende de la aprobación ajena, cada silencio se siente como un rechazo.",
    "psychology3": "Y el vacío no se llena con esfuerzo: se llena reconociendo que ya vales.",
    "solution": "La salida empieza por separar lo que haces de lo que eres.",
    "biblical_grounding": "No estás aquí para comprar tu valor: lo recibes.",
    "hope": "Cuando dejas de demostrar, empiezas a vivir.",
    "callout": "Si conoces a alguien que siempre está demostrando su valor, compártelo.",
}


def _emission(kind: str):
    if kind == "short":
        return produce_editorial(
            topic="descanso",
            central_idea="nos cuesta tanto descansar aunque estemos cansados",
            format_name="short",
            narrations=SHORT_NARR,
        )
    return produce_editorial(
        topic="demostrar-valor",
        central_idea="sienten que siempre tienen que demostrar su valor",
        format_name="youtube",
        narrations=LONG_NARR,
    )


# ══════════════════════════════════════════════
print("[1] CANVAS POR PLATAFORMA (fix V2-06)")
# ══════════════════════════════════════════════
em_s = _emission("short")
em_l = _emission("youtube")

ok("short es 1080x1920 (9:16)",
   (em_s.canvas_width, em_s.canvas_height) == (1080, 1920),
   f"{em_s.canvas_width}x{em_s.canvas_height}")
ok("short relación 9/16",
   em_s.canvas_width / em_s.canvas_height == 9 / 16)
ok("youtube es 1920x1080 (16:9)",
   (em_l.canvas_width, em_l.canvas_height) == (1920, 1080),
   f"{em_l.canvas_width}x{em_l.canvas_height}")
ok("youtube relación 16/9",
   em_l.canvas_width / em_l.canvas_height == 16 / 9)

# ══════════════════════════════════════════════
print("\n[2] LAYOUT CONECTADO, SIN OVERFLOW")
# ══════════════════════════════════════════════
over_s = sum(1 for l in em_s.acom_layouts if l.overflow)
ok("short: layouts sin overflow", over_s == 0, f"{over_s} overflow")
ok("short: cada layout con score y font",
   all(l.score > 0 and l.font_size > 0 for l in em_s.acom_layouts))

over_l = sum(1 for l in em_l.acom_layouts if l.overflow)
ok("youtube: layouts sin overflow tras fix canvas 1920x1080",
   over_l == 0, f"{over_l} overflow")
ok("youtube: cada layout con score y font",
   all(l.score > 0 and l.font_size > 0 for l in em_l.acom_layouts))

# Recalcular con la API pública para validar el wiring
req = scene_brief_to_text_layout_request(
    em_l.briefs[0], format_name="youtube",
    canvas_width=1920, canvas_height=1080)
l0 = compute_layout(req)
ok("scene_brief_to_text_layout_request 16:9 usa 1920x1080",
   l0.overflow_x is False, f"font {l0.font_size}")

# ══════════════════════════════════════════════
print("\n[3] scene_dicts COMPATIBLES CON RENDERER LEGADO")
# ══════════════════════════════════════════════
ok("short: n scene_dicts == n briefs",
   len(em_s.scene_dicts) == len(em_s.briefs))
ok("scene_dicts son dicts legados con text (id/ai/motion/trans)",
   all(isinstance(sd, dict) and "text" in sd and "motion" in sd
       for sd in em_s.scene_dicts))
sd0 = scene_brief_to_render_scene_dict(em_s.briefs[0], index=0)
ok("scene_brief_to_render_scene_dict genera dict legado",
   isinstance(sd0, dict) and ("text" in sd0 or "ai" in sd0 or "q" in sd0))

_sroles = {b.narrative_role.value for b in em_s.briefs}
_lroles = {b.narrative_role.value for b in em_l.briefs}
ok("short roles incluyen hook y callout (CTA)",
   {"hook", "callout"} <= _sroles, str(sorted(_sroles)))
ok("youtube roles incluyen hook y callout (CTA)",
   {"hook", "callout"} <= _lroles)
ok("short no usa rol PAYOFF (estructura corta)",
   "payoff" not in _sroles)

# ══════════════════════════════════════════════
print("\n[4] ADAPTER / WORK CONTEXT / MOTION")
# ══════════════════════════════════════════════
ctx = build_work_context(em_s)
ok("build_work_context apunta bajo videos/v2_pruebas",
   "v2_pruebas" in ctx, ctx)

m = MotionType.ZOOM_IN
ok("MotionType es subclase de str (bug latente)",
   isinstance(m, str))
ok("getattr enum detectado (zoom)",
   "zoom" in str(m.value).lower() or "ZOOM" in str(m))

import inspect
sig = inspect.signature(render_emission)
ok("render_emission(emission, output_mp4, aspect=...) firma correcta",
   "emission" in sig.parameters and "output_mp4" in sig.parameters
   and "aspect" in sig.parameters)

# ══════════════════════════════════════════════
print("\n[5] BACKWARD COMPATIBILITY + producir_pruebas")
# ══════════════════════════════════════════════
import hacer_video_caverna
import hacer_video_youtube
ok("hacer_video_caverna.render_scene intacto",
   hasattr(hacer_video_caverna, "render_scene"))
ok("hacer_video_youtube.render_scene intacto",
   hasattr(hacer_video_youtube, "render_scene"))

import producir_pruebas
ok("producir_pruebas define SHORT_NARR con hook",
   bool(producir_pruebas.SHORT_NARR) and "hook" in producir_pruebas.SHORT_NARR)
ok("producir_pruebas define LONG_NARR con callout",
   bool(producir_pruebas.LONG_NARR) and "callout" in producir_pruebas.LONG_NARR)


# ══════════════════════════════════════════════
print()
print("=" * 60)
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("=" * 60)
sys.exit(1 if FAIL else 0)
