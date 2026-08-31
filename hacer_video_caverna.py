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

from pipeline.tts import (
    DEEPEN,
    PAUSE_RE,
    align_words,
    has_pauses,
    mix_boom,
    probe_duration,
    rate_suffix,
    deepen_suffix,
    split_pauses,
    tts_audio,
)
from pipeline.media import (
    commons_url,
    generate_bgm,
    mix_bgm,
    norm,
    probe_duration,
    run,
)
from pipeline.scene_generation import (
    download_image,
    find_local_img,
    find_local_video,
    strip_img_metadata,
)
from pipeline.visual import (
    parse_html_emphasis,
    resolve_visual,
)
from pipeline.scene_art import (
    build_bg,
    build_bg_bright,
    build_bg_serif,
    make_walking,
)


def strip_img_metadata(path):
    """Wrapper de compatibilidad: delega a pipeline.scene_generation."""
    return strip_img_metadata.__wrapped__(path) if hasattr(strip_img_metadata, "__wrapped__") else __import__("pipeline.scene_generation", fromlist=["strip_img_metadata"]).strip_img_metadata(path)


strip_img_metadata.__wrapped__ = __import__("pipeline.scene_generation", fromlist=["strip_img_metadata"]).strip_img_metadata


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
    """Wrapper de compatibilidad: delega a pipeline.media."""
    return run.__wrapped__(cmd, **kw) if hasattr(run, "__wrapped__") else __import__("pipeline.media", fromlist=["run"]).run(cmd, **kw)


run.__wrapped__ = __import__("pipeline.media", fromlist=["run"]).run


def generate_bgm(out_path, duration=300):
    """Wrapper de compatibilidad: delega a pipeline.media."""
    return generate_bgm.__wrapped__(out_path, duration=duration) if hasattr(generate_bgm, "__wrapped__") else __import__("pipeline.media", fromlist=["generate_bgm"]).generate_bgm(out_path, duration=duration)


generate_bgm.__wrapped__ = __import__("pipeline.media", fromlist=["generate_bgm"]).generate_bgm


def mix_bgm(video_in, bgm_path, out_path, volume=0.4):
    """Wrapper de compatibilidad: delega a pipeline.media."""
    return mix_bgm.__wrapped__(video_in, bgm_path, out_path, volume=volume) if hasattr(mix_bgm, "__wrapped__") else __import__("pipeline.media", fromlist=["mix_bgm"]).mix_bgm(video_in, bgm_path, out_path, volume=volume)


mix_bgm.__wrapped__ = __import__("pipeline.media", fromlist=["mix_bgm"]).mix_bgm


def probe_duration(path):
    """Wrapper de compatibilidad: delega a pipeline.media."""
    return probe_duration.__wrapped__(path) if hasattr(probe_duration, "__wrapped__") else __import__("pipeline.media", fromlist=["probe_duration"]).probe_duration(path)


probe_duration.__wrapped__ = __import__("pipeline.media", fromlist=["probe_duration"]).probe_duration


def norm(s):
    """Wrapper de compatibilidad: delega a pipeline.media."""
    return norm.__wrapped__(s) if hasattr(norm, "__wrapped__") else __import__("pipeline.media", fromlist=["norm"]).norm(s)


norm.__wrapped__ = __import__("pipeline.media", fromlist=["norm"]).norm


def commons_url(params):
    """Wrapper de compatibilidad: delega a pipeline.media."""
    return commons_url.__wrapped__(params) if hasattr(commons_url, "__wrapped__") else __import__("pipeline.media", fromlist=["commons_url"]).commons_url(params)


commons_url.__wrapped__ = __import__("pipeline.media", fromlist=["commons_url"]).commons_url


def download_image(scene, out_path):
    return __import__("pipeline.scene_generation", fromlist=["download_image"]).download_image(scene, out_path)


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


PAUSE_RE = re.compile(r"\[(\d+)\]\s*")


# TTS / pacing / timings moved to pipeline.tts. Compatibility wrappers remain
# here to preserve the existing call sites and behavior exactly.


def has_pauses(text):
    """True si el texto contiene marcas de pausa [ms] (p. ej. [800])."""
    return has_pauses.__wrapped__(text) if hasattr(has_pauses, "__wrapped__") else __import__("pipeline.tts", fromlist=["has_pauses"]).has_pauses(text)


def split_pauses(text):
    """Divide un texto con marcas [ms] en frases con pausa después de cada una."""
    return __import__("pipeline.tts", fromlist=["split_pauses"]).split_pauses(text)


async def _tts_audio_paused(text, voice, out_wav, deepen=DEEPEN, rate="+0%"):
    """Wrapper de compatibilidad para la lógica modularizada."""
    return await __import__("pipeline.tts", fromlist=["_tts_audio_paused"])._tts_audio_paused(text, voice, out_wav, deepen=deepen, rate=rate)


