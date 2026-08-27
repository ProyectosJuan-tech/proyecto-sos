"""
vfxkit_titles.py — Tipografía cinética animada via vfxkit.
Genera clips MP4 con texto animado para usar como:
  - Titulares de intro/outro
  - Transiciones entre escenas
  - Momentos de énfasis ("¡SÍ!")
  - CTAs animados

Uso:
    from vfxkit_titles import generate_title, generate_horizontal_title
    generate_title("LA CAVERNA", "/tmp/title.mp4", style="aurora")

Paletas disponibles: aurora, sunset, cyber, gold, ice, neon, magma, mono
"""
import sys
import os

_VFXKIT_PATH = os.path.join(os.path.expanduser("~"), "tools", "vfxkit")
if _VFXKIT_PATH not in sys.path:
    sys.path.insert(0, _VFXKIT_PATH)

import vfxkit as vk
from vfxkit import recipes as rx, palettes

PALETTES = list(palettes._DATA.keys())


def generate_title(text, output_path,
                   style="aurora",
                   size=120,
                   width=1080, height=1920,
                   fps=30, duration=5.0,
                   show_particles=True,
                   show_shine=True,
                   show_beams=True,
                   subtitle=None,
                   seed=0):
    pal = palettes.get(style)
    comp = vk.Composition(width, height, fps=fps, duration=duration,
                          bg=pal.bg_gradient(width, height))
    rx.rich_background(comp, style, beams=show_beams, seed=seed)
    txt = rx.kinetic_text(comp, text, palette=style, size=size,
                          stagger=0.08, entrance=0.85)
    if show_particles:
        rx.particle_burst(comp, t0=txt["settle"] - 0.05, seed=seed)
    if show_shine:
        rx.text_shine(comp, txt, t0=txt["settle"] + 0.15)
    if subtitle:
        rx.tagline(comp, subtitle, size=max(32, size // 3),
                   t0=txt["settle"] + 0.1)
    rx.cinematic_grade(comp)
    comp.render_video(output_path)
    return output_path


def generate_horizontal_title(text, output_path,
                              style="aurora", size=96,
                              fps=30, duration=5.0, **kwargs):
    return generate_title(text, output_path, style=style, size=size,
                          width=1920, height=1080,
                          fps=fps, duration=duration, **kwargs)


def generate_short_emphasis(text, output_path,
                            style="neon", size=160,
                            width=1080, height=1920,
                            fps=30, duration=2.5):
    pal = palettes.get(style)
    comp = vk.Composition(width, height, fps=fps, duration=duration,
                          bg=pal.bg_gradient(width, height))
    rx.rich_background(comp, style, beams=False, bokeh=True,
                       particles=True, intensity=0.5)
    txt = rx.kinetic_text(comp, text, palette=style, size=size,
                          stagger=0.04, entrance=0.5,
                          hold_to=duration - 0.4)
    rx.particle_burst(comp, t0=txt["settle"] - 0.03)
    rx.cinematic_grade(comp, bloom=None, grain=0.015)
    comp.render_video(output_path)
    return output_path


def generate_cta(text, output_path,
                 style="gold", size=80,
                 width=1080, height=1920,
                 fps=30, duration=3.0):
    pal = palettes.get(style)
    comp = vk.Composition(width, height, fps=fps, duration=duration,
                          bg=pal.bg_gradient(width, height))
    rx.rich_background(comp, style, beams=False, bokeh=True,
                       particles=True, intensity=0.3)
    txt = rx.kinetic_text(comp, text, palette=style, size=size,
                          stagger=0.06, entrance=0.7)
    rx.text_shine(comp, txt, t0=txt["settle"] + 0.1)
    rx.cinematic_grade(comp, chroma=None, grain=0.01)
    comp.render_video(output_path)
    return output_path


def title_scene(text, style="aurora", subtitle=None, duration=5.0, **kwargs):
    return {
        "title_text": text,
        "title_style": style,
        "title_subtitle": subtitle,
        "title_duration": duration,
        **kwargs
    }


if __name__ == "__main__":
    import tempfile
    out = os.path.join(tempfile.gettempdir(), "vfxkit_test.mp4")
    print(f"Generando test en {out}...")
    generate_title("LA CAVERNA DE PLATÓN", out, style="aurora",
                   size=100, duration=4.0)
    print(f"Listo: {out}")
