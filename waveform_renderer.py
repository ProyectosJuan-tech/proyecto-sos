"""
waveform_renderer.py — Formas de onda de audio via FFmpeg.
Genera visualizaciones de audio reactivas para usar como:
  - Intro/outro con onda de audio
  - Overlay sutil bajo la voz
  - Fondo animado reactiva al audio

Uso:
    from waveform_renderer import render_waveform_overlay, render_waveform_video
    render_waveform_overlay("audio.wav", "overlay.png")  # imagen transparente
    render_waveform_video("audio.wav", "wave.mp4")       # video de onda
"""
import subprocess
import os


def render_waveform_overlay(audio_path, output_path,
                            width=1080, height=120,
                            color="white"):
    """
    Genera imagen PNG transparente con la forma de onda estática.
    Útil como overlay en escenas.
    """
    cmd = [
        "ffmpeg", "-y", "-i", audio_path,
        "-filter_complex",
        f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}:colors={color}",
        "-frames:v", "1", output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def render_waveform_video(audio_path, output_path,
                          width=1080, height=150,
                          mode="cline",
                          color="white",
                          bg_color=None,
                          fps=30):
    """
    Genera video MP4 con onda de audio animada.

    Args:
        audio_path: Archivo de audio (wav, mp3, etc.)
        output_path: MP4 de salida
        width, height: Resolución del video de onda
        mode: line | p2p | cline (cline = simétrico, más bonito)
        color: Color de la onda (hex o nombre)
        bg_color: Color de fondo (None = negro)
        fps: Frames por segundo

    Returns:
        output_path
    """
    filters = f"showwaves=s={width}x{height}:mode={mode}:colors={color}:rate={fps}"
    if bg_color:
        filters = f"color=c={bg_color}:s={width}x{height}:r={fps}[bg];[0:a]{filters}[wave];[bg][wave]overlay"
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-filter_complex", filters,
            "-pix_fmt", "yuv420p", "-r", str(fps),
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-filter_complex", f"[0:a]{filters}[v]",
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-c:a", "copy",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            output_path
        ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def render_waveform_circle(audio_path, output_path,
                           size=400,
                           color="white",
                           bg_color=None,
                           fps=30):
    """
    Genera video con onda de audio circular (efecto visual premium).
    """
    filters = (
        f"aformat=channel_layouts=mono,"
        f"showwaves={size}x{size}:cline:colors={color}:draw=full,"
        f"geq='p(mod(W/PI*(PI+atan2(H/2-Y,X-W/2)),W),H-2*hypot(H/2-Y,X-W/2))':"
        f"a='alpha(mod(W/PI*(PI+atan2(H/2-Y,X-W/2)),W),H-2*hypot(H/2-Y,X-W/2))'"
    )
    if bg_color:
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-i", f"color=c={bg_color}:s={size}x{size}:r={fps}",
            "-filter_complex", f"[0:a]{filters}[wave];[1:v][wave]overlay=(W-w)/2:(H-h)/2",
            "-c:v", "libx264", "-c:a", "copy",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            "-t", "10",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-filter_complex", f"[0:a]{filters}[v]",
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-c:a", "copy",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            "-t", "10",
            output_path
        ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python3 waveform_renderer.py <audio> <output.mp4> [circle]")
        sys.exit(1)
    audio = sys.argv[1]
    out = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "cline"
    if mode == "circle":
        render_waveform_circle(audio, out)
    else:
        render_waveform_video(audio, out, mode=mode)
    print(f"Listo: {out}")
