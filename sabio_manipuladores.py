#!/usr/bin/env python3
"""Escenas del largo "Las 10 frases del sabio para callar a los manipuladores".

Formato listicle probado (el "10 Frases Estoicas para Callar a los Manipuladores"
hizo 1M views). Personaje El Sabio (sabio.py) SOLO en intro y CTA como identidad
de marca; las 21 escenas restantes son VISUALES NARRATIVOS que ilustran el
contenido: la protagonista (mujer ~45, castaña, jersey crema) + el manipulador
(hombre ~50s). Alineado a fe católica y método anti-gurú: sin culpa, sin
diagnóstico, sin proselitismo abierto.

Estructura (23 escenas):
  intro (gancho ≤15s) + 10 bloques × 2 escenas (frase de impacto + desarrollo/método)
  + re-hook dentro del bloque 4 + bonus "una cosa más" + CTA.

Cada escena: text (1-2 oraciones), ai (prompt IA del visual narrativo), q
(fallback Commons), motion (zoom-in/out, pan-r/l alternados), opcional
ai_video: true + ai_model (clips Pollinations wan-fast; audio del clip se
descarta en el render, encima va la voz).
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys_path = os.path.join(ROOT)
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
import sabio

# --- Personajes narrativos fijos (consistencia entre escenas) ---
PROTAGONISTA = (
    "A Latina woman in her mid-forties with shoulder-length brown hair, warm "
    "brown eyes, soft gentle face, wearing a cream knit sweater, dignified and "
    "serene presence"
)

MANIPULADOR = (
    "A man in his early fifties with narrowed calculating eyes, tight jaw, "
    "leaning forward with a pointing hand, cold composed expression, wearing a "
    "dark grey shirt"
)

# Estilo visual: cálido y claro (bienestar) — oscuro SOLO para momentos de tensión.
WARM = (
    "bright airy high-key soft diffused window light, warm cream and sage palette, "
    "gentle highlights, no hard shadows, photorealistic, high detail"
)
TENSE = (
    "moody cinematic light, cool shadows with a single warm lamp accent, "
    "photorealistic, high detail"
)

MOTIONS = [
    "zoom-in", "pan-right", "zoom-out", "pan-left", "zoom-in", "pan-right",
    "zoom-out", "pan-left", "zoom-in", "pan-right", "zoom-out", "pan-left",
    "zoom-in", "pan-right", "zoom-out", "pan-left", "zoom-in", "pan-right",
    "zoom-out", "pan-left", "zoom-in", "pan-right", "zoom-out",
]


def _scene(text, ai, q, idx, light=True, ai_video=False, ai_model=None, av=None):
    s = {
        "text": text,
        "ai": ai,
        "q": q,
        "motion": MOTIONS[idx % len(MOTIONS)],
        "light": light,
    }
    if ai_video:
        s["ai_video"] = True
        if ai_model:
            s["ai_model"] = ai_model
        if av:
            s["av"] = av
    return s


def scenes(cta_text):
    S = []
    # Intro: gancho ≤15s — SABIO (marca)
    S.append(_scene(
        "Hay personas que viven de tu reacción. Si les das un grito, te ganan. "
        "Si les das calma, te pierden. Hoy te dejo las diez frases del sabio "
        "para desarmar a quien te quiere manejar. Quedate hasta el final: la última frase es la que más duele. Pero primero, una advertencia honesta: esto no es magia, es práctica.",
        sabio.scene_prompt("tea_window"),
        "elderly man warm morning light window", 0))

    # 1
    S.append(_scene(
        "El que te manipula no teme tus gritos: teme tu silencio.",
        f"{MANIPULADOR} sitting back satisfied in an armchair, smirking while "
        f"glancing sideways at a {PROTAGONISTA} who looks down quietly with a "
        f"steady calm expression, two-person frame, tension in the air, "
        f"{TENSE}",
        "man in armchair glancing at woman", 1, light=False, ai_video=True,
        ai_model="wan-fast", av=(f"Slow zoom toward {MANIPULADOR} smirking in an "
        f"armchair, he glances sideways at {PROTAGONISTA} who looks down calmly, "
        f"the tension of silence, moody cinematic light, 16:9, photorealistic")))
    S.append(_scene(
        "Pensalo un momento. El manipulador se alimenta de tu reacción: si se enoja "
        "espera que te enojes, si te acusa espera que te defiendas. Cuando callás con "
        "calma, le sacás el alimento. No es quedarte en blanco: es elegir no darle de "
        "comer a la pelea. Tu silencio sereno le dice lo que mil gritos no logran: "
        "yo no juego tu juego. Y el que no grita gana más despacio, pero gana para siempre.",
        f"{PROTAGONISTA} sitting still and serene on a wooden chair, hands folded "
        f"in her lap, while {MANIPULADOR} waits in the dark background watching "
        f"her, calm vs frustration contrast, {WARM}",
        "calm woman on wooden chair", 2))

    # 2
    S.append(_scene(
        "No entres al juego. El manipulador necesita un rival; sin rival, su obra "
        "se cae sola.",
        f"{PROTAGONISTA} standing by a window holding a smooth grey stone in her "
        f"open palm, looking at it with quiet resolution, deciding to be that "
        f"stone, soft window light, {WARM}",
        "woman holding grey stone palm", 3, ai_video=True, ai_model="wan-fast",
        av=(f"Slow push-in on {PROTAGONISTA} turning the smooth grey stone over "
        f"in her palm by a window, her expression turning to quiet resolution, "
        f"soft window light, 16:9, photorealistic")))
    S.append(_scene(
        "Si te invitan a discutir, no estás obligado a asistir. Una discusión necesita "
        "dos, pero una decisión alcanza con uno. Cuando no respondés, el otro se queda "
        "hablando solo con su propia rabia, y la rabia sin eco se apaga. No es orgullo: "
        "es saber que hay conversaciones que no llevan a nada. Vos elegís dónde gastar "
        "tu energía, y la energía es tu tesoro. Elegir bien tus peleas es la mitad del método. Y no te pongas a explicar tu silencio: el silencio se explica solo.",
        f"{MANIPULADOR} arguing alone to an empty chair, gesturing with raised "
        f"hands, while {PROTAGONISTA} walks away calmly in the background, "
        f"his anger without echo, {WARM}",
        "man arguing to empty chair", 4))

    # 3
    S.append(_scene(
        "Decir no con amor es un sí a vos. Un no sereno vale más que mil "
        "explicaciones.",
        f"{PROTAGONISTA} in her living room wrapping a blanket around her "
        f"shoulders, holding a warm cup of tea, soft golden evening light, "
        f"giving herself a peaceful moment, self-respect beginning, {WARM}",
        "woman wrapping blanket cup of tea", 5, ai_video=True,
        ai_model="wan-fast",
        av=(f"{PROTAGONISTA} slowly wrapping a knit blanket around her shoulders "
        f"in her living room, lifting a warm cup of tea, golden evening light, "
        f"gentle zoom-in, self-respect beginning, 16:9, photorealistic")))
    S.append(_scene(
        "Muchos no decimos que no porque queremos quedar bien, y ese miedo nos "
        "esclaviza. Pero explicar tu no es darle armas al que quiere convencerte: cada "
        "excusa es una puerta que le dejás abierta. Un no claro, dicho con calma y con "
        "cariño, se respeta. No hace falta justificarse con quien no quiere entender. "
        "Tu sí más valioso empieza con un no bien dicho. Y recordá que tu sí es tuyo, no un favor que te deben.",
        f"{PROTAGONISTA} looking calmly at {MANIPULADOR} with a gentle but firm "
        f"face, her open palm raised in a soft stop gesture, he pauses "
        f"mid-sentence, warm respectful tension, {WARM}",
        "woman gentle stop gesture", 6))

    # 4 (re-hook al ~35%)
    S.append(_scene(
        "Pero acá está lo más serio: el que te quiere manejar te hace dudar de lo "
        "que sentís.",
        f"{MANIPULADOR} pointing a finger at {PROTAGONISTA} who stands confused "
        f"in front of a mirror, her reflection hesitant, gaslighting atmosphere, "
        f"{TENSE}",
        "man pointing at woman mirror", 7, light=False))
    S.append(_scene(
        "Te dice que exagerás, que estás loco, que siempre sos igual, que te lo "
        "inventás. Esa es la manipulación más fina: te mueve el piso de tu propia "
        "verdad. No le creas. Tu verdad no necesita su permiso para existir. Esa es "
        "la batalla que tenés que ganar en silencio, dentro de vos. Cuando dejás de "
        "dudar de ti, el otro pierde su mejor herramienta. Porque nadie puede manejar a quien ya no se pregunta si vale.",
        f"{PROTAGONISTA} standing straight with a calm firm face, her feet solid "
        f"on the floor, morning light entering through a window, quiet inner "
        f"strength, {WARM}",
        "woman standing firm morning light", 8))

    # 5
    S.append(_scene(
        "No expliques tu vida al que ya decidió no entenderte.",
        f"{PROTAGONISTA} calmly closing a wooden door behind her with one hand, "
        f"warm light from inside, {MANIPULADOR} on the other side barely visible "
        f"in cool shadow, quiet boundary, {WARM}",
        "woman closing wooden door", 9))
    S.append(_scene(
        "Hay gente que solo pide explicaciones para encontrar grietas y usarlas en "
        "tu contra. Vos ya explicaste de sobra, más de una vez. A partir de hoy, "
        "explicá una vez, con amor, y callate. El que quiere entender, entiende; el que "
        "no quiere, nunca va a entender aunque le des tu vida en palabras. Tu tiempo "
        "vale más que otra discusión inútil. Quien te quiere, se acerca; quien te usa, se cansa y se va. No gastes palabras donde no hay oídos.",
        f"{PROTAGONISTA} pressing her lips softly, holding back words, holding a "
        f"small notebook to her chest, warm lamp light, serene restraint, {WARM}",
        "woman holding words notebook", 10))

    # 6
    S.append(_scene(
        "La culpa que te echan no es tuya: es su herramienta.",
        f"{MANIPULADOR} holding out an old iron key toward {PROTAGONISTA}, the "
        f"key representing guilt used to unlock her will, cold shadow on him, "
        f"warm light on her hesitant hand, {TENSE}",
        "man holding iron key to woman", 11, light=False, ai_video=True,
        ai_model="wan-fast",
        av=(f"{MANIPULADOR} slowly holding out an old iron key toward "
        f"{PROTAGONISTA}, she hesitates with her hand, cold shadow on him, warm "
        f"light on her, slow zoom-in, 16:9, photorealistic")))
    S.append(_scene(
        "Cuando alguien te hace sentir culpable para que obedezcas, acordate de esto: "
        "esa culpa no es un examen, es una llave. Te la dan para abrir tu voluntad y "
        "que hagas lo que ellos quieren. Devolvésela con silencio, no con pelea. "
        "Preguntate si hiciste mal a propósito, con intención; si no, andá en paz. "
        "La paz es tu respuesta. La culpa verdadera corrige y sana; la falsa, solo amarra.",
        f"{PROTAGONISTA} serene with eyes closed, the iron key resting untouched "
        f"on the table beside her, soft morning light, returning guilt with "
        f"peace, {WARM}",
        "iron key on table woman serene", 12))

    # 7
    S.append(_scene(
        "El manipulador no teme tu defensa: teme tu paz.",
        f"{PROTAGONISTA} sitting in calm stillness like an armor, hands resting "
        f"on her knees, while {MANIPULADOR} stands across with nowhere to grab, "
        f"soft diffused light, unshakeable peace, {WARM}",
        "calm woman sitting armor stillness", 13, ai_video=True,
        ai_model="wan-fast",
        av=(f"{PROTAGONISTA} sitting perfectly still like armor, hands on her "
        f"knees, slow breathing, while {MANIPULADOR} shifts across with nowhere "
        f"to grab, soft diffused light, unshakeable peace, 16:9, photorealistic")))
    S.append(_scene(
        "Una persona en paz no se puede manejar. Mientras vos estés serena, el otro "
        "no tiene dónde agarrarse: tus reacciones son el anzuelo, y si no mordés, no "
        "hay pesca. Por eso la calma no es pasividad: es la armadura más fuerte que "
        "existe. Nadie controla a alguien que no se desespera. Cuidá tu paz como un "
        "tesoro, porque es tu libertad. La paz no se negocia: se cuida todos los días. Y cuando sientas que pierdes la paz, respirá hondo tres veces antes de responder.",
        f"{PROTAGONISTA} resting a hand over her heart, breathing slowly, warm "
        f"window light on her peaceful face, guarding her peace as treasure, "
        f"{WARM}",
        "woman hand over heart breathing", 14))

    # 8
    S.append(_scene(
        "Si tenés que gritar para que te escuchen, el problema no es tu voz: es el "
        "que no quiere oír.",
        f"{PROTAGONISTA} lowering her volume and speaking with calm clarity, one "
        f"hand palm-down in a gentle hush gesture, {MANIPULADOR} leaning back "
        f"caught off guard, {WARM}",
        "woman calm hush gesture", 15, ai_video=True, ai_model="wan-fast",
        av=(f"{PROTAGONISTA} speaking with calm clarity while lowering one hand "
        f"in a gentle hush gesture, {MANIPULADOR} leaning back caught off guard, "
        f"warm light, slow zoom-out, 16:9, photorealistic")))
    S.append(_scene(
        "Gritar nos deja vacíos y, encima, le da la razón al otro: te muestra enojado "
        "y se queda tranquilo. El que no te escucha, no te escucha ni a los gritos. "
        "Cambiá la estrategia: bajá el volumen, subí la claridad. Decilo una vez, con "
        "calma, y retirate. Lo que no se oye en voz alta, se oye en silencio. Y lo que vale no se grita: se dice con el corazón sereno.",
        f"{PROTAGONISTA} walking away composed after saying her piece, {MANIPULADOR} "
        f"standing speechless in the background, quiet clarity winning, {WARM}",
        "woman walking away composed", 16))

    # 9
    S.append(_scene(
        "El sabio no discute con quien vive de la pelea: se retira, y al retirarse "
        "gana.",
        f"{PROTAGONISTA} walking away down a quiet path at dawn, golden light "
        f"ahead of her, peace as her victory, hands relaxed, {WARM}",
        "woman walking dawn path peace", 17, ai_video=True,
        ai_model="wan-fast",
        av=(f"{PROTAGONISTA} walking away down a quiet path at dawn, golden "
        f"light ahead of her, camera following gently behind, peace as her "
        f"victory, hands relaxed, 16:9, photorealistic")))
    S.append(_scene(
        "Retirarse no es huir: es elegir el campo de batalla. Hay gente que solo sabe "
        "pelear, y en ese terreno nadie gana nunca. El sabio se guarda su energía para "
        "lo que vale: la familia, la fe, el trabajo hecho con amor, el descanso. Dejá "
        "que el otro se quede con su discusión; vos llevate tu paz. A la larga, la paz "
        "siempre tiene la última palabra. Porque el final no lo escribe el que más habla, sino el que mejor vive. No todo conflicto es tuyo: a veces la mejor respuesta es no tomar el conflicto ajeno.",
        f"{MANIPULADOR} holding his own argument alone at a table while "
        f"{PROTAGONISTA} sits far away with her cup of tea in warm light, "
        f"serene distance, {WARM}",
        "man alone at table woman with tea", 18))

    # 10 (cierre: loop con el gancho)
    S.append(_scene(
        "Y la última, la más importante: el que te manipula no teme tus gritos, teme "
        "tu silencio.",
        f"{PROTAGONISTA} and {MANIPULADOR} in a tight two-person frame, she "
        f"serene and silent, he deflating slowly, re-framing of the opening "
        f"confrontation, soft warm light, {WARM}",
        "woman serene facing man", 19))
    S.append(_scene(
        "Volvé a este video cada vez que alguien te quiera hacer pisar el palito. La "
        "próxima vez, respirá hondo, contá hasta tres y callate con calma. Esa pausa es "
        "tu armadura: en esos tres segundos el otro ya perdió. El silencio del sabio "
        "no es orgullo, es paz. Y la paz es el idioma que el manipulador nunca "
        "aprende. Quedate con esa frase, y que sea tu escudo. Y si fallás una vez, no pasa nada: el método se aprende con la práctica.",
        f"{PROTAGONISTA} holding a three-count pause with one finger raised, "
        f"calm steady breath, quiet armor, warm morning light, {WARM}",
        "woman three count pause finger", 20))

    # Bonus "una cosa más" (+end-screen)
    S.append(_scene(
        "Una cosa más. Cuando callás por amor y no por castigo, tu silencio también "
        "sana. No se trata de ignorar a la gente, se trata de no dejarse manejar. "
        "Cerrá los ojos un momento y practicá ahora: respirá, soltá los hombros, y "
        "pensá en alguien a quien hoy podés regalarle tu calma. Ese es el método del "
        "sabio. Y la próxima vez que sientas el nudo en el estómago antes de responder, "
        "acordate: ese nudo es la señal, y la calma es la respuesta.",
        f"{PROTAGONISTA} with eyes closed, taking a deep breath, shoulders "
        f"releasing, soft golden light on her peaceful face, practicing calm "
        f"now, {WARM}",
        "woman eyes closed breathing", 21, ai_video=True, ai_model="wan-fast",
        av=(f"{PROTAGONISTA} with eyes closed taking a deep breath, shoulders "
        f"slowly releasing, soft golden light on her peaceful face, gentle "
        f"zoom-in, practicing calm, 16:9, photorealistic")))
    S.append(_scene(
        f"{cta_text}",
        sabio.scene_prompt("old_door"),
        "elderly man open wooden door warm light", 22))

    return S


if __name__ == "__main__":
    sc = scenes("Suscríbete, dale like y comenta.")
    total = sum(len(s["text"].split()) for s in sc)
    n_vid = sum(1 for s in sc if s.get("ai_video"))
    print(f"{len(sc)} escenas, {total} palabras (~{total/2.3/60:.1f} min a rate -8%), "
          f"{n_vid} con ai_video")