async def tts_audio(text, voice, out_wav, deepen=DEEPEN, rate="+0%", engine=None):
    """Genera audio usando la implementación modularizada con compatibilidad completa."""
    return await __import__("pipeline.tts", fromlist=["tts_audio"]).tts_audio(text, voice, out_wav, deepen=deepen, rate=rate, engine=engine)


def align_words(text, wav):
    return __import__("pipeline.tts", fromlist=["align_words"]).align_words(text, wav)


def rate_suffix(rate):
    return __import__("pipeline.tts", fromlist=["rate_suffix"]).rate_suffix(rate)


def deepen_suffix(deepen):
    return __import__("pipeline.tts", fromlist=["deepen_suffix"]).deepen_suffix(deepen)


def mix_boom(wav):
    return __import__("pipeline.tts", fromlist=["mix_boom"]).mix_boom(wav)


# Legacy symbol preservation for other codepaths.
__all__ = [
    "has_pauses",
    "split_pauses",
    "_tts_audio_paused",
    "tts_audio",
    "align_words",
    "rate_suffix",
    "deepen_suffix",
    "mix_boom",
]


def make_walking(out_path):
    """Wrapper de compatibilidad: delega a pipeline.scene_art."""
    return make_walking.__wrapped__(out_path) if hasattr(make_walking, "__wrapped__") else __import__("pipeline.scene_art", fromlist=["make_walking"]).make_walking(out_path)


make_walking.__wrapped__ = __import__("pipeline.scene_art", fromlist=["make_walking"]).make_walking


def build_bg(img_path, out_path, drawing=False):
    """Wrapper de compatibilidad: delega a pipeline.scene_art."""
    return build_bg.__wrapped__(img_path, out_path, drawing=drawing) if hasattr(build_bg, "__wrapped__") else __import__("pipeline.scene_art", fromlist=["build_bg"]).build_bg(img_path, out_path, drawing=drawing)


build_bg.__wrapped__ = __import__("pipeline.scene_art", fromlist=["build_bg"]).build_bg


def build_bg_bright(img_path, out_path):
    """Wrapper de compatibilidad: delega a pipeline.scene_art."""
    return build_bg_bright.__wrapped__(img_path, out_path) if hasattr(build_bg_bright, "__wrapped__") else __import__("pipeline.scene_art", fromlist=["build_bg_bright"]).build_bg_bright(img_path, out_path)


build_bg_bright.__wrapped__ = __import__("pipeline.scene_art", fromlist=["build_bg_bright"]).build_bg_bright


def build_bg_serif(img_path, out_path):
    """Wrapper de compatibilidad: delega a pipeline.scene_art."""
    return build_bg_serif.__wrapped__(img_path, out_path) if hasattr(build_bg_serif, "__wrapped__") else __import__("pipeline.scene_art", fromlist=["build_bg_serif"]).build_bg_serif(img_path, out_path)


build_bg_serif.__wrapped__ = __import__("pipeline.scene_art", fromlist=["build_bg_serif"]).build_bg_serif


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


def resolve_visual(scene):
    """Wrapper de compatibilidad: delega a pipeline.visual."""
    return resolve_visual.__wrapped__(scene) if hasattr(resolve_visual, "__wrapped__") else __import__("pipeline.visual", fromlist=["resolve_visual"]).resolve_visual(scene)


resolve_visual.__wrapped__ = __import__("pipeline.visual", fromlist=["resolve_visual"]).resolve_visual


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
    tts_clean = tts_text
    if has_pauses(tts_text):
        _, _chunks, tts_clean = split_pauses(tts_text)

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
        timings = align_words(tts_clean, wav)
        if timings is None:
            toks = tts_clean.split()
            dur = probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))
    render_scene(timings, bg_img, wav, mp4, final=(idx == len(SCENES)),
                 emphasis_map=emphasis_map)
    return mp4


def render_scene(timings, bg_img, wav, out_path, final=False, motion=None,
                 text_scheme="dark", fade=0.4, crf=20, preset="medium", tune=None,
                 static_lines=None, static_size=None, static_sizes=None,
                 trans=None, clean_styles=None, line_breaks=None, serif_data=None,
                 emphasis_map=None, align="center", equalizer=False):
    """Wrapper de compatibilidad: delega a pipeline.rendering."""
    return __import__("pipeline.rendering", fromlist=["render_scene"]).render_scene(
        timings, bg_img, wav, out_path, final=final, motion=motion,
        text_scheme=text_scheme, fade=fade, crf=crf, preset=preset, tune=tune,
        static_lines=static_lines, static_size=static_size, static_sizes=static_sizes,
        trans=trans, clean_styles=clean_styles, line_breaks=line_breaks,
        serif_data=serif_data, emphasis_map=emphasis_map, align=align,
        equalizer=equalizer,
    )


