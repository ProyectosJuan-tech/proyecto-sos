#!/usr/bin/env python3
import asyncio
import json
import math
import os
import re
import subprocess
import urllib.parse
import urllib.request
import zlib

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
import edge_tts


def strip_img_metadata(path):
    """Quita todo metadata (EXIF, GPS, cámara, comment) de una imagen. Sobreescribe el archivo."""
    try:
        img = Image.open(path)
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        if path.endswith((".jpg", ".jpeg")):
            clean.save(path, "JPEG", quality=95)
        elif path.endswith(".png"):
            clean.save(path, "PNG")
        elif path.endswith(".webp"):
            clean.save(path, "WEBP")
        else:
            clean.save(path, quality=95)
        return path
    except Exception:
        return path


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(PROJECT_ROOT, "videos", "largo")
IMGDIR = os.path.join(BASE, "imgs")
AUDDIR = os.path.join(BASE, "audio")
OUTDIR = os.path.join(BASE, "out")
TMP = os.path.join(BASE, "tmp")
for d in (IMGDIR, AUDDIR, OUTDIR, TMP):
    os.makedirs(d, exist_ok=True)

FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_HEAVY = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_SERIF = "/usr/share/fonts/truetype/msttcorefonts/Georgia.ttf"
FONT_SERIF_HEART = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
W, H = 1080, 1920
FPS = 30
PAD_BEFORE, PAD_AFTER = 0.45, 0.7
DEEPEN = 0.92
ACCENT = (227, 179, 65)
MASTER = (18, "slow", "film")
TEXT_PAD_X = 40
TEXT_PAD_Y = 20
TEXT_BG_ALPHA = 140
TEXT_SCHEMES = {
    "dark": {"accent": (227, 179, 65), "main": (255, 255, 255),
             "dim": (185, 189, 196), "shadow": (0, 0, 0)},
    "light": {"accent": (198, 118, 16), "main": (38, 38, 38),
              "dim": (150, 150, 150), "shadow": (255, 255, 255)},
}
_model = None


# ── Karaoke style markers: {y}yellow {b}bold {big}bigger {yb}yellow+bold ──
_KARAOKE_STYLE_RE = re.compile(r"\{(/?)(y|big|b|yb)\}")
_YELLOW = (255, 215, 0)
_BIG_SCALE = 1.35


def parse_karaoke_styles(marked_text):
    """Parse style markers from text.
    Returns (clean_text, clean_styles, line_breaks) where:
    - clean_text: plain text for TTS/alignment (no markers, no \\n)
    - clean_styles: list parallel to words, each is {} or {color/big/heavy}
    - line_breaks: set of word indices where a forced line break occurs"""
    active = set()
    words = []
    styles = []
    line_breaks = set()
    word_idx = 0
    i = 0
    while i < len(marked_text):
        m = _KARAOKE_STYLE_RE.match(marked_text, i)
        if m:
            if m.group(1) == "/":
                active.discard(m.group(2))
            else:
                active.add(m.group(2))
            i = m.end()
        elif marked_text[i] == '\n':
            if words:
                line_breaks.add(word_idx - 1)
            i += 1
        elif marked_text[i] == ' ':
            i += 1
        else:
            j = i
            while j < len(marked_text) and marked_text[j] not in (' ', '\n') and not _KARAOKE_STYLE_RE.match(marked_text, j):
                j += 1
            word = marked_text[i:j]
            style = {}
            if "y" in active or "yb" in active:
                style["color"] = _YELLOW
            if "big" in active or "yb" in active:
                style["big"] = True
            if "b" in active or "yb" in active:
                style["heavy"] = True
            # Attach trailing punctuation to previous word
            if words and not word[0].isalpha() and not word[0] in '¿¡':
                words[-1] += word
            else:
                words.append(word)
                styles.append(style)
                word_idx += 1
            i = j
    return " ".join(words), styles, line_breaks


# ── HTML <strong> parser para énfasis en karaoke ──
_HTML_TAG_RE = re.compile(r"<(/?)(strong|em|b|i)>")

def parse_html_emphasis(marked_text):
    """Parse HTML emphasis tags (<strong>, <em>, <b>, <i>).

    Returns (clean_text, emphasis_map) where:
    - clean_text: plain text without HTML tags
    - emphasis_map: dict {word_index: level} where level is:
        "strong" for <strong>/<b>, "em" for <em>/<i>

    The TTS gets clean_text; the karaoke renderer uses emphasis_map
    to apply visual treatment (scale, glow, color) to emphasized words.
    """
    level_stack = []
    emphasis_map = {}
    clean_parts = []
    word_idx = 0
    i = 0
    while i < len(marked_text):
        m = _HTML_TAG_RE.match(marked_text, i)
        if m:
            is_close = m.group(1) == "/"
            tag = m.group(2)
            level = "strong" if tag in ("strong", "b") else "em"
            if is_close:
                if level_stack and level_stack[-1] == level:
                    level_stack.pop()
            else:
                level_stack.append(level)
            i = m.end()
        elif marked_text[i] in (' ', '\n', '\t'):
            clean_parts.append(" ")
            i += 1
        else:
            j = i
            while j < len(marked_text) and marked_text[j] not in (' ', '\n', '\t') and not _HTML_TAG_RE.match(marked_text, j):
                j += 1
            word = marked_text[i:j]
            clean_parts.append(word)
            if level_stack:
                emphasis_map[word_idx] = level_stack[-1]
            word_idx += 1
            i = j
    clean_text = "".join(clean_parts).strip()
    clean_text = re.sub(r"  +", " ", clean_text)
    return clean_text, emphasis_map


def parse_serif_text(raw):
    """Texto para modo serif: párrafos separados por \\n\\n, líneas por \\n,
    palabras doradas con {y}...{/y}.
    Devuelve (plain_text, struct) donde struct = [[[(word, gold), ...], ...], ...]
    (lista de párrafos > líneas > palabras)."""
    plain_parts = []
    struct = []
    for para_raw in raw.split("\n\n"):
        para = []
        pwords = []
        for line_raw in para_raw.split("\n"):
            words = []
            active_gold = False
            spaced = re.sub(r"(\{/?y\})", r" \1 ", line_raw)
            tokens = spaced.split()
            for tok in tokens:
                if tok == "{y}":
                    active_gold = True
                elif tok == "{/y}":
                    active_gold = False
                elif words and not tok[0].isalpha() and tok[0] not in "¿¡":
                    words[-1] = (words[-1][0] + tok, words[-1][1])
                    pwords[-1] += tok
                else:
                    words.append((tok, active_gold))
                    pwords.append(tok)
            if words:
                para.append(words)
        if para:
            struct.append(para)
            plain_parts.append(" ".join(pwords))
    return " ".join(plain_parts), struct


