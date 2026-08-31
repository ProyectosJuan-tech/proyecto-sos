#!/usr/bin/env python3
"""Pipeline base YOUTUBE: videos largos horizontales 16:9 (1920x1080).

Reutiliza los helpers de hacer_video_caverna que no dependen del formato
(TTS, karaoke word-by-word, BGM, Wikimedia Commons, concat) y redefine el
render para 16:9 apaisado, pensado para monetización larga (8+ min, RPM alto).

IMPORTANTE: no toca hacer_video_caverna (pipeline Facebook vertical).
"""
import json
import math
import os
import subprocess
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_caverna as base

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H = 1920, 1080
FPS = 30
PAD_BEFORE, PAD_AFTER = 0.45, 0.5
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
ACCENT = (227, 179, 65)
TEXT_SCHEMES = {
    "dark": {"accent": (227, 179, 65), "main": (255, 255, 255),
             "dim": (185, 189, 196), "shadow": (0, 0, 0)},
    "light": {"accent": (198, 118, 16), "main": (38, 38, 38),
              "dim": (150, 150, 150), "shadow": (255, 255, 255)},
}

VOICES = {"male": "es-MX-JorgeNeural", "female": "es-AR-ElenaNeural"}


def _ease(progress):
    """Ease-in-out (acelera suave, frena suave) para motion de cámara."""
    return 0.5 - 0.5 * math.cos(math.pi * progress)


def run(cmd, **kw):
    base.run(cmd, **kw)


def probe_duration(path):
    return base.probe_duration(path)


def build_bg(img_path, out_path):
    """Fondo 16:9 con crop centrado + overlay inferior para el karaoke."""
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
    img = ImageEnhance.Brightness(img).enhance(0.62)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        rel = y / H
        a = int(30 + 110 * rel)
        if 0.50 <= rel <= 0.90:
            a = min(200, a + 70)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(out_path)
    return out_path


def build_bg_bright(img_path, out_path):
    """Fondo 16:9 LUMINOSA: SIN crush de brillo x0.62. Un gradiente suave
    cubre la zona de karaoke para que el texto siga leyendose sin apagar
    la imagen. Para la dirección visual cinematográfica, luminosa, humana."""
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
            a = 20
        elif rel < 0.52:
            a = int(20 + (90 - 20) * (rel - 0.42) / 0.10)
        elif rel <= 0.88:
            a = 90
        elif rel <= 0.96:
            a = int(90 + (130 - 90) * (rel - 0.88) / 0.08)
        else:
            a = 130
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(out_path, quality=92)
    return out_path


def _layout_karaoke(timings, final, emphasis_map=None):
    """Posiciona el karaoke en la franja inferior-central (estilo narrativo).

    Tupla de 7 elementos: (word, ws, we, x, font, color, emphasis)
    - color: None = usar scheme, tuple = override (para <strong> con ACCENT)
    - emphasis: None | "strong"
    """
    size = 64 if final else 56
    md = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    emphasis_map = emphasis_map or {}
    drawable = [(w, s + PAD_BEFORE, e + PAD_BEFORE) for w, s, e in timings]

    def layout(font_size):
        font = ImageFont.truetype(FONT, font_size)
        strong_font = ImageFont.truetype(
            "/usr/share/fonts/opentype/inter/Inter-Black.otf", font_size)
        line_words = base.wrap_lines(md, drawable, font, int(W * 0.78))
        line_h = int(font_size * 1.45)
        y = int(H * 0.52)
        positions = []
        widx = 0
        for line in line_words:
            row_pre = []
            for item in line:
                w_str, timing, _f = item
                emph = emphasis_map.get(widx)
                f = strong_font if emph == "strong" else font
                row_pre.append((w_str, timing, f, emph))
                widx += 1
            widths = [md.textlength(r[0], font=r[2]) for r in row_pre]
            total_w = sum(widths) + 18 * (len(row_pre) - 1)
            x = (W - total_w) / 2
            row = []
            for (w_str, timing, f, emph), wdt in zip(row_pre, widths):
                color = ACCENT if emph == "strong" else None
                row.append((w_str, timing[1], timing[2], x, f, color, emph))
                x += wdt + 18
            positions.append((row, y))
            y += line_h
        return font, positions

    while size > 40:
        font, positions = layout(size)
        bottom = positions[-1][1] + int(size * 1.45) if positions else 0
        if bottom <= int(H * 0.90):
            break
        size -= 4

    if timings:
        gaps = [we - ws for _, ws, we in timings]
        if len(gaps) > 3:
            mean_g = sum(gaps) / len(gaps)
            variance = sum((g - mean_g) ** 2 for g in gaps) / len(gaps)
            if variance < 0.001:
                print(f"⚠ KARAOKE: alineación uniforme (var={variance:.4f}) — "
                      f"posible Whisper fallback sin palabras")

    return font, positions


