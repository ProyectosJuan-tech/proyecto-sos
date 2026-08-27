#!/usr/bin/env python3
"""Permite "ver" imágenes con un modelo de visión (crítico visual QA).

Cascada de críticos:
  1. Free.ai qwen25-vl (gratis, describe sin alucinar — valida 2026-08-16)
  2. Cloudflare llama-3.2-vision / moondream (fallback, requiere cf creds)

Uso:
    python3 ver_imagen.py <imagen.jpg> ["pregunta opcional"]

Ejemplos:
    python3 ver_imagen.py VIDEOS_YOUTUBE/thumbnails/sabio_apura_thumb_9x16.jpg
    python3 ver_imagen.py thumb.jpg "¿El texto es legible? ¿Hay amontonamiento?"
"""
import base64
import json
import os
import sys

import httpx

ROOT = os.path.dirname(os.path.abspath(__file__))
VISION_MODEL = "@cf/meta/llama-3.2-11b-vision-instruct"
ALT_MODEL = "@cf/moondream/moondream3.1-9B-A2B"

DEFAULT_PROMPT = (
    "Describe this image in detail as if checking a YouTube thumbnail: "
    "what does it show, the subject and expression, colors, background, "
    "any text and EXACTLY what it says, layout and composition, "
    "and any visual problems (too much text, clutter, low contrast, "
    "elements cut off)."
)


def _creds():
    acct = open(os.path.join(ROOT, "cf_account_id.txt")).read().strip()
    token = open(os.path.join(ROOT, "cf_token.txt")).read().strip()
    return acct, token


def _payload(image_b64, prompt, model):
    return {"prompt": prompt, "image": "data:image/jpeg;base64," + image_b64}


def _extract(resp_json, model):
    if model == VISION_MODEL:
        return resp_json.get("result", {}).get("response", "")
    return resp_json.get("result", {}).get("description", "")


def _ver_cloudflare(imagen, pregunta):
    acct, token = _creds()
    b64 = base64.b64encode(open(imagen, "rb").read()).decode()
    prompt = pregunta or DEFAULT_PROMPT
    for m in (VISION_MODEL, ALT_MODEL):
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{m}"
            with httpx.Client(timeout=90.0) as client:
                r = client.post(url, json=_payload(b64, prompt, m),
                                headers={"Authorization": f"Bearer {token}"})
                if r.status_code != 200:
                    print(f"  vision {m} HTTP {r.status_code}: {r.text[:200]}", flush=True)
                    continue
                out = _extract(r.json(), m)
                if out:
                    return f"[{m}] {out}"
        except Exception as e:
            print(f"  vision {m} error: {e}", flush=True)
    return None


def _ver_freeai(imagen, pregunta):
    try:
        from freeai_edit import describe_image, get_key
        if not get_key():
            return None
        prompt = pregunta or DEFAULT_PROMPT
        out = describe_image(imagen, prompt)
        return f"[qwen25-vl/freeai] {out}"
    except Exception as e:
        print(f"  vision qwen25-vl error: {e}", flush=True)
        return None


def ver(imagen, pregunta=None):
    if not os.path.exists(imagen):
        return f"ERROR: no existe {imagen}"
    result = _ver_freeai(imagen, pregunta)
    if result:
        return result
    result = _ver_cloudflare(imagen, pregunta)
    if result:
        return result
    return "ERROR: ningún modelo de visión respondió"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: ver_imagen.py <imagen> [pregunta]")
    img = sys.argv[1]
    q = sys.argv[2] if len(sys.argv) > 2 else None
    print(ver(img, q))
