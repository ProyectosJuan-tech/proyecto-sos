#!/usr/bin/env python3
"""Motor de estilos visuales estilo Golpo AI, con Pillow + numpy.

Convierte cualquier imagen (foto) en looks ilustrados:
chalkboard, whiteboard, sharpie, modern_minimal, editorial,
playful, technical, illustration.

Además incluye el efecto "mano dibujando" (pen-in-hand):
line-art + revelado progresivo con un stylus siguiendo el trazo.

Uso:
    img = apply_style(img, "sharpie", W=1080, H=1920)
    bg, strokes, order = build_draw(img, style="whiteboard")
    mask = reveal_mask(order, progress)          # np.uint8 (H,W)
    frame = draw_frame(bg, strokes, mask)        # PIL RGB
    frame = compose_stylus(frame, x, y, "right")
"""
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw, ImageFilter, ImageOps

W, H = 1080, 1920
SW, SH = W // 2, H // 2          # resolución de procesado (look ilustrado)
DRAW_BANDS = 10                  # bandas del revelado serpenteante

_LIGHT = {
    "whiteboard", "sharpie", "modern_minimal",
    "editorial", "playful", "illustration",
}
_DRAW_OK = {
    "whiteboard", "chalkboard", "sharpie", "technical",
    "modern_minimal", "editorial", "playful", "illustration",
}
_BG = {
    "whiteboard": (255, 255, 255), "chalkboard": (22, 26, 30),
    "technical": (18, 38, 68), "sharpie": (255, 255, 255),
    "modern_minimal": (255, 255, 255), "editorial": (250, 245, 235),
    "playful": (255, 255, 255), "illustration": (255, 251, 243),
}


def crop_9_16(img, w=W, h=H):
    """Recorta centrado a 9:16 y redimensiona a (w, h)."""
    iw, ih = img.size
    target = w / h
    if iw / ih > target:
        nw = int(ih * target)
        x = (iw - nw) // 2
        img = img.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / target)
        y = (ih - nh) // 2
        img = img.crop((0, y, iw, y + nh))
    return img.resize((w, h), Image.LANCZOS)


def is_light(style):
    """True si el fondo del estilo es claro (texto oscuro)."""
    return style in _LIGHT


def _edge_mask(gray, blur=1.2, thr=48, thicken=0):
    """Máscara de trazos: blanco = línea, negro = fondo."""
    g = gray.filter(ImageFilter.GaussianBlur(blur))
    e = g.filter(ImageFilter.FIND_EDGES)
    e = ImageOps.autocontrast(e)
    m = e.point(lambda v: 255 if v > thr else 0)
    if thicken >= 3 and thicken % 2 == 1:
        m = m.filter(ImageFilter.MaxFilter(thicken))
    return m


def _fill_gray(gray, n, low, high):
    """Pósteriza en gris: valor bajo -> low, alto -> high (ints 0-255)."""
    q = gray.quantize(n).convert("L")
    thr = 255 * (n - 1) // (2 * n)
    return q.point(lambda v: high if v > thr else low)


def _lum(c):
    return int(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])


def _speckle(alpha=90):
    """Grano de tiza/lápiz: máscara L con manchas claras."""
    n = Image.effect_noise((SW, SH), 60).convert("L")
    return n.point(lambda v: 255 if v < alpha else 0)


def _strokes(mask, color, speckle=False):
    """Capa RGBA de trazos del color dado, con grano opcional."""
    r, g, b = color
    a = mask
    if speckle:
        sp = _speckle()
        a = Image.composite(Image.new("L", (SW, SH), 255), mask, sp)
    r_im = Image.new("L", mask.size, r)
    g_im = Image.new("L", mask.size, g)
    b_im = Image.new("L", mask.size, b)
    return Image.merge("RGBA", (r_im, g_im, b_im, a))


def _final(im, unsharp=2):
    im = im.resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=unsharp, threshold=3))
    return im.convert("RGB")


def _line_art(img, color, bg, fill, thicken, speckle):
    """Imagen línea-art con relleno suave: (RGB final, strokes RGBA small)."""
    g = img.convert("L").resize((SW, SH), Image.LANCZOS)
    m = _edge_mask(g, thicken=thicken)
    base = Image.new("RGB", (SW, SH), bg)
    fl = _fill_gray(g, 2, _lum(fill), _lum(bg))
    base = Image.composite(fl, base, m)
    strokes = _strokes(m, color, speckle=speckle)
    art = Image.alpha_composite(base.convert("RGBA"), strokes).convert("RGB")
    return _final(art), strokes.resize((W, H), Image.NEAREST)


