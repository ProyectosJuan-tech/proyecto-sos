#!/usr/bin/env python3
"""Videos largos horizontales para YOUTUBE (16:9, monetizables 8+ min).

Misma lógica que hacer_videos_nuevos.py pero con el pipeline YouTube:
- Fondo horizontal 1920x1080 (imagen IA 16:9 o b-roll Pexels landscape).
- Voz jorge/elena + karaoke word-by-word + BGM opcional.
- Los videos finales caen en VIDEOS_YOUTUBE/largos/.

Cómo crear un video largo nuevo:
1. Verificar en cerebro/wiki/contenido/frases-usadas.md que no se repite.
2. Agregar un dict en VIDEOS: name, scenes (text + ai + q + motion/stock).
3. Correr y registrar en cerebro/wiki/contenido/.
"""
import json
import os
import subprocess
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_caverna as m
import hacer_video_youtube as y

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJECT_ROOT, "videos", "youtube")
DEST = os.path.join(PROJECT_ROOT, "VIDEOS_YOUTUBE", "largos")
STYLE = ", cinematic, dark and moody, dramatic lighting, photorealistic, high detail"
LIGHT_STYLE = ", bright airy, high-key soft diffused window light, warm cream and sage palette, gentle highlights, no hard shadows, crisp and colorful, warm and hopeful, photorealistic, high detail"

VOICES = {
    "jorge": {"voice": "es-MX-JorgeNeural", "deepen": 0.92},
}

def _sabio_manipuladores_yt():
    import sabio_manipuladores as sm
    return sm.scenes(
        "Si te sirvió, suscribite y compartilo con alguien que hoy necesita callar "
        "con calma. El sabio te deja una frase cada día en el canal. Nos vemos "
        "mañana.")


