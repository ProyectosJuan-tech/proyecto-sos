#!/usr/bin/env python3
"""Sistema Visual Estoico — pista estoica/filosófica del canal (no la pista bienestar).

Helper de prompts de imagen según el skill `.opencode/skills/sistema-visual`.
El arco es PROBLEMA → AUTORIDAD → SOLUCIÓN → TRANSFORMACIÓN → CTA, con evolución
de color oscuridad → luz. Ver wiki `cerebro/wiki/contenido/sistema-visual-estoico.md`.

Uso:
    visual_estoico.py                    # muestra las 5 escenas tipo (seneca)
    visual_estoico.py storm              # una escena específica (storm/bust/writing/release/cta)
"""
import sys

# Paleta del sistema (regla 70/20/10)
STOIC_PALETTE = {
    "black": "#090a09",        # fondo base
    "black_soft": "#151512",   # escenas de acción (escritorio, método)
    "white": "#e8e2d5",        # blanco cálido (texto)
    "gold": "#d99b28",         # IMPORTANTE (palabras clave, relojes, luz)
    "stone": "#6f6a5f",        # gris piedra (mármol, sombras)
}

# Sufijo de estilo cinematográfico oscuro (pista estoica).
STOIC_STYLE = (
    ", cinematic, dark and moody, dramatic lighting, deep shadows, "
    "high contrast, photorealistic, premium documentary, classical "
    "atmosphere, subtle film grain, high dynamic range"
)

# Sufijo para el elemento de luz dorada de énfasis (transición hacia la calma).
GOLD_LIGHT = (
    ", a single warm golden side light partially illuminating the subject, "
    "subtle antique gold rim light, warm amber glow"
)

# Base común del prompt estructurado (sin texto, sin logos, con continuidad).
PROMPT_TEMPLATE = (
    "Cinematic vertical 9:16 scene for a premium YouTube Short about Stoic "
    "philosophy.\n"
    "Subject: {subject}\n"
    "Action: {action}\n"
    "Environment: {environment}\n"
    "Emotional intention: {emotion}\n"
    "Visual metaphor: {metaphor}\n"
    "Lighting: {lighting}\n"
    "Composition: {composition}\n"
    "Camera: {camera}\n"
    "Color palette: black, charcoal, stone gray, warm ivory, subtle antique gold.\n"
    "Visual style: cinematic photography, photorealistic, premium documentary, "
    "classical Stoic atmosphere, dramatic lighting, natural textures, subtle film "
    "grain, realistic skin and materials, deep shadows, high dynamic range.\n\n"
    "No text. No typography. No logos. No watermark. No modern objects unless "
    "explicitly requested. Maintain visual continuity with the previous and next scenes."
)


def build_prompt(subject, action, environment, emotion, metaphor,
                 lighting, composition, camera):
    """Ensambla el prompt base del sistema visual estoico (ver skill)."""
    return PROMPT_TEMPLATE.format(
        subject=subject, action=action, environment=environment,
        emotion=emotion, metaphor=metaphor, lighting=lighting,
        composition=composition, camera=camera,
    )


# Escenas tipo del arco estoico. Cada prompt es 1 oración con el sufijo de estilo.
SCENES = {
    "storm": (
        "Middle-aged man sitting alone in a dark small room, holding his head in "
        "both hands, a giant surreal storm of clouds and lightning swirling above "
        "him representing his anxious thoughts, outside the storm the world is "
        "calm, cold desaturated tones"
        + STOIC_STYLE
    ),
    "bust": (
        "Ancient Roman marble bust of Seneca with weathered realistic texture, "
        "serene observing expression, dark empty background like an old Roman "
        "library, partially lit by a single warm golden side light touching his "
        "face, stone gray and black and gold palette"
        + STOIC_STYLE
    ),
    "writing": (
        "Close-up of a hand writing worries in an open notebook on a wooden desk, "
        "small hourglass marking fifteen minutes beside it, warm lamp light "
        "replacing the cold tones, feeling of control and clarity, black and "
        "brown and gold palette"
        + STOIC_STYLE
    ),
    "release": (
        "The same middle-aged man from the anxious scene now sitting calmly by a "
        "window at dawn, closed notebook and pencil on the table, storm gone, "
        "calm mountains and sunrise landscape outside, warm soft natural light, "
        "wider open camera, feeling of relief and presence, gold and orange and "
        "warm ivory palette"
        + STOIC_STYLE
    ),
    "cta": (
        "Warm hopeful morning sky with soft golden sunlight breaking through, "
        "calm and open composition, feeling of peace, gold and sky and warm "
        "ivory palette"
        + STOIC_STYLE
    ),
}


def scene_prompt(key="bust"):
    """Devuelve el prompt completo para una etapa del arco estoico."""
    return SCENES.get(key, SCENES["bust"])


def all_scenes():
    return list(SCENES)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and arg != "all":
        print(scene_prompt(arg))
    else:
        for k in all_scenes():
            print(f"\n=== {k.upper()} ===")
            print(scene_prompt(k))