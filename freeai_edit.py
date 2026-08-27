#!/usr/bin/env python3
"""Edición img2img y visión (crítico) vía Free.ai — gratis, sin tarjeta.

Free.ai: una API con tokens diarios gratis (30k/día con cuenta; plan free).
Modelos self-hosted (Apache 2.0):
  - qwen-image-edit  : img2img / edición por instrucción (1.000 tokens/edición)
  - step1x-edit      : edición que razona, mejor en edits multi-paso (2.000)
  - sdxl             : img2img clásico, sigue menos la instrucción (1.000)
  - qwen25-vl        : visión / crítico (500 tokens/crítica)

Límites plan free: ~5 imágenes/día (tapa) + 1.000 requests/mes + 30k tokens/día.
Uso comercial OK (Apache 2.0 / MIT), sin watermark.

API: https://api.free.ai (key en env FREEAI_KEY o freeai_key.txt).
  - POST /v1/image/edit/    {"model", "prompt", "image_url": data URL, "operation":"img2img"}
  - POST /v1/image/describe/ {"model":"qwen25-vl", "image_url": data URL, "prompt"}
  - GET  /v1/models           verifica auth (sin costo)
"""
import base64
import mimetypes
import os
import time
from pathlib import Path

import httpx

_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "freeai_key.txt")
_BASE = "https://api.free.ai"

EDIT_MODELS = ("qwen-image-edit", "step1x-edit", "sdxl")
VISION_MODELS = ("qwen25-vl", "qwen-vl", "moondream2")
ENHANCE_MODELS = ("realesrgan",)
GENERATE_MODELS = ("flux2-klein", "sdxl", "flux-schnell")


def get_key():
    """Devuelve la key de Free.ai desde env o freeai_key.txt. '' si no hay."""
    k = os.environ.get("FREEAI_KEY", "").strip()
    if k:
        return k
    try:
        k = Path(_KEY_FILE).read_text().strip()
        return k
    except OSError:
        return ""


def _headers():
    key = get_key()
    if not key:
        raise RuntimeError("Sin key de Free.ai: setear FREEAI_KEY o crear freeai_key.txt")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _to_data_url(path):
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def test_key():
    """Verifica auth contra /v1/models (no consume tokens). True/False."""
    try:
        r = httpx.get(f"{_BASE}/v1/models", headers={"Authorization": f"Bearer {get_key()}"}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


def _wait_job(j, timeout=300):
    """Si la respuesta viene encolada ({queued, poll_url}), la sigue hasta terminar.

    Devuelve el dict final del job (con image_url) o lanza.
    """
    poll = j.get("poll_url")
    if not poll:
        return j
    url = poll if poll.startswith("http") else f"{_BASE}{poll}"
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(6)
        r = httpx.get(url, headers={"Authorization": f"Bearer {get_key()}"}, timeout=30)
        if r.status_code != 200:
            continue
        st = r.json()
        status = (st.get("status") or "").lower()
        if status in ("completed", "done", "succeeded"):
            return st
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"Job falló: {st}")
    raise RuntimeError(f"Timeout esperando job {j.get('job_id')}")


