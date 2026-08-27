#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_caverna as m
import hacer_videos_nuevos as n
import sabio

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJECT_ROOT, "videos")
WARM_STYLE = ", bright airy, golden hour warm light, high-key soft diffused window light, warm cream and sage palette, gentle highlights, no hard shadows, crisp and colorful, photorealistic, high detail"

VOICES = {
    "jorge": {"voice": "es-MX-JorgeNeural", "deepen": 0.92},
}

SHORTS = [
    {
        "id": "soltar",
        "voices": ["jorge"],
        "rate": "-8%",
        "text": ("Tu cansancio no viene de lo que haces.\n\n"
                 "Viene de lo que {y}intentas controlar{/y}.\n\n"
                 "Hoy suelta {y}una sola expectativa{/y}.\n\n"
                 "Menos control, {y}menos cansancio{/y}."),
        "prompt": "Close-up of a woman's hands in her fifties gently releasing golden autumn leaves into a soft breeze, warm golden hour light, shallow depth of field, serene garden bokeh background, photorealistic, cinematic, high detail, shot on 85mm f/1.4",
        "q": "hands leaves",
        "style": WARM_STYLE,
        "text_mode": "serif",
        "motion": "zoom-in",
        "bgm": True,
    },
    {
        "id": "soltar_yt",
        "voices": ["jorge"],
        "rate": "-8%",
        "text": ("Tu cansancio no viene de lo que haces.\n\n"
                 "Viene de lo que {y}intentas controlar{/y}.\n\n"
                 "Hoy suelta {y}una sola expectativa{/y}.\n\n"
                 "Menos control, {y}menos cansancio{/y}."),
        "prompt": "Close-up of a woman's hands in her fifties gently releasing golden autumn leaves into a soft breeze, warm golden hour light, shallow depth of field, serene garden bokeh background, photorealistic, cinematic, high detail, shot on 85mm f/1.4",
        "q": "hands leaves",
        "style": WARM_STYLE,
        "text_mode": "serif",
        "motion": "zoom-in",
        "bgm": True,
        "cta": "Si esto te hizo sentido, suscríbete.",
    },
    {
        "id": "florecer_fb",
        "voices": ["jorge"],
        "rate": "-8%",
        "text": ("Quizás no estás estancada.\n\n"
                 "Quizás estás intentando crecer en un lugar donde siempre "
                 "tuviste que sobrevivir.\n\n"
                 "Porque hay algo en nosotros que quiere {y}crecer{/y}. "
                 "Que quiere {y}sanar{/y}. Que quiere {y}volver a ser{/y}.\n\n"
                 "Y a veces no necesita que la arreglen. "
                 "Necesita un lugar donde {y}sea seguro existir{/y}."),
        "cta": "Si esto te hizo sentido, sígueme.",
        "text_mode": "serif",
        "motion": "zoom-in",
        "bgm": True,
    },
    {
        "id": "florecer_yt",
        "voices": ["jorge"],
        "rate": "-8%",
        "text": ("Quizás no estás estancada.\n\n"
                 "Quizás estás intentando crecer en un lugar donde siempre "
                 "tuviste que sobrevivir.\n\n"
                 "Porque hay algo en nosotros que quiere {y}crecer{/y}. "
                 "Que quiere {y}sanar{/y}. Que quiere {y}volver a ser{/y}.\n\n"
                 "Y a veces no necesita que la arreglen. "
                 "Necesita un lugar donde {y}sea seguro existir{/y}."),
        "cta": "Si esto te hizo sentido, suscríbete.",
        "text_mode": "serif",
        "motion": "zoom-in",
        "bgm": True,
    },
    {
        "id": "sobrepiensa",
        "text": "¿Sobrepiensas? Haz este ejercicio. Preguntale a tu mente: ¿cuál será mi próximo pensamiento? ¿Ves? Se quedó en blanco. Tu mente no necesita más vueltas, necesita que la mires. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Pensive redhead woman with freckles looking out window, thoughtful expression, natural light, realistic",
        "style": WARM_STYLE,
    },
    {
        "id": "identidad",
        "text": "¿Cuántos reels viste hoy buscando la fórmula para ser feliz? La respuesta no está ahí. Está en vos, y ya la tenías. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties with eyes closed receiving warm dawn light, serene smile, simple clothing, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "adiestrada",
        "text": "El scroll te tiene encadenada: mientras pasás el dedo, te va robando la atención. No sos débil: está diseñado así. Cortá el scroll: salí de la caverna. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties sitting calmly in warm morning light, gently placing her phone face down, coffee beside her, cozy home, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "ganas",
        "text": "No esperes tener ganas para actuar: mientras esperás, nada cambia. Aristóteles decía: la virtud se practica. Actuar trae las ganas. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties watering a small plant on her windowsill, morning light, hopeful mood, serene, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "perfecta",
        "text": "Mirar las supuestas vidas perfectas de otros te hunden: te dejan sintiéndote menos. Un estudio lo comprobó. Comparate con tu vida real, no con las supuestas vidas perfectas. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties looking out a large window at the morning sun, thoughtful expression, warm light filling the room, contemplative, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "habito",
        "text": "Creés que la disciplina es un don y eso te paraliza. No es tu culpa: la disciplina se entrena. Cambiá tu entorno y la disciplina va apareciendo. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties doing a simple morning routine, pouring tea, tidy and calm kitchen, warm light, steady quiet rhythm, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "descanso",
        "text": "No descansás porque te enseñaron que descansar es perder el tiempo. Por eso estás agotada. El descanso no es premio, es método. Descansar no es perder tiempo: es cuidarte. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties resting peacefully on a sofa, eyes closed, morning light through the window, phone left far away on the table, cozy calm living room, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "paz",
        "text": "Buscás la paz en rituales caros que te venden. La calma de otro no sirve. La paz no se compra: diez minutos de silencio, sin rituales. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties sitting still by a window in early morning silence, hands around a cup of tea, no phone in sight, soft warm light, tranquil serene mood, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "calma",
        "text": "No te alcanza la calma y la mente se estrecha: solo ves lo urgente. No te falta fuerza: es escasez. Salís recuperando la calma con lo que tenés. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties holding a single lit candle in a dark room, warm light on her face, dawn light through an ajar door behind her, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "pasos",
        "text": "Hay una decisión que no achica tu caverna. No es perfecta: es la más inteligente. Tomala otra vez, y otra. Así se sale de la caverna: de a pasos. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties walking out of a cave toward morning light, one step at a time, golden sunrise ahead, hopeful, warm tones",
        "style": WARM_STYLE,
    },
    {
        "id": "estructural",
        "text": "No salís de la caverna negando la cueva: el mundo aprieta. Pero adentro hay un paso que no te encierra más. Ese paso es salir de la caverna. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties inside a cave entrance, hand resting on the stone wall, looking out at warm light entering, thoughtful, golden hour",
        "style": WARM_STYLE,
    },
    {
        "id": "rumiar",
        "text": "Lo que más te agota no es el trabajo: es dar vueltas al mismo pensamiento. Rumiar no es pensar: es repetir el miedo. Cortá el bucle: tu pensamiento no necesita más vueltas, necesita una decisión. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties by a window at dawn, holding a warm cup of tea, eyes softly closed, releasing a worry, serene warm light, golden hour",
        "q": "cup of tea window",
        "style": WARM_STYLE,
    },
    {
        "id": "amor",
        "text": "Pensás que amarte a vos misma te vuelve floja. Es al revés: quien se trata mal no avanza, se apaga. La autocompasión no es debilidad: sostiene el método. Amarte a vos misma no te vuelve floja: te vuelve capaz. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties looking at herself in a mirror with a gentle kind smile, warm morning light through a window, self compassionate mood, golden hour",
        "q": "mirror woman",
        "style": WARM_STYLE,
    },
    {
        "id": "nervios",
        "text": "No reaccionás mal porque estés frágil: tu cuerpo está en alerta hace años. Por eso cualquier cosa te enciende la alarma. No te falta fuerza: te falta bajar la alarma. Y eso también es método. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties sitting still on her bed at sunrise, taking a slow deep breath, hands relaxed on her lap, calm warm bedroom light, golden hour",
        "q": "woman rest",
        "style": WARM_STYLE,
    },
    {
        "id": "cero",
        "text": "Creés que a esta altura solo te queda empezar de cero. Falso: no empezás de cero, empezás de experiencia. Todo lo que viviste no te pesa: te sostiene. Tu historia no es un borrador: es el material. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties standing at a large window at sunrise, looking forward with quiet confidence, warm golden light on her face, hopeful, golden hour",
        "q": "sunrise window",
        "style": WARM_STYLE,
    },
    {
        "id": "tiempo",
        "text": "Sentís que el tiempo nunca te alcanza, y la culpa te come. No es que administres mal: es que te piden todo. Sacar algo también es una decisión. Tu tiempo no se encuentra: se defiende. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties at a small wooden table with an open notebook and a cup of tea, crossing out a task, calm deliberate moment, warm light, golden hour",
        "q": "morning coffee",
        "style": WARM_STYLE,
    },
    {
        "id": "error",
        "text": "No te paraliza la falta de talento: te paraliza el miedo a equivocarte. Pero los errores son información, no veredictos. Erraste mil veces y seguís acá: eso no es fracaso, es camino. Equivocarte no te define: avanzar sí. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Woman in her fifties working with clay at a pottery wheel, hands gently shaping, soft warm studio light, dust in golden air, serene focused mood",
        "q": "pottery wheel",
        "style": WARM_STYLE,
    },
    {
        "id": "ayuda",
        "text": "Te enseñaron que pedir ayuda es de floja y callás lo que te pasa. No es cierto: pedir ayuda es método. Nadie sale solo de la caverna: todos salimos acompañados. Pedir ayuda no es rendirse: es avanzar. Dale un like, suscribite, comentá y compartí.",
        "prompt": "Two women in their fifties sitting together at a kitchen table, talking warmly over coffee, morning light, companionship and relief, golden hour",
        "q": "friends coffee",
        "style": WARM_STYLE,
    },
    {
        "id": "respira",
        "text": "Tu respiración es el control remoto de tu sistema nervioso. Inhalá 4, retené 4, exhalá 6. Tu cuerpo ya sabe calmarse. Probá ahora. Link en el primer comentario.",
        "prompt": "Woman in her fifties sitting calmly with eyes closed, one hand on chest one on belly, slow deep breath, warm morning light, serene peaceful, golden hour",
        "q": "woman breathing meditation",
        "style": WARM_STYLE,
    },
    {
        "id": "muerte",
        "bgm": True,
        "text": "¿Cuántas horas, días, semanas te quedan si viajas al otro lado a los ochenta años? Piensa: ¿para qué cargas rencores si no te los vas a llevar? Él te conoce. El salmo noventa: enséñanos a calcular nuestros años. ¿Tú lo conoces? Dale me gusta, compártelo y sígueme.",
        "text_yt": "¿Cuántas horas, días, semanas te quedan si viajas al otro lado a los ochenta años? Piensa: ¿para qué cargas rencores si no te los vas a llevar? Él te conoce. El salmo noventa: enséñanos a calcular nuestros años. ¿Tú lo conoces? Suscríbete, dale like y comenta.",
        "prompt": "Woman in her sixties standing at an open old wooden door, warm golden morning light streaming in, holding a lit candle, calm serene face, contemplative and peaceful, golden hour",
        "q": "old wooden door light",
        "style": WARM_STYLE,
    },
    {
        "id": "sabio_apura",
        "voices": ["jorge"],
        "text": "El sabio no es el que más sabe: es el que menos se apura. La calma no te atrasa: te adelanta. El sabio es el que menos se apura.",
        "prompt": sabio.scene_prompt("porch_coffee"),
        "style": "",
    },
    {
        "id": "sabio_silencio",
        "voices": ["jorge"],
        "text": "El que te manipula no teme tus gritos: vive de ellos. Lo que teme es que dejes de reaccionar. El sabio no juega: se retira en silencio.",
        "prompt": sabio.scene_prompt("mirror_serene"),
        "style": "",
    },
    {
        "id": "sabio_atencion",
        "voices": ["jorge"],
        "text": "¿Cuánto mirás sin ver? De mañana, de noche, sin saber qué buscabas. La caverna es no mirar adentro. Un minuto de silencio al día. ¿Cuánto mirás sin ver?",
        "prompt": sabio.scene_prompt("mirror_serene"),
        "style": "",
    },
    {
        "id": "integrar",
        "text": "No estás rota. Estás respondiendo con lo que aprendiste.\nTu mente activó un mecanismo de protección. No fue una elección, fue un reflejo.\nIntegrar no es borrar el pasado. Es darte cuenta del reflejo...\n...y elegir qué hacer ahora.\nAyúdame siguiendo este perfil.",
        "prompt": "Intimate close-up of a woman hands gently holding a cracked ceramic bowl repaired with gold veins, kintsugi style, warm soft morning light streaming through a window, shallow depth of field, photorealistic, high detail, shot on 85mm f/1.4",
        "style": WARM_STYLE,
        "rate": "-8%",
    },
    {
        "id": "integrar_yt",
        "text": "No estás rota. Estás respondiendo con lo que aprendiste.\nTu mente activó un mecanismo de protección. No fue una elección, fue un reflejo.\nIntegrar no es borrar el pasado. Es darte cuenta del reflejo...\n...y elegir qué hacer ahora.\nRecuerda suscribirte, y comentar que has integrado ya.",
        "prompt": "Intimate close-up of a woman hands gently holding a cracked ceramic bowl repaired with gold veins, kintsugi style, warm soft morning light streaming through a window, shallow depth of field, photorealistic, high detail, shot on 85mm f/1.4",
        "style": WARM_STYLE,
        "rate": "-8%",
    },
    {
        "id": "burnout",
        "text": "No es que te falte motivación.\nEs que tu sistema nervioso entró en modo ahorro.\nDejaste de sentir entusiasmo no porque seas aburrido, sino porque tu cuerpo decidió que sobrevivir era más importante que disfrutar.\nIntegrar esto no es forzarte a producir más. Es escuchar la señal de parada antes de que el motor se rompa.\nAyúdame siguiendo este perfil.",
        "prompt": "Person sitting at a desk staring blankly at a computer screen, late evening, only screen light illuminating their face, tired posture, real home office setting, documentary style photograph, natural imperfections, Kodak Portra 400",
        "style": WARM_STYLE,
        "rate": "-8%",
    },
    {
        "id": "burnout_yt",
        "text": "No es que te falte motivación.\nEs que tu sistema nervioso entró en modo ahorro.\nDejaste de sentir entusiasmo no porque seas aburrido, sino porque tu cuerpo decidió que sobrevivir era más importante que disfrutar.\nIntegrar esto no es forzarte a producir más. Es escuchar la señal de parada antes de que el motor se rompa.\nRecuerda suscribirte, y comentar que has integrado ya.",
        "prompt": "Person sitting at a desk staring blankly at a computer screen, late evening, only screen light illuminating their face, tired posture, real home office setting, documentary style photograph, natural imperfections, Kodak Portra 400",
        "style": WARM_STYLE,
        "rate": "-8%",
    },
    ]


