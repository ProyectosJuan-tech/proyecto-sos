#!/usr/bin/env python3
"""B-roll vertical desde Pexels API. Adaptado de freefaceless/FreeFaceless (MIT).

Clave: env PEXELS_API_KEY o archivo pexels_key.txt en the project root.
Gratis sin tarjeta (200 req/h). Si no hay clave, las funciones devuelven None
y el pipeline cae al fallback siguiente (Wikimedia Commons).
"""
import hashlib
import json
import os
import time
from pathlib import Path

import httpx

import consumption

_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pexels_key.txt")
_API_VIDEO = "https://api.pexels.com/videos/search"
_API_PHOTO = "https://api.pexels.com/v1/search"

# ─────────────────────────────────────────────
# Config de caché y límites (overridable por env para tests)
# ─────────────────────────────────────────────
_CACHE_DIR = os.environ.get(
    "PEXELS_CACHE_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"),
)
_CACHE_FILE = os.path.join(_CACHE_DIR, "pexels_cache.json")
_CACHE_TTL = int(os.environ.get("PEXELS_CACHE_TTL", str(12 * 3600)))  # 12h
_CACHE_MAX_ENTRIES = int(os.environ.get("PEXELS_CACHE_MAX", "500"))
_MAX_RETRIES = int(os.environ.get("PEXELS_MAX_RETRIES", "2"))  # reintentos transitorios
_BACKOFF_BASE = float(os.environ.get("PEXELS_BACKOFF_BASE", "1.5"))


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


# Legacy alias para compatibilidad con callers existentes
API = _API_VIDEO


# ─────────────────────────────────────────────
# Caché local (query + tipo de medio + orientación)
# ─────────────────────────────────────────────
def _cache_load() -> dict:
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _cache_save(data: dict) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_CACHE_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError:
        pass  # caché best-effort: nunca romper por no poder escribir


def _cache_lookup(cache_key: str) -> list | None:
    data = _cache_load()
    entry = data.get(cache_key)
    if not entry:
        consumption.incr("pexels.cache_misses")
        return None
    ts = entry.get("ts", 0)
    if time.time() - ts > _CACHE_TTL:
        consumption.incr("pexels.cache_misses")
        return None
    consumption.incr("pexels.cache_hits")
    return entry.get("results")


def _cache_store(cache_key: str, results: list) -> None:
    data = _cache_load()
    data[cache_key] = {"ts": time.time(), "results": results}
    # Límite de entradas (FIFO simple): no deja crecer el archivo indefinidamente
    if len(data) > _CACHE_MAX_ENTRIES:
        oldest = sorted(data, key=lambda k: data[k].get("ts", 0))
        for k in oldest[: len(data) - _CACHE_MAX_ENTRIES]:
            data.pop(k, None)
    _cache_save(data)


def _cache_key(kind: str, orientation: str, query: str) -> str:
    raw = f"{kind}|{orientation}|{query.strip().lower()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def _cache_clear() -> None:
    """Borra el caché (para regenerar desde cero, tests, o limpieza)."""
    try:
        if os.path.exists(_CACHE_FILE):
            os.remove(_CACHE_FILE)
    except OSError:
        pass


# ─────────────────────────────────────────────
# HTTP layer con clasificación de estados + retries/backoff acotados
# ─────────────────────────────────────────────
def _http_get_json(url: str, params: dict, key: str) -> dict | None:
    """GET a la API de Pexels con:
      - clasificación de respuesta: 200 / vacía / 404 / 429 / 5xx / timeout
      - reintentos acotados + backoff para 429 y transitorios (5xx/red)
      - 404 / endpoint inválido → no insiste, retorna None (fallback)
    Devuelve el JSON parseado (dict) o None.
    """
    headers = {"Authorization": key}
    for attempt in range(_MAX_RETRIES + 1):
        try:
            r = httpx.get(url, headers=headers, params=params, timeout=30)
            consumption.incr("pexels.http_requests")
            if r.status_code == 200:
                data = r.json()
                if data is None:
                    return None
                return data
            if r.status_code == 404:
                # endpoint inválido / deprecado: NO insistir, pasar a fallback
                consumption.incr("pexels.errors")
                return None
            if r.status_code == 429:
                consumption.incr("pexels.429")
            elif 500 <= r.status_code < 600:
                consumption.incr("pexels.errors")
            # resto (400, 403, 401, 422...) → no reintentar, fallback
            else:
                consumption.incr("pexels.errors")
                return None
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError):
            consumption.incr("pexels.errors")
            consumption.incr("pexels.retries")
        except Exception:  # noqa: BLE001 — respuesta imprevisible
            consumption.incr("pexels.errors")
            return None

        # reintentar SOLO en los transitorios con backoff acotado
        if attempt < _MAX_RETRIES:
            if r and r.status_code in (429,):
                consumption.incr("pexels.retries")
            time.sleep(_BACKOFF_BASE * (attempt + 1))
    return None


