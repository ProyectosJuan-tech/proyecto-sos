#!/usr/bin/env python3
"""Rehace los 3 largos para YOUTUBE en horizontal 16:9 (1920x1080).

Toma las escenas de hacer_videos_nuevos (textos ya con CTA
"Dale like, suscribite, comentá y compartí"), regenera imágenes IA 16:9
y renderiza con el pipeline YouTube. Guarda en VIDEOS_YOUTUBE/largos/.
NO toca los verticales de Facebook (videos/*/out/).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_youtube as yy
import hacer_videos_nuevos as n
import hacer_videos_youtube as y

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJECT_ROOT, "videos", "youtube")
DEST = os.path.join(PROJECT_ROOT, "VIDEOS_YOUTUBE", "largos")
TARGETS = ["inmediatez", "libertad", "darse-cuenta"]
VOICES = {"jorge": {"voice": "es-MX-JorgeNeural", "deepen": 0.92},
          "elena": {"voice": "es-AR-ElenaNeural", "deepen": 0.88}}

LIGHT_SCENES = n.LIGHT_SCENES


def build_video_yt(name):
    vid = next(v for v in n.VIDEOS if v["name"] == name)
    scenes = vid["scenes"]
    if name in LIGHT_SCENES:
        scenes = [
            dict(sc, light=True) if i + 1 in LIGHT_SCENES[name] else dict(sc)
            for i, sc in enumerate(scenes)
        ]
    rate = vid.get("rate", "+0%")
    vd = {
        "imgs": os.path.join(ROOT, name, "imgs"),
        "audio": os.path.join(ROOT, name, "audio"),
        "out": os.path.join(ROOT, name, "out"),
        "tmp": os.path.join(ROOT, name, "tmp"),
    }
    for d in vd.values():
        os.makedirs(d, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)

    voice_keys = vid.get("voices") or ["jorge"]
    voice_keys = ["jorge" if v in ("male", "jorge") else v for v in voice_keys]
    for vk in voice_keys:
        clips = []
        for idx, scene in enumerate(scenes, start=1):
            print(f"[{name}/{vk}] escena {idx}/{len(scenes)}", flush=True)
            clips.append(y.build_scene(vd, scene, idx, vk, len(scenes), rate=rate))
        out = os.path.join(vd["out"], f"{name}_{vk}.mp4")
        yy.concat(clips, out)
        if vid.get("bgm"):
            bgm = os.path.join(ROOT, "bgm", "ambient.wav")
            n.m.generate_bgm(bgm)
            mixed = out + ".bgm.mp4"
            n.m.mix_bgm(out, bgm, mixed)
            os.replace(mixed, out)
        dur = yy.probe_duration(out)
        out_name = f"{name}_male.mp4" if vk == "jorge" else f"{name}_female.mp4"
        final = os.path.join(DEST, out_name)
        os.replace(out, final)
        ok = "MONETIZABLE (>=8min)" if dur >= 480 else "corto"
        print(f"OK {final}  {dur/60:.1f} min  [{ok}]", flush=True)


if __name__ == "__main__":
    only = sys.argv[1:]
    for name in TARGETS:
        if not only or name in only:
            build_video_yt(name)
