"""
V2.3 — Probe de integración real: render_adapter._download_with_quality_gate.

Valida que el gate quede cableado en el pipeline V2 sin romper la bajada de
imagen: genera/descarga 1 imagen real, la corre por el Quality Gate (visión
real), y devuelve (path, decision). Registra el log en tmp/quality_gate.json.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render_adapter as ra

scene = {
    "text": "Borrás una tarea de la lista por miedo a equivocarte.",
    "ai": "Close view of a to-do list on a desk near a sunny window, a pen "
          "hovering as if about to cross out a task, warm hopeful morning "
          "light, contemplative and calm, photorealistic, 9:16.",
    "q": "to do list morning light",
    "motion": "zoom-in",
}
work = "/tmp/opencode/qg_integration"
os.makedirs(os.path.join(work, "imgs"), exist_ok=True)
os.makedirs(os.path.join(work, "tmp"), exist_ok=True)

path, decision = ra._download_with_quality_gate(
    scene, 1, os.path.join(work, "imgs"), "vertical", work)

entry = {"scene": 1, "path": path, "decision": None if decision is None
         else decision.value}
with open(os.path.join(work, "TMP_resumen.json"), "w") as f:
    import json
    json.dump(entry, f, ensure_ascii=False, indent=2)

print("INTEGRATION PATH:", path)
print("INTEGRATION DECISION:", decision)
print("EXISTS:", bool(path and os.path.exists(path)))
print("SIZE:", os.path.getsize(path) if path and os.path.exists(path) else 0)
