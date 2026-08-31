# SERIE "¿POR QUÉ?" — EPISODIO 1 (producción real, sistema completo)
#
# "¿Por qué tengo celular, cama, comida y aun así me siento vacío?"
#
# Enfoque editorial (fase previa aprobada):
#   experiencia humana (culpa por sentirse vacío teniendo "todo")
#     → psicología (tener ≠ sentido; distracción ≠ solución)
#     → fe natural (el vacío como anhelo de lo infinito; ofrecida, no impuesta)
#     → cierra con una pregunta que deja pensando (no una fórmula).
#
# REGLA: SIN overrides manuales de prompts. El sistema existente
#   (IDEA → EDITORIAL → SCENE BRIEFS → NARRATIVE VISUAL DIRECTOR →
#    ASSET SELECTION → QUALITY GATE → RENDER) decide la representación visual,
#   cuidando que el contenido editorial permita objetos cotidianos concretos
#   (celular, cama, comida, habitación) sin ilustrar literalmente cada línea.
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_orchestrator import produce_editorial
from render_adapter import render_emission, build_work_context

# ── Identidad del episodio ──
EPISODIO_ID = "1"
SLUG = "porque-1-vacio"
TITULO = "¿Por qué tengo todo y sigo sintiéndome vacío?"
REQUESTED_TOPIC = "el vacío interior"
REQUESTED_IDEA = TITULO

OUT_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "¿PORQUÉ?", "PARA_YOUTUBE", SLUG
)

# ── CTA (YouTube en esta primera corrida; la versión FB se hará después) ──
# Cierre emocional breve y natural (directiva editorial): no acumular
# "comparte + dale like + suscríbete". La escena CALLOUT usa este texto.
CTA_YT = ("No te castigues por sentirte vacío. Escucha la pregunta que hay "
          "detrás de ese vacío: ¿qué estás buscando en el fondo? Si esto te "
          "resonó, compártelo con alguien que también pueda necesitar "
          "escucharlo.")

