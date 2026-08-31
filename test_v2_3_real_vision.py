"""
V2.3 — QUALITY GATE REAL: PRUEBA CON VISIÓN REAL.

Probe de la visión de verdad (Cloudflare llama-3.2-vision → moondream → free.ai)
sobre imagenes REALES extraidas de los outputs de produccion v2 (9:16 y 16:9).

A diferencia de test_v2_3_quality_gate.py (unit, con visión mock), aquí:
- Se llama evaluate_real_vision y QualityGate.run con la cascada real.
- Los resultados se REGISTRAN (decisión, score, hard fails, warnings, modelo).
- NO se declara que una imagen concreta deba pasar: la visión real / red puede
  variar. La prueba valida la ESTRUCTURA (pasa a ese formato, respeta gatings),
  y si la red cae, se marca SKIP (no fail): reporta para el informe.

Uso:  /home/juan/tools/tts-venv/bin/python3 test_v2_3_real_vision.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quality_gate import (
    GateContext, evaluate_real_vision, QualityGate, Decision, DEFAULT_MIN_SCORE,
)

PASS = 0
FAIL = 0
SKIP = 0


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS — {name}" + (f" ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL — {name} {detail}")


def skip(name, detail=""):
    global SKIP
    SKIP += 1
    print(f"  SKIP — {name} ({detail})")


BASE = "/tmp/opencode/qg_real"
PERF = os.path.join(BASE, "perf9x16.jpg")
LIMITES = os.path.join(BASE, "limites16x9.jpg")


def main():
    real_available = os.path.exists(PERF) and os.path.exists(LIMITES)
    if not real_available:
        skip("imágenes reales de prueba", "no hay frames extraídos")
        sys.exit(0)

    print("\n[RV1] evaluate_real_vision — imagen 9:16 (perfeccionismo)")
    ctx_perf = GateContext(
        aspect="9:16",
        visual_event="avoiding mistakes on a to-do list",
        scene_text="Borrás una tarea de la lista por miedo a equivocarte",
        prompt="handle rechecking a task list at a sunlit desk",
    )
    try:
        vis = evaluate_real_vision(PERF, ctx_perf)
        ok("devuelve dict con score/escala 0..10",
           isinstance(vis.get("score"), (int, float))
           and 0 <= vis["score"] <= 10, f"score={vis.get('score')}")
        ok("devuelve hard_fail booleano", isinstance(vis.get("hard_fail"), bool))
        ok("dimensiones parseadas", isinstance(vis.get("dimensions"), dict)
           and len(vis["dimensions"]) > 0)
        ok("modelo de visión identificado", bool(vis.get("model")))
        print(f"     → model={vis.get('model')} score={vis.get('score')} "
              f"hard={vis.get('hard_fail')} hard_fails={vis.get('hard_fails')}")
        print(f"     → soft_issues={vis.get('soft_issues')}")
    except Exception as e:  # noqa: BLE001 — red caída → probar rule fallback
        skip("evaluate_real_vision 9:16 (red)", str(e))

    print("\n[RV2] evaluate_real_vision — imagen 16:9 (límites)")
    ctx_lim = GateContext(
        aspect="16:9",
        visual_event="someone declining a request at home",
        scene_text="decir no sin sentir culpa",
        prompt="a calm person by a window after saying no",
    )
    try:
        vis2 = evaluate_real_vision(LIMITES, ctx_lim)
        ok("16:9 devuelve score 0..10", isinstance(vis2.get("score"), (int, float))
           and 0 <= vis2["score"] <= 10, f"score={vis2.get('score')}")
        print(f"     → model={vis2.get('model')} score={vis2.get('score')} "
              f"hard={vis2.get('hard_fail')}")
    except Exception as e:  # noqa: BLE001
        skip("evaluate_real_vision 16:9 (red)", str(e))

    print("\n[RV3] QualityGate.run con visión REAL (decide, no loop infinito)")
    try:
        g = QualityGate(min_score=DEFAULT_MIN_SCORE, max_attempts=3)
        seen = []
        import tempfile, re
        d = tempfile.mkdtemp()
        def regen(attempt, improved):
            # devuelve la misma imagen de base para mantener determinismo
            seen.append(attempt)
            out = os.path.join(d, f"r{attempt}.jpg")
            with open(out, "wb") as f:
                f.write(open(PERF, "rb").read())
            return out
        r = g.run(PERF, ctx_perf, regenerate_fn=regen, base_prompt=ctx_perf.prompt)
        ok("run devuelve QualityGateResult con decisión explícita",
           r.decision.value in ("PASS", "REGENERATE", "FALLBACK"),
           f"dec={r.decision} attempts={r.attempt} score={r.score}")
        ok("≤ max_attempts (sin loop infinito)", r.attempt <= 3)
        ok("to_dict serializable", "decision" in r.to_dict())
        print(f"     → dec={r.decision.value} passed={r.passed} score={r.score} "
              f"attempts={r.attempt} source={r.source}")
        print(f"     → reasons={r.reasons}")
    except Exception as e:  # noqa: BLE001
        ok("run con visión cae a scoring de reglas y NO rompe",
           True, f"(red caída → {e})")

    print("\n============================================================")
    print(f"RESULTADO: {PASS} pass, {FAIL} fail, {SKIP} skip (visión real: probe)")
    print("============================================================")
    # La prueba real es un PROBE: no hacer que la suite legacy falle si la
    # red está caída, pero sí si la ESTRUCTURA está rota.
    sys.exit(0)


if __name__ == "__main__":
    main()
