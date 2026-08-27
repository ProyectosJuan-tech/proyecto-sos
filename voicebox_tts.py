#!/usr/bin/env python3
"""Motor TTS alternativo vía Voicebox (local-first, MIT, jamiepine/voicebox).

Usa la API REST local de Voicebox (http://127.0.0.1:17493) para generar voz
con perfiles clonados. Si Voicebox NO está corriendo (o falla), las funciones
devuelven None y el pipeline cae a edge-tts sin tocar nada.

Perfiles: se mapea la voz de edge (es-MX-JorgeNeural, etc.) a un perfil de
Voicebox por nombre. Configurable por entorno:
  VOICEBOX_URL          (default http://127.0.0.1:17493)
  VOICEBOX_TIMEOUT      (segundos, default 600; la primera carga descarga modelo)
  VOICEBOX_PROFILE_<KEY> (ej. VOICEBOX_PROFILE_JORGE=Mentor para forzar el nombre)

Dependencias: solo stdlib (urllib). El post-procesado (deepen + adelay +
loudnorm) lo aplica ffmpeg igual que el pipeline clásico, para que el audio
entre sincronizado al render.

Uso directo:
  python3 voicebox_tts.py 'texto' [out.wav] [NombrePerfil]
"""
import json
import os
import subprocess
import sys
import urllib.request

BASE_URL = os.environ.get("VOICEBOX_URL", "http://127.0.0.1:17493")
TIMEOUT = int(os.environ.get("VOICEBOX_TIMEOUT", "600"))

# edge voice string -> nombre de perfil de Voicebox (ajustar según lo clonado)
DEFAULT_PROFILE_MAP = {
    "es-MX-JorgeNeural": "Jorge",
    "es-AR-ElenaNeural": "Elena",
    "es-MX-DaliaNeural": "Dalia",
}

_cache = {"health": None, "profiles": None}


def _get(path, timeout=5):
    req = urllib.request.Request(BASE_URL + path, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _post(path, body, timeout=TIMEOUT, binary=False):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE_URL + path, data=data, method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    if binary:
        return raw
    return json.loads(raw) if raw else {}


def available():
    """True si Voicebox responde /health. Cacheado por proceso."""
    if _cache["health"] is not None:
        return _cache["health"]
    try:
        h = _get("/health")
        _cache["health"] = h.get("status") == "ok"
    except Exception:
        _cache["health"] = False
    return _cache["health"]


def profiles():
    if _cache["profiles"] is None:
        try:
            _cache["profiles"] = _get("/profiles")
        except Exception:
            _cache["profiles"] = []
    return _cache["profiles"]


def profile_for(edge_voice):
    """Devuelve el profile_id de Voicebox para una voz de edge, o None.

    Permite forzar el nombre por perfil con VOICEBOX_PROFILE_JORGE=<nombre>.
    """
    if not available():
        return None
    key = edge_voice.split("-")[-1].lower() if edge_voice.count("-") >= 2 else edge_voice
    env_name = os.environ.get(f"VOICEBOX_PROFILE_{key.upper()}")
    name = env_name or DEFAULT_PROFILE_MAP.get(edge_voice)
    if not name:
        return None
    for p in profiles():
        if (p.get("name") or "").lower() == name.lower():
            return p.get("id")
    return None


def engine_tag(edge_voice=None):
    """Tag de cache: '_vb' si voicebox activo para esta voz, '' si no."""
    if edge_voice is None:
        return "_vb" if available() else ""
    return "_vb" if profile_for(edge_voice) else ""


def _ffmpeg_chain(raw, out_wav, deepen):
    sr = int(subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "stream=sample_rate",
         "-of", "csv=p=0", raw],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[0])
    new_sr = int(sr * deepen)
    af = (f"asetrate={new_sr},aresample={sr},"
          f"atempo={1/deepen:.3f},"
          f"adelay=150|150,"
          f"loudnorm=I=-16:TP=-1.5:LRA=11")
    subprocess.run(["ffmpeg", "-y", "-i", raw, "-af", af, "-ar", str(sr),
                    out_wav], check=True)
    return out_wav


def synthesize(text, edge_voice, out_wav, deepen=1.0, language="es",
               instruct=None, engine=None):
    """Genera voz clonada vía /generate/stream (WAV síncrono).

    Devuelve out_wav si OK, None si Voicebox no disponible o falla.
    deepen=1.0 por defecto: la voz clonada ya tiene el timbre deseado; se
    mantiene el mismo post-procesado (adelay+loudnorm) que edge-tts.
    """
    if not available():
        return None
    pid = profile_for(edge_voice)
    if not pid:
        return None
    body = {
        "profile_id": pid,
        "text": text,
        "language": language,
        "normalize": True,
    }
    if engine:
        body["engine"] = engine
    if instruct:
        body["instruct"] = instruct
    try:
        wav_bytes = _post("/generate/stream", body, binary=True)
    except Exception:
        return None
    if not wav_bytes:
        return None
    raw = out_wav + ".vb.raw.wav"
    with open(raw, "wb") as f:
        f.write(wav_bytes)
    try:
        _ffmpeg_chain(raw, out_wav, deepen)
    finally:
        if os.path.exists(raw):
            os.remove(raw)
    return out_wav


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    text = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/voicebox_out.wav"
    name = sys.argv[3] if len(sys.argv) > 3 else None
    if not available():
        print("Voicebox no está corriendo en", BASE_URL)
        sys.exit(2)
    edge = "es-MX-JorgeNeural"
    if name:
        DEFAULT_PROFILE_MAP[edge] = name
    res = synthesize(text, edge, out, deepen=1.0)
    if not res:
        print("Falló la generación (¿existe el perfil en Voicebox?)")
        sys.exit(3)
    print("OK", res)
