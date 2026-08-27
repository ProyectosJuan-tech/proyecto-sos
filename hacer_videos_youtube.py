#!/usr/bin/env python3
"""Videos largos horizontales para YOUTUBE (16:9, monetizables 8+ min).

Misma lógica que hacer_videos_nuevos.py pero con el pipeline YouTube:
- Fondo horizontal 1920x1080 (imagen IA 16:9 o b-roll Pexels landscape).
- Voz jorge/elena + karaoke word-by-word + BGM opcional.
- Los videos finales caen en VIDEOS_YOUTUBE/largos/.

Cómo crear un video largo nuevo:
1. Verificar en cerebro/wiki/contenido/frases-usadas.md que no se repite.
2. Agregar un dict en VIDEOS: name, scenes (text + ai + q + motion/stock).
3. Correr y registrar en cerebro/wiki/contenido/.
"""
import json
import os
import subprocess
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_caverna as m
import hacer_video_youtube as y

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJECT_ROOT, "videos", "youtube")
DEST = os.path.join(PROJECT_ROOT, "VIDEOS_YOUTUBE", "largos")
STYLE = ", cinematic, dark and moody, dramatic lighting, photorealistic, high detail"
LIGHT_STYLE = ", bright airy, high-key soft diffused window light, warm cream and sage palette, gentle highlights, no hard shadows, crisp and colorful, warm and hopeful, photorealistic, high detail"

VOICES = {
    "jorge": {"voice": "es-MX-JorgeNeural", "deepen": 0.92},
}

def _sabio_manipuladores_yt():
    import sabio_manipuladores as sm
    return sm.scenes(
        "Si te sirvió, suscribite y compartilo con alguien que hoy necesita callar "
        "con calma. El sabio te deja una frase cada día en el canal. Nos vemos "
        "mañana.")


VIDEOS = [
    {
        "name": "demo-monetizable",
        "bgm": True,
        "voices": ["jorge"],
        "scenes": [
            {"ai": "Woman in her fifties sitting by a window at golden hour, eyes closed, warm light, peaceful, photorealistic",
             "q": "woman window golden hour",
             "text": "Este es un video de prueba del pipeline de YouTube. Si lo ves, significa que todo funcionó: imagen horizontal, voz, karaoke y música de fondo.",
             "motion": "zoom-in"},
            {"ai": "Open book on a wooden table with warm morning light, dust particles, cozy",
             "q": "open book morning light",
             "text": "Acá va una segunda escena con otro fondo y movimiento de cámara. En un video real, cada escena desarrolla una idea del método.",
             "motion": "pan-right"},
            {"ai": "Silhouette walking toward sunrise on a hill, golden landscape, hopeful",
             "q": "silhouette sunrise hill",
             "text": "El video largo horizontal es el formato que monetiza en YouTube: más de ocho minutos, con anuncios y retención. Suscríbete.",
             "motion": "zoom-out"},
        ],
    },
    {
        "name": "sabio-manipuladores",
        "bgm": True,
        "rate": "-8%",
        "voices": ["jorge"],
        "scenes": _sabio_manipuladores_yt(),
    },
]


def _muerte_yt():
    import muerte_scenes as ms
    return [dict(s, light=(i in ms.LIGHT))
            for i, s in enumerate(ms.scenes_muerte(
                "Suscríbete, dale like y comenta."), start=1)]


VIDEOS.append({
    "name": "muerte",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _muerte_yt(),
})


def _manipulacion_yt():
    import manipulacion_scenes as ms
    return ms.scenes(
        "Si te gustó, suscribite, me ayudás mucho. Dale un like y activá la "
        "campanita para que YouTube te avise cada vez que subo otro video.")


VIDEOS.append({
    "name": "manipulacion",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _manipulacion_yt(),
})


# V2 (2026-08-16): mismas escenas/guion, imágenes/videos del set descargado
# en la carpeta de imágenes del video. Solo N3 (galletita) y N6
# (calendario) quedan IA porque el set no trae equivalente.
V2_IMG = {
    1: "img1", 2: "img2", 3: "img5", 4: "hombre_oficina", 5: "hombre_cansado",
    6: "img2", 7: "img4", 8: "img4", 9: "hombre_oficina", 10: "img5",
    11: "img5", 12: "capatillas", 13: "img_cafe", 14: "img_cafe",
    15: "hombre_cansado", 16: "img_cafe", 17: "N3", 18: "ropa_preparada",
    19: "cosas_ordenadas", 20: "cosas_ordenadas", 21: "img5", 22: "img_cafe",
    23: "img_cafe", 24: "ropa_preparada", 25: "hombre_pensando_camino",
    26: "cosas_ordenadas", 27: "plato_sucio", 28: "N6", 29: "mujer_leyendo",
    30: "img3", 31: "hombre_pensando_camino", 32: "hombre_pensando_camino",
    33: "hombre_pensando_camino", 34: "img1", 35: "img3", 36: "plato_sucio",
    37: "img1", 38: "img3",
}


