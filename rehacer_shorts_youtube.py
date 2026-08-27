#!/usr/bin/env python3
"""Re-renderiza los shorts para YOUTUBE con el CTA nuevo.

Genera los shorts en VIDEOS_YOUTUBE/shorts/ con el texto ya editado
(CTA "Dale like, suscribite y comentá"). NO toca videos/shorts/out/
(versiones de Facebook).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_caverna as m
import hacer_shorts as hs

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJECT_ROOT, "videos")
DEST = os.path.join(PROJECT_ROOT, "VIDEOS_YOUTUBE", "shorts")
SRC_OUT = os.path.join(ROOT, "shorts", "out")

os.makedirs(DEST, exist_ok=True)


def build_yt_short(short, vkey):
    text = short.get("text_yt") or short["text"]
    v = hs.VOICES[vkey]
    d = {
        "imgs": os.path.join(ROOT, "shorts", "imgs"),
        "audio": os.path.join(ROOT, "shorts", "audio"),
        "out": DEST,
        "tmp": os.path.join(ROOT, "shorts", "tmp"),
    }
    for k in d.values():
        os.makedirs(k, exist_ok=True)

    sid = short["id"]
    img_path = os.path.join(d["imgs"], f"{sid}.jpg")
    if not (os.path.exists(img_path) and os.path.getsize(img_path) > 5000):
        try:
            hs.download_ai(short["prompt"], img_path, seed=411, style=short["style"])
        except Exception as e:
            print(f"  IA falló, uso Commons: {e}", flush=True)
            m.download_image({"q": short.get("q")}, img_path)
    m.strip_img_metadata(img_path)

    bg_img = os.path.join(d["tmp"], f"{sid}_{vkey}_bg.jpg")
    if not (short.get("estilo") or short.get("handdraw")):
        m.build_bg(img_path, bg_img)
        from PIL import Image, ImageFilter
        _bg = Image.open(bg_img).convert("RGB")
        _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        _bg.save(bg_img)

    import zlib
    wav = os.path.join(d["audio"], f"{sid}_{vkey}_{zlib.crc32(text.encode())}.wav")
    if not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(text, v["voice"], wav,
                                  deepen=v["deepen"]))

    tj = os.path.join(d["tmp"], f"{sid}_{vkey}_{zlib.crc32(text.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = m.align_words(text, wav)
        if timings is None:
            toks = text.split()
            dur = m.probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))

    mp4 = os.path.join(d["out"], f"{sid}_{vkey}.mp4")
    m.render_pipeline(short, timings, img_path, bg_img, wav, mp4, final=True)
    if short.get("bgm"):
        bgm = os.path.join(ROOT, "bgm", "ambient.wav")
        m.generate_bgm(bgm)
        mixed = mp4 + ".bgm.mp4"
        m.mix_bgm(mp4, bgm, mixed)
        os.replace(mixed, mp4)
    total = m.probe_duration(mp4)
    hs.check_meta_rules(short, timings, total)
    print(f"OK {mp4} {total:.1f}s", flush=True)


if __name__ == "__main__":
    only = sys.argv[1:]
    targets = [s for s in hs.SHORTS if not only or s["id"] in only]
    for short in targets:
        for vkey in short.get("voices") or list(hs.VOICES):
            print(f"[{short['id']}/{vkey}]", flush=True)
            build_yt_short(short, vkey)