def download_ai(prompt, out_path, seed=None, style=""):
    try:
        import flux_img
        r = flux_img.generate(prompt + style, out_path)
        m.strip_img_metadata(out_path)
        return r
    except Exception as e:
        print(f"    IA falló: {e}", flush=True)
        raise RuntimeError(f"IA no generó imagen: {prompt[:40]}")


def check_meta_rules(short, timings, total):
    warn = []
    if total > 14.0:
        warn.append(f"duracion {total:.1f}s > 13s (Meta: baja completion)")
    first_on = min((s for _, s, e in timings), default=0.0)
    if first_on > 3.0:
        warn.append(f"voz arranca a los {first_on:.1f}s (Meta: gancho <= 3s)")
    stops = {"que", "no", "es", "la", "las", "los", "el", "de", "en", "y",
             "un", "una", "te", "tu", "con", "por", "para", "contra"}
    sentences = [s.strip() for s in re.split(r"[.!?]", short["text"])
                 if s.strip() and s.strip().lower() not in ("sígueme", "sigueme")]

    def toks(s):
        return {w.strip("¿?,;:").lower() for w in s.split()
                if w.strip("¿?,;:").lower() not in stops and len(w.strip("¿?,;:")) > 3}

    if len(sentences) >= 2 and not (toks(sentences[0]) & toks(sentences[-1])):
        warn.append("loop debil: el final no engancha con el inicio")
    for w in warn:
        print(f"  AVISO [{short['id']}]: {w}", flush=True)
    return warn