def _layout_static(lines, final, start_size=96, min_size=48,
                    line_sizes=None, font_path=None):
    fp = font_path or FONT
    """Texto estático centrado (frases pilar) con tamaños por línea escalables."""
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
            font = ImageFont.truetype(fp, sz)
            fonts.append(font)
            line_heights.append(int(sz * 1.28))

        total_h = sum(line_heights)
        y0 = int(H * 0.40) - total_h // 2
        y = y0
        for i, txt in enumerate(texts):
            font = fonts[i]
            w = md.textlength(txt, font=font)
            x = (W - w) / 2
            positions.append(([(txt, 0.0, 1e12, x)], y))
            y += line_heights[i]
        return fonts[0] if fonts else ImageFont.truetype(fp, global_size), positions

    size = start_size
    while size > min_size:
        font, positions = layout(size)
        fits = True
        scale = size / start_size if start_size else 1.0
        for i, txt in enumerate(texts):
            sz = max(32, int(base_sizes[i] * scale)) if base_sizes[i] else size
            f = ImageFont.truetype(fp, sz)
            if md.textlength(txt, font=f) > W - 160:
                fits = False
                break
        if positions:
            last_y = positions[-1][1]
            last_sz_val = base_sizes[-1] if base_sizes[-1] else size
            last_sz = max(32, int(last_sz_val * scale)) if base_sizes[-1] else size
            bottom = last_y + int(last_sz * 1.28)
        else:
            bottom = 0
        if fits and bottom <= int(H * 0.86):
            break
        size -= 4
    return font, positions


def _draw_text_bg(frame, positions, scheme, alpha=140):
    """Fondo semi-opaco detrás del bloque de texto karaoke."""
    if not positions:
        return
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    min_x, min_y = W, H
    max_x, max_y = 0, 0
    for row, y in positions:
        for item in row:
            word = item[0]
            x = item[3]
            f = item[4]
            wd = draw_ov.textlength(word, font=f)
            min_x = min(min_x, x)
            max_x = max(max_x, x + wd)
            ascent, descent = f.getmetrics()
            min_y = min(min_y, y)
            max_y = max(max_y, y + ascent + descent)
    bg_color = 0 if scheme.get("shadow", (0, 0, 0)) != (255, 255, 255) else 255
    draw_ov.rounded_rectangle(
        [min_x - 40, min_y - 20, max_x + 40, max_y + 20],
        radius=16, fill=(bg_color, bg_color, bg_color, alpha))
    frame.paste(Image.alpha_composite(
        frame.convert("RGBA"), overlay).convert("RGB"))


def _draw_karaoke(frame, font, positions, t, scheme):
    """Tipografía narrativa con 3 niveles de importancia.

    Niveles:
    - Normal (futura): dim, shadow 2px
    - Active (hablada): main, microescala 1.04×, glow 3px
    - Strong (énfasis): Inter-Black + accent, microescala 1.12×, glow 4px
    - Strong pasada: Inter-Black + accent, sin glow
    - Normal pasada: accent, sin glow
    """
    d = ImageDraw.Draw(frame)
    for row, y in positions:
        for item in row:
            w, ws, we, x = item[0], item[1], item[2], item[3]
            f = item[4] if len(item) > 4 else font
            custom_col = item[5] if len(item) > 5 else None
            emph = item[6] if len(item) > 6 else None

            is_active = ws <= t < we
            is_past = t >= we
            is_strong = emph == "strong"

            # --- COLOR ---
            if is_past:
                col = custom_col or scheme["accent"]
            elif is_active:
                col = scheme["main"]
            else:
                col = scheme["dim"]

            # --- FUENTE (strong siempre Inter-Black) ---
            if is_strong:
                f = ImageFont.truetype(
                    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
                    f.size)

            # --- MICROESCALA (solo durante activación) ---
            if is_active:
                elapsed = t - ws
                if is_strong:
                    scale = 1.0 + 0.12 * max(0, 1.0 - elapsed / 0.20)
                else:
                    scale = 1.0 + 0.04 * max(0, 1.0 - elapsed / 0.15)
                scaled_size = int(f.size * scale)
                f = ImageFont.truetype(f.path, scaled_size)

            # --- GLOW (solo durante activación) ---
            if is_active:
                glow_r = 4 if is_strong else 3
                for dx in range(-glow_r, glow_r + 1):
                    for dy in range(-glow_r, glow_r + 1):
                        if dx or dy:
                            d.text((x + dx, y + dy), w, font=f,
                                   fill=scheme["shadow"])
            else:
                d.text((x + 2, y + 2), w, font=f, fill=scheme["shadow"])

            d.text((x, y), w, font=f, fill=col)
    return frame