VIDEOS = [
    {
        "name": "demo-monetizable",
        "bgm": True,
        "voices": ["jorge"],
        "scenes": [
            {"ai": "Woman in her fifties sitting by a window at golden hour, eyes closed, warm light, peaceful, photorealistic",
             "q": "woman window golden hour",
             "text": "Este es un video de prueba del pipeline de YouTube. Si lo ves, significa que todo funcionó: imagen horizontal, voz, karaoke y música de fondo.",
             "motion": "zoom-in"},
            {"ai": "Open book on a wooden table with warm morning light, dust particles, cozy",
             "q": "open book morning light",
             "text": "Acá va una segunda escena con otro fondo y movimiento de cámara. En un video real, cada escena desarrolla una idea del método.",
             "motion": "pan-right"},
            {"ai": "Silhouette walking toward sunrise on a hill, golden landscape, hopeful",
             "q": "silhouette sunrise hill",
             "text": "El video largo horizontal es el formato que monetiza en YouTube: más de ocho minutos, con anuncios y retención. Suscríbete.",
             "motion": "zoom-out"},
        ],
    },
    {
        "name": "sabio-manipuladores",
        "bgm": True,
        "rate": "-8%",
        "voices": ["jorge"],
        "scenes": _sabio_manipuladores_yt(),
    },
    {
        "name": "oracion-preocupaciones",
        "bgm": True,
        "rate": "-8%",
        "gap_secs": 1.5,
        "voices": ["jorge"],
        "scenes": [
            {"ai": "A man in his fifties in a plain shirt kneeling at the foot of a sunlit window, hands together in prayer, eyes closed, soft warm morning light diffusing through sheer curtains, intimate observational photography, photorealistic, high detail",
             "q": "man praying kneeling window light",
             "text": "Señor, aquí estoy. [1200] Por unos minutos quiero detenerme y estar contigo. [600]",
             "motion": "zoom-in"},
            {"ai": "A woman in her fifties kneeling beside her bed hands joined in prayer, profile view, quiet bedroom in soft morning light, calm intimate atmosphere, photorealistic, high detail",
             "q": "woman praying beside bed",
             "text": "Dejo a un lado lo que estaba haciendo, [600] las preocupaciones, [600] las cosas pendientes y todo aquello que ocupa mi cabeza.",
             "motion": "pan-right"},
            {"ai": "A man in his fifties in a plain shirt kneeling with hands together in prayer facing a bright window, light streaming onto his face, serene, warm hopeful glow, photorealistic, high detail",
             "q": "man praying facing window light",
             "text": "Y te pido, Señor, que envíes sobre mí tu Espíritu Santo. [1200] Ven, Espíritu Santo. [1500]",
             "motion": "zoom-in"},
            {"ai": "A woman in her fifties kneeling with open palms facing upward in prayer, soft light washing over her hands, calm serene expression, warm cream tones, photorealistic, high detail",
             "q": "woman praying open palms",
             "text": "Ilumina mi corazón. [1200] Dame serenidad. [1200] Ayúdame a estar aquí, delante de Dios, con todo lo que soy y con todo lo que estoy viviendo.",
             "motion": "zoom-out"},
            {"ai": "A man in his fifties kneeling beside his bed with hands together in prayer, three-quarter view, quiet bedroom at dawn with soft window light, intimate and peaceful, photorealistic, high detail",
             "q": "person praying hands",
             "text": "No quiero esconderte nada. [1200] Tú conoces mis preocupaciones antes de que pueda expresarlas.",
             "motion": "pan-left",
             "stock": True},
            {"ai": "A woman in her fifties kneeling with folded hands by a window, gentle morning light, soft shadows, restful and safe atmosphere, warm palette, photorealistic, high detail",
             "q": "woman praying candle",
             "text": "Conoces mis pensamientos, [600] mis temores, [600] mis cansancios y también aquellas cosas que no sé cómo explicar. [1200] Por eso hoy vengo a ti tal como estoy.",
             "motion": "zoom-in",
             "stock": True},
            {"ai": "A man in his fifties in a plain shirt kneeling facing a tall window, hands together in prayer, warm afternoon light crossing the room, contemplative, photorealistic, high detail",
             "q": "man praying tall window",
             "text": "Señor, hay cosas que me preocupan. [1200] Algunas tienen que ver con mi familia. [1200] Otras con mi trabajo, con mi futuro, con mi situación económica o con decisiones que tengo que tomar.",
             "motion": "pan-right"},
            {"ai": "A woman in her fifties kneeling beside her bed with hands together in prayer, low warm light, gentle and tender mood, photorealistic, high detail",
             "q": "woman praying beside bed low light",
             "text": "Quizás hay una conversación que me preocupa. [1200] Una persona que quiero y por la que estoy sufriendo. [1200] Algo que no salió como esperaba. [1200] Algo que no puedo cambiar. [1200] Tú sabes lo que es.",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling with open palms facing upward toward soft light, hands gently raised, glowing warm illumination, hopeful, photorealistic, high detail",
             "q": "man praying open palms upward",
             "text": "Y hoy quiero ponerlo delante de ti. [1500]",
             "motion": "zoom-out"},
            {"ai": "A man in his fifties kneeling with hands together in prayer facing a window, calm steady morning light, determined and peaceful expression, photorealistic, high detail",
             "q": "man praying steady light",
             "text": "Señor, ayúdame a recordar que no tengo que cargarlo todo yo solo. [1200] Hay cosas que puedo hacer, [600] decisiones que debo tomar y responsabilidades que me corresponden.",
             "motion": "pan-left"},
            {"ai": "A woman in her fifties kneeling with open palms facing upward, hands lifted in surrender, soft bright light, warm and trusting mood, photorealistic, high detail",
             "q": "woman praying hands lifted",
             "text": "Pero también hay cosas que no están en mis manos. [1200] Y esas cosas quiero entregártelas. [1200] Te entrego aquello que no puedo controlar. [1200] Te entrego aquello que todavía no entiendo. [1200] Te entrego aquello que me da miedo. [1500]",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling beside a sunlit window with hands together in prayer, gentle breeze moving the curtain, serene, photorealistic, high detail",
             "q": "man praying sunlit window",
             "text": "Ayúdame a hacer mi parte con responsabilidad y, [600] después, [600] a confiar en ti con aquello que queda fuera de mi alcance.",
             "motion": "pan-right"},
            {"ai": "A man in his fifties kneeling with hands together in prayer, head slightly bowed, quiet humble atmosphere, soft window light, photorealistic, high detail",
             "q": "man praying head bowed",
             "text": "Señor, también quiero pedirte perdón. [1200] Perdóname por las veces que actué mal. [1200] Por las palabras que dije sin pensar. [600]",
             "motion": "zoom-in"},
            {"ai": "A woman in her fifties kneeling with folded hands, gentle remorseful mood, soft warm light from a window, tender and humble, photorealistic, high detail",
             "q": "woman praying folded hands",
             "text": "Por las veces que dejé que el orgullo hablara por mí. [1200] Por las veces que respondí desde el enojo, [600] el miedo o la indiferencia.",
             "motion": "pan-left"},
            {"ai": "A man in his fifties kneeling beside his bed with hands together in prayer, low gentle light, peaceful reconciliation mood, photorealistic, high detail",
             "q": "hands clasped prayer",
             "text": "Perdóname también por las veces que desconfié de ti. [1200] Por querer tener el control de todo. [1200]",
             "motion": "zoom-out",
             "stock": True},
            {"ai": "A man in his fifties kneeling with open palms facing upward, soft warm light over his hands, gentle and open-hearted, photorealistic, high detail",
             "q": "man praying open heart palms",
             "text": "Por olvidar que tú estás conmigo incluso cuando no entiendo lo que está sucediendo. [1200] Dame un corazón humilde para reconocer mis errores y la fuerza para comenzar nuevamente.",
             "motion": "pan-right"},
            {"ai": "A man in his fifties in a plain shirt kneeling facing a bright window with warm golden morning light, hands together in prayer, grateful peaceful expression, photorealistic, high detail",
             "q": "gratitude sunset silhouette",
             "text": "Y ahora, Señor, quiero darte gracias. [1200] Gracias por la vida. [1200] Gracias por las personas que has puesto en mi camino.",
             "motion": "zoom-in",
             "stock": True},
            {"ai": "A woman in her fifties kneeling with folded hands in a cozy warm room, soft golden light, grateful serene mood, photorealistic, high detail",
             "q": "woman praying grateful warm",
             "text": "Gracias por el alimento, [600] por un lugar donde descansar, [600] por las oportunidades que he recibido y también por las pequeñas cosas que muchas veces dejo de mirar.",
             "motion": "pan-left"},
            {"ai": "A man in his fifties kneeling with hands together in prayer by a window with soft evening light, warm peaceful glow, photorealistic, high detail",
             "q": "man praying evening window",
             "text": "Gracias por este día. [1200] Gracias incluso por aquello que todavía no comprendo. [1200]",
             "motion": "zoom-out"},
            {"ai": "A woman in her fifties kneeling with open palms gently resting, soft window light, reflective warm mood, photorealistic, high detail",
             "q": "hands grateful light",
             "text": "Piensa ahora, delante de Dios, [1200] en algo concreto por lo que puedas darle gracias. [1200] Puede ser algo muy sencillo. [1200]",
             "motion": "pan-right",
             "stock": True},
            {"ai": "A man in his fifties kneeling with hands together in prayer, still and focused, gentle light, photorealistic, high detail",
             "q": "warm candle hands",
             "text": "Una persona. [1200] Un momento. [1200] Una oportunidad. [1200] Un pequeño regalo de este día. [1200]",
             "motion": "zoom-in",
             "stock": True},
            {"ai": "A man in his fifties in profile kneeling with hands together in prayer, soft warm side light, intimate and reverent, photorealistic, high detail",
             "q": "person praying church",
             "text": "Y simplemente dile: [1200] Gracias, Señor. [1500]",
             "motion": "zoom-out",
             "stock": True},
            {"ai": "A man in his fifties kneeling facing a large bright window, hands together in prayer, luminous warm light wrapping the room, trusting and safe, photorealistic, high detail",
             "q": "sunlight through window morning",
             "text": "Señor, tú eres bueno. [1200] Gracias porque no estoy solo. [1200] Gracias porque tu presencia no depende de que mi vida esté en orden.",
             "motion": "zoom-in",
             "stock": True},
            {"ai": "A man in his fifties kneeling with open palms facing upward to soft heavenly light, gently glowing, adoring peaceful expression, photorealistic, high detail",
             "q": "peaceful sunrise field",
             "text": "Tú permaneces cuando todo cambia. [1200] Tú permaneces cuando tengo respuestas y también cuando tengo preguntas. [1500] Por eso hoy quiero alabarte y reconocer tu bondad.",
             "motion": "pan-left",
             "stock": True},
            {"ai": "A man in his fifties kneeling beside his bed with hands together in prayer, soft protective warm light, tender caring mood, photorealistic, high detail",
             "q": "hands prayer protection",
             "text": "Cuida de mí, Señor. [1200] Protege mi vida y la vida de las personas que amo. [1200] Acompaña a mi familia.",
             "motion": "zoom-in",
             "stock": True},
            {"ai": "A woman in her fifties kneeling with folded hands, gentle compassionate mood, soft warm window light, caring and hopeful, photorealistic, high detail",
             "q": "candle prayer comfort",
             "text": "Cuida a quienes hoy están enfermos, [600] cansados, preocupados o atravesando momentos difíciles. [1200]",
             "motion": "pan-right",
             "stock": True},
            {"ai": "A man in his fifties kneeling by a window with warm golden light, hands together in prayer, hopeful refuge mood, photorealistic, high detail",
             "q": "man praying refuge light",
             "text": "Sé refugio para quien tiene miedo y esperanza para quien siente que ya no puede más. [1500]",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling with open palms facing upward, hands gently raised as in offering, soft warm light, trusting surrender, photorealistic, high detail",
             "q": "offering hands upward",
             "text": "Y ahora, Señor, quiero ponerme en tus manos. [1500] Tomo todo aquello que me preocupa y lo deposito delante de ti. [1500]",
             "motion": "zoom-out",
             "stock": True},
            {"ai": "A man in his fifties kneeling with hands together in prayer, centered and calm, soft morning light, resolved peaceful mood, photorealistic, high detail",
             "q": "open hands surrender light",
             "text": "No porque deje de importarme. [1200] Sino porque ya no quiero vivir como si todo dependiera de mí. [1500]",
             "motion": "pan-left",
             "stock": True},
            {"ai": "A man in his fifties kneeling facing a window with clear warm light, hands together in prayer, teaching trust, serene, photorealistic, high detail",
             "q": "man praying trusting window",
             "text": "Enséñame a confiar. [1200] Enséñame a hacer lo que me corresponde y a dejar en tus manos aquello que no puedo resolver. [1500]",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling with hands together in prayer, gentle reassuring light, brave calm expression, photorealistic, high detail",
             "q": "man praying brave calm",
             "text": "Cuando tenga miedo, [1200] recuérdame que estás conmigo. [1200] Cuando no vea el camino, [1200] ayúdame a dar el siguiente paso.",
             "motion": "pan-right"},
            {"ai": "A man in his fifties kneeling with open palms facing upward, soft steady light, trusting rest mood, photorealistic, high detail",
             "q": "man praying resting palms",
             "text": "Cuando quiera controlar todo, [1200] enséñame a descansar en ti. [1200] Cuando las cosas no salgan como esperaba, [1200] dame la fe para seguir caminando.",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling with hands together in prayer, humble and open, warm window light, photorealistic, high detail",
             "q": "man praying humble open",
             "text": "Señor, hoy no te pido tener todas las respuestas. [1200] Te pido tener un corazón capaz de confiar en ti. [1500]",
             "motion": "zoom-out"},
            {"ai": "A man in his fifties kneeling beside his bed with hands together in prayer, soft warm twilight light, trusting hopeful mood, photorealistic, high detail",
             "q": "path walk sunrise hope",
             "text": "Tú conoces el camino. [1200] Tú conoces mi vida. [1200] Tú conoces aquello que necesito incluso antes de que pueda pedirlo. [1200]",
             "motion": "pan-left",
             "stock": True},
            {"ai": "A man in his fifties kneeling facing a bright window with soft golden light, hands together in prayer, placing trust with closed eyes, warm and safe, photorealistic, high detail",
             "q": "sunlight window peaceful room",
             "text": "Por eso dejo delante de ti mis preocupaciones, [600] mis planes, [600] mis temores y mi futuro. [1500] Me pongo en tus manos.",
             "motion": "zoom-in",
             "stock": True},
            {"ai": "A man in his fifties kneeling with open palms facing upward, gentle radiant light, guided and peaceful, photorealistic, high detail",
             "q": "man praying guided palms",
             "text": "Quédate conmigo, Señor. [1200] Guía mis pasos. [1200]",
             "motion": "pan-right"},
            {"ai": "A man in his fifties kneeling with hands together in prayer, calm wise light from a window, serene wisdom, photorealistic, high detail",
             "q": "man praying wisdom light",
             "text": "Dame sabiduría para decidir, [600] fortaleza para afrontar lo que venga y paz para aceptar aquello que hoy no puedo cambiar. [1500]",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling by a window with warm evening light, hands together in prayer, honest and tender moment, photorealistic, high detail",
             "q": "man praying honest tender",
             "text": "Y cuando vuelva a preocuparme, [1200] ayúdame a recordar que puedo volver a ti. [1200] Que puedo detenerme. [1200] Respirar. [1200] Y decirte una vez más: [1200] Señor, confío en ti. [1500]",
             "motion": "pan-left"},
            {"ai": "A man in his fifties kneeling facing a luminous window, hands together in prayer, receiving light over his head, humble grateful, photorealistic, high detail",
             "q": "man praying receiving light",
             "text": "Padre bueno, recibe esta oración. [1200] Recibe todo aquello que hoy llevo en el corazón. [1200]",
             "motion": "zoom-in"},
            {"ai": "A man in his fifties kneeling by a window with warm golden sunset light, hands together in prayer, peaceful hopeful glow filling the room, photorealistic, high detail",
             "q": "sunrise horizon hope",
             "text": "Y permite que, después de estos minutos contigo, [600] pueda continuar mi día con un poco más de paz, [600] con un poco más de esperanza y con la certeza de que no camino solo. [1500]",
             "motion": "pan-right",
             "stock": True},
            {"ai": "A man in his fifties kneeling with hands together in prayer by a window, soft warm light, serene and grateful closing moment, wide gentle framing, photorealistic, high detail",
             "q": "man praying closing light",
             "text": "En el nombre del Padre, [600] del Hijo y del Espíritu Santo. [1500] Amén.",
             "motion": "zoom-out"},
        ],
    },
]


