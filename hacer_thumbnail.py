#!/usr/bin/env python3
"""Generador de miniaturas del canal siguiendo el skill diseno-grafico.

Diseño full-bleed (imagen a pantalla completa, sin cajas):
- La imagen ocupa TODO el canvas sin estirar (cover).
- Banda oscura degradada en el tercio inferior para legibilidad del texto.
- Texto UNA línea, CENTRADO, auto-ajustado al ancho (nunca se corta).
- Fuente display bold (Anton), 1 palabra acento en color, outline negro.
- Contraste min 4.5:1; evitar rojo (se mimetiza con la UI de YouTube).
- Zonas seguras: texto en el tercio central-inferior, no en el borde.

Uso:
    python3 hacer_thumbnail.py <imagen.jpg> <out.jpg> --texto "NO APURES" --acento "APURES" \
        --sub "la calma te adelanta" --aspecto 16:9|9:16 --color FFC93C
"""
import argparse
import json
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))

# Tokens de marca (fuente única de verdad: assets/brand/brand.config.json)
with open(os.path.join(ROOT, "assets", "brand", "brand.config.json")) as _bf:
    _BRAND = json.load(_bf)
_BRAND_COLORS = {k: v["hex"] if isinstance(v, dict) else v
                 for k, v in _BRAND.get("colors", {}).items()}

_FONT_CANDIDATES = [
    # La identidad manda primero (tokens): Anton es el título de marca.
    os.path.expanduser("~/.local/share/fonts/Anton-Regular.ttf"),
    os.path.expanduser("~/.local/share/fonts/BebasNeue-Regular.ttf"),
    os.path.expanduser("~/.local/share/fonts/Montserrat-ExtraBold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    os.path.join(ROOT, "DejaVuSerif-Bold.ttf"),
]


def _font(size):
    for p in _FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _hex(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def _crop_to(pil_img, aspect):
    """Recorta (cover) la imagen a la proporción pedida."""
    target = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1.0}[aspect]
    w, h = pil_img.size
    if w / h > target:
        nw = int(h * target)
        x0 = (w - nw) // 2
        pil_img = pil_img.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / target)
        y0 = (h - nh) // 2
        pil_img = pil_img.crop((0, y0, w, y0 + nh))
    size = {"16:9": (1280, 720), "9:16": (1080, 1920), "1:1": (1080, 1080)}[aspect]
    return pil_img.resize(size, Image.LANCZOS)


def _char_w(draw, ch, font, ow=0):
    """Ancho visual de un glifo INCLUYENDO su trazo."""
    bb = draw.textbbox((0, 0), ch, font=font, stroke_width=ow)
    return bb[2] - bb[0]


def _text_width(draw, text, font, tracking=0, ow=0):
    """Ancho del texto incluyendo tracking (interletrado) y trazo.
    Misma medida que el avance del dibujo en _text_outline (si no, el
    centrado horizontal queda desplazado y el texto se corta al borde)."""
    if not text:
        return 0
    w = sum(_char_w(draw, ch, font, ow) for ch in text)
    if len(text) > 1:
        w += tracking * (len(text) - 1)
    return w


def _fit_two_lines(draw, words, start_size, max_w, tracking=0, ow=0):
    """Mejor ruptura de 2 líneas (doctrina: el título es forma gráfica).
    Elige el corte que maximiza el tamaño común de ambas líneas."""
    best = None
    for i in range(1, len(words)):
        l1, l2 = " ".join(words[:i]), " ".join(words[i:])
        s1 = _fit_font(draw, l1, start_size, max_w, tracking=0, ow=ow).size
        s2 = _fit_font(draw, l2, start_size, max_w, tracking=0, ow=ow).size
        if best is None or min(s1, s2) > best[0]:
            best = (min(s1, s2), l1, l2)
    return best  # (size, linea1, linea2)


def _fit_font(draw, text, start_size, max_width, tracking=0, ow=0, direction=-1):
    """Reduce el tamaño de fuente hasta que el texto entre en max_width."""
    size = start_size
    while size > 40:
        f = _font(size)
        if _text_width(draw, text, f, tracking, ow) <= max_width:
            return f
        size += direction * max(4, int(start_size * 0.04))
    return _font(40)


