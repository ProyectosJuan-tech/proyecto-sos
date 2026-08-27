#!/usr/bin/env python3
"""Miniatura 16:9 estilo ChatGPT con iconos UI (suscribir/like/comentar/campanita/compartir).

Uso:
    python3 miniatura_con_iconos.py <imagen_base> <out.jpg> [--titulo "5 SEÑALES"] [--acento SEÑALES] [--sub "QUE CONFUNDÍS CON CARIÑO"]
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageOps, ImageFont

GOLD = (217, 155, 40, 255)
IVORY = (240, 236, 226, 255)
BLACK = (8, 9, 9, 255)
YELLOW = (192, 132, 30, 255)
RED = (192, 24, 24, 255)
WHITE = (245, 245, 245, 255)

FONT_DIR = os.path.join(os.path.expanduser("~"), ".local/share/fonts")
ANTON = os.path.join(FONT_DIR, "Anton-Regular.ttf")
INTER = os.path.join(FONT_DIR, "Inter%5Bopsz%2Cwght%5D.ttf")
MATERIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "brand", "cta", "fonts", "MaterialIcons-Regular.ttf")

# Glifos oficiales de la UI de YouTube (Material Icons, Apache-2.0)
GLYPHS = {
    "play": 0xE037,      # play_arrow
    "like": 0xE8DC,      # thumb_up
    "bubble": 0xE0B9,    # comment (burbuja de comentario)
    "bell": 0xE7F4,      # notifications (campanita)
    "link": 0xE80D,      # share (compartir)
}


def draw_icon(im, cx, cy, radius, kind, color):
    """Dibuja un botón circular con glifo Material Icons real de YouTube UI.
    im debe estar en modo RGBA."""
    d = ImageDraw.Draw(im)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    glyph = GLYPHS[kind]
    gsize = int(radius * 1.15)
    f = ImageFont.truetype(MATERIAL, gsize)
    d.text((cx, cy), chr(glyph), font=f, fill=WHITE, anchor="mm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imagen")
    ap.add_argument("out")
    ap.add_argument("--titulo", default="5 SEÑALES")
    ap.add_argument("--acento", default=None, help="palabra en dorado dentro del titulo")
    ap.add_argument("--sub", default="")
    ap.add_argument("--girar-sujeto", action="store_true", help="flip horizontal")
    ap.add_argument("--sujeto-x", type=float, default=0.72, help="posicion x de la cara (0-1)")
    ap.add_argument("--sujeto-y", type=float, default=0.45, help="posicion y de la cara (0-1)")
    ap.add_argument("--sujeto-r", type=float, default=0.26, help="radio de la cara en ancho (0-1)")
    args = ap.parse_args()

    W, H = 1280, 720
    src = Image.open(args.imagen).convert("RGB")

    # escalar a cubrir 16:9 y recortar ventana centrada en el sujeto
    scale = max(W / src.width, H / src.height) * 1.35
    w2, h2 = int(src.width * scale), int(src.height * scale)
    img = src.resize((w2, h2), Image.LANCZOS)
    if args.girar_sujeto:
        img = ImageOps.mirror(img)
    cx = int(w2 * args.sujeto_x)
    offx = int(cx - W * args.sujeto_x)
    offx = max(0, min(offx, w2 - W))
    offy = int((h2 - H) / 2)
    canvas = img.crop((offx, offy, offx + W, offy + H)).copy()

    # degradado izquierdo para el texto (sin tocar franja iconos)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(W):
        t = x / (W * 0.62)
        t = 0 if t < 0 else (1 if t > 1 else t)
        od.line([(x, 0), (x, H)], fill=(0, 0, 0, int(235 * (1 - t) ** 1.4)))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # --- HEADLINE ---
    words = args.titulo.split()
    parts = []
    for w in words:
        if args.acento and w.upper() == args.acento.upper():
            parts.append((w, GOLD))
        else:
            parts.append((w, IVORY))
    # juntar palabras en máximo 2 líneas
    if len(words) <= 2:
        lines = [parts]
    else:
        lines = [parts[:2], parts[2:]]
    y_top = int(H * 0.06)
    max_w = int(W * 0.62)
    for li, line in enumerate(lines):
        line_txt = " ".join(w for w, _ in line)
        fsize = 135
        f = ImageFont.truetype(ANTON, fsize)
        while draw.textlength(line_txt, font=f) > max_w and fsize > 30:
            fsize -= 4
            f = ImageFont.truetype(ANTON, fsize)
        x = int(W * 0.05)
        y = y_top + li * int(fsize * 1.0)
        for w, c in line:
            draw.text((x, y), w, font=f, fill=c)
            x += int(draw.textlength(w + " ", font=f) * 0.94)

    # --- SUB ---
    if args.sub:
        fsub = ImageFont.truetype(INTER, 44)
        while draw.textlength(args.sub, font=fsub) > max_w and fsub.size > 20:
            fsub = ImageFont.truetype(INTER, fsub.size - 2)
        y_sub = int(H * 0.30)
        draw.text((int(W * 0.05) + 2, y_sub + 2), args.sub, font=fsub, fill=BLACK)
        draw.text((int(W * 0.05), y_sub), args.sub, font=fsub, fill=(220, 205, 170, 255))

    # --- FRANJA DE ICONOS ---
    icons = [
        ("SUSCRIBITE", RED, "play"),
        ("DALE LIKE", YELLOW, "like"),
        ("COMENTÁ", YELLOW, "bubble"),
        ("ACTIVÁ LA CAMPANITA", YELLOW, "bell"),
        ("COMPARTÍ", YELLOW, "link"),
    ]
    band_h = int(H * 0.26)
    band_y = H - band_h
    # oscurecer la franja para los iconos
    bf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bf)
    bd.rectangle([0, band_y, W, H], fill=(0, 0, 0, 225))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), bf)
    draw = ImageDraw.Draw(canvas)

    n = len(icons)
    slot_w = W / n
    icon_r = int(band_h * 0.20)
    cy = band_y + int(band_h * 0.60)
    fcap = ImageFont.truetype(ANTON, int(icon_r * 0.72))
    for i, (label, color, kind) in enumerate(icons):
        cx = int(slot_w * (i + 0.5))
        draw_icon(canvas, cx, cy, icon_r, kind, color)
        # etiqueta ARRIBA del ícono (como en ChatGPT)
        txt = label
        tw = draw.textlength(txt, font=fcap)
        while tw > slot_w * 0.98 and fcap.size > 14:
            fcap = ImageFont.truetype(ANTON, fcap.size - 2)
            tw = draw.textlength(txt, font=fcap)
        tx = int(cx - tw / 2)
        ty = int(cy - icon_r - fcap.size * 1.7)
        draw.text((tx + 2, ty + 2), txt, font=fcap, fill=(0, 0, 0, 255))
        draw.text((tx, ty), txt, font=fcap, fill=WHITE)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    canvas.convert("RGB").save(args.out, "JPEG", quality=92)
    print("OK", args.out)


if __name__ == "__main__":
    main()