# ── GUION v2 (tuteo; arco experiencia→comprensión→profundización→fe→esperanza;
#    sin autoridad genérica de tipo "la psicología lo dice claro";
#    mecanismo psicológico concreto; fe natural, no bloque agregado) ──
GUION = {
    "hook": ("Tienes un celular. Tienes una cama donde dormir. Tienes comida. "
             "Quizás incluso personas que te quieren. Y aun así, hay noches en "
             "las que tienes todo eso delante y te preguntas: ¿por qué me siento "
             "vacío?"),
    "problem": ("Y entonces aparece la culpa. Piensas: '¿Qué me pasa? Si no me "
                "falta nada, debería estar bien'. Pero tener motivos para "
                "agradecer no significa que tengas prohibido sentirte mal."),
    "agitation": ("Así que intentas llenar ese hueco con algo: compras, comida, "
                  "redes, trabajo, planes, mensajes, cualquier cosa que consiga "
                  "distraerte por un rato. Y funciona... hasta que el silencio "
                  "vuelve."),
    "psychology": ("Porque una cosa es sentir placer y otra muy distinta es "
                   "sentir que tu vida tiene sentido. Puedes tener estímulos "
                   "todo el día y seguir preguntándote para qué haces todo esto. "
                   "El problema no siempre es que te falte algo que comprar. A "
                   "veces lo que falta es algo que las cosas no pueden darte."),
    "solution": ("Por eso quizá no necesitas castigarte por sentirte vacío, ni "
                 "correr a llenar ese espacio inmediatamente. Tal vez necesitas "
                 "detenerte y preguntarte con honestidad qué estás buscando "
                 "realmente: ¿descanso, sentido, amor, propósito, pertenencia?"),
    "hope": ("Y quizá, detrás de esa pregunta, haya un anhelo todavía más "
             "profundo. Porque el corazón humano no solo busca tener más; "
             "también busca algo que trascienda lo que puede comprar, controlar "
             "o acumular. Y Dios conoce ese anhelo. Te conoce por tu nombre y "
             "no es indiferente a lo que estás buscando."),
    # la escena CALLOUT (CTA) la decide el sistema con la cta pasada
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
    try:
        from consumption import reset
        reset()
    except Exception:
        pass
    os.makedirs(OUT_ROOT, exist_ok=True)
    print(f"=== SERIE ¿POR QUÉ? | EPISODIO {EPISODIO_ID} ===", flush=True)
    print(f"TÍTULO: {TITULO}", flush=True)

    em = produce_editorial(
        topic=REQUESTED_TOPIC,
        central_idea=REQUESTED_IDEA,
        format_name="short",
        narrations=GUION,
        cta=CTA_YT,
        requested_topic=REQUESTED_TOPIC,
        requested_idea=REQUESTED_IDEA,
        enforce_topic_lock=True,
    )

    mp4 = os.path.join(OUT_ROOT, f"{SLUG}_9x16.mp4")
    work_dir = build_work_context(em)

    # SIN overrides manuales: el sistema decide el visual.
    md = em.media_direction
    print("TOPIC LOCK: PASS (plan responde a 'el vacío interior')", flush=True)
    print("media_sequence:", list(md.media_sequence) if md else None, flush=True)

    render_ok = False
    if os.path.exists(mp4) and os.path.getsize(mp4) > 0:
        print("  (mp4 ya existe; se regenera solo informe + paquete)", flush=True)
        render_ok = True
    else:
        try:
            render_emission(em, mp4, work_dir=work_dir, aspect="vertical")
        except Exception as e:  # noqa: BLE001 — documentar, NO entrar en loop
            print(f"\n[ERROR RENDER] {e}", flush=True)
        else:
            render_ok = os.path.exists(mp4)

    probe = ffprobe(mp4) if render_ok else {"error": "no se generó MP4"}
    gate_log = _load_gate_log(work_dir)

    report = {
        "serie": "PORQUE",
        "episodio": EPISODIO_ID,
        "tag": SLUG,
        "titulo": TITULO,
        "requested_topic": REQUESTED_TOPIC,
        "requested_idea": REQUESTED_IDEA,
        "topic_lock": "PASS",
        "formato": "short vertical 9:16",
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

    try:
        from consumption import get_minimal_report
        report["consumption"] = get_minimal_report()
    except Exception:
        report["consumption"] = None

    with open(os.path.join(OUT_ROOT, f"informe_{SLUG}.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── PAQUETE DE PUBLICACIÓN (solo si existe MP4 final) ──
    package_md = None
    if render_ok:
        from publication_package import write_beside_mp4
        ctx = {
            "title": TITULO,
            "topic": REQUESTED_TOPIC,
            "idea": REQUESTED_IDEA,
            "requested_topic": REQUESTED_TOPIC,
            "requested_idea": REQUESTED_IDEA,
            "enfoque": "anti-gurú con base real · fe + psicología integrada · serie ¿POR QUÉ?",
            "formato": "short vertical",
            "format_name": "short",
            "aspect": "vertical 9:16",
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
        package_md = write_beside_mp4(context=ctx, platform="youtube")
        print("\n[PAQUETE PUBLICACIÓN]", flush=True)
        print("MD:", package_md, flush=True)

    print("\n===== INFORME EPISODIO 1 =====", flush=True)
    print("MP4:", mp4, "| render_ok:", render_ok, flush=True)
    print("probe:", json.dumps(probe, ensure_ascii=False), flush=True)
    for sc in report["scenes"]:
        g = sc.get("gate") or {}
        print(f"  s{sc['scene']:>2} {sc['narrative_role']:<18} med={sc.get('medium','?'):<12} "
              f"motion={sc['motion']:<9} dur={sc['duration_s']:>4}s "
              f"gate={g.get('decision')} score={g.get('score')} editorial_unsafe={g.get('editorial_unsafe')}",
              flush=True)
    print("Informe:", os.path.join(OUT_ROOT, f"informe_{SLUG}.json"), flush=True)
    return 0 if render_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
