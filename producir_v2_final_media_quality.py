# V2-FINAL — PRODUCCIONES REALES con MEDIA DIRECTOR (MediaQuality).
#
# Genera 2 renders de verdad, uno por formato, para validar end-to-end la
# capa de calidad de medios: filtro editorial (HARD FAIL) + Media Director
# (AI_IMAGE / PHOTO_STOCK / VIDEO_STOCK) + rutas de render photo/video/ai.
#
#   * Short  9:16  — "Decir NO también es quererte"   (tema: límites)
#   * Youtube 16:9 — "La paz no se encuentra, se permite" (tema: paz interior)
#
# Nosotros solo aportamos el guion (narrations por rol); el sistema decide toda
# la maquinaria visual (estructura, visual_event, medios, motion, CTA).
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_orchestrator import produce_editorial
from render_adapter import render_emission, build_work_context

OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", "v2_pruebas")


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


# ── Guiones (tuteo, fe compatible, público 35-64) ──
SHORT_NARR = {  # tema: límites
    "hook": "¿Decir que no te hace sentir culpable? Hay alguien en tu vida acostumbrado a que nunca le digas que no.",
    "problem": "Cada vez que cedes aunque no quieres, regalas un trocito de tu día y de tu paz. No es egoísmo pedir tu lugar.",
    "agitation": "Y lo más duro: cuanto más das sin límite, más se acostumbran a que siempre estés disponible.",
    "psychology": "Poner un límite no es un portazo: es una puerta que se cierra despacio, con amor, para cuidar lo que vale.",
    "solution": "Empieza pequeño: ante la próxima petición, respira y di 'déjame pensarlo'. No necesitas justificarte.",
    "hope": "Decir no a lo que te vacía es decir sí a lo que eres. Y proteger tu paz también es una forma de querer.",
    "callout": "Si hoy necesitabas permiso para poner un límite, este es. Compártelo con alguien que también lo necesita.",
}

LONG_NARR = {  # tema: paz interior
    "hook": "¿Y si la paz que tanto buscas no se encuentra en ningún lugar, sino que se permite?",
    "reality": "Pasamos años persiguiendo una calma que siempre parece estar en la próxima meta, el próximo logro, el próximo descanso.",
    "problem": "El problema: mientras la buscas afuera, tu mente sigue encendida y el cuerpo tenso, como si la paz fuera un premio lejano.",
    "psychology": "La paz no llega cuando todo se ordena. Llega cuando dejas de exigir que el mundo esté en calma para poder estar tú en calma.",
    "psychology2": "No se trata de no sentir: se trata de no dejar que el ruido decida por ti. Tu respiración ya tiene ritmo; tu corazón también.",
    "psychology3": "Y hay una verdad más honda: la paz no se fabrica con esfuerzo, se recibe. Es un don que ya tienes, solo hay que dejar de taparlo.",
    "solution": "Empieza con una pausa al día: tres respiraciones, la luz de una ventana, el silencio después de una taza. Nada más.",
    "biblical_grounding": "No tienes que comprar tu calma con logros. Ya eres suficiente: tu valor no se gana, se reconoce.",
    "hope": "Cuando permites la paz, empiezas a vivir desde ella y no hacia ella. Eso cambia todo.",
    "callout": "Si necesitabas permiso para pausar, aquí lo tienes. Compártelo con alguien que corre sin parar.",
}


def _load_gate_log(work_dir: str) -> list:
    p = os.path.join(work_dir, "tmp", "quality_gate.json")
    rows = []
    if os.path.exists(p):
        for line in open(p):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def producir(tag: str, topic: str, idea: str, format_name: str, narr: dict,
             aspect: str) -> int:
    root = os.path.join(OUT_ROOT, tag)
    os.makedirs(root, exist_ok=True)
    print(f"\n======== PRODUCCIÓN: {tag} | {format_name} {aspect} ========", flush=True)

    em = produce_editorial(topic=topic, central_idea=idea, format_name=format_name,
                           narrations=narr)
    mp4 = os.path.join(root, f"{tag}_{'9x16' if aspect=='vertical' else '16x9'}.mp4")
    work_dir = build_work_context(em)

    md = em.media_direction
    print("media_sequence:", list(md.media_sequence) if md else None, flush=True)
    print("repr_sequence :", list(md.representation_sequence) if md else None, flush=True)

    render_ok = False
    if os.path.exists(mp4) and os.path.getsize(mp4) > 0:
        print("  (mp4 ya existe; se regenera solo el informe)", flush=True)
        render_ok = True
    else:
        try:
            render_emission(em, mp4, work_dir=work_dir, aspect=aspect)
        except Exception as e:  # noqa: BLE001
            print(f"\n[ERROR RENDER] {e}", flush=True)
        else:
            render_ok = os.path.exists(mp4)

    probe = ffprobe(mp4) if render_ok else {"error": "no se generó MP4"}
    gate_log = _load_gate_log(work_dir)

    report = {
        "tag": tag, "tema": topic, "idea": idea, "formato": format_name,
        "mp4": mp4, "render_ok": render_ok, "probe": probe,
        "canvas": [em.canvas_width, em.canvas_height],
        "media_direction": md.to_report() if md else None,
        "roles": [b.narrative_role.value for b in em.briefs],
        "gate_log": gate_log,
        "scenes": [],
    }
    for i, b in enumerate(em.briefs):
        sc = {
            "scene": i + 1,
            "narrative_role": b.narrative_role.value,
            "text": b.narration,
            "duration_s": round(b.duration, 1),
            "motion": b.motion.value if hasattr(b.motion, "value") else str(b.motion),
            "preferred_source": getattr(b, "preferred_source", None).value
                if getattr(b, "preferred_source", None) else None,
            "ai": b.ai_prompt or "",
        }
        if md is not None and i < len(md.scenes):
            sm = md.scenes[i]
            sc["medium"] = sm.medium.value
            sc["repr"] = sm.representation.value
            sc["fit"] = round(sm.fit_score, 2)
            sc["reason"] = sm.reasoning
        g = next((x for x in gate_log if x.get("scene") == i + 1), None)
        sc["gate"] = g
        report["scenes"].append(sc)

    with open(os.path.join(root, f"informe_{tag}.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

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
    r1 = producir("limites", "decir que no también es quererte",
                  "Decir NO también es quererte", "short", SHORT_NARR, "vertical")
    r2 = producir("paz_interior", "la paz no se encuentra, se permite",
                  "La paz no se encuentra, se permite", "youtube", LONG_NARR, "horizontal")
    print("\nALL DONE", flush=True)
    return 0 if (r1 == 0 and r2 == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
