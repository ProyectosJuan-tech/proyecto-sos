#!/usr/bin/env python3
"""Dirección cinematográfica de imágenes para el canal (sistema de 2 pasos).

Sustituye el prompting "sujeto bonito + luz" por DIRECCIÓN DE ESCENA: cada imagen
debe contar un momento con una historia interna, no mostrar a una persona posando.

SISTEMA DE 2 PASOS (regla permanente):
  PASO 1 — Director: definir EMOTIONAL CORE, VISUAL EVENT, SYMBOL, BODY LANGUAGE,
           ENVIRONMENT, CAMERA, LIGHT, MESSAGE (ver SCENES).
  PASO 2 — Generador: convertir esa dirección en el prompt cinematográfico final
           (build_prompt), natural, largo, en inglés, estilo fotografía observacional.

REGLAS DE ORO:
  - No pedir emociones en la cara ("mujer triste"). Pedir ACCIONES que esa emoción
    produciría ("borra por tercera vez una tarea de una lista").
  - La persona NO mira a cámara salvo que el guion lo pida: perfil, 3/4, espalda,
    mirada hacia un objeto, manos haciendo algo, persona pequeña en el ambiente,
    planos abiertos, primeros planos de objetos, interacción con el entorno.
  - El cuadro debe entenderse en 2 segundos, sin audio: "qué está pasando" antes
    que "qué cara tiene".
  - Estilo: fotografía observacional íntima, no fotografía de moda ni retrato.
  - Prompts LARGOS y NATURALES (acción → contexto → emoción → composición →
    fotografía). Se admite negación natural en inglés ("no looking at camera") pero
    no bloques tipo "avoid:" de keywords.

JERARQUÍA DE SUJETOS (v2 2026-08-24) — preferencia al dirigir cada escena:
  OBJETO/ESPACIO/NATURALEZA > MANOS AISLADAS > PERSONA DISTANTE >
  PERFIL/ESPALDA > ROSTRO.
  Si la emoción puede comunicarse sin rostro, el director DEBE preferir una
  escena sin rostro (ver SUBJECT_HIERARCHY).

VISUAL RISK (v2) — estimar ANTES de generar para no pedir escenas imposibles:
  anatomical_risk    manos entrelazadas, abrazos, dedos, interacción compleja
                     cuerpo-objeto = HIGH; una sola mano simple o sin manos = LOW
  compositional_risk muchos elementos que ubicar o texto encima = HIGH;
                     1-3 objetos con espacio negativo claro = LOW
  fusion_risk        persona + plantas/mascotas/tejidos que FLUX puede fundir
                     entre sí = HIGH; persona separada del set u objeto solo = LOW
  Ejemplos canónicos:
    "mujer abrazando plantas con ambas manos"  → anatomical HIGH, fusion HIGH
    "mujer de espaldas regando UNA maceta"     → anatomical LOW,  fusion LOW
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Proveedor real usado por flux_img.generate para Pollinations: model=flux-realism
# (fotorrealista cinematográfico) con fallback flux. Mantener documentado para no
# asumir qué modelo está generando (el mismo prompt varía según el modelo).

DIRECTOR_BRAIN = """You are a cinematic visual director for long-form YouTube videos.
You write prompts for FLUX image generation models.

Do not generate generic portraits, fashion poses, model photos, character sheets, or people simply looking at the camera.

Every image must communicate a specific emotional situation and tell a small story without dialogue.

SASC FRAMEWORK (Subject → Action → Setting → Camera) — use this structure:
1. SUBJECT: What or who is in the image. Be specific about appearance, clothing, expression, pose.
2. ACTION: What is happening. Even for still images, describe implied motion or frozen moments.
3. SETTING: Where this takes place. Background details, lighting sources, time of day, environment.
4. CAMERA: Technical details. Lens focal length, aperture, film type, lighting setup, perspective.

FLUX does NOT support negative prompts. Use natural negation in English: "no faces visible" instead of "avoid faces".

LIGHTING has the highest single impact on output quality. Be specific:
- "soft window light from the left"
- "golden hour rim light"
- "single tungsten key light"
- "overcast diffused daylight"
- "warm bedside lamp mixed with cool blue from window"