def build_short(short, vkey):
    v = VOICES[vkey]
    d = {
        "imgs": os.path.join(ROOT, "shorts", "imgs"),
        "audio": os.path.join(ROOT, "shorts", "audio"),
        "out": os.path.join(ROOT, "shorts", "out"),
        "tmp": os.path.join(ROOT, "shorts", "tmp"),
    }
    for k in d.values():
        os.makedirs(k, exist_ok=True)

    sid = short["id"]
    img_path = os.path.join(d["imgs"], f"{sid}.jpg")
    if not (os.path.exists(img_path) and os.path.getsize(img_path) > 5000):
        try:
            download_ai(short["prompt"], img_path, seed=411, style=short["style"])
        except Exception as e:
            print(f"  IA falló, uso Commons: {e}", flush=True)
            m.download_image({"q": short.get("q")}, img_path)
    m.strip_img_metadata(img_path)

    from shutil import copyfile
    _imgdir = os.path.join(PROJECT_ROOT, "IMAGENES_PARA_VIDEOS")
    os.makedirs(_imgdir, exist_ok=True)
    copyfile(img_path, os.path.join(_imgdir, f"{sid}.jpg"))

    bg_img = os.path.join(d["tmp"], f"{sid}_{vkey}_bg.jpg")
    if short.get("text_mode") == "serif":
        m.build_bg_serif(img_path, bg_img)
    elif short.get("dark"):
        m.build_bg(img_path, bg_img)
        from PIL import Image, ImageFilter
        _bg = Image.open(bg_img).convert("RGB")
        _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        _bg.save(bg_img)
    elif not (short.get("estilo") or short.get("handdraw")):
        m.build_bg_bright(img_path, bg_img)
        from PIL import Image, ImageFilter
        _bg = Image.open(bg_img).convert("RGB")
        _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        _bg.save(bg_img)

    raw_text = short["text"]
    serif_mode = short.get("text_mode") == "serif"
    raw_full = raw_text + "\n" + (short.get("cta") or "")
    if serif_mode:
        tts_text, _ = m.parse_serif_text(raw_text)
        cta_plain, _ = m.parse_serif_text(short.get("cta") or "")
        tts_text = (tts_text + " " + cta_plain).strip()
        clean_text, clean_styles, line_breaks = tts_text, None, None
        emphasis_map = {}
    else:
        # Parse HTML <strong>/<em> tags first, then karaoke styles
        if "<" in raw_text:
            clean_text, emphasis_map = m.parse_html_emphasis(raw_text)
        else:
            emphasis_map = {}
        clean_text, clean_styles, line_breaks = m.parse_karaoke_styles(clean_text)
    use_styles = bool(clean_styles and any(s for s in clean_styles))

    wav = os.path.join(d["audio"], f"{sid}_{vkey}{m.tts_engine_tag(v['voice'])}_{zlib.crc32(raw_full.encode())}.wav")
    if not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(clean_text, v["voice"], wav,
                                  deepen=v["deepen"],
                                  rate=short.get("rate", "+0%")))

    tj = os.path.join(d["tmp"], f"{sid}_{vkey}{m.tts_engine_tag(v['voice'])}_{zlib.crc32(raw_full.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = m.align_words(clean_text, wav)
        if timings is None:
            toks = clean_text.split()
            dur = m.probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))

    mp4 = os.path.join(d["out"], f"{sid}_{vkey}.mp4")
    m.render_pipeline(short, timings, img_path, bg_img, wav, mp4, final=True,
                      motion=short.get("motion"),
                      clean_styles=clean_styles if use_styles else None,
                      line_breaks=line_breaks if use_styles else None,
                      emphasis_map=emphasis_map)
    if short.get("bgm"):
        bgm = os.path.join(ROOT, "bgm", "ambient.wav")
        m.generate_bgm(bgm)
        mixed = mp4 + ".bgm.mp4"
        m.mix_bgm(mp4, bgm, mixed)
        os.replace(mixed, mp4)
    total = m.probe_duration(mp4)
    check_meta_rules(short, timings, total)
    print(f"OK {mp4} {total:.1f}s", flush=True)


if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for short in SHORTS:
        if only and short["id"] != only:
            continue
        for vkey in short.get("voices") or list(VOICES):
            print(f"[{short['id']}/{vkey}]", flush=True)
            build_short(short, vkey)
