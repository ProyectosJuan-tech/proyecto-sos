#!/usr/bin/env python3
"""Producción en serie desde un JSON de guiones aprobados.

Pieza 3 del "Método Viral": recibe la salida de generar_textos.py --banco
(textos_generados/guiones_<fecha>.json) y renderiza los videos SIN editar
hacer_shorts.py / hacer_videos_youtube.py a mano.

- Videos "short" → build_short de hacer_shorts.py (cortos verticales 1 escena).
- Videos "largo" → build_video de hacer_videos_youtube.py (largos horizontales).

Uso:
    python3 hacer_serie.py textos_generados/guiones_<fecha>.json
        [--elegir 1,2]        índices de videos del JSON a renderizar
        [--frases 1,2]        para shorts: qué frases candidatas renderizar
        [--voz jorge,elena]   voces a usar (default: las de cada video)
        [--bgm]               forzar BGM en shorts (largos ya lo traen)
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_shorts as hs
import hacer_videos_youtube as hy

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = PROJECT_ROOT


def _slug(titulo):
    s = re.sub(r"[^a-z0-9]+", "_", titulo.lower()).strip("_")
    return s[:40]


def _probe_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=15).stdout.strip()
        return float(out) if out else 0
    except Exception:
        return 0


def _build_largo(video, idx, voces, bgm):
    scenes = []
    motions = ["zoom-in", "pan-right", "zoom-out", "pan-left"]
    for i, e in enumerate(video.get("escenas", [])):
        scenes.append({
            "text": e["text"],
            "ai": e.get("ai", ""),
            "q": e.get("q", ""),
            "motion": motions[i % len(motions)],
        })
    if not scenes:
        print(f"  ⚠ video {idx} sin escenas, se saltea", flush=True)
        return None
    vid = {
        "name": _slug(video.get("titulo", f"largo_{idx}")),
        "bgm": True,
        "rate": "-8%",
        "voices": voces or ["jorge"],
        "scenes": scenes,
    }
    hy.build_video(vid)
    final = os.path.join(hy.DEST, f"{vid['name']}_{vid['voices'][0]}.mp4")
    dur = _probe_duration(final)
    if dur < 480:
        print(f"  ⚠ {dur/60:.1f} min < 8 min (monetizable). Regla del canal: "
              f"no hincharlo para llegar; si el contenido aguanta, agregar bloques, "
              f"si no, publicar como está.", flush=True)
    print(f"OK {final}", flush=True)
    return final


def _build_short(frase, titulo, idx, voces, bgm):
    sid = _slug(frase.get("keyword") or titulo or f"short_{idx}")
    prompt = frase.get("prompt", "")
    if not prompt:
        print(f"  ⚠ frase {idx} sin prompt de imagen, se saltea", flush=True)
        return None
    short = {
        "id": sid,
        "text": frase["texto"],
        "prompt": prompt,
        "style": hs.WARM_STYLE,
        "voices": voces or list(hs.VOICES),
    }
    if bgm:
        short["bgm"] = True
    for vk in short["voices"]:
        print(f"[{short['id']}/{vk}]", flush=True)
        hs.build_short(short, vk)
    mp4 = os.path.join(ROOT, "videos", "shorts", "out", f"{sid}_{short['voices'][0]}.mp4")
    print(f"OK {mp4}", flush=True)
    return mp4


def main():
    ap = argparse.ArgumentParser(description="Renderiza una serie desde guiones aprobados")
    ap.add_argument("guiones", help="archivo JSON (salida de generar_textos.py --banco)")
    ap.add_argument("--elegir", default=None, help="índices de videos (ej. 1,2)")
    ap.add_argument("--frases", default=None, help="para shorts: índices de frases candidatas")
    ap.add_argument("--voz", default=None, help="voces separadas por coma (ej. jorge,elena)")
    ap.add_argument("--bgm", action="store_true", help="forzar BGM en shorts")
    args = ap.parse_args()

    with open(args.guiones) as f:
        data = json.load(f)
    videos = data.get("videos", [])
    elegir = [int(x) for x in args.elegir.split(",")] if args.elegir else None
    frases_idx = [int(x) for x in args.frases.split(",")] if args.frases else None
    voces = args.voz.split(",") if args.voz else None

    for idx, v in enumerate(videos, 1):
        if elegir and idx not in elegir:
            continue
        print(f"\n=== [{idx}] {v['titulo']} ===", flush=True)
        if v["formato"] == "largo":
            _build_largo(v, idx, voces, args.bgm)
        else:
            for fi, fr in enumerate(v.get("frases", []), 1):
                if frases_idx and fi not in frases_idx:
                    continue
                _build_short(fr, v.get("titulo"), fi, voces, args.bgm)


if __name__ == "__main__":
    main()