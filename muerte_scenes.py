#!/usr/bin/env python3
"""Escenas del video largo "muerte" (Salmo 90, soltar rencores, la puerta).

Mismo guion para Facebook vertical y YouTube horizontal. El CTA final
difiere por plataforma: FB "Sígueme, dale like y comenta." / YT
"Suscríbete, dale like y comenta." Se pasa como argumento a scenes_muerte().
Voz única jorge (male), rate -8% (más pausado, más énfasis).
Las escenas claras (esperanza/método/la puerta) llevan "light": True;
LIGHT = conjunto 1-based de esas posiciones (para LIGHT_SCENES de FB).

Narración alineada a la fe católica (regla no negociable de AGENTS.md):
nunca decir algo contrario a la fe Católica Apostólica Romana, aunque no se
usen los términos explícitos para no chocar al no creyente. Las imágenes
siguen siendo GENÉRICAS (sin iconografía católica): sin cruces, santos,
iglesias ni lugares de culto — que un no católico no se sienta excluido, y
que tampoco contradigan a la fe.

Cambios teológicos del Acto 2 (corrección del usuario, 2026-08-11):
- Escena 5: de lista de "lo que me hacen" a EXAMEN DE CONCIENCIA personal
  (propias omisiones y faltas de caridad).
- Escena 7: se eliminó la visión utilitarista del perdón ("lo hago por mí");
  se sustituyó por la teología del perdón divino — perdonamos porque Dios nos
  amó y perdonó primero (Mt 6,12).
- Escena 8: "rencor y mentira" pasan a "egoísmo y soberbia de no querer
  perdonar", apuntando al pecado capital de la soberbia que bloquea la gracia.
"""