VOICES = {"male": "es-MX-JorgeNeural", "female": "es-MX-DaliaNeural"}

SCENES = [
    {"file": "File:Plato by Leonidas Drosis on May 7, 2022.jpg",
     "text": "Hace más de dos mil años, Platón escribió uno de los relatos más poderosos de la historia: el mito de la caverna."},
    {"file": "File:An Illustration of The Allegory of the Cave, from Plato’s Republic.jpg",
     "text": "Imagina hombres encadenados desde su nacimiento, mirando fijamente una pared. Nunca han visto el mundo real. Solo sombras proyectadas por un fuego detrás de ellos."},
    {"file": "File:Platon Cave Sanraedam 1604.jpg",
     "text": "Ellos creen que esas sombras son toda la realidad. Porque es lo único que han conocido."},
    {"q": "city lights night",
     "text": "Ese es el truco de la caverna: no saber que estás atado. Hoy, esa caverna tiene otro nombre: el algoritmo."},
    {"q": "smartphone hand screen",
     "text": "Te muestra lo que otros eligieron que veas. Te entretiene, te asusta, te distrae. Y tú llamas realidad a esa pared."},
    {"file": "File:Silhouette of man exiting cave.jpg",
     "text": "Salir no es fácil. Duele. La luz lastima los ojos acostumbrados a la oscuridad."},
    {"q": "sunrise landscape",
     "text": "Pero el que sale ve el sol. Ve el mundo tal como es, no como se lo contaron. Y regresa para despertar a los demás."},
    {"draw": "walk",
     "text": "Tal vez aún estás encadenado. O tal vez ya caminas hacia la luz. De ti depende: seguir mirando sombras, o dar el paso."},
    {"q": "sunrise mountain",
     "text": "Deja de perseguir las sombras que otros proyectan en la pared. La verdad está afuera, pero solo se alcanza caminando."},
]


def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def generate_bgm(out_path, duration=300):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        return out_path
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=138.59:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=164.81:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}",
        "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.008:duration={duration}",
        "-filter_complex",
        "[0]volume=0.05,tremolo=f=0.15:d=0.5[a];"
        "[1]volume=0.04,tremolo=f=0.11:d=0.5[b];"
        "[2]volume=0.035,tremolo=f=0.19:d=0.5[c];"
        "[3]volume=0.03,tremolo=f=0.13:d=0.5[d];"
        "[4]lowpass=f=600[e];"
        "[a][b][c][d][e]amix=inputs=5:normalize=0,lowpass=f=900,"
        f"afade=t=in:st=0:d=3,afade=t=out:st={duration - 3}:d=3",
        "-ar", "24000", "-ac", "1", out_path,
    ]
    run(cmd)
    return out_path


def mix_bgm(video_in, bgm_path, out_path, volume=0.4):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_in,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex",
        f"[1:a]volume={volume}[bgm];"
        "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-movflags", "+faststart", out_path,
    ]
    run(cmd)
    return out_path


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def norm(s):
    return re.sub(r"[^a-záéíóúüñ0-9]", "", s.lower())


def commons_url(params):
    url = ("https://commons.wikimedia.org/w/api.php?action=query" + params +
           "&prop=imageinfo&iiprop=url|size&iiurlwidth=1080&format=json")
    req = urllib.request.Request(url, headers={"User-Agent": "video-builder/1.0"})
    d = json.load(urllib.request.urlopen(req, timeout=40))
    cands = []
    for p in d.get("query", {}).get("pages", {}).values():
        ii = p.get("imageinfo", [{}])[0]
        u = ii.get("thumburl") or ii.get("url")
        w, h = ii.get("width") or 0, ii.get("height") or 0
        if u and w >= 700:
            cands.append((w * h, u))
    cands.sort(reverse=True)
    return cands[0][1] if cands else None


