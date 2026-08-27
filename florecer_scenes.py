#!/usr/bin/env python3
"""Escenas del largo YT "No estás estancada: llevas demasiado tiempo sobreviviendo".

Guion basado en la estructura aprobada por el usuario (2026-08-20):
gancho humano -> validación -> Carl Rogers tarde -> FRASE CORAZÓN ->
re-enganche -> bloqueos -> 3 nutrientes -> aplicación -> cierre+fe.

Reglas aplicadas:
- Tuteo SIEMPRE (nunca voseo).
- Objeto-primero: los objetos cuentan la historia; persona solo en e03
  (espalda) y e30 (manos). Sin miradas a cámara.
- Arco visual frío->cálido: e01-e08 apagado (STYLE), e09-e13 cálido (LIGHT),
  e14 serio (STYLE), e15 revelación (LIGHT), e16-e20 bloqueo (STYLE),
  e21-e34 pleno cálido (LIGHT).
- Prompts SIMPLES para Pollinations ([escena] + [acción] + [luz] + [estilo]).
- Motion deliberado: gancho zoom-in, desarrollo pans alternados,
  frase corazón zoom-in lento, cierre zoom-out.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# (text, ai, q, motion, light)
SCENES = [
    # === GANCHO (0:00) ===
    (
        "¿Alguna vez viste a alguien cambiar casi por completo cuando por fin "
        "alguien la escucha de verdad? La misma persona, la misma historia. "
        "Pero algo en ella se enciende y empieza a moverse.",
        "Rain streaks running down a window seen from inside a dim quiet room, "
        "cold blue-gray morning light, empty wooden table in foreground, "
        "cinematic muted tones",
        "rainy window", "zoom-in", False,
    ),
    (
        "No cambió el consejo. No cambió la información. Cambió algo mucho más "
        "profundo. Y lo más curioso es que eso mismo puede pasar contigo, "
        "justo donde hoy te sientes detenida.",
        "Same dim room window but soft sunlight breaking through gray clouds "
        "outside, first warm rays touching the windowsill, hopeful transition "
        "light, cinematic",
        "sunlight through clouds", "pan-right", False,
    ),
    (
        "Hoy vas a entender por qué te sientes estancada aunque haces todo "
        "bien. Por qué el esfuerzo no alcanza. Y qué es lo único que "
        "realmente necesitas para volver a crecer.",
        "Woman in her fifties standing with her back to camera looking out a "
        "large window, soft morning light on her shoulders, quiet "
        "contemplative mood, warm domestic interior",
        "woman silhouette window", "zoom-in", False,
    ),
    # === VALIDACIÓN ===
    (
        "Pero antes de hablar de psicología, déjame decirte algo claro: si te "
        "sientes estancada, no es porque estés rota. Y esto no es un consuelo "
        "bonito. Es una observación seria.",
        "Cracked terracotta flower pot sitting alone on a wooden shelf near a "
        "window, overcast diffused light, muted earth tones, quiet still life",
        "cracked terracotta pot", "pan-left", False,
    ),
    (
        "No te falta disciplina. No te falta actitud. No te falta fe en la "
        "vida. Llevas años intentando con todas tus fuerzas, y eso ya dice "
        "mucho de ti.",
        "Wilted houseplant with drooping leaves on a windowsill, gray overcast "
        "daylight, dusty shelf, muted melancholic tones, shallow depth of field",
        "wilting houseplant", "zoom-out", False,
    ),
    (
        "Y si además te comparas con personas que parecen avanzar sin "
        "esfuerzo, el estancamiento pesa el doble. Pero cuidado: estás "
        "comparando tu invierno con el verano de otra persona.",
        "Two potted plants side by side on a windowsill, one lush and green "
        "one small and struggling, soft window light, gentle contrast story",
        "potted plants windowsill", "pan-right", False,
    ),
    (
        "Mira una planta que no crece. Nadie le grita. Nadie la culpa ni le "
        "pide esfuerzo. Solo se pregunta qué le falta: luz, agua, tierra "
        "buena. Con las personas debería pasar igual.",
        "Close-up of a hand gently touching dry cracked soil in a garden bed, "
        "warm late afternoon light, texture detail, documentary photography style",
        "dry cracked soil", "zoom-in", False,
    ),
    (
        "Contigo pasó al revés. Nadie te enseñó a preguntarte qué te falta. "
        "Te enseñaron a exigirte más, a esforzarte más y a culparte mejor "
        "cada vez que igual no avanzabas.",
        "Stack of self-help books beside a cup of cold tea on a wooden table, "
        "gray rainy day light through window, quiet interior, muted tones",
        "books tea table", "pan-left", False,
    ),
    # === ROGERS ENTRA TARDE ===
    (
        "A mediados del siglo pasado, un psicólogo llamado Carl Rogers se hizo "
        "una pregunta incómoda para su época. Tan incómoda que muchos colegas "
        "la consideraron una pérdida de tiempo.",
        "Vintage mid-century psychology office with a leather armchair, "
        "bookshelf and warm lamp light, empty room, nostalgic film look, soft "
        "shadows",
        "vintage office chair", "zoom-in", True,
    ),
    (
        "La pregunta era esta: ¿y si dejamos de intentar arreglar a las "
        "personas? ¿Y si simplemente las acompañamos, las escuchamos, mientras "
        "ellas mismas encuentran su camino?",
        "Two comfortable armchairs facing each other in an empty room with "
        "soft window light, space for conversation, warm neutral palette, calm "
        "atmosphere",
        "armchairs living room", "pan-right", True,
    ),
    (
        "Durante años trabajó así, consulta tras consulta, escuchando sin "
        "juzgar. Y en ese silencio respetuoso apareció algo que cambió la "
        "psicología para siempre.",
        "Open notebook with a fountain pen resting on it, morning sun rays "
        "crossing the desk, dust particles in light beam, intimate close-up",
        "notebook pen desk", "zoom-out", True,
    ),
    (
        "Carl Rogers descubrió que dentro de cada persona vive una fuerza natural "
        "que busca crecer, sanar y volver a ser quien realmente es. Igual que "
        "una semilla busca la luz sin que nadie se lo ordene.",
        "Tiny green seedling sprouting from dark rich soil, single golden "
        "sunbeam illuminating it, macro photography, deep background blur, "
        "hope symbol",
        "seedling soil", "zoom-in", True,
    ),
    (
        "La llamó tendencia actualizante. Y funciona como una semilla: no "
        "necesita presión, ni gritos, ni más exigencia. Necesita condiciones. "
        "Necesita el lugar correcto.",
        "Interior of a greenhouse full of green plants with golden light rays "
        "streaming through glass panels, dust particles floating, abundant "
        "life, warm hopeful atmosphere",
        "greenhouse interior", "pan-left", True,
    ),
    # === RE-ENGANCHE (~40%) ===
    (
        "Pero acá viene lo serio. Porque si esa fuerza vive en ti desde "
        "siempre... ¿por qué llevas tanto tiempo sintiéndote detenida? Esa "
        "pregunta tiene respuesta. Y no es la que crees.",
        "Long shadow of a small plant cast on a wall at dusk, dramatic low "
        "warm light, minimalist composition, quiet symbolic mood",
        "plant shadow wall", "zoom-in", False,
    ),
    # === FRASE CORAZÓN (payoff antes de la mitad) ===
    (
        "Carl Rogers encontró la respuesta mirando lo que rodeaba a sus pacientes, "
        "no lo que les faltaba adentro: cuando dejamos de gastar toda nuestra "
        "energía intentando sobrevivir, algo dentro de nosotros empieza a "
        "buscar cómo vivir.",
        "Greenhouse rows of young plants bathed in golden morning light, one "
        "small sprout in sharp focus in front, revelation warmth, cinematic "
        "depth",
        "greenhouse plants light", "zoom-in", True,
    ),
    # === LO QUE BLOQUEA ===
    (
        "Piénsalo en una planta en tierra seca. No está enferma. No está "
        "vencida. Está ocupada sobreviviendo. Cada gota de agua la usa para "
        "resistir otro día.",
        "Small green sprout emerging through cracked dry earth, close-up "
        "macro, harsh midday light on parched ground, resilience symbol, "
        "shallow depth of field",
        "sprout growing soil", "pan-right", False,
    ),
    (
        "Toda su energía va en aguantar el sol, resistir el viento, esperar "
        "la lluvia que no llega. No queda ni una gota de fuerza para brotar. "
        "Ni una sola.",
        "Plant roots visible inside a clear glass vase of water on a dim "
        "windowsill, backlit, delicate white roots searching, minimal "
        "composition",
        "plant roots water", "zoom-out", False,
    ),
    (
        "Y hay algo más: una planta así no puede dar fruto, aunque su especie "
        "esté hecha para eso. No es falta de vocación. Es falta de condiciones.",
        "Bare fruit tree branches against an overcast pale sky, winter "
        "dormancy, quiet minimal landscape, muted cool tones",
        "bare tree winter", "pan-left", False,
    ),
    (
        "Contigo pasó igual. Si creciste leyendo ánimos al entrar por la "
        "puerta, evitando tormentas, cuidando el clima emocional de tu casa, "
        "tu gran aprendizaje fue sobrevivir.",
        "Cozy hallway of an old family home in dim evening light, a child's "
        "crayon drawing taped to the wall, nostalgic warm shadow mood",
        "cozy hallway home", "zoom-in", False,
    ),
    (
        "Y sobreviviste tan bien que se volvió tu manera automática de estar "
        "en el mundo. Hasta que un día descubriste que ni siquiera sabes cómo "
        "se siente estar tranquila.",
        "Wool blanket draped over an armchair beside a window with gray light "
        "outside, quiet living room, muted peaceful tones, soft focus",
        "wool blanket armchair", "pan-right", False,
    ),
    # === LOS 3 NUTRIENTES ===
    (
        "Entonces, ¿qué hacemos? Carl Rogers decía que las personas no necesitan "
        "más presión ni más consejos. Necesitan tres nutrientes. Los mismos "
        "tres, siempre.",
        "Three small terracotta pots in a row on a sunny windowsill, each with "
        "rich soil ready for planting, warm morning light, simple composition",
        "terracotta pots", "zoom-out", True,
    ),
    (
        "El primero es aceptación: poder ser como eres, sin condición. Sin "
        "tener que ganarte el amor cada día, como si fueras una empleada de "
        "tu propia vida.",
        "Hands gently opening a simply wrapped gift box on a wooden table, "
        "warm sunlight across the scene, generous tender moment, close-up",
        "gift box hands", "pan-right", True,
    ),
    (
        "El segundo es comprensión: que alguien entre en tu mundo y mire con "
        "tus ojos, sin apurarte, sin corregirte, sin decirte ya deberías estar "
        "mejor.",
        "Two steaming tea cups across a wooden table by a window, soft "
        "afternoon light, intimate conversation setting, warm cozy tones",
        "tea cups table", "pan-left", True,
    ),
    (
        "Y el tercero es autenticidad: bajar la máscara. Que lo que muestras "
        "afuera sea lo que vives adentro. Porque sostener una imagen también "
        "agota.",
        "A theater mask resting on a table beside a blooming flower in a "
        "small vase, soft directional light, symbolic still life, warm shadows",
        "theater mask", "zoom-in", True,
    ),
    (
        "Cuando esos tres nutrientes aparecen, algo se suelta en el cuerpo. "
        "Los hombros bajan. La respiración se hace profunda. Una parte muy "
        "adentro entiende: ya puedo.",
        "Knitted shawl softly slipping off the arm of a relaxed armchair, "
        "warm lamp light, cozy living room corner, sense of relief and rest",
        "shawl armchair", "zoom-out", True,
    ),
    (
        "Y cuando faltan, nos pasa esto: vivimos años enteros pidiendo permiso "
        "para existir. Esperando que alguien nos autorice a descansar, a "
        "equivocarnos, a empezar de nuevo.",
        "Open birdcage with its door wide open and a small bird flying toward "
        "bright sky, backlit golden hour, freedom symbol, uplifting",
        "bird flying sky", "pan-right", True,
    ),
    (
        "Quizás por eso te cuesta tanto descansar. Porque en algún momento "
        "aprendiste que tu valor dependía de tu rendimiento. Y eso también es "
        "sobrevivir disfrazado de vida.",
        "Quiet bedroom morning with alarm clock and neatly folded blanket on "
        "the bed, soft warm dawn light through curtains, restful stillness",
        "bedroom morning", "zoom-out", True,
    ),
    # === APLICACIÓN ===
    (
        "Ahora, ¿qué haces con todo esto mañana a la mañana? Empieza chico. "
        "Muy chico. Los cambios que duran nunca empiezan con una revolución.",
        "Small metal watering can on a windowsill in early morning light, "
        "fresh new day feeling, clean simple composition, warm tones",
        "watering can", "pan-left", True,
    ),
    (
        "Busca un lugar donde puedas ser tú sin editar tus palabras. Una "
        "persona de confianza. Un espacio tuyo. Un rincón silencioso donde "
        "nadie te pide nada.",
        "Reading nook corner with a comfortable armchair, small bookshelf and "
        "a healthy green plant, warm lamp glow, inviting personal space",
        "reading nook", "zoom-in", True,
    ),
    (
        "Ahí empieza a regar lo que quedó dormido: esa idea que pospusiste mil "
        "veces, esa ilusión que te da un poco de vergüenza admitir, esa parte "
        "tuya que lleva años esperando.",
        "Hand writing in an open journal with a pen, golden hour light "
        "streaming across the page, intimate close-up, warm nostalgic tones",
        "writing journal", "pan-right", True,
    ),
    (
        "No necesitas cambiar tu vida entera esta semana. Solo necesitas "
        "tierra nueva para la parte de ti que quiere volver. El resto llega "
        "solo, cuando la raíz despierta.",
        "Soil-dusted hands repotting a green plant into a larger terracotta "
        "pot, gardening tools nearby, warm natural light, care and growth "
        "ritual",
        "repotting plant", "zoom-in", True,
    ),
    # === CIERRE + FE (sin proselitismo) ===
    (
        "Porque no fuiste creada para sobrevivir. Fuiste creada para amar, "
        "para servir, para florecer. Y ninguna etapa de tu vida llegó tarde "
        "para empezar.",
        "Garden in full bloom seen through an open cottage door, golden hour "
        "light flooding in, abundance of flowers, welcoming warmth",
        "garden flowers door", "zoom-out", True,
    ),
    (
        "Tu vida es un don. Y los dones no se guardan en un cajón: se "
        "cultivan, se agradecen y se comparten.",
        "Single lit candle on a wooden table in a warm dusk interior, soft "
        "flame glow, peaceful reflective atmosphere, dark warm background",
        "lit candle table", "zoom-in", True,
    ),
    # === BONUS "una cosa más" (+3.2x end-screen) ===
    (
        "Ah, y una cosa más antes de irte: no esperes a sentirte lista para "
        "empezar. Las plantas no florecen de una vez: primero cuidan la raíz "
        "en silencio. Después, un día, florecen.",
        "Macro of a white flower blooming beside a transparent vase showing "
        "delicate roots, warm golden window light, quiet strength symbol, "
        "shallow depth of field",
        "flower roots vase", "zoom-in", True,
    ),
    (
        "Si este video te hizo sentido, dale like y suscríbete. Acá caminamos "
        "juntos hacia una vida más plena, de a pasos reales, sin promesas "
        "vacías.",
        "Sunrise over a quiet landscape seen through a window with a plant "
        "silhouette in the foreground, new beginning light, hopeful warm tones",
        "sunrise window", "zoom-out", True,
    ),
]


def scenes():
    out = []
    for i, (text, ai, q, motion, light) in enumerate(SCENES, start=1):
        sc = {"text": text, "ai": ai, "q": q, "motion": motion}
        if light:
            sc["light"] = True
        assert "\tvos\t" not in text.lower() and " sentís " not in text.lower()
        out.append(sc)
    return out


if __name__ == "__main__":
    total_words = sum(len(s[0].split()) for s in SCENES)
    print(f"{len(SCENES)} escenas, {total_words} palabras")
    est = total_words / 2.0 + len(SCENES) * 1.15
    print(f"duración estimada: {est/60:.1f} min")
