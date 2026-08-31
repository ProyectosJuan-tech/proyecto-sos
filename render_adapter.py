"""
V2-06 — RENDER_ADAPTER: convierte la salida editorial V2 en MP4 reales
usando el renderer legacy existente. NO sustituye el pipeline.

    V2 (EditorialEmission: scene_dicts + briefs + layouts + assets)
        ↓
    render_adapter
        ↓
    legacy renderer (hacer_video_caverna m.* / hacer_video_youtube y.*)
        ↓
    MP4

Aditivo: no toca nada del pipeline. Reutiliza m.render_scene / y.render_scene,
la bajada de imagen (flux_img :: download_image), build_bg(_bright), tts_audio,
align_words y concat existentes.

No hardcodea temas: produce cualquier EditorialEmission.
"""

from __future__ import annotations

import json
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hacer_video_caverna as m
import hacer_video_youtube as y

try:
    from PIL import Image, ImageFilter
except Exception:  # pragma: no cover
    Image = None
    ImageFilter = None

# Voz única del canal
VOICE_KEY = "jorge"
VOICE = "es-MX-JorgeNeural"
DEEPEN = 0.92
DEFAULT_RATE = "-8%"

# Preferencia arte: cálido para bienestar
LIGHT_STYLE = "bright airy natural, cinematic still, soft window light"


# ─────────────────────────────────────────
# Bajada de imagen (IA → Commons fallback)
# ─────────────────────────────────────────
def _smart_fit_to_aspect(img_path, target_ar="16:9"):
    """V2.1: alinea el asset al aspect target recortando con smart_crop_geometry
    (respeta el punto focal si lo hay; si no, centro) ANTES de build_bg.

    Hace que el crop del renderer legacy apenas tenga que recortar y que, cuando
    lo haga, no se pierda el sujeto. Pura geometría, sin red ni visión.
    """
    if Image is None or not os.path.exists(img_path):
        return
    from visual_quality_engine import smart_crop_geometry, apply_crop
    try:
        im = Image.open(img_path)
        w, h = im.size
        src_ar = w / h
        want = 16 / 9 if target_ar == "16:9" else 9 / 16
        if abs(src_ar - want) < 0.03:
            return  # ya está en el aspect correcto
        box = smart_crop_geometry(w, h, target_ar=target_ar)
        if tuple(int(v) for v in box) == (0, 0, w, h):
            return
        im = apply_crop(im, box).convert("RGB")
        im.save(img_path, quality=95)
    except Exception:  # noqa: BLE001 — nunca romper el render por un crop fallido
        return


def _prompt_has_human(text: str) -> bool:
    low = (text or "").lower()
    return any(w in low for w in (
        "woman", "mujer", "man", "hombre", "person", "persona", "her", "his",
        "hands", "manos", "portrait", "retrato", "face", "rostro",
    ))


def _safe_ai_prompt(scene) -> str:
    """Prompt de imagen con PREVENCIÓN editorial (build_safe_prompt): si la
    escena tiene personas, fuerza ropa modesta y escena sin riesgo, y añade el
    sufijo de "no nudity". Evita que un prompt de riesgo llegue al generador."""
    from editorial_filter import build_safe_prompt
    base = scene.get("ai") or scene.get("visual_event") or scene.get("q") or ""
    return build_safe_prompt(base, has_human=_prompt_has_human(base))


