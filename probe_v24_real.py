# V2.4 — PROBE REAL (E2E opcional): prompt nuevo → generador real → gate regla.
# No es un test obligatorio: si Pollinations no responde (sin red / rate limit),
# se reporta honestamente y no rompe la fase. Valida que el prompt del PROVEEDOR
# ADAPTER llega al generador real y pasa las reglas estructurales del gate.
import os, sys, json, time

from editorial_orchestrator import build_editorial_plan
from narrative_visual_director import NarrativeVisualDirector
import flux_img

THEMES = [
    ("psicologia", "perfeccionismo", "el miedo al error te paraliza"),
    ("fe", "aprobacion", "la aprobación de otros no te define"),
    ("habitos", "habitos", "los pequeños hábitos construyen tu día"),
]

OUT = "/tmp/opencode/v24_real"
os.makedirs(OUT, exist_ok=True)
results = {}

for key, topic, idea in THEMES:
    try:
        plan, briefs = build_editorial_plan(
            topic=topic, central_idea=idea, format_name="short")
        dirs = NarrativeVisualDirector().direct_plan(briefs)
        base = dirs[0].prompt
        from visual_quality_engine import build_quality_prompt
        prompt = build_quality_prompt(base, canvas_ar="9:16", has_human=True)
        out_path = os.path.join(OUT, f"{key}_e01.jpg")
        # Generación real (Pollinations no-key)
        w_img = flux_img.generate(prompt, out_path, aspect="9:16", retries=1, wait=15)
        if not w_img or not os.path.exists(out_path):
            results[key] = {"status": "SKIPPED", "reason": "generador no devolvió imagen"}
            print(f"[{key}] SKIPPED — generador no devolvió imagen")
            continue
        # Gate determinista (reglas, sin red de visión)
        from quality_gate import QualityGate, GateContext
        ctx = GateContext(
            aspect="9:16",
            visual_event=dirs[0].visual_event,
            scene_text=briefs[0].narration,
            prompt=prompt,
        )
        gate = QualityGate(min_score=8.0, max_attempts=1, critic_fn=None)
        res = gate.run(out_path, ctx, regenerate_fn=None, base_prompt=prompt)
        results[key] = {
            "status": "GENERATED",
            "image": out_path,
            "size": f"{os.path.getsize(out_path)//1024}KB",
            "gate": res.decision.value,
            "score": res.score,
            "hard_fail": bool(res.hard_fail),
            "reasons": list(res.reasons)[:6],
        }
        print(f"[{key}] GENERATED {out_path} → gate {res.decision.value} (score {res.score})")
    except Exception as e:  # noqa: BLE001
        results[key] = {"status": "ERROR", "reason": str(e)[:200]}
        print(f"[{key}] ERROR — {str(e)[:160]}")

with open(os.path.join(OUT, "probe_v24_real.json"), "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nRESULTADO:", json.dumps(results, ensure_ascii=False))
