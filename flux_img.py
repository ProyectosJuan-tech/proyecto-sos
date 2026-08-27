#!/usr/bin/env python3
"""Generador de imágenes con cascada de proveedores gratuitos.

Adaptado de numbpill3d/ffmpeg-ai (MIT) — src/ffmpeg_ai/ai/images.py.

Orden de proveedores (todos sin tarjeta):
  1. Pollinations  — gratis, sin key (rate-limit por IP, se serializa solo).
                     Endpoint viejo (image.pollinations.ai) siempre devuelve
                     la misma imagen (Sana 576x1024). Endpoint nuevo
                     (gen.pollinations.ai) requiere API key gratis en
                     enter.pollinations.ai — modelos: zimage, seedream5,
                     nanobanana-pro, gptimage, klein, flux.
  2. free.ai       — FLUX.2 Klein 4B, SDXL, Real-ESRGAN upscale.
                     Plan free: 1 generación/día, upscale sin límite.
                     Key en FREEAI_KEY env o freeai_key.txt.
  3. Gemini        — gemini-2.5-flash-image (Nano Banana), gratis con key sin
                     tarjeta (~250 img/día; GEMINI_API_KEY env o gemini_key.txt).
                     Si no hay key se salta en silencio. Alta calidad.
  4. Cloudflare    — Workers AI FLUX.1-schnell/SDXL, gratis con cuenta sin tarjeta
                     (10k neuronas/día; CLOUDFLARE_ACCOUNT_ID+CLOUDFLARE_API_TOKEN
                     env o cf_account_id.txt+cf_token.txt). Se salta sin key.
  5. HuggingFace   — gratis con HF_TOKEN (env o hf_token.txt); FLUX/SDXL
                     deprecados hoy, pero si resucitan entra primero
  6. Stable Horde  — clúster comunitario, guest key embebida
  7. Together      — FLUX.1-schnell-Free, gratis indefinido (requiere TOGETHER_API_KEY)

HERRAMIENTAS COMPLEMENTARIAS (no en cascade, uso directo):
  - freeai_edit.py   — generate_image(), upscale_image(), remove_background()
  - rembg            — eliminación de fondos en CPU (u2net model)
  - withoutbg        — mejor eliminación de fondos (ONNX, CPU, 455MB model)
  - Real-ESRGAN      — upscale 2x/4x vía free.ai API

FLUX PROMPTING (Black Forest Labs best practices):
  - SASC: Subject → Action → Setting → Camera
  - SIEMPRE incluir referencia de cámara: "shot on Sony A7IV, 85mm f/2.8"
  - SIEMPRE incluir film stock: "Kodak Portra 400" (calido) o "Fujifilm Pro 400H"
  - FLUX NO soporta negative prompts — usar negación natural: "no faces visible"
  - La luz tiene el mayor impacto en calidad: ser específico
  - Prompts de 30-80 palabras para la mayoría de escenas

Si todos fallan, lanza RuntimeError (el caller cae a Wikimedia Commons).
Para forzar un proveedor: flux_img.generate(..., provider="gemini") o env IMG_PROVIDER.
"""
import asyncio
import base64
import json
import os
import random
import urllib.parse
from pathlib import Path

import httpx

_TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_token.txt")
_GEMINI_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_key.txt")
_CF_ACCT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf_account_id.txt")
_CF_TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf_token.txt")
_GEMINI_MODEL = "gemini-2.5-flash-image"
DEFAULT_ASPECT = "9:16"

# (width, height) nativos por proveedor (9:16 vertical)
IMG_WIDTH, IMG_HEIGHT = 1080, 1920

_POLLINATIONS_MODELS = ["flux-realism", "flux"]

_HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
]

_HORDE_PORTRAIT = (768, 1344)

_CF_MODELS = [
    "@cf/black-forest-labs/flux-1-schnell",
    "@cf/stabilityai/stable-diffusion-xl-base-1.0",
]


def _token():
    return _read_key_file("HF_TOKEN", _TOKEN_FILE)