def _muerte_yt():
    import muerte_scenes as ms
    return [dict(s, light=(i in ms.LIGHT))
            for i, s in enumerate(ms.scenes_muerte(
                "Suscríbete, dale like y comenta."), start=1)]


VIDEOS.append({
    "name": "muerte",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _muerte_yt(),
})


def _manipulacion_yt():
    import manipulacion_scenes as ms
    return ms.scenes(
        "Si te gustó, suscribite, me ayudás mucho. Dale un like y activá la "
        "campanita para que YouTube te avise cada vez que subo otro video.")


VIDEOS.append({
    "name": "manipulacion",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _manipulacion_yt(),
})


def _oracion_dormir_scenes():
    import oracion_dormir_scenes as ods
    scenes = ods.scenes()
    _TRANS = ["fade-soft", "fade", "blur-in", "zoom-fade", "fade-up"]
    FONT_CORMORANT = "/home/juan/snap/code/259/.local/share/fonts/CormorantGaramond-VariableFont_wght.ttf"
    # Transiciones suaves rotadas e intercaladas en el video en curso.
    # (se quitaron slide/slide-up/wipe-soft: deslizamientos tipo PowerPoint)
    for i, s in enumerate(scenes):
        s.setdefault("trans", {"style": _TRANS[i % len(_TRANS)], "dur": 0.8})
        if i == 0:
            # Intro: titulo en MAYUSCULAS con Cormorant Garamond
            s["static_text"] = ["ORACIÓN ANTES DE DORMIR"]
            s["static_font"] = FONT_CORMORANT
            s["static_size"] = 150
    return scenes


