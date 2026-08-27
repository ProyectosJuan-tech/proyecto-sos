#!/usr/bin/env python3
"""Escenas del largo YT 'Integrar, no sanar' (16:9, ~6 min).

Guion aprobado por el usuario (2026-08-26):
gancho fuerte -> validación -> gurús/constelaciones -> cueva ->
luz/Dios -> oración -> integrar vs borrar -> aceptar ->
fuerza divina -> confianza -> amanecer -> paz -> CTA.

Reglas aplicadas:
- Tuteo SIEMPRE (nunca voseo).
- Arco visual: oscuro (e01-e08) -> transición (e09-e14) -> cálido/luz (e15-e28).
- Pexels b-roll en escenas de Dios/luz/amanecer (e06, e11, e21, e22, e24, e26, e27).
- Static text en frases clave (mayúsculas del guion).
- Motion deliberado: gancho zoom-in, desarrollo alternado, cierre zoom-out.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def scenes():
    E = []

    # === GANCHO (0:00) ===
    E.append({
        "text": "¿Y si no necesitas sanar lo que viviste, sino integrarlo y aceptarlo?",
        "ai": "Person standing alone in a dark room, single window with distant warm light, "
              "cinematic moody atmosphere, photorealistic, high detail",
        "q": "person dark room window light",
        "motion": "zoom-in",
        "static_text": ["¿Y si no necesitas SANAR?", "sino INTEGRARLO", "y ACEPTARLO?"],
        "static_size": 80,
        "static_sizes": {0: 110, 1: 110, 2: 110},
    })

    E.append({
        "text": "Todo el mundo te dice que tienes que sanar. Que hay algo en ti que está "
                "roto y que tienes que reparar. Que hasta que no lo hagas, no podrás ser feliz.",
        "ai": "Broken mirror reflecting distorted face, cold blue-gray light, dark moody "
              "atmosphere, fragments scattered on floor, cinematic, photorealistic",
        "q": "broken mirror reflection",
        "motion": "pan-right",
    })

    E.append({
        "text": "Y te lo creíste. Porque estás luchando, estás buscando respuestas "
                "y no sabes cómo resolver lo que te pasa.",
        "ai": "Person standing in a dark maze of shadows, multiple paths leading nowhere, "
              "dim cold light, cinematic moody, photorealistic",
        "q": "person maze shadows",
        "motion": "zoom-out",
    })

    E.append({
        "text": "Gurús, constelaciones, piedras, energías, frecuencias. Cada semana "
                "aparece una nueva moda que promete resolver lo que te duele.",
        "ai": "Purple glowing crystals on dark altar surrounded by lit candles and "
              "esoteric symbols, moody purple light, mystical atmosphere, no people, "
              "cinematic still life, photorealistic",
        "q": "crystals candles esoteric",
        "motion": "pan-left",
    })

    E.append({
        "text": "Y tú pruebas, y pruebas, y nada cambia de verdad.",
        "ai": "Exhausted person sitting surrounded by scattered objects and failed remedies, "
              "dim cold light, dark moody atmosphere, cinematic, photorealistic",
        "q": "exhausted person scattered objects",
        "motion": "zoom-in",
    })

    # === CONFIUSIÓN → TRANSICIÓN ===
    E.append({
        "text": "Y estás aquí. En este día. Con situaciones que te confunden. "
                "Con un nudo en el pecho que no tiene nombre.",
        "ai": "Misty mountain peaks shrouded in dense fog, cold blue-gray light, "
              "mysterious atmosphere, cinematic, photorealistic",
        "q": "misty mountain fog",
        "motion": "zoom-out",
        "stock": True,
    })

    E.append({
        "text": "Y lo que buscas es paz. Pero no llega. No viene mágicamente.",
        "ai": "Distant warm light glimmering at the end of a long dark corridor, "
              "out of reach, dark moody atmosphere, no people, cinematic, photorealistic",
        "q": "distant light dark corridor",
        "motion": "zoom-in",
    })

    E.append({
        "text": "¿Por qué? Porque estás mirando para afuera. Para todos los lugares "
                "que te ofrecen una solución, pero donde solo encuentras más confusión, "
                "más respuestas, más cosas que probar, pero no la salida.",
        "ai": "Person surrounded by arrows pointing in opposite directions, confused "
              "atmosphere, dark moody light, cinematic, photorealistic",
        "q": "person confused arrows",
        "motion": "pan-right",
    })

    # === LA CUEVA ===
    E.append({
        "text": "Es como una cueva oscura. Estás ahí, de pie, rodeada de sombras. "
                "Y crees que no hay forma de salir. Pero hay una puerta. Siempre la hubo.",
        "ai": "Dark cave interior with silhouette of person looking toward bright opening, "
              "dramatic chiaroscuro, cinematic, photorealistic",
        "q": "dark cave light opening",
        "motion": "zoom-out",
        "static_text": ["Siempre la hubo."],
        "static_size": 80,
        "static_sizes": {0: 110},
    })

    E.append({
        "text": "El problema no es la cueva. El problema es que no estás levantando "
                "la mirada. Estás tan enfocada en el suelo, en lo que te pesa, en todo "
                "aquello que llevas dentro, que no ves la luz que está justo enfrente de ti.",
        "ai": "Person looking down at the ground, bright warm light behind her back "
              "unnoticed, dramatic backlight, cinematic, photorealistic",
        "q": "person looking down light behind",
        "motion": "zoom-in",
    })

    # === LA LUZ / DIOS ===
    E.append({
        "text": "Porque la luz está esperando. No se fue. No se escondió. "
                "Está ahí, esperándote con paciencia. Esperando que le digas una cosa. Una sola.",
        "ai": "Golden sun rays piercing through mountain peaks at dawn, warm light "
              "streaming through mist, hopeful atmosphere, cinematic, photorealistic",
        "q": "sun rays mountain dawn",
        "motion": "pan-left",
        "stock": True,
        "light": True,
    })

    E.append({
        "text": "Dios mío, necesito tu ayuda. No sé cómo salir de esto. "
                "No sé cómo confiar en ti.",
        "ai": "Lit candle warm glow dark background, no people, cinematic still life",
        "q": "lit candle warm glow",
        "motion": "zoom-out",
        "stock_video": "e12.mp4",
        "static_text": ["\"DIOS MÍO, NECESITO TU AYUDA.\"", "\"NO SÉ CÓMO SALIR DE ESTO.\"", "\"NO SÉ CÓMO CONFIAR EN TI.\""],
        "static_size": 80,
        "static_sizes": {0: 100, 1: 90, 2: 90},
    })

    E.append({
        "text": "Esa frase. Esas palabras simples. Son la llave que abre la puerta "
                "de la cueva. No necesitas una oración perfecta. No necesitas saber las "
                "palabras correctas. Solo necesitas la verdad.",
        "ai": "Antique key on wooden surface with soft lateral warm light, cinematic "
              "still life, photorealistic, high detail",
        "q": "antique key wooden surface",
        "motion": "zoom-in",
    })

    E.append({
        "text": "Y aquí está la clave de todo. Lo que te voy a decir ahora puede "
                "cambiar la forma en que ves todo lo que viviste.",
        "ai": "Close-up of eyes opening with reflected warm light, dramatic cinematic "
              "lighting, photorealistic, high detail",
        "q": "eyes opening light reflection",
        "motion": "zoom-in",
        "boom": True,
        "static_text": ["CAMBIAR LA FORMA EN QUE", "VES TODO LO QUE VIVISTE"],
        "static_size": 80,
        "static_sizes": {0: 110, 1: 110},
    })

    # === INTEGRAR VS BORRAR ===
    E.append({
        "text": "No necesitas borrar lo que viviste. Lo que viviste ya pasó. "
                "No se puede deshacer. Y tratar de eliminarlo de tu historia, como si "
                "nunca hubiera ocurrido, muchas veces termina haciéndote más daño.",
        "ai": "Pages burning with ashes floating upward, warm fire light against dark "
              "background, cinematic, photorealistic",
        "q": "pages burning ashes",
        "motion": "pan-right",
    })

    E.append({
        "text": "Lo que necesitas es integrarlo. Aceptarlo. Decir: esto pasó. Me dolió. "
                "Me cambió. Pero eso no me define. Yo sigo de pie. Y lo que me pasó ahora "
                "es parte de lo que soy, sin que tenga que destruirme.",
        "ai": "Tree growing between rocks with visible roots, warm dawn light, "
              "resilient nature, cinematic, photorealistic",
        "q": "tree growing rocks dawn",
        "motion": "zoom-out",
        "static_text": ["Esto pasó.", "Me dolió.", "Me cambió.", "Pero no me define."],
        "static_size": 80,
        "static_sizes": {0: 110, 1: 110, 2: 110, 3: 110},
    })

    E.append({
        "text": "Aceptar no es justificar. No es decir que estuvo bien. "
                "Es reconocer que ya pasó. Y que tú, a pesar de eso, sigues aquí. "
                "Con una fuerza que no sabías que tenías.",
        "ai": "Silhouette standing on top of small mountain at sunrise, warm golden "
              "light, triumphant atmosphere, cinematic, photorealistic",
        "q": "silhouette mountain sunrise",
        "motion": "zoom-in",
        "light": True,
    })

    E.append({
        "text": "Y esa fuerza no viene solo de ti. Viene de algo más grande. "
                "De alguien que te sostuvo cuando tú no podías sostenerte. "
                "De alguien que te mira continuamente con amor.",
        "ai": "Person with hand on chest surrounded by warm enveloping golden light, "
              "peaceful expression, cinematic, photorealistic",
        "q": "person hand chest warm light",
        "motion": "zoom-out",
        "light": True,
    })

    # === CONFIANZA / FE ===
    E.append({
        "text": "Dios no te pide que olvides. No te pide que finjas que no pasó. "
                "Te pide que confíes. Que creas que lo que viviste no fue en vano. "
                "Que tiene un sentido que ahora no ves, pero que un día vas a entender.",
        "ai": "Mountain path disappearing into clouds with warm light at the end, "
              "hopeful journey atmosphere, cinematic, photorealistic",
        "q": "mountain path clouds light",
        "motion": "pan-left",
        "light": True,
    })

    E.append({
        "text": "Y cuando dices, con el corazón: Señor, necesito tu ayuda. "
                "No sé cómo confiar en ti. Pero quiero aprender. Algo cambia.",
        "ai": "Person kneeling in nature with soft environmental light, peaceful "
              "surrender atmosphere, cinematic, photorealistic",
        "q": "person kneeling nature light",
        "motion": "zoom-in",
        "static_text": ["\"Señor, necesito tu ayuda.\"", "Pero quiero aprender."],
        "static_size": 80,
        "static_sizes": {0: 110, 1: 90},
    })

    # === EL AMANECER ===
    E.append({
        "text": "No mágicamente. No de la noche a la mañana. Sino como el amanecer. "
                "¿Viste cómo sale el sol? No aparece de golpe. Va llegando despacio. "
                "Primero una luz tenue. Después un color. Después otro. "
                "Y de repente, todo es claro. Y te preguntas: ¿cómo no vi esto antes?",
        "ai": "Time-lapse mountain sunrise, colors changing from dark blue to gold "
              "to warm orange, gradual dawn light, cinematic, photorealistic",
        "q": "mountain sunrise time lapse",
        "motion": "zoom-out",
        "stock": True,
        "light": True,
        "static_text": ["¿Cómo no vi esto antes?"],
        "static_size": 80,
        "static_sizes": {0: 110},
    })

    E.append({
        "text": "Así es la paz que buscas. Llega como el amanecer. Gradual. Silenciosa. "
                "Pero segura. Y cuando llega, te das cuenta de que siempre estuvo ahí. "
                "Solo que tú todavía no podías verla.",
        "ai": "Mountains bathed in warm golden dawn light, mist rising gently, "
              "peaceful hopeful atmosphere, cinematic, photorealistic",
        "q": "mountains golden dawn light",
        "motion": "pan-right",
        "stock": True,
        "light": True,
    })

    # === NO NECESITAS / NECESITAS ===
    E.append({
        "text": "No necesitas constelaciones, ni energías, ni gurús. "
                "No necesitas pagar por algo que ya es tuyo. "
                "La paz no se compra. Se recibe. "
                "Es un regalo de Alguien que la tiene preparada para ti desde antes de que nacieras.",
        "ai": "Golden gift box wrapped in ribbon sitting on mountain rock with warm "
              "sunlight streaming through clouds, no people, peaceful atmosphere, "
              "cinematic still life, photorealistic",
        "q": "golden gift mountain sunlight",
        "motion": "zoom-in",
        "light": True,
    })

    E.append({
        "text": "Necesitas al Creador. Al que te conoce por tu nombre. "
                "Al que sabe cuántas veces lloraste en silencio. "
                "Al que te sostuvo en la peor noche de tu vida y no te soltó. "
                "Ese es el que está esperando que levantes la mirada.",
        "ai": "Majestic mountain peaks under clear sky with golden divine light, "
              "imposing and hopeful atmosphere, cinematic, photorealistic",
        "q": "majestic mountains golden light",
        "motion": "zoom-out",
        "stock": True,
        "light": True,
        "static_text": ["Necesitas al Creador."],
        "static_size": 80,
        "static_sizes": {0: 120},
    })

    E.append({
        "text": "Y cuando lo hagas, cuando finalmente mires hacia arriba en vez de "
                "hacia abajo, vas a ver algo que no esperabas. No vas a ver un castigo. "
                "No vas a ver un juicio. Vas a ver brazos abiertos, listos para abrazarte.",
        "ai": "Person with open arms facing mountains at dawn, warm golden light, "
              "welcoming embrace atmosphere, cinematic, photorealistic",
        "q": "person open arms mountains dawn",
        "motion": "zoom-in",
        "light": True,
    })

    E.append({
        "text": "Porque eso es lo que Dios hace. Te espera. Con paciencia. "
                "Con amor. Sin importar cuánto tardaste en llegar. "
                "Lo que importa es que llegaste.",
        "ai": "Mountain peaks at sunset with golden sky, warm peaceful atmosphere, "
              "divine love symbolism, cinematic, photorealistic",
        "q": "mountain sunset golden sky",
        "motion": "zoom-out",
        "stock": True,
        "light": True,
        "static_text": ["Lo que importa es que llegaste."],
        "static_size": 80,
        "static_sizes": {0: 110},
    })

    # === PAUSA + CTA ===
    E.append({
        "text": "Detente cinco segundos. Y dile: Señor, Dios mi Creador, necesito tu ayuda. "
                "No sé cómo confiar en ti. Pero quiero aprender.",
        "ai": "Mountains with clouds parting and golden rays of light descending, "
              "divine presence atmosphere, cinematic, photorealistic",
        "q": "mountains clouds parting light rays",
        "motion": "zoom-in",
        "stock": True,
        "light": True,
        "static_text": ["DETENTE 5 SEGUNDOS",
                        "\"Señor, Dios mi Creador,",
                        "necesito tu ayuda.",
                        "No sé cómo confiar en ti.",
                        "Pero quiero aprender.\""],
        "static_size": 80,
        "static_sizes": {0: 120, 1: 90, 2: 90, 3: 90, 4: 90},
    })

    E.append({
        "text": "Si esto te hizo bien, dale like y suscríbete al canal. "
                "Compártelo con alguien que necesite escuchar esto hoy. "
                "Y recuerda: estás en camino. "
                "Te mando un abrazo con todo mi corazón y te deseo abundantes bendiciones.",
        "ai": "Mountain peaks at golden sunset, warm hopeful light, cinematic "
              "finale atmosphere, photorealistic",
        "q": "mountain sunset finale",
        "motion": "zoom-in",
        "light": True,
        "static_text": ["ESTÁS EN CAMINO",
                        "Te mando un abrazo",
                        "con todo mi corazón",
                        "y te deseo",
                        "abundantes Bendiciones!"],
        "static_size": 68,
        "static_sizes": {0: 90, 4: 72},
    })

    return E


if __name__ == "__main__":
    for i, s in enumerate(scenes(), 1):
        print(f"e{i:02d}. {s['text'][:70]}...")
        print(f"    ai: {s['ai'][:60]}...")
        print(f"    motion: {s.get('motion')} | light: {s.get('light')} | "
              f"stock: {s.get('stock')} | static: {s.get('static_text')}")
        print()
