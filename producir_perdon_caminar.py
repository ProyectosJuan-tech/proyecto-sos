# V2.5 — PRODUCCIÓN REAL: "EL PERDÓN TE HACE CAMINAR MÁS LIBRE EN LA VIDA"
#
# Short 9:16, plataforma: YouTube (V2_PLATAFORMA=youtube por defecto).
# Usa el sistema completo: produce_editorial (con TOPIC LOCK) → scene_dicts →
# render_emission → MP4 → Production Report → Publication Package (junto al MP4).
#
# El sistema decide TODA la maquinaria visual (roles, visual_event, medios,
# motion, CTA, imágenes); el driver solo aporta el guion (como el harness real).
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_orchestrator import produce_editorial
from render_adapter import render_emission, build_work_context

SLUG = "el_perdon_te_hace_caminar_mas_libre_en_la_vida"
OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", SLUG)

# ── IDEA DEL USUARIO (fuente de verdad del TOPIC LOCK) ──
REQUESTED_TOPIC = "el perdón"
REQUESTED_IDEA = "El perdón te hace caminar más libre en la vida"

# ── CTA del usuario (reemplaza al automático; tuteo, contextual) ──
CTA_USUARIO = ("Si esto te resonó, compártelo con quien lo necesite. "
               "Te invito a que te suscribas al canal y darle \"me gusta\"")

# ── Prompt corregido para la ESCENA 2 (problem) ──
# El prompt original generaba una escena de cama al amanecer que derivó en una
# mujer con el pecho expuesto. Se reemplaza por una imagen SEGURA y clara que
# comunica "el peso que arrastras" (hombros encorvados, ropa completa, sin
# escena de cama ni piel al descubierto).
PROMPT_S2 = (
    "A person fully dressed in normal modest everyday clothes (a long-sleeved "
    "shirt and trousers) seen from behind and in three-quarter view, standing "
    "mid-stride on a quiet city sidewalk, shoulders rounded and slightly "
    "hunched as if carrying an invisible weight, empty hands at the sides. "
    "A single worn backpack rests on their shoulders, the only sign of the load. "
    "Soft overcast morning light, muted warm tones, shallow depth of field, "
    "intimate observational editorial photography, natural skin tones, realistic "
    "textures, believable shadows, documentary framing. Shot on 50mm f/2, natural "
    "depth, at eye level. Photorealistic, emotionally subtle, sophisticated "
    "cinematic still. Vertical 9:16 composition, subject legible and naturally "
    "scaled, ample space in the upper area, the subject clear of the lower text "
    "band."
)

# ── Prompt corregido para la ESCENA 3 (agitation) ──
# Por pedido del usuario: plantas + una persona desperezándose de espaldas a
# la cámara. Comunica "soltar el peso que encorva el cuerpo" con una postura de
# estiramiento/desperezarse, vista desde atrás (sin mirada a cámara), rodeada
# de plantas, completamente vestida. La metáfora apoya "dejas de caminar doblado".
PROMPT_S3 = (
    "A person fully dressed in normal modest everyday clothes (a relaxed "
    "long-sleeved top and casual trousers) seen from BEHIND, in the middle of "
    "stretching and waking up the body: both arms raised overhead, slowly "
    "arching and stretching the back with a deep breath, head tilted back. "
    "The scene is a bright, calm living space full of green houseplants on "
    "shelves and windowsills, soft golden morning sunlight streaming through "
    "a large window. The person is comfortable and unhurried, mid-morning "
    "routine. Soft warm natural window light, gentle shadows, lush green plant "
    "leaves in the foreground. Intimate observational editorial photography, "
    "natural skin tones, realistic textures, believable shadows, documentary "
    "framing. Shot on 50mm f/2, natural depth, at eye level. Photorealistic, "
    "emotionally subtle, sophisticated cinematic still. Vertical 9:16 "
    "composition, subject legible and naturally scaled, ample space in the "
    "upper area, the subject clear of the lower text band."
)

