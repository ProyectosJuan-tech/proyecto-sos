#!/usr/bin/env python3
"""Post-procesamiento profesional: color grading + normalización audio + QA.

Uso:
  python3 post_procesar.py <video.mp4> [--out <salida.mp4>] [--grade] [--normalize] [--qa]

Opciones:
  --grade       Aplica color grading sutil (film look, vibrance, vignette)
  --normalize   Normaliza audio a -16 LUFS (YouTube) o -14 LUFS (social)
  --qa          Ejecuta QA automático (ffprobe, duración, audio, resolution)
  --all         Aplica todo (grade + normalize + qa)
  --preset      Preset de grading: film (default), warm, cool, cinematic
  --platform    Plataforma destino: youtube (default) o facebook
"""
import argparse
import json
import os
import subprocess
import sys

W_V, H_V = 1080, 1920  # vertical
W_H, H_H = 1920, 1080  # horizontal


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def ffprobe_json(path, args):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json"] + args + [path]
    out, err, rc = run(cmd)
    if rc != 0:
        return {}
    return json.loads(out)


def detect_format(path):
    info = ffprobe_json(path, ["-show_streams", "-show_format"])
    fmt = info.get("format", {})
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    w = int(video.get("width", 0))
    h = int(video.get("height", 0))
    return {
        "width": w, "height": h,
        "is_vertical": h > w,
        "has_audio": bool(audio),
        "duration": float(fmt.get("duration", 0)),
        "size_mb": os.path.getsize(path) / (1024 * 1024),
    }


# ─── COLOR GRADING ───────────────────────────────────────────────────

GRADES = {
    "film": {
        "desc": "Look de película cálida (nuestro estándar)",
        "filter": (
            "curves=master='0/0.03 0.5/0.5 1/0.97',"  # fade suave en negros
            "eq=contrast=1.05:saturation=1.08,"
            "colorbalance=rs=0.03:bs=-0.03"  # sombras cálidas
        ),
    },
    "warm": {
        "desc": "Cálido extremo (bienestar, golden hour)",
        "filter": (
            "curves=master='0/0.04 0.5/0.52 1/0.96',"
            "eq=contrast=1.03:saturation=1.12,"
            "colorbalance=rs=0.05:gs=0.02:bs=-0.05:rm=0.03:bm=-0.03"
        ),
    },
    "cool": {
        "desc": "Frío/dramático (caverna, despertar)",
        "filter": (
            "curves=master='0/0.02 0.5/0.48 1/0.98',"
            "eq=contrast=1.08:saturation=0.95,"
            "colorbalance=rs=-0.03:bs=0.05:rm=-0.02:bm=0.03"
        ),
    },
    "cinematic": {
        "desc": "Cinematic teal & orange (blockbuster)",
        "filter": (
            "curves=master='0/0.03 0.5/0.5 1/0.97',"
            "eq=contrast=1.06:saturation=1.1,"
            "colorbalance=rs=-0.04:bs=0.06:rm=0.03:bm=-0.02:rh=0.04:bh=-0.04"
        ),
    },
}


def apply_grade(video_in, video_out, preset="film"):
    grade = GRADES.get(preset, GRADES["film"])
    vf = grade["filter"]
    cmd = [
        "ffmpeg", "-y", "-i", video_in,
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-tune", "film", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart", video_out,
    ]
    print(f"  [grade] aplicando '{preset}': {grade['desc']}")
    out, err, rc = run(cmd)
    if rc != 0:
        print(f"  [grade] ERROR: {err[:200]}")
        return False
    return True


# ─── AUDIO NORMALIZATION ──────────────────────────────────────────────

def normalize_audio(video_in, video_out, lufs=-16, tp=-1.5):
    af = f"loudnorm=I={lufs}:TP={tp}:LRA=11"
    cmd = [
        "ffmpeg", "-y", "-i", video_in,
        "-af", af,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", video_out,
    ]
    print(f"  [audio] normalizando a {lufs} LUFS, peak {tp} dBTP")
    out, err, rc = run(cmd)
    if rc != 0:
        print(f"  [audio] ERROR: {err[:200]}")
        return False
    return True


# ─── QA AUTOMÁTICO ───────────────────────────────────────────────────