def scenes_muerte(cta):
    s = [
        # --- Acto 1: la cuenta ---
        {"ai": "Woman in her sixties standing alone in a dim room at night facing a tall dark window, faint moonlight through the glass, pensive and still, shot on 85mm f/1.4, shallow depth of field, dark and moody, dramatic lighting, photorealistic, high detail",
         "q": "elderly woman window night",
         "text": "¿Cuántas horas, días, semanas de vida te quedan si te tocara viajar al otro lado a los ochenta años? La pregunta suena rara, pero es la más seria que puedes hacerte hoy. Y casi nadie se la hace.",
         "motion": "zoom-in"},
        {"ai": "Close-up of weathered elderly hands turning pages of an old paper calendar, warm dim lamp light, counting days, a fountain pen beside, nostalgic and solemn, shot on 50mm f/2, dark and moody, cinematic, photorealistic, high detail",
         "q": "old calendar hands",
         "text": "Ochenta años son veintinueve mil días. Si tienes cincuenta y cinco, ya gastaste veinte mil. Los que quedan no son infinitos: son una cantidad que cabe en una hoja de papel. Y la mayoría no quiere hacer esa cuenta.",
         "motion": "zoom-in"},
        {"ai": "Middle-aged woman in a dark room surrounded by many glowing phone screens and notifications floating around her face, screens lighting her face from below, overwhelmed and hypnotized, cinematic, dark and moody, photorealistic, high detail",
         "q": "screens face dark",
         "text": "El mundo y sus distracciones no quieren que hagas esa cuenta. Porque el que sabe cuánto le queda, deja de gastar el tiempo en lo que no vale. Y eso no le conviene a nadie más que a ti.",
         "motion": "pan-right"},
        {"ai": "Ancient marble bust of a stoic philosopher on a wooden table with a single lit candle, dramatic chiaroscuro shadows, dust in the warm light beam, solemn and timeless, dark and moody, cinematic, photorealistic, high detail",
         "q": "marble bust candle",
         "text": "Los sabios de la fe la hacían todos los días: recordar la propia finitud no es por miedo, sino para ordenar el alma. El que recuerda que el tiempo en la tierra termina, deja de posponer lo importante.",
         "motion": "zoom-out"},
        # --- Acto 2: las cargas ---
        {"ai": "Silhouette of a woman carrying a huge stack of heavy stones on her back, dark cave background, single beam of dramatic light from above, symbolic burden, dark and moody, cinematic, photorealistic, high detail",
         "q": "silhouette stones burden",
         "text": "Piensa en tu lista: no solo en las heridas que otros te causaron, sino en los afectos desordenados, el egoísmo y las faltas de amor. También en esos juicios severos contra quienes fallaron, o contra ti misma. Cada falta de caridad es un ladrillo que pusiste en tu mochila.",
         "motion": "pan-left"},
        {"ai": "Rusty iron chains and padlocks hanging on an old wooden door, dim greenish light, dust in the air, abandoned and oppressive, dark and moody, dramatic lighting, photorealistic, high detail",
         "q": "chains locks door",
         "text": "El rencor y la falta de conversión son los costos más altos que pagas: te quitan la alegría del presente por aferrarte a lo que ya pasó. El orgullo nos hace guardar la deuda en la memoria, cobrándola todos los días en tu cabeza.",
         "motion": "zoom-in"},
        {"ai": "Open hands releasing a dim heavy weight of shadows over a faint warm glow, letting go of resentment, symbolic, dark and moody, cinematic, photorealistic, high detail",
         "q": "hands letting go shadows",
         "text": "El perdón no es un cálculo humano ni una técnica para estar tranquilos: es un acto de amor que imita al maestro. No perdonas porque el otro tenga méritos, sino porque tú misma fuiste perdonada primero por Dios en la cruz. Perdonar es devolver el alma a la fuente de la gracia.",
         "motion": "zoom-out"},
        {"ai": "Elderly hands gently pouring tea into a cup for someone else, dignified act of serving, warm candlelight, dark background, respectful and loving gesture, cinematic, photorealistic, high detail",
         "q": "hands pouring tea serving",
         "text": "Y aquí está la parte que casi nadie se atreve a decir: servir no es rebajarse. Es todo lo contrario: servir con amor es para lo que fuiste creado, porque el mismo Cristo vino a servir. Las verdaderas ataduras no están en la entrega. Las ataduras son el egoísmo, el orgullo y la soberbia de no querer perdonar.",
         "motion": "zoom-out"},
        # --- Acto 3: el desvío del alma ---
        {"ai": "Chained prisoners sitting in a row facing a dark cave wall, flickering torchlight casting their shadows, dramatic chiaroscuro, allegory of the cave, dark and moody, cinematic, photorealistic, high detail",
         "q": "prisoners cave wall",
         "text": "Piensa: ¿por qué sigues viviendo atada a lo que te daña? Atada a los odios, a los rencores, a las mentiras que te contaron, y que tú misma repetiste hasta creértelas.",
         "motion": "zoom-in"},
        {"ai": "Elderly woman sitting at a dining table while three people ignore her looking at their phones, cold dim light, she looks down, lonely and invisible, cinematic, dark and moody, photorealistic, high detail",
         "q": "elderly woman ignored dinner",
         "text": "Pendiente de la opinión ajena. Presa del qué dirán. Mendigando atención de personas que no te quieren escuchar, que no te tienen en cuenta, que hace años que no te miran a los ojos. Y ese es un peso que tú misma alimentas todos los días.",
         "motion": "pan-right"},
        {"ai": "Close-up of two hands bound tightly with rough rope, dark background, single dramatic beam of light on the ropes, symbolic imprisonment, dark and moody, cinematic, photorealistic, high detail",
         "q": "hands tied rope",
         "text": "Vivir así nos hace olvidar nuestra dignidad de hijos de Dios, y por eso duele: porque nos acostumbramos a lo que no nos corresponde. Decimos así es la vida, así soy yo. No, no es la vida. Es un desvío que permitiste y que nadie te enseñó a ver.",
         "motion": "zoom-in"},
        {"ai": "Person looking at many mirror reflections of themselves, identity blurred, opinions floating like whispers, dim moody light, dark and moody, cinematic, photorealistic, high detail",
         "q": "mirror reflections identity",
         "text": "Y la falsa aprobación, esa es otra trampa disfrazada de cariño. Vivir condicionado por el mundo no es servir: es buscar fuera la palabra de amor y valor que solo Dios ha puesto en tu interior. El que aprueba tu vida desde afuera, no conoce tu alma.",
         "motion": "pan-left"},
        {"ai": "Woman in her sixties sitting alone in a dark room, a single soft beam of light illuminating her thoughtful face, deep honest reflection, quiet and intimate, dark and moody, cinematic, photorealistic, high detail",
         "q": "woman alone thinking light",
         "text": "El primer paso de la conversión y la sabiduría no es tener todas las respuestas. Es hacerte la pregunta con honestidad. Una vez. Sin escapatoria, sin cambiar de tema. Esa pregunta ya cambia todo lo que viene después.",
         "motion": "zoom-out"},
        # --- Acto 4: el salmo 90 ---
        {"ai": "Ancient stone tablets with old carved writing on a wooden table, warm candlelight, dust particles floating in the light beam, reverent and timeless, cinematic, dramatic lighting, photorealistic, high detail",
         "q": "ancient stone tablets",
         "text": "Hace miles de años, el salmo noventa lo dijo, y no se ha quedado viejo: enséñanos a calcular nuestros años, para que nuestro corazón alcance la sabiduría.",
         "motion": "zoom-in"},
        {"ai": "Ancient parchment scroll with old hebrew letters on a wooden table, warm candlelight, dust in the light beam, reverent and timeless, cinematic, dramatic lighting, photorealistic, high detail",
         "q": "ancient scroll candle",
         "text": "La sabiduría del salmo es de las pocas cuentas que no envejecen: en tres mil años no se quedó vieja. Porque no habla de una época: habla de la condición humana. Y esa no cambia, se repite.",
         "motion": "pan-right"},
        {"ai": "Hourglass with golden sand falling slowly on a wooden table by a window, warm morning light streaming in, dramatic close-up, time passing, cinematic, photorealistic, high detail",
         "q": "hourglass sand window",
         "text": "Fíjate bien qué pide: no pide más años. Pide aprender a valorar los que tiene. La sabiduría no está en vivir más: está en entender el regalo de lo que ya tienes.",
         "motion": "pan-right"},
        {"ai": "Open old leather book on a wooden table, warm golden candle and window light, pages gently lit, dust in the light beam, peaceful wisdom, bright airy warm cream and sage palette, cinematic, photorealistic, high detail",
         "q": "open book candle window",
         "light": True,
         "text": "Calcular los años no es contar con miedo. Es darle a cada día su peso. Es saber que el día de hoy es una gracia que no se repite, y que gastarlo en rencores es desperdiciar el amor de Dios.",
         "motion": "zoom-out"},
        {"ai": "Woman in her sixties writing numbers in a journal at a wooden desk by a bright window, soft diffused morning light, warm cream and sage tones, calm and deliberate, bright airy, cinematic, photorealistic, high detail",
         "q": "woman writing journal morning",
         "light": True,
         "text": "Eso es la sabiduría del salmo: no es filosofía de libros. Es una cuenta que se hace con la vida. Y la vida, cuando aprendes a recibirla como un don, deja de gastarse sola.",
         "motion": "zoom-in"},
        # --- Acto 5: la puerta ---
        {"ai": "Massive old wooden door standing alone in a golden wheat field, warm sunset light leaking from the edges of the door, mysterious and sacred, dust in the light beam, cinematic, photorealistic, high detail",
         "q": "old wooden door field light",
         "light": True,
         "text": "Y llegamos a la parte que más cuesta escuchar. Al final del camino, vas a ir al otro lado, a presentarte ante la puerta del que te creó.",
         "motion": "zoom-in"},
        {"ai": "Woman in her sixties standing before a massive old wooden door, her hand raised ready to knock, brilliant warm golden light spilling from the threshold, sacred and solemn moment, cinematic, photorealistic, high detail",
         "q": "woman knocking old door",
         "light": True,
         "text": "No te lo digo para asustarte. Te lo digo porque es la verdad eterna que ordena todo lo demás. Si esa puerta nos espera, entonces nada de lo que cargas hoy tiene sentido, salvo una cosa.",
         "motion": "zoom-out"},
        {"ai": "Woman in her sixties with eyes closed, face lifted toward a warm beam of golden light from above, feeling seen and known, serene and reverent, bright airy soft diffused light, cinematic, photorealistic, high detail",
         "q": "woman golden light face",
         "light": True,
         "text": "El que te creó. Piensa eso con calma: tu Creador te conoce. Te conoce desde antes de tu nombre, desde antes de tus heridas, desde antes de todo lo que el mundo te dijo que eras. Él te conoce.",
         "motion": "pan-right"},
        {"ai": "Warm intimate golden light in a quiet room, a woman's face softly lit, being called by name, gentle and personal, bright airy, cinematic, photorealistic, high detail",
         "q": "warm light woman face",
         "light": True,
         "text": "Él te conoce por tu nombre. No por tu título, ni por lo que lograste, ni por lo que aparentas. Por tu nombre, el de siempre. El que se dice con amor puro y misericordia.",
         "motion": "zoom-in"},
        {"ai": "Open ledger with names written carefully with a fountain pen, warm golden light, intimate and solemn, bright airy, cinematic, photorealistic, high detail",
         "q": "ledger names pen light",
         "light": True,
         "text": "Y en esa puerta no vas a presentar tus éxitos materiales: vas a presentar cómo respondiste a su amor. Lo que guardaste, lo que soltaste, a quién serviste. La cuenta de la vida no suma lo que acumulaste: suma lo que amaste por la gracia de Dios.",
         "motion": "pan-left"},
        {"ai": "Woman in her sixties standing at a crossroads at dawn, one path leading toward a distant glowing door of light, the other back into darkness, choosing, golden morning light, cinematic, photorealistic, high detail",
         "q": "crossroads dawn woman",
         "light": True,
         "text": "Él te conoce. ¿Tú lo conoces a Él? Esa es la pregunta. No la que te hace el mundo. La que importa de verdad, delante de esa puerta, una sola vez, y que no admite distracciones.",
         "motion": "zoom-in"},
        # --- Acto 6: método + cierre ---
        {"ai": "Elderly hands writing numbers with a fountain pen on a sheet of paper by warm window light, calculating the years, deliberate and calm, bright airy, warm cream and sage palette, cinematic, photorealistic, high detail",
         "q": "hands writing numbers paper",
         "light": True,
         "text": "Y para que no te quedes solo con la pregunta, aquí está el camino. Primero: haz la cuenta. Pon en manos de Dios los años que te queden. Ponerlo en papel le saca el miedo y te trae al presente.",
         "motion": "zoom-in"},
        {"ai": "Open hands releasing small grey stones into a beam of golden morning light, stones falling slowly, symbolic letting go, warm and hopeful, bright airy, cinematic, photorealistic, high detail",
         "q": "hands releasing stones light",
         "light": True,
         "text": "Segundo: suelta una carga por día. Un rencor, una mentira, el deseo de complacer a quien no te valora. No hace falta soltarlo todo de golpe: hace falta empezar a soltar con oración. La mochila se aligera una cosa a la vez.",
         "motion": "zoom-out"},
        {"ai": "Elderly hands holding an old phone, ready to call someone, warm golden window light, reconciliation and peace, bright airy, cinematic, photorealistic, high detail",
         "q": "hands holding phone light",
         "light": True,
         "text": "Tercero: repara hoy una sola cosa que puedas reparar. Un mensaje, una llamada, un pedido de perdón. Lo que se sana en vida se vuelve tesoro en el cielo. Hoy hay tiempo para eso: úsalo.",
         "motion": "zoom-in"},
        {"ai": "Silhouette of a woman walking slowly toward a warm glowing sunrise on a quiet road, morning mist, hopeful new day, bright airy golden tones, cinematic, photorealistic, high detail",
         "q": "woman walking sunrise road",
         "light": True,
         "text": "Cuarto: hazte la pregunta de la puerta cada mañana: ¿camino hoy con mi Creador? No como un deber pesado. Como quien se prepara con alegría para el encuentro definitivo.",
         "motion": "pan-right"},
        {"ai": "Calendar with many small days and one single day marked with warm golden light, each day a page, hopeful, bright airy, cinematic, photorealistic, high detail",
         "q": "calendar day light",
         "light": True,
         "text": "Y la prueba de que vives despierto no está al final de la vida: está hoy. Cómo trataste a alguien esta tarde, si soltaste una amargura, si miraste hacia lo eterno. La vida se mide en días, y cada día es una página.",
         "motion": "zoom-out"},
        {"ai": "Woman in her sixties standing at an open wooden door, brilliant warm golden sunlight flooding in around her, serene and free, eyes bright, warm and hopeful, bright airy, cinematic, photorealistic, high detail",
         "q": "woman open door sunlight",
         "light": True,
         "text": "Volvemos al principio, para cerrar el círculo: ¿cuántas horas, días, semanas te quedan si viajas al otro lado a los ochenta años? La cuenta no es para asustarte: es para despertarte. " + cta,
         "motion": "zoom-in"},
    ]
    return s


LIGHT = {i for i, sc in enumerate(scenes_muerte(""), start=1) if sc.get("light")}