def _get_results(kind: str, url: str, params: dict, orientation: str,
                 query: str, process) -> list:
    """Búsqueda con caché + HTTP. `process(data_json) -> list[dict]`.

    Flujo: ¿caché? → sí: reutilizar; no: consultar Pexels → guardar.
    Devuelve lista (puede ser vacía).
    """
    ck = _cache_key(kind, orientation, query)
    cached = _cache_lookup(ck)
    if cached is not None:
        return cached

    consumption.incr("pexels.queries")
    key = _key()
    if not key:
        return []
    data = _http_get_json(url, params, key)
    if data is None:
        return []
    results = process(data)
    _cache_store(ck, results)
    return results


def _process_videos(data: dict) -> list:
    return [v for v in data.get("videos", [])
            if not _menciona_menor(
                " ".join([
                    v.get("url", "") or "",
                    (v.get("user") or {}).get("name", "") or "",
                ]))]


def _process_photos(data: dict) -> list:
    return [p for p in data.get("photos", [])
            if not _menciona_menor(
                " ".join([
                    p.get("alt", "") or "",
                    p.get("photographer", "") or "",
                ]))]


# Palabras (es/en) que delatan presencia de menores de edad. Si un resultado
# de Pexels las menciona en su alt/nombre/url, se descarta para NO mostrar
# niños/as ni adolescentes en los videos del canal.
_MENOR_TERMS = (
    "niñ", "niños", "niñas", "niño", "niña", "infancia", "infante",
    "bebé", "bebe", "bebes", "menor", "menores", "adolescente",
    "child", "children", "kid", "kids", "baby", "babies", "newborn",
    "toddler", "boy", "boys", "girl", "girls", "teen", "teens",
    "teenager", "teenagers", "adolescent",
)


def _menciona_menor(texto: str) -> bool:
    """True si el texto (alt/url/nombre de un recurso Pexels) alude a menores."""
    if not texto:
        return False
    t = texto.lower()
    return any(term in t for term in _MENOR_TERMS)

def search_vertical(query, min_duration=3.0):
    """Devuelve URL del mejor video vertical (>=1080w) o None.

    El caché lo maneja _get_results (por query+orientación): aquí solo se filtra
    el resultado, sin keys duplicadas que rompan la contabilidad de consumo.
    """
    params = {"query": query, "orientation": "portrait", "per_page": 15}
    videos = _get_results("video", _API_VIDEO, params, "portrait", query,
                          _process_videos)
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


def _landscape_ok(v):
    """¿El video v (dict de Pexels) tiene un archivo horizontal >=1920w?"""
    for f in v.get("video_files", []):
        if f.get("width", 0) >= 1920 and f.get("height", 0) <= f.get("width", 0):
            return True
    return False


def search_landscape(query, min_duration=3.0):
    """Devuelve URL del mejor video horizontal 16:9 (>=1920w) o None."""
    params = {"query": query, "orientation": "landscape", "per_page": 15}
    videos = _get_results("video", _API_VIDEO, params, "landscape", query,
                          _process_videos)
    for v in videos:
        if v.get("duration", 0) < min_duration or not _landscape_ok(v):
            continue
        url = _best_landscape_url(v)
        if url:
            return url
    return None


def _best_landscape_url(v):
    files = [f for f in v["video_files"]
             if f.get("width", 0) >= 1920 and f.get("height", 0) <= f.get("width", 0)]
    if not files:
        return None
    files.sort(key=lambda f: f.get("width", 0), reverse=True)
    return files[0]["link"]


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


def fetch_for_scene_landscape(query, out_path, min_duration=3.0,
                              fallback_query="abstract landscape"):
    """Descarga un b-roll horizontal 16:9 para una escena. Devuelve Path o None.

    min_duration: duración mínima (s) que debe tener el clip para que no haga
    "salto" (loop brusco) si la escena es más larga que el clip.
    """
    url = search_landscape(query, min_duration=min_duration)
    if url is None:
        url = search_landscape(fallback_query, min_duration=min_duration)
    if url is None:
        return None
    try:
        return download(url, out_path)
    except Exception:
        return None