def qa_check(video_path, platform="youtube"):
    info = detect_format(video_path)
    issues = []

    # Resolución
    if platform == "youtube":
        expected = (1920, 1080)
        if info["width"] != expected[0] or info["height"] != expected[1]:
            issues.append(f"Resolución {info['width']}x{info['height']}, esperado {expected[0]}x{expected[1]}")
    else:
        if info["width"] != 1080 or info["height"] != 1920:
            issues.append(f"Resolución {info['width']}x{info['height']}, esperado 1080x1920")

    # Audio
    if not info["has_audio"]:
        issues.append("SIN AUDIO")

    # Duración
    if platform == "youtube" and info["duration"] < 480:
        issues.append(f"Duración {info['duration']:.0f}s (<8min, no monetiza en YT)")
    elif platform == "facebook" and info["duration"] < 60:
        issues.append(f"Duración {info['duration']:.0f}s (<60s)")

    # Tamaño
    if info["size_mb"] > 500:
        issues.append(f"Archivo muy grande: {info['size_mb']:.0f}MB")

    # LUFS check
    cmd_lufs = [
        "ffmpeg", "-i", video_path,
        "-af", "loudnorm=print_format=json", "-f", "null", "-"
    ]
    out, err, rc = run(cmd_lufs)
    try:
        lufs_data = json.loads(err.split("Parsed_loudnorm")[-1].split("}")[0].split("{")[1] + "}")
        integrated = float(lufs_data.get("input_i", "-99"))
        if integrated > -12:
            issues.append(f"Audio muy alto: {integrated:.1f} LUFS (target -16)")
        elif integrated < -22:
            issues.append(f"Audio muy bajo: {integrated:.1f} LUFS (target -16)")
    except Exception:
        pass

    return info, issues


# ─── MAIN ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post-procesamiento profesional")
    parser.add_argument("video", help="Video de entrada")
    parser.add_argument("--out", help="Video de salida (default: <input>_final.mp4)")
    parser.add_argument("--grade", action="store_true", help="Aplicar color grading")
    parser.add_argument("--normalize", action="store_true", help="Normalizar audio")
    parser.add_argument("--qa", action="store_true", help="Ejecutar QA automático")
    parser.add_argument("--all", action="store_true", help="Todo (grade + normalize + qa)")
    parser.add_argument("--preset", default="film", choices=list(GRADES.keys()),
                        help="Preset de grading (default: film)")
    parser.add_argument("--platform", default="youtube", choices=["youtube", "facebook"],
                        help="Plataforma destino")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"ERROR: {args.video} no existe")
        sys.exit(1)

    out_path = args.out or args.video.replace(".mp4", "_final.mp4")
    current = args.video

    print(f"\n=== Post-procesamiento: {os.path.basename(args.video)} ===")

    if args.qa or args.all:
        print("\n--- QA ---")
        info, issues = qa_check(current, args.platform)
        print(f"  Formato: {info['width']}x{info['height']} ({'vertical' if info['is_vertical'] else 'horizontal'})")
        print(f"  Duración: {info['duration']:.1f}s")
        print(f"  Tamaño: {info['size_mb']:.1f}MB")
        print(f"  Audio: {'SÍ' if info['has_audio'] else 'NO'}")
        if issues:
            print(f"  ⚠ Problemas:")
            for i in issues:
                print(f"    - {i}")
        else:
            print("  ✓ QA OK")

    if args.grade or args.all:
        print("\n--- Color Grading ---")
        tmp = current.replace(".mp4", "_graded.mp4")
        if apply_grade(current, tmp, args.preset):
            current = tmp
            print("  ✓ Grading aplicado")

    if args.normalize or args.all:
        print("\n--- Audio Normalization ---")
        tmp = current.replace(".mp4", "_norm.mp4")
        lufs = -14 if args.platform == "facebook" else -16
        if normalize_audio(current, tmp, lufs=lufs):
            current = tmp
            print("  ✓ Audio normalizado")

    if current != out_path:
        os.rename(current, out_path)
        print(f"\n✓ Salida: {out_path} ({os.path.getsize(out_path)//1024} KB)")
    else:
        print(f"\n✓ Sin cambios necesarios")

    # Limpiar temporales
    for suffix in ["_graded.mp4", "_norm.mp4"]:
        tmp = args.video.replace(".mp4", suffix)
        if os.path.exists(tmp) and tmp != out_path:
            os.remove(tmp)


if __name__ == "__main__":
    main()