def download_image(scene, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        return out_path
    if "file" in scene:
        u = commons_url("&titles=" + urllib.parse.quote(scene["file"]))
        if u is None:
            raise RuntimeError(f"no existe el archivo: {scene['file']}")
    else:
        u = commons_url(
            "&generator=search"
            "&gsrsearch=" + urllib.parse.quote("filetype:bitmap " + scene["q"]) +
            "&gsrlimit=8&gsrnamespace=6")
        if u is None:
            raise RuntimeError(f"sin imagen para {scene['q']}")
    run(["curl", "-s", "-o", out_path, "-L", "--max-time", "60", u])
    if os.path.getsize(out_path) < 5000:
        raise RuntimeError(f"imagen muy chica: {scene}")
    return out_path


def tts_engine_tag(voice):
    """Tag de cache según motor activo: '_vb' (Voicebox) o '' (edge-tts).

    El nombre del wav incluye el tag para que edge-tts y Voicebox nunca
    compartan cache aunque el texto sea el mismo.
    """
    try:
        import voicebox_tts
        return voicebox_tts.engine_tag(voice)
    except Exception:
        return ""


async def tts_audio(text, voice, out_wav, deepen=DEEPEN, rate="+0%",
                    engine=None):
    """Genera audio. Si engine es 'voicebox' (o None con voicebox activo),
    intenta Voicebox primero y cae a edge-tts si no está disponible o falla.
    """
    if engine != "edge":
        try:
            import voicebox_tts
            res = voicebox_tts.synthesize(text, voice, out_wav, deepen=deepen)
            if res:
                return out_wav
        except Exception as e:
            print(f"  [voicebox] falló, uso edge-tts: {e}", flush=True)
    raw = out_wav + ".raw.mp3"
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(raw)
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
    run(["ffmpeg", "-y", "-i", raw, "-af", af, "-ar", str(sr), out_wav])
    os.remove(raw)
    return out_wav


def align_words(text, wav):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(wav, language="es", word_timestamps=True,
                                    vad_filter=True)
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


def make_walking(out_path):
    img = Image.new("RGB", (W, H))
    px = img.load()
    horizon = int(H * 0.62)
    sky_top = (14, 16, 40)
    sky_hor = (232, 128, 42)
    ground_t = (24, 16, 14)
    ground_b = (6, 5, 8)
    for y in range(H):
        if y < horizon:
            k = y / horizon
            r = int(sky_top[0] + (sky_hor[0] - sky_top[0]) * k)
            g = int(sky_top[1] + (sky_hor[1] - sky_top[1]) * k)
            b = int(sky_top[2] + (sky_hor[2] - sky_top[2]) * k)
        else:
            k = (y - horizon) / (H - horizon)
            r = int(ground_t[0] + (ground_b[0] - ground_t[0]) * k)
            g = int(ground_t[1] + (ground_b[1] - ground_t[1]) * k)
            b = int(ground_t[2] + (ground_b[2] - ground_t[2]) * k)
        for x in range(0, W, 4):
            for xx in range(x, min(x + 4, W)):
                px[xx, y] = (r, g, b)

    sun_x, sun_y = int(W * 0.72), int(H * 0.30)
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    maxr = int(W * 0.34)
    for r in range(maxr, 0, -10):
        a = int(110 * (1 - r / maxr))
        gd.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=a)
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    warm = Image.new("RGB", (W, H), (255, 196, 96))
    img = Image.composite(warm, img, glow)
    d = ImageDraw.Draw(img)
    d.ellipse([sun_x - 46, sun_y - 46, sun_x + 46, sun_y + 46],
              fill=(255, 240, 190))

    fig = (6, 7, 12)
    base = int(H * 0.925)
    cx = int(W * 0.60)
    hh = int(H * 0.185)
    hr = int(H * 0.024)
    hy = base - hh
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=fig)
    sh_y = hy + hr - 2
    hip_y = base - int(H * 0.100)
    torso_w = int(H * 0.052)
    d.line([cx, sh_y, cx, hip_y], fill=fig, width=torso_w)
    d.ellipse([cx - torso_w // 2, sh_y - torso_w // 2,
               cx + torso_w // 2, sh_y + torso_w // 2], fill=fig)
    d.ellipse([cx - torso_w // 2, hip_y - torso_w // 2,
               cx + torso_w // 2, hip_y + torso_w // 2], fill=fig)
    wl = int(H * 0.016)
    d.line([cx, hip_y, cx + int(W * 0.05), base - int(H * 0.045),
            cx + int(W * 0.045), base], fill=fig, width=wl)
    d.line([cx, hip_y, cx - int(W * 0.038), base - int(H * 0.05),
            cx - int(W * 0.028), base], fill=fig, width=wl)
    d.ellipse([cx + int(W * 0.033) - wl // 2, base - wl // 2,
               cx + int(W * 0.033) + wl // 2, base + wl // 2], fill=fig)
    d.ellipse([cx - int(W * 0.028) - wl // 2, base - wl // 2,
               cx - int(W * 0.028) + wl // 2, base + wl // 2], fill=fig)
    d.line([cx + int(W * 0.012), sh_y + int(H * 0.02),
            cx + int(W * 0.075), hip_y - int(H * 0.015)], fill=fig, width=wl)
    d.line([cx - int(W * 0.012), sh_y + int(H * 0.02),
            cx - int(W * 0.062), hip_y - int(H * 0.022)], fill=fig, width=wl)

    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(out_path)
    return out_path


def build_bg(img_path, out_path, drawing=False):
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        x = (iw - nw) // 2
        img = img.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / target)
        y = (ih - nh) // 2
        img = img.crop((0, y, iw, y + nh))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.62 if not drawing else 1.0)

    if drawing:
        img = img.convert("RGB")
    else:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for y in range(H):
            rel = y / H
            base = int(40 + 150 * rel)
            if 0.47 <= rel <= 0.90:
                base = min(255, base + 80)
            elif 0.43 <= rel < 0.47:
                base += int(80 * (rel - 0.43) / 0.04)
            elif 0.90 < rel <= 0.95:
                base += int(80 * (1 - (rel - 0.90) / 0.05))
            od.line([(0, y), (W, y)], fill=(0, 0, 0, base))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        rel = y / H
        base = 0
        if 0.52 <= rel <= 0.88:
            base = 118
        elif 0.48 <= rel < 0.52:
            base = int(118 * (rel - 0.48) / 0.04)
        elif 0.88 < rel <= 0.94:
            base = int(118 * (1 - (rel - 0.88) / 0.06))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, base))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(out_path)
    return out_path


def build_bg_bright(img_path, out_path):
    """Fondo para direccion visual LUMINOSA (bienestar 2026-08): mismo recorte
    9:16 pero SIN el crush de brillo x0.62 ni doble banda negra del modo clasico.
    Un unico gradiente suave cubre la zona de karaoke para que el texto blanco
    siga leyendose sin apagar la imagen (emocional != oscuro)."""
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        x = (iw - nw) // 2
        img = img.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / target)
        y = (ih - nh) // 2
        img = img.crop((0, y, iw, y + nh))
    img = img.resize((W, H), Image.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        rel = y / H
        if rel < 0.42:
            a = 25
        elif rel < 0.52:
            a = int(25 + (100 - 25) * (rel - 0.42) / 0.10)
        elif rel <= 0.88:
            a = 115
        elif rel <= 0.96:
            a = int(115 + (145 - 115) * (rel - 0.88) / 0.08)
        else:
            a = 145
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(out_path, quality=92)
    return out_path


def build_bg_serif(img_path, out_path):
    """Fondo para modo serif (estilo quote-card): recorte 9:16 + gradiente
    vertical suave. Sin crush de brillo ni banda de karaoke: la legibilidad
    la da el gradiente (replica el brillo 97->47 de la referencia)."""
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        x = (iw - nw) // 2
        img = img.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / target)
        y = (ih - nh) // 2
        img = img.crop((0, y, iw, y + nh))
    img = img.resize((W, H), Image.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        rel = y / H
        base = int(90 + 80 * rel)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, base))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(out_path, quality=92)
    return out_path


def wrap_lines(draw, words, font, max_w, line_breaks=None, clean_styles=None):
    """Wrap words respecting forced line_breaks.
    Each item in `words` is (word_text, start, end).
    Returns list of lines, each line = [(word_text, timing, font), ...]"""
    lines = []
    cur = []
    line_breaks = line_breaks or set()
    widx = 0
    for timing in words:
        w_str = timing[0]
        if widx in line_breaks and cur:
            lines.append(cur)
            cur = []
        ww = draw.textlength(w_str, font=font)
        if cur:
            cur_w = sum(draw.textlength(c[0], font=c[2]) for c in cur)
            total = cur_w + 18 * (len(cur) - 1) + 18 + ww
            if total > max_w:
                lines.append(cur)
                cur = [(w_str, timing, font)]
            else:
                cur.append((w_str, timing, font))
        else:
            cur.append((w_str, timing, font))
        widx += 1
    if cur:
        lines.append(cur)
    return lines


def _draw_text_bg(frame, positions, scheme, alpha=TEXT_BG_ALPHA):
    """Dibuja fondo semi-opaco detrás del bloque de texto."""
    if not positions:
        return
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    min_x, min_y = W, H
    max_x, max_y = 0, 0
    for row, y in positions:
        for item in row:
            word, ws, we, x, f = item[0], item[1], item[2], item[3], item[4]
            wd = draw_ov.textlength(word, font=f)
            min_x = min(min_x, x)
            max_x = max(max_x, x + wd)
            ascent, descent = f.getmetrics()
            min_y = min(min_y, y)
            max_y = max(max_y, y + ascent + descent)
    bg_color = 0 if scheme.get("shadow", (0,0,0)) != (255,255,255) else 255
    draw_ov.rounded_rectangle(
        [min_x - TEXT_PAD_X, min_y - TEXT_PAD_Y,
         max_x + TEXT_PAD_X, max_y + TEXT_PAD_Y],
        radius=16, fill=(bg_color, bg_color, bg_color, alpha))
    frame.paste(Image.alpha_composite(
        frame.convert("RGBA"), overlay).convert("RGB"))


def _draw_equalizer(frame, t, scheme, bars=32, height=120, base_y=None,
                    color=None, glow=True):
    """Ecualizador animado en la parte inferior del frame.
    Simula barras que pulsan con el ritmo usando seeded random por tiempo."""
    if base_y is None:
        base_y = H - 80
    rng = np.random.default_rng(42)
    phases = rng.uniform(0, 6.28, bars)
    freqs = rng.uniform(0.4, 1.2, bars)
    bar_color = color or scheme.get("accent", (227, 179, 65))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    bw = (W - 80) / bars
    for i in range(bars):
        amp = (np.sin(t * 2.4 + phases[i]) * 0.5 + 0.5)
        amp *= (0.3 + 0.7 * abs(np.sin(t * freqs[i] + i * 0.5)))
        bh = max(4, int(amp * height))
        x0 = 40 + i * bw
        x1 = x0 + bw - 3
        y0 = base_y - bh
        y1 = base_y
        a = int(180 + 75 * amp)
        d.rounded_rectangle([x0, y0, x1, y1], radius=3,
                            fill=(*bar_color, a))
        if glow and amp > 0.6:
            d.rounded_rectangle([x0 - 2, y0 - 4, x1 + 2, y1 + 2],
                                radius=5, fill=(*bar_color, int(40 * amp)))
    frame.paste(Image.alpha_composite(
        frame.convert("RGBA"), overlay).convert("RGB"))


def _layout_karaoke(timings, final, clean_styles=None, line_breaks=None,
                    emphasis_map=None, align="center"):
    size = 76 if final else 66
    md = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    clean_styles = clean_styles or []
    line_breaks = line_breaks or set()
    emphasis_map = emphasis_map or {}
    drawable = [(w, s + PAD_BEFORE, e + PAD_BEFORE) for w, s, e in timings]

    def layout(font_size):
        font = ImageFont.truetype(FONT, font_size)
        strong_font = ImageFont.truetype(FONT_HEAVY, font_size)
        line_words = wrap_lines(md, drawable, font, W - 180, line_breaks)
        base_lh = int(font_size * 1.55)
        y = int(H * 0.50)
        positions = []
        widx = 0
        for line in line_words:
            row = []
            has_big = False
            for w_str, timing, wf in line:
                ws, we = timing[1] + PAD_BEFORE, timing[2] + PAD_BEFORE
                sty = clean_styles[widx] if widx < len(clean_styles) else {}
                emph = emphasis_map.get(widx)
                if sty.get("big"):
                    has_big = True
                # <strong> usa font heavy + color dorado
                if emph == "strong":
                    row.append((w_str, ws, we, 0, strong_font,
                                sty.get("color") or ACCENT, "strong"))
                else:
                    row.append((w_str, ws, we, 0, wf,
                                sty.get("color"), emph))
                widx += 1
            total_w = sum(md.textlength(r[0], font=r[4]) for r in row) + 18 * (len(row) - 1)
            if align == "left":
                x = 90
            elif align == "right":
                x = W - total_w - 90
            else:
                x = (W - total_w) / 2
            for ri in range(len(row)):
                w, ws, we, _, f, col, emph = row[ri]
                wdt = md.textlength(w, font=f)
                row[ri] = (w, ws, we, x, f, col, emph)
                x += wdt + 18
            line_h = int(base_lh * 1.25) if has_big else base_lh
            positions.append((row, y))
            y += line_h
        return font, positions

    while size > 56:
        font, positions = layout(size)
        bottom = positions[-1][1] + int(size * 1.55) if positions else 0
        if bottom <= int(H * 0.90):
            break
        size -= 4
    return font, positions


def _draw_karaoke(frame, font, positions, t, scheme):
    d = ImageDraw.Draw(frame)
    for row, y in positions:
        for item in row:
            w, ws, we, x, f, custom_col = item[0], item[1], item[2], item[3], item[4], item[5]
            emph = item[6] if len(item) > 6 else None
            is_active = ws <= t < we
            is_past = t >= we

            if is_past:
                col = custom_col or scheme["accent"]
            elif is_active:
                col = scheme["main"]
            else:
                col = scheme["dim"]

            # Palabra activa: outline más grueso (glow sutil)
            if is_active:
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx or dy:
                            d.text((x + dx, y + dy), w, font=f,
                                   fill=scheme["shadow"])
                d.text((x, y), w, font=f, fill=col)
            else:
                d.text((x + 2, y + 2), w, font=f, fill=scheme["shadow"])
                d.text((x, y), w, font=f, fill=col)
    return frame


def _layout_static(lines, final, start_size=88, min_size=40,
                    line_sizes=None, y_center=0.42):
    """Texto estático centrado con tamaños por línea.

    lines: lista de str.
    line_sizes: dict {índice: tamaño_base}. Los tamaños se escalan
    proporcionalmente cuando el auto-shrink achica el tamaño global.
    """
    md = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    # Normalizar: extraer textos y tamaños base por línea
    texts = []
    base_sizes = []
    for i, item in enumerate(lines):
        texts.append(item)
        if line_sizes and i in line_sizes:
            base_sizes.append(line_sizes[i])
        else:
            base_sizes.append(None)  # usar el tamaño global

    def layout(global_size):
        positions = []
        line_heights = []
        fonts = []
        # Escalar tamaños proporcionalmente al global_size
        scale = global_size / start_size if start_size else 1.0
        for i, txt in enumerate(texts):
            if base_sizes[i]:
                sz = max(32, int(base_sizes[i] * scale))
            else:
                sz = global_size
            # Jerarquía: mayúsculas = 1.3x, comillas = 1.1x
            is_upper = txt == txt.upper() and txt.strip() and not txt.isnumeric()
            is_quoted = txt.startswith('"') or txt.startswith('"')
            if is_upper:
                sz = int(sz * 1.3)
            elif is_quoted:
                sz = int(sz * 1.1)
            font = ImageFont.truetype(FONT, sz)
            fonts.append(font)
            line_heights.append(int(sz * 1.28))

        total_h = sum(line_heights)
        y0 = int(H * y_center) - total_h // 2
        y = y0
        for i, txt in enumerate(texts):
            font = fonts[i]
            w = md.textlength(txt, font=font)
            x = (W - w) / 2
            positions.append(([(txt, 0.0, 1e12, x, font, None)], y))
            y += line_heights[i]
        return fonts[0] if fonts else ImageFont.truetype(FONT, global_size), positions

    size = start_size
    font, positions = layout(size)
    while size > min_size:
        font, positions = layout(size)
        fits = True
        scale = size / start_size if start_size else 1.0
        for i, txt in enumerate(texts):
            sz = max(32, int(base_sizes[i] * scale)) if base_sizes[i] else size
            f = ImageFont.truetype(FONT, sz)
            if md.textlength(txt, font=f) > W - 80:
                fits = False
                break
        if positions:
            last_y = positions[-1][1]
            last_sz_val = base_sizes[-1] if base_sizes[-1] else size
            last_sz = max(32, int(last_sz_val * scale)) if base_sizes[-1] else size
            bottom = last_y + int(last_sz * 1.28)
        else:
            bottom = 0
        if fits and bottom <= int(H * 0.88):
            break
        size -= 4
    return font, positions


def _layout_serif_static(struct, cta_struct, timings=None,
                         start_size=64, min_size=36):
    """Layout serif estilo quote-card (referencia ChatGPT):
    - Gancho (1er párrafo) más grande, cuerpo debajo, bloque arrancando al 19%.
    - CTA fijado al 80% con corazón debajo.
    - Si hay timings, cada palabra queda marcada karaoke (dim->dorado->blanco).
    Auto-achique hasta que el bloque principal no pise el CTA."""
    md = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    cache = {}

    def get_font(path, sz):
        key = (path, sz)
        if key not in cache:
            cache[key] = ImageFont.truetype(path, sz)
        return cache[key]

    def layout_block(blk, size, gap_word=None, line_mult=1.5,
                     para_gap_mult=0.85):
        font = get_font(FONT_SERIF, size)
        if gap_word is None:
            gap_word = max(12, int(size * 0.30))
        lh = int(size * line_mult)
        para_gap = int(size * para_gap_mult)
        max_w = W - 170

        def center_row(words):
            widths = [md.textlength(w, font=font) for w, _ in words]
            total_w = sum(widths) + gap_word * (len(words) - 1)
            x = (W - total_w) / 2
            row = []
            for (w, gold), wd in zip(words, widths):
                row.append([w, x, gold, None, None])
                x += wd + gap_word
            return row

        rows = []
        y = 0
        for pi, para in enumerate(blk):
            if pi > 0:
                y += para_gap
            for words in para:
                cur, cur_w = [], 0
                for w, gold in words:
                    ww = md.textlength(w, font=font)
                    add = ww if not cur else ww + gap_word
                    if cur and cur_w + add > max_w:
                        rows.append((center_row(cur), y))
                        y += lh
                        cur, cur_w = [(w, gold)], ww
                    else:
                        cur.append((w, gold))
                        cur_w += add
                if cur:
                    rows.append((center_row(cur), y))
                    y += lh
        return font, rows, y

    cta_top = int(H * 0.80)
    hook_scale = 1.32
    y0 = int(H * 0.19)

    def full_layout(size):
        """Gancho a size*hook_scale, resto del cuerpo a size.
        Cada fila lleva su fuente: (celdas, y, font)."""
        hook_size = min(int(size * hook_scale), start_size + 26)
        hfont, hrows, hbottom = layout_block(struct[:1], hook_size,
                                             line_mult=1.4)
        out = [(row, y + y0, hfont) for row, y in hrows]
        bottom = hbottom + y0
        if len(struct) > 1:
            bfont, brows, bbottom = layout_block(struct[1:], size)
            out += [(row, y + hbottom + int(size * 0.75) + y0, bfont)
                    for row, y in brows]
            bottom += int(size * 0.75) + bbottom
        return out, bottom

    size = start_size
    rows, bottom = full_layout(size)
    while size > min_size and bottom > cta_top - int(H * 0.035):
        size -= 3
        rows, bottom = full_layout(size)

    # Karaoke: adjuntar (ws, we) a cada palabra del cuerpo en orden
    n_main = 0
    if timings:
        tmap = [(w, s + PAD_BEFORE, e + PAD_BEFORE) for w, s, e in timings]
        flat_main = [cell for row, _, _ in rows for cell in row]
        n_main = len(flat_main)
        for i, cell in enumerate(flat_main):
            if i < len(tmap):
                cell[3], cell[4] = tmap[i][1], tmap[i][2]

    # CTA: tamaño atado al principal, con achique propio si no entra
    cta_size = max(40, int(size * 0.86))
    while cta_size > 30:
        _, cta_rows, cta_bottom = layout_block(cta_struct, cta_size, 12, 1.4, 0.5)
        widest = max((md.textlength(cell[0], font=get_font(FONT_SERIF, cta_size))
                      for row, _ in cta_rows for cell in row), default=0)
        if widest <= W - 120 and cta_bottom + int(cta_size * 2.2) <= H - 60:
            break
        cta_size -= 3
    # Re-adjuntar timings del CTA tras el re-layout final
    if timings:
        tmap = [(w, s + PAD_BEFORE, e + PAD_BEFORE) for w, s, e in timings]
        n_main = len([cell for row, _, _ in rows for cell in row])
        for j, cell in enumerate(cell for row, _ in cta_rows for cell in row):
            k = n_main + j
            if k < len(tmap):
                cell[3], cell[4] = tmap[k][1], tmap[k][2]
    cfont = get_font(FONT_SERIF, cta_size)
    cta_rows = [(row, y + cta_top) for row, y in cta_rows]
    heart_y = cta_top + cta_bottom + int(cta_size * 0.45)
    heart_font = get_font(FONT_SERIF_HEART, int(cta_size * 1.05))
    return rows, cfont, cta_rows, heart_y, heart_font


def _draw_serif(frame, rows, cfont, cta_rows, heart_y, heart_font,
                scheme, t=None):
    """Texto serif quote-card con karaoke sutil (cada fila lleva su fuente):
    - palabra marcada {y}: siempre dorada
    - pendiente de hablar: blanco tenue
    - palabra actual: dorada (cabeza de lectura)
    - ya hablada: blanca
    Sin sombra ni outline (fiel a la referencia)."""
    d = ImageDraw.Draw(frame)
    dim = scheme.get("dim", (185, 189, 196))

    def word_color(cell):
        w, x, gold, ws, we = cell
        if gold:
            return scheme["accent"]
        if t is None or ws is None:
            return scheme["main"]
        if t >= we:
            return scheme["main"]
        if t >= ws:
            return scheme["accent"]
        return dim

    for row, y, f in rows:
        for cell in row:
            d.text((cell[1], y), cell[0], font=f, fill=word_color(cell))
    for row, y in cta_rows:
        for cell in row:
            d.text((cell[1], y), cell[0], font=cfont, fill=word_color(cell))
    hw = d.textlength("\u2665", font=heart_font)
    d.text(((W - hw) / 2, heart_y), "\u2665", font=heart_font,
           fill=scheme["accent"])
    return frame


def _ease(progress):
    """Ease-in-out (acelera suave, frena suave) para motion de cámara."""
    return 0.5 - 0.5 * math.cos(math.pi * progress)


def render_scene(timings, bg_img, wav, out_path, final=False, motion=None,
                 text_scheme="dark", fade=0.4, crf=20, preset="medium", tune=None,
                 static_lines=None, static_size=None, static_sizes=None,
                 trans=None,
                 clean_styles=None, line_breaks=None, serif_data=None,
                 emphasis_map=None, align="center", equalizer=False):
    dur = probe_duration(wav)
    total = PAD_BEFORE + dur + PAD_AFTER
    frames = int(math.ceil(total * FPS))
    scheme = TEXT_SCHEMES.get(text_scheme, TEXT_SCHEMES["dark"])
    white = Image.new("RGB", (W, H), (255, 255, 255))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    trans = trans or {}
    tstyle = trans.get("style", "fade")
    tdur = trans.get("dur", fade)

    def apply_transition(frame, t):
        """Transición al inicio y final de la escena (dentro de pads)."""
        if tdur <= 0:
            return frame
        if t < tdur:
            p = t / tdur
        elif total - t < tdur:
            p = (total - t) / tdur
        else:
            return frame
        p = max(0.0, min(1.0, p))
        if tstyle == "black":
            return Image.blend(frame, black, (1 - p) * 0.85)
        if tstyle == "flash":
            return Image.blend(frame, white, (1 - p) ** 2)
        if tstyle == "blur":
            r = int((1 - p) * 10)
            if r > 0:
                return frame.filter(ImageFilter.GaussianBlur(radius=r))
            return frame
        return Image.blend(frame, white, (1 - p) * 0.85)

    if motion:
        src = Image.open(bg_img).convert("RGB")
        sw, sh = int(W * 1.15), int(H * 1.15)
        src = src.resize((sw, sh), Image.LANCZOS)
    else:
        src = None

    def get_frame(fi):
        if not motion:
            return Image.open(bg_img).convert("RGB").copy()
        t = fi / FPS
        progress = _ease(t / total if total > 0 else 0)
        sw_, sh_ = src.size
        if motion == "zoom-in":
            s = 1.15 - 0.15 * progress
            cw, ch = int(W * s), int(H * s)
            x1 = (sw_ - cw) // 2
            y1 = (sh_ - ch) // 2
            crop = src.crop((x1, y1, x1 + cw, y1 + ch))
            return crop.resize((W, H), Image.LANCZOS)
        elif motion == "zoom-out":
            s = 1.0 + 0.15 * progress
            cw, ch = int(W * s), int(H * s)
            x1 = (sw_ - cw) // 2
            y1 = (sh_ - ch) // 2
            crop = src.crop((x1, y1, x1 + cw, y1 + ch))
            return crop.resize((W, H), Image.LANCZOS)
        elif motion == "pan-right":
            mx = int(sw_ * 0.06)
            xo = int(mx * (1 - 2 * progress))
            x1 = (sw_ - W) // 2 + xo
            y1 = (sh_ - H) // 2
            x1 = max(0, min(x1, sw_ - W))
            y1 = max(0, min(y1, sh_ - H))
            return src.crop((x1, y1, x1 + W, y1 + H)).copy()
        elif motion == "pan-left":
            mx = int(sw_ * 0.06)
            xo = int(mx * (-1 + 2 * progress))
            x1 = (sw_ - W) // 2 + xo
            y1 = (sh_ - H) // 2
            x1 = max(0, min(x1, sw_ - W))
            y1 = max(0, min(y1, sh_ - H))
            return src.crop((x1, y1, x1 + W, y1 + H)).copy()
        elif motion == "pan-up":
            my = int(sh_ * 0.04)
            yo = int(my * (-1 + 2 * progress))
            x1 = (sw_ - W) // 2
            y1 = (sh_ - H) // 2 + yo
            x1 = max(0, min(x1, sw_ - W))
            y1 = max(0, min(y1, sh_ - H))
            return src.crop((x1, y1, x1 + W, y1 + H)).copy()
        elif motion == "pan-down":
            my = int(sh_ * 0.04)
            yo = int(my * (1 - 2 * progress))
            x1 = (sw_ - W) // 2
            y1 = (sh_ - H) // 2 + yo
            x1 = max(0, min(x1, sw_ - W))
            y1 = max(0, min(y1, sh_ - H))
            return src.crop((x1, y1, x1 + W, y1 + H)).copy()
        else:
            return src.crop(((sw_ - W) // 2, (sh_ - H) // 2,
                             (sw_ - W) // 2 + W, (sh_ - H) // 2 + H)).copy()

    if serif_data:
        struct, cta_struct = serif_data
        srows, cfont, cta_rows, heart_y, heart_font = \
            _layout_serif_static(struct, cta_struct, timings=timings)
    elif static_lines:
        font, positions = _layout_static(static_lines, final,
                                         static_size or 88,
                                         line_sizes=static_sizes)
    else:
        font, positions = _layout_karaoke(timings, final,
                                          clean_styles=clean_styles,
                                          line_breaks=line_breaks,
                                          emphasis_map=emphasis_map,
                                          align=align)

    venc = ["-c:v", "libx264", "-preset", preset]
    if tune:
        venc += ["-tune", tune]
    venc += ["-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-t", f"{total:.3f}",
    ] + venc + [
        "-af", f"adelay={int(PAD_BEFORE*1000)}:all=1,apad",
        "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for fi in range(frames):
        t = fi / FPS
        frame = get_frame(fi)
        if serif_data:
            _draw_serif(frame, srows, cfont, cta_rows,
                        heart_y, heart_font, scheme, t=t)
        else:
            if not static_lines:
                _draw_text_bg(frame, positions, scheme)
            _draw_karaoke(frame, font, positions, t, scheme)
        if equalizer:
            _draw_equalizer(frame, t, scheme)
        frame = apply_transition(frame, t)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def render_scene_video(timings, video_path, wav, out_path, final=False,
                       text_scheme="dark", darken=0.22, fade=0.4,
                       crf=20, preset="medium", tune=None,
                       static_lines=None, static_size=None, static_sizes=None,
                       static_y=0.42,
                       trans=None,
                       clean_styles=None, line_breaks=None,
                       emphasis_map=None, align="center"):
    """Escena con fondo de video (b-roll vertical). Loop infinito via ffmpeg."""
    dur = probe_duration(wav)
    total = PAD_BEFORE + dur + PAD_AFTER
    frames = int(math.ceil(total * FPS))
    scheme = TEXT_SCHEMES.get(text_scheme, TEXT_SCHEMES["dark"])

    vf = ("scale={0}:{1}:force_original_aspect_ratio=increase,"
          "crop={0}:{1},".format(W, H) +
          f"eq=brightness=-{darken:.2f}:saturation=0.85,fps={FPS}")
    dec = subprocess.Popen(
        ["ffmpeg", "-y", "-stream_loop", "-1", "-i", video_path,
         "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    if static_lines:
        font, static_positions = _layout_static(static_lines, final,
                                         static_size or 88,
                                         line_sizes=static_sizes,
                                         y_center=static_y)
        _, karaoke_positions = _layout_karaoke(timings, final,
                                               clean_styles=clean_styles,
                                               line_breaks=line_breaks,
                                               emphasis_map=emphasis_map,
                                               align=align)
    else:
        font, karaoke_positions = _layout_karaoke(timings, final,
                                          clean_styles=clean_styles,
                                          line_breaks=line_breaks,
                                          emphasis_map=emphasis_map,
                                          align=align)
        static_positions = None
    venc = ["-c:v", "libx264", "-preset", preset]
    if tune:
        venc += ["-tune", tune]
    venc += ["-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-t", f"{total:.3f}",
    ] + venc + [
        "-af", f"adelay={int(PAD_BEFORE*1000)}:all=1,apad",
        "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    frame_size = W * H * 3
    white = Image.new("RGB", (W, H), (255, 255, 255))
    for fi in range(frames):
        t = fi / FPS
        raw = dec.stdout.read(frame_size)
        if len(raw) != frame_size:
            dec.stdout.close()
            dec.terminate()
            raise RuntimeError(f"video de fondo corto/fallo: {video_path}")
        frame = Image.frombytes("RGB", (W, H), raw)
        if fi == 0:
            _draw_text_bg(frame, karaoke_positions, scheme)
            if static_positions:
                _draw_text_bg(frame, static_positions, scheme)
        _draw_karaoke(frame, font, karaoke_positions, t, scheme)
        if static_positions:
            _draw_karaoke(frame, font, static_positions, t, scheme)
        if fade > 0:
            if t < fade:
                frame = Image.blend(frame, white, min(0.75, 1 - t / fade))
            elif total - t < fade:
                frame = Image.blend(frame, white,
                                    min(0.75, (fade - (total - t)) / fade))
        proc.stdin.write(frame.tobytes())
    dec.stdout.close()
    dec.terminate()
    dec.wait()
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def render_scene_draw(timings, img_path, wav, out_path, final=False,
                      style="whiteboard", crf=20, preset="medium", tune=None,
                      clean_styles=None, line_breaks=None, align="center"):
    """Escena con efecto 'mano dibujando': line-art revelado + stylus + karaoke."""
    import estilos_golpo as golpo

    dur = probe_duration(wav)
    total = PAD_BEFORE + dur + PAD_AFTER
    frames = int(math.ceil(total * FPS))
    art = Image.open(img_path).convert("RGB")
    bg_np, st_np, order = golpo.build_draw(art, style=style)
    font, positions = _layout_karaoke(timings, final,
                                      clean_styles=clean_styles,
                                      line_breaks=line_breaks,
                                      align=align)
    scheme = TEXT_SCHEMES["light"] if golpo.is_light(style) else TEXT_SCHEMES["dark"]

    venc = ["-c:v", "libx264", "-preset", preset]
    if tune:
        venc += ["-tune", tune]
    venc += ["-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-t", f"{total:.3f}",
    ] + venc + [
        "-af", f"adelay={int(PAD_BEFORE*1000)}:all=1,apad",
        "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for fi in range(frames):
        t = fi / FPS
        progress = min(max(t / dur, 0.0), 1.0) if dur > 0 else 1.0
        mask = golpo.reveal_mask(order, progress)
        frame = golpo.draw_frame(bg_np, st_np, mask)
        tip = golpo.stylus_position(order, progress)
        if tip is not None:
            frame = golpo.compose_stylus(frame, *tip)
        if fi == 0:
            _draw_text_bg(frame, positions, scheme)
        _draw_karaoke(frame, font, positions, t, scheme)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def styled_bg(img_path, out_path, style):
    """Aplica un estilo ilustrado (estilos_golpo) y guarda el fondo 9:16."""
    import estilos_golpo as golpo

    img = Image.open(img_path).convert("RGB")
    golpo.apply_style(img, style).save(out_path, quality=92)
    return out_path


def render_pipeline(scene, timings, img_path, bg_img, wav, mp4,
                    final=False, motion=None, master=False,
                    clean_styles=None, line_breaks=None,
                    emphasis_map=None):
    """Elige pipeline según claves: handdraw | estilo | clásico."""
    crf, preset, tune = MASTER if master else (20, "medium", None)
    static_lines = scene.get("static_text") or None
    static_size = scene.get("static_size")
    static_sizes = scene.get("static_sizes")
    trans = scene.get("trans")
    estilo = scene.get("estilo")

    if scene.get("handdraw"):
        return render_scene_draw(timings, img_path, wav, mp4, final=final,
                                 style=estilo or "whiteboard",
                                 crf=crf, preset=preset, tune=tune,
                                 clean_styles=clean_styles,
                                 line_breaks=line_breaks,
                                 align=scene.get("text_align", "center"))
    if scene.get("text_mode") == "serif":
        _, struct = parse_serif_text(scene["text"])
        _, cta_struct = parse_serif_text(scene.get("cta") or "")
        return render_scene(timings, bg_img, wav, mp4, final=final,
                            motion=motion,
                            text_scheme=scene.get("text_scheme", "dark"),
                            crf=crf, preset=preset, tune=tune,
                            trans=trans,
                            serif_data=(struct, cta_struct))
    if scene.get("title_text"):
        from vfxkit_titles import generate_title
        title_mp4 = mp4.replace(".mp4", "_title.mp4")
        generate_title(scene["title_text"], title_mp4,
                       style=scene.get("title_style", "aurora"),
                       size=scene.get("title_size", 120),
                       width=W, height=H,
                       duration=scene.get("title_duration", 5.0),
                       subtitle=scene.get("title_subtitle"))
        return title_mp4

    if scene.get("waveform"):
        from waveform_renderer import render_waveform_video
        wave_mp4 = mp4.replace(".mp4", "_wave.mp4")
        render_waveform_video(wav, wave_mp4,
                              width=W, height=scene.get("waveform_height", 150),
                              mode=scene.get("waveform_mode", "cline"),
                              color=scene.get("waveform_color", "white"))
        return wave_mp4

    if estilo:
        styled_bg(img_path, bg_img, estilo)
        import estilos_golpo as golpo
        scheme = "light" if golpo.is_light(estilo) else "dark"
        return render_scene(timings, bg_img, wav, mp4, final=final,
                            motion=motion, text_scheme=scheme,
                            crf=crf, preset=preset, tune=tune,
                            static_lines=static_lines, static_size=static_size,
                            static_sizes=static_sizes,
                            trans=trans, clean_styles=clean_styles,
                            line_breaks=line_breaks,
                            emphasis_map=emphasis_map,
                            align=scene.get("text_align", "center"),
                            equalizer=scene.get("equalizer", False))
    return render_scene(timings, bg_img, wav, mp4, final=final, motion=motion,
                        crf=crf, preset=preset, tune=tune,
                        static_lines=static_lines, static_size=static_size,
                        static_sizes=static_sizes,
                        trans=trans, clean_styles=clean_styles,
                        line_breaks=line_breaks,
                        emphasis_map=emphasis_map,
                        align=scene.get("text_align", "center"),
                        equalizer=scene.get("equalizer", False))


def resolve_visual(scene):
    """Convierte una escena semántica en parámetros técnicos.

    Si la escena tiene clave "visual" (dict con type/subject/action/mood),
    genera el prompt de imagen y sugiere motion/style automáticamente.
    Si no tiene "visual", retorna la escena sin cambios.

    Ejemplo de uso:
        scene = {
            "text": "No necesitas sanar, necesitas integrar.",
            "visual": {
                "type": "object_closeup",
                "subject": "woman hands",
                "action": "holding old photograph",
                "mood": "reflective"
            },
            "emphasis": ["integrar"]
        }
        scene = resolve_visual(scene)
        # scene["ai"] = "woman hands holding old photograph, reflective mood, soft natural light, cinematic, photorealistic"
        # scene["motion"] = "zoom-in"
    """
    visual = scene.get("visual")
    if not visual or not isinstance(visual, dict):
        return scene

    # Construir prompt desde componentes semánticos
    parts = []
    if visual.get("subject"):
        parts.append(visual["subject"])
    if visual.get("action"):
        parts.append(visual["action"])
    if visual.get("mood"):
        parts.append(f"{visual['mood']} mood")
    parts.append("soft natural light, cinematic, photorealistic, high detail")
    scene["ai"] = ", ".join(parts)

    # Sugerir motion según el tipo de escena
    if not scene.get("motion"):
        vtype = visual.get("type", "")
        motion_map = {
            "object_closeup": "zoom-in",
            "human_reflection": "zoom-in",
            "wide_landscape": "zoom-out",
            "hands_detail": "zoom-in",
            "environment": "pan-right",
            "symbolic": "zoom-out",
        }
        scene["motion"] = motion_map.get(vtype, "zoom-in")

    # Convertir emphasis list a tags <strong> en el texto
    emphasis_words = scene.get("emphasis")
    if emphasis_words and isinstance(emphasis_words, list):
        text = scene["text"]
        for word in emphasis_words:
            # Case-insensitive replacement manteniendo caso original
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            text = pattern.sub(f"<strong>{word}</strong>", text)
        scene["text"] = text
        # Limpiar emphasis ya que ahora están en el texto
        del scene["emphasis"]

    return scene


def build_scene(scene, idx, vk):
    voice = VOICES[vk]
    slug = f"e{idx:02d}_{vk}"
    etag = tts_engine_tag(voice)
    img_path = os.path.join(IMGDIR, f"e{idx:02d}.jpg")
    bg_img = os.path.join(TMP, f"{slug}_bg.jpg")

    # Resolver escena semántica → prompt técnico + emphasis tags
    scene = resolve_visual(scene)

    # Parse HTML <strong>/<em> tags: TTS recibe texto limpio, render recibe emphasis_map
    raw_text = scene["text"]
    if "<" in raw_text:
        tts_text, emphasis_map = parse_html_emphasis(raw_text)
    else:
        tts_text = raw_text
        emphasis_map = {}

    wav = os.path.join(AUDDIR, f"{slug}{etag}_{zlib.crc32(tts_text.encode())}.wav")
    mp4 = os.path.join(OUTDIR, f"{slug}.mp4")

    if scene.get("draw"):
        make_walking(img_path)
    else:
        download_image(scene, img_path)
    if scene.get("draw"):
        build_bg(img_path, bg_img, drawing=True)
    elif scene.get("dark"):
        build_bg(img_path, bg_img)
    else:
        build_bg_bright(img_path, bg_img)
    if not os.path.exists(wav):
        asyncio.run(tts_audio(tts_text, voice, wav))
    tj = os.path.join(TMP, f"{slug}{etag}_{zlib.crc32(tts_text.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = align_words(tts_text, wav)
        if timings is None:
            toks = tts_text.split()
            dur = probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))
    render_scene(timings, bg_img, wav, mp4, final=(idx == len(SCENES)),
                 emphasis_map=emphasis_map)
    return mp4


def concat(clips, out_path):
    lst = os.path.join(TMP, "concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
         "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
         "-map_metadata", "-1",
         "-movflags", "+faststart", out_path])


def main():
    for vk in VOICES:
        clips = []
        for idx, scene in enumerate(SCENES, start=1):
            print(f"[{vk}] escena {idx}/{len(SCENES)} ...", flush=True)
            clips.append(build_scene(scene, idx, vk))
        out = os.path.join(OUTDIR, f"caverna_{vk}.mp4")
        concat(clips, out)
        print(f"OK  {out}  {probe_duration(out):.1f}s  "
              f"{os.path.getsize(out)//1024} KB")


if __name__ == "__main__":
    main()
