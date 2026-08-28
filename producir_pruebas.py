"""
V2-06 — PRODUCIR_PRUEBAS: genera los DOS MP4 reales de prueba.

A) Short 9:16 — "Por qué nos cuesta tanto descansar aunque estemos cansados"
B) 16:9    — "Por qué algunas personas sienten que siempre tienen que
              demostrar su valor"

Flujo real V2: produce_editorial(topic, idea, format) → scene_dicts → render_adapter → MP4.
No hardcodea un pipeline nuevo; reutiliza el renderer legacy.

Los outputs van a videos/v2_pruebas/ (ignorados por .gitignore).
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_orchestrator import produce_editorial
from render_adapter import render_emission, build_work_context
from text_layout import compute_layout
from v2_bridge import scene_brief_to_text_layout_request

OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", "v2_pruebas")


# ── Narraciones por rol para cada tema (flujo editorial real, texto aprobado-esque) ──
SHORT_NARR = {
    "hook": "¿Crees que descansar es no hacer nada? El cansancio que sientes no siempre viene de lo que hiciste.",
    "problem": "Aunque duermas, sigues cansada. No es pereza: tu mente sigue encendida cuando el cuerpo por fin se detiene.",
    "agitation": "Y por eso te sientes culpable por descansar, como si parar fuera rendirse. Y ese ruido no te deja recuperar energías.",
    "psychology": "Hay un patrón: tu valor quedó atado a lo que produces. Y cuando no produces, tu mente no te deja soltar.",
    "solution": "El descanso no se gana: se permite. Empieza con cinco minutos al día mirando el cielo, sin móvil, sin culpa.",
    "biblical_grounding": "El descanso también es un don: no tienes que ganártelo, puedes recibirlo.",
    "hope": "Descansar no es perder tiempo, es volver a ti. Y eso es lo que te permite vivir mejor.",
    "callout": "Si esta idea te llegó, compártela con alguien que también necesita permiso para parar.",
}

LONG_NARR = {
    "hook": "¿Por qué algunas personas sienten que siempre tienen que demostrar su valor?",
    "reality": "Todos conocemos a alguien que trabaja, ayuda y da sin parar, y aun así nunca se siente suficiente.",
    "problem": "El problema no es dar demasiado, es creer que tu valor depende de lo que haces por los demás.",
    "psychology": "Así se forma un patrón: cuanto más demuestras, más crees que debes demostrar. Y nadie te aplaude tanto como tú lo necesitas.",
    "psychology2": "Cuando tu autoestima depende de la aprobación ajena, cada silencio se siente como un rechazo y cada descuido como una prueba de que no vales.",
    "psychology3": "Y aunque lo intentas una y otra vez, el vacío no se llena con esfuerzo: se llena reconociendo que ya vales.",
    "solution": "La salida empieza por separar lo que haces de lo que eres. Un límite claro no hace que valgas menos: te protege.",
    "biblical_grounding": "No estás aquí para comprar tu valor: lo recibes. Nadie tiene que demostrar su derecho a ser amado.",
    "hope": "Cuando dejas de demostrar, empiezas a vivir. Y eso se nota en el cuerpo, en el ánimo y en cómo te tratan.",
    "callout": "Si conoces a alguien que siempre está demostrando su valor, compártelo: puede ser la primera vez que alguien se lo dice.",
}


def _run():
    os.makedirs(OUT_ROOT, exist_ok=True)
    results = {}

    # ── CASO A: Short ──
    print("\n=== CASO A: SHORT 9:16 ===", flush=True)
    em_s = produce_editorial(
        topic="descanso",
        central_idea="nos cuesta tanto descansar aunque estemos cansados",
        format_name="short",
        narrations=SHORT_NARR,
    )
    # Recalcular layouts (el scaffold no recalcula los layouts con narrations inyectadas)
    short_mp4 = os.path.join(OUT_ROOT, "prueba_short_9x16.mp4")
    wd_s = build_work_context(em_s)

    # Registrar layouts reales por escena (con las narrations inyectadas)
    layouts_s = []
    for b in em_s.briefs:
        req = scene_brief_to_text_layout_request(
            b, format_name="short",
            canvas_width=em_s.canvas_width, canvas_height=em_s.canvas_height,
        )
        layouts_s.append(compute_layout(req))

    print("  escenas:", [b.narrative_role.value for b in em_s.briefs], flush=True)
    print(f"  render → {short_mp4}", flush=True)
    short_mp4 = render_emission(em_s, short_mp4, work_dir=wd_s, aspect="vertical")
    results["short"] = {
        "mp4": short_mp4, "format": "short", "w": em_s.canvas_width,
        "h": em_s.canvas_height, "w_expected": 1080, "h_expected": 1920,
        "n_scenes": len(em_s.briefs),
        "layouts": [{"font": l.font_size, "lines": len(l.lines), "score": round(l.score, 1),
                     "overflow": l.overflow, "status": l.status} for l in layouts_s],
        "roles": [b.narrative_role.value for b in em_s.briefs],
    }

    # ── CASO B: 16:9 ──
    print("\n=== CASO B: 16:9 ===", flush=True)
    em_l = produce_editorial(
        topic="demostrar-valor",
        central_idea="sienten que siempre tienen que demostrar su valor",
        format_name="youtube",
        narrations=LONG_NARR,
    )
    yt_mp4 = os.path.join(OUT_ROOT, "prueba_16x9.mp4")
    wd_l = build_work_context(em_l)

    layouts_l = []
    for b in em_l.briefs:
        req = scene_brief_to_text_layout_request(
            b, format_name="youtube",
            canvas_width=em_l.canvas_width, canvas_height=em_l.canvas_height,
        )
        layouts_l.append(compute_layout(req))

    print("  escenas:", [b.narrative_role.value for b in em_l.briefs], flush=True)
    print(f"  render → {yt_mp4}", flush=True)
    yt_mp4 = render_emission(em_l, yt_mp4, work_dir=wd_l, aspect="horizontal")
    results["youtube"] = {
        "mp4": yt_mp4, "format": "youtube", "w": em_l.canvas_width,
        "h": em_l.canvas_height, "w_expected": 1920, "h_expected": 1080,
        "n_scenes": len(em_l.briefs),
        "layouts": [{"font": l.font_size, "lines": len(l.lines), "score": round(l.score, 1),
                     "overflow": l.overflow, "status": l.status} for l in layouts_l],
        "roles": [b.narrative_role.value for b in em_l.briefs],
    }

    with open(os.path.join(OUT_ROOT, "resultados.json"), "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nResumen guardado en", os.path.join(OUT_ROOT, "resultados.json"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(_run())