def _motion_frame(src, motion, progress, size):
    sw_, sh_ = src.size
    if motion == "zoom-in":
        s = 1.12 - 0.12 * progress
        cw, ch = int(W * s), int(H * s)
        x1 = (sw_ - cw) // 2
        y1 = (sh_ - ch) // 2
        return src.crop((x1, y1, x1 + cw, y1 + ch)).resize((W, H), Image.LANCZOS)
    if motion == "zoom-out":
        s = 1.0 + 0.12 * progress
        cw, ch = int(W * s), int(H * s)
        x1 = (sw_ - cw) // 2
        y1 = (sh_ - ch) // 2
        return src.crop((x1, y1, x1 + cw, y1 + ch)).resize((W, H), Image.LANCZOS)
    if motion in ("pan-right", "pan-left"):
        mx = int(sw_ * 0.05)
        xo = int(mx * (1 - 2 * progress))
        if motion == "pan-left":
            xo = -xo
        x1 = (sw_ - W) // 2 + xo
        y1 = (sh_ - H) // 2
        x1 = max(0, min(x1, sw_ - W))
        y1 = max(0, min(y1, sh_ - H))
        return src.crop((x1, y1, x1 + W, y1 + H)).copy()
    x1 = (sw_ - W) // 2
    y1 = (sh_ - H) // 2
    return src.crop((x1, y1, x1 + W, y1 + H)).copy()