def _habitos_v2_yt():
    import habitos_scenes as hs
    scenes = hs.scenes()
    for i, s in enumerate(scenes, start=1):
        s["img"] = V2_IMG.get(i, s["img"])
    return scenes


def _habitos_yt():
    import habitos_scenes as hs
    return hs.scenes()


VIDEOS.append({
    "name": "habitos-sistema",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _habitos_yt(),
})

VIDEOS.append({
    "name": "habitos-sistema-v2",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _habitos_v2_yt(),
})


def _florecer_yt():
    import florecer_scenes as fs
    return fs.scenes()


VIDEOS.append({
    "name": "florecer-largo",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _florecer_yt(),
})


def _integrar_yt():
    import integrar_scenes as s
    return s.scenes()


VIDEOS.append({
    "name": "integrar-no-sanar",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _integrar_yt(),
})


def download_ai_image(prompt, out_path, seed=None, style=None):
    try:
        import flux_img
        return flux_img.generate(prompt + (style or LIGHT_STYLE), out_path, aspect="16:9")
    except Exception as e:
        print(f"    IA falló: {e}", flush=True)
        raise RuntimeError(f"IA no generó imagen: {prompt[:40]}")


def find_local_img(imgs_dir, idx, name=None):
    import glob
    if name:
        for p in sorted(glob.glob(os.path.join(imgs_dir, f"{name}.*"))):
            if os.path.getsize(p) > 5000:
                return p
    for p in sorted(glob.glob(os.path.join(imgs_dir, f"e{idx:02d}.*"))):
        if os.path.getsize(p) > 5000:
            return p
    return None


def find_local_video(imgs_dir, idx):
    p = os.path.join(imgs_dir, f"e{idx:02d}.mp4")
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        return p
    return None


def rate_suffix(rate):
    if not rate or rate == "+0%":
        return ""
    return "_r" + rate.replace("%", "").replace("+", "p").replace("-", "m")