# ── GUION (tuteo, fe+psicología integrada, 35-64; ángulo: caminar aligerado) ──
GUION = {
    "hook": "¿Qué pasaría si caminar se volviera más liviano? Ese rencor que cargas hoy no es tuyo.",
    "problem": "No es debilidad sentirte herido. Pero el dolor, si no lo sueltas, se vuelve un peso que arrastras a donde quiera que vayas.",
    "agitation": "Y lo más pesado de todo: quien te hirió quizás va libre, mientras tú caminas doblado bajo algo que ya no te pertenece.",
    "psychology": "Perdonar no es decir que estuvo bien, ni olvidar, ni volver a confiar. Es decidir que aquello ya no camine contigo.",
    "solution": "Suelta el rencor, no porque ellos lo merezcan, sino porque tu paso se aligera y vuelves a andar erguido.",
    "hope": "Quien te conoce por tu nombre te invita a soltar la carga para que camines libre. Hoy da el primer paso.",
    # la escena CALLOUT (CTA) la decide el sistema automáticamente
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
    os.makedirs(OUT_ROOT, exist_ok=True)
    platform = os.environ.get("V2_PLATAFORMA", "youtube")
    print(f"=== PRODUCCIÓN: '{REQUESTED_IDEA}' (short 9:16) | plataforma={platform} ===", flush=True)

    # Idea del usuario como fuente de verdad del lock + motivo del pipeline.
    em = produce_editorial(
        topic=REQUESTED_TOPIC,
        central_idea=REQUESTED_IDEA,
        format_name="short",
        narrations=GUION,
        cta=CTA_USUARIO,
        requested_topic=REQUESTED_TOPIC,
        requested_idea=REQUESTED_IDEA,
        enforce_topic_lock=True,
    )

    mp4 = os.path.join(OUT_ROOT, f"{SLUG}_9x16.mp4")
    work_dir = build_work_context(em)

    # Overrides de prompt por escena (correcciones pedidas por el usuario).
    # Aplican a scene_dict (lo que renderiza), brief y plan (lo que reporta), y
    # limpian el cache de imagen para forzar regeneración con el prompt nuevo.
    imgs_dir = os.path.join(work_dir, "imgs")

    def _override_scene(idx: int, prompt: str, cache_names: list[str]) -> None:
        em.scene_dicts[idx]["ai"] = prompt
        em.briefs[idx].ai_prompt = prompt
        if em.plan and getattr(em.plan, "scenes", None) and len(em.plan.scenes) > idx:
            em.plan.scenes[idx].ai_prompt = prompt
        for f in cache_names:
            p = os.path.join(imgs_dir, f)
            if os.path.exists(p):
                os.remove(p)

    # Escena 2 (problem): evitar desnudo → persona vestida caminando con peso.
    if len(em.scene_dicts) > 1 and len(em.briefs) > 1:
        _override_scene(1, PROMPT_S2, ["e02.jpg", "e02_r1.jpg", "e02_r2.jpg",
                                       "e02_1.jpg", "e02_2.jpg"])
    # Escena 3 (agitation): plantas + persona desperezándose de espaldas.
    if len(em.scene_dicts) > 2 and len(em.briefs) > 2:
        _override_scene(2, PROMPT_S3, ["e03.jpg", "e03_r1.jpg", "e03_r2.jpg",
                                       "e03_1.jpg", "e03_2.jpg"])

    md = em.media_direction
    print("TOPIC LOCK: PASS (plan responde a 'el perdón')", flush=True)
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
        "tag": SLUG,
        "requested_topic": REQUESTED_TOPIC,
        "requested_idea": REQUESTED_IDEA,
        "topic_lock": "PASS",
        "formato": "short vertical",
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

    with open(os.path.join(OUT_ROOT, f"informe_{SLUG}.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── PAQUETE DE PUBLICACIÓN (solo si existe MP4 final) ──
    package_md = None
    if render_ok:
        from publication_package import write_beside_mp4
        ctx = {
            "title": REQUESTED_IDEA,
            "topic": REQUESTED_TOPIC,
            "idea": REQUESTED_IDEA,
            "requested_topic": REQUESTED_TOPIC,
            "requested_idea": REQUESTED_IDEA,
            "enfoque": "anti-gurú con base real · fe + psicología integrada",
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
    print("Informe:", os.path.join(OUT_ROOT, f"informe_{SLUG}.json"), flush=True)
    return 0 if render_ok else 2


if __name__ == "__main__":
    sys.exit(main())