def render_scene(timings, bg_img, wav, out_path, final=False, motion=None,
                 text_scheme="dark", fade=0.6, crf=20, preset="medium", tune=None,
                 static_lines=None, static_size=None, static_sizes=None, font_path=None,
                 trans=None, emphasis_map=None, pad_after=None):
    dur = probe_duration(wav)
    pa = PAD_AFTER if pad_after is None else pad_after
    total = PAD_BEFORE + dur + pa
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
        if tstyle == "slide":
            # Deslizamiento suave horizontal + dip-to-white (entra desde la derecha,
            # sale hacia la derecha). Lienzo blanco para integrarse con el fade.
            offset = int(W * (1 - p) * 0.35)
            canvas = white.copy()
            canvas.paste(frame, (offset, 0))
            return Image.blend(canvas, white, (1 - p) * 0.45)
        if tstyle == "slide-up":
            # Deslizamiento vertical suave: entra desde abajo hacia arriba + dip.
            offset = int(H * (1 - p) * 0.30)
            canvas = white.copy()
            canvas.paste(frame, (0, offset))
            return Image.blend(canvas, white, (1 - p) * 0.45)
        if tstyle == "fade-up":
            # Subida sutil (más corta) + dip-to-white.
            offset = int(H * (1 - p) * 0.12)
            canvas = white.copy()
            canvas.paste(frame, (0, offset))
            return Image.blend(canvas, white, (1 - p) * 0.55)
        if tstyle == "blur-in":
            # Entra desenfocado hasta foco, fundiendo a blanco.
            r = int((1 - p) * 9)
            f = frame.filter(ImageFilter.GaussianBlur(radius=r)) if r > 0 else frame
            return Image.blend(f, white, (1 - p) * 0.4)
        if tstyle == "zoom-fade":
            # Entra creciendo levemente desde menor escala + dip-to-white.
            z = 1.0 + (1 - p) * 0.08
            nw, nh = max(1, int(W * z)), max(1, int(H * z))
            f = frame.resize((nw, nh), Image.LANCZOS)
            canvas = white.copy()
            canvas.paste(f, ((W - nw) // 2, (H - nh) // 2))
            return Image.blend(canvas, white, (1 - p) * 0.5)
        if tstyle == "wipe-soft":
            # Cortinilla suave de izquierda a derecha + dip leve.
            cut = int(W * p)
            canvas = white.copy()
            canvas.paste(frame.crop((0, 0, cut, H)), (0, 0))
            return Image.blend(canvas, white, (1 - p) * 0.35)
        if tstyle == "fade-soft":
            # Fundido suave y tenue (más sutil que el fade normal).
            return Image.blend(frame, white, (1 - p) * 0.4)
        # fade (dip-to-white) por defecto
        return Image.blend(frame, white, (1 - p) * 0.85)

    if motion:
        src = Image.open(bg_img).convert("RGB")
        sw, sh = int(W * 1.18), int(H * 1.18)
        src = src.resize((sw, sh), Image.LANCZOS)
    else:
        bg = Image.open(bg_img).convert("RGB").copy()
        src = None

    def get_frame(fi):
        if src is None:
            return bg.copy()
        t = fi / FPS
        progress = _ease(t / total if total > 0 else 0)
        return _motion_frame(src, motion, progress, None)

    if static_lines:
        font, positions = _layout_static(static_lines, final, static_size or 96,
                                         line_sizes=static_sizes, font_path=font_path)
    else:
        font, positions = _layout_karaoke(timings, final,
                                          emphasis_map=emphasis_map)

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
        if fi == 0 and not static_lines:
            _draw_text_bg(frame, positions, scheme)
        _draw_karaoke(frame, font, positions, t, scheme)
        frame = apply_transition(frame, t)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def render_scene_video(timings, video_path, wav, out_path, final=False,
                       text_scheme="dark", darken=0.20, fade=0.6,
                       static_lines=None, static_size=None, static_sizes=None, font_path=None,
                       trans=None, emphasis_map=None, pad_after=None):
    """Escena con b-roll de video horizontal de fondo (loop)."""
    dur = probe_duration(wav)
    pa = PAD_AFTER if pad_after is None else pad_after
    total = PAD_BEFORE + dur + pa
    frames = int(math.ceil(total * FPS))
    scheme = TEXT_SCHEMES.get(text_scheme, TEXT_SCHEMES["dark"])

    vf = ("scale={0}:{1}:force_original_aspect_ratio=increase,"
          "crop={0}:{1},".format(W, H) +
          f"eq=brightness=-{darken:.2f}:saturation=0.9,fps={FPS}")
    dec = subprocess.Popen(
        ["ffmpeg", "-y", "-i", video_path,
         "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    if static_lines:
        font, positions = _layout_static(static_lines, final, static_size or 96,
                                         line_sizes=static_sizes, font_path=font_path)
    else:
        font, positions = _layout_karaoke(timings, final,
                                          emphasis_map=emphasis_map)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-af", f"adelay={int(PAD_BEFORE*1000)}:all=1,apad",
        "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    frame_size = W * H * 3
    white = Image.new("RGB", (W, H), (255, 255, 255))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    trans = trans or {}
    tstyle = trans.get("style", "fade")
    tdur = trans.get("dur", fade)

    def apply_transition(frame, t):
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
        if tstyle == "slide":
            # Deslizamiento suave horizontal + dip-to-white (entra desde la derecha,
            # sale hacia la derecha). Lienzo blanco para integrarse con el fade.
            offset = int(W * (1 - p) * 0.35)
            canvas = white.copy()
            canvas.paste(frame, (offset, 0))
            return Image.blend(canvas, white, (1 - p) * 0.45)
        # fade (dip-to-white) por defecto
        return Image.blend(frame, white, (1 - p) * 0.85)

    last_frame = None
    for fi in range(frames):
        t = fi / FPS
        raw = dec.stdout.read(frame_size)
        if len(raw) == frame_size:
            frame = Image.frombytes("RGB", (W, H), raw)
            last_frame = frame
        else:
            # El clip de fondo terminó (más corto que la escena): congelar el
            # último frame en vez de hacer loop/brusco. El dip-to-white de
            # transición sigue aplicándose normal sobre el frame quieto.
            if last_frame is None:
                dec.stdout.close()
                dec.terminate()
                raise RuntimeError(f"video de fondo vacío: {video_path}")
            frame = last_frame
        if fi == 0 and not static_lines:
            _draw_text_bg(frame, positions, scheme)
        _draw_karaoke(frame, font, positions, t, scheme)
        frame = apply_transition(frame, t)
        proc.stdin.write(frame.tobytes())
    dec.stdout.close()
    dec.terminate()
    dec.wait()
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {out_path}")
    return out_path


def concat(clips, out_path):
    """Unifica escenas y FIJE CFR 30 (evita frame rate variable que marca
    kdenlive como VFR). El `-c copy` de base.concat conserva timestamps
    irregulares; aca re-encoda el video final a 30fps constante.
    """
    lst = os.path.join(base.TMP, "concat_yt.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
         "-c:a", "copy", "-map_metadata", "-1",
         "-movflags", "+faststart", out_path])
    return out_path