def edit_image(ref_path, prompt, out_path, model="qwen-image-edit", max_attempts=3):
    """Edita ref_path con una instrucción (img2img). Devuelve out_path o lanza.

    ref_path  : imagen base (p.ej. personaje con rostro fijo).
    prompt    : instrucción de edición (p.ej. "same woman, now with hair in a low bun").
    out_path  : dónde guardar el resultado (jpg/png).
    model     : qwen-image-edit | step1x-edit | sdxl.
    """
    if model not in EDIT_MODELS:
        raise ValueError(f"model debe ser uno de {EDIT_MODELS}")
    data = {
        "model": model,
        "prompt": prompt,
        "image_url": _to_data_url(ref_path),
        "operation": "img2img",
    }
    out = Path(out_path)
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = httpx.post(f"{_BASE}/v1/image/edit/", headers=_headers(), json=data, timeout=120)
        except httpx.HTTPError as e:
            last = e
            time.sleep(2 * attempt)
            continue
        if r.status_code == 200:
            try:
                j = r.json()
            except Exception:
                last = RuntimeError(f"Respuesta no JSON: {r.status_code}")
                continue
            try:
                j = _wait_job(j)
            except RuntimeError as e:
                last = e
                time.sleep(2 * attempt)
                continue
            url = j.get("image_url") or j.get("url")
            if not url:
                last = RuntimeError(f"Sin image_url en respuesta: {j}")
                continue
            img = httpx.get(url, timeout=60)
            if img.status_code != 200:
                last = RuntimeError(f"No pude bajar imagen {img.status_code}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(img.content)
            return str(out)
        # 402 = sin tokens; otros errores JSON con mensaje
        try:
            j = r.json()
            msg = j.get("error", {}).get("error") or j.get("error") or j.get("detail") or str(j)[:200]
        except Exception:
            msg = r.text[:200]
        if "402" in str(r.status_code) or "signup" in str(msg).lower():
            raise RuntimeError(f"Free.ai sin tokens/cuota: {r.status_code} {msg}")
        last = RuntimeError(f"HTTP {r.status_code}: {msg}")
        time.sleep(2 * attempt)
    raise last if last else RuntimeError("edit_image falló")


def describe_image(img_path, question, model="qwen25-vl", max_attempts=3):
    """Crítico visual: le pregunta algo a una imagen. Devuelve el texto de la respuesta.

    Usado para QA de imágenes (deformidades, si comunica la escena, etc.).
    """
    if model not in VISION_MODELS:
        raise ValueError(f"model debe ser uno de {VISION_MODELS}")
    files = {"image": (Path(img_path).name, Path(img_path).read_bytes())}
    data = {"model": model, "prompt": question}
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = httpx.post(f"{_BASE}/v1/image/describe/", headers={
                "Authorization": f"Bearer {get_key()}"}, files=files, data=data, timeout=90)
        except httpx.HTTPError as e:
            last = e
            time.sleep(2 * attempt)
            continue
        if r.status_code == 200:
            j = r.json()
            # respuestas típicas: {"description": ...} o {"text": ...} o {"choices": [...]}
            if isinstance(j, dict):
                for k in ("description", "text", "response", "answer", "result"):
                    if j.get(k):
                        return j[k]
                if j.get("choices"):
                    c = j["choices"][0]
                    if isinstance(c, dict):
                        return c.get("message", {}).get("content") or c.get("text") or str(c)
                    return str(c)
            return str(j)
        try:
            j = r.json()
            msg = j.get("error", {}).get("error") or j.get("error") or j.get("detail") or str(j)[:200]
        except Exception:
            msg = r.text[:200]
        if "402" in str(r.status_code):
            raise RuntimeError(f"Free.ai sin tokens: {r.status_code} {msg}")
        last = RuntimeError(f"HTTP {r.status_code}: {msg}")
        time.sleep(2 * attempt)
    raise last if last else RuntimeError("describe_image falló")


def upscale_image(img_path, out_path, scale=2, model="realesrgan", max_attempts=3):
    """Upscale una imagen con Real-ESRGAN vía free.ai. Devuelve out_path o lanza.

    img_path : imagen a upscalear (cualquier tamaño).
    out_path : dónde guardar el resultado.
    scale    : factor de upscale (2 o 4).
    """
    data = {
        "model": model,
        "image_url": _to_data_url(img_path),
        "scale": scale,
    }
    out = Path(out_path)
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = httpx.post(f"{_BASE}/v1/image/enhance/", headers=_headers(), json=data, timeout=180)
        except httpx.HTTPError as e:
            last = e
            time.sleep(2 * attempt)
            continue
        if r.status_code == 200:
            try:
                j = r.json()
            except Exception:
                last = RuntimeError(f"Respuesta no JSON: {r.status_code}")
                continue
            try:
                j = _wait_job(j)
            except RuntimeError as e:
                last = e
                time.sleep(2 * attempt)
                continue
            url = j.get("image_url") or j.get("url")
            if not url:
                last = RuntimeError(f"Sin image_url en respuesta: {j}")
                continue
            img = httpx.get(url, timeout=60)
            if img.status_code != 200:
                last = RuntimeError(f"No pude bajar imagen {img.status_code}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(img.content)
            return str(out)
        try:
            j = r.json()
            msg = j.get("error", {}).get("error") or j.get("error") or j.get("detail") or str(j)[:200]
        except Exception:
            msg = r.text[:200]
        if "402" in str(r.status_code) or "signup" in str(msg).lower():
            raise RuntimeError(f"Free.ai sin tokens/cuota: {r.status_code} {msg}")
        last = RuntimeError(f"HTTP {r.status_code}: {msg}")
        time.sleep(2 * attempt)
    raise last if last else RuntimeError("upscale_image falló")


def generate_image(prompt, out_path, model="flux2-klein", max_attempts=3):
    """Genera una imagen con un modelo de free.ai. Devuelve out_path o lanza.

    prompt  : texto descriptivo en inglés.
    out_path: dónde guardar (jpg/png).
    model   : flux2-klein | sdxl | flux-schnell.
    """
    data = {"prompt": prompt, "model": model}
    out = Path(out_path)
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = httpx.post(f"{_BASE}/v1/image/generate/", headers=_headers(), json=data, timeout=120)
        except httpx.HTTPError as e:
            last = e
            time.sleep(2 * attempt)
            continue
        if r.status_code == 200:
            try:
                j = r.json()
            except Exception:
                last = RuntimeError(f"Respuesta no JSON: {r.status_code}")
                continue
            try:
                j = _wait_job(j)
            except RuntimeError as e:
                last = e
                time.sleep(2 * attempt)
                continue
            url = j.get("image_url") or j.get("url")
            if not url:
                last = RuntimeError(f"Sin image_url en respuesta: {j}")
                continue
            img = httpx.get(url, timeout=60)
            if img.status_code != 200:
                last = RuntimeError(f"No pude bajar imagen {img.status_code}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(img.content)
            return str(out)
        try:
            j = r.json()
            msg = j.get("error", {}).get("error") or j.get("error") or j.get("detail") or str(j)[:200]
        except Exception:
            msg = r.text[:200]
        if "402" in str(r.status_code) or "signup" in str(msg).lower():
            raise RuntimeError(f"Free.ai sin tokens/cuota: {r.status_code} {msg}")
        last = RuntimeError(f"HTTP {r.status_code}: {msg}")
        time.sleep(2 * attempt)
    raise last if last else RuntimeError("generate_image falló")


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Free.ai: generate, upscale, edit, describe.")
    ap.add_argument("cmd", choices=["generate", "upscale", "edit", "describe", "test"],
                    help="generate '<prompt>' <out> [model] | upscale <img> <out> [scale] | "
                         "edit <img> '<prompt>' <out> [model] | describe <img> '<pregunta>' [model] | test")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()

    if a.cmd == "test":
        print("key OK" if test_key() else "key inválida o sin red")
        sys.exit(0)

    if a.cmd == "generate":
        if len(a.args) < 2:
            sys.exit("uso: freeai_edit.py generate '<prompt>' <out> [model]")
        model = a.args[2] if len(a.args) > 2 else "flux2-klein"
        print(generate_image(a.args[0], a.args[1], model=model))

    if a.cmd == "upscale":
        if len(a.args) < 2:
            sys.exit("uso: freeai_edit.py upscale <img> <out> [scale]")
        scale = int(a.args[2]) if len(a.args) > 2 else 2
        print(upscale_image(a.args[0], a.args[1], scale=scale))

    if a.cmd == "edit":
        if len(a.args) < 3:
            sys.exit("uso: freeai_edit.py edit <img> '<prompt>' <out> [model]")
        model = a.args[3] if len(a.args) > 3 else "qwen-image-edit"
        print(edit_image(a.args[0], a.args[1], a.args[2], model=model))

    if a.cmd == "describe":
        if len(a.args) < 2:
            sys.exit("uso: freeai_edit.py describe <img> '<pregunta>' [model]")
        model = a.args[2] if len(a.args) > 2 else "qwen25-vl"
        print(describe_image(a.args[0], a.args[1], model=model))