VIDEOS.append({
    "name": "oracion-dormir-gracias",
    "bgm": True,
    "rate": "-8%",
    "gap_secs": 1.5,
    "voices": ["jorge"],
    "scenes": _oracion_dormir_scenes(),
})


# V2 (2026-08-16): mismas escenas/guion, imágenes/videos del set descargado
# en la carpeta de imágenes del video. Solo N3 (galletita) y N6
# (calendario) quedan IA porque el set no trae equivalente.
V2_IMG = {
    1: "img1", 2: "img2", 3: "img5", 4: "hombre_oficina", 5: "hombre_cansado",
    6: "img2", 7: "img4", 8: "img4", 9: "hombre_oficina", 10: "img5",
    11: "img5", 12: "capatillas", 13: "img_cafe", 14: "img_cafe",
    15: "hombre_cansado", 16: "img_cafe", 17: "N3", 18: "ropa_preparada",
    19: "cosas_ordenadas", 20: "cosas_ordenadas", 21: "img5", 22: "img_cafe",
    23: "img_cafe", 24: "ropa_preparada", 25: "hombre_pensando_camino",
    26: "cosas_ordenadas", 27: "plato_sucio", 28: "N6", 29: "mujer_leyendo",
    30: "img3", 31: "hombre_pensando_camino", 32: "hombre_pensando_camino",
    33: "hombre_pensando_camino", 34: "img1", 35: "img3", 36: "plato_sucio",
    37: "img1", 38: "img3",
}


def _habitos_v2_yt():
    import habitos_scenes as hs
    scenes = hs.scenes()
    for i, s in enumerate(scenes, start=1):
        s["img"] = V2_IMG.get(i, s["img"])
    return scenes


def _habitos_yt():
    import habitos_scenes as hs
    return hs.scenes()


VIDEOS.append({
    "name": "habitos-sistema",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _habitos_yt(),
})

VIDEOS.append({
    "name": "habitos-sistema-v2",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _habitos_v2_yt(),
})


def _florecer_yt():
    import florecer_scenes as fs
    return fs.scenes()


VIDEOS.append({
    "name": "florecer-largo",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _florecer_yt(),
})


def _integrar_yt():
    import integrar_scenes as s
    return s.scenes()


VIDEOS.append({
    "name": "integrar-no-sanar",
    "bgm": True,
    "voices": ["jorge"],
    "rate": "-8%",
    "scenes": _integrar_yt(),
})


