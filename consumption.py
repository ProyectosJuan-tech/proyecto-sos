"""
consumption.py — Contabilidad de consumo de proveedores externos.

Objetivo: saber cuánto consumo externo hubo en una producción, sin inventar
métricas. Expone un registro simple en memoria + un snapshot a JSON al final,
para que el driver de producción lo incluya en el informe.

Estructura de contadores (cada uno empieza en 0 y se incrementa con incr()):

  pexels.queries          → búsquedas (semánticas) ejecutadas
  pexels.http_requests    → llamadas HTTP reales a la API de Pexels
  pexels.cache_hits       → búsquedas resueltas desde el caché local (sin HTTP)
  pexels.cache_misses     → búsquedas que requirieron HTTP (no estaban en caché)
  pexels.429              → respuestas 429
  pexels.errors           → errores (5xx / red / parse)
  pexels.retries          → reintentos por 429/transitorio

  ai_image.requests       → generaciones de imagen solicitadas (cascada)
  ai_image.cache_hits     → reutilizadas desde el caché local por hash
  ai_image.cache_misses   → no estaban en caché (se generaron)
  ai_image.regenerations  → regeneraciones (nuevo intento tras un FALLBACK/REGENERATE)

  video_stock.requests    → descargas/solicitudes de b-roll de video
  video_stock.cache_hits  → reutilizadas desde caché/disco sin descargar

  vision.requests         → llamadas a modelos de visión
  vision.éxitos           → respuestas de visión válidas
  vision.fallos_por_cuota → fallos por cuota (402/429/rate-limit)

Nota: si una métrica no puede conocerse en un punto del pipeline, simplemente no
se incrementa y en el informe aparece como "No disponible" (el driver decide).
"""

import json
import os
import threading
from collections import Counter

_COUNTERS: Counter = Counter()
_LOCK = threading.Lock()


def incr(key: str, amount: int = 1) -> None:
    """Incrementa un contador de consumo de forma thread-safe."""
    with _LOCK:
        _COUNTERS[key] += amount


def get(key: str) -> int:
    with _LOCK:
        return int(_COUNTERS.get(key, 0))


def total(prefix: str) -> int:
    """Suma todos los contadores cuyo nombre empieza por `prefix`."""
    with _LOCK:
        return sum(v for k, v in _COUNTERS.items() if k.startswith(prefix))


def snapshot() -> dict:
    """Devuelve un dict JSON-serializable con todo el consumo registrado."""
    return dict(sorted(_COUNTERS.items()))


def reset() -> None:
    with _LOCK:
        _COUNTERS.clear()


def get_minimal_report() -> dict:
    """Devuelve el bloque de consumo en el formato que pide el informe."""
    return {
        "PEXELS": {
            "queries realizadas": get("pexels.queries"),
            "HTTP requests": get("pexels.http_requests"),
            "cache hits": get("pexels.cache_hits"),
            "cache misses": get("pexels.cache_misses"),
            "429": get("pexels.429"),
            "errores": get("pexels.errors"),
            "reintentos": get("pexels.retries"),
        },
        "AI IMAGE": {
            "generation requests": get("ai_image.requests"),
            "cache hits": get("ai_image.cache_hits"),
            "cache misses": get("ai_image.cache_misses"),
            "regenerations": get("ai_image.regenerations"),
        },
        "VIDEO STOCK": {
            "requests": get("video_stock.requests"),
            "cache hits": get("video_stock.cache_hits"),
        },
        "VISION": {
            "requests": get("vision.requests"),
            "éxitos": get("vision.ok"),
            "fallos por cuota": get("vision.quota_fail"),
        },
    }


def dump_to_file(path: str) -> None:
    """Guarda el snapshot completo en un JSON (para inspección)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump({"consumption": snapshot()}, f, ensure_ascii=False, indent=2)
