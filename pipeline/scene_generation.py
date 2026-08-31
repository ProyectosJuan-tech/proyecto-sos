import glob
import os
import subprocess
import urllib.parse
import urllib.request
import json

from PIL import Image


def strip_img_metadata(path):
    """Quita metadata EXIF/GPS/comentarios sin cambiar comportamiento del pipeline."""
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
    """Bajada desde Wikimedia Commons con misma lógica del legacy."""
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
    subprocess.run(["curl", "-s", "-o", out_path, "-L", "--max-time", "60", u], check=True)
    if os.path.getsize(out_path) < 5000:
        raise RuntimeError(f"imagen muy chica: {scene}")
    return out_path


def find_local_img(imgs_dir, idx):
    """Busca imagen local eNN.* (png/jpg/webp) generada a mano."""
    candidates = sorted(glob.glob(os.path.join(imgs_dir, f"e{idx:02d}.*")))
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        for p in candidates:
            if p.lower().endswith(ext) and os.path.getsize(p) > 5000:
                return p
    return None


def find_local_video(imgs_dir, idx):
    """Busca b-roll local eNN.mp4 descargado o manual."""
    p = os.path.join(imgs_dir, f"e{idx:02d}.mp4")
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        return p
    return None