def render_scene_video(timings, video_path, wav, out_path, final=False,
                       text_scheme="dark", darken=0.22, fade=0.4,
                       crf=20, preset="medium", tune=None,
                       static_lines=None, static_size=None, static_sizes=None,
                       static_y=0.42, trans=None,
                       clean_styles=None, line_breaks=None,
                       emphasis_map=None, align="center"):
    """Wrapper de compatibilidad: delega a pipeline.rendering."""
    return __import__("pipeline.rendering", fromlist=["render_scene_video"]).render_scene_video(
        timings, video_path, wav, out_path, final=final, text_scheme=text_scheme,
        darken=darken, fade=fade, crf=crf, preset=preset, tune=tune,
        static_lines=static_lines, static_size=static_size, static_sizes=static_sizes,
        static_y=static_y, trans=trans, clean_styles=clean_styles,
        line_breaks=line_breaks, emphasis_map=emphasis_map, align=align,
    )


def render_scene_draw(timings, img_path, wav, out_path, final=False,
                      style="whiteboard", crf=20, preset="medium", tune=None,
                      clean_styles=None, line_breaks=None, align="center"):
    """Wrapper de compatibilidad: delega a pipeline.rendering."""
    return __import__("pipeline.rendering", fromlist=["render_scene_draw"]).render_scene_draw(
        timings, img_path, wav, out_path, final=final, style=style,
        crf=crf, preset=preset, tune=tune, clean_styles=clean_styles,
        line_breaks=line_breaks, align=align,
    )


def render_pipeline(scene, timings, img_path, bg_img, wav, mp4,
                    final=False, motion=None, master=False,
                    clean_styles=None, line_breaks=None,
                    emphasis_map=None):
    """Wrapper de compatibilidad: delega a pipeline.rendering."""
    return __import__("pipeline.rendering", fromlist=["render_pipeline"]).render_pipeline(
        scene, timings, img_path, bg_img, wav, mp4, final=final, motion=motion,
        master=master, clean_styles=clean_styles, line_breaks=line_breaks,
        emphasis_map=emphasis_map,
    )


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


# ── Recursos visuales locales: caché por tema ──────────────────────────────
# De ahora en más, toda imagen/video descargado para crear videos se guarda
# en esta carpeta central y se reusa antes de golpear a los proveedores IA
# (Pollinations/Gemini/Cloudflare/HF), Pexels o Commons.
RECURSOS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "RECURSOS_VISUALES_PARA_VIDEOS_Y_SHORTS")


def _tema_slug(tema):
    """Normaliza una clave de tema/keywords a un nombre de archivo seguro."""
    if not tema:
        return "sin_tema"
    s = re.sub(r"[^a-z0-9]+", "_", str(tema).lower().strip())
    return (s.strip("_") or "sin_tema")[:60]


def buscar_recurso(ext, tema):
    """Busca en RECURSOS_DIR un archivo <tema>.<ext> ya descargado.

    Devuelve la ruta absoluta si existe, None si no (para que el caller
    descargue y luego llame a guardar_recurso). ext sin punto: 'jpg', 'mp4'.

    Hace match exacto (<tema>.<ext>) y flexible (el slug del tema contenido
    en el nombre del archivo, o a la inversa) para tolerar nombres manuales
    como 'hombre_afro_orando.jpg'."""
    if not os.path.isdir(RECURSOS_DIR):
        return None
    slug = _tema_slug(tema)
    dest = os.path.join(RECURSOS_DIR, f"{slug}.{ext}")
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        return dest
    # Match flexible: el slug conten ido en el basename (sin ext) o al revés.
    try:
        for f in sorted(os.listdir(RECURSOS_DIR)):
            if not f.endswith(f".{ext}"):
                continue
            base = f[: -len(f".{ext}")]
            base_slug = _tema_slug(base)
            if slug and (slug in base_slug or base_slug in slug):
                p = os.path.join(RECURSOS_DIR, f)
                if os.path.getsize(p) > 5000:
                    return p
    except OSError:
        pass
    return None


def guardar_recurso(ruta_fuente, tema, ext):
    """Guarda una copia de ruta_fuente en RECURSOS_DIR como <tema>.<ext>.
    No sobreescribe si ya existe. Devuelve la ruta guardada o None."""
    try:
        os.makedirs(RECURSOS_DIR, exist_ok=True)
        slug = _tema_slug(tema)
        dest = os.path.join(RECURSOS_DIR, f"{slug}.{ext}")
        if os.path.exists(dest):
            return dest
        from shutil import copyfile
        copyfile(ruta_fuente, dest)
        return dest
    except Exception:
        return None


def limpiar_metadata_video(mp4):
    """Quita TODO metadata del MP4 (remux con -map_metadata -1, sin re-encode).
    Garantiza que YouTube no vea rastro de qué generador se usó. No op: si ya
    está limpio, conserva el archivo original igualmente (remux es rápido)."""
    tmp = mp4 + ".nolmeta.mp4"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", mp4, "-map", "0", "-c", "copy",
         "-map_metadata", "-1", "-movflags", "+faststart", tmp],
        capture_output=True)
    if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
        os.replace(tmp, mp4)
    else:
        if os.path.exists(tmp):
            os.remove(tmp)
    return mp4


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
