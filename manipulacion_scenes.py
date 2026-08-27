#!/usr/bin/env python3
"""Escenas del largo "5 señales de manipulación que confundís con cariño".

Guion aprobado por el usuario (2026-08-14). Prompts cortos para Pollinations
(usuario, 2026-08-15): [personaje/escena] + [acción] + [metáfora concreta] +
[luz/ambiente] + [estilo] + [formato]. Estructura deliberadamente SIMPLE
(sin 40 instrucciones) porque Pollinations pierde lo importante con prompts
gigantes.

Arco visual (el espectador percibe la historia SIN audio):
1-7  oscuro / confusión
8-17 tensión / manipulación
18-29 duda / conflicto
30-35 recuperación del control
36-38 luz / libertad / serenidad

Escenas simbólicas (cadena, llave, espejo, cinco puertas, vela) > literalismo.
Estructura (39 escenas): gancho + contexto + 5 señales + síntesis + pausa +
recuerdo + fortaleza serena + CTA. Textos 1-38 FIJOS (audio TTS por hash);
la 39 es el CTA final (like + campanita).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

MOTIONS = [
    "zoom-in", "pan-right", "zoom-out", "pan-left", "zoom-in", "pan-right",
    "zoom-out", "pan-left", "zoom-in", "pan-right", "zoom-out", "pan-left",
    "zoom-in", "pan-right", "zoom-out", "pan-left", "zoom-in", "pan-right",
    "zoom-out", "pan-left", "zoom-in", "pan-right", "zoom-out", "pan-left",
    "zoom-in", "pan-right", "zoom-out", "pan-left", "zoom-in", "pan-right",
    "zoom-out", "pan-left", "zoom-in", "pan-right", "zoom-out", "pan-left",
    "zoom-in", "pan-right", "zoom-out",
]


def _scene(text, ai, q, idx):
    return {
        "text": text,
        "ai": ai,
        "q": q,
        "motion": MOTIONS[idx % len(MOTIONS)],
    }


def scenes(cta_text):
    E = []
    i = [0]

    def add(text, ai, q):
        i[0] += 1
        E.append(_scene(text, ai, q, i[0]))

    # 1 — La carga invisible
    add(
        "Sentís una carga que no sabés de dónde viene. Decís que sí, aunque "
        "querías decir que no. Te sentís culpable por poner un límite. Y lo más "
        "extraño es que nadie te obligó.",
        "Exhausted adult person walking alone with a huge invisible heavy "
        "backpack, feeling guilty and confused, nobody forcing them, quiet city "
        "street, cinematic photorealistic film still, psychological drama, "
        "moody lighting, muted colors, 16:9, no text",
        "tired person backpack street",
    )
    # 2 — Cinco señales invisibles
    add(
        "Hoy te voy a mostrar cinco señales invisibles de que alguien puede "
        "estar manipulándote sin que te des cuenta. Pero, sobre todo, qué podés "
        "hacer frente a cada una sin convertirte en una persona fría, "
        "desconfiada o cruel.",
        "Adult person standing before five dark doors, each door casting a "
        "different shadow, mysterious invisible dangers, thoughtful expression, "
        "cinematic psychological photography, muted colors, dramatic lighting, "
        "16:9, no text",
        "five dark doors corridor person",
    )
    # 3 — La bondad usada en tu contra
    add(
        "Porque tu bondad no es el problema. El problema aparece cuando alguien "
        "aprende a usarla en tu contra.",
        "Kind adult helping another person, the other person secretly pulling "
        "them forward by the helping hand, subtle manipulation, no violence, "
        "cinematic realistic photography, dark background, 16:9",
        "two people hand help pull",
    )
    # 4 — La manipulación silenciosa
    add(
        "Cuando pensamos en manipulación, imaginamos gritos, amenazas o alguien "
        "intentando controlar cada movimiento que hacemos. Pero muchas veces no "
        "funciona así. La manipulación más efectiva puede ser silenciosa.",
        "Calm adult sitting alone while a hidden person behind them casts a "
        "huge controlling shadow, silent manipulation, psychological cinematic "
        "photography, dark room, 16:9",
        "person sitting quiet room shadow",
    )
    # 5 — Creer que la decisión fue tuya
    add(
        "No te ordena. Te hace sentir que la decisión fue tuya. No te obliga. "
        "Hace que tengas miedo de decepcionar. No te quita la libertad. Hace "
        "que usarla te haga sentir culpable.",
        "Adult choosing between two identical doors while another person "
        "watches secretly from behind, illusion of free choice, cinematic "
        "psychological drama, muted colors, 16:9",
        "two doors person choosing",
    )
    # 6 — Parece cariño
    add(
        "Y por eso es tan difícil reconocerla. Porque muchas veces no parece "
        "violencia. Parece cariño. Parece confianza. Parece una necesidad "
        "urgente. Y a veces incluso parece amor.",
        "Two adults hugging warmly, one secretly holding a thin rope connected "
        "to the other person's wrist, affection hiding control, cinematic "
        "realistic photography, 16:9",
        "two people hugging rope wrist",
    )
    # 7 — Volver a tu centro
    add(
        "Por eso, en lugar de enseñarte a sospechar de todo el mundo, quiero "
        "enseñarte algo mucho más útil: a reconocer cuándo una situación está "
        "intentando sacarte de tu centro. Y responder desde ahí.",
        "Calm adult standing in the center while many hands reach toward them "
        "from every direction, staying centered despite outside pressure, "
        "cinematic psychological photography, 16:9",
        "person standing still dark room hands",
    )

    # --- SEÑAL 1 — FALSA URGENCIA ---
    # 8
    add(
        "Señal uno. La falsa urgencia. Necesito que decidas ahora. Contestame "
        "ya. Si realmente te importara, no tendrías que pensarlo tanto. ¿Te "
        "suena?",
        "Anxious adult staring at smartphone filled with incoming "
        "notifications, large clock in background, feeling rushed, dark "
        "cinematic lighting, realistic photography, 16:9",
        "person smartphone notifications dark",
    )
    # 9
    add(
        "La urgencia puede ser una herramienta muy poderosa porque reduce tu "
        "capacidad de pensar. Cuando sentís que tenés que responder de "
        "inmediato, dejás de preguntarte si querés hacer esto, y empezás a "
        "preguntarte cómo hacer para que esta persona no se enoje. Ahí está la "
        "trampa. No siempre hay una emergencia real.",
        "Confused adult at a crossroads looking at a huge clock instead of the "
        "two paths, pressure destroying clear thinking, cinematic "
        "psychological scene, 16:9",
        "crossroads two paths clock person",
    )
    # 10
    add(
        "Y acá aparece una respuesta del estoicismo extremadamente sencilla: "
        "lo pienso y te aviso. Nada más. No necesitás justificarte. No "
        "necesitás escribir un párrafo explicando por qué. No necesitás pedir "
        "permiso para pensar.",
        "Calm adult placing smartphone face down and closing eyes to think, "
        "peaceful room, warm window light, stoic cinematic photography, 16:9",
        "person table phone face down calm",
    )
    # 11
    add(
        "Porque la prisa de otra persona no se convierte automáticamente en una "
        "obligación tuya. El filósofo Epicteto enseñaba que debemos distinguir "
        "entre aquello que depende de nosotros y aquello que no. La reacción de "
        "la otra persona no depende de vos. Tu decisión, sí. Así que recuperá "
        "algo muy simple: tiempo.",
        "Calm adult looking at a wristwatch while another person waits "
        "impatiently in the blurred background, reclaiming personal time, "
        "cinematic photography, 16:9",
        "person holding watch calm",
    )

    # --- SEÑAL 2 — HALAGO INTERESADO ---
    # 12
    add(
        "Señal dos. El halago interesado. Esta es mucho más difícil de "
        "detectar. Porque el halago no se siente como una amenaza. Se siente "
        "bien. Sos la única persona en la que puedo confiar. Siempre estás "
        "cuando te necesito. Sabía que vos me ibas a entender.",
        "Person warmly complimenting another adult while secretly placing a "
        "small key into their hand, friendly surface hiding manipulation, "
        "cinematic realistic photography, 16:9",
        "two people talking key hand",
    )
    # 13
    add(
        "Y después aparece el pedido. Un favor enorme. Una excepción. Algo que "
        "probablemente no aceptarías tan fácilmente si el elogio no hubiera "
        "aparecido antes. El problema no es que alguien te felicite. El problema "
        "es cuando el elogio funciona como una llave para abrir una puerta que "
        "normalmente mantendrías cerrada.",
        "Close-up of a golden key opening a locked wooden door, symbolic of "
        "praise unlocking something normally closed, cinematic dramatic "
        "lighting, 16:9",
        "hand golden key door opening",
    )
    # 14
    add(
        "Entonces hacé algo muy sencillo. Separá el cariño de la petición. "
        "Preguntate: si esta persona no me hubiera dicho nada bonito, ¿igual "
        "aceptaría? Si la respuesta es no, entonces evaluá el pedido por sí "
        "mismo. No por cómo te hizo sentir antes.",
        "Adult sitting at table examining a wooden heart and a separate heavy "
        "box, separating affection from a request, minimalist cinematic "
        "photography, 16:9",
        "person table wooden heart box",
    )
    # 15
    add(
        "Porque alguien puede quererte y aun así pedirte algo injusto. Y alguien "
        "puede decirte algo hermoso y aun así estar intentando conseguir algo "
        "de vos. No hace falta acusarlo. No hace falta pelear. Simplemente "
        "aprendé a mirar la petición sin el envoltorio.",
        "Adult opening a beautiful gift box and discovering a heavy metal "
        "burden inside, happiness turning into realization, cinematic "
        "psychological photography, 16:9",
        "person opening gift box heavy",
    )

    # --- LA BONDAD COMO PUNTO DÉBIL ---
    # 16
    add(
        "Pero acá está lo más serio de todo. No te manipulan necesariamente "
        "porque seas débil. Muchas veces ocurre exactamente lo contrario. Usan "
        "una de tus mejores cualidades como herramienta contra vos. Tu empatía. "
        "Tu capacidad de perdonar. Tu deseo de ayudar. Tu miedo a lastimar.",
        "Kind empathetic adult helping someone while many other hands reach "
        "toward them asking for help, kind but exhausted expression, cinematic "
        "realism, 16:9",
        "person helping many hands exhausted",
    )
    # 17
    add(
        "Y si alguien descubre que puede conseguir lo que quiere activando esas "
        "cualidades, puede empezar a utilizarlas. Por eso proteger tus límites "
        "no significa dejar de ser buena. Significa impedir que tu bondad deje "
        "de ser una elección. Porque si solamente ayudás cuando alguien consigue "
        "hacerte sentir culpable, eso ya no es generosidad. Es presión.",
        "Generous adult giving everything to many reaching hands until their "
        "own hands are empty, generosity becoming pressure, emotional cinematic "
        "photography, 16:9",
        "person giving hands empty exhausted",
    )

    # --- SEÑAL 3 — PRESIÓN DE LA MAYORÍA ---
    # 18
    add(
        "Señal tres. Todos están de acuerdo menos vos. Todos piensan lo mismo. "
        "Preguntale a cualquiera. Vos sos la única que lo ve así. Esta frase "
        "parece una prueba. Pero no lo es. Que muchas personas crean algo no "
        "convierte automáticamente esa creencia en verdad.",
        "One adult sitting alone opposite a group of six people who all agree "
        "with each other, isolated person looking thoughtful, social pressure, "
        "cinematic realism, 16:9",
        "person alone table group opposite",
    )
    # 19
    add(
        "Séneca, el filósofo, insistía en la importancia de no dejarnos "
        "arrastrar simplemente por la multitud. Porque existe una forma muy "
        "poderosa de presión: hacerte sentir que estás sola. Cuando creés que "
        "todos están de acuerdo, aparece una pregunta incómoda: ¿y si el "
        "problema soy yo?",
        "Confused adult surrounded by mirrors, every mirror reflecting a crowd "
        "while only one person stands in reality, questioning own judgment, "
        "psychological cinematic scene, 16:9",
        "person alone mirrors group reflection",
    )
    # 20
    add(
        "Y entonces podés terminar abandonando tu propio criterio simplemente "
        "para volver a sentirte aceptada. La respuesta estoica es simple: que "
        "muchos lo crean no significa que sea verdad. Después, buscá los hechos. "
        "¿Qué ocurrió realmente? ¿Qué evidencia existe? ¿Qué estoy pensando yo?",
        "Adult leaving a blurred crowd and examining photographs, documents and "
        "a calendar on a well-lit desk, searching for facts, cinematic realism, "
        "16:9",
        "person desk evidence crowd blurred",
    )
    # 21
    add(
        "Y, sobre todo: ¿cambiaría de opinión si nadie estuviera mirando? Si la "
        "respuesta es sí, quizás no estás siguiendo la verdad. Estás siguiendo "
        "la presión.",
        "Adult alone before a large mirror, looking honestly at their own "
        "reflection, no other people present, introspective and peaceful, "
        "cinematic photography, 16:9",
        "person alone mirror introspection",
    )

    # --- SEÑAL 4 — DISTORSIONAR LA REALIDAD ---
    # 22
    add(
        "Señal cuatro. Cuando empiezan a cambiar tu realidad. Esta es "
        "especialmente peligrosa. Contás algo que ocurrió. Y la otra persona "
        "responde: eso nunca pasó. Estás exagerando. Te lo imaginaste. Yo nunca "
        "dije eso. Siempre entendés todo mal.",
        "Two adults arguing calmly, one holding photographs while the other "
        "denies what happened, confused expression, psychological manipulation, "
        "cinematic realism, 16:9",
        "two people table photographs deny",
    )
    # 23
    add(
        "Una conversación aislada no significa necesariamente manipulación. "
        "Todos recordamos las cosas de manera diferente. Pero cuando esto se "
        "convierte en un patrón, cuando constantemente terminás dudando de tu "
        "memoria, de tus percepciones y hasta de tu criterio, tenés que "
        "detenerte.",
        "Adult staring at a cracked mirror with multiple reflections of their "
        "own face, confusion and self-doubt, psychological cinematic "
        "photography, 16:9",
        "person cracked mirror fragments",
    )
    # 24
    add(
        "Porque una persona puede discutir tu interpretación. Pero no debería "
        "necesitar destruir tu confianza en vos misma para ganar una discusión. "
        "La respuesta no es entrar en una guerra de recuerdos. Es volver a los "
        "hechos.",
        "Two adults disagreeing at a table covered with photographs, documents "
        "and calendar, one stops arguing and calmly examines the evidence, "
        "cinematic realism, 16:9",
        "two people disagreement evidence table",
    )
    # 25
    add(
        "Anotá lo importante. Guardá mensajes cuando sea necesario. Recordá "
        "fechas. Separá lo que sabés de lo que suponés. Y preguntate: ¿qué "
        "ocurrió, independientemente de cómo esta persona quiere que yo me "
        "sienta al respecto? Tu conciencia no necesita gritar para ser válida.",
        "Close-up of adult hand writing dates in a notebook beside photographs, "
        "phone and calendar, recording important facts, warm natural light, "
        "cinematic photography, 16:9",
        "hand writing notebook photographs",
    )

    # --- SEÑAL 5 — LA CULPA COMO CADENA ---
    # 26
    add(
        "Señal cinco. La culpa como cadena. Y esta probablemente sea una de las "
        "más fáciles de reconocer cuando aprendés a verla. Si me quisieras, "
        "harías esto. Después de todo lo que hice por vos. Me estás "
        "decepcionando. Yo lo haría por vos.",
        "Sad adult with a thin metal chain symbolically connected to their "
        "chest, chain extending toward another person in the shadows, guilt as "
        "emotional control, cinematic realism, 16:9",
        "person chain chest guilt shadow",
    )
    # 27
    add(
        "El mensaje escondido es: si no hacés lo que quiero, sos una mala "
        "persona. Y ahí aparece una confusión muy peligrosa. Confundimos amor "
        "con obediencia. Confundimos empatía con obligación. Confundimos poner "
        "un límite con ser egoístas.",
        "Adult standing like a realistic human marionette with nearly invisible "
        "strings controlled by another person, emotional obedience and guilt, "
        "mature psychological drama, 16:9",
        "person marionette strings arms",
    )
    # 28
    add(
        "Pero Epicteto nos recuerda una idea fundamental: cada persona es "
        "responsable de su propia vida y de sus propias decisiones. Vos podés "
        "acompañar. Podés ayudar. Podés escuchar. Pero no podés vivir la vida "
        "de otra persona por ella.",
        "Two adults at a fork in the road peacefully choosing different paths, "
        "accepting separate lives and decisions, sunrise, stoic cinematic "
        "photography, 16:9",
        "two people fork road different paths",
    )
    # 29
    add(
        "Y tampoco necesitás sacrificar tu paz para demostrar que te importa. "
        "Una respuesta puede ser tan sencilla como: entiendo que estés dolido, "
        "pero esta decisión me corresponde a mí. No es crueldad. Es un límite. "
        "Y un límite no necesita una disculpa para existir.",
        "Two adults facing each other, one calmly raising an open hand to "
        "establish a respectful boundary, peaceful expressions, soft line of "
        "light between them, cinematic realism, 16:9",
        "two people face to face boundary hand",
    )

    # --- CIERRE — RECUPERACIÓN DEL CONTROL (la luz progresa) ---
    # 30
    add(
        "Entonces, ¿qué hacemos? No se trata de volverte fría. No se trata de "
        "desconfiar de todos. No se trata de mirar cada favor como una "
        "conspiración. Eso también sería otra forma de perder la paz. La "
        "filosofía estoica propone algo mucho más difícil: mantener la bondad "
        "sin entregar el control de tu mente.",
        "Calm adult protecting a small glowing candle while hands reach from "
        "darkness toward it, protecting kindness and inner peace, cinematic "
        "symbolic photography, 16:9",
        "person protecting candle hands dark",
    )
    # 31
    add(
        "Podés seguir siendo generosa. Pero elegir cuándo ayudar. Podés seguir "
        "siendo empática. Pero sin convertirte en responsable de las emociones "
        "de todos. Podés perdonar. Sin permitir que alguien repita eternamente "
        "el mismo daño. Y podés amar. Sin abandonar tus propios límites.",
        "Adult helping another person stand while maintaining a clear personal "
        "boundary, compassionate but firm, peaceful cinematic photography, 16:9",
        "person helping stand boundary line",
    )
    # 32
    add(
        "Porque tu paz no existe para que los demás la utilicen. Existe para "
        "que puedas vivir bien, y también servir mejor a quienes realmente "
        "necesitan de vos.",
        "Peaceful adult sitting beside a lake at sunrise while distant people "
        "try to get their attention, person remains calm, cinematic stoic "
        "photography, 16:9",
        "person lake sunrise peaceful",
    )
    # 33
    add(
        "Y hay una cosa más. Quizás la herramienta más sencilla de todas sea "
        "también la más poderosa: la pausa. La próxima vez que alguien te haga "
        "una petición que te genere presión, no respondas de inmediato. "
        "Quedate en silencio. Lo voy a pensar. Nada más.",
        "Adult receiving a message, placing smartphone face down and taking a "
        "deep breath instead of responding, calm self-control, cinematic "
        "photography, 16:9",
        "person phone face down pause breath",
    )
    # 34
    add(
        "Ese pequeño espacio cambia todo. Porque durante unos segundos dejás de "
        "reaccionar a la emoción que alguien acaba de provocar en vos. Y volvés "
        "a elegir. No tenés que explicar de inmediato. No tenés que convencer a "
        "nadie. No tenés que demostrar que sos una buena persona. Podés pensar. "
        "Podés respirar. Y después decidir.",
        "Calm adult standing still while a chaotic blurred crowd moves rapidly "
        "behind them, deep breathing and inner peace, cinematic psychological "
        "photography, 16:9",
        "person quiet breathing crowd blurred",
    )
    # 35
    add(
        "Porque una decisión tomada en paz sigue siendo tuya. Una decisión "
        "tomada por miedo a decepcionar, muchas veces pertenece a otra persona.",
        "Adult standing at two paths, dark path filled with shadows and "
        "pressure, bright path peaceful and open, calmly choosing bright path, "
        "cinematic realism, 16:9",
        "person fork road light dark paths",
    )
    # 36 — Resumen visual de las cinco señales
    add(
        "Así que recordá las cinco señales: falsa urgencia. Halago interesado. "
        "Presión de la mayoría. Distorsión de los hechos. Y culpa como cadena. "
        "No para vivir sospechando. Sino para conservar algo mucho más "
        "importante: la libertad de elegir quién querés ser.",
        "Calm adult standing free while five broken chains lie at their feet, "
        "dawn light breaking through, sense of liberation after being bound by "
        "five invisible controls, cinematic symbolic photography, 16:9, no text",
        "person center five symbols clock key mirror chain",
    )
    # 37
    add(
        "Porque ser una buena persona no significa estar disponible para que "
        "cualquiera use tu bondad. Significa poder hacer el bien, sin dejar de "
        "gobernarte a vos misma.",
        "Strong calm adult standing beside a peaceful horse, holding its reins, "
        "vast landscape at sunrise, symbol of self-control and inner freedom, "
        "cinematic realism, 16:9",
        "person reins horse sunrise landscape",
    )
    # 38 — Fortaleza serena (cierre potente)
    add(
        "Si este tipo de filosofía práctica te ayuda a vivir con más calma, "
        "criterio y fortaleza, suscribite. Acá no buscamos volvernos de "
        "piedra. Buscamos algo mucho más difícil: una fortaleza serena.",
        "Solitary adult standing on mountain at sunrise, looking toward vast "
        "horizon, calm confident posture, inner strength and serenity, epic "
        "cinematic photorealism, 16:9",
        "person mountain sunrise horizon freedom",
    )
    # 39 — CTA final (like + campanita)
    add(
        cta_text,
        "Calm adult standing on a high terrace at sunrise looking toward vast "
        "peaceful landscape, grateful relaxed posture, golden light, epic "
        "cinematic photorealism, 16:9",
        "person terrace sunrise gratitude peace",
    )
    return E