CAMERA REFERENCES for photorealism (always include one):
- "shot on Sony A7IV, 85mm f/2.8" (portrait)
- "shot on Fujifilm X-T5, 56mm f/1.2" (intimate)
- "Canon 5D Mark IV, 24-70mm at 35mm" (documentary)
- "Hasselblad X2D, 80mm f/2.8" (editorial)
- "35mm film, Kodak Portra 400" (warm analog)
- "8mm film, grain" (vintage)

FILM STOCK references add authentic photorealistic look:
- "Kodak Portra 400" — warm natural tones
- "Fujifilm Pro 400H" — cooler, pastel
- "Ilford HP5" — black and white grain
- "Cinestill 800T" — tungsten, cinematic halation

FRAME composition — be specific about shot type:
- "extreme close-up of hands on a book" (detail)
- "medium shot from bed level" (intimate)
- "wide shot with person small in frame" (environmental)
- "low angle from floor level" (power/vulnerability)
- "overhead close-up" (contemplative)

Prefer cinematic storytelling over beauty.

Characters should feel like real people caught in an authentic moment, not models posing for a photograph.

Use natural body language, subtle facial expressions, believable environments, meaningful props, environmental storytelling, cinematic composition, realistic anatomy, natural skin texture, realistic hands, believable clothing, and physically plausible lighting.

Avoid: generic beautiful woman, looking at camera, studio portrait, fashion photography, perfect symmetrical face, plastic skin, anime face, doll-like appearance, empty background, generic sadness, generic happiness, posed body, sexualized posing, exaggerated facial expressions, overly smooth skin, blurred anatomy, distorted hands, floating objects, artificial bokeh, stock photography aesthetic.

The image must show an event, not just a person.

The emotional meaning should be understandable even if the viewer sees the image for only two seconds.

MOOD LAW (v2.1 2026-08-24): the photograph must feel luminous + natural + habitable + contemporary + hopeful. It must NOT feel dramatic + gray + melancholic + solemn + dark. "Cinematic" does NOT mean deep shadows, underexposure, greenish gray or sad indie mood. Prefer: abundant ambient light, shadows that keep detail, natural whites, visible color with clear tone separation, a sense of space, real materials, natural photographic texture, window light, lived-in interiors. Serene and deep is good; dark and gloomy is not.

SYMBOL PRIORITY: every scene has ONE meaningful symbol tied to the message — an empty armchair for letting go, a new sprout for growing back, an abandoned cup on a crowded desk for exhaustion. The symbol carries the story; place it where the eye lands first.

OBJECT TEST: before adding any object ask "does this object communicate something?". If no, leave it out. Never add objects just to fill space or inject decorative color.

COLOR: never default to beige + brown + olive + gray mush. Choose colors that serve THIS story's palette (blue, sky, red, terracotta, yellow, coral, pink, green, wood, cream, white are all allowed).

ANATOMY SIMPLIFICATION: prefer faceless scenes whenever the emotion allows it. If an interaction implies high anatomical risk, simplify it BEFORE generating ("woman embracing a plant with both hands" = HIGH risk -> "woman standing beside a tall plant, gently touching one leaf" = LOW risk). Visual integrity matters more than showing a person.

