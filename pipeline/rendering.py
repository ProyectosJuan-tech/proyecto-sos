"""Render/layout helpers moved out of hacer_video_caverna.py.

This module preserves the exact legacy behavior while giving the pipeline a
separate, testable rendering concern. The legacy module still exposes the same
API via thin compatibility wrappers.
"""

import math
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

from pipeline.tts import align_words, probe_duration, split_pauses

W, H = 1080, 1920
FPS = 30
PAD_BEFORE, PAD_AFTER = 0.45, 0.7
ACCENT = (227, 179, 65)
TEXT_PAD_X = 40
TEXT_PAD_Y = 20
TEXT_BG_ALPHA = 140
TEXT_SCHEMES = {
    "dark": {"accent": (227, 179, 65), "main": (255, 255, 255),
             "dim": (185, 189, 196), "shadow": (0, 0, 0)},
    "light": {"accent": (198, 118, 16), "main": (38, 38, 38),
              "dim": (150, 150, 150), "shadow": (255, 255, 255)},
}
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_HEAVY = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_SERIF = "/usr/share/fonts/truetype/msttcorefonts/Georgia.ttf"
FONT_SERIF_HEART = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

_KARAOKE_STYLE_RE = re.compile(r"\{(/?)(y|big|b|yb)\}")
_YELLOW = (255, 215, 0)
_BIG_SCALE = 1.35


def parse_karaoke_styles(marked_text):
    """Parse style markers from text."""
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
            if words and not word[0].isalpha() and not word[0] in '¿¡':
                words[-1] += word
            else:
                words.append(word)
                styles.append(style)
                word_idx += 1
            i = j
    return " ".join(words), styles, line_breaks


_HTML_TAG_RE = re.compile(r"<(/?)(strong|em|b|i)>")


def parse_html_emphasis(marked_text):
    """Parse HTML emphasis tags (<strong>, <em>, <b>, <i>)."""
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
    """Texto para estilo serif. Copia fiel de la implementación legacy."""
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


