#!/usr/bin/env python3
"""Personaje recurrente "El Sabio" — identidad visual del canal (estilo nomofactos).

Un hombre mayor sabio y cálido, fotorrealista, presente en TODOS los shorts para
que el canal sea reconocible. Voz asociada: jorge (mentor).

Consistencia:
  - Prompt fijo de personaje (SABIO) + escena. Con el MISMO seed en Pollinations
    el rostro queda muy parecido entre escenas; para consistencia perfecta se usa
    img2img con imagen de referencia (requiere POLLINATIONS_KEY, ver ai_video.py).
  - seed por defecto 411 (igual que hacer_shorts.py).
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

SABIO = (
    "An elderly Latin American man in his seventies, kind warm eyes, "
    "short gray-white hair, gentle smile, soft wrinkles, wearing a simple "
    "beige cardigan over a light shirt, grandfatherly wise presence"
)

WARM = (
    ", warm golden morning light, bright airy interior, soft diffused window light, "
    "high-key, cream and sage palette, gentle highlights, no hard shadows, "
    "photorealistic, high detail"
)

# Escenas tipo: la misma persona en situaciones cotidianas que ya valida la audiencia.
SCENES = {
    "tea_window": f"{SABIO} sitting in a cozy armchair by a large window holding a cup of tea, morning light on his face{WARM}",
    "book_table": f"{SABIO} reading an old book at a wooden table, a cup of coffee beside him, warm lamp light{WARM}",
    "garden_walk": f"{SABIO} walking slowly in a quiet garden path at dawn, hands gently behind his back, hopeful{WARM}",
    "candle_dark": f"{SABIO} in a dim warm room holding a single lit candle, light on his face, calm contemplative{WARM}",
    "mirror_serene": f"{SABIO} looking out a large window at sunrise, thoughtful serene expression, quiet confidence{WARM}",
    "plant_window": f"{SABIO} gently watering a small plant on his windowsill, morning light, tender careful mood{WARM}",
    "porch_coffee": f"{SABIO} sitting on a wooden porch in the morning with a cup of coffee, golden light, peaceful{WARM}",
    "old_door": f"{SABIO} standing at an open old wooden door, warm light streaming in, calm wise face{WARM}",
}


def scene_prompt(scene_key="tea_window"):
    """Devuelve el prompt completo para la escena del Sabio."""
    return SCENES.get(scene_key, SCENES["tea_window"])


def all_scenes():
    return list(SCENES)


if __name__ == "__main__":
    print(scene_prompt("tea_window"))