OUTPUT FORMAT: Every prompt must end with a camera/film reference like "shot on [camera], [lens], [film stock]" to anchor photorealism."""

# Guías v2.1 de dirección (consumidas por sesiones IA y por humanos)

SYMBOL_FIRST_EXAMPLES = {
    "soltar": "espacio liberado, objeto dejado atrás, puerta abierta, sillón vacío",
    "volver a crecer": "planta nueva, brote, cuidado con las manos, luz sobre hojas",
    "agotamiento": "acumulación de tareas, cuerpo descansando por fin, taza olvidada en escritorio cargado",
    "empezar de nuevo": "transición, umbral entreabiertos, movimiento hacia la luz, primer rayo sobre una mesa despejada",
}

# LEY DE METÁFORA (no plantilla): el concepto elige el símbolo por FAMILIA de
# metáfora (ver metaphor_families en assets/brand/brand.config.json), nunca
# "para X usar objeto Y". La AUSENCIA también es un mensaje: cuando el concepto
# habla de soltar/perder, el espacio vacío dice "ahora hay lugar" mejor que una
# persona expresando tristeza. No introducir persona automática.
METAPHOR_LAW = (
    "Cuando el concepto habla de soltar → buscar símbolo de espacio, ausencia, "
    "liberación o apertura. Crecer → crecimiento visual. Agotamiento → "
    "acumulación o falta de espacio. Empezar de nuevo → apertura, transición o "
    "movimiento. Aprender metáforas, no plantillas: la ausencia del sujeto puede "
    "SER el mensaje."
)

OBJECT_NARRATIVE_RULE = (
    "Cada objeto debe contar la historia. Antes de agregar uno preguntar: "
    "'¿este objeto comunica algo?'. Si la respuesta es no, NO agregarlo "
    "(ni para llenar espacio ni para meter color decorativo)."
)

COLOR_GUIDE = (
    "No caer en beige+marrón+verde oliva+gris por defecto. La paleta sirve a la "
    "historia de la escena. Permitidos: azul, celeste, rojo, terracota, amarillo, "
    "coral, rosa, verde, madera, crema, blanco. La fotografía mantiene SUS "
    "propios colores naturales: nunca desaturar ni teñir para que combine con "
    "la tipografía — la identidad gráfica se superpone encima."
)

ANATOMY_SIMPLIFY_EXAMPLE = (
    "HIGH RISK: 'mujer abrazando una planta con ambas manos' → "
    "LOW/MEDIUM RISK: 'woman standing beside a tall plant, gently touching one leaf'."
)

# Emoción -> ACCIÓN (nunca emoción -> cara). Las emociones se ven en las acciones.
EMOTION_TO_ACTION = {
    "frustracion": "borra por tercera vez una tarea de una lista",
    "cansancio": "se queda sentada en el borde de la cama antes de levantarse",
    "ansiedad": "mira cinco cosas pendientes sobre una mesa",
    "esperanza": "abre las cortinas después de una noche difícil",
    "decision": "deja el celular lejos y abre el libro",
    "culpa": "mira una tarea que volvió a postergar",
    "progreso": "marca una pequeña casilla en un calendario",
    "resistencia": "tiene las zapatillas puestas pero todavía no salió",
    "alivio": "termina una pequeña tarea y se queda quieta unos segundos",
}

# Jerarquía de sujetos (v2 2026-08-24): elegir el nivel MÁS ALTO posible al
# dirigir. El rostro es el último recurso: si la emoción se comunica sin cara,
# la escena va sin cara. Orden = de más fácil de generar bien a más difícil.
SUBJECT_HIERARCHY = [
    "OBJETO",           # zapatilla, taza, libro, calendario, puerta (cuentan solos)
    "ESPACIO",          # habitación vacía, cama revuelta, mesa con dos opciones
    "NATURALEZA",       # planta, flores, ventana con luz
    "MANOS",            # manos aisladas haciendo una acción simple
    "PERSONA_DISTANTE", # persona pequeña en el ambiente, plano general
    "PERFIL_ESPALDA",   # perfil 3/4 o de espaldas
    "ROSTRO",           # solo si el guion lo exige explícitamente
]

# Protagonista recurrente (mujer ~30, real, no modelo). El descriptor debe repetirse
# IGUAL en todos los prompts para que Pollinations con seed fijo mantenga el rostro.
# En el sistema objeto-primero 2026-08-15 la mayoría de escenas NO muestran la cara:
# N7 y N8 la muestran de ESPALDAS, por lo que la consistencia deja de ser un problema.
PROTAGONIST = ("A woman around 30 with dark brown shoulder-length hair, "
               "a natural ordinary face, realistic everyday appearance, "
               "simple comfortable clothing, not a model")

# ---------------------------------------------------------------------------
# SCENES — PASO 1 (Dirección) + PASO 2 (Prompt final, prompt["final"]).
#
# SISTEMA 2026-08-15 (decisión del usuario): REDUCIR a 8 imágenes OBJETO-PRIMERO.
# El problema no era "la IA dibuja feo": era que pedíamos retratos. Ahora cada
# imagen la cuentan los OBJETOS (zapatilla, libro, calendario, taza, puerta) y
# NO un rostro. Sólo N7 y N8 tienen persona, vista de ESPALDAS: la consistencia
# de protagonista deja de ser un problema (sin cara que mantener).
#
# Arco visual (38 bloques → 8 imágenes):
#   N1  la promesa de noche          (noche, oscuro)
#   N2  la mañana que no arranca     (mañana, gris)
#   N3  el entorno que manda         (obstáculos: galletita, mesa)
#   N4  la señal                     (taza + libro: el ancla)
#   N5  la preparación               (ropa lista junto a la puerta)
#   N6  el registro                  (mano marcando el calendario)
#   N7  el volver                    (atarse la zapatilla, de espaldas)
#   N8  la salida al amanecer        (de espaldas, luz dorada)
# ---------------------------------------------------------------------------
SCENES = {
    "N1": {
        "serves": "S01 Te lo prometés de noche / S02 Y mañana llega / S34 pregunta del principio / S37 mandale este video",
        "emotional_core": "frustración callada y duda tras repetidas promesas rotas",
        "visual_event": "al borde de la cama de noche, los pies descalzos tocando el piso, las zapatillas y el libro sin abrir a los pies",
        "symbol": "zapatillas + libro sin abrir + celular con alarma brillando en la mesita",
        "body_language": "solo piernas y pies descalzos en el borde, sin rostro: el cuerpo entero dice la promesa incumplida",
        "environment": "dormitorio modesto y vivido, lámpara cálida + azul de ventana",
        "camera": "plano cerrado a la altura del piso, las zapatillas en primer plano",
        "light": "luz cálida de lámpara mezclada con azul frío de la noche",
        "message": "prometí de nuevo y volví a fallar (los objetos lo dicen, no la cara)",
        "final": (
            "A warm inviting bedroom at night, softly lit and cozy, seen from low "
            "down at floor level. The bare feet of a woman hang over the edge of the "
            "bed, the only part of the body visible. On the floor directly below, a "
            "pair of running shoes and an unopened book lie untouched, as if prepared "
            "days ago and never used. On the bedside table, a phone screen glows "
            "gently with a silent alarm. A warm bedside lamp fills the room with a "
            "bright soft orange glow, mixed with a hint of cool blue from the window: "
            "intimate, calm and cozy, a quiet moment of reflection, absolutely not "
            "scary or threatening. Cinematic psychological drama, intimate "
            "observational photography, strong environmental storytelling, realistic "
            "textures, soft warm shadows, warm golden palette, 35mm film look, low "
            "angle close shot, the objects in sharp focus carrying the story. No "
            "faces visible, no people looking at camera. Photorealistic, emotionally "
            "subtle, sophisticated cinematic still."
        ),
    },
    "N2": {
        "serves": "S05 la motivación sube y baja / S08 a pura voluntad / S30 vas a fallar",
        "emotional_core": "la mañana gris que otra vez no arranca, agotamiento resignado",
        "visual_event": "cama revuelta y vacía a la mañana, el celular con la alarma silenciada sobre la almohada, ropa de ayer en el suelo",
        "symbol": "celular con alarma silenciada + cama sin hacer + libro y zapatillas intactos junto a la puerta",
        "body_language": "sin persona: la cama vacía cuenta la historia de la mañana que no arrancó",
        "environment": "dormitorio a la mañana, luz gris pálida, todo en sombra suave",
        "camera": "plano medio sobre la cama, la puerta con los objetos intactos de fondo",
        "light": "luz de mañana gris y suave",
        "message": "otra vez no pude levantarme (sin necesidad de ver a nadie)",
        "final": (
            "An unmade empty bed in a bedroom early in the morning, the covers pushed "
            "aside as if the person left in a hurry or never truly got up. On the "
            "pillow, a phone with a dismissed alarm on its screen, the only glowing "
            "element. Pale grey morning light filters through the window; the room is "
            "softly shadowed. In the background near the door, a book and a pair of "
            "running shoes sit untouched, evidence of the plan that did not happen. "
            "Yesterday's clothes lie on the floor. Cinematic psychological drama, "
            "intimate observational photography, strong environmental storytelling, "
            "realistic textures, believable shadows, restrained grey palette, 35mm "
            "film look, medium shot over the bed, no people visible. The empty bed "
            "tells the story. Photorealistic, emotionally subtle, sophisticated "
            "cinematic still."
        ),
    },
    "N3": {
        "serves": "S06 te sobran obstáculos / S15 quién gana / S17 la galletita abierta / S19 diseñá tu entorno",
        "emotional_core": "el entorno le gana a la voluntad cansada: lo que está a la vista manda",
        "visual_event": "mesa de cocina con un paquete de galletitas abierto en primer plano y el frutero a la vista, la taza de café a medio tomar",
        "symbol": "paquete de galletitas abierto + frutero + taza",
        "body_language": "sin persona, o solo una mano detenida entre las dos opciones",
        "environment": "cocina real vivida, luz cálida de día",
        "camera": "plano cenital suave o frontal bajo sobre la mesa, los objetos componen el conflicto",
        "light": "luz cálida natural de ventana",
        "message": "no pongas tu voluntad contra una galletita a la vista",
        "final": (
            "A bright airy kitchen table on a warm morning, the composition built "
            "around a quiet conflict between two options: an open package of cookies "
            "in the foreground, a bowl of fresh fruit at the edge of the frame, and a "
            "half-finished cup of coffee between them. The scene is ordinary and "
            "lived-in, slightly messy in a realistic way. A hand rests near the "
            "cookie package, paused, undecided, but no face is visible. Bright warm "
            "sunlight pours in through a large window, the kitchen well lit and "
            "welcoming, white and light wood tones, cheerful and airy. Intimate "
            "observational photography, strong environmental storytelling, shallow "
            "depth of field with the cookie package sharp in the foreground, 35mm "
            "film look, bright warm color palette, photorealistic. The frame "
            "communicates the choice without words and without a person posing."
        ),
    },
    "N4": {
        "serves": "S07 repetición / S13 señal / S16-S23-S27 anclaje / S26 ejemplo real",
        "emotional_core": "automaticidad serena: el hábito enganchado a una señal que ya existe",
        "visual_event": "taza de café y libro abierto lado a lado sobre la mesa, una mano llegando al libro de forma automática",
        "symbol": "taza + libro abierto junto a ella",
        "body_language": "solo la mano llegando al libro, gesto automático y distraído",
        "environment": "mesa de cocina a la mañana, luz cálida",
        "camera": "plano medio-cercano sobre manos/objetos, sin mirada a cámara, sin rostro",
        "light": "luz cálida de mañana cruzando la mesa",
        "message": "el hábito se cuelga de un momento que ya existe",
        "final": (
            "Close cinematic photograph of a kitchen table in the morning: a plain "
            "coffee cup and an open book placed side by side, a woman's hand already "
            "reaching for the book, the movement automatic, before conscious thought. "
            "The hand and the objects tell the story; the woman's face is not visible, "
            "only her arm entering the frame. Soft warm morning light falls across the "
            "table, the scene ordinary and lived-in. Intimate observational "
            "photography, natural human gesture, realistic hands and anatomy, warm "
            "directional light, shallow believable depth of field, 35mm film look, "
            "close-medium shot, strong environmental storytelling, photorealistic, "
            "emotionally subtle. No faces, no eye contact with camera, no posed "
            "motivation; a routine that has become automatic."
        ),
    },
    "N5": {
        "serves": "S18 dejá la ropa preparada / S24 reducí la fricción / S25 la decisión ya la tomaste anoche",
        "emotional_core": "tranquilidad práctica: media decisión ya tomada, la fricción eliminada de antemano",
        "visual_event": "ropa y zapatillas ordenadas junto a la puerta de entrada, luz de mañana cayendo sobre ellas",
        "symbol": "ropa doblada + zapatillas listas junto a la puerta",
        "body_language": "sin persona: los objetos ordenados son la prueba de la decisión",
        "environment": "entrada de departamento pequeño, luz cálida de mañana",
        "camera": "plano bajo desde el suelo hacia la puerta, los objetos en primer plano",
        "light": "luz de mañana cálida entrando por la puerta",
        "message": "la decisión ya la tomaste anoche",
        "final": (
            "The entrance of a small apartment in the morning, seen from low down. "
            "A pair of running shoes and neatly folded workout clothes are laid out "
            "ready by the front door, waiting to be used. Warm morning light enters "
            "from the doorway and falls across the clothes; a key hangs on a hook on "
            "the wall, a doormat in the foreground. No people visible; the arranged "
            "objects are the proof of a decision already made the night before. "
            "Intimate observational photography, strong environmental storytelling, "
            "realistic textures, believable shadows, warm directional morning light, "
            "shallow depth of field, 35mm film look, low angle close shot, "
            "photorealistic, emotionally calm and understated."
        ),
    },
    "N6": {
        "serves": "S14 señal-rutina-recompensa / S28 marco el día / S31-S33 cuánto tardás en volver",
        "emotional_core": "constancia callada, sin orgullo; la racha rota también cuenta",
        "visual_event": "primer plano de la mano marcando un día en el calendario de pared, varios días marcados y UNO sin marcar en el medio",
        "symbol": "calendario de pared con cruces y un día vacío",
        "body_language": "mano con lapicera marcando, gesto tranquilo y ordinario",
        "environment": "calendario en pared lisa, luz cálida natural",
        "camera": "extreme close-up sobre mano + calendario, el fondo desenfocado",
        "light": "luz natural cálida desde una ventana",
        "message": "la constancia importa más que la racha perfecta",
        "final": (
            "Extreme close-up of a woman's hand marking a day on a wall calendar with "
            "a pen, drawing a small cross on today's square. Several previous days are "
            "already marked, with one single unmarked day in between the crosses, a "
            "small honest gap. The hand is calm and ordinary, realistic skin texture, "
            "a simple metal pen. Warm natural light from a window, the calendar pinned "
            "on a plain wall, the background softly blurred and out of focus. Cinematic "
            "intimate still, shallow depth of field, realistic anatomy, natural "
            "gesture, warm directional light, restrained palette, 35mm film look, "
            "photorealistic, emotionally subtle. No face visible; the objects carry "
            "the story, a chain of completed days with one honest gap."
        ),
    },
    "N7": {
        "serves": "S12 dos minutos alcanzan / S25 volvé rápido si fallás / S32 volver al otro día",
        "emotional_core": "calma de reanudar, sin drama; empezar pequeño o volver es el hábito",
        "visual_event": "vista de espaldas, sentada al borde de la cama inclinándose para atarse UNA zapatilla, la otra al lado",
        "symbol": "una zapatilla atándose + la segunda a su lado",
        "body_language": "de espaldas a cámara, inclinada atando, gesto deliberado y tranquilo",
        "environment": "dormitorio a la mañana, luz suave",
        "camera": "plano medio-cercano desde atrás, la espalda y las manos en foco",
        "light": "luz suave de mañana",
        "message": "el error no es caer, es quedarse en el piso; volver es el hábito",
        "final": (
            "A simple, realistic photo of a woman seen completely from behind, sitting "
            "on the edge of her bed in the morning, calmly tying one running shoe on "
            "her right foot. Only her back and shoulders are visible; her face is "
            "turned away and not in frame. She bends forward slightly, both hands "
            "working on the shoelace in a normal, relaxed position. On the floor "
            "beside her foot, a second running shoe rests. She wears plain "
            "comfortable clothes, a simple t-shirt and leggings. Soft morning light "
            "from a window on the side, a modest lived-in bedroom. Normal realistic "
            "human body proportions, natural healthy anatomy, correct number of "
            "fingers, no deformities, a plain everyday scene. Intimate observational "
            "photography, shallow depth of field, 35mm film look, close-medium shot "
            "from behind, photorealistic, calm and understated."
        ),
    },
    "N8": {
        "serves": "S35 diseñalo para el día difícil / S36 CTA / S38 suscribite",
        "emotional_core": "calma y continuidad, sin celebración; el día difícil se empieza igual",
        "visual_event": "saliendo del departamento al amanecer, vista de espaldas, figura pequeña contra la calle",
        "symbol": "puerta abierta + figura de espaldas + calle vacía al amanecer",
        "body_language": "camina hacia adelante, figura pequeña en la calle, de espaldas, sin mirar a cámara",
        "environment": "calle tranquila al amanecer, luz dorada pálida",
        "camera": "plano medio-abierto desde atrás, sujeto fuera de centro",
        "light": "luz dorada de amanecer, sombras largas y suaves",
        "message": "hacé más fácil una cosa y repetila",
        "final": (
            "A woman seen from behind, small in the frame, walking away from her "
            "apartment door at dawn, closing it calmly behind her, dressed in simple "
            "walking clothes and running shoes. She steps forward into pale golden "
            "morning light, her figure small against the quiet street and soft sky. No "
            "celebration, no smile for anyone; she is simply beginning an ordinary "
            "day, even a difficult one. Warm dawn light on the buildings, long soft "
            "shadows, an empty neighborhood street. Cinematic visual storytelling, "
            "documentary-style photography, natural posture, realistic textures, "
            "believable human proportions, warm directional dawn light, restrained "
            "palette, 35mm film look, medium-wide shot from behind, subject off-center, "
            "strong environmental storytelling, photorealistic, emotionally "
            "restrained. She does not look at the camera; the frame communicates calm "
            "continuity."
        ),
    },
}


def build_prompt(name):
    """PASO 2 — devuelve el prompt cinematográfico final para la escena `name`."""
    return SCENES[name]["final"]


# Campos opcionales del BRIEF estructurado (v2). Si una escena los define,
# direct() los expone; compose_prompt() los usa para armar el prompt inglés.
BRIEF_OPTIONAL_KEYS = (
    "subject_priority",   # nivel de SUBJECT_HIERARCHY elegido
    "action",             # la acción que cuenta la emoción (inglés natural)
    "setting",            # dónde (puede convivir con environment)
    "color",              # paleta: verde + crema + terracota, acentos rojos, etc.
    "composition",        # encuadre + espacio negativo ("clean left third for text")
    "text_space",         # zona reservada para texto de miniatura, si aplica
    "style",              # anclas fotográficas por PROPIEDADES, no fotógrafos
    "risks",              # dict: anatomical/compositional/fusion = LOW|MEDIUM|HIGH (+reason)
)


# ---------------------------------------------------------------------------
# BRAND CONFIG + STYLE_SELECTION (identidad del canal como DATOS)
# ---------------------------------------------------------------------------

_BRAND_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "assets", "brand", "brand.config.json")


def _load_brand_config():
    try:
        with open(_BRAND_CONFIG_PATH) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 — sin config el sistema sigue igual
        return {}


BRAND_CONFIG = _load_brand_config()


def style_family(key):
    """Descripción de la familia de composición elegida ('A_editorial_izquierdo', ...)."""
    fams = BRAND_CONFIG.get("style_families", {})
    if not key:
        return ""
    if key not in fams:
        raise ValueError(f"style_family desconocida: {key}. "
                         f"Opciones: {', '.join(fams)}")
    return fams[key]


def pre_design_report(d):
    """Bloque obligatorio ANTES de generar: estilo, por qué y señales de identidad."""
    fams = BRAND_CONFIG.get("style_families", {})
    lines = ["STYLE SELECTED: " + (d.get("style_family", "(sin familia)")
                                  if not d.get("style_family") else
                                  f"{d['style_family']} — {fams.get(d['style_family'], '?')}"),
             f"WHY: {d.get('emotional_core', '?')}",
             "IDENTITY SIGNALS: " + "; ".join(BRAND_CONFIG.get("identity_signals", []))]
    return "\n".join(lines)


def direct(name, include_brain=False):
    """Devuelve la dirección estructurada (PASO 1) + prompt final (PASO 2)."""
    s = dict(SCENES[name])
    out = {
        "emotional_core": s["emotional_core"],
        "visual_event": s["visual_event"],
        "symbol": s["symbol"],
        "body_language": s["body_language"],
        "environment": s["environment"],
        "camera": s["camera"],
        "light": s["light"],
        "message": s["message"],
        "prompt": s["final"],
    }
    for k in BRIEF_OPTIONAL_KEYS:
        if k in s:
            out[k] = s[k]
    if include_brain:
        out["director_brain"] = DIRECTOR_BRAIN
    return out


# Anclas de estilo del canal POR PROPIEDADES visuales (no nombres de fotógrafos:
# la identidad debe ser propia, describible y estable entre modelos).
# v2.1 anti-moody: luminosa, habitable, esperanzadora — NUNCA gris solemne.
CHANNEL_STYLE_ANCHORS = (
    "intimate observational photography, editorial lifestyle feel, "
    "natural skin tones, realistic textures, shadows that keep detail, "
    "bright airy daylight, generous ambient window light, natural whites, "
    "visible color separation, moderate depth of field, documentary framing, "
    "lived-in contemporary interior, hopeful serene mood"
)

_NEGATIONS_BY_RISK = {
    "anatomical_risk": {
        "HIGH": ("hands are not intertwined and fingers are clearly separated",
                 "the subject interacts with the object using one simple grip"),
        "MEDIUM": ("hands are relaxed and clearly defined"),
    },
    "fusion_risk": {
        "HIGH": ("each element stays visually separate from the others"),
        "MEDIUM": ("the person and the plants do not blend together"),
    },
}


def compose_prompt(d):
    """Compone el prompt cinematográfico inglés desde un BRIEF estructurado.

    El brief es un dict con claves en INGLÉS natural (frases listas, no keywords):
      emotional_core, visual_event, symbol, action, setting, light, color,
      composition, camera, [subject_priority], [text_space], [style], [risks],
      [style_family] (clave de style_families en assets/brand/brand.config.json).

    Cadena de armado: setting+evento → símbolos/props → luz → color →
    composición/text_space → anclas de estilo por propiedades → cámara/film →
    negaciones naturales derivadas de risks. NO toca los "final" validados.
    """
    # v2.1: symbol es OBLIGATORIO (la escena se cuenta desde el símbolo).
    req = ("emotional_core", "visual_event", "symbol", "setting", "light", "camera")
    missing = [k for k in req if not d.get(k)]
    if missing:
        raise ValueError(f"brief incompleto, faltan: {missing}")

    parts = []

    # 1) Escena base: setting + evento visual como una sola frase narrativa.
    parts.append(f"{d['setting'].rstrip('.')}. {_cap(d['visual_event'])}")

    # 2) SÍMBOLO (prioridad alta): va inmediatamente después del evento para
    #    que pese en el front-loading del encoder.
    parts.append(f"The story is carried by {_lc(d['symbol'])}")

    # 3) Acción explícita si aporta algo distinto del evento.
    act = d.get("action")
    if act and act.lower().strip(". ") not in d["visual_event"].lower():
        parts.append(_cap(act))

    # 4) Luz (factor de mayor impacto): cómo interactúa, no solo su nombre.
    parts.append(_cap(d["light"]))

    # 5) Color con propósito emocional.
    if d.get("color"):
        parts.append(f"Palette: {_lc(d['color'])}")

    # 6) Composición + espacio reservado para texto (miniaturas).
    comp = d.get("composition") or ""
    ts = d.get("text_space") or ""
    if comp or ts:
        c = f"{comp}; {ts}" if comp and ts else (comp or ts)
        parts.append(f"Composition: {_lc(c)}")

    # 6b) STYLE_SELECTION: familia de composición del canal (brand.config.json).
    fam = style_family(d.get("style_family", ""))
    if fam:
        parts.append(_cap(fam))

    # 7) Anclas de estilo del canal (propiedades) + estilo extra del brief.
    style_extra = d.get("style") or ""
    anchors = f"{CHANNEL_STYLE_ANCHORS}, {style_extra}" if style_extra else CHANNEL_STYLE_ANCHORS
    parts.append(anchors[0].upper() + anchors[1:])

    # 8) Cámara / film stock que ancla el fotorrealismo.
    cam = d["camera"].strip()
    if not cam.lower().startswith("shot on"):
        cam = f"Shot on {cam}"
    parts.append(_cap(cam))

    # 9) Negación natural según riesgos declarados (FLUX no soporta negativos).
    risks = d.get("risks") or {}
    for key, variants in _NEGATIONS_BY_RISK.items():
        level = str(risks.get(key, "")).upper()
        if level in variants:
            vlist = variants[level]
            if isinstance(vlist, str):
                vlist = (vlist,)
            parts.extend(vlist)

    # 10) Cierre estándar del canal. (emotional_core NO se incrusta: es
    #     metadata de dirección/QA; en el prompt la emoción ya está contada
    #     por el evento, la luz y la acción.)
    parts.append("Photorealistic, emotionally subtle, sophisticated cinematic still.")

    return ". ".join(_cap(p).rstrip(".") for p in parts) + "."


def _cap(s):
    s = s.strip()
    return s[0].upper() + s[1:] if s else s


def _lc(s):
    s = s.strip().rstrip(".")
    return s[0].lower() + s[1:] if s else s


def _looks_like_camera_anchor(text):
    t = text.lower()
    return any(w in t for w in ("shot on", "mm", "film", "f/", "camera"))


if __name__ == "__main__":
    import json
    args = sys.argv[1:]
    if args and args[0] == "--estilos":
        for k, v in BRAND_CONFIG.get("style_families", {}).items():
            print(f"{k}: {v}")
        sys.exit(0)
    if args and args[0] == "--brief":
        # python3 director_visual.py --brief brief.json  → prompt compuesto + risks
        d = json.load(open(args[1]))
        out = {"risks": d.get("risks", {}),
               "subject_priority": d.get("subject_priority", ""),
               "final": compose_prompt(d)}
        if d.get("style_family"):
            out["pre_design"] = pre_design_report(d)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0)
    args = args or list(SCENES)
    for name in args:
        if name not in SCENES:
            print(f"{name}: no existe", flush=True)
            continue
        print(f"=== {name} ===")
        print(json.dumps(direct(name, include_brain=True), ensure_ascii=False, indent=2))
        print(flush=True)
