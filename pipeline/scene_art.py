import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


W, H = 1080, 1920


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
    d.ellipse([sun_x - 46, sun_y - 46, sun_x + 46, sun_y + 46], fill=(255, 240, 190))

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
    """Fondo para direccion visual LUMINOSA."""
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
    """Fondo para modo serif."""
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