def _read_key_file(env_name, path):
    """Lee una key de env o archivo (prioridad: env > archivo)."""
    val = os.environ.get(env_name, "").strip()
    if val:
        return val
    try:
        with open(path) as f:
            val = f.read().strip()
    except OSError:
        val = ""
    return val


def _gemini_key():
    return _read_key_file("GEMINI_API_KEY", _GEMINI_KEY_FILE)


def _cloudflare_creds():
    acct = _read_key_file("CLOUDFLARE_ACCOUNT_ID", _CF_ACCT_FILE)
    token = _read_key_file("CLOUDFLARE_API_TOKEN", _CF_TOKEN_FILE)
    return acct, token


def _get_pollinations_lock():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    lock_attr = f"_pollinations_lock_{id(loop) if loop else 'none'}"
    if not hasattr(_get_pollinations_lock, lock_attr):
        setattr(_get_pollinations_lock, lock_attr, asyncio.Lock())
    return getattr(_get_pollinations_lock, lock_attr)


async def _try_pollinations(prompt, out_path, seed, width, height):
    encoded = urllib.parse.quote(prompt, safe="")
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        for model in _POLLINATIONS_MODELS:
            url = (f"https://image.pollinations.ai/prompt/{encoded}"
                   f"?width={width}&height={height}&seed={seed}"
                   f"&nologo=true&model={model}")
            for attempt in range(4):
                try:
                    async with _get_pollinations_lock():
                        resp = await client.get(url)
                    if resp.status_code == 429:
                        await asyncio.sleep(10 * (attempt + 1) + random.uniform(0, 30))
                        continue
                    resp.raise_for_status()
                    ct = resp.headers.get("content-type", "")
                    if not ct.startswith("image/") or len(resp.content) < 1024:
                        break
                    out_path.write_bytes(resp.content)
                    return out_path
                except (httpx.TimeoutException, httpx.NetworkError):
                    await asyncio.sleep(5 * (attempt + 1))
                except httpx.HTTPStatusError:
                    if attempt < 3:
                        await asyncio.sleep(5 * (attempt + 1))
    return None


async def _try_gemini(prompt, out_path, seed, width, height):
    """Gemini 2.5 Flash Image (Nano Banana). Sin key no hace nada."""
    key = _gemini_key()
    if not key:
        return None
    endpoint = ("https://generativelanguage.googleapis.com/v1beta/models/"
                + _GEMINI_MODEL + ":generateContent?key="
                + urllib.parse.quote(key, safe=""))
    aspect = "9:16" if height > width else ("16:9" if width > height else "1:1")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect},
        },
    }).encode("utf-8")
    last = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    endpoint, data=body,
                    headers={"Content-Type": "application/json"})
            if resp.status_code == 429:
                last = f"429 (rate limit), intento {attempt + 1}/3"
                await asyncio.sleep(15 * (attempt + 1))
                continue
            if resp.status_code in (400, 403, 404):
                return None
            resp.raise_for_status()
            data = resp.json()
            parts = (data.get("candidates", [{}])[0]
                         .get("content", {})
                         .get("parts", []))
            b64 = None
            for part in parts:
                if "inlineData" in part:
                    b64 = part["inlineData"].get("data")
                    break
            if not b64 or len(b64) < 1000:
                reason = (data.get("candidates", [{}])[0]
                              .get("finishReason", "sin imagen"))
                last = f"finishReason={reason}"
                await asyncio.sleep(10)
                continue
            out_path.write_bytes(base64.b64decode(b64))
            return out_path
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last = str(e)
            await asyncio.sleep(8 * (attempt + 1))
        except Exception as e:
            last = str(e)
            await asyncio.sleep(8 * (attempt + 1))
    print(f"    Gemini falló: {last}", flush=True)
    return None


