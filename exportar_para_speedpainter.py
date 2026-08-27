#!/usr/bin/env python3
"""Exporta escenas como PNGs limpios 1080x1920 para subir a Canva Speed Painter.

Workflow:
  1. python3 exportar_para_speedpainter.py <nombre_video> [carpeta_salida]
  2. Abrir Canva → Speed Painter → subir cada PNG → animar → descargar MP4
  3. Mover los MP4s descargados a videos/<nombre>/imgs/ como eNN_sp.mp4
  4. Usar en hacer_videos_nuevos.py con "stock_video": "eNN_sp.mp4"

Soporta videos de hacer_videos_nuevos.py (VIDEOS) y shorts (SHORTS).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageEnhance

W, H = 1080, 1920

# ---------------------------------------------------------------------------
# Importar definiciones de videos
# ---------------------------------------------------------------------------
import hacer_videos_nuevos as hn
import hacer_shorts as hs


def find_video(name):
    """Busca un video por nombre en VIDEOS o SHORTS."""
    for v in hn.VIDEOS:
        if v["name"] == name:
            return v["name"], v["scenes"], "largo"
    for s in hs.SHORTS:
        if s["id"] == name:
            return s["id"], [s], "short"
    return None, None, None


def clean_916(img_path, out_path):
    """Recorta a 9:16 y resize a 1080x1920 SIN oscurecer ni overlays."""
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
    img.save(out_path)
    return out_path


def export_video(name, out_dir=None):
    video_name, scenes, kind = find_video(name)
    if not video_name:
        print(f"ERROR: no encontré '{name}' en VIDEOS ni SHORTS")
        print("Videos disponibles:")
        for v in hn.VIDEOS:
            print(f"  - {v['name']} ({len(v['scenes'])} escenas)")
        for s in hs.SHORTS:
            print(f"  - {s['id']} (short)")
        return

    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "speedpainter", video_name)
    os.makedirs(out_dir, exist_ok=True)

    base = os.path.dirname(os.path.abspath(__file__))
    # Buscar imágenes en múltiples ubicaciones posibles
    candidates = [
        os.path.join(base, "videos", video_name, "imgs"),
        os.path.join(base, "videos", "youtube", video_name, "imgs"),
        os.path.join(base, "videos", "largo", "imgs"),
    ]
    if kind == "short":
        candidates.insert(0, os.path.join(base, "videos", "shorts", "imgs"))

    img_dir = None
    for c in candidates:
        if os.path.isdir(c):
            img_dir = c
            break
    if img_dir is None:
        img_dir = candidates[0]

    print(f"\n=== {video_name} ({kind}, {len(scenes)} escenas) ===")
    print(f"Salida: {out_dir}/\n")

    exported = []
    for i, scene in enumerate(scenes, 1):
        slug = f"e{i:02d}"
        src = os.path.join(img_dir, f"{slug}.jpg")
        dst = os.path.join(out_dir, f"{slug}.png")

        if not os.path.exists(src):
            print(f"  [{slug}] imagen no encontrada: {src}")
            print(f"      Generá la imagen primero con el pipeline normal")
            continue

        clean_916(src, dst)
        size_kb = os.path.getsize(dst) // 1024
        print(f"  [{slug}] OK → {dst} ({size_kb} KB)")
        exported.append(dst)

    print(f"\n--- Listo: {len(exported)} PNGs en {out_dir}/ ---")
    if exported:
        print("\nPróximos pasos:")
        print(f"  1. Abrí Canva → Speed Painter")
        print(f"  2. Subí cada PNG de {out_dir}/")
        print(f"  3. Elegí: duración, estilo de mano, FPS (30 para social)")
        print(f"  4. Animate → Download MP4")
        print(f"  5. Guardá los MP4s como eNN_sp.mp4 en:")
        print(f"     {img_dir}/")
        print(f"  6. En el dict de la escena, agregá:")
        print(f'     "stock_video": "eNN_sp.mp4"')
    return exported


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python3 exportar_para_speedpainter.py <nombre_video> [carpeta_salida]")
        print("\nVideos disponibles:")
        for v in hn.VIDEOS:
            print(f"  - {v['name']} ({len(v['scenes'])} escenas)")
        for s in hs.SHORTS:
            print(f"  - {s['id']} (short)")
        sys.exit(1)
    name = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    export_video(name, out)
