# V2 — PRUEBA REAL CON TOPIC LOCK: "EL PERDÓN TE HACE LIBRE" (9:16 + 16:9)
#
# Fase TOPIC/IDEA LOCK. Un driver de producción declarativo:
#   * La idea entregada por el usuario es la FUENTE DE VERDAD
#     (REQUESTED_TOPIC / REQUESTED_IDEA).
#   * Se la pasa a produce_editorial como requested_topic/requested_idea para
#     que el TOPIC LOCK valide que el plan construido responde a ESA idea y no a
#     otra (frena si el harness intentara sustituir el tema).
#   * Se produce el MISMO tema en los DOS formatos del canal (Short 9:16 y
#     YouTube 16:9), con guiones de perdón coherentes con fe + psicología.
#
# El sistema decide TODA la maquinaria visual (roles, visual_event, medios,
# motion, CTA, imágenes); el driver solo aporta el guion como el harness real.
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_orchestrator import produce_editorial
from render_adapter import render_emission, build_work_context

OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", "v2_pruebas", "perdon_dual")

# ── IDEA DEL USUARIO (fuente de verdad del TOPIC LOCK) ──
REQUESTED_TOPIC = "el perdón"
REQUESTED_IDEA = "El perdón te hace libre"

# ── Guiones del perdón (tuteo, fe+psicología integrada, 35-64) ──
SHORT_NARR = {
    "hook": "¿Cuántos años llevas cargando a alguien que ya no ocupa tu vida? Ese rencor pesa más que la persona que lo causó.",
    "problem": "No es debilidad tuya sentirte herido. El dolor es real, y negarlo no lo borra. El problema es que el dolor se vuelve una casa donde ya no vives tú, sino quien te lastimó.",
    "agitation": "Y lo más duro: quien te hirió quizás ni lo recuerda, mientras tú repites la escena a solas.",
    "psychology": "Perdonar no significa decir que estuvo bien, ni olvidar, ni volver a confiar, ni abrir la puerta para que vuelva a hacerte daño.",
    "solution": "Lo que esa persona hizo no cambia. Pero tú decides que aquello deje de ocupar tu presente. Suelta, no porque ellos lo merezcan: porque tú mereces tu paz.",
    "hope": "Devolver el perdón no es un favor a ellos: es devolverte a ti la paz que te quitaron. Y quien te conoce por tu nombre te invita a soltar la carga y vivir tu día.",
    "callout": "Si hay alguien a quien aún le guardas rencor, el permiso para soltarlo empieza hoy. Compártelo con quien lo necesite.",
}

LONG_NARR = {
    "hook": "¿Y si soltar el rencor no es un favor a quien te lastimó, sino la forma de devolverte a ti la paz que te quitaron?",
    "reality": "Cargamos años a personas que ya no están en nuestra vida. Y el peso no lo siente quien nos hirió: lo sentimos nosotros, cada vez que la escena vuelve en silencio.",
    "problem": "El problema no es haber sido herido: eso es real y no tienes que negarlo. El problema es que el rencor se vuelve una casa donde ya no vives tú, sino quien te lastimó.",
    "psychology": "Perdonar no es decir que estuvo bien. No es olvidar, ni volver a confiar, ni abrir la puerta para que vuelvan a hacerte daño.",
    "psychology2": "El perdón es una decisión sobre TU presente: que aquello que hizo desaparezca como dueño de tus días. No cambia el pasado; cambia quién manda en tu hoy.",
    "psychology3": "Hay una verdad más honda: soltar la ofensa no te hace más débil, te hace más libre. El odio consume energía que tu cuerpo y tu alma necesitan para vivir.",
    "solution": "Empieza con un paso pequeño: hoy, al recordar lo que pasó, no lo repitas hacia adelante. Dilo una vez y deja que se quede en el pasado. Mañana, otro paso.",
    "biblical_grounding": "No perdonas porque el otro lo merezca. Perdonas porque quien te conoce por tu nombre te invita a soltar la carga que no era tuya.",
    "hope": "Devolver el perdón es devolverte a ti la libertad. Y desde ese espacio, vuelves a vivir tu día con el peso que solo era de ellos, fuera de tus hombros.",
    "callout": "Si hay alguien a quien aún le guardas rencor, el permiso para soltarlo empieza hoy. Compártelo con quien lo necesite.",
}