def _download_image(scene, idx, img_dir, aspect="vertical"):
    """Descarga la imagen de una escena V2. Devuelve la ruta o None.

    V2.1: genera la imagen en el MISMO aspect que la plataforma (vertical 9:16 /
    horizontal 16:9). Antes se llamaba a flux_img.generate sin aspect, con lo que
    un video 16:9 generaba una 9:16 y luego el build_bg la recortaba al centro:
    esa es la causa raíz del "asset gigante / composición rota" en 16:9.
    V2-FINAL: el prompt pasa por build_safe_prompt (prevención editorial).
    """
    prompt = _safe_ai_prompt(scene)
    img = os.path.join(img_dir, f"e{idx:02d}.jpg")
    img_aspect = "16:9" if aspect == "horizontal" else "9:16"
    if os.path.exists(img) and os.path.getsize(img) > 5000:
        # Re-render con escena SIN CAMBIOS → reutilizar el asset ya generado.
        # Si el prompt/seed/aspect de la escena CAMBIÓ, el fingerprint del
        # manifest no coincide y se regenera (solo esta escena).
        try:
            import flux_img
            prev = flux_img.image_cache_lookup(img)
            cur = flux_img._fingerprint(prompt, idx * 101, img_aspect)
            if prev == cur:
                return img
            # fingerprint distinto → escena cambiada: regenerar sin caché.
            try:
                flux_img.generate(prompt, img, aspect=img_aspect, seed=idx * 101,
                                  use_cache=False, force=True)
                m.strip_img_metadata(img)
                return img if os.path.getsize(img) > 5000 else None
            except Exception:
                pass
        except Exception:
            return img
    tried = 0
    if prompt:
        try:
            import flux_img
            flux_img.generate(prompt, img, aspect=img_aspect, seed=idx * 101)
            m.strip_img_metadata(img)
            return img if os.path.getsize(img) > 5000 else None
        except Exception as e:
            tried += 1
    if scene.get("q"):
        try:
            m.download_image({"q": scene["q"]}, img)
            return img if os.path.getsize(img) > 5000 else None
        except Exception as e:
            tried += 1
    if tried:
        print(f"    AVISO: no se pudo conseguir imagen para escena {idx}", flush=True)
    return None


# ─────────────────────────────────────────
# QUALITY GATE REAL (V2.3) — evalua la imagen real, regenera/fallback
# ─────────────────────────────────────────
def _quality_gate_enabled() -> bool:
    """El gate se puede desactivar con env V2_QUALITY_GATE=0 (para depurar/
    reproducibilidad). Por defecto ON en render V2."""
    val = os.environ.get("V2_QUALITY_GATE", "1")
    return val not in ("0", "false", "False", "")


def _gate_context(scene, idx, aspect, work_dir, previous_events):
    """Construye el GateContext para una escena (evento + contexto de variedad)."""
    from quality_gate import GateContext, aspect_of
    visual_event = scene.get("visual_event") or scene.get("ai") or scene.get("q") or ""
    prompt = scene.get("ai") or visual_event or ""
    events = []
    events_file = os.path.join(work_dir, "tmp", "gate_events.json")
    if os.path.exists(events_file):
        try:
            import json
            events = json.load(open(events_file))
        except Exception:  # noqa: BLE001
            events = []
    return GateContext(
        aspect=aspect_of(aspect),
        visual_event=visual_event,
        scene_text=scene.get("text", ""),
        prompt=prompt,
        previous_events=list(events),
        previous_motifs=list(events),
    ), events_file


def _record_gate_event(visual_event, events_file):
    import json
    evs = []
    if os.path.exists(events_file):
        try:
            evs = json.load(open(events_file))
        except Exception:  # noqa: BLE001
            evs = []
    if visual_event and visual_event not in evs:
        evs.append(visual_event)
        evs = evs[-12:]
    os.makedirs(os.path.dirname(events_file), exist_ok=True)
    try:
        json.dump(evs, open(events_file, "w"))
    except Exception:  # noqa: BLE001
        pass