def build_scene(vid_dirs, scene, idx, vk, n_scenes, rate="+0%"):
    slug = f"e{idx:02d}_{vk}"
    rsfx = rate_suffix(rate)
    img_name = scene.get("img")
    img_path = find_local_img(vid_dirs["imgs"], idx, img_name) or os.path.join(
        vid_dirs["imgs"], f"{img_name or 'e%02d' % idx}.jpg")
    bg_img = os.path.join(vid_dirs["tmp"], f"{slug}_bg.jpg")
    etag = m.tts_engine_tag(VOICES[vk]["voice"])

    # Resolver escena semántica → prompt técnico + emphasis tags
    scene = m.resolve_visual(scene)

    # Parse HTML <strong>/<em> tags: TTS recibe texto limpio, render recibe emphasis_map
    raw_text = scene["text"]
    if "<" in raw_text:
        tts_text, emphasis_map = m.parse_html_emphasis(raw_text)
    else:
        tts_text = raw_text
        emphasis_map = {}

    wav = os.path.join(vid_dirs["audio"],
                       f"{slug}{rsfx}{etag}_{zlib.crc32(tts_text.encode())}.wav")
    mp4 = os.path.join(vid_dirs["out"], f"{slug}.mp4")
    os.makedirs(vid_dirs["tmp"], exist_ok=True)

    video_path = find_local_video(vid_dirs["imgs"], idx)
    if video_path is None and scene.get("stock"):
        try:
            import pexels_stock
            if pexels_stock.available():
                q = scene.get("q") or scene.get("ai")
                video_path = pexels_stock.fetch_for_scene_landscape(
                    q, os.path.join(vid_dirs["imgs"], f"e{idx:02d}.mp4"))
        except Exception as e:
            print(f"    stock falló: {e}", flush=True)
            video_path = None

    if video_path is None and scene.get("ai_video"):
        try:
            import ai_video
            if ai_video.available():
                video_path = ai_video.fetch_for_scene(
                    scene.get("av") or scene["ai"],
                    os.path.join(vid_dirs["imgs"], f"e{idx:02d}_ai.mp4"),
                    aspect="16:9", model=scene.get("ai_model", "wan-fast"))
        except Exception as e:
            print(f"    ai_video falló: {e}", flush=True)
            video_path = None

    if not (os.path.exists(img_path) and os.path.getsize(img_path) > 5000):
        try:
            download_ai_image(scene["ai"], img_path, seed=idx * 101,
                              style=scene.get("style", LIGHT_STYLE))
        except Exception as e:
            print(f"    IA falló, uso Commons: {e}", flush=True)
            m.download_image(scene, img_path)
    m.strip_img_metadata(img_path)
    if scene.get("light", True):
        y.build_bg_bright(img_path, bg_img)
    else:
        y.build_bg(img_path, bg_img)
    from PIL import Image, ImageFilter
    _bg = Image.open(bg_img).convert("RGB")
    _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
    _bg.save(bg_img)

    voice = VOICES[vk]["voice"]
    deepen = VOICES[vk]["deepen"]
    if not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(tts_text, voice, wav,
                                  deepen=deepen, rate=rate))
    if scene.get("boom"):
        from hacer_videos_nuevos import mix_boom
        wav = mix_boom(wav)
    tj = os.path.join(vid_dirs["tmp"],
                      f"{slug}{rsfx}{etag}_{zlib.crc32(tts_text.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = m.align_words(tts_text, wav)
        if timings is None:
            toks = tts_text.split()
            dur = y.probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))

    n = n_scenes
    static_lines = scene.get("static_text") or None
    static_size = scene.get("static_size")
    static_sizes = scene.get("static_sizes")
    trans = scene.get("trans")
    if video_path is not None:
        y.render_scene_video(timings, video_path, wav, mp4,
                             final=(idx == n), static_lines=static_lines,
                             static_size=static_size, static_sizes=static_sizes,
                             trans=trans, emphasis_map=emphasis_map)
    else:
        y.render_scene(timings, bg_img, wav, mp4, final=(idx == n),
                       motion=scene.get("motion"), static_lines=static_lines,
                       static_size=static_size, static_sizes=static_sizes,
                       trans=trans, emphasis_map=emphasis_map)
    return mp4


def build_video(vid):
    name = vid["name"]
    scenes = vid["scenes"]
    vd = {
        "imgs": os.path.join(ROOT, name, "imgs"),
        "audio": os.path.join(ROOT, name, "audio"),
        "out": os.path.join(ROOT, name, "out"),
        "tmp": os.path.join(ROOT, name, "tmp"),
    }
    for d in vd.values():
        os.makedirs(d, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)

    for vk in (vid.get("voices") or list(VOICES)):
        clips = []
        for idx, scene in enumerate(scenes, start=1):
            print(f"[{name}/{vk}] escena {idx}/{len(scenes)}", flush=True)
            clips.append(build_scene(vd, scene, idx, vk, len(scenes),
                                     rate=vid.get("rate", "+0%")))
        out = os.path.join(vd["out"], f"{name}_{vk}.mp4")
        y.concat(clips, out)
        if vid.get("bgm"):
            bgm = os.path.join(ROOT, "bgm", "ambient.wav")
            m.generate_bgm(bgm)
            mixed = out + ".bgm.mp4"
            m.mix_bgm(out, bgm, mixed)
            os.replace(mixed, out)
        dur = y.probe_duration(out)
        final = os.path.join(DEST, f"{name}_{vk}.mp4")
        os.replace(out, final)
        ok = "MONETIZABLE (>=8min)" if dur >= 480 else "corto"
        print(f"OK {final}  {dur/60:.1f} min  [{ok}]", flush=True)


def listar_escenas(name):
    v = next(v for v in VIDEOS if v["name"] == name)
    for idx, sc in enumerate(v["scenes"], start=1):
        print(f"e{idx:02d}.jpg  |  {sc['text'][:70]}")
        print(f"   prompt: {sc['ai']}")
    print(f"\nGuardar en: {os.path.join(ROOT, name, 'imgs')}/")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "escenas":
        for n in (args[1:] or [v["name"] for v in VIDEOS]):
            print(f"\n=== {n} ===")
            listar_escenas(n)
        sys.exit(0)
    names = args or [v["name"] for v in VIDEOS]
    for v in VIDEOS:
        if v["name"] in names:
            build_video(v)