def _oracion_hijos_yt():
    _TRANS = ["fade-soft", "fade", "blur-in"]
    _FONT_TITLE = "/home/juan/snap/code/259/.local/share/fonts/CormorantGaramond-VariableFont_wght.ttf"
    scenes = [
        # ── TÍTULO ──
        {"static_text": ["ORACIÓN POR MIS HIJOS"], "static_font": _FONT_TITLE, "static_size": 140,
         "ai": "Warm sunset over a peaceful valley, golden light, soft clouds, warm amber tones, photorealistic, high detail",
         "q": "sunset peaceful valley warm"},
        # ── VIDEO PEXELS (e01-e11) ──
        {"text": "Señor, [400] hoy quiero poner a mis hijos en tus manos. [1200]",
         "ai": "Soft lit candle on a wooden table, warm glow, peaceful, photorealistic",
         "q": "candle warm glow peaceful", "motion": "zoom-in", "stock": True},
        {"text": "Antes de pedirte cualquier cosa por ellos, [400] quiero darte gracias. [800]",
         "ai": "Soft warm window light streaming through sheer curtains, morning, photorealistic",
         "q": "window light warm morning", "motion": "pan-right", "stock": True},
        {"text": "Gracias por sus vidas. [600]\nGracias porque me los confiaste. [600]",
         "ai": "Warm sunrise over calm landscape, golden light, hopeful, photorealistic",
         "q": "sunrise golden light", "motion": "zoom-out", "stock": True},
        {"text": "Gracias por cada momento que he podido compartir con ellos, [400] por sus risas, [400] por sus preguntas, [400] por sus luchas, [400] incluso por esas etapas que a veces no sé cómo acompañar. [800]",
         "ai": "Family dinner table warm light home, candid, photorealistic",
         "q": "family dinner warm light", "motion": "pan-left", "stock": True},
        {"text": "Tu Palabra dice que los hijos son un regalo del Señor. [600]\nY hoy quiero recordar eso. [800]",
         "ai": "Open Bible on wooden table with soft morning light, warm, photorealistic",
         "q": "open book morning light", "motion": "zoom-in", "stock": True},
        {"text": "No son una posesión mía. [600]\nNo son un proyecto que tengo que controlar. [600]\nSon personas que tú amas incluso más que yo. [1200]",
         "ai": "Hands gently holding a small plant seedling, soft warm light, photorealistic",
         "q": "hands plant seedling warm light", "motion": "pan-right", "stock": True},
        {"text": "Por eso, Señor, [400] te pido que me enseñes a ser padre. [600]\nQue me enseñes a ser madre. [1200]",
         "ai": "Mother holding sleeping child warm window light, tender, photorealistic",
         "q": "mother holding child window light", "motion": "zoom-out", "stock": True},
        {"text": "Dame sabiduría para saber cuándo hablar [400] y cuándo guardar silencio. [800]",
         "ai": "Person sitting quietly by window soft light, contemplative, photorealistic",
         "q": "person window quiet contemplative", "motion": "pan-left", "stock": True},
        {"text": "Enséñame a corregir sin humillar. [400]\nA poner límites sin destruir. [400]\nA enseñar sin imponerles mis propios miedos. [1200]",
         "ai": "Parent and child walking together in nature, warm light, photorealistic",
         "q": "parent child walking nature", "motion": "zoom-in", "stock": True},
        {"text": "Tu Palabra nos recuerda: [800]\n«Padres, no irriten a sus hijos; [400] al contrario, [400] edúquenlos, [400] corrigiéndolos y aconsejándolos, [400] según el espíritu del Señor». [1200]",
         "ai": "Hands gently holding an old book with warm candle light, photorealistic",
         "q": "hands holding book candle light", "motion": "pan-right", "stock": True},
        {"text": "Señor, [400] ayúdame a vivir estas palabras. [1200]\nQue mi autoridad no nazca de la ira, [400] ni del orgullo, [400] ni de la necesidad de tener siempre la razón. [800]",
         "ai": "Person kneeling in warm soft light, humble posture, photorealistic",
         "q": "person hands praying window light", "motion": "zoom-out", "stock": True},
        # ── FOTO PEXELS (e12-e22) ──
        {"text": "Que pueda guiarlos con paciencia. [600]\nQue cuando tenga que corregirlos, [400] pueda hacerlo buscando su bien [400] y no simplemente descargando mi enojo. [1200]",
         "ai": "Parent speaking gently to child warm light, soft moment, photorealistic",
         "q": "adult hands guiding warm light soft", "motion": "zoom-in", "stock_photo": True},
        {"text": "Y cuando me equivoque con ellos, [600] dame la humildad para pedirles perdón. [1200]",
         "ai": "Hands clasped together soft warm light, humble, photorealistic",
         "q": "hands clasped warm light", "motion": "pan-left", "stock_photo": True},
        {"text": "No permitas que mis palabras de enojo [600] se conviertan en heridas que ellos carguen durante años. [1200]",
         "ai": "Empty chair by a window soft morning light, lonely, photorealistic",
         "q": "empty chair window morning", "motion": "zoom-out", "stock_photo": True},
        {"text": "No permitas que mis exigencias [600] les hagan creer que nunca son suficientes. [1200]",
         "ai": "Child's small shoes by the door warm light, tender, photorealistic",
         "q": "empty shoes at doorway warm light", "motion": "pan-right", "stock_photo": True},
        {"text": "Enséñame a recordar que también están aprendiendo a vivir. [1200]",
         "ai": "Child's hand holding an adult's hand walking, warm light, photorealistic",
         "q": "child hand adult hand walking", "motion": "zoom-in", "stock_photo": True},
        {"text": "Señor, [400] dame ojos para ver lo que ellos necesitan [400] y no solamente lo que yo espero de ellos. [1200]",
         "ai": "Person looking out a window soft warm light, reflective, photorealistic",
         "q": "person window reflective", "motion": "pan-left", "stock_photo": True},
        {"text": "Ayúdame a conocer sus preocupaciones, [400] sus amistades, [400] sus miedos, [400] sus sueños [400] y esas cosas que quizá todavía no se animan a contarme. [1200]",
         "ai": "Two coffee cups on a table soft warm light, intimate, photorealistic",
         "q": "coffee cups warm intimate", "motion": "zoom-out", "stock_photo": True},
        {"text": "Que mi casa pueda ser para ellos un lugar donde puedan volver. [1200]\nUn lugar donde encuentren verdad, [600] pero también misericordia. [800]",
         "ai": "Warm home entrance with soft light, welcoming, photorealistic",
         "q": "home entrance warm welcoming", "motion": "pan-right", "stock_photo": True},
        {"text": "Un lugar donde puedan aprender, [400] equivocarse, [400] pedir perdón [400] y comenzar nuevamente. [1200]",
         "ai": "Open door with warm light coming through, inviting, photorealistic",
         "q": "open door warm light", "motion": "zoom-in", "stock_photo": True},
        {"text": "Señor, [400] protege a mis hijos. [1200]\nProtégelos de aquello que yo no puedo ver. [800]",
         "ai": "Hands cupped together holding warm light, protective, photorealistic",
         "q": "hands cupped warm light", "motion": "pan-left", "stock_photo": True},
        {"text": "De las malas decisiones. [600]\nDe las personas que puedan hacerles daño. [600]\nDe las mentiras que puedan hacerles perder su valor. [600]\nDe todo aquello que quiera alejarlos del bien. [1200]",
         "ai": "Path through a dark forest toward distant light, hopeful, photorealistic",
         "q": "path forest light hopeful", "motion": "zoom-out", "stock_photo": True},
        # ── IMAGEN IA (e23-e33) ──
        {"text": "Y cuando yo no pueda acompañarlos, [600] acompañalos tú. [1200]\nCuando estén lejos de casa, [400] quédate con ellos. [800]",
         "ai": "Close-up of weathered hands gently resting on an open Bible, warm candlelight casting soft shadows on worn pages, intimate devotional moment, shot on 50mm f/1.8, shallow depth of field, warm amber tones, photorealistic, high detail",
         "q": "hands bible candlelight", "motion": "zoom-in"},
        {"text": "Cuando estén atravesando una dificultad que no conozco, [400] sostenlos. [800]\nCuando tengan que elegir entre el bien y el mal, [400] dales luz para reconocer el camino correcto. [1200]",
         "ai": "Elderly woman kneeling by a window, profile view, warm golden light streaming through lace curtains onto her face, serene devoted expression, soft linen clothing, intimate observational photography, photorealistic, high detail",
         "q": "woman praying window profile", "motion": "pan-right"},
        {"text": "Señor, [400] también te pido por mi propia ansiedad. [1200]",
         "ai": "Person sitting alone on a wooden bench in a quiet garden, morning mist, soft diffused light, contemplative posture, hands resting on lap, editorial lifestyle photography, photorealistic, high detail",
         "q": "person garden bench morning", "motion": "zoom-out"},
        {"text": "A veces quiero protegerlos de todo. [800]\nQuiero evitarles el sufrimiento, [400] las decepciones, [400] los errores. [800]",
         "ai": "Mother and child silhouette walking toward sunset on a quiet path, warm golden backlight, long shadows on the ground, tender guiding moment, cinematic natural light, photorealistic, high detail",
         "q": "mother child sunset silhouette", "motion": "pan-left"},
        {"text": "Pero sé que no puedo caminar por ellos. [1200]\nEnséñame a confiar en ti. [600]\nEnséñame a acompañarlos sin querer controlar cada paso. [1200]",
         "ai": "Close-up of a parent's open empty hands facing upward, soft warm window light catching the palms, gesture of surrender and trust, intimate observational photography, photorealistic, high detail",
         "q": "open hands surrender light", "motion": "zoom-in"},
        {"text": "A enseñarles a caminar [600] y también a dejarlos caminar. [1200]\nQue puedan crecer sabiendo que no están solos, [600] pero también aprendiendo a tomar decisiones con responsabilidad. [1200]",
         "ai": "Empty wooden path through a sunlit forest, golden light filtering through green leaves, dappled shadows on the ground, inviting forward journey, warm natural tones, photorealistic, high detail",
         "q": "forest path golden light", "motion": "pan-right"},
        {"text": "Dame la sabiduría que viene de ti. [800]",
         "ai": "Person writing in a journal at a wooden desk, soft warm lamp light, books nearby, quiet evening atmosphere, intimate editorial photography, photorealistic, high detail",
         "q": "person writing journal lamp", "motion": "zoom-out"},
        {"text": "Que pueda transmitirles una fe que no sea solamente palabras, [600] sino una forma de vivir. [1200]",
         "ai": "Close-up of hands releasing upward toward soft glowing light, gesture of offering and faith, warm tones, ethereal atmosphere, photorealistic, high detail",
         "q": "hands releasing upward light", "motion": "zoom-in"},
        {"text": "Que ellos puedan aprender de mi manera de tratar a los demás, [400] de mi manera de pedir perdón, [400] de mi manera de enfrentar las dificultades, [400] de mi manera de confiar en ti. [1200]",
         "ai": "Two pairs of hands exchanging a warm cup of tea, close-up, soft warm window light, gentle caring gesture, warm cream tones, photorealistic, high detail",
         "q": "hands sharing tea warm light", "motion": "pan-left"},
        {"text": "Señor, [400] si alguna vez mis hijos se alejan, [800] no permitas que yo deje de amarlos. [1200]\nSi se equivocan, [600] dame paciencia. [800]\nSi toman caminos que me preocupan, [600] dame sabiduría para saber cómo acercarme. [1200]",
         "ai": "Person kneeling by a window, profile view, soft morning light illuminating their face, quiet devoted posture, warm intimate atmosphere, observational photography, photorealistic, high detail",
         "q": "person kneeling window profile", "motion": "zoom-out"},
        {"text": "Y si algún día ya no necesitan que les diga qué hacer, [800] enséñame a seguir estando cerca sin invadir su vida. [1200]\nPorque quiero que sepan que siempre tendrán alguien que los ama. [1200]",
         "ai": "Person standing at a doorway looking outward, soft warm light behind them, silhouette framing, contemplative farewell moment, warm natural tones, photorealistic, high detail",
         "q": "person doorway looking out", "motion": "pan-right"},
        {"text": "Y sobre todo, [600] quiero que descubran que tienen, principalmente, un Padre celestial [600] que nunca deja de amarlos. [1200]",
         "ai": "Open sky at dawn with soft golden light breaking through clouds, vast hopeful landscape below, warm amber tones, spiritual atmosphere, photorealistic, high detail",
         "q": "dawn sky golden light clouds", "motion": "zoom-in"},
        {"text": "Señor, [400] hoy te entrego a mis hijos. [1200]\nTe entrego sus caminos, [400] sus decisiones, [400] sus amistades, [400] sus estudios, [400] su trabajo, [400] sus relaciones, [400] sus sueños [400] y también sus heridas. [1200]",
         "ai": "Person kneeling in soft warm light, hands open in offering gesture, humble devoted posture, quiet room with window light, intimate observational photography, photorealistic, high detail",
         "q": "person kneeling offering light", "motion": "pan-left"},
        {"text": "Ponlos bajo tu cuidado. [800]\nY cuida también mi corazón, [600] para que no quiera ocupar el lugar que solamente te corresponde a ti. [1200]\nAyúdame a hacer mi parte [400] con amor, paciencia y sabiduría, [600] y a confiar en ti con aquello que no puedo controlar. [1200]",
         "ai": "Hands folded gently over a heart, soft warm light, intimate close-up, warm skin tones, devotional mood, photorealistic, high detail",
         "q": "hands folded heart warm light", "motion": "zoom-out"},
        {"text": "Si el Señor no edifica la casa, [600] en vano trabajan quienes la construyen. [1200]\nPor eso, Señor, [800] edifica nuestra casa. [1200]\nQuédate en nuestra familia. [800]",
         "ai": "Warm family home exterior at golden hour, soft light in windows, welcoming garden, peaceful residential scene, warm natural tones, photorealistic, high detail",
         "q": "family home golden hour", "motion": "zoom-in"},
        {"text": "Enséñanos a amarnos. [400]\nEnséñanos a perdonarnos. [400]\nEnséñanos a hablarnos con respeto. [400]\nEnséñanos a corregirnos sin destruirnos. [400]\nEnséñanos a confiar en ti. [1200]\nY cuando yo no sepa qué hacer, [600] recuérdame que puedo volver a ti. [1200]",
         "ai": "Warm living room with soft afternoon light, comfortable chairs, family photos on the wall, plants, lived-in cozy atmosphere, photorealistic, high detail",
         "q": "warm living room afternoon light", "motion": "pan-right"},
        {"text": "Hoy pongo a mis hijos en tus manos. [1200]\nCuídalos. [400]\nGuíalos. [400]\nProtégelos. [400]\nDales sabiduría. [400]\nDales un corazón bueno. [600]\nY ayúdalos a descubrir el camino que tú tienes preparado para sus vidas. [1200]",
         "ai": "Person standing at a sunrise horizon, facing the light, silhouette with warm golden backlight, vast open landscape, hopeful new beginning, cinematic natural light, photorealistic, high detail",
         "q": "person sunrise horizon hopeful", "motion": "pan-left"},
        {"text": "Y a mí, Señor, [800] dame la gracia de ser para ellos [600] un padre o una madre que sepa amar, [400] corregir, [400] escuchar, [400] perdonar [400] y dejar en tus manos aquello que no puedo controlar. [1500]\nAmén.",
         "ai": "Warm sunset over a peaceful valley, golden light fading gently, tranquil ending atmosphere, soft warm tones, photorealistic, high detail",
         "q": "sunset peaceful valley warm", "motion": "zoom-out"},
    ]
    for i, s in enumerate(scenes):
        s.setdefault("trans", {"style": _TRANS[i % len(_TRANS)], "dur": 0.8})
    return scenes


