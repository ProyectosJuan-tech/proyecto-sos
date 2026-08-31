# V2 — PRUEBA REAL DE PRODUCCIÓN: "EL PERDÓN TE HACE LIBRE" (Short 9:16)
#
# Uso el sistema completo tal como está implementado (SIN modificar nada).
# Flujo real V2: produce_editorial(topic, idea, narrations, format) → scene_dicts
# → render_adapter.render_emission → MP4.
#
# El sistema decide TODA la maquinaria visual: estructura (roles/arco), visual_event,
# visual_strategy, composición/formato/realismo (V2.4 adapter), CTA (callout) e imágenes.
# Yo solo aporto el texto narrado (guion), como hace el harness real de producción.
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_orchestrator import produce_editorial
from render_adapter import render_emission, build_work_context

OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", "v2_pruebas", "perdon")

# ── GUION (texto narrado por rol; tuteo, sensible, fe+psicología integrada) ──
GUION = {
    "hook": "¿Cuántos años llevas cargando a alguien que ya no ocupa tu vida? Ese rencor pesa más que la persona que lo causó.",
    "problem": "No es debilidad tuya sentirte herido. El dolor es real, y negarlo no lo borra. El problema es que el dolor se vuelve una casa donde ya no vives tú, sino quien te lastimó.",
    "agitation": "Y lo más duro: quien te hirió quizás ni lo recuerda, mientras tú repites la escena a solas.",
    "psychology": "Perdonar no significa decir que estuvo bien, ni olvidar, ni volver a confiar, ni abrir la puerta para que vuelva a hacerte daño.",
    "solution": "Lo que esa persona hizo no cambia. Pero tú decides que aquello deje de ocupar tu presente. Suelta, no porque ellos lo merezcan: porque tú mereces tu paz.",
    "hope": "Devolver el perdón no es un favor a ellos: es devolverte a ti la paz que te quitaron. Y quien te conoce por tu nombre te invita a soltar la carga y vivir tu día.",
    # NOTA: la escena CALLOUT la decide el sistema (cta por defecto automática).
}


def ffprobe(mp4: str) -> dict:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
             "-show_streams", mp4],
            capture_output=True, text=True, timeout=60,
        ).stdout
        data = json.loads(out)
        fmt = data.get("format", {})
        v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
        return {
            "duration": round(float(fmt.get("duration", 0)), 2),
            "size_bytes": int(fmt.get("size", 0)),
            "video": f"{v.get('width')}x{v.get('height')}",
            "vcodec": v.get("codec_name"),
            "acodec": a.get("codec_name"),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def _load_gate_log(work_dir: str):
    """Lee el log del quality gate por escena (si existe)."""
    p = os.path.join(work_dir, "tmp", "quality_gate.json")
    rows = []
    if os.path.exists(p):
        for line in open(p):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def main() -> int:
    os.makedirs(OUT_ROOT, exist_ok=True)
    print("=== PRUEBA REAL: 'El perdón te hace libre' (Short 9:16) ===", flush=True)

    em = produce_editorial(
        topic="el perdón",
        central_idea="El perdón te hace libre",
        format_name="short",
        narrations=GUION,
    )

    mp4 = os.path.join(OUT_ROOT, "el_perdon_te_hace_libre_9x16.mp4")
    work_dir = build_work_context(em)
    print("escenas:", [b.narrative_role.value for b in em.briefs], flush=True)
    print("render →", mp4, flush=True)
    if os.path.exists(mp4) and os.path.getsize(mp4) > 0:
        # ya renderizado: no volver a renderizar (regenerar solo el informe)
        print("  (mp4 ya existe; se regenera solo el informe)", flush=True)
        render_ok = True
    else:
        try:
            render_emission(em, mp4, work_dir=work_dir, aspect="vertical")
        except Exception as e:  # noqa: BLE001 — documentar, NO entrar en loop
            print(f"\n[ERROR RENDER] {e}", flush=True)
            render_ok = False
        else:
            render_ok = os.path.exists(mp4)

    probe = ffprobe(mp4) if render_ok else {"error": "no se generó MP4"}

    # Log del gate (si el render lo escribió)
    gate_log = _load_gate_log(work_dir)

    report = {
        "tema": "el perdón",
        "idea": "El perdón te hace libre",
        "formato": "short 9:16",
        "mp4": mp4,
        "render_ok": render_ok,
        "probe": probe,
        "emit": em.to_report(),
        "roles": [b.narrative_role.value for b in em.briefs],
        "cta": em.plan.cta if em.plan else None,
        "scenes": [],
        "gate_log": gate_log,
        "warnings": [],
        "fallbacks": [],
        "assets": [a.status if hasattr(a, "status") else "?" for a in em.asset_selections],
    }

    # Per-escena: role, text, visual_event, strategy, final_prompt, asset, gate
    for i, b in enumerate(em.briefs):
        ai = b.ai_prompt or ""
        sel = em.asset_selections[i] if i < len(em.asset_selections) else None
        sc = {
            "scene": i + 1,
            "narrative_role": b.narrative_role.value,
            "text": b.narration,
            "visual_event": b.visual_event,
            "setting": b.setting,
            "lighting": b.lighting,
            "camera": b.camera,
            "symbol": b.symbol,
            "action": b.action,
            "duration_s": round(b.duration, 1),
            "motion": b.motion.value if hasattr(b.motion, "value") else str(b.motion),
            "final_prompt": ai,
        "asset_status": sel.status if sel else None,
        "asset_query": sel.query_used if sel else None,
        "asset_selected_id": (sel.selected.id if (sel and sel.selected) else None),
        }
        # gate del log coincidente por scene
        g = next((g for g in gate_log if g.get("scene") == i + 1), None)
        sc["gate"] = g
        report["scenes"].append(sc)
        if not ai:
            report["warnings"].append(f"escena {i+1}: ai_prompt vacío (fallback)")

    with open(os.path.join(OUT_ROOT, "informe_perdon.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── Consola —─
    print("\n===== INFORME DE PRODUCCIÓN =====", flush=True)
    print("MP4:", mp4, flush=True)
    print("render_ok:", render_ok, flush=True)
    print("probe:", json.dumps(probe, ensure_ascii=False), flush=True)
    print("emit:", json.dumps(report["emit"], ensure_ascii=False), flush=True)
    print("CTA (sistema):", report["cta"], flush=True)
    print("assets:", report["assets"], flush=True)
    for sc in report["scenes"]:
        g = sc["gate"] or {}
        print(f"\n--- scene {sc['scene']} | {sc['narrative_role']} ---", flush=True)
        print(f"  text: {sc['text']}", flush=True)
        print(f"  visual_event: {sc['visual_event']}", flush=True)
        print(f"  motion: {sc['motion']} | dur: {sc['duration_s']}s", flush=True)
        print(f"  gate: {g.get('decision')} score={g.get('score')} hard_fail={g.get('hard_fail')} attempts={g.get('attempts')}", flush=True)
        print(f"  asset: {sc['asset_status']} q='{sc['asset_query']}'", flush=True)
        print(f"  prompt: {sc['final_prompt'][:160]}...", flush=True)
    if report["warnings"]:
        print("\nWARNINGS:", report["warnings"], flush=True)
    print("\nInforme JSON: ", os.path.join(OUT_ROOT, "informe_perdon.json"), flush=True)
    return 0 if render_ok else 2


if __name__ == "__main__":
    sys.exit(main())