def _text_outline(draw, xy, text, font, fill, outline_w=None, tracking=0):
    """Texto con trazo grueso (negro cálido de marca) + sombra paralela."""
    x, y = xy
    ow = outline_w or max(4, int(font.size * 0.09))
    shadow = _hex(_BRAND_COLORS.get("NEUTRAL", "#14100D"))
    if tracking:
        # Centrado vertical por CAJA VISUAL real (no por métricas del ascensor:
        # en Anton el ascensor es grande y el visor chico, lo que bajaba el
        # título ~100px y lo montaba sobre el subtítulo).
        tw = _text_width(draw, text, font, tracking)
        bb = draw.textbbox((0, 0), text, font=font)
        v_center = (bb[1] + bb[3]) / 2
        for layer in ((x + ow // 2, y + ow // 2, shadow), (x, y, fill)):
            lx = layer[0] - tw / 2
            ly = layer[1] - v_center
            for i, ch in enumerate(text):
                draw.text((lx, ly), ch, font=font, fill=layer[2],
                          stroke_width=ow, stroke_fill=shadow)
                # avanzar por el MISMO ancho con trazo que midió _text_width
                lx += _char_w(draw, ch, font, ow) + tracking
    else:
        draw.text((x + ow // 2, y + ow // 2), text, font=font, fill=shadow, anchor="mm")
        draw.text((x, y), text, font=font, fill=fill, anchor="mm",
                  stroke_width=ow, stroke_fill=shadow)


def _bottom_gradient(canvas, start_frac=0.52, max_alpha=170):
    """Degradado oscuro en el tercio inferior para legibilidad del texto."""
    W, H = canvas.size
    y0 = int(H * start_frac)
    overlay = Image.new("RGBA", (W, H - y0), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(H - y0):
        alpha = int(max_alpha * (i / (H - y0)) ** 1.4)
        od.line([(0, i), (W, i)], fill=(0, 0, 0, alpha))
    canvas.paste(overlay, (0, y0), overlay)
    return canvas


def make_thumbnail(image_path, out_path, texto, acento=None, sub=None,
                   aspect="9:16", accent_color=None, text_frac=0.60,
                   tracking=-0.02):
    """Full-bleed: imagen completa + texto centrado auto-ajustado.
    accent_color None → token ACCENT de marca."""
    if accent_color is None:
        accent_color = _BRAND_COLORS.get("ACCENT", "#D9A441")
    img = Image.open(image_path).convert("RGB")
    canvas = _crop_to(img, aspect).convert("RGBA")
    W, H = canvas.size

    canvas = _bottom_gradient(canvas)
    draw = ImageDraw.Draw(canvas, "RGBA")

    words = texto.strip().upper().split()
    line = " ".join(words)
    max_w = int(W * 0.86)
    # El outline escala con el tamaño FINAL de fuente (convergencia en 2
    # pasadas). Antes era fijo (9% del tamaño inicial): al contar el trazo
    # en el ancho, la fuente colapsaba al mínimo.
    font_main = _fit_font(draw, line, int(H * 0.15), max_w, tracking=0,
                          ow=max(4, int(H * 0.15 * 0.09)))
    for _ in range(2):
        ow = max(4, int(font_main.size * 0.09))
        trk_main = int(font_main.size * tracking)
        font_main = _fit_font(draw, line, font_main.size, max_w,
                              tracking=trk_main, ow=ow)

    # DOMINANCIA (jerarquía primero): 1 línea solo si el título queda grande
    # (>=11% de la altura); si no, 2 líneas balanceadas ("forma gráfica").
    lines = [line]
    if font_main.size < H * 0.11 and len(words) > 1:
        size2, l1, l2 = _fit_two_lines(
            draw, words, int(H * 0.15), max_w,
            ow=max(4, int(H * 0.15 * 0.09)))
        for _ in range(2):
            ow = max(4, int(size2 * 0.09))
            trk2 = int(size2 * tracking)
            s1 = _fit_font(draw, l1, size2, max_w, tracking=trk2, ow=ow).size
            s2 = _fit_font(draw, l2, size2, max_w, tracking=trk2, ow=ow).size
            size2 = min(s1, s2)
        font_main = _font(size2)
        lines = [l1, l2]
    trk_main = int(font_main.size * tracking)

    text_y = int(H * text_frac)
    if acento and any(w == acento.upper() for w in words):
        color = _hex(accent_color)
    else:
        color = (255, 255, 255, 255)
    if len(lines) == 1:
        _text_outline(draw, (W // 2, text_y), lines[0], font_main, color,
                      outline_w=ow, tracking=trk_main)
        block_bottom = text_y + font_main.size // 2
    else:
        paso = int(font_main.size * 1.08)
        y1 = text_y - paso // 2
        _text_outline(draw, (W // 2, y1), lines[0], font_main, color,
                      outline_w=ow, tracking=trk_main)
        _text_outline(draw, (W // 2, y1 + paso), lines[1], font_main, color,
                      outline_w=ow, tracking=trk_main)
        block_bottom = y1 + paso + font_main.size // 2

    if sub:
        # El subtítulo NUNCA supera el 72% del título (jerarquía garantizada).
        sub_start = min(int(H * 0.055), int(font_main.size * 0.72))
        font_sub = _fit_font(draw, sub, sub_start, max_w, tracking=0, ow=3)
        # Debajo del BORDE INFERIOR del bloque del título. Antes: 0.82*size
        # desde el centro → el subtítulo tapaba la mitad del título.
        sub_y = block_bottom + int(font_main.size * 0.14) + font_sub.size // 2
        sub_color = _hex(_BRAND_COLORS.get("SECONDARY", "#FFF7E8"))
        _text_outline(draw, (W // 2, sub_y),
                      sub, font_sub, sub_color, outline_w=3)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    canvas.convert("RGB").save(out_path, "JPEG", quality=92)
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("imagen")
    ap.add_argument("out")
    ap.add_argument("--texto", required=True)
    ap.add_argument("--acento", default=None)
    ap.add_argument("--sub", default=None)
    ap.add_argument("--aspecto", default="9:16", choices=["16:9", "9:16", "1:1"])
    ap.add_argument("--color", default=_BRAND_COLORS.get("ACCENT", "D9A441").lstrip("#"),
                    help="color del acento (default: token ACCENT de marca)")
    ap.add_argument("--texto-y", type=float, default=0.60,
                    help="posición vertical del texto (0-1)")
    args = ap.parse_args()
    print(make_thumbnail(args.imagen, args.out, args.texto, args.acento,
                         args.sub, args.aspecto, args.color, args.texto_y))