VIDEOS.append({
    "name": "oracion-por-hijos",
    "bgm": True,
    "rate": "-8%",
    "gap_secs": 1.5,
    "voices": ["jorge"],
    "scenes": _oracion_hijos_yt(),
})


def download_ai_image(prompt, out_path, seed=None, style=None):
    try:
        import flux_img
        return flux_img.generate(prompt + (style or LIGHT_STYLE), out_path, aspect="16:9")
    except Exception as e:
        print(f"    IA falló: {e}", flush=True)
        raise RuntimeError(f"IA no generó imagen: {prompt[:40]}")


def find_local_img(imgs_dir, idx, name=None):
    import glob
    if name:
        for p in sorted(glob.glob(os.path.join(imgs_dir, f"{name}.*"))):
            if os.path.getsize(p) > 5000:
                return p
    for p in sorted(glob.glob(os.path.join(imgs_dir, f"e{idx:02d}.*"))):
        if os.path.getsize(p) > 5000:
            return p
    return None


def find_local_video(imgs_dir, idx):
    p = os.path.join(imgs_dir, f"e{idx:02d}.mp4")
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        return p
    return None


def rate_suffix(rate):
    if not rate or rate == "+0%":
        return ""
    return "_r" + rate.replace("%", "").replace("+", "p").replace("-", "m")