def wrap_lines(draw, words, font, max_w, line_breaks=None, clean_styles=None):
    """Wrap words respecting forced line breaks."""
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
    bg_color = 0 if scheme.get("shadow", (0, 0, 0)) != (255, 255, 255) else 255
    draw_ov.rounded_rectangle(
        [min_x - TEXT_PAD_X, min_y - TEXT_PAD_Y,
         max_x + TEXT_PAD_X, max_y + TEXT_PAD_Y],
        radius=16, fill=(bg_color, bg_color, bg_color, alpha))
    frame.paste(Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB"))


def _draw_equalizer(frame, t, scheme, bars=32, height=120, base_y=None,
                    color=None, glow=True):
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
        d.rounded_rectangle([x0, y0, x1, y1], radius=3, fill=(*bar_color, a))
        if glow and amp > 0.6:
            d.rounded_rectangle([x0 - 2, y0 - 4, x1 + 2, y1 + 2], radius=5, fill=(*bar_color, int(40 * amp)))
    frame.paste(Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB"))


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
                if emph == "strong":
                    row.append((w_str, ws, we, 0, strong_font, sty.get("color") or ACCENT, "strong"))
                else:
                    row.append((w_str, ws, we, 0, wf, sty.get("color"), emph))
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

            if is_active:
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx or dy:
                            d.text((x + dx, y + dy), w, font=f, fill=scheme["shadow"])
                d.text((x, y), w, font=f, fill=col)
            else:
                d.text((x + 2, y + 2), w, font=f, fill=scheme["shadow"])
                d.text((x, y), w, font=f, fill=col)
    return frame


def _layout_static(lines, final, start_size=88, min_size=40,
                   line_sizes=None, y_center=0.42):
    md = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    texts = []
    base_sizes = []
    for i, item in enumerate(lines):
        texts.append(item)
        if line_sizes and i in line_sizes:
            base_sizes.append(line_sizes[i])
        else:
            base_sizes.append(None)

    def layout(global_size):
        positions = []
        line_heights = []
        fonts = []
        scale = global_size / start_size if start_size else 1.0
        for i, txt in enumerate(texts):
            if base_sizes[i]:
                sz = max(32, int(base_sizes[i] * scale))
            else:
                sz = global_size
            is_upper = txt == txt.upper() and txt.strip() and not txt.isnumeric()
            is_quoted = txt.startswith('"') or txt.startswith("'")
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
        hook_size = min(int(size * hook_scale), start_size + 26)
        hfont, hrows, hbottom = layout_block(struct[:1], hook_size, line_mult=1.4)
        out = [(row, y + y0, hfont) for row, y in hrows]
        bottom = hbottom + y0
        if len(struct) > 1:
            bfont, brows, bbottom = layout_block(struct[1:], size)
            out += [(row, y + hbottom + int(size * 0.75) + y0, bfont) for row, y in brows]
            bottom += int(size * 0.75) + bbottom
        return out, bottom

    size = start_size
    rows, bottom = full_layout(size)
    while size > min_size and bottom > cta_top - int(H * 0.035):
        size -= 3
        rows, bottom = full_layout(size)

    cta_size = max(40, int(size * 0.86))
    while cta_size > 30:
        _, cta_rows, cta_bottom = layout_block(cta_struct, cta_size, 12, 1.4, 0.5)
        widest = max((md.textlength(cell[0], font=get_font(FONT_SERIF, cta_size)) for row, _ in cta_rows for cell in row), default=0)
        if widest <= W - 120 and cta_bottom + int(cta_size * 2.2) <= H - 60:
            break
        cta_size -= 3
    cfont = get_font(FONT_SERIF, cta_size)
    cta_rows = [(row, y + cta_top) for row, y in cta_rows]
    heart_y = cta_top + cta_bottom + int(cta_size * 0.45)
    heart_font = get_font(FONT_SERIF_HEART, int(cta_size * 1.05))
    return rows, cfont, cta_rows, heart_y, heart_font


def _draw_serif(frame, rows, cfont, cta_rows, heart_y, heart_font,
                scheme, t=None):
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
            return scheme["main"]
        return dim

    for row, y, f in rows:
        for cell in row:
            d.text((cell[1], y), cell[0], font=f, fill=word_color(cell))
    for row, y in cta_rows:
        for cell in row:
            d.text((cell[1], y), cell[0], font=cfont, fill=word_color(cell))
    hw = d.textlength("♥", font=heart_font)
    d.text(((W - hw) / 2, heart_y), "♥", font=heart_font, fill=scheme["accent"])
    return frame


def _ease(progress):
    return 0.5 - 0.5 * math.cos(math.pi * progress)


def render_scene(timings, bg_img, wav, out_path, final=False, motion=None,
                 text_scheme="dark", fade=0.4, crf=20, preset="medium", tune=None,
                 static_lines=None, static_size=None, static_sizes=None,
                 trans=None, clean_styles=None, line_breaks=None, serif_data=None,
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
        if tdur <= 0:
            return frame
        if t < tdur:
            # intro: por defecto la escena arranca desde la imagen (sin
            # dip-to-white al inicio) para que la thumbnail muestre el sujeto
            # y no un frame casi blanco antes de reproducir. Se conserva el
            # dip a la entrada solo si se pide explicitamente con intro_fade.
            if not trans.get("intro_fade"):
                return frame
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
        srows, cfont, cta_rows, heart_y, heart_font = _layout_serif_static(struct, cta_struct, timings=timings)
    elif static_lines:
        font, positions = _layout_static(static_lines, final, static_size or 88, line_sizes=static_sizes)
    else:
        font, positions = _layout_karaoke(timings, final, clean_styles=clean_styles, line_breaks=line_breaks,
                                          emphasis_map=emphasis_map, align=align)

    venc = ["-c:v", "libx264", "-preset", preset]
    if tune:
        venc += ["-tune", tune]
    venc += ["-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-t", f"{total:.3f}"] + venc + [
           "-af", f"adelay={int(PAD_BEFORE * 1000)}:all=1,apad",
           "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
           "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for fi in range(frames):
        t = fi / FPS
        frame = get_frame(fi)
        if serif_data:
            _draw_serif(frame, srows, cfont, cta_rows, heart_y, heart_font, scheme, t=t)
        else:
            if not static_lines:
                _draw_text_bg(frame, positions, scheme)
            _draw_karaoke(frame, font, positions, t, scheme)
        if equalizer:
            _draw_equalizer(frame, t, scheme)
        frame = apply_transition(frame, t)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close(); proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def render_scene_video(timings, video_path, wav, out_path, final=False,
                       text_scheme="dark", darken=0.22, fade=0.4,
                       crf=20, preset="medium", tune=None,
                       static_lines=None, static_size=None, static_sizes=None,
                       static_y=0.42, trans=None,
                       clean_styles=None, line_breaks=None,
                       emphasis_map=None, align="center"):
    dur = probe_duration(wav)
    total = PAD_BEFORE + dur + PAD_AFTER
    frames = int(math.ceil(total * FPS))
    scheme = TEXT_SCHEMES.get(text_scheme, TEXT_SCHEMES["dark"])

    vf = ("scale={0}:{1}:force_original_aspect_ratio=increase,"
          "crop={0}:{1},".format(W, H) +
          f"eq=brightness=-{darken:.2f}:saturation=0.85,fps={FPS}")
    dec = subprocess.Popen(["ffmpeg", "-y", "-stream_loop", "-1", "-i", video_path,
                            "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    if static_lines:
        font, static_positions = _layout_static(static_lines, final, static_size or 88,
                                                line_sizes=static_sizes, y_center=static_y)
        _, karaoke_positions = _layout_karaoke(timings, final, clean_styles=clean_styles,
                                               line_breaks=line_breaks, emphasis_map=emphasis_map, align=align)
    else:
        font, karaoke_positions = _layout_karaoke(timings, final, clean_styles=clean_styles,
                                                 line_breaks=line_breaks, emphasis_map=emphasis_map, align=align)
        static_positions = None
    venc = ["-c:v", "libx264", "-preset", preset]
    if tune:
        venc += ["-tune", tune]
    venc += ["-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-t", f"{total:.3f}"] + venc + [
           "-af", f"adelay={int(PAD_BEFORE * 1000)}:all=1,apad",
           "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
           "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    frame_size = W * H * 3
    white = Image.new("RGB", (W, H), (255, 255, 255))
    for fi in range(frames):
        t = fi / FPS
        raw = dec.stdout.read(frame_size)
        if len(raw) != frame_size:
            dec.stdout.close(); dec.terminate(); raise RuntimeError(f"video de fondo corto/fallo: {video_path}")
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
                frame = Image.blend(frame, white, min(0.75, (fade - (total - t)) / fade))
        proc.stdin.write(frame.tobytes())
    dec.stdout.close(); dec.terminate(); dec.wait(); proc.stdin.close(); proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def render_scene_draw(timings, img_path, wav, out_path, final=False,
                      style="whiteboard", crf=20, preset="medium", tune=None,
                      clean_styles=None, line_breaks=None, align="center"):
    import estilos_golpo as golpo

    dur = probe_duration(wav)
    total = PAD_BEFORE + dur + PAD_AFTER
    frames = int(math.ceil(total * FPS))
    art = Image.open(img_path).convert("RGB")
    bg_np, st_np, order = golpo.build_draw(art, style=style)
    font, positions = _layout_karaoke(timings, final, clean_styles=clean_styles, line_breaks=line_breaks, align=align)
    scheme = TEXT_SCHEMES["light"] if golpo.is_light(style) else TEXT_SCHEMES["dark"]

    venc = ["-c:v", "libx264", "-preset", preset]
    if tune:
        venc += ["-tune", tune]
    venc += ["-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(FPS)]
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-t", f"{total:.3f}"] + venc + [
           "-af", f"adelay={int(PAD_BEFORE * 1000)}:all=1,apad",
           "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
           "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    proc.stdin.close(); proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def styled_bg(img_path, out_path, style):
    import estilos_golpo as golpo
    img = Image.open(img_path).convert("RGB")
    golpo.apply_style(img, style).save(out_path, quality=92)
    return out_path


def render_pipeline(scene, timings, img_path, bg_img, wav, mp4,
                    final=False, motion=None, master=False,
                    clean_styles=None, line_breaks=None,
                    emphasis_map=None):
    from vfxkit_titles import generate_title
    import estilos_golpo as golpo

    crf, preset, tune = (18, "slow", "film") if master else (20, "medium", None)
    static_lines = scene.get("static_text") or None
    static_size = scene.get("static_size")
    static_sizes = scene.get("static_sizes")
    trans = scene.get("trans")
    estilo = scene.get("estilo")

    if scene.get("handdraw"):
        return render_scene_draw(timings, img_path, wav, mp4, final=final,
                                 style=estilo or "whiteboard",
                                 crf=crf, preset=preset, tune=tune,
                                 clean_styles=clean_styles, line_breaks=line_breaks,
                                 align=scene.get("text_align", "center"))
    if scene.get("text_mode") == "serif":
        # El texto puede llevar marcas de pausa [ms]; pasarlas a la pantalla
        # mostraría los numeros, asi que se limpia antes de construir el struct.
        _scr_text = split_pauses(scene["text"])[2]
        _scr_cta = split_pauses(scene.get("cta") or "")[2]
        _, struct = parse_serif_text(_scr_text)
        _, cta_struct = parse_serif_text(_scr_cta)
        return render_scene(timings, bg_img, wav, mp4, final=final,
                            motion=motion,
                            text_scheme=scene.get("text_scheme", "dark"),
                            crf=crf, preset=preset, tune=tune,
                            trans=trans,
                            serif_data=(struct, cta_struct))
    if scene.get("title_text"):
        title_mp4 = mp4.replace(".mp4", "_title.mp4")
        generate_title(scene["title_text"], title_mp4, style=scene.get("title_style", "aurora"),
                       size=scene.get("title_size", 120), width=W, height=H,
                       duration=scene.get("title_duration", 5.0), subtitle=scene.get("title_subtitle"))
        return title_mp4

    if scene.get("waveform"):
        from waveform_renderer import render_waveform_video
        wave_mp4 = mp4.replace(".mp4", "_wave.mp4")
        render_waveform_video(wav, wave_mp4, width=W, height=scene.get("waveform_height", 150),
                              mode=scene.get("waveform_mode", "cline"), color=scene.get("waveform_color", "white"))
        return wave_mp4

    if estilo:
        styled_bg(img_path, bg_img, estilo)
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


__all__ = [
    "render_scene",
    "render_scene_video",
    "render_scene_draw",
    "styled_bg",
    "render_pipeline",
    "parse_karaoke_styles",
    "parse_html_emphasis",
    "parse_serif_text",
    "_layout_karaoke",
    "_draw_karaoke",
    "_layout_static",
    "_draw_text_bg",
    "_draw_equalizer",
]
