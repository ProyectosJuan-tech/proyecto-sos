"""
V2-05 — PRODUCIR_VIDEO: punto de entrada CLI del motor editorial V2.

Uso:
    python3 producir_video.py --formato short   --tema "..." --idea "..."
    python3 producir_video.py --formato youtube --tema "..." --idea "..."
    python3 producir_video.py --teste

Recorre IDEA → plan → briefs → assets → layouts y emite los scene_dicts
listos para el renderer existente. NO renderiza (el pipeline legacy sigue
siendo el responsable de materializar el video).

El feature flag --engine=v2 es explícito: sin él, el script no hace nada
(protege las rutas legacy).
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Motor editorial V2")
    parser.add_argument("--engine", default="v2", choices=["v2"],
                        help="Feature flag: solo existe engine=v2")
    parser.add_argument("--formato", default="short",
                        choices=["short", "youtube", "16:9", "16x9"],
                        help="Formato: short (9:16) o youtube (16:9)")
    parser.add_argument("--tema", default="", help="Tema del contenido")
    parser.add_argument("--idea", default="", help="Idea central")
    parser.add_argument("--cta", default="", help="Call to action")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Salida en JSON")
    parser.add_argument("--teste", action="store_true",
                        help="Ejecuta la prueba rápida de integración")
    args = parser.parse_args(argv)

    if args.teste:
        return _run_selftest()

    if args.engine != "v2":
        sys.stderr.write("Motor desconocido (solo v2). Abortando.\n")
        return 1

    if not args.tema or not args.idea:
        sys.stderr.write("Se requieren --tema y --idea.\n")
        return 2

    from editorial_orchestrator import produce_editorial
    em = produce_editorial(
        topic=args.tema,
        central_idea=args.idea,
        format_name=args.formato,
        cta=args.cta,
    )

    report = em.to_report()
    if args.as_json:
        payload = {
            "report": report,
            "scenes": [scene_brief_to_payload(b) for b in em.briefs],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"== {args.formato.upper()} ==")
    print(f"Resolución: {report['resolution']}")
    print(f"Escenas: {report['n_scenes']} | Duración: {report['total_duration_s']}s")
    for i, (b, sd) in enumerate(zip(em.briefs, em.scene_dicts)):
        print(f"  e{i+1:02d} [{b.narrative_role.value}] {sd.get('ai') or sd.get('q','')[:40]}")
        print(f"      texto: {b.narration[:70]}")
    print("OK: cadena editorial completada. scene_dicts listos para render.")
    return 0


def scene_brief_to_payload(b) -> dict:
    return {
        "id": b.scene_id,
        "role": b.narrative_role.value,
        "narration": b.narration,
        "ai": b.ai_prompt or b.visual_event,
        "duration": b.duration,
        "motion": b.motion.value if hasattr(b.motion, "value") else str(b.motion),
        "transition": b.transition.value if hasattr(b.transition, "value") else str(b.transition),
    }


def _run_selftest() -> int:
    from scene_brief import NarrativeRole
    from editorial_orchestrator import produce_editorial, LongFormPlan, validate_long_plan
    from short_director import validate_plan

    em = produce_editorial(
        topic="descanso",
        central_idea="cuesta descansar aunque estemos cansados",
        format_name="short",
    )
    plan = em.plan
    v = validate_plan(plan)
    print(f"[selftest short] escenas={len(em.briefs)} "
          f"dur={plan.estimate_total_duration():.1f}s valid={v['valid']}")

    em2 = produce_editorial(
        topic="valor",
        central_idea="algunas personas sienten que siempre tienen que demostrar su valor",
        format_name="youtube",
    )
    plan2 = em2.plan
    v2 = validate_long_plan(plan2)
    print(f"[selftest youtube] escenas={len(em2.briefs)} "
          f"dur={plan2.estimate_total_duration():.1f}s valid={v2['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