def build_scene(vid_dirs, scene, idx, vk, n_scenes, rate="+0%", gap_secs=None):
    slug = f"e{idx:02d}_{vk}"
    rsfx = rate_suffix(rate)
    img_name = scene.get("img")
    img_path = find_local_img(vid_dirs["imgs"], idx, img_name) or os.path.join(
        vid_dirs["imgs"], f"{img_name or 'e%02d' % idx}.jpg")
    bg_img = os.path.join(vid_dirs["tmp"], f"{slug}_bg.jpg")
    etag = m.tts_engine_tag(VOICES[vk]["voice"])

    # Resolver escena semántica → prompt técnico + emphasis tags
    scene = m.resolve_visual(scene)

    # Escena solo con static_text (título): generar silencio + imagen de fondo
    raw_text = scene.get("text", "")
    if not raw_text and scene.get("static_text"):
        bg_img_path = find_local_img(vid_dirs["imgs"], idx) or os.path.join(
            vid_dirs["imgs"], f"e{idx:02d}.jpg")
        if not (os.path.exists(bg_img_path) and os.path.getsize(bg_img_path) > 5000):
            download_ai_image(scene.get("ai", "Warm soft light abstract background, photorealistic"),
                              bg_img_path, seed=idx * 101, style=scene.get("style", LIGHT_STYLE))
        m.strip_img_metadata(bg_img_path)
        bg_processed = os.path.join(vid_dirs["tmp"], f"{slug}_bg.jpg")
        y.build_bg_bright(bg_img_path, bg_processed)
        static_dur = 5.0
        wav = os.path.join(vid_dirs["audio"], f"{slug}_silent.wav")
        if not os.path.exists(wav):
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                            f"anullsrc=r=24000:cl=mono", "-t", str(static_dur),
                            "-c:a", "aac", "-b:a", "128k", wav],
                           capture_output=True)
        timings = []
        mp4 = os.path.join(vid_dirs["out"], f"{slug}.mp4")
        static_lines = scene.get("static_text")
        static_size = scene.get("static_size")
        static_font = scene.get("static_font") or None
        trans = scene.get("trans")
        y.render_scene(timings, bg_processed, wav, mp4, final=(idx == n_scenes),
                       static_lines=static_lines, static_size=static_size,
                       font_path=static_font, trans=trans)
        return mp4

    # Parse HTML <strong>/<em> tags: TTS recibe texto limpio, render recibe emphasis_map
    if "<" in raw_text:
        tts_text, emphasis_map = m.parse_html_emphasis(raw_text)
    else:
        tts_text = raw_text
        emphasis_map = {}
    tts_clean = tts_text
    if m.has_pauses(tts_text):
        _, _chunks, tts_clean = m.split_pauses(tts_text)

    wav = os.path.join(vid_dirs["audio"],
                       f"{slug}{rsfx}{etag}_{zlib.crc32(tts_text.encode())}.wav")
    mp4 = os.path.join(vid_dirs["out"], f"{slug}.mp4")
    os.makedirs(vid_dirs["tmp"], exist_ok=True)

    video_path = find_local_video(vid_dirs["imgs"], idx)
    if video_path is None and scene.get("stock"):
        try:
            import pexels_stock
            if pexels_stock.available():
                q = scene.get("q") or scene.get("ai")
                dest = os.path.join(vid_dirs["imgs"], f"e{idx:02d}.mp4")
                # Descarga directa (forma anterior): sin buscar en el caché local.
                # Solo se guarda una copia del recurso descargado para la biblioteca.
                md = 3.0
                if os.path.exists(wav):
                    md = max(4.0, float(y.probe_duration(wav)) + y.PAD_BEFORE + 0.5)
                else:
                    md = sum(len(s.split()) for s in [scene.get("text", "")]) * 0.12
                    md = max(4.0, min(20.0, md))
                video_path = pexels_stock.fetch_for_scene_landscape(q, dest, min_duration=md)
                m.guardar_recurso(dest, q, "mp4")
        except Exception as e:
            print(f"    stock falló: {e}", flush=True)
            video_path = None

    if video_path is None and scene.get("ai_video"):
        try:
            import ai_video
            if ai_video.available():
                video_path = ai_video.fetch_for_scene(
                    scene.get("av") or scene["ai"],
                    os.path.join(vid_dirs["imgs"], f"e{idx:02d}_ai.mp4"),
                    aspect="16:9", model=scene.get("ai_model", "wan-fast"))
        except Exception as e:
            print(f"    ai_video falló: {e}", flush=True)
            video_path = None

    if video_path is None and not (os.path.exists(img_path) and os.path.getsize(img_path) > 5000):
        tema = scene.get("q") or scene.get("ai")
        # Descarga directa (forma anterior): sin buscar en el caché local.
        # Solo se guarda una copia del recurso descargado para la biblioteca.
        if scene.get("stock_photo"):
            import pexels_stock
            try:
                descargada = pexels_stock.fetch_photo_for_scene(
                    tema, img_path, orientation="landscape")
                if descargada and os.path.getsize(img_path) > 5000:
                    print(f"    foto Pexels descargada: {os.path.basename(descargada)}", flush=True)
                    m.guardar_recurso(img_path, tema, "jpg")
                else:
                    print("    foto Pexels falló, uso IA", flush=True)
                    try:
                        download_ai_image(scene["ai"], img_path, seed=idx * 101,
                                          style=scene.get("style", LIGHT_STYLE))
                    except Exception as e2:
                        print(f"    IA falló, uso Commons: {e2}", flush=True)
                        m.download_image(scene, img_path)
                    m.guardar_recurso(img_path, tema, "jpg")
            except Exception as e:
                print(f"    stock_photo falló: {e}, uso IA", flush=True)
                try:
                    download_ai_image(scene["ai"], img_path, seed=idx * 101,
                                      style=scene.get("style", LIGHT_STYLE))
                except Exception as e2:
                    print(f"    IA falló, uso Commons: {e2}", flush=True)
                    m.download_image(scene, img_path)
                m.guardar_recurso(img_path, tema, "jpg")
        else:
            try:
                download_ai_image(scene["ai"], img_path, seed=idx * 101,
                                  style=scene.get("style", LIGHT_STYLE))
            except Exception as e:
                print(f"    IA falló, uso Commons: {e}", flush=True)
                m.download_image(scene, img_path)
            m.guardar_recurso(img_path, tema, "jpg")
    if video_path is None:
        m.strip_img_metadata(img_path)
        if scene.get("light", True):
            y.build_bg_bright(img_path, bg_img)
        else:
            y.build_bg(img_path, bg_img)
        from PIL import Image, ImageFilter
        _bg = Image.open(bg_img).convert("RGB")
        _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        _bg.save(bg_img)

    voice = VOICES[vk]["voice"]
    deepen = VOICES[vk]["deepen"]
    if not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(tts_text, voice, wav,
                                  deepen=deepen, rate=rate))
    if scene.get("boom"):
        from hacer_videos_nuevos import mix_boom
        wav = mix_boom(wav)
    tj = os.path.join(vid_dirs["tmp"],
                      f"{slug}{rsfx}{etag}_{zlib.crc32(tts_text.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = m.align_words(tts_clean, wav)
        if timings is None:
            toks = tts_clean.split()
            dur = y.probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))

    n = n_scenes
    static_lines = scene.get("static_text") or None
    static_size = scene.get("static_size")
    static_sizes = scene.get("static_sizes")
    static_font = scene.get("static_font") or None
    trans = scene.get("trans")
    pad_after = None
    if gap_secs is not None and idx < n:
        pad_after = max(0.0, gap_secs - y.PAD_BEFORE)
    if video_path is not None:
        y.render_scene_video(timings, video_path, wav, mp4,
                             final=(idx == n), static_lines=static_lines,
                             static_size=static_size, static_sizes=static_sizes, font_path=static_font,
                             trans=trans, emphasis_map=emphasis_map,
                             pad_after=pad_after)
    else:
        y.render_scene(timings, bg_img, wav, mp4, final=(idx == n),
                       motion=scene.get("motion"), static_lines=static_lines,
                       static_size=static_size, static_sizes=static_sizes, font_path=static_font,
                       trans=trans, emphasis_map=emphasis_map,
                       pad_after=pad_after)
    return mp4