def _color_art(img, style):
    """Look ilustrado a color: relleno cuantizado + contornos."""
    g = img.convert("L").resize((SW, SH), Image.LANCZOS)
    sm = img.resize((SW, SH), Image.LANCZOS)
    if style == "sharpie":
        fill = _fill_color(sm, 6)
        m = _edge_mask(g, blur=0.8, thr=40, thicken=3)
        strokes = _strokes(m, (18, 18, 22))
    elif style == "modern_minimal":
        fl = _fill_color(sm, 3)
        fl = ImageEnhance.Color(fl).enhance(0.7)
        fl = ImageEnhance.Brightness(fl).enhance(1.12)
        fill = fl
        m = _edge_mask(g, blur=1.0, thr=52, thicken=0)
        strokes = _strokes(m, (72, 72, 78))
    elif style == "editorial":
        fl = _fill_color(sm, 6)
        fl = ImageEnhance.Contrast(fl).enhance(1.15)
        fl = ImageEnhance.Color(fl).enhance(1.1)
        fill = fl
        m = _edge_mask(g, blur=0.9, thr=44, thicken=1)
        strokes = _strokes(m, (52, 38, 32))
    elif style == "playful":
        fl = _fill_color(sm, 8)
        fl = ImageEnhance.Color(fl).enhance(1.35)
        fl = ImageEnhance.Brightness(fl).enhance(1.05)
        fill = fl
        m = _edge_mask(g, blur=0.8, thr=40, thicken=2)
        strokes = _strokes(m, (255, 255, 255))
    elif style == "illustration":
        fl = _fill_color(sm, 5)
        fl = ImageEnhance.Color(fl).enhance(1.05)
        fill = fl
        m = _edge_mask(g, blur=0.9, thr=46, thicken=1)
        strokes = _strokes(m, (84, 56, 44))
    else:
        raise ValueError(f"estilo desconocido: {style}")

    art = Image.alpha_composite(fill.convert("RGBA"), strokes).convert("RGB")
    return _final(art), strokes


def _fill_color(img, n):
    return img.quantize(n, method=Image.MEDIANCUT).convert("RGB")


def apply_style(img, style, w=W, h=H):
    """Convierte una imagen en el look ilustrado pedido (RGB)."""
    img = crop_9_16(img, w, h)
    if style in ("whiteboard", "chalkboard", "technical"):
        art, _ = _line_art(
            img,
            color={"whiteboard": (40, 40, 45), "chalkboard": (236, 239, 243),
                   "technical": (198, 228, 255)}[style],
            bg=_BG[style],
            fill={"whiteboard": (240, 240, 242), "chalkboard": (70, 76, 84),
                  "technical": (34, 60, 100)}[style],
            thicken={"whiteboard": 1, "chalkboard": 1, "technical": 0}[style],
            speckle=(style == "chalkboard"),
        )
        return art
    if style in ("sharpie", "modern_minimal", "editorial", "playful", "illustration"):
        art, _ = _color_art(img, style)
        return art
    raise ValueError(f"estilo desconocido: {style}")


def build_draw(img, style="whiteboard", w=W, h=H):
    """Prepara el efecto dibujo: fondo, trazos y matriz de orden.

    Devuelve (bg np.uint8 (H,W,3), strokes np.uint8 (H,W,4),
    order np.float64 (H,W) en [0,1)).
    """
    if style not in _DRAW_OK:
        style = "whiteboard"
    img = crop_9_16(img, w, h)
    conf = {
        "whiteboard": dict(color=(35, 35, 40), fill=(78, 78, 86),
                           high=(168, 168, 174), thicken=1),
        "chalkboard": dict(color=(238, 242, 248), fill=(122, 128, 138),
                           high=(232, 236, 242), thicken=1),
        "technical": dict(color=(198, 228, 255), fill=(42, 70, 110),
                          high=(122, 152, 200), thicken=0),
        "sharpie": dict(color=(18, 18, 22), fill=(232, 232, 236),
                        high=(255, 255, 255), thicken=3),
        "modern_minimal": dict(color=(58, 58, 66), fill=(226, 226, 230),
                               high=(255, 255, 255), thicken=0),
        "editorial": dict(color=(52, 38, 32), fill=(222, 212, 196),
                          high=(250, 246, 238), thicken=1),
        "playful": dict(color=(232, 72, 72), fill=(242, 214, 206),
                        high=(252, 240, 235), thicken=2),
        "illustration": dict(color=(84, 56, 44), fill=(206, 190, 170),
                             high=(246, 240, 230), thicken=1),
    }[style]
    c = conf
    g = img.convert("L").resize((SW, SH), Image.LANCZOS)
    m = _edge_mask(g, blur=1.2, thr=58, thicken=c["thicken"])
    fl = _fill_gray(g, 2, _lum(c["fill"]), _lum(c["high"]))
    fl_soft = fl.point(lambda v: int(v * 0.4))
    ink = Image.composite(Image.new("L", (SW, SH), 255), fl_soft, m)
    strokes = _strokes(ink, c["color"], speckle=(style == "chalkboard"))

    bg_np = np.asarray(Image.new("RGB", (W, H), _BG[style]), dtype=np.uint8)
    st_np = np.asarray(strokes.resize((W, H), Image.NEAREST), dtype=np.uint8)
    order = _trace_order(m)
    order_img = Image.fromarray((order * 65535.0).astype(np.uint16),
                                mode="I;16").resize((W, H), Image.LANCZOS)
    return bg_np, st_np, np.asarray(order_img, np.float64) / 65535.0