async def _try_cloudflare(prompt, out_path, seed, width, height):
    """Cloudflare Workers AI (FLUX.1-schnell / SDXL). Sin credenciales no hace nada.
    Permiso del token: Account -> Workers AI -> Edit."""
    acct, token = _cloudflare_creds()
    if not acct or not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=90.0) as client:
        for model in _CF_MODELS:
            url = ("https://api.cloudflare.com/client/v4/accounts/"
                   + acct + "/ai/run/" + model)
            # FLUX.1-schnell genera tiles 512; SDXL admite hasta 2048 con aspecto propio
            if "stable-diffusion" in model:
                body = {"prompt": prompt, "width": width, "height": height,
                        "num_steps": 25, "seed": seed}
            else:
                # 2026-08-24: la API de schnell ya NO acepta 'seed' (400
                # "additional properties not allowed") — se omite.
                body = {"prompt": prompt, "steps": 4}
            try:
                resp = await client.post(url, json=body, headers=headers)
                if resp.status_code == 429:
                    await asyncio.sleep(30)
                    continue
                if resp.status_code != 200 or len(resp.content) < 1024:
                    continue
                raw = resp.content
                if raw.lstrip().startswith(b"{"):
                    try:
                        b64 = resp.json().get("result", {}).get("image", "")
                    except Exception:
                        b64 = ""
                    if not b64 or len(b64) < 100:
                        continue
                    raw = base64.b64decode(b64)
                if len(raw) < 1024:
                    continue
                out_path.write_bytes(raw)
                return out_path
            except (httpx.TimeoutException, httpx.NetworkError):
                continue
    return None


async def _try_huggingface(prompt, out_path, width, height):
    token = _token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"inputs": prompt, "parameters": {"width": width, "height": height}}
    async with httpx.AsyncClient(timeout=90.0) as client:
        for model in _HF_MODELS:
            url = f"https://router.huggingface.co/hf-inference/models/{model}"
            for attempt in range(2):
                try:
                    resp = await client.post(url, json=body, headers=headers)
                    if resp.status_code == 503:
                        try:
                            wait = json.loads(resp.content).get("estimated_time", 20)
                        except Exception:
                            wait = 20
                        await asyncio.sleep(min(wait, 30))
                        continue
                    if resp.status_code != 200 or len(resp.content) < 1024:
                        break
                    out_path.write_bytes(resp.content)
                    return out_path
                except (httpx.TimeoutException, httpx.NetworkError):
                    break
    return None


async def _try_stable_horde(prompt, out_path, seed, width, height):
    key = os.environ.get("STABLE_HORDE_API_KEY", "")
    w, h = _HORDE_PORTRAIT
    headers = {"apikey": key, "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "params": {
            "width": w, "height": h, "steps": 25,
            "sampler_name": "k_euler_a", "n": 1, "seed": str(seed),
        },
        "models": ["AlbedoBase XL (SDXL)"],
        "r2": False, "shared": False,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://stablehorde.net/api/v2/generate/async",
                json=payload, headers=headers)
            if resp.status_code not in (200, 202):
                return None
            job_id = resp.json().get("id")
            if not job_id:
                return None
            for _ in range(60):
                await asyncio.sleep(5)
                check = await client.get(
                    f"https://stablehorde.net/api/v2/generate/check/{job_id}",
                    headers=headers)
                if check.status_code != 200:
                    continue
                data = check.json()
                if data.get("faulted"):
                    return None
                if not data.get("is_possible", True):
                    return None
                if not data.get("done") and data.get("wait_time", 0) > 180:
                    return None
                if not data.get("done"):
                    continue
                status = await client.get(
                    f"https://stablehorde.net/api/v2/generate/status/{job_id}",
                    headers=headers, timeout=60.0)
                if status.status_code != 200:
                    return None
                gens = status.json().get("generations", [])
                if not gens:
                    return None
                img_b64 = gens[0].get("img", "")
                if not img_b64 or len(img_b64) < 100:
                    return None
                out_path.write_bytes(base64.b64decode(img_b64))
                return out_path
    except Exception:
        return None
    return None