def build_video(vid):
    name = vid["name"]
    scenes = vid["scenes"]
    vd = {
        "imgs": os.path.join(ROOT, name, "imgs"),
        "audio": os.path.join(ROOT, name, "audio"),
        "out": os.path.join(ROOT, name, "out"),
        "tmp": os.path.join(ROOT, name, "tmp"),
    }
    for d in vd.values():
        os.makedirs(d, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)

    for vk in (vid.get("voices") or list(VOICES)):
        clips = []
        for idx, scene in enumerate(scenes, start=1):
            print(f"[{name}/{vk}] escena {idx}/{len(scenes)}", flush=True)
            clips.append(build_scene(vd, scene, idx, vk, len(scenes),
                                     rate=vid.get("rate", "+0%"),
                                     gap_secs=vid.get("gap_secs")))
        out = os.path.join(vd["out"], f"{name}_{vk}.mp4")
        y.concat(clips, out)
        if vid.get("bgm"):
            bgm = os.path.join(ROOT, "bgm", "ambient.wav")
            m.generate_bgm(bgm)
            mixed = out + ".bgm.mp4"
            m.mix_bgm(out, bgm, mixed)
            os.replace(mixed, out)
        dur = y.probe_duration(out)
        final = os.path.join(DEST, f"{name}_{vk}.mp4")
        os.replace(out, final)
        m.limpiar_metadata_video(final)
        ok = "MONETIZABLE (>=8min)" if dur >= 480 else "corto"
        print(f"OK {final}  {dur/60:.1f} min  [{ok}]", flush=True)


def listar_escenas(name):
    v = next(v for v in VIDEOS if v["name"] == name)
    for idx, sc in enumerate(v["scenes"], start=1):
        txt = sc.get("text") or sc.get("static_text", [""])[0] if sc.get("static_text") else ""
        src = "VIDEO" if sc.get("stock") else "FOTO" if sc.get("stock_photo") else "IA"
        print(f"e{idx:02d}.jpg  |  [{src}]  {txt[:70]}")
        if sc.get("ai"):
            print(f"   prompt: {sc['ai'][:60]}...")
    print(f"\nGuardar en: {os.path.join(ROOT, name, 'imgs')}/")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "escenas":
        for n in (args[1:] or [v["name"] for v in VIDEOS]):
            print(f"\n=== {n} ===")
            listar_escenas(n)
        sys.exit(0)
    names = args or [v["name"] for v in VIDEOS]
    for v in VIDEOS:
        if v["name"] in names:
            build_video(v)