def _cc_labels(mask):
    """Etiqueta componentes conexas (8-vecinos). Devuelve (labels int32, n)."""
    h, w = mask.shape
    labels = np.zeros((h, w), np.int32)
    ys, xs = np.where(mask)
    pix = set(zip(ys.tolist(), xs.tolist()))
    from collections import deque

    lab = 0
    while pix:
        lab += 1
        seed = pix.pop()
        dq = deque([seed])
        while dq:
            y, x = dq.popleft()
            labels[y, x] = lab
            for ny in range(y - 1, y + 2):
                for nx in range(x - 1, x + 2):
                    if (ny, nx) in pix:
                        pix.remove((ny, nx))
                        dq.append((ny, nx))
    return labels, lab


def _bfs(start, pix):
    """Distancias (BFS) desde start dentro del conjunto de píxeles pix."""
    from collections import deque

    dist = {start: 0}
    dq = deque([start])
    while dq:
        cur = dq.popleft()
        y, x = cur
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                n = (ny, nx)
                if n != cur and n in pix and n not in dist:
                    dist[n] = dist[cur] + 1
                    dq.append(n)
    return dist


def _dilate_order(order, radius):
    """Propaga el orden de las líneas a vecinos (grosor + relleno cercano)."""
    a = order.copy()
    h, w = a.shape
    for _ in range(radius):
        p = np.pad(a, 1, constant_values=-2.0)
        cand = np.maximum.reduce([
            np.roll(p, -1, 0), np.roll(p, 1, 0),
            np.roll(p, -1, 1), np.roll(p, 1, 1),
            np.roll(np.roll(p, -1, 0), -1, 1), np.roll(np.roll(p, -1, 0), 1, 1),
            np.roll(np.roll(p, 1, 0), -1, 1), np.roll(np.roll(p, 1, 0), 1, 1),
        ])[1:-1, 1:-1]
        a = np.where((a >= 0) | (cand < 0), a, cand)
    return a