def ffprobe(mp4: str) -> dict:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
             "-show_streams", mp4], capture_output=True, text=True, timeout=60,
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
    p = os.path.join(work_dir, "tmp", "quality_gate.json")
    rows = []
    if os.path.exists(p):
        for line in open(p):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def producir(tag: str, format_name: str, aspect: str, narr: dict,
             platform: str = "both") -> int:
    root = os.path.join(OUT_ROOT, tag)
    os.makedirs(root, exist_ok=True)
    print(f"\n======== PRODUCCIÓN: {tag} | {format_name} {aspect} | plataforma={platform} ========", flush=True)

    # La IDEA DEL USUARIO se pasa como fuente de verdad del lock. El motivo va
    # en topic/central_idea (para el pipeline) y en requested_* (para el lock).
    em = produce_editorial(
        topic=REQUESTED_TOPIC,
        central_idea=REQUESTED_IDEA,
        format_name=format_name,
        narrations=narr,
        requested_topic=REQUESTED_TOPIC,
        requested_idea=REQUESTED_IDEA,
        enforce_topic_lock=True,
    )

    mp4 = os.path.join(root, f"{tag}_{'9x16' if aspect=='vertical' else '16x9'}.mp4")
    work_dir = build_work_context(em)

    md = em.media_direction
    print("TOPIC LOCK: PASS (plan responde a 'el perdón')", flush=True)
    print("media_sequence:", list(md.media_sequence) if md else None, flush=True)

    render_ok = False
    if os.path.exists(mp4) and os.path.getsize(mp4) > 0:
        print("  (mp4 ya existe; se regenera solo el informe)", flush=True)
        render_ok = True
    else:
        try:
            render_emission(em, mp4, work_dir=work_dir, aspect=aspect)
        except Exception as e:  # noqa: BLE001 — documentar, NO entrar en loop
            print(f"\n[ERROR RENDER] {e}", flush=True)
        else:
            render_ok = os.path.exists(mp4)

    probe = ffprobe(mp4) if render_ok else {"error": "no se generó MP4"}
    gate_log = _load_gate_log(work_dir)

    report = {
        "tag": tag,
        "requested_topic": REQUESTED_TOPIC,
        "requested_idea": REQUESTED_IDEA,
        "topic_lock": "PASS",
        "formato": f"{format_name} {aspect}",
        "mp4": mp4,
        "render_ok": render_ok,
        "probe": probe,
        "canvas": [em.canvas_width, em.canvas_height],
        "media_direction": md.to_report() if md else None,
        "roles": [b.narrative_role.value for b in em.briefs],
        "cta": em.plan.cta if em.plan else None,
        "gate_log": gate_log,
        "scenes": [],
        "assets": [a.status if hasattr(a, "status") else "?" for a in em.asset_selections],
    }
    for i, b in enumerate(em.briefs):
        sc = {
            "scene": i + 1,
            "narrative_role": b.narrative_role.value,
            "text": b.narration,
            "duration_s": round(b.duration, 1),
            "motion": b.motion.value if hasattr(b.motion, "value") else str(b.motion),
            "ai": b.ai_prompt or "",
        }
        if md is not None and i < len(md.scenes):
            sm = md.scenes[i]
            sc["medium"] = sm.medium.value
            sc["fit"] = round(sm.fit_score, 2)
            sc["reason"] = sm.reasoning
        g = next((x for x in gate_log if x.get("scene") == i + 1), None)
        sc["gate"] = g
        report["scenes"].append(sc)

    with open(os.path.join(root, f"informe_{tag}.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── PAQUETE DE PUBLICACIÓN (solo si existe MP4 final) ──
    package_md = None
    if render_ok:
        from publication_package import write_beside_mp4
        ctx = {
            "title": report["requested_idea"],
            "topic": report["requested_topic"],
            "idea": report["requested_idea"],
            "requested_topic": report["requested_topic"],
            "requested_idea": report["requested_idea"],
            "enfoque": "anti-gurú con base real · fe + psicología integrada",
            "formato": report["formato"],
            "format_name": format_name,
            "aspect": "vertical 9:16" if aspect == "vertical" else "horizontal 16:9",
            "duracion_s": (report.get("probe") or {}).get("duration") or sum(b.duration for b in em.briefs),
            "n_scenes": len(em.briefs),
            "mp4": mp4,
            "fecha": "2026-08-28",
            "cta": report.get("cta") or (em.plan.cta if em.plan else None),
            "warnings": [],
            "providers": [a.status if hasattr(a, "status") else "ok" for a in em.asset_selections],
            "fallbacks": [f"gate FALLBACK en escena {n+1}" for n, s in enumerate(report["scenes"])
                          if (s.get("gate") or {}).get("decision") == "FALLBACK"],
        }
        package_md = write_beside_mp4(context=ctx, platform=platform)
        print("\n[PAQUETE PUBLICACIÓN]", flush=True)
        print("MD:", package_md, flush=True)

    print("\n===== INFORME =====", flush=True)
    print("MP4:", mp4, "| render_ok:", render_ok, flush=True)
    print("probe:", json.dumps(probe, ensure_ascii=False), flush=True)
    for sc in report["scenes"]:
        g = sc.get("gate") or {}
        print(f"  s{sc['scene']:>2} {sc['narrative_role']:<18} med={sc.get('medium','?'):<12} "
              f"motion={sc['motion']:<9} dur={sc['duration_s']:>4}s "
              f"gate={g.get('decision')} score={g.get('score')} editorial_unsafe={g.get('editorial_unsafe')}",
              flush=True)
    print("Informe:", os.path.join(root, f"informe_{tag}.json"), flush=True)
    return 0 if render_ok else 2


def main() -> int:
    os.makedirs(OUT_ROOT, exist_ok=True)
    platform = os.environ.get("V2_PLATAFORMA", "both")
    print("=== PRUEBA REAL TOPIC LOCK + PAQUETE PUBLICACIÓN: "
          f"'El perdón te hace libre' (9:16 + 16:9) | plataforma={platform} ===", flush=True)
    r1 = producir("perdon_short", "short", "vertical", SHORT_NARR, platform=platform)
    r2 = producir("perdon_long", "youtube", "horizontal", LONG_NARR, platform=platform)
    print("\nALL DONE", flush=True)
    return 0 if (r1 == 0 and r2 == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
