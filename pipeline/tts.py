import os
import re
import subprocess
import numpy as np
import zlib

try:
    import edge_tts
except Exception:  # pragma: no cover
    edge_tts = None

DEEPEN = 0.92
PAUSE_RE = re.compile(r"\[(\d+)\]")


def norm(s):
    s = s.lower().replace("¿", "").replace("¡", "")
    s = re.sub(r"[^a-z0-9áéíóúüñ ]", "", s)
    return " ".join(s.split())


def has_pauses(text):
    """True si el texto contiene marcas de pausa [ms]."""
    return bool(PAUSE_RE.search(text or ""))


def split_pauses(text):
    """Divide un texto con marcas [ms] en frases con pausa después de cada una."""
    clean = PAUSE_RE.sub("", text or "")
    if not has_pauses(text):
        return False, [(text.strip(), 0)], clean
    parts = PAUSE_RE.split(text)
    chunks = []
    for k in range(0, len(parts) - 1, 2):
        frase = (parts[k] or "").strip()
        if frase:
            chunks.append((frase, int(parts[k + 1])))
    last = (parts[-1] or "").strip()
    if last:
        chunks.append((last, 0))
    chunks = [(f, p) for f, p in chunks if f]
    return True, chunks, clean.strip()


def probe_duration(path):
    if not os.path.exists(path):
        return 0.0
    try:
        out = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", path
        ], capture_output=True, text=True, check=True).stdout.strip()
        return float(out) if out else 0.0
    except Exception:
        return 0.0


def _decode_pcm(wav, sr):
    raw = subprocess.run(
        ["ffmpeg", "-v", "quiet", "-i", wav, "-f", "s16le", "-ac", "1",
         "-ar", str(sr), "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _trim_tail(pcm, sr, hold_ms=90, thr=0.008):
    keep = int(sr * hold_ms / 1000)
    if len(pcm) <= keep:
        return pcm
    i = len(pcm) - 1
    while i >= keep and abs(pcm[i]) < thr:
        i -= 1
    return pcm[: i + keep]


async def _tts_audio_paused(text, voice, out_wav, deepen=DEEPEN, rate="+0%"):
    """Sintetiza frase por frase e intercala silencio exacto entre ellas."""
    _, chunks, _ = split_pauses(text)
    sr = 24000
    parts = []
    for frase, _p in chunks:
        t = f"__part_{len(parts)}.mp3"
        if edge_tts is None:
            raise RuntimeError("edge_tts no disponible")
        await edge_tts.Communicate(frase, voice, rate=rate).save(t)
        parts.append(_trim_tail(_decode_pcm(t, sr), sr))
        os.remove(t)
    total = sum(len(p) for p in parts) + sum(
        int(p * sr / 1000) for _f, p in chunks[:-1]
    )
    buf = np.zeros(total, dtype=np.float32)
    pos = 0
    for i, pcm in enumerate(parts):
        buf[pos:pos + len(pcm)] = pcm
        pos += len(pcm)
        if i < len(parts) - 1:
            gap = int(chunks[i][1] * sr / 1000)
            pos += gap
    pcm16 = (np.clip(buf, -1, 1) * 32767).astype(np.int16)
    raw = out_wav + ".raw.pcm"
    pcm16.tofile(raw)
    new_sr = int(sr * deepen)
    af = (
        f"asetrate={new_sr},aresample={sr},"
        f"atempo={1/deepen:.3f},"
        f"adelay=150|150,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    subprocess.run([
        "ffmpeg", "-y", "-f", "s16le", "-ar", str(sr), "-ac", "1",
        "-i", raw, "-af", af, "-ar", str(sr), out_wav
    ], check=True, capture_output=True)
    os.remove(raw)
    return out_wav


async def tts_audio(text, voice, out_wav, deepen=DEEPEN, rate="+0%", engine=None):
    """Genera audio. Si engine es 'voicebox' (o None con voicebox activo), usa Voicebox primero."""
    if engine != "edge":
        try:
            import voicebox_tts
            res = voicebox_tts.synthesize(text, voice, out_wav, deepen=deepen)
            if res:
                return out_wav
        except Exception as e:
            print(f"  [voicebox] falló, uso edge-tts: {e}", flush=True)
    if has_pauses(text):
        return await _tts_audio_paused(text, voice, out_wav, deepen=deepen, rate=rate)
    if edge_tts is None:
        raise RuntimeError("edge_tts no disponible")
    raw = out_wav + ".raw.mp3"
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(raw)
    sr = int(subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "stream=sample_rate",
         "-of", "csv=p=0", raw],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[0])
    new_sr = int(sr * deepen)
    af = (
        f"asetrate={new_sr},aresample={sr},"
        f"atempo={1/deepen:.3f},"
        f"adelay=150|150,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    subprocess.run(["ffmpeg", "-y", "-i", raw, "-af", af, "-ar", str(sr), out_wav],
                   check=True, capture_output=True)
    os.remove(raw)
    return out_wav


def align_words(text, wav):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav, language="es", word_timestamps=True, vad_filter=True)
    ws = []
    for seg in segments:
        for w in seg.words:
            ws.append((w.start, w.end, w.word))
    if not ws:
        return None

    toks = text.split()
    mine = [norm(t) for t in toks]
    out = []
    wi = 0
    for start, end, wtext in ws:
        if wi >= len(toks):
            break
        tn = norm(wtext)
        if mine[wi] == tn:
            out.append((toks[wi], start, end))
            wi += 1
            continue
        found = None
        for j in range(wi, min(wi + 3, len(toks))):
            if mine[j] == tn:
                found = j
                break
        if found is not None:
            for k in range(wi, found):
                out.append((toks[k], start, end))
            out.append((toks[found], start, end))
            wi = found + 1
        else:
            out.append((toks[wi], start, end))
            wi += 1
    if len(out) < len(toks):
        last_t = out[-1][2] if out else 0.0
        for k in range(len(out), len(toks)):
            out.append((toks[k], last_t, last_t + 0.2))
    return out


def rate_suffix(rate):
    if not rate or rate == "+0%":
        return ""
    return "_r" + rate.replace("%", "").replace("+", "p").replace("-", "m")


def deepen_suffix(deepen):
    if not deepen or abs(deepen - 0.92) < 0.01:
        return ""
    return "_d" + str(int(round(deepen * 100)))


def mix_boom(wav):
    out = wav + ".boom.wav"
    if os.path.exists(out):
        return out
    boom = os.path.join(os.path.dirname(wav), "_boom_synth.wav")
    sr = int(subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "stream=sample_rate",
        "-of", "csv=p=0", wav
    ], capture_output=True, text=True, check=True).stdout.strip().splitlines()[0])
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=60:duration=0.6:sample_rate={sr}",
        "-af", "volume=0.85,afade=t=out:st=0.08:d=0.52,adelay=120|120",
        "-t", "0.8", "-ar", str(sr), "-ac", "1", boom,
    ], check=True, capture_output=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", wav, "-i", boom,
        "-filter_complex",
        "[0:a]volume=1.0[a];[1:a]volume=0.55[b];[a][b]amix=inputs=2:duration=first:dropout_transition=0,limiter=limit=0.95",
        "-ar", str(sr), "-ac", "1", out,
    ], check=True, capture_output=True)
    os.remove(boom)
    return out


def build_tts_cache_key(text, rate, deepen):
    """Cache key equivalente al naming actual del pipeline legacy."""
    return f"{rate_suffix(rate)}{deepen_suffix(deepen)}_{zlib.crc32((text or '').encode())}"