def _download_with_quality_gate(scene, idx, img_dir, aspect, work_dir):
    """Genera la imagen y la corre por el Quality Gate Real.

    generate → evaluate (imagen real) → PASS/REGENERATE/FALLBACK.
    REGENERATE → regenera con prompt mejorado (hasta max_attempts, sin loop).
    FALLBACK → conserva el mejor candidato (o cae a Commons si no hay ninguno).
    Devuelve (path_imagen, gate_result|None). Puente para _render_scene.
    """
    if not _quality_gate_enabled():
        # ruta previa: un solo intento, sin gate (backward compatible)
        path = _download_image(scene, idx, img_dir, aspect)
        return path, None

    from quality_gate import (
        QualityGate, GateContext, Decision, DEFAULT_MAX_ATTEMPTS,
    )

    prompt = _safe_ai_prompt(scene)

    first = _download_image(scene, idx, img_dir, aspect)
    if not first:
        return None, None

    ctx, events_file = _gate_context(scene, idx, aspect, work_dir, [])

    def regenerate_fn(attempt, improved_prompt):
        # genera una imagen NUEVA en un archivo de intento distinto, con seed
        # variado y el prompt mejorado (determinista salvo la red de imagen).
        alt = os.path.join(img_dir, f"e{idx:02d}_r{attempt}.jpg")
        if os.path.exists(alt) and os.path.getsize(alt) > 5000:
            return alt
        prompt_attempt = improved_prompt or _safe_ai_prompt(scene)
        img_aspect = "16:9" if aspect == "horizontal" else "9:16"
        try:
            import flux_img
            flux_img.generate(prompt_attempt, alt, aspect=img_aspect,
                              seed=(idx * 101) + attempt * 7331)
            m.strip_img_metadata(alt)
            return alt if os.path.getsize(alt) > 5000 else None
        except Exception:  # noqa: BLE001
            try:
                # fallback: Commons con la query original
                m.download_image({"q": scene.get("q", "morning light")}, alt)
                return alt if os.path.getsize(alt) > 5000 else None
            except Exception:  # noqa: BLE001
                return None

    store = []

    def store_attempt(res, path):
        store.append({"attempt": res.attempt, "score": res.score,
                      "hard_fail": res.hard_fail,
                      "decision": res.decision.value,
                      "reasons": list(res.reasons),
                      "path": path})

    gate = QualityGate(
        min_score=float(os.environ.get("V2_GATE_MIN_SCORE", "6.5")),
        max_attempts=int(os.environ.get("V2_GATE_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS))),
    )
    # El gate regenera en un archivo de intento; si el intento no mejora se
    # mantiene el mejor candidato. El prompt del intento se escribe en scene_alt.
    result = gate.run(
        first, ctx,
        regenerate_fn=regenerate_fn,
        base_prompt=prompt,
        store_attempt=store_attempt,
    )

    final_path = result.final_candidate or first
    # si el gate no regeneró nada nuevo (sin critic_fn operable) no perdemos nada
    if final_path and os.path.exists(final_path):
        pass
    else:
        final_path = first

    # V2-FINAL — SEGURIDAD: si el gate dice que NINGÚN candidato fue
    # editorialmente seguro (no_safe_candidate), NUNCA renderizamos el asset
    # inseguro. Caemos a un asset determinista seguro (Wikimedia Commons con una
    # keyword inocua) y lo marcamos en el log.
    if getattr(result, "no_safe_candidate", False):
        safe_alt = os.path.join(img_dir, f"e{idx:02d}_safe_fallback.jpg")
        try:
            if not (os.path.exists(safe_alt) and os.path.getsize(safe_alt) > 5000):
                m.download_image({"q": "calm living room morning light"}, safe_alt)
        except Exception:  # noqa: BLE001
            pass
        if os.path.exists(safe_alt) and os.path.getsize(safe_alt) > 5000:
            final_path = safe_alt
        try:
            with open(os.path.join(work_dir, "tmp", "quality_gate.json"), "a") as f:
                json.dump({"scene": idx, "aspect": aspect,
                           "no_safe_candidate": True,
                           "final": final_path,
                           "note": "todos los candidatos editorial inseguros; "
                                   "se usó asset seguro determinista."},
                          f, ensure_ascii=False)
                f.write("\n")
        except Exception:  # noqa: BLE001
            pass

    _record_gate_event(ctx.visual_event, events_file)

    # perseguir el log del gate por escena
    try:
        import json
        os.makedirs(os.path.join(work_dir, "tmp"), exist_ok=True)
        with open(os.path.join(work_dir, "tmp", "quality_gate.json"), "a") as f:
            json.dump({"scene": idx, "aspect": aspect, "final": final_path,
                       "decision": result.decision.value,
                       "score": result.score, "hard_fail": result.hard_fail,
                       "attempts": store}, f, ensure_ascii=False)
            f.write("\n")
    except Exception:  # noqa: BLE001
        pass

    return final_path, result.decision


# ─────────────────────────────────────────
# TTS + timings (reutiliza m/asyncio)
# ─────────────────────────────────────────
def _tts_and_timings(text, work_dir, idx, voice, deepen, rate):
    slug = f"e{idx:02d}"
    etag = m.tts_engine_tag(voice)
    wav = os.path.join(work_dir, "audio", f"{slug}{etag}_{zlib.crc32(text.encode())}.wav")
    os.makedirs(os.path.dirname(wav), exist_ok=True)

    if not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(text, voice, wav, deepen=deepen, rate=rate))

    tj = os.path.join(work_dir, "tmp",
                      f"{slug}{etag}_{zlib.crc32(text.encode())}_timings.json")
    if os.path.exists(tj):
        return wav, [tuple(x) for x in json.load(open(tj))]

    timings = m.align_words(text, wav)
    if timings is None:
        toks = text.split()
        dur = m.probe_duration(wav)
        step = (dur / len(toks)) if toks else 0.1
        timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
    json.dump(timings, open(tj, "w"))
    return wav, timings


# ─────────────────────────────────────────
# Render escena (vertical u horizontal)
# ─────────────────────────────────────────
# ─────────────────────────────────────────
# MEDIA DIRECTOR routing (V2-FINAL): AI_IMAGE / PHOTO_STOCK / VIDEO_STOCK
# ─────────────────────────────────────────
def _scene_medium(scene) -> str:
    """Devuelve el medio del scene_dict: 'video' | 'photo' | 'ai'."""
    if scene.get("stock") or scene.get("stock_video") or scene.get("ai_video"):
        return "video"
    if scene.get("photo_stock"):
        return "photo"
    return "ai"


def _query_or_default(scene) -> str:
    q = scene.get("q") or ""
    return q if q else (scene.get("ai") or scene.get("visual_event") or "cozy home sunlight")


def _fetch_video_stock(scene, idx, img_dir, aspect):
    """Descarga un b-roll de video de Pexels para la escena (stock vertical/horizontal).
    Devuelve la ruta al .mp4 o None."""
    import pexels_stock as ps
    if not ps.available():
        return None
    q = _query_or_default(scene)
    video = os.path.join(img_dir, f"e{idx:02d}.mp4")
    if os.path.exists(video) and os.path.getsize(video) > 5000:
        return video
    # V2.7: si el Candidate Selection ya eligió una URL para esta escena
    # (scoreada por contenido), usarla directamente en vez de re-buscar.
    # Opt-in: solo si el scene_dict trae la clave; si falla, cae al flujo actual.
    sel_url = scene.get("v2_7_selected_url") or ""
    if sel_url:
        try:
            ps.download(sel_url, video)
            if os.path.getsize(video) > 5000:
                return str(video)
        except Exception:  # noqa: BLE001
            pass
    try:
        if aspect == "horizontal":
            got = ps.fetch_for_scene_landscape(q, video)
        else:
            got = ps.fetch_for_scene(q, video)
        return str(got) if got and os.path.getsize(str(video)) > 5000 else None
    except Exception:  # noqa: BLE001
        return None


def _fetch_photo_stock(scene, idx, img_dir, aspect):
    """Descarga una foto de Pexels (PHOTO_STOCK) para la escena.
    Devuelve la ruta a la .jpg o None."""
    import pexels_stock as ps
    if not ps.available():
        return None
    q = _query_or_default(scene)
    img = os.path.join(img_dir, f"e{idx:02d}.jpg")
    if os.path.exists(img) and os.path.getsize(img) > 5000:
        return img
    orientation = "landscape" if aspect == "horizontal" else "portrait"
    sel_url = scene.get("v2_7_selected_url") or ""
    if sel_url:
        try:
            ps.download(sel_url, img)
            if os.path.getsize(img) > 5000:
                return str(img)
        except Exception:  # noqa: BLE001
            pass
    try:
        got = ps.fetch_photo_for_scene(q, img, orientation=orientation)
        return str(got) if got and os.path.getsize(str(img)) > 5000 else None
    except Exception:  # noqa: BLE001
        return None


def _render_scene(scene, idx, n_scenes, work_dir, aspect):
    os.makedirs(os.path.join(work_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(work_dir, "tmp"), exist_ok=True)
    os.makedirs(os.path.join(work_dir, "imgs"), exist_ok=True)
    os.makedirs(os.path.join(work_dir, "out"), exist_ok=True)

    text = scene.get("text", "")
    wav, timings = _tts_and_timings(
        text, work_dir, idx, VOICE, DEEPEN, scene.get("rate", DEFAULT_RATE)
    )
    img_dir = os.path.join(work_dir, "imgs")
    mp4 = os.path.join(work_dir, "out", f"e{idx:02d}.mp4")
    trans = scene.get("trans")
    static_lines = scene.get("static_text") or None
    static_size = scene.get("static_size")

    medium = _scene_medium(scene)

    # ── VIDEO STOCK (fondo animado real): usa render_scene_video ──
    if medium == "video":
        video_path = _fetch_video_stock(scene, idx, img_dir, aspect)
        if not video_path:
            # si Pexels falla, caer al flujo de imagen (AI)
            medium = "ai"
        else:
            motion = scene.get("motion") or "static"
            if aspect == "horizontal":
                y.render_scene_video(timings, video_path, wav, mp4,
                                     final=(idx == n_scenes),
                                     static_lines=static_lines,
                                     static_size=static_size, trans=trans)
            else:
                m.render_scene_video(timings, video_path, wav, mp4,
                                     final=(idx == n_scenes),
                                     static_lines=static_lines,
                                     static_size=static_size, trans=trans)
            return mp4

    # ── PHOTO STOCK (foto real de Pexels): imagen + Ken Burns ──
    if medium == "photo":
        photo_path = _fetch_photo_stock(scene, idx, img_dir, aspect)
        if not photo_path:
            medium = "ai"  # Pexels sin clave/foto → caer a IA
        else:
            img_path = photo_path
    else:
        img_path = None

    # ── AI / foto: imagen sobre fondo + motion ──
    if medium == "ai":
        img_path, _gate_dec = _download_with_quality_gate(
            scene, idx, img_dir, aspect, work_dir)
    if not img_path:
        raise RuntimeError(f"escena {idx}: sin imagen")

    bg_img = os.path.join(work_dir, "tmp", f"e{idx:02d}_bg.jpg")
    if aspect == "horizontal":
        _smart_fit_to_aspect(img_path, target_ar="16:9")
        y.build_bg_bright(img_path, bg_img)
    else:
        _smart_fit_to_aspect(img_path, target_ar="9:16")
        m.build_bg_bright(img_path, bg_img)
    if Image is not None:
        _bg = Image.open(bg_img).convert("RGB")
        _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        _bg.save(bg_img)
    else:  # pragma: no cover
        pass

    motion = scene.get("motion")
    if aspect == "horizontal":
        y.render_scene(timings, bg_img, wav, mp4, final=(idx == n_scenes),
                       motion=motion, static_lines=static_lines,
                       static_size=static_size, trans=trans)
    else:
        m.render_scene(timings, bg_img, wav, mp4, final=(idx == n_scenes),
                       motion=motion, static_lines=static_lines,
                       static_size=static_size, trans=trans)
    return mp4


# ─────────────────────────────────────────
# Concat
# ─────────────────────────────────────────
def _concat(clips, out_path, aspect):
    if aspect == "horizontal":
        y.concat(clips, out_path)
    else:
        m.concat(clips, out_path)


# ─────────────────────────────────────────
# API pública
# ─────────────────────────────────────────
def render_emission(emission, output_mp4, *, work_dir=None, aspect=None,
                    rate=DEFAULT_RATE):
    """Renderiza una EditorialEmission a un MP4 con el renderer legacy.

    Args:
        emission: EditorialEmission de editorial_orchestrator.produce_editorial()
        output_mp4: ruta final del MP4
        work_dir: dir de trabajo (imgs/audio/out/tmp). Default: tmp del proyecto
        aspect: "vertical" | "horizontal". Default: según emission
    """
    if aspect is None:
        aspect = "horizontal" if emission.canvas_width == 1920 else "vertical"
    if work_dir is None:
        work_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "videos", "v2_pruebas",
            emission.plan.topic.replace(" ", "_") if emission.plan else "v2",
        )

    scenes = emission.scene_dicts
    # Inyectar rate si no viene
    for sd in scenes:
        sd.setdefault("rate", rate)

    clips = []
    for idx, sd in enumerate(scenes, start=1):
        print(f"    render escena {idx}/{len(scenes)}", flush=True)
        clips.append(_render_scene(sd, idx, len(scenes), work_dir, aspect))

    os.makedirs(os.path.dirname(output_mp4) or ".", exist_ok=True)
    _concat(clips, output_mp4, aspect)
    return output_mp4


def build_work_context(emission):
    """Devuelve el work_dir para una emission (para coordinar entre llamadas)."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "videos", "v2_pruebas",
        emission.plan.topic.replace(" ", "_") if emission.plan else "v2",
    )
