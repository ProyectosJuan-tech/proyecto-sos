import json
import os
import re
import subprocess
import urllib.parse
import urllib.request


def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def generate_bgm(out_path, duration=300):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        return out_path
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fade_in = min(3, max(0.25, duration / 8))
    fade_out = min(3, max(0.25, duration / 8))
    fade_out_start = max(0, duration - fade_out)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=138.59:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=164.81:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}",
        "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.008:duration={duration}",
        "-filter_complex",
        "[0]volume=0.05,tremolo=f=0.15:d=0.5[a];"
        "[1]volume=0.04,tremolo=f=0.11:d=0.5[b];"
        "[2]volume=0.035,tremolo=f=0.19:d=0.5[c];"
        "[3]volume=0.03,tremolo=f=0.13:d=0.5[d];"
        "[4]lowpass=f=600[e];"
        "[a][b][c][d][e]amix=inputs=5:normalize=0,lowpass=f=900,"
        f"afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out}",
        "-ar", "24000", "-ac", "1", out_path,
    ]
    run(cmd)
    return out_path


def mix_bgm(video_in, bgm_path, out_path, volume=0.4):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_in,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex",
        f"[1:a]volume={volume}[bgm];"
        "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "24000", "-ac", "1",
        "-movflags", "+faststart", out_path,
    ]
    run(cmd)
    return out_path


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def norm(s):
    return re.sub(r"[^a-záéíóúüñ0-9]", "", s.lower())


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