async def _try_together(prompt, out_path, seed, width, height):
    key = os.environ.get("TOGETHER_API_KEY", "")
    if not key:
        return None
    tw, th = 1024, 1792
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "prompt": prompt, "width": tw, "height": th,
        "steps": 4, "n": 1, "seed": seed,
        "response_format": "b64_json",
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.together.xyz/v1/images/generations",
                json=payload, headers=headers)
            if resp.status_code != 200:
                return None
            data = resp.json()
            images = data.get("data", [])
            if not images:
                return None
            b64 = images[0].get("b64_json", "")
            if not b64 or len(b64) < 100:
                return None
            out_path.write_bytes(base64.b64decode(b64))
            return out_path
    except Exception:
        return None


async def _try_freeai(prompt, out_path, seed, width, height):
    """free.ai — SDXL y FLUX.1-schnell gratis, sin key ni signup.
    Max 1024x1024. Devuelve JSON con image_url, hay que descargar."""
    models = ["flux-schnell", "sdxl"]
    async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
        for model in models:
            try:
                resp = await client.post(
                    "https://api.free.ai/v1/image/generate/",
                    json={"prompt": prompt, "model": model},
                    headers={"Content-Type": "application/json"})
                if resp.status_code != 200:
                    continue
                data = resp.json()
                img_url = data.get("image_url", "")
                if not img_url:
                    continue
                img_resp = await client.get(img_url)
                if img_resp.status_code != 200 or len(img_resp.content) < 1024:
                    continue
                out_path.write_bytes(img_resp.content)
                return out_path
            except (httpx.TimeoutException, httpx.NetworkError):
                continue
    return None


async def _generate_async(prompt, out_path, seed, width, height, provider=None):
    providers = [
        _try_pollinations, _try_freeai, _try_gemini, _try_cloudflare,
        _try_huggingface, _try_stable_horde, _try_together,
    ]
    if provider:
        wanted = f"_try_{provider}"
        all_names = ", ".join(fn.__name__.replace("_try_", "")
                              for fn in providers)
        providers = [fn for fn in providers if fn.__name__ == wanted]
        if not providers:
            raise ValueError(
                f"IMG_PROVIDER inválido: {provider} (opciones: {all_names})")
    for fn in providers:
        try:
            result = await fn(prompt, out_path, seed, width, height)
        except Exception:
            result = None
        if result is not None:
            print(f"    imagen OK vía {fn.__name__.replace('_try_', '')} "
                  f"({os.path.getsize(out_path)} B)", flush=True)
            return out_path
        print(f"    {fn.__name__.replace('_try_', '')} falló, siguiente...",
              flush=True)
    return None


def generate(prompt, out_path, aspect=DEFAULT_ASPECT, retries=2, wait=20,
             provider=None, seed=None):
    """Genera una imagen con cascada de proveedores. Devuelve out_path o lanza
    RuntimeError si ninguno responde (el caller cae a Wikimedia Commons).
    provider: nombre del proveedor a forzar (ej. "gemini", "cloudflare", ...);
    también se lee de la env IMG_PROVIDER.
    seed: fijar para consistencia de personaje entre escenas (mismo seed +
    mismo prompt = misma imagen; mismo seed + distinta escena = mismo rostro)."""
    width, height = IMG_WIDTH, IMG_HEIGHT
    if aspect == "16:9":
        width, height = 1920, 1080
    elif aspect == "1:1":
        width, height = 1024, 1024

    provider = provider or os.environ.get("IMG_PROVIDER", "").strip() or None
    last = None
    for attempt in range(retries):
        try:
            s = seed if seed is not None else attempt * 101
            result = asyncio.run(
                _generate_async(prompt, Path(out_path), s, width, height,
                                provider=provider))
            if result is not None and os.path.getsize(out_path) > 5000:
                return out_path
            last = "todos los proveedores fallaron"
        except Exception as e:
            last = str(e)
        if attempt < retries - 1:
            import time
            time.sleep(wait)
    raise RuntimeError(f"HF no generó imagen: {last}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit("uso: flux_img.py 'prompt' [out.jpg]")
    prompt = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/hf_test.jpg"
    print(generate(prompt, out))