def search_videos_raw(query, orientation="portrait", per_page=15, min_duration=3.0):
    """Devuelve lista de dicts con metadata de videos de Pexels.

    Cada dict contiene:
        id, url, duration, width, height, orientation, fps,
        file_size, thumbnail, quality, source

    No filtra por orientación — devuelve todos y el caller decide.
    Devuelve lista vacía si no hay clave o hay error.
    """
    params = {"query": query, "per_page": per_page}
    videos = _get_results("video", _API_VIDEO, params, "any", query,
                          _process_videos)
    results = []
    for v in videos:
        if v.get("duration", 0) < min_duration:
            continue
        v_width = v.get("width", 0)
        v_height = v.get("height", 0)
        v_orientation = "portrait" if v_height > v_width else (
            "landscape" if v_width > v_height else "square"
        )
        # Seleccionar el mejor archivo de video
        files = v.get("video_files", [])
        if not files:
            continue
        # Preferir HD
        hd_files = [f for f in files if f.get("quality") == "hd"]
        best_files = hd_files if hd_files else files
        best = max(best_files, key=lambda f: f.get("height", 0))

        results.append({
            "id": v.get("id"),
            "url": best.get("link", ""),
            "duration": v.get("duration", 0),
            "width": best.get("width", 0),
            "height": best.get("height", 0),
            "orientation": v_orientation,
            "fps": best.get("fps", 0),
            "file_size": best.get("size", 0),
            "thumbnail": v.get("image", ""),
            "quality": best.get("quality", ""),
            "source": "pexels",
        })
    return results


# ─────────────────────────────────────────────
# FOTOS Stock de Pexels (PHOTO_STOCK) — API de Fotos (`/v1/search`)
# OJO 2026-08-28: `/v1/photos/search` devolvía 404 (endpoint deprecado). El
# endpoint actual de búsqueda de fotos es `/v1/search`.
# ─────────────────────────────────────────────
_PHOTO_API = "https://api.pexels.com/v1/search"


def _photo_orientation_param(orientation: str | None) -> tuple[str, str | None]:
    """Devuelve (cache_orientation, api_orientation)."""
    if orientation == "portrait":
        return "portrait", "portrait"
    if orientation == "landscape":
        return "landscape", "landscape"
    return "any", None


def search_photos_raw(query: str, orientation: str | None = None,
                      per_page: int = 15) -> list[dict]:
    """Lista de fotos de Pexels con metadata (id, url, width, height, alt).

    orientation: "portrait" | "landscape" | None (cualquiera).
    Devuelve [] si no hay clave o hay error.
    """
    cache_orient, api_orient = _photo_orientation_param(orientation)
    params = {"query": query, "per_page": per_page}
    if api_orient:
        params["orientation"] = api_orient
    photos = _get_results("photo", _PHOTO_API, params, cache_orient, query,
                          _process_photos)
    out = []
    for p in photos:
        w, h = p.get("width", 0), p.get("height", 0)
        o = ("portrait" if h > w else "landscape" if w > h else "square")
        url = p.get("src", {}).get("large2x") or p.get("src", {}).get("original")
        if not url:
            continue
        out.append({
            "id": p.get("id"),
            "url": url,
            "width": w or 0,
            "height": h or 0,
            "orientation": o,
            "alt": p.get("alt") or "",
            "photographer": p.get("photographer") or "",
            "source": "pexels_photo",
        })
    return out


def search_photo(query: str, orientation: str | None = None,
                 min_w: int = 1080) -> str | None:
    """URL de la mejor foto de Pexels (>=min_w en su lado menor)."""
    for cand in search_photos_raw(query, orientation=orientation, per_page=20):
        w, h = cand["width"], cand["height"]
        if min(w, h) < min_w:
            continue
        if orientation == "portrait" and cand["orientation"] != "portrait":
            continue
        if orientation == "landscape" and cand["orientation"] != "landscape":
            continue
        return cand["url"]
    return None


def fetch_photo_for_scene(query: str, out_path, *,
                          orientation: str | None = None,
                          fallback_query: str = "cozy home sunlight") -> str | None:
    """Descarga una foto de Pexels para la escena. Devuelve Path o None."""
    url = search_photo(query, orientation=orientation)
    if url is None:
        url = search_photo(fallback_query, orientation=orientation)
    if url is None:
        return None
    try:
        return str(download(url, out_path))
    except Exception:
        return None


if __name__ == "__main__":
    import sys
    print("Pexels:", "OK" if available() else "SIN CLAVE (pexels_key.txt)")
    if available():
        print(search_vertical(sys.argv[1] if len(sys.argv) > 1 else "coffee"))