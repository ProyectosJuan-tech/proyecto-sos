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


def _download_image(scene, idx, img_dir, aspect="vertical"):
    """Descarga la imagen de una escena V2. Devuelve la ruta o None.

    V2.1: genera la imagen en el MISMO aspect que la plataforma (vertical 9:16 /
    horizontal 16:9). Antes se llamaba a flux_img.generate sin aspect, con lo que
    un video 16:9 generaba una 9:16 y luego el build_bg la recortaba al centro:
    esa es la causa raíz del "asset gigante / composición rota" en 16:9.
    """
    prompt = scene.get("ai") or scene.get("visual_event") or scene.get("q") or ""
    img = os.path.join(img_dir, f"e{idx:02d}.jpg")
    if os.path.exists(img) and os.path.getsize(img) > 5000:
        return img
    tried = 0
    img_aspect = "16:9" if aspect == "horizontal" else "9:16"
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
def _render_scene(scene, idx, n_scenes, work_dir, aspect):
    os.makedirs(os.path.join(work_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(work_dir, "tmp"), exist_ok=True)
    os.makedirs(os.path.join(work_dir, "imgs"), exist_ok=True)
    os.makedirs(os.path.join(work_dir, "out"), exist_ok=True)

    img_path = _download_image(scene, idx, os.path.join(work_dir, "imgs"), aspect)
    if not img_path:
        raise RuntimeError(f"escena {idx}: sin imagen")

    bg_img = os.path.join(work_dir, "tmp", f"e{idx:02d}_bg.jpg")
    if aspect == "horizontal":
        # V2.1: recorte smart (respeta aspect + foco) ANTES de build_bg.
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

    text = scene.get("text", "")
    wav, timings = _tts_and_timings(
        text, work_dir, idx, VOICE, DEEPEN, scene.get("rate", DEFAULT_RATE)
    )

    mp4 = os.path.join(work_dir, "out", f"e{idx:02d}.mp4")
    motion = scene.get("motion")
    trans = scene.get("trans")
    static_lines = scene.get("static_text") or None
    static_size = scene.get("static_size")

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
