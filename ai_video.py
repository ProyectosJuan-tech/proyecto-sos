#!/usr/bin/env python3
"""Generador de clips de video AI (vertical 9:16 / horizontal 16:9) vía
Pollinations (gen.pollinations.ai). Requiere POLLINATIONS_KEY (env) o
pollinations_key.txt; sin key devuelve None en silencio y el caller cae a
Pexels o a imagen con Ken Burns.

Endpoint: GET https://gen.pollinations.ai/video/{prompt}?model=...&aspectRatio=...
Key gratis (sin tarjeta): crear cuenta en https://enter.pollinations.ai
  tier Spore = 1.5 pollen/semana (alcanza para pocos clips).
  wan-fast es el modelo más barato (0.01 pollen/s).
"""
import os
import time
import urllib.parse

import httpx

_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "pollinations_key.txt")
_BASE = "https://gen.pollinations.ai/video/{prompt}"
DEFAULT_MODEL = "wan-fast"
# (modelo, pollen/s) de los disponibles hoy (2026-08)
_MODELS = {
    "wan-fast": 0.01,
    "p-video": 0.02,
    "nova-reel": 0.08,
    "veo": 0.08,
    "wan": 0.10,
    "seedance-2.5": 0.18,
    "seedance-2.0": 0.18,
    "grok-imagine-video-1.5": 0.14,
    "seedance-pro": None,
    "wan-pro": None,
    "grok-video-pro": None,
    "happyhorse-1.1": None,
}


def _key():
    key = os.environ.get("POLLINATIONS_KEY", "").strip()
    if key:
        return key
    try:
        with open(_KEY_FILE) as f:
            key = f.read().strip()
    except OSError:
        key = ""
    return key


def available():
    """True si hay key (sin key el video AI no funciona)."""
    return bool(_key())


def models():
    return list(_MODELS)


def fetch_for_scene(prompt, out_path, duration=5, aspect="9:16",
                    model=DEFAULT_MODEL, seed=-1, retries=2, wait=45,
                    timeout=300):
    """Genera un clip AI y lo guarda en out_path. Devuelve out_path o None
    (sin key, key inválida, sin créditos o fallo de red). Nunca lanza."""
    key = _key()
    if not key:
        return None
    encoded = urllib.parse.quote(prompt, safe="")
    params = urllib.parse.urlencode({
        "model": model, "aspectRatio": aspect, "duration": duration,
        "seed": seed, "key": key,
    })
    url = _BASE.format(prompt=encoded) + "?" + params
    last = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url)
            if resp.status_code in (401, 403, 404):
                print("    Pollinations video: key inválida o modelo no existe "
                      f"({resp.status_code})", flush=True)
                return None
            if resp.status_code == 402:
                print("    Pollinations video: sin créditos (402)", flush=True)
                return None
            if resp.status_code == 429:
                last = f"429 rate limit, intento {attempt + 1}/{retries}"
                time.sleep(wait + 15 * attempt)
                continue
            resp.raise_for_status()
            if len(resp.content) < 1024:
                last = "contenido demasiado chico"
                time.sleep(wait)
                continue
            out_path.write_bytes(resp.content)
            print(f"    video AI OK vía Pollinations/{model} "
                  f"({os.path.getsize(out_path)} B)", flush=True)
            return out_path
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 402, 403, 404):
                return None
            last = str(e)
            time.sleep(wait)
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last = str(e)
            time.sleep(wait)
    print(f"    Pollinations video falló: {last}", flush=True)
    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit(f"uso: ai_video.py 'prompt' [out.mp4] [modelo] "
                 f"[aspecto 9:16|16:9] [segundos]\n"
                 f"modelos: {', '.join(models())}")
    prompt = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ai_video_test.mp4"
    model = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_MODEL
    aspect = sys.argv[4] if len(sys.argv) > 4 else "9:16"
    dur = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    print("key presente:", bool(_key()))
    res = fetch_for_scene(prompt, out, duration=dur, aspect=aspect, model=model)
    print("resultado:", res)
