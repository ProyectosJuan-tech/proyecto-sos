#!/usr/bin/env python3
"""B-roll vertical desde Pexels API. Adaptado de freefaceless/FreeFaceless (MIT).

Clave: env PEXELS_API_KEY o archivo pexels_key.txt en the project root.
Gratis sin tarjeta (200 req/h). Si no hay clave, las funciones devuelven None
y el pipeline cae al fallback siguiente (Wikimedia Commons).
"""
import os
from pathlib import Path

import httpx

_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pexels_key.txt")
API = "https://api.pexels.com/videos/search"


def _key():
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(_KEY_FILE) as f:
            key = f.read().strip()
    except OSError:
        key = ""
    return key


def available():
    return bool(_key())


def search_vertical(query, min_duration=3.0):
    """Devuelve URL del mejor video vertical (>=1080w) o None."""
    key = _key()
    if not key:
        return None
    try:
        r = httpx.get(
            API,
            headers={"Authorization": key},
            params={"query": query, "orientation": "portrait", "per_page": 15},
            timeout=30,
        )
        r.raise_for_status()
    except Exception:
        return None
    videos = r.json().get("videos", [])
    for v in videos:
        if v.get("duration", 0) < min_duration:
            continue
        files = [f for f in v["video_files"]
                 if f.get("width", 0) >= 1080 and f.get("height", 0) > f.get("width", 0)]
        if not files:
            continue
        files.sort(key=lambda f: f.get("height", 0))
        return files[0]["link"]
    return None


def search_landscape(query, min_duration=3.0):
    """Devuelve URL del mejor video horizontal 16:9 (>=1920w) o None."""
    key = _key()
    if not key:
        return None
    try:
        r = httpx.get(
            API,
            headers={"Authorization": key},
            params={"query": query, "orientation": "landscape", "per_page": 15},
            timeout=30,
        )
        r.raise_for_status()
    except Exception:
        return None
    videos = r.json().get("videos", [])
    for v in videos:
        if v.get("duration", 0) < min_duration:
            continue
        files = [f for f in v["video_files"]
                 if f.get("width", 0) >= 1920 and f.get("height", 0) <= f.get("width", 0)]
        if not files:
            continue
        files.sort(key=lambda f: f.get("width", 0), reverse=True)
        return files[0]["link"]
    return None


def download(url, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
    return out_path


def fetch_for_scene(query, out_path, fallback_query="abstract background"):
    """Descarga un b-roll vertical para una escena. Devuelve Path o None."""
    url = search_vertical(query)
    if url is None:
        url = search_vertical(fallback_query)
    if url is None:
        return None
    try:
        return download(url, out_path)
    except Exception:
        return None


def fetch_for_scene_landscape(query, out_path,
                              fallback_query="abstract landscape"):
    """Descarga un b-roll horizontal 16:9 para una escena. Devuelve Path o None."""
    url = search_landscape(query)
    if url is None:
        url = search_landscape(fallback_query)
    if url is None:
        return None
    try:
        return download(url, out_path)
    except Exception:
        return None


if __name__ == "__main__":
    import sys
    print("Pexels:", "OK" if available() else "SIN CLAVE (pexels_key.txt)")
    if available():
        print(search_vertical(sys.argv[1] if len(sys.argv) > 1 else "coffee"))