def _trace_order(mask, line_frac=0.78, fill_bands=40, min_comp=8):
    """Orden de dibujo a mano alzada: cada trazo se dibuja desde un extremo.

    Las líneas (bordes) se trazan siguiendo el contorno (BFS por componente,
    componentes en orden serpenteante por posición). El relleno restante se
    lava suavemente al final. Devuelve matriz float64 en [0,1).
    """
    from collections import deque

    m = np.asarray(mask, dtype=bool)
    h, w = m.shape
    order = np.full((h, w), -1.0, np.float64)

    labels, n = _cc_labels(m)
    if n == 0:
        return np.zeros((h, w), np.float64)

    flat = labels.ravel()
    ys = np.arange(h)[:, None].repeat(w, axis=1).ravel()
    xs = np.arange(w)[None, :].repeat(h, axis=0).ravel()
    cnt = np.bincount(flat, minlength=n + 1)
    sumy = np.bincount(flat, minlength=n + 1, weights=ys)
    sumx = np.bincount(flat, minlength=n + 1, weights=xs)

    idx = np.argsort(flat, kind="stable")
    uniq, starts = np.unique(flat[idx], return_index=True)

    items = []
    for lab, start in zip(uniq, starts):
        if lab == 0 or cnt[lab] < 1:
            continue
        c = cnt[lab]
        items.append((sumy[lab] / c, sumx[lab] / c, lab, c))
    block = h // 14
    items.sort(key=lambda it: (int(it[0] // block),
                               it[1] if (int(it[0] // block) % 2 == 0) else -it[1]))

    total = int(np.bincount(flat)[1:].sum())
    acc = 0.0
    for my, mx, lab, c in items:
        frac = c / total
        start = starts[np.searchsorted(uniq, lab)]
        ys_g = ys[idx[start:start + c]]
        xs_g = xs[idx[start:start + c]]
        if c < min_comp:
            order[ys_g, xs_g] = acc + frac * 0.5
            acc += frac
            continue
        pix = set(zip(ys_g.tolist(), xs_g.tolist()))
        p0 = next(iter(pix))
        d0 = _bfs(p0, pix)
        q = max(d0, key=d0.get)
        d1 = _bfs(q, pix)
        dmax = max(float(v) for v in d1.values())
        dmax = max(dmax, 1.0)
        for y, x in pix:
            order[y, x] = acc + (d1[(y, x)] / dmax) * frac
        acc += frac

    order = _dilate_order(order, radius=4)
    order = np.where(order >= 0, np.clip(order, 0.0, line_frac), order)

    rest = order < 0
    yg, xg = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    fill = 1.0 - (yg / h)                       # relleno de abajo hacia arriba
    if fill_bands > 0:
        bw = w / fill_bands
        bx = xg / (w - 1)
        within = np.where(((xg / bw).astype(int)) % 2 == 0, bx, 1.0 - bx)
        fill = np.clip(fill * 0.5 + within * 0.5, 0.0, 1.0)
    order[rest] = line_frac + (1.0 - line_frac) * 0.98 * fill[rest]
    return np.clip(order, 0.0, 1.0 - 1e-9)


def reveal_mask(order, progress, soft=14.0):
    """Máscara uint8 (H,W): 255 = dibujado, 0 = aún no."""
    a = np.clip((progress - order) * soft, 0.0, 1.0)
    return (a * 255.0).astype(np.uint8)


def draw_frame(bg_np, st_np, mask):
    """Compone fondo + trazos según máscara y alpha -> imagen PIL RGB."""
    a = (mask.astype(np.float64) / 255.0)[..., None]
    a = a * (st_np[..., 3:4].astype(np.float64) / 255.0)
    out = bg_np * (1.0 - a) + st_np[..., :3] * a
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def stylus_position(order, progress, tol=0.012):
    """Posición del stylus en la punta del trazo que se está dibujando.

    Solo hay un componente activo por momento, así que el frente
    (píxeles por revelar con orden muy cercano a `progress`) es un único
    grupo: su centroide es la punta. Devuelve (x, y, "right"|"left") o None.
    """
    if progress >= 1.0:
        return None
    p = min(max(progress, 0.0), 1.0)
    front = (order >= p) & (order <= p + tol)
    if not front.any():
        return None
    ys, xs = np.where(front)
    y = int(ys.mean())
    x = int(xs.mean())
    return x, y, "right" if x > W // 2 else "left"


def _build_stylus():
    """Genera un stylus/marcador procedural (RGBA) y su espejo."""
    sw, sh = 260, 130

    def make(direction):
        im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        shd = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        ImageDraw.Draw(shd).ellipse([30, 96, 230, 116], fill=(0, 0, 0, 80))
        im = Image.alpha_composite(im, shd.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(im)
        if direction == "right":
            d.rounded_rectangle((44, 46, 196, 76), radius=15, fill=(46, 52, 66, 255))
            d.rounded_rectangle((52, 50, 188, 58), radius=4, fill=(120, 130, 150, 120))
            d.rectangle([184, 44, 200, 78], fill=(150, 155, 168, 255))
            d.polygon([(196, 48), (238, 60), (196, 76)], fill=(34, 38, 50, 255))
        else:
            d.rounded_rectangle((sw - 196, 46, sw - 44, 76), radius=15,
                                fill=(46, 52, 66, 255))
            d.rounded_rectangle((sw - 188, 50, sw - 52, 58), radius=4,
                                fill=(120, 130, 150, 120))
            d.rectangle([sw - 200, 44, sw - 184, 78], fill=(150, 155, 168, 255))
            d.polygon([(sw - 196, 48), (sw - 238, 60), (sw - 196, 76)],
                      fill=(34, 38, 50, 255))
        return im

    return make("right"), make("left")


_STYLUS_CACHE = None


def stylus_images():
    global _STYLUS_CACHE
    if _STYLUS_CACHE is None:
        _STYLUS_CACHE = _build_stylus()
    return _STYLUS_CACHE


def compose_stylus(frame, x, y, direction, scale=0.9):
    """Pega el stylus sobre el frame en (x, y)."""
    right, left = stylus_images()
    st = right if direction == "right" else left
    w, h = st.size
    w, h = int(w * scale), int(h * scale)
    st = st.resize((w, h), Image.LANCZOS)
    px = int(x - w * 0.92) if direction == "right" else int(x - w * 0.08)
    py = int(y - h * 0.72)
    frame.paste(st, (px, py), st)
    return frame
