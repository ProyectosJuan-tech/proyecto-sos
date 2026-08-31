#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hacer_video_caverna as m

STYLE = ", cinematic, dark and moody, dramatic lighting, photorealistic, high detail"
LIGHT_STYLE = ", bright airy, high-key soft diffused window light, warm cream and sage palette, gentle highlights, no hard shadows, crisp and colorful, warm and hopeful, photorealistic, high detail"

# Escenas que usan imagen clara (esperanza/método) en vez de la oscura
# (caverna/muerte/adicción). El resto del video queda oscuro.
LIGHT_SCENES = {
    "inmediatez": {12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                   27, 28, 30},
    "libertad": {19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30},
    "darse-cuenta": {14, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31},
    "muerte": set(__import__("muerte_scenes").LIGHT),
    "no-permanezcas-atrapado": {5, 7, 9, 10, 11},
}
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(PROJECT_ROOT, "videos")

_DESPERTAR_DRAW = [
    "chalkboard", "chalkboard", "whiteboard", "chalkboard", "chalkboard",
    "chalkboard", "chalkboard", "sharpie", "sharpie", "whiteboard",
    "chalkboard", "chalkboard", "editorial", "editorial", "chalkboard",
    "sharpie", "whiteboard", "editorial", "editorial", "editorial",
    "editorial", "whiteboard", "whiteboard", "sharpie", "whiteboard",
    "technical", "technical", "technical", "technical", "technical",
    "technical", "whiteboard", "editorial", "whiteboard", "editorial",
    "whiteboard",
]

VIDEOS = [
    {
        "name": "cadenas",
        "scenes": [
            {"ai": "Chained prisoners in a dark cave facing a wall, torchlight, dramatic shadows",
             "q": "allegory of the cave",
             "text": "Tus cadenas no son de hierro."},
            {"ai": "Person's face lit only by a smartphone glow in the dark, alone",
             "q": "person smartphone night",
             "text": "Son notificaciones."},
            {"ai": "Person scrolling a phone at night, city lights bokeh, isolation",
             "q": "city lights night",
             "text": "Miles de veces al día, algo te arranca de tu vida real."},
            {"ai": "Silhouettes cast on a cave wall by firelight",
             "q": "silhouette cave",
             "text": "Y lo llamas estar informado."},
            {"ai": "A dark cave wall with projected shadows, faint light",
             "q": "dark cave",
             "text": "Eso no es información: es la pared de la caverna. Sígueme para salir."},
        ],
    },
    {
        "name": "ley-atraccion",
        "scenes": [
            {"ai": "Smartphone with motivational quotes glowing in the dark",
             "q": "smartphone hand screen",
             "text": "La ley de atracción te dijo que pensaras bonito para atraer dinero. ¿Conoces a un solo millonario que se hizo pensando?"},
            {"ai": "Ancient marble bust of Aristotle, dramatic lighting",
             "q": "Aristotle bust",
             "text": "Hace dos mil trescientos años, Aristóteles lo explicó: para que algo exista hacen falta las cuatro causas. Materia, y un agente que actúe."},
            {"ai": "Industrial gears and machinery, cause and effect, dark cinematic",
             "q": "gears machinery",
             "text": "El pensamiento no es materia ni acción. Es un deseo sin vehículo."},
            {"ai": "Split scene: a person meditating in the dark versus a person working with tools, contrast",
             "q": "meditation silhouette",
             "text": "Por eso la autoayuda moderna te deja igual: te hace sentir culpable por vibrar mal, cuando el problema nunca fue tu vibración."},
            {"ai": "A person walking the same path every day at sunrise, repetition, ritual",
             "q": "sunrise path",
             "text": "Aristóteles decía otra cosa: la virtud no se despierta, se practica. Somos lo que hacemos repetidamente. La excelencia no es un acto: es un hábito."},
            {"ai": "A hand planting a small seed in the ground, hopeful light",
             "q": "hands soil planting",
             "text": "Deja de pedirle al universo. El universo no escucha. Pero tú sí puedes actuar."},
            {"ai": "A road toward bright light at sunrise, walking silhouette",
             "q": "road horizon sunrise",
             "text": "Empieza hoy con una acción pequeña. En un año, esa constancia hará lo que ninguna afirmación pudo. El universo no recompensa tu vibración. Recompensa tu constancia."},
        ],
    },
    {
        "name": "despertar",
        "bgm": True,
        "scenes": [
            {"ai": "Woman sleeping peacefully in bed, soft morning light through curtains, warm tones",
             "q": "woman sleeping morning",
             "text": "Hay personas que viven toda su vida dormidas. No en la cama: dormidas de mente. Despiertas de cuerpo, dormidas en la manera de ver las cosas.",
             "motion": "zoom-in"},
            {"ai": "Ancient Roman marble bust of Saint Paul, warm candlelight, dramatic shadows",
             "q": "roman statue bust",
             "text": "Hace dos mil años, un hombre escribió una de las frases más filosóficas que existen: cambien su manera de pensar. No hablaba de religión: hablaba del despertar.",
             "motion": "pan-right"},
            {"ai": "Woman standing at a large window at sunrise, light flooding in, silhouette, contemplative",
             "q": "sunrise window silhouette",
             "text": "El despertar no es un truco ni un evento mágico. Es un momento de la vida en el que te volvés receptiva. Y cuando llega, no es para ignorarlo.",
             "motion": "zoom-out"},
            {"ai": "Arthur Schopenhauer portrait, dark moody oil painting style, candlelit",
             "q": "schopenhauer portrait",
             "text": "Schopenhauer decía que el mundo no es como es: es como te lo muestran. Todo lo que ves pasa por un filtro. Y ese filtro no lo elegiste vos.",
             "motion": "pan-left"},
            {"ai": "Busy city crowd walking fast, motion blur, neon lights, urban rush",
             "q": "city crowd walking",
             "text": "La voluntad de vivir nos mantiene en movimiento: deseando, comprando, mirando. Entre el deseo y el aburrimiento, no queda tiempo para preguntarse por qué.",
             "motion": "zoom-in"},
            {"ai": "Person scrolling smartphone in dark room, face lit only by screen glow, isolated",
             "q": "person smartphone dark",
             "text": "El sistema no necesita encadenarte: le alcanza con entretenerte. Te da pantallas, te da urgencias, te da metas prestadas. Y mientras tanto, no mirás.",
             "motion": "pan-right"},
            {"ai": "Ancient cave wall with flickering fire shadows of chained figures, dramatic chiaroscuro",
             "q": "cave shadows fire",
             "text": "Platón lo contó hace dos mil años: hombres mirando sombras en una pared, creyendo que esa era toda la realidad. La caverna no se fue. Solo cambió de forma.",
             "motion": "zoom-out"},
            {"ai": "Crowd of people walking in same direction, identical clothes, urban conformity",
             "q": "crowd same direction",
             "text": "Nos enseñaron que el éxito es imitar a otros. Que la vida buena es la que se parece a la de los demás. Y así, copiando sueños ajenos, se nos va la nuestra.",
             "motion": "pan-left"},
            {"ai": "Shopping mall consumerism, people with bags, bright lights, artificial happiness",
             "q": "shopping mall consumer",
             "text": "La ciencia moderna lo confirma: la psicología llama a esto gestión del terror. Cuando la mente no quiere mirar lo que duele, se distrae con consumo y estatus.",
             "motion": "zoom-in"},
            {"ai": "Woman sitting alone thoughtful by a window, warm afternoon light, peaceful contemplation",
             "q": "woman window thoughtful",
             "text": "Y no es tu culpa. Nadie te enseñó a despertar: te enseñaron a mirar la pared. Reconocerlo no es amargarse: es el primer paso para dar la vuelta.",
             "motion": "pan-right"},
            {"ai": "Hourglass with sand falling, golden light, dramatic close-up, time running",
             "q": "hourglass sand",
             "text": "Hay una verdad que no se dice en las pantallas: vas a morir. Suena duro, pero es justamente esa verdad la que puede despertarte.",
             "motion": "zoom-in"},
            {"ai": "Roman philosopher Seneca marble statue, museum lighting, stoic dignity",
             "q": "seneca statue",
             "text": "Séneca la practicaba todos los días. Los estoicos miraban la muerte de frente, no por miedo, sino para recordar que el tiempo no sobra.",
             "motion": "pan-left"},
            {"ai": "Old leather-bound book pages turning, candlelight, warm library atmosphere",
             "q": "old book pages",
             "text": "Montaigne lo dijo simple: filosofar es aprender a morir. Quien aprende a morir, se desaprende a servir.",
             "motion": "zoom-out"},
            {"ai": "Marble bust of Epicurus in a peaceful garden setting, warm sunlight, classical philosophy",
             "q": "epicurus garden bust",
             "text": "Epicuro fue más lejos: la muerte no es nada para nosotros. Cuando existimos, ella no está. Cuando llega, ya no existimos. No hay que temerle: hay que usarla.",
             "motion": "pan-right"},
            {"ai": "Hourglass almost empty, last grains falling, dramatic lighting, urgency",
             "q": "hourglass empty",
             "text": "El que olvida que va a morir, cree que tiene tiempo infinito. Y por eso pospone lo importante y se hipnotiza con lo urgente.",
             "motion": "zoom-in"},
            {"ai": "Businessman running on treadmill in empty office, status chasing, golden city view",
             "q": "businessman treadmill city",
             "text": "Los que parecen haber triunfado tampoco miran. Corren detrás de lo mismo: más, nunca alcanza. No los copies: son otro sueño, más ruidoso.",
             "motion": "pan-left"},
            {"ai": "Woman face close-up with eyes open, warm dawn light, awake, alive, present",
             "q": "woman face dawn awake",
             "text": "Acordarte de que la vida es finita no te hace triste: te hace despierta. Es el recuerdo que le saca el polvo a lo importante.",
             "motion": "zoom-out"},
            {"ai": "Warm cup of tea on wooden table, morning light streaming, steam rising, cozy simple moment",
             "q": "tea morning light",
             "text": "Quien recuerda que la vida es corta, empieza a ver lo que antes ignoraba: un mate caliente, la luz de la tarde, una conversación sin apuro.",
             "motion": "pan-right"},
            {"ai": "Japanese tea ceremony, serene hands pouring tea, zen simplicity, warm tones",
             "q": "tea ceremony japanese",
             "text": "Los japoneses tienen una palabra para esto: ichigo ichie. Este encuentro, este momento, una sola vez en la vida. No vuelve.",
             "motion": "zoom-in"},
            {"ai": "Cherry blossom petals falling in slow motion, soft pink light, mono no aware beauty",
             "q": "cherry blossom petals",
             "text": "Otra palabra: mono no aware. La belleza de lo que pasa. Lo que es hermoso precisamente porque no dura.",
             "motion": "pan-down"},
            {"ai": "Small wildflowers in a field at golden hour, close-up, warm light, simple beauty",
             "q": "wildflowers field golden",
             "text": "La felicidad no está en el logro futuro que te venden: está en lo que ya tenés y todavía no mirás. No hace falta conseguir nada: hace falta mirar.",
             "motion": "pan-left"},
            {"ai": "River flowing over smooth stones, clear water, natural light, Heraclitus flux",
             "q": "river stones flowing",
             "text": "Heráclito lo dijo hace dos mil quinientos años: todo fluye. No te bañás dos veces en el mismo río. Tampoco vas a vivir dos veces este momento.",
             "motion": "zoom-out"},
            {"ai": "Woman walking alone on a path at sunrise, present moment, mindful steps, warm light",
             "q": "woman path sunrise",
             "text": "No hace falta irse al Himalaya para despertar. Hace falta estar donde estás, de verdad. Esa es la práctica más difícil del mundo.",
             "motion": "pan-right"},
            {"ai": "Woman looking at herself in mirror, tired from pretending, moment of honesty",
             "q": "mirror woman tired",
             "text": "Mientras tanto, el mundo te pide aparentar. Aparentar cansa. Mirar, no cansa: mirar alimenta.",
             "motion": "zoom-in"},
            {"ai": "Sunrise new day, door opening to light, new beginning, hopeful",
             "q": "sunrise door light",
             "text": "El despertar no es un click que te pasa una vez. Es un verbo: se conjuga todos los días. Cada mañana volvés a elegir con qué ojos mirás.",
             "motion": "zoom-out"},
            {"ai": "Person sitting in silence, eyes closed, calm breathing, peaceful morning room",
             "q": "person silence breathing",
             "text": "Primero: un momento de silencio al día. La respiración te trae al ahora. No necesitás nada: solo aire y atención.",
             "motion": "pan-left"},
            {"ai": "Hourglass with sunrise in background, memento mori, compass, daily practice",
             "q": "hourglass sunrise compass",
             "text": "Segundo: un recordatorio diario de que la vida es finita. No como miedo: como brújula. ¿Estoy haciendo lo que importa, o lo que me impusieron?",
             "motion": "zoom-in"},
            {"ai": "Hands holding a warm cup of tea, close-up, mindful moment, small daily ritual",
             "q": "hands holding tea close",
             "text": "Tercero: elegí una cosa pequeña al día y estás plenamente ahí. El té, el paseo, la planta. Una sola cosa, de verdad.",
             "motion": "pan-right"},
            {"ai": "Clock with question mark, pause moment, contemplative doubt, warm light",
             "q": "clock question mark",
             "text": "Cuarto: cuando algo te urja, preguntate: ¿esto es mío o me lo prestaron? La mitad de tus urgencias son ajenas.",
             "motion": "zoom-out"},
            {"ai": "Aristotle marble bust, Greek philosophy, dramatic museum lighting",
             "q": "aristotle bust marble",
             "text": "Aristóteles lo sabía: no se es despierto una vez y listo. Se practica. Somos lo que hacemos repetidamente. El despertar es un hábito, no un destino.",
             "motion": "pan-left"},
            {"ai": "Brain neurons glowing, meditation silhouette overlay, science meets mindfulness",
             "q": "brain neurons meditation",
             "text": "Y la ciencia acompaña: entrenar la atención cambia el cerebro. No es esoterismo: es método medido. La calma también se entrena, como un músculo.",
             "motion": "zoom-in"},
            {"ai": "Woman hand reaching toward warm light, hope, new path, gentle courage",
             "q": "hand reaching light",
             "text": "Si antes creíste en la autoayuda, no fue ingenuidad: fue hambre. Hambre de algo real. Ahora tenés un método con base.",
             "motion": "pan-right"},
            {"ai": "Ancient manuscript scroll with candle, wisdom tradition, warm library",
             "q": "ancient manuscript candle",
             "text": "Volvemos al principio: cambien su manera de pensar. No es una orden. Es una invitación a soltar el sueño y dar la vuelta.",
             "motion": "zoom-out"},
            {"ai": "Silhouette walking out of cave into bright light, exit, freedom, new dawn",
             "q": "cave exit light silhouette",
             "text": "La caverna no se cierra para siempre: se sale. Y se vuelve a salir. Todos los días. Eso no es fracaso: es práctica.",
             "motion": "pan-left"},
            {"ai": "Woman eyes wide open at sunrise, alive, present, warm golden light on face",
             "q": "woman eyes open sunrise",
             "text": "Los ojos abiertos ven lo mismo que antes. Pero lo ven distinto. Y lo distinto se llama vida. La tuya, la de ahora.",
             "motion": "zoom-in"},
            {"ai": "Path stretching forward into sunrise, walking alone, invitation, warm hopeful light",
             "q": "path sunrise forward",
             "text": "Si algo de esto te despertó, guardá este video y compartilo con alguien que también esté despertando. Sígueme.",
             "motion": "zoom-out"},
        ],
    },
    {
        "name": "sobrepiensa",
        "bgm": True,
        "voices": ["male"],
        "rate": "-8%",
        "scenes": [
            {"ai": "Person lying in bed at 2AM, phone face down on nightstand, glass of water nearby, slightly messy hair, dark circles under eyes, ceiling view from below, real bedroom with clothes on chair, warm lamp light, intimate observational photograph, Kodak Portra 400",
             "q": "insomnia bed ceiling",
             "motion": "zoom-in",
             "text": "Te acuestas. Cierras los ojos. Y justo cuando pensabas que el día había terminado... tu cabeza empieza de nuevo. ¿Por qué dije eso? ¿Y si mañana sale mal? Tendría que haber contestado otra cosa. Y lo peor es que no estás resolviendo nada. Estás teniendo la misma conversación por quinta vez."},
            {"ai": "Person sitting on a bus or train, staring out window, slightly tired, normal clothes, real public transport interior, other passengers blurred in background, afternoon light through window, documentary style photograph, natural imperfections, Fujifilm Pro 400H",
             "q": "person bus window thinking",
             "motion": "pan-right",
             "text": "Ahí aparece una red de tu cerebro llamada red neuronal por defecto. Está relacionada con recordar, imaginar, pensar en el futuro y pensar sobre ti mismo. Y eso explica algo bastante extraño: cuando por fin dejas de hacer cosas, tu cabeza puede empezar a hacer mucho más ruido."},
            {"ai": "Surreal pink elephant floating in a dreamlike void, soft pastel colors, ethereal glow, minimalist background, slightly absurd and whimsical, like a thought materializing, artistic illustration style, clean composition",
             "q": "pink elephant surreal thought",
             "motion": "zoom-in",
             "text": "Ahora haz una prueba conmigo. No pienses en un elefante rosa. No lo imagines. No pienses en su trompa. No pienses en el color. ¿Apareció? Ahí está. Es una versión del famoso efecto oso blanco: cuando intentamos controlar activamente un pensamiento, podemos terminar manteniéndolo presente."},
            {"ai": "Chaos of tangled thought bubbles and question marks surrounding a person's silhouette, gradually dissolving and fading, dark background transitioning to soft light, visual metaphor for thoughts losing power, cinematic atmosphere, observational photograph style",
             "q": "thoughts dissolving mind",
             "motion": "zoom-out",
             "text": "¿Y si el problema no fuera pensar? ¿Y si fuera pelearte con cada pensamiento que aparece? Porque hay algo interesante que ocurre cuando dejamos de intentar controlar el contenido de nuestra mente. Los investigadores lo llaman mind blanking: momentos en los que una persona reporta no tener un contenido mental identificable."},
            {"ai": "Extreme close-up of a person's face with eyes gently closed, peaceful expression, soft warm light on skin, slight imperfections visible, intimate portrait, shallow depth of field, quiet contemplative moment, Kodak Portra 400",
             "q": "close up eyes closed peaceful",
             "motion": "zoom-in",
             "rate": "-15%",
             "pause_after": 5.0,
             "text": "Cierra los ojos. Y pregúntate: ¿Cuál va a ser mi próximo pensamiento?\nNo respondas. No busques una respuesta. Espera. Hazlo conmigo. ¿Cuál va a ser mi próximo pensamiento?"},
            {"ai": "Train window view, landscape passing by in motion blur, person's reflection faintly visible in glass, warm afternoon light, documentary style, world moving while observer stays still, contemplative travel photograph, Fujifilm Pro 400H",
             "q": "train window passing landscape",
             "motion": "pan-left",
             "text": "Es como dejar de perseguir una conversación que está ocurriendo dentro de tu cabeza. No necesitas ganar. No necesitas terminarla. Puedes simplemente dejarla pasar."},
            {"ai": "Simple glass of water on a wooden table, morning light, real kitchen setting, no styling, mundane everyday object, quiet domestic moment, observational still life, natural light photograph",
             "q": "glass of water morning light kitchen",
             "motion": "zoom-out",
             "text": "Y no hace falta que medites durante una hora. Esto puede durar apenas unos segundos."},
            {"ai": "Person walking alone on a city sidewalk after a difficult day, slightly slouched posture, normal clothes, evening light, urban environment, real street with everyday details, no posing, documentary street photography style, natural imperfections, Kodak Portra 400",
             "q": "person walking city evening tired",
             "motion": "pan-right",
             "text": "La próxima vez que estés repasando algo que dijiste hace tres horas... o imaginando una discusión que todavía ni ocurrió... freno. Y pregúntate: ¿Cuál será mi próximo pensamiento?"},
            {"ai": "Black screen with white text centered: ALGUNOS PENSAMIENTOS SOLO NECESITAN PASAR. Minimal, powerful, typographic design, clean sans-serif font, centered composition, high contrast",
             "q": "minimal typography quote",
             "motion": "none",
             "text": "Quizás tu problema no es que pensás demasiado. Quizás llevás demasiado tiempo tratando de resolver cada pensamiento que aparece. Y no todos necesitan una respuesta. Algunos solamente necesitan pasar."},
            {"ai": "Person lying in bed at night, same room as opening scene, eyes slowly closing, peaceful expression replacing earlier worry, phone face down, warm dim light, real bedroom, intimate observational photograph, Kodak Portra 400",
             "q": "person bed closing eyes night peaceful",
             "motion": "zoom-in",
             "text": "Así que la próxima vez que estés acostado... mirando el techo... y tu cabeza vuelva a empezar... no pelees con ella. Pregúntale: ¿Cuál será mi próximo pensamiento? Y por un momento... deja de perseguirlo. Tu cabeza no siempre necesita una respuesta. Guárdalo. Alguna noche vas a volver."},
        ],
    },
    {
        "name": "integrar",
        "bgm": True,
        "voices": ["male"],
        "rate": "-8%",
        "scenes": [
            {"ai": "Woman sitting on the floor surrounded by broken pottery, looking at a faded old map in her hands, warm light, contemplative, observational photograph, Kodak Portra 400",
             "q": "woman old map broken pottery",
             "motion": "zoom-in",
             "text": "El problema no es que estés rota. El problema es que sigues usando un mapa viejo para navegar un territorio nuevo."},
            {"ai": "Close-up of hands tracing the cracks of a repaired clay bowl kintsugi style, golden light highlighting the repairs, shallow depth of field, intimate photograph, Kodak Portra 400",
             "q": "kintsugi bowl hands golden light",
             "motion": "pan-left",
             "text": "Lo que viviste ya pasó. No puedes cambiarlo, ni deberías intentar borrarlo. Lo que sí quedó grabado fue la estrategia de supervivencia."},
            {"ai": "Woman writing in a notebook at a wooden table, sunlight hitting the paper, calm focus, real desk with everyday objects, documentary style photograph, natural imperfections, Fujifilm Pro 400H",
             "q": "woman notebook wooden table sunlight",
             "motion": "zoom-out",
             "text": "En ese momento, tu cerebro aprendió: 'Si hago esto, sobrevivo'. Ese aprendizaje fue brillante. Te protegió."},
            {"ai": "Two old mechanical clocks on a shelf, one ticking loudly, dust particles dancing in the light beam, warm afternoon light, still life photograph, Kodak Portra 400",
             "q": "old mechanical clocks dust light",
             "motion": "pan-right",
             "text": "Pero ese aprendizaje se convirtió en un mecanismo automático. Como un reloj que sigue marcando una hora que ya no existe."},
            {"ai": "Close-up of woman's hand tightening around a folded paper, subtle tension, shallow depth of field, warm indoor light, intimate observational photograph, Kodak Portra 400",
             "q": "hand tightening folded paper tension",
             "motion": "zoom-in",
             "text": "Hoy pasa algo pequeño. Un tono de voz, un silencio. Y el mecanismo se dispara. Sin avisar. Sin pedir permiso."},
            {"ai": "Woman standing in a doorway, looking back with uncertainty, half in shadow half in light, real interior, documentary style photograph, natural imperfections, Kodak Portra 400",
             "q": "woman doorway shadow light uncertainty",
             "motion": "pan-left",
             "text": "Y ahí viene la trampa: piensas '¿Por qué reaccioné así? ¿Qué tiene de malo?'. No tiene nada de malo. Tiene todo de antiguo."},
            {"ai": "Close-up of hand resting on a wooden table, fingers slowly uncurling and relaxing, warm light, intimate observational photograph, shallow depth of field, Kodak Portra 400",
             "q": "hand relaxing wooden table warm light",
             "motion": "zoom-out",
             "text": "Reaccionar automáticamente no es quién eres. Es tu historia hablando por ti. Y tu historia merece ser escuchada, no obedecida ciegamente."},
            {"ai": "Woman walking slowly toward an open window, curtains moving gently, golden hour light filling the room, real interior, documentary style photograph, observational, Kodak Portra 400",
             "q": "woman window golden hour curtains",
             "motion": "zoom-out",
             "text": "Cuando reconoces el mecanismo, aparece un espacio. Un pequeño instante entre el estímulo y tu respuesta. Ahí vive tu libertad."},
            {"ai": "Woman sitting by a large window, writing calmly, peaceful expression, warm late afternoon sunlight, real room, documentary style photograph, observational, Kodak Portra 400",
             "q": "woman window writing peaceful sunlight",
             "motion": "static",
             "text": "Integrar no es conseguir que el pasado deje de existir. Es conseguir que deje de ser el único lugar desde el que respondes. Lo que aprendiste te explica. Pero ya no tiene que decidir por ti."},
        ],
    },
]

VIDEOS.append({
    "name": "inmediatez",
    "bgm": True,
    "voices": ["male"],
    "scenes": [
        {"ai": "Chained prisoners in a dark cave facing a wall, torchlight, dramatic shadows",
         "q": "allegory of the cave",
         "text": "La caverna de Platón no quedó en los libros de filosofía. Se te mudó a la mano. Fijate: cada vez que el teléfono vibra, levantás la vista al toque, sin pensarlo. Un sonido, una luz, una alerta. Y así vivís, atrapado en el segundo que viene y se va. El instante no te deja mirar más allá."},
        {"ai": "Dark cave wall with flickering fire casting shadow figures, prisoners silhouettes",
         "q": "cave shadows fire",
         "text": "Platón hablaba de gente atada de nacimiento frente a un muro. A sus espaldas, un fuego dibujaba sombras, y ellos juraban que eso era el mundo real. Ese fuego, hoy, se llama inmediatez. Todo llega al instante, todo caduca al instante, todo se reemplaza en horas. Y la mirada sigue fija en el muro, sin preguntarse qué hay detrás."},
        {"ai": "Hands holding smartphone in the dark, face lit only by screen glow, lonely",
         "q": "smartphone night",
         "text": "El algoritmo no tiene que convencerte de ninguna idea. Con que te quedes en el ahora, le alcanza. Cada aviso está hecho para sacarte del momento que estás viviendo. Tu vida, la de verdad, transcurre al lado mientras tu cabeza está en otro lado. Y no es debilidad tuya: es mirar sombras sin saberlo."},
        {"ai": "Person overwhelmed by glowing notifications in dark room, digital prison",
         "q": "notifications phone dark",
         "text": "Y no es tu culpa. Nadie te explicó qué estaba pasando. El sistema construyó una máquina perfecta para que no pienses, porque pensar requiere tres cosas: tiempo, silencio y distancia. Y el instante no te deja ninguna de las tres. Solo te da urgencias, metas prestadas y una pared que brilla."},
        {"ai": "Hourglass with sand falling in dim light, dramatic close-up, time running",
         "q": "hourglass sand",
         "text": "Pero hay una pregunta que la inmediatez nunca te deja hacer: cuánto me queda. Porque vivir solo en el instante tiene un precio que no se ve a simple vista. El que vive solo en el ahora, se olvida de que va a morir. Y el que se olvida de su propia muerte, termina dejando de vivir su propia vida."},
        {"ai": "Person drowning in urgent tasks and papers, dark office, anxious, clock on wall",
         "q": "desk work stress",
         "text": "Suena duro, pero miralo con honestidad: tu día entero está lleno de cosas urgentes. Mails, mensajes, pedidos, pendientes. Y te pregunto sin vueltas: ¿cuántas de esas cosas van a importar dentro de un año? Casi ninguna. Y sin embargo el tiempo que gastás apagando incendios ajenos, ese tiempo no vuelve nunca."},
        {"ai": "Clock melting over a smartphone, surreal, time slipping away, dark tones",
         "q": "clock time",
         "text": "El sistema no te roba dinero. Te roba algo mucho más caro: la conciencia de que tu tiempo termina. Mientras pensás que hay años por delante, posponés lo importante para después. Y ese después nunca llega, porque todos los días vuelve a llenarse de lo urgente que otros te dejan."},
        {"ai": "Compass and hourglass on old wooden table, candlelight, memento mori",
         "q": "compass hourglass",
         "text": "Y acá está el punto: nadie te va a avisar cuándo te llega el turno. Por eso la muerte hay que mirarla uno mismo, no desde el miedo, sino como una brújula. El que recuerda que va a morir, deja de pedir permiso para vivir. Deja de guardar la vida para un día que no sabe si llega."},
        {"ai": "Silhouettes cast on cave wall by firelight, Plato allegory, dramatic",
         "q": "silhouette cave",
         "text": "Schopenhauer lo entendió antes que el algoritmo. Decía que el mundo no es como es, sino como lo mostramos: todo lo que vemos pasa por un filtro. Y su filtro, decía, es el deseo. Deseamos, y el deseo nunca se sacia. Siempre quiere más, siempre mira lo que falta, siempre te empuja hacia la pared."},
        {"ai": "Endless conveyor belt of products and glowing desires in the dark, consumer vortex",
         "q": "shopping consumer",
         "text": "La voluntad, decía Schopenhauer, nos mantiene en movimiento eterno: deseando, comprando, mirando, comparando. Entre el deseo y el aburrimiento, la mente no encuentra un solo momento de silencio para preguntarse por qué hace todo eso. Y esa es exactamente la pared de la caverna moderna: actividad constante, sentido cero."},
        {"ai": "Person reaching toward a glowing screen with longing, dark cave metaphor",
         "q": "person smartphone dark",
         "text": "El sistema usa esa voluntad a su favor. Te muestra lo que te falta, te muestra lo que otros tienen, te muestra la vida que deberías tener. Y tu deseo se enciende solo, como un reflejo. Ese es el fuego detrás de la pared. Y mientras deseás, no mirás: solo proyectás."},
        {"ai": "Man sitting calmly by a flowing river at dusk, watching, peaceful",
         "q": "river calm",
         "text": "Pero Schopenhauer también decía que hay una puerta de salida. No se trata de matar los deseos, eso es imposible. Se trata de aprender a verlos como se mira un río desde la orilla: los ves pasar, no te ahogás en ellos. No negarlos, solo verlos. Y ese simple acto de mirar, ya es salir de la caverna."},
        {"ai": "Ancient scroll with text, candlelight, wisdom tradition, warm library",
         "q": "ancient manuscript candle",
         "text": "Hace dos mil años, San Pablo escribió una de las frases más filosóficas que existen: cambien su manera de pensar. Y no hablaba solo de religión. Hablaba de algo más profundo: la mente se entrena, se transforma, igual que se entrena un cuerpo. No se nace con una forma de ver el mundo para siempre."},
        {"ai": "Hands turning a compass toward sunrise, choice, new direction, warm light",
         "q": "sunrise compass",
         "text": "Cambiar la manera de pensar no es leer un libro y listo, como quien cambia de zapatos. Es una práctica diaria, un entrenamiento que se sostiene. Cada día elegís a qué le das tu atención, y con eso, sin que lo notes, elegís de qué está hecha tu vida."},
        {"ai": "Half open door with light spilling through, dark room, decision",
         "q": "door light dark",
         "text": "El instinto te arrastra hacia el ahora: rápido, cómodo, sin esfuerzo. La inmediatez es fácil porque no exige decisiones. Cambiar la manera de pensar exige lo contrario: parar, mirar, elegir. Por eso el sistema no quiere que pienses. Para él, una persona que piensa es un peligro: es alguien que puede salir."},
        {"ai": "Empty chair by a window at golden hour, silence, no phone in sight",
         "q": "window golden hour chair",
         "text": "Y la buena noticia es que no hace falta ser un santo ni un filósofo para empezar. Hace falta un método: un momento del día, aunque sea breve, donde el teléfono no entre. Cinco minutos de silencio, sin sonidos, sin pantallas. Ahí, en ese vacío, tu manera de pensar empieza a cambiar sola."},
        {"ai": "Marble bust in museum lighting, stoic dignity, memento mori",
         "q": "roman statue bust",
         "text": "El recordatorio de la muerte no es morboso, no es algo para huir. Los estoicos lo practicaban todos los días, no por miedo, sino para ordenar lo que importa. Quien recuerda que va a morir, deja de perder tiempo en discusiones que no llevan a nada. Se vuelve urgente solo con lo verdadero."},
        {"ai": "Woman opening eyes at dawn, window light on face, awakening, present",
         "q": "woman dawn face",
         "text": "Probalo hoy mismo: cuando te levantes, antes de agarrar el teléfono, preguntate: si este fuera mi último día, ¿qué haría? Esa pregunta tiene un poder enorme: limpia lo falso, lo prestado, lo innecesario. Y en segundos te muestra con claridad qué es tuyo y qué te fue dado para distraerte."},
        {"ai": "Old man walking toward sunrise on an empty road, mindful steps",
         "q": "sunrise road walking",
         "text": "El que cree que tiene tiempo infinito, pospone. El que recuerda que no lo tiene, elige. La diferencia entre esas dos personas no es la suerte ni la edad. Es un recordatorio que se renueva todos los días: la vida se gasta. Y gastarla a consciencia, es la diferencia entre vivir y sobrevivir."},
        {"ai": "Flower growing in the middle of ruins, warm light, fragile beauty",
         "q": "flower ruins",
         "text": "No te estoy pidiendo que pienses en la muerte todo el día. Eso no es vivir, es esconderse de otra manera. Te pido algo más simple: que la mires una vez, sin miedo, para que te ordene el resto. La muerte no es el final de tu vida. Es el filtro que la vuelve real, que le da peso a cada día."},
        {"ai": "Person sitting in silence, eyes closed, calm breathing, peaceful morning room",
         "q": "person silence breathing",
         "text": "Bajemos el método a tierra, en cuatro pasos que podés empezar hoy. Primero: un minuto de silencio al día, sin pantallas, sin radio, sin nada. Suena a poco, lo sé. Pero es el primer paso para que el instante no siga decidiendo por vos."},
        {"ai": "Hand turning off smartphone notifications, dark room becoming warm, relief",
         "q": "hand phone off",
         "text": "Segundo: desactivá las notificaciones que no son tuyas. Pensalo así: cada aviso es una puerta que alguien abre en tu cabeza. Vos decidís quién entra y quién espera. Esa decisión, que parece técnica, también es una manera de cambiar tu forma de pensar."},
        {"ai": "Calendar pages flying away, time regained, warm light, release",
         "q": "calendar time",
         "text": "Tercero: una vez al día, preguntate si lo que estás haciendo ahora importa dentro de un año. Si la respuesta es no, entonces no tiene por qué comerse tu día entero. Esa pregunta te ahorra horas. Y las horas que te quedan, son tuyas para lo que sí importa."},
        {"ai": "Woman planting a seed at dawn, hands in soil, hopeful light",
         "q": "hands soil planting",
         "text": "Cuarto: hacé una cosa por día para la persona que vas a ser dentro de un año. No para el mundo, no para las redes, no para quedar bien. Para esa versión tuya que va a mirar hacia atrás y va a sentir orgullo o pena. Vos elegís hoy cuál de las dos la espera."},
        {"ai": "Path of small steps ascending out of a cave toward light, exit",
         "q": "cave exit light",
         "text": "El cambio no es mágico y no es de una noche. Es de a pasos, pequeños, a veces invisibles. Cada vez que elegís no mirar, cada vez que apagás el teléfono, cada minuto de silencio, es una vuelta que le das a la caverna. Salir no es un destino: es una dirección que se elige todos los días."},
        {"ai": "Slot machine arm merged with a smartphone, neon, addictive glow, allegory",
         "q": "slot machine neon",
         "text": "Y la ciencia moderna te lo confirma, no es una opinión. Los algoritmos usan el mismo mecanismo que una máquina tragamonedas: recompensa impredecible. A veces algo interesante, a veces no. Y ese patrón, ya está medido, es el que engancha al cerebro y lo mantiene mirando la pared."},
        {"ai": "Brain neurons glowing, meditation silhouette overlay, science meets mindfulness",
         "q": "brain meditation",
         "text": "Pero la misma ciencia que te explica el problema, te da la salida: el cerebro se puede entrenar. La atención es como un músculo: si la usás con intención, se fortalece. Por eso el silencio no es vacío. El silencio es gimnasio. Cada minuto que te quedás ahí, estás entrenando la libertad."},
        {"ai": "Person choosing a book over a phone by warm lamp light, calm",
         "q": "reading lamp book",
         "text": "Pensalo así: cada vez que elegís no mirar, ganás algo invisible, algo que nadie va a aplaudir. Ganás claridad, ganás calma, ganás tiempo de vida real. No se ve en las redes, nadie lo cuenta, pero se siente en el cuerpo y en las decisiones."},
        {"ai": "Hand holding smartphone, wall of shadows covering the person, cave allegory",
         "q": "shadows wall",
         "text": "Volvemos al principio, para cerrar el círculo: la caverna no es un cuento antiguo. Es tu mano sosteniendo el teléfono. La pared es la pantalla. Y las sombras son las urgencias, los miedos y las metas prestadas que te venden cada día. Reconocer eso, ya es el primer paso afuera."},
        {"ai": "Silhouette walking out of cave into bright sunrise, exit, freedom, new dawn",
         "q": "sunrise cave silhouette",
         "text": "Hoy sabés algo que el sistema no quiere que sepas: tu tiempo termina, y precisamente por eso es tuyo. El que recuerda que va a morir, empieza a vivir de verdad. Guardá este video para el día que lo necesites. Y si algo de esto te despertó, dale like, suscribite y contame en comentarios. Compartilo con alguien."},
    ],
})

VIDEOS.append({
    "name": "libertad",
    "bgm": True,
    "voices": ["male"],
    "rate": "-8%",
    "scenes": [
        {"ai": "Open birdcage door with a small bird inside not flying out, morning light, freedom metaphor",
         "q": "open birdcage bird",
         "text": "La libertad no es poder hacer todo lo que quieras. La libertad de verdad es más difícil y más silenciosa: es darte cuenta de que mucho de lo que creés que elegís, no lo elegiste vos. No hablo de política ni de irte a vivir a otra parte. Hablo de algo más profundo: de dónde salen las elecciones que hacés todos los días."},
        {"ai": "Bird in an open cage, golden light, cage door wide open, symbolic",
         "q": "bird cage open",
         "text": "Imaginá una jaula con la puerta abierta y un pájaro que no sale. Así de poderosa es la costumbre: no lo retiene el hierro, lo retiene el olvido de que la puerta está abierta. Y esa jaula la llevamos puesta sin darnos cuenta, repitiendo lo aprendido porque nadie nos enseñó que se puede mirar afuera."},
        {"ai": "Silhouette of a person releasing chains, one chain after another, dawn light",
         "q": "breaking chains silhouette",
         "text": "Lo que llamás yo, en buena parte, es un montón de frases que escuchaste, miedos que aprendiste y metas que no eran tuyas. Soltarlas, una por una, es la libertad. No se sueltan todas juntas, no se sueltan de un tirón. Se aflojan con conciencia, con atención, con método."},
        {"ai": "Child at a school desk learning rules, chalkboard, nostalgic warm classroom",
         "q": "school classroom chalkboard",
         "text": "De chica te enseñaron qué se debe: estudiar, portarte bien, no molestar, querer lo que todos quieren. Eso no es malo, era necesario. El problema aparece cuando repetís esos mandatos sin saber que los repetís. Cuando te creés que los elegiste, cuando ya ni los escuchás, pero te gobiernan."},
        {"ai": "Woman hesitating at a doorway, whispers and shadows of opinions around her, dramatic",
         "q": "woman door shadows",
         "text": "¿Qué van a decir? Cuántas decisiones de tu vida se tomaron para responder esa pregunta. El miedo al qué dirán es una cadena invisible que se arrastra desde la infancia. No la ves, no la tocás, pero sentís su peso cada vez que dejás de hacer lo que querías por miedo a la mirada ajena."},
        {"ai": "Crossroads with three paths, person choosing among them, expectations, symbolic",
         "q": "crossroads path choice",
         "text": "Ejemplo: alguien elige una carrera, un trabajo, hasta una pareja, para cumplir expectativas ajenas. Y no se da cuenta: cree que lo eligió. Esa es la trampa de la caverna. No te imponen la decisión con violencia: te la enseñan como si fuera tuya, y vos la repetís como si lo fuera."},
        {"ai": "Jean-Jacques Rousseau portrait, 18th century philosopher, candlelit library",
         "q": "rousseau portrait",
         "text": "Rousseau lo escribió hace tres siglos: el hombre nace libre y en todas partes está encadenado. Encadenado no por otros: por las ideas que otros le dejaron sin explicarle. Heredamos guiones, mandatos y miedos como se heredan los muebles de una casa: estaban ahí, y nadie nos preguntó si los queríamos."},
        {"ai": "Group of silhouettes all facing the same direction, one person different, conformity",
         "q": "crowd conformity",
         "text": "La comparación es otro eslabón. El científico Asch lo midió: la gente cambia su respuesta solo para no desentonar con el grupo. No es debilidad: es cómo está hecho el cerebro social. Buscamos pertenecer, y a veces pagamos el precio de dejar de ser nosotros para lograrlo."},
        {"ai": "Hands holding heavy invisible chains, a face with a spark of awareness, hopeful light",
         "q": "hands chains light",
         "text": "Y no es tu culpa: nadie nace con la vara puesta, la recibe. Reconocer tus cadenas no te hace más débil. Te hace dueña de decidir cuál soltar primero. Y esa decisión, esa lista que armás vos, ya es el primer acto libre de tu vida."},
        {"ai": "Marble bust of Epictetus, stoic philosopher, dramatic museum lighting",
         "q": "epictetus bust statue",
         "text": "Epicteto fue esclavo y filósofo, y aun así fue de los hombres más libres de su tiempo. Distinguía dos cosas: lo que depende de vos y lo que no. La libertad no está en controlar el mundo: está en dejar de pedirle que sea como vos querés. Empezá por lo que sí está en tus manos: tu juicio, tu elección, tu respuesta."},
        {"ai": "Stoic philosopher statue contemplating, dark library, candlelight, inner calm",
         "q": "stoic statue philosopher",
         "text": "Decía que no nos perturba lo que pasa, sino lo que opinamos de lo que pasa. El estoico no suprime el miedo: lo mira, y al mirarlo le quita el poder de decidir por él. Entre el estímulo y tu respuesta hay un espacio, y en ese espacio está tu libertad."},
        {"ai": "Marble bust of Spinoza, dark contemplative, philosophical depth",
         "q": "spinoza portrait philosopher",
         "text": "Spinoza fue más lejos: llamó libertad a comprender lo que nos mueve. Nadie es libre mientras lo empujan las pasiones. Es libre quien entiende qué lo empuja. La libertad no es no tener cadenas: es verlas. Porque lo que se ve, se puede decidir; lo que no se ve, te maneja."},
        {"ai": "Man in a sparse cell looking up at a small window of light, resilient, hopeful",
         "q": "cell window light man",
         "text": "Frankl, dentro de un campo de concentración, escribió que se le puede arrebatar todo a un hombre excepto la última libertad: elegir su actitud ante lo que no puede cambiar. Esa libertad ni la vida misma te la puede quitar. Y si él pudo adentro de un infierno, vos también podés en tu día a día."},
        {"ai": "Jean-Paul Sartre portrait, existentialist writer, moody lighting, 20th century",
         "q": "sartre portrait philosopher",
         "text": "Sartre dijo que estamos condenados a ser libres: no hacer nada también es una elección. Muchas veces no puedo es no quiero disfrazado. La mala fe es hacerse el que no elige para no cargar con la responsabilidad de haber elegido. Pero elegís igual: por omisión, también elegís."},
        {"ai": "Person standing at a cliff edge at dawn, vast landscape, dizziness of freedom",
         "q": "cliff edge sunrise person",
         "text": "Kierkegaard llamó a la libertad vértigo: cuando te das cuenta de que dependés de vos, da un poco de miedo. Ese miedo no es señal de que estés mal: es señal de que estás despertando. El vértigo no es caída: es el cuerpo avisando que estás muy cerca del borde de tu propia vida."},
        {"ai": "Classical conditioning experiment, dog and bell, vintage scientific illustration",
         "q": "pavlov dog bell",
         "text": "Pavlov condicionó a un perro para que salivara con una campana. A nosotros nos pasó igual: ante un sonido, respondemos. El condicionamiento no es una metáfora, es fisiología. Y lo que se condicionó, se puede descondicionar. No se trata de borrar lo aprendido: se trata de poder elegir cuándo respondés y cuándo no."},
        {"ai": "Old handwritten list of shoulds and obligations, overwhelming, dim warm light",
         "q": "handwritten list old paper",
         "text": "La psicoanalista Karen Horney lo describió como la tiranía de los deberías: una lista interminable de tengo que gobernando desde adentro, que nunca alcanza a cumplirse del todo. Cada deberías es un eslabón. Y lo peor: no sabés quién los escribió, porque los asumiste de tan chica."},
        {"ai": "Glowing neural circuits in a brain, automatic habits, dark scientific visualization",
         "q": "brain neurons glowing",
         "text": "La neurociencia lo confirma: los guiones viven en circuitos automáticos. El cerebro es perezoso: repite lo conocido porque le cuesta menos. Repetir no es elegir: es ahorrar energía. Por eso te cuesta tanto cambiar: no es falta de voluntad, es que tu cerebro elige el camino que ya conoce."},
        {"ai": "Brain with luminous pathways being reshaped by attention, bright hopeful, neuroplasticity",
         "q": "brain neural pathways light",
         "text": "La buena noticia: el mismo cerebro que automatiza, puede desautomatizar. La atención es la herramienta. Primero notás el impulso; después, con repetición, deja de gobernarte. Eso es plasticidad, no magia. Es gimnasia mental: cada vez que decidís en vez de reaccionar, abrís un camino nuevo."},
        {"ai": "Woman writing in a journal by morning window light, releasing old phrases, warm hopeful",
         "q": "woman writing journal morning",
         "text": "Soltar una cadena no es un salto: es aflojarla una vuelta por día. Primera herramienta: inventario de mandatos. Escribí las frases que escuchaste de chica y repetís como propias: así son las cosas, esto no se toca, tenés que ser así. Solo anotarlas ya es un acto enorme: convertís en visible lo invisible."},
        {"ai": "Woman looking at an old family photo, questioning inherited beliefs, soft light",
         "q": "old family photo woman",
         "text": "Segundo: preguntale a cada mandato de dónde viene. ¿Quién lo dijo primero? ¿Te sirve hoy? Un mandato no se obedece porque siempre estuvo: se obedece mientras te sirva. Y si no te sirve, no es desobediencia: es higiene. Es sacarte de encima un peso que nunca fue tuyo."},
        {"ai": "Woman facing her own reflection calmly, letting go of others opinions, warm light",
         "q": "mirror reflection woman",
         "text": "Tercero: imaginá el peor escenario de hacerlo a tu manera. Casi siempre es el qué dirán. Epicteto decía: si querés mejorar, aceptá que te tomen por tonto o por inútil. Pagar ese precio chico es el inicio de la libertad. Porque el que necesita la aprobación de todos, es esclavo de todos."},
        {"ai": "Hands doing a creative craft alone, no audience, cozy intimate warm light",
         "q": "hands craft cozy",
         "text": "Cuarto: hacé una microacción sin público. Escribí algo sin publicarlo, cociná sin mostrar, opiná sin pedir permiso. El que no aplaude también cuenta: el primer aplauso que necesitás es el tuyo. Hacer por hacer, sin mirada ajena, te devuelve algo que el sistema te sacó: la certeza de que tu valor no depende de la reacción."},
        {"ai": "Hand hovering near a smartphone, pausing, moment of choice, morning light",
         "q": "hand phone pause",
         "text": "Quinto: observá el impulso sin obedecerlo. El teléfono suena y ya vas a agarrarlo... respirá dos segundos y decidí vos si respondés. Ese segundo es un espacio de libertad que se agranda con la práctica. Primero son dos segundos, después son decisiones enteras. Así se entrena la libertad: de a espacios."},
        {"ai": "Woman gently saying no with a calm confident expression, serene warm light",
         "q": "woman saying no calm",
         "text": "Sexto: decí un no al día, sin explicar. No explicar es clave: quien explica, pide permiso. Un no tuyo, sin excusa, es la cadena más fácil de soltar. Y vas a ver que el mundo no se cae. El mundo aguanta un no. Lo que no aguanta es que vivas toda la vida diciendo que sí a todo."},
        {"ai": "Woman sitting in peaceful silence by a window, no phone, golden hour calm",
         "q": "woman window silence calm",
         "text": "Séptimo: estate un rato con vos, sin pantallas, sin ruido. Muchas cadenas solo se ven en silencio. La libertad empieza cuando ya no necesitás entretenerte para no pensar. Es difícil, al principio cuesta: el ruido tapa, el silencio muestra. Pero lo que muestra el silencio, es tuyo."},
        {"ai": "Woman setting a table with intentionality, warm home light, conscious choices",
         "q": "setting table warm home",
         "text": "No se trata de rebelarte contra todo: algunas cadenas son útiles y las volvés a poner. Se trata de que las que tengas sean las que elegiste. Elección consciente: eso es madurez, no conformismo. No es lo mismo vivir por inercia que vivir por decisión, aunque a veces se parezcan por fuera."},
        {"ai": "Dinner table set with meaning, warm evening light, understanding the rules",
         "q": "family dinner table warm",
         "text": "Pensalo como una mesa: no es libre quien rompe todas las reglas, es libre quien se sienta a la mesa sabiendo por qué está cada cosa. La libertad no es desorden: es un orden que se entiende. Y un orden que se entiende, se puede cambiar. El que rompe todo, cambia de cadena; el que entiende, elige."},
        {"ai": "Chains slowly loosening, one link at a time, sunrise light, gradual freedom",
         "q": "chains breaking sunrise",
         "text": "Volvemos al principio, para cerrar el círculo: la libertad no es hacer lo que quieras, es soltar lo que no es tuyo para descubrir lo que sí es. Las cadenas no se rompen de un golpe: se aflojan una vuelta por día. Y cada vuelta que aflojás, aunque nadie la vea, te acerca a vos misma."},
        {"ai": "Silhouette walking forward into open light, releasing chains behind, new dawn",
         "q": "silhouette light path freedom",
         "text": "Hoy miraste tus manos y viste que hay cadenas que no elegiste. Eso ya es el primer afloje. Si este video te hizo ver una cadena tuya, dale like, suscribite y contame en comentarios cuál vas a empezar a soltar, y compartilo con alguien que también esté soltando."},
    ],
})

VIDEOS.append({
    "name": "despertar-mano",
    "bgm": True,
    "reuse": "despertar",
    "scenes": [
        dict(s, estilo=est, handdraw=True)
        for s, est in zip(next(v["scenes"] for v in VIDEOS if v["name"] == "despertar"),
                          _DESPERTAR_DRAW)
    ],
})

VIDEOS.append({
    "name": "darse-cuenta",
    "bgm": True,
    "voices": ["male"],
    "scenes": [
        {"ai": "Two people sitting in conversation, one listening intently, tangled knots of ribbon on the table between them, warm dim lamp light",
         "q": "talking two people",
         "text": "Cuando alguien te cuenta un nudo de su vida, casi nunca te está contando el nudo. Te está contando otra cosa. Hoy te enseño la pregunta que lo destapa."},
        {"ai": "Woman turning a tangled coil of thread in her hands, uneasy expression, moody dim light",
         "q": "worried woman thread",
         "text": "El otro día escuchaba a una persona contarme una molestia. Nada grave: algo que le incomodaba, en distintos grados, desde un cosquilleo hasta un rechazo que iba y venía. Un nudo de esos que se cuenta en voz alta, sin saber que se está contando uno mismo."},
        {"ai": "Person looking into a hand mirror, realization dawning, soft golden light on the face",
         "q": "hand mirror reflection",
         "text": "Y en un momento, en vez de opinar, le devolví su propio hilo. Le dije, así, tal cual: en el fondo, me estás diciendo que eso te incomoda, o te confunde, o te parece que es diferente, o va en contra de lo que has aprendido o de tus creencias. ¿No?"},
        {"ai": "Person illuminated by a single soft beam of light in a dark room, deep silence, moment of realization",
         "q": "silence light contemplation",
         "text": "Y se hizo un silencio. Un silencio de los que valen oro. Porque era exactamente eso, y nadie se lo había dicho así nunca. Ese silencio tiene nombre: se llama darse cuenta."},
        {"ai": "Old map of a mind with small drawers and chests, one drawer overflowing, surreal, warm lantern light",
         "q": "old map",
         "text": "El nudo no era el problema de afuera. Era un mapa, adentro, que se quedaba corto. Y como nadie le enseñó a leer ese mapa, el mapa aprendió a quejarse. Nosotros, a esa queja, le decimos incomodidad."},
        {"ai": "Emerging from a dark cave into blinding sunshine, eyes hurting, hand shielding face, chiaroscuro",
         "q": "dark cave light",
         "text": "Platón lo anticipó hace dos mil años. Cuando el preso sale de la caverna y mira la luz, le arden los ojos. No es placer: es dolor. Y muchos, por ese dolor, deciden volver a las sombras. La incomodidad es el dolor de la luz."},
        {"ai": "Wooden cabinet with many drawers, one drawer bursting with oversized objects, surreal, dark moody",
         "q": "drawers cabinet",
         "text": "Arranquemos por el mapa. Desde que nacés, tu cabeza arma esquemas: cajones donde guardás lo que conocés y lo que suponés. Lo que entra en un cajón, lo asimilás sin fricción. Lo que no entra, choca. Y ese choque, ya lo sabés, se llama incomodidad."},
        {"ai": "Child building structures with blocks and symbols, learning, soft warm light, constructivism",
         "q": "child building blocks",
         "text": "Hace un siglo, el psicólogo suizo Jean Piaget lo explicó con dos palabras: asimilar y acomodar. Asimilar es meter lo nuevo en el cajón que ya tenés. Acomodar es agrandar ese cajón, o tirarlo y hacer otro. Crecés cada vez que acomodás."},
        {"ai": "An object too large for a small box, forced in, splintering wood, dramatic lighting",
         "q": "broken box",
         "text": "El problema: acomodar cuesta. Y cuando algo no entra en ningún cajón, en vez de acomodar, la cabeza lo empuja afuera con violencia. Ese empujón sale con varios nombres, según el día: eso es falso, eso es tonto, eso no tiene sentido."},
        {"ai": "Two opposing magnets repelling each other with visible sparks, dramatic dark background",
         "q": "magnets repelling",
         "text": "El psicólogo Leon Festinger le puso nombre científico a ese empujón: disonancia cognitiva. Cuando una idea nueva choca con una creencia querida, el cerebro siente un malestar de verdad. Y hace lo que puede para matarlo, a cualquier precio."},
        {"ai": "Person distractedly scrolling a glowing smartphone, escape symbols floating, dark lonely room",
         "q": "smartphone distraction",
         "text": "Fijate cómo lo mata: cambia de tema, busca a quien le dé la razón, se burla de quien lo dijo, agarra el teléfono para no pensar. Cualquier cosa antes que mirar la idea de frente. Es tan automático que no parece una elección: parece razón."},
        {"ai": "Person clinging to an old collapsing pillar while a sturdy building stands behind, stubborn twilight sky",
         "q": "old ruin pillar",
         "text": "Muchas veces lo mata defendiendo la creencia vieja hasta el ridículo. Cuanto más invertiste en una idea —tiempo, esfuerzo, identidad—, más te duele soltarla. No es terquedad: es que soltarla significa admitir que parte de tu vida se construyó sobre eso."},
        {"ai": "Person standing at the edge of an incomplete map, vast unknown luminous territory beyond",
         "q": "map edge horizon",
         "text": "Y volvemos al darse cuenta: ese malestar no está diciendo que el otro esté equivocado ni que el mundo esté mal. Te está diciendo, con la única voz que encontró, que hay un cajón que no alcanza. El que molesta no es el otro: es el límite del mapa."},
        {"ai": "Hand rewriting a sentence on paper, crossing out words, replacing with a large warm question mark, hopeful light",
         "q": "writing question mark",
         "text": "Clave simple: la próxima vez que algo te dé bronca, cambiá una palabra. En vez de esto está mal, decí esto no me cabe. Escuchá cuánto cambia el cuerpo con esa sola palabra. No estás negando el problema: estás abriendo la puerta para entenderlo."},
        {"ai": "Person facing their own reflection across the room, another self looking back, silhouette, realization",
         "q": "person reflection",
         "text": "Y acá viene lo bueno: la pregunta que destapa al otro, un día te destapa a vos. Porque la misma incomodidad que escuchás en los demás la pasás en silencio todos los días. Solo que la tuya viene disfrazada de opinión."},
        {"ai": "Woman contemplating three questions written on a chalkboard, warm classroom light, thoughtful",
         "q": "questions chalkboard",
         "text": "Hacé la prueba. Andá a las cosas que te molestan y preguntales: ¿esto me incomoda, me confunde, o me parece que va en contra de lo que aprendí? La respuesta, la mayoría de las veces, es la tercera. Y no te habías dado cuenta."},
        {"ai": "Closed door with a person walking away, missed light spilling from the crack, fading opportunity",
         "q": "closed door",
         "text": "El precio de no hacerse la pregunta es alto: lo que rechazás por feo, muchas veces era justo lo que te faltaba. Cuántas veces descartaste a una persona, una idea, un libro, solo porque te movieron el piso. No fue mala suerte: el rechazo te cerró la puerta antes de mirar."},
        {"ai": "Dramatic laughter mask floating, a hidden face of fear behind it, chiaroscuro",
         "q": "mask theater",
         "text": "Y cuidado con la burla. Cuando algo te incomoda de verdad, a veces lo único que se te ocurre es burlarte. La burla no es superioridad: es miedo. Nadie se burla de lo que entiende; la risa fuerte tapa lo que no se quiere ver."},
        {"ai": "Person holding an opinion bubble in one hand and a question mark in the other, deciding, warm light",
         "q": "question mark",
         "text": "No te estoy pidiendo que dejes de opinar. Solo digo que la opinión no es el primer paso: es el último. Antes de opinar hay una pregunta que casi nadie se hace: ¿esto me molesta porque es así, o porque no me cabe? La respuesta cambia todo."},
        {"ai": "Person pausing mid-motion, palm up, taking a breath, soft warm morning light",
         "q": "breathing pause",
         "text": "Entonces, ¿cómo se hace? Se aprende a leer el ruido. Cinco pasos, ninguno mágico, todos repetibles. Primero: cuando algo te incomode, en vez de reaccionar, pausá dos segundos y separá el mensaje de la forma. ¿Qué te está diciendo, sin el tono feo?"},
        {"ai": "Vintage framed family portrait on a wall, warm nostalgic light, silent influence",
         "q": "family portrait old",
         "text": "Segundo: preguntale a la incomodidad de dónde viene. ¿Qué aprendí que hace que esto me choque? ¿Qué creencia, qué suposición, qué ejemplo de mi familia protesta acá? Casi siempre la respuesta ya estaba antes de esta conversación: el cajón tiene dueño, y no sos vos."},
        {"ai": "Two doors: one warm and inviting with golden light (growth), one solid stone with a red stop hand (limit)",
         "q": "two doors",
         "text": "Tercero, y el más importante: distinguí. No toda incomodidad es señal de que te falta crecer. Hay un ruido del cajón y un ruido del límite. El ruido del cajón protesta porque algo no entra: te invita a crecer. El ruido del límite es el cuerpo que dice no, acá no, esto es demasiado: eso se respeta."},
        {"ai": "Fog of faint echoing voices around a person, a quiet still glowing heart at center, surreal calm",
         "q": "fog",
         "text": "¿Cómo se distinguen? El ruido del cajón suele venir con opinión ajena: me enseñaron así, todos piensan así, así siempre fue. El ruido del límite suele venir sin palabras: una quietud, un basta seco. Si viene con mandato, es estructura; si viene sin explicación, escuchalo."},
        {"ai": "Puzzle pieces fitting softly together, a piece being made slightly bigger, golden warm glow",
         "q": "puzzle pieces",
         "text": "Cuarto: si es el cajón, no lo rompas: acomodalo. Agrandalo un poquito. Buscá el punto de contacto, la parte de razón que tiene eso que te molesta. No tenés que tragártelo entero: alcanza con un pedazo que te haga ruido porque es verdad, no porque es nuevo."},
        {"ai": "Person sitting calmly by a small burning fire of discomfort, not running from it, warm hearth light",
         "q": "fireside calm",
         "text": "Quinto: aprendé a convivir con la incomodidad unos minutos sin taparla. El malestar desaparece solo cuando el cajón crece. Si lo tapás hoy, vuelve mañana con la misma información, mejor disfrazada. Tolerar el no-me-cabe sin matarlo es la verdadera práctica."},
        {"ai": "Large glowing key inserted in a door, ocean of possibility behind it, morning light",
         "q": "key door",
         "text": "Un truco que ayuda: la pregunta del otro lado. Cuando algo te incomode, preguntate qué pasaría si eso fuera cierto. No si es cierto: si fuera. Solo abrir esa puerta una vez ya cambia cómo suena la idea. La duda es la llave; no tenés que entrar, alcanza con girarla."},
        {"ai": "Two friends talking honestly, one gently holding a mirror toward the other, warm light",
         "q": "friends talking",
         "text": "Y si estás atascada, buscá un espejo de verdad: la gente en la que confiás te puede señalar dónde tu incomodidad es tu estructura y dónde es tu límite. Pedir esa lectura no es débil: es método. Y vos, cuando alguien te cuente su nudo, hacé lo mismo: devolvele su propio hilo."},
        {"ai": "Compass pointing toward unknown luminous territory, small repeated lights on an old map, discovery",
         "q": "compass map",
         "text": "Y ahora podés invertir el modelo. En vez de huir de la incomodidad, buscarla con criterio: cuando algo te da cosquillas varias veces, no es casualidad. Tu estructura te está avisando que afuera hay un pedazo de mundo que todavía no pudiste mirar. Eso, bien leído, es una brújula."},
        {"ai": "Hand catching a falling leaf at golden hour, not letting it drop, warm hopeful light",
         "q": "hand catching leaf",
         "text": "Ojo, no se trata de incomodarte por deporte ni de discutir todo. Se trata de no descartar de entrada. Lo que se rechaza sin examen se parece mucho a lo que se entiende sin esfuerzo. Y vos ya sabés cuál de las dos te deja más grande."},
        {"ai": "Two people in conversation at a round table, a circular golden light closing into a loop above them",
         "q": "round table conversation",
         "text": "Volvemos a la conversación del principio, para cerrar el círculo. Cuando alguien te cuenta un nudo, o cuando el nudo lo tenés vos: en el fondo, me estás diciendo que esto te incomoda, o te confunde, o va en contra de lo que has aprendido y de tus creencias. Ahora ya sabés leer esa frase."},
        {"ai": "Silhouette walking toward a brighter wider horizon at sunrise, growing map of the world unfolding ahead",
         "q": "sunrise horizon silhouette",
         "text": "El que nunca se incomoda, nunca acomoda nada. La incomodidad no es tu enemiga: es la señal de que tu mundo está por hacerse más grande. Si hoy viste un cajón tuyo, dale like, suscribite y contame en comentarios qué nudo tuyo se destapó con esta frase, y compartilo con alguien que esté en el suyo."},
    ],
})


def download_ai_image(prompt, out_path, seed=None, style=None):
    try:
        import flux_img
        suffix = style if style is not None else STYLE
        return flux_img.generate(prompt + suffix, out_path, seed=seed)
    except Exception as e:
        print(f"    IA falló: {e}", flush=True)
        raise RuntimeError(f"IA no generó imagen: {prompt[:40]}")


def find_local_img(imgs_dir, idx):
    """Busca imagen local eNN.* (png/jpg/webp) generada a mano.
    Prioriza .png/.webp sobre .jpg para no confundir con descargas de Pollinations."""
    import glob
    candidates = sorted(glob.glob(os.path.join(imgs_dir, f"e{idx:02d}.*")))
    # Priorizar formatos de mayor calidad sobre .jpg
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        for p in candidates:
            if p.lower().endswith(ext) and os.path.getsize(p) > 5000:
                return p
    return None


def find_local_video(imgs_dir, idx):
    """Busca b-roll local eNN.mp4 descargado o manual."""
    p = os.path.join(imgs_dir, f"e{idx:02d}.mp4")
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        return p
    return None


def rate_suffix(rate):
    """Sufijo de cache para el rate de TTS; vacío para el rate por defecto."""
    if not rate or rate == "+0%":
        return ""
    return "_r" + rate.replace("%", "").replace("+", "p").replace("-", "m")


def deepen_suffix(deepen):
    """Sufijo de cache para el deepen de TTS; vacío si es el default (0.92)."""
    if not deepen or abs(deepen - 0.92) < 0.01:
        return ""
    return "_d" + str(int(round(deepen * 100)))


def mix_boom(wav):
    """Genera un golpe de bajo (boom) sintético y lo mezcla bajo la voz.

    Se usa para dar impacto a palabras cortas enfáticas ("¡SÍ!"). El boom
    arranca a los ~120ms (cuando la voz ya sonó) con un decaimiento rápido.
    Devuelve la ruta del wav mezclado (cacheado como <wav>.boom.wav).
    """
    out = wav + ".boom.wav"
    if os.path.exists(out):
        return out
    boom = os.path.join(os.path.dirname(wav), "_boom_synth.wav")
    sr = int(subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "stream=sample_rate",
         "-of", "csv=p=0", wav],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[0])
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"sine=frequency=60:duration=0.6:sample_rate={sr}",
                    "-af", "volume=0.85,afade=t=out:st=0.08:d=0.52,"
                    f"adelay=120:all=1",
                    "-t", "0.8", "-ar", str(sr), "-ac", "1", boom],
                   check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", wav, "-i", boom,
                    "-filter_complex",
                    "[0:a]volume=1.0[a];[1:a]volume=0.55[b];"
                    "[a][b]amix=inputs=2:duration=first:dropout_transition=0,"
                    "alimiter=limit=0.95",
                    "-ar", str(sr), "-ac", "1", out],
                   check=True, capture_output=True)
    os.remove(boom)
    return out


def build_scene_local(vid_dirs, scene, idx, vk, n_scenes, rate="+0%",
                      bright=True):
    slug = f"e{idx:02d}_{vk}"
    sc_rate = scene.get("rate", rate)
    sc_deepen = scene.get("deepen", 0.92)
    rsfx = rate_suffix(sc_rate) + deepen_suffix(sc_deepen)
    img_path = find_local_img(vid_dirs["imgs"], idx) or os.path.join(
        vid_dirs["imgs"], f"e{idx:02d}.jpg")
    bg_img = os.path.join(vid_dirs["tmp"], f"{slug}_bg.jpg")

    # Resolver escena semántica → prompt técnico + emphasis tags
    scene = m.resolve_visual(scene)

    # Parse HTML <strong>/<em> tags: TTS recibe texto limpio, render recibe emphasis_map
    raw_text = scene["text"]
    if "<" in raw_text:
        tts_text, emphasis_map = m.parse_html_emphasis(raw_text)
    else:
        tts_text = raw_text
        emphasis_map = {}
    tts_clean = tts_text
    if m.has_pauses(tts_text):
        _, _chunks, tts_clean = m.split_pauses(tts_text)

    wav = os.path.join(vid_dirs["audio"],
                       f"{slug}{rsfx}_{zlib.crc32(tts_text.encode())}.wav")
    mp4 = os.path.join(vid_dirs["out"], f"{slug}.mp4")
    os.makedirs(vid_dirs["tmp"], exist_ok=True)

    video_path = find_local_video(vid_dirs["imgs"], idx)
    if video_path is None and scene.get("stock"):
        try:
            import pexels_stock
            if pexels_stock.available():
                q = scene.get("q") or scene.get("ai")
                dest = os.path.join(vid_dirs["imgs"], f"e{idx:02d}.mp4")
                cached = m.buscar_recurso("mp4", q)
                if cached:
                    from shutil import copyfile
                    copyfile(cached, dest)
                    video_path = dest
                    print(f"    video reusado del caché local: {os.path.basename(cached)}", flush=True)
                else:
                    video_path = pexels_stock.fetch_for_scene(q, dest)
                    m.guardar_recurso(dest, q, "mp4")
        except Exception as e:
            print(f"    stock falló: {e}", flush=True)
            video_path = None

    if video_path is None and scene.get("ai_video"):
        try:
            import ai_video
            if ai_video.available():
                dest = os.path.join(vid_dirs["imgs"], f"e{idx:02d}_ai.mp4")
                cached = m.buscar_recurso("mp4", scene.get("q") or scene["ai"])
                if cached:
                    from shutil import copyfile
                    copyfile(cached, dest)
                    video_path = dest
                    print(f"    video AI reusado del caché local: {os.path.basename(cached)}", flush=True)
                else:
                    video_path = ai_video.fetch_for_scene(
                        scene.get("q") or scene["ai"], dest,
                        aspect="9:16", model=scene.get("ai_model", "wan-fast"))
                    m.guardar_recurso(dest, scene.get("q") or scene["ai"], "mp4")
        except Exception as e:
            print(f"    ai_video falló: {e}", flush=True)
            video_path = None

    if video_path is not None:
        return build_scene_video(vid_dirs, scene, idx, vk, n_scenes,
                                 video_path, wav, mp4, rate=rate)

    if not (os.path.exists(img_path) and os.path.getsize(img_path) > 5000):
        if scene.get("reuse_img"):
            src = find_local_img(vid_dirs["imgs"], idx - 1) or os.path.join(
                vid_dirs["imgs"], f"e{idx-1:02d}.jpg")
            if os.path.exists(src):
                from shutil import copyfile
                copyfile(src, img_path)
        else:
            tema = scene.get("q") or scene.get("ai")
            cached = m.buscar_recurso("jpg", tema)
            if cached:
                from shutil import copyfile
                copyfile(cached, img_path)
                print(f"    imagen reusada del caché local: {os.path.basename(cached)}", flush=True)
            else:
                try:
                    style = scene.get("img_style")
                    if style is None:
                        style = LIGHT_STYLE if scene.get("light") else STYLE
                    download_ai_image(scene["ai"], img_path,
                                      seed=scene.get("img_seed", idx * 101),
                                      style=style)
                except Exception as e:
                    print(f"    IA falló, uso Commons: {e}", flush=True)
                    m.download_image(scene, img_path)
                m.guardar_recurso(img_path, tema, "jpg")
    m.strip_img_metadata(img_path)
    if not (scene.get("estilo") or scene.get("handdraw")):
        if bright:
            m.build_bg_bright(img_path, bg_img)
        else:
            m.build_bg(img_path, bg_img)
        from PIL import Image, ImageFilter
        _bg = Image.open(bg_img).convert("RGB")
        _bg = _bg.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        _bg.save(bg_img)

    voice = m.VOICES[vk]
    pause_after = scene.get("pause_after")
    if pause_after and not os.path.exists(wav):
        # Split text and add silence
        parts = tts_text.split("\n") if "\n" in tts_text else tts_text.rsplit(".", 1)
        if len(parts) == 2:
            t1, t2 = parts[0].strip() + ".", parts[1].strip()
        else:
            t1, t2 = tts_text, ""
        p1 = wav + ".p1.wav"
        p2 = wav + ".p2.wav"
        sil = wav + ".silence.wav"
        m.asyncio.run(m.tts_audio(t1, voice, p1, deepen=sc_deepen, rate=sc_rate))
        if t2:
            m.asyncio.run(m.tts_audio(t2, voice, p2, deepen=sc_deepen, rate=sc_rate))
        sr = 24000
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        f"anullsrc=r={sr}:cl=mono:d={pause_after}",
                        "-ar", str(sr), sil], capture_output=True, check=True)
        concat_txt = wav + ".concat.txt"
        with open(concat_txt, "w") as f:
            f.write(f"file '{p1}'\nfile '{sil}'\n")
            if t2:
                f.write(f"file '{p2}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
                        "-ar", str(sr), wav], capture_output=True, check=True)
        for tmpf in [p1, p2, sil, concat_txt]:
            if os.path.exists(tmpf):
                os.remove(tmpf)
    elif not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(tts_text, voice, wav,
                                  deepen=sc_deepen, rate=sc_rate))
    if scene.get("boom"):
        wav = mix_boom(wav)
    tj = os.path.join(vid_dirs["tmp"],
                      f"{slug}{rsfx}_{zlib.crc32(tts_text.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = m.align_words(tts_clean, wav)
        if timings is None:
            toks = tts_clean.split()
            dur = m.probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))

    n = n_scenes
    m.render_pipeline(scene, timings, img_path, bg_img, wav, mp4,
                      final=(idx == n), motion=scene.get("motion"),
                      emphasis_map=emphasis_map)
    return mp4


def build_scene_video(vid_dirs, scene, idx, vk, n_scenes, video_path, wav, mp4, rate="+0%"):
    """Escena con b-roll de video de fondo (local o Pexels)."""
    slug = f"e{idx:02d}_{vk}"
    rsfx = rate_suffix(rate)
    voice = m.VOICES[vk]

    # Resolver escena semántica → prompt técnico + emphasis tags
    scene = m.resolve_visual(scene)

    # Parse HTML <strong>/<em> tags
    raw_text = scene["text"]
    if "<" in raw_text:
        tts_text, emphasis_map = m.parse_html_emphasis(raw_text)
    else:
        tts_text = raw_text
        emphasis_map = {}
    tts_clean = tts_text
    if m.has_pauses(tts_text):
        _, _chunks, tts_clean = m.split_pauses(tts_text)

    if not os.path.exists(wav):
        m.asyncio.run(m.tts_audio(tts_text, voice, wav, rate=rate))
    tj = os.path.join(vid_dirs["tmp"],
                      f"{slug}{rsfx}_{zlib.crc32(tts_text.encode())}_timings.json")
    if os.path.exists(tj):
        timings = [tuple(x) for x in json.load(open(tj))]
    else:
        timings = m.align_words(tts_clean, wav)
        if timings is None:
            toks = tts_clean.split()
            dur = m.probe_duration(wav)
            step = dur / len(toks)
            timings = [(w, i * step, (i + 1) * step) for i, w in enumerate(toks)]
        json.dump(timings, open(tj, "w"))
    m.render_scene_video(timings, video_path, wav, mp4,
                         final=(idx == n_scenes),
                         emphasis_map=emphasis_map,
                         static_lines=scene.get("static_text"),
                         static_size=scene.get("static_size"),
                         static_y=scene.get("static_y", 0.42))
    return mp4


def build_video(vid):
    name = vid["name"]
    scenes = vid["scenes"]
    if vid.get("reuse"):
        base = os.path.join(ROOT, vid["reuse"])
        vd = {
            "imgs": os.path.join(base, "imgs"),
            "audio": os.path.join(base, "audio"),
            "tmp": os.path.join(base, "tmp"),
            "out": os.path.join(ROOT, name, "out"),
            "scenes": scenes,
        }
    else:
        vd = {
            "imgs": os.path.join(ROOT, name, "imgs"),
            "audio": os.path.join(ROOT, name, "audio"),
            "out": os.path.join(ROOT, name, "out"),
            "tmp": os.path.join(ROOT, name, "tmp"),
            "scenes": scenes,
        }
    for d in (vd["imgs"], vd["audio"], vd["out"], vd["tmp"]):
        os.makedirs(d, exist_ok=True)
    for vk in (vid.get("voices") or ["male"]):
        clips = []
        for idx, scene in enumerate(scenes, start=1):
            if name in LIGHT_SCENES and idx in LIGHT_SCENES[name]:
                scene = dict(scene, light=True)
            print(f"[{name}/{vk}] escena {idx}/{len(scenes)}", flush=True)
            clips.append(build_scene_local(
                vd, scene, idx, vk, len(scenes), rate=vid.get("rate", "+0%"),
                bright=vid.get("bright", True)))
        out = os.path.join(vd["out"], f"{name}_{vk}.mp4")
        m.concat(clips, out)
        if vid.get("bgm"):
            bgm = os.path.join(ROOT, "bgm", "ambient.wav")
            m.generate_bgm(bgm)
            mixed = out + ".bgm.mp4"
            m.mix_bgm(out, bgm, mixed)
            os.replace(mixed, out)
        m.limpiar_metadata_video(out)
        print(f"OK {out} {m.probe_duration(out):.1f}s", flush=True)


def listar_escenas(name):
    v = next(v for v in VIDEOS if v["name"] == name)
    for idx, sc in enumerate(v["scenes"], start=1):
        print(f"e{idx:02d}.jpg  |  {sc['text'][:70]}")
        print(f"   prompt: {sc['ai']}")
    print(f"\nGuardar en: {os.path.join(ROOT, name, 'imgs')}/")


VIDEOS.append({
    "name": "muerte",
    "bgm": True,
    "voices": ["male"],
    "rate": "-8%",
    "scenes": __import__("muerte_scenes").scenes_muerte(
        "Dale me gusta, compártelo y sígueme."),
})

VIDEOS.append({
    "name": "seneca",
    "voices": ["male"],
    "scenes": [
        {"ai": "Middle-aged man sitting alone in a dark room, surreal storm clouds swirling around him as his anxious thoughts, dramatic cinematic lighting, rain and lightning outside the window, photorealistic, high detail",
         "q": "storm night window man",
         "text": "Tu mente te hace sufrir por cosas que todavía no pasaron."},
        {"ai": "Ancient Roman marble bust of Seneca with beard, partially lit by warm golden light, dark museum background, dramatic chiaroscuro, philosophical dignity, photorealistic, high detail",
         "q": "seneca statue",
         "text": "Séneca decía que sufrimos más en la imaginación que en la realidad."},
        {"ai": "Hand writing worries on a sheet of paper at a wooden desk, small hourglass marking fifteen minutes beside it, warm candlelight, dark calm atmosphere, close-up, photorealistic, high detail",
         "q": "hand writing paper desk",
         "text": "Probá esto: escribí tus preocupaciones durante quince minutos."},
        {"ai": "Hand gently releasing a folded paper into soft morning light, calm tranquil dawn by a window, relief and peace, warm gentle tones, photorealistic, high detail",
         "q": "hand releasing paper light",
         "text": "Escribilas, soltalas y volvé al presente. Suscribite."},
    ],
})


STYLE_FINAL = ", photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16"

VIDEOS.append({
    "name": "cuantas-cosas",
    "bgm": True,
    "voices": ["male"],
    "scenes": [
        {"ai": "A tired Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, moving automatically through a busy day, walking quickly through her home while doing several small tasks at once, distracted and mentally overwhelmed, looking stressed and disconnected from the present moment, cinematic composition" + STYLE_FINAL,
         "q": "person busy home",
         "text": "Antes de seguir con lo próximo, frená un segundo.",
         "img_style": "", "motion": "zoom-in"},
        {"ai": "A tired Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, suddenly stops in the middle of her daily routine, standing completely still in a quiet room while everything around her feels slightly blurred, taking a deep breath and looking thoughtful, visual contrast between movement and stillness" + STYLE_FINAL,
         "q": "person standing still",
         "text": "Y preguntate algo: ¿cuántas cosas hiciste bien hoy?",
         "img_style": "", "motion": "zoom-out", "img_seed": 2002},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, organizing a messy room, carefully putting books, clothes and small objects back in their proper places, the room becoming visibly cleaner and more organized, the person looking quietly satisfied with her small accomplishment" + STYLE_FINAL,
         "q": "organizing books shelf",
         "text": "¿Acomodaste algo que venías dejando hace días? ¡Bien!",
         "img_style": "", "motion": "pan-right"},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, greeting another Argentine woman warmly on a city sidewalk, a simple genuine smile and friendly gesture, ordinary everyday moment, both people looking natural and relaxed, subtle feeling of human connection, soft golden light" + STYLE_FINAL,
         "q": "greeting neighbor sidewalk",
         "text": "¿Saludaste a alguien aunque estabas con la cabeza en otra cosa? ¡Genial!",
         "img_style": "", "motion": "pan-left", "img_seed": 4004},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, cleaning a small part of her home, wiping a kitchen counter and putting things away, simple everyday task, person looking slightly tired but satisfied after finishing, sunlight entering through a window, cozy realistic home" + STYLE_FINAL,
         "q": "cleaning kitchen counter",
         "text": "¿Limpiaste algo de la casa? ¡Vamos! Ya ves que sí podés.",
         "img_style": "", "motion": "zoom-in"},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, sitting at a desk completing an annoying administrative task on a laptop, several papers nearby, looking relieved after finally finishing something she had been postponing, ordinary realistic home environment, subtle feeling of accomplishment" + STYLE_FINAL,
         "q": "person desk laptop task",
         "text": "¿Hiciste ese trámite que no tenías ganas de hacer? ¡Una menos!",
         "img_style": "", "motion": "pan-right"},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, helping another adult carry several heavy boxes, genuine act of kindness in an ordinary neighborhood, both people showing natural grateful expressions, no exaggerated emotion, warm human connection, soft golden lighting" + STYLE_FINAL,
         "q": "helping carry boxes",
         "text": "¿Ayudaste a alguien? Eso también cuenta.",
         "img_style": "", "motion": "pan-left", "img_seed": 7007},
        {"ai": "An exhausted Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, sitting on the edge of her bed early in the morning, looking tired and unmotivated, but slowly standing up and preparing to start the day, soft morning sunlight entering through the window, quiet feeling of courage and persistence" + STYLE_FINAL,
         "q": "woman edge bed morning",
         "text": "¿Te levantaste aunque hoy no tenías muchas ganas? También cuenta.",
         "img_style": "", "motion": "zoom-in"},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, sitting at a desk placing the final check mark on a completed task list, then leaning back with a small satisfied smile, simple everyday accomplishment, warm afternoon light, realistic home environment" + STYLE_FINAL,
         "q": "task list checkmark desk",
         "text": "¿Terminaste algo, aunque haya sido pequeño? Bien hecho.",
         "img_style": "", "motion": "zoom-out"},
        {"ai": "An exhausted Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, sitting quietly at the end of the day near a window, looking tired but peaceful, realizing she did the best she could today, soft sunset light illuminating her face, calm intimate atmosphere, no sadness, acceptance and self-compassion" + STYLE_FINAL,
         "q": "person window sunset tired",
         "text": "Y si hoy simplemente hiciste lo que pudiste... Eso también vale.",
         "img_style": "", "motion": "zoom-in"},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, sitting at a wooden table looking at several small objects from her day: keys, a clean cup, a notebook, a completed task, a phone, and other ordinary objects, realizing that many small things were accomplished throughout the day, peaceful reflective expression, warm evening light" + STYLE_FINAL,
         "q": "table objects keys cup",
         "text": "Porque estamos tan acostumbrados a mirar lo que nos falta, que muchas veces ni siquiera registramos todo lo que sí hacemos.",
         "img_style": "", "motion": "pan-left", "img_seed": 11011},
        {"ai": "An Argentine woman in her forties, fair light skin, wavy chestnut brown hair, hazel eyes, European Spanish facial features, standing peacefully beside a large window at sunset, looking outside through the window with a calm reflective expression, not looking at the camera, seen from the side, warm sunlight illuminating her face, quiet moment of self-reflection, feeling proud of small daily accomplishments without arrogance, hopeful and peaceful ending" + STYLE_FINAL,
         "q": "person window sunset standing",
         "text": "Así que antes de pasar a la próxima cosa... frená un segundo. Y preguntate: ¿cuántas cosas hice bien hoy?",
         "img_style": "", "motion": "zoom-out"},
        {"reuse_img": True,
         "text": "Si te hizo bien escuchar esto, suscribite. Y contame en los comentarios: ¿qué hiciste bien hoy? Aunque haya sido algo pequeño. También cuenta.",
         "static_text": ["¿QUÉ HICISTE", "BIEN HOY?", "Aunque haya sido algo pequeño.", "También cuenta."],
         "motion": "zoom-in"},
    ],
})


GANA_BASE = ", photorealistic cinematic film still, realistic Latin American man in his 30s, natural face, emotional realism, subtle Christian atmosphere, dramatic natural lighting, muted warm colors, shallow depth of field, high detail, vertical 9:16, no text, no letters, no subtitles, no logo, no watermark"

VIDEOS.append({
    "name": "vas-ganando",
    "bgm": True,
    "voices": ["male"],
    "rate": "-8%",
    "scenes": [
        {"ai": "A tired Latin American man in his 30s sitting alone on the edge of his bed early in the morning, looking down with frustration and mental exhaustion, thinking about problems that keep returning, modest realistic bedroom, soft gray morning light through the window, feeling stuck but not hopeless" + GANA_BASE,
         "q": "man bed morning tired",
         "text": "¿Y si estás ganando... aunque tu problema siga ahí?",
         "img_style": "", "img_seed": 411, "motion": "zoom-in"},
        {"reuse_img": True,
         "text": "Muchas personas pasan de día en día pensando que no vencieron. Porque hay situaciones que persisten.",
         "motion": "zoom-out", "trans": {"style": "blur", "dur": 0.4}},
        {"ai": "The same Latin American man in his 30s from the previous image now standing by a large window at sunrise, looking out, a faint warm glow on his tired face, holding a cup of coffee, cozy home, warm morning light, first hope" + GANA_BASE,
         "q": "man window sunrise coffee",
         "text": "Pero si llegaste hasta hoy... venciste.",
         "img_style": "", "img_seed": 411, "motion": "zoom-in"},
        {"ai": "Jesus of Nazareth in his thirties, serene and dignified, walking through a crowd that rejects him, people turning away and ignoring him, first century Jerusalem street, warm muted light, subtle Christian atmosphere" + GANA_BASE,
         "q": "jesus crowd rejection",
         "text": "Jesús dijo: \"Yo he vencido al mundo\".",
         "img_style": "", "img_seed": 733, "motion": "pan-right"},
        {"ai": "Jesus of Nazareth carrying a heavy wooden cross through a hostile crowd, exhausted but serene, people shouting and judging him, first century Jerusalem, dramatic light, subtle Christian atmosphere" + GANA_BASE,
         "q": "jesus cross carrying",
         "text": "Y mirá esto. Hizo el bien. Amó. Ayudó. No respondió al mal con mal.",
         "img_style": "", "img_seed": 733, "motion": "zoom-in"},
        {"reuse_img": True,
         "text": "Y aun así... lo juzgaron. Lo rechazaron. Lo llevaron a la cruz.",
         "motion": "pan-left", "trans": {"style": "black", "dur": 0.5}},
        {"ai": "Silhouette of Jesus on a hill at dawn, a wooden cross planted in the ground beside him, golden sunrise light breaking over the horizon, peaceful and victorious, subtle Christian atmosphere, warm gold tones" + GANA_BASE,
         "q": "jesus hill sunrise silhouette",
         "text": "Pero no perdió. Venció.",
         "img_style": "", "img_seed": 733, "motion": "zoom-in",
         "trans": {"style": "flash", "dur": 0.25}},
        {"ai": "The same Latin American man in his 30s sitting in a dark room surrounded by tall shadowy figures representing unresolved problems, one small warm path of light opening ahead of him on the floor, dramatic chiaroscuro" + GANA_BASE,
         "q": "man dark room shadows light",
         "text": "Y vos también vencés.",
         "img_style": "", "img_seed": 411, "motion": "zoom-in",
         "trans": {"style": "blur", "dur": 0.4}},
        {"reuse_img": True,
         "text": "Solo que hay un problema: el mundo te muestra lo que todavía sigue ahí. Pero no te muestra todo lo que atravesaste para llegar hasta acá.",
         "motion": "pan-right"},
        {"ai": "The same Latin American man in his 30s standing at a crossroads between two paths, one path he controls and one beyond his control, contemplating his choices, warm dawn light" + GANA_BASE,
         "q": "man crossroads choice",
         "text": "Hay cosas que dependen de vos. Y hay cosas que no. Algunas podés cambiarlas. Otras, solamente atravesarlas.",
         "img_style": "", "img_seed": 411, "motion": "pan-left",
         "trans": {"style": "blur", "dur": 0.35}},
        {"ai": "The same Latin American man in his 30s walking alone on a long empty road at sunset, looking back at how far he has come, tired but steady, golden evening light" + GANA_BASE,
         "q": "man walking road sunset",
         "text": "Entonces... Anteayer, ¿venciste?",
         "img_style": "", "img_seed": 411, "motion": "pan-right"},
        {"reuse_img": True,
         "text": "¡SÍ!",
         "rate": "-35%", "boom": True,
         "static_text": ["¡SÍ!"], "static_size": 170,
         "motion": "zoom-in", "trans": {"style": "flash", "dur": 0.2}},
        {"ai": "The same Latin American man in his 30s walking on the same road, now closer to the horizon, lighter steps, a small smile of quiet victory, sunrise ahead" + GANA_BASE,
         "q": "man walking road closer",
         "text": "Ayer, ¿venciste?",
         "img_style": "", "img_seed": 411, "motion": "pan-right"},
        {"reuse_img": True,
         "text": "¡SÍ!",
         "rate": "-35%", "boom": True,
         "static_text": ["¡SÍ!"], "static_size": 210,
         "motion": "zoom-in", "trans": {"style": "flash", "dur": 0.2}},
        {"ai": "The same Latin American man in his 30s standing on a small hill at sunrise, looking at the bright horizon with calm pride, hands relaxed, golden light washing over him" + GANA_BASE,
         "q": "man hill sunrise horizon",
         "text": "Hoy estás acá. ¿Venciste?",
         "img_style": "", "img_seed": 411, "motion": "zoom-in",
         "trans": {"style": "blur", "dur": 0.35}},
        {"reuse_img": True,
         "text": "¡SÍ!",
         "rate": "-35%", "boom": True,
         "static_text": ["¡SÍ!"], "static_size": 250,
         "motion": "zoom-in", "trans": {"style": "flash", "dur": 0.25}},
        {"ai": "The same Latin American man in his 30s walking toward a bright luminous horizon at dawn, seen from behind, the road opening wide ahead, warm golden and hopeful light, subtle Christian atmosphere" + GANA_BASE,
         "q": "man walking bright horizon",
         "text": "Entonces seguí. Vas ganando.",
         "img_style": "", "img_seed": 411, "motion": "zoom-out"},
    ],
})



# ===== 20 REELS FB generados 2026-08-21 (ideas en VIDEOS_FACE_PARA_SUBIR/) =====
VIDEOS.append({
 "name": "fb01-rutina-de-manana-sin-prisa",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A Latin American woman in her fifties sitting on the edge of her bed in profile, breathing slowly and deliberately, eyes soft, shoulders relaxed, sheer curtains diffusing pale morning light across the room, quiet unhurried atmosphere, intimate documentary framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman morning bed light",
   "text": "Si tu mañana empieza corriendo, tu sistema nervioso pasará el resto del día intentando apagar incendios.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "zoom-in"
  },
  {
   "ai": "Close-up of two mature hands cradling a steaming ceramic mug, thin vapor rising slowly into a shaft of soft window light, warm terracotta and cream tones, wooden kitchen table blurred behind, shallow depth of field, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "steaming coffee hands",
   "text": "Despertar con el sonido estridente de la alarma y saltar de la cama para atender urgencias ajenas no es empezar el día, es entrar en modo de supervivencia absoluto. Tu cuerpo interpreta esa prisa inicial como una amenaza inminente, inundándote de cortisol antes de que alcances a dar el primer sorbo de café.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "pan-right"
  },
  {
   "ai": "Warm empty bedroom at sunrise, rumpled linen bed catching the first golden rays through a half-open window, a small potted plant on the sill, dust particles floating in the light beam, peaceful stillness, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "sunlit cozy bedroom",
   "text": "La consecuencia es que pasas las siguientes horas reaccionando con irritabilidad, fatiga mental y una molesta opresión en el pecho que no te deja respirar. Al final de la jornada, terminas exhausta no por lo que hiciste, sino por la tensión constante con la que sostuviste cada pequeña tarea cotidiana.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "pan-left"
  },
  {
   "ai": "A Latin American woman in her fifties sitting on the edge of her bed in profile, breathing slowly and deliberately, eyes soft, shoulders relaxed, sheer curtains diffusing pale morning light across the room, quiet unhurried atmosphere, intimate documentary framing, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman morning bed light",
   "text": "Aristóteles nos enseñaba que la excelencia se cultiva en los pequeños hábitos diarios. Regálate apenas diez minutos de transición lenta al despertar, respirando de manera pausada antes de tocar tu teléfono o encender las pantallas.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "zoom-in"
  },
  {
   "ai": "Close-up of two mature hands cradling a steaming ceramic mug, thin vapor rising slowly into a shaft of soft window light, warm terracotta and cream tones, wooden kitchen table blurred behind, shallow depth of field, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "steaming coffee hands",
   "text": "Permítete recibir la luz del día como el hermoso don que es, dándole a tu cuerpo el tiempo necesario para comprender que está a salvo.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "pan-right"
  },
  {
   "ai": "A Latin American woman in her fifties sitting on the edge of her bed in profile, breathing slowly and deliberately, eyes soft, shoulders relaxed, sheer curtains diffusing pale morning light across the room, quiet unhurried atmosphere, intimate documentary framing, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "sunlit cozy bedroom",
   "text": "Protege tu despertar con paciencia, porque si tu mañana empieza corriendo, tu sistema nervioso pasará el resto del día intentando apagar incendios.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "zoom-out"
  },
  {
   "ai": "Close-up of two mature hands cradling a steaming ceramic mug, thin vapor rising slowly into a shaft of soft window light, warm terracotta and cream tones, wooden kitchen table blurred behind, shallow depth of field, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman morning bed light",
   "text": "Si buscas recuperar el ritmo de tu vida, dale me gusta, compártelo y sígueme para que caminemos juntas.",
   "img_style": "",
   "img_seed": 5037,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb02-descansar-sin-sentir-culpa",
 "bgm": True,
 "bright": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A closed linen notebook resting on a wooden breakfast table beside a pale-blue ceramic cup of tea, soft early morning window light falling gently across the table, a small green plant at the edge of frame, quiet clear start of a new day, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "closing notebook hands",
   "text": "Estar cansada no es un fallo en tu fuerza de voluntad, es la señal física de que has estado sosteniendo demasiado.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "zoom-in"
  },
  {
   "ai": "Hands placing neatly folded towels into a wicker basket in a bright tidy living room, white walls and a lush green plant beside a sunlit window, balanced daylight with soft shadows, honest calm everyday home rhythm, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "woman window leaves",
   "text": "Vivimos bajo la falsa promesa de que solo mereces detenerte cuando todo esté perfectamente terminado y tu lista de pendientes esté vacía. Sin embargo, esa lista nunca se termina y tú sigues posponiendo tu necesidad de parar, acumulando un agotamiento que ya duele en los hombros.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "pan-right"
  },
  {
   "ai": "A woman seen from behind sitting in a cozy armchair beside a bright window, an open book resting face-down on the armrest, one hand loosely holding a warm mug, soft daylight filling the room, green plants nearby, thoughtful yet peaceful moment, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "bare feet rug",
   "text": "Cuando finalmente te sientas a descansar, tu mente te castiga con pensamientos de culpa que te dicen que estás perdiendo el tiempo o que eres perezosa. Así, el descanso se convierte en una tortura mental y nunca logras recuperar la energía que tu cuerpo te pide a gritos.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "pan-left"
  },
  {
   "ai": "Hands gently repotting a vibrant green plant into a terracotta pot on a sunny windowsill, fresh dark soil and water droplets sparkling on the leaves, cheerful natural daylight, quiet satisfaction of growth and care, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "closing notebook hands",
   "text": "El psicólogo Carl Rogers explicaba que el organismo sabe lo que necesita para sanar si tan solo lo escuchamos sin juzgarlo. El descanso no es un premio que debes ganarte con esfuerzo, sino un derecho natural y una gracia para renovar tu templo.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman in profile settling into a sunny reading chair wrapped in a soft yellow knit blanket holding a warm cup of tea, relaxed shoulders and a hint of a smile, generous window light, books and blooming flowers around her, serene everyday contentment, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "woman window leaves",
   "text": "Aprende a detenerte por el simple hecho de que estás cansada, entregando tus cargas con la confianza de que el mundo seguirá girando sin ti.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "pan-right"
  },
  {
   "ai": "A woman seen from behind opening glass doors onto a small balcony full of flowering plants, gentle breeze moving the leaves, bright late-afternoon light entering the room with balanced exposure, sense of space opening and permission to pause, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "bare feet rug",
   "text": "Permítete parar hoy sin dar explicaciones, porque estar cansada no es un fallo en tu fuerza de voluntad, es la señal física de que has estado sosteniendo demasiado.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "zoom-out"
  },
  {
   "ai": "Wide view of a luminous living room opening onto a balcony full of flowering red and pink geraniums, two colorful ceramic cups on a wooden table in the foreground, late morning sunshine filling the space with warmth and life, expansive hopeful atmosphere, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
   "q": "closing notebook hands",
   "text": "Si este mensaje abraza tu corazón, dale me gusta, compártelo y sígueme para recordar que mereces paz.",
   "img_style": "",
   "img_seed": 5074,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb03-el-perfeccionismo-te-paraliza",
 "rate": "-10%",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Close-up of a hand writing with a pencil on slightly wrinkled paper, crossing nothing out and continuing steadily, graphite catching warm side light, wooden desk scattered with drafts, honest imperfect work in progress, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hand writing pencil paper",
   "text": "Esperar a tener todo bajo control para empezar es la forma más sutil de boicotear tu propia paz.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind opening a wooden window to let fresh afternoon air into a home office, papers and books waiting on the desk below, golden light spilling across the floorboards, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "opening window afternoon",
   "text": "Te repites que vas a iniciar ese proyecto, ordenar ese espacio o cuidar de ti cuando tengas el tiempo ideal y las condiciones perfectas. Esa búsqueda implacable de la perfección no es amor al detalle, sino un mecanismo de defensa para evitar el dolor de no ser lo suficientemente buena.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "pan-right"
  },
  {
   "ai": "Hands gently arranging books on a shelf coming into sharp focus while the foreground blurs, warm domestic light, quiet act of beginning again with what is at hand, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tidying bookshelf hands",
   "text": "La consecuencia directa es una parálisis silenciosa que te llena de frustración y te hace sentir estancada mientras los meses transcurren. Te culpas por no avanzar, creyendo que te falta disciplina, cuando en realidad lo que te frena es el miedo a cometer un error.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "pan-left"
  },
  {
   "ai": "Close-up of a hand writing with a pencil on slightly wrinkled paper, crossing nothing out and continuing steadily, graphite catching warm side light, wooden desk scattered with drafts, honest imperfect work in progress, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hand writing pencil paper",
   "text": "Los antiguos filósofos estoicos nos recordaban que el camino se hace dando pasos reales, no planeando trayectos perfectos en la mente. Comienza hoy con lo que tienes, de la manera más sencilla e imperfecta posible, sabiendo que el valor está en el intento y no en el resultado impecable.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind opening a wooden window to let fresh afternoon air into a home office, papers and books waiting on the desk below, golden light spilling across the floorboards, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "opening window afternoon",
   "text": "Confía en el proceso y en el Creador, que valora tu intención sincera por encima de cualquier estándar humano.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "pan-right"
  },
  {
   "ai": "Close-up of a hand writing with a pencil on slightly wrinkled paper, crossing nothing out and continuing steadily, graphite catching warm side light, wooden desk scattered with drafts, honest imperfect work in progress, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tidying bookshelf hands",
   "text": "Da ese pequeño paso hoy mismo, porque esperar a tener todo bajo control para empezar es la forma más sutil de boicotear tu propia paz.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "zoom-out"
  },
  {
   "ai": "Woman seen from behind opening a wooden window to let fresh afternoon air into a home office, papers and books waiting on the desk below, golden light spilling across the floorboards, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hand writing pencil paper",
   "text": "Si necesitas empezar sin presiones, dale me gusta, compártelo y sígueme para avanzar juntas.",
   "img_style": "",
   "img_seed": 5111,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb04-decir-no-sin-culpa",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Hot tea pouring slowly into an already full ceramic cup, liquid trembling at the rim about to spill, steam curling upward, warm side light on glazed pottery, quiet visual metaphor for taking on more than one can hold, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tea pouring full cup",
   "text": "Cada vez que dices sí a los demás por miedo a decepcionarlos, te estás diciendo no a ti misma.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman's hand gently laying a buzzing phone face down on a wooden table and sliding it away, choosing not to answer, soft evening window light, calm deliberate gesture, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "phone face down table",
   "text": "Pasas la vida aceptando favores, compromisos y tareas que no deseas realizar, solo para evitar el conflicto o para que no piensen que eres egoísta. Te has convertido en el pilar que sostiene a todos, pero a costa de vaciar tu propio tanque de energía.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "pan-right"
  },
  {
   "ai": "Lateral profile of a middle-aged woman standing at her balcony gazing at a distant tree-lined street, expression serene and settled, warm dusk light brushing her face, unhurried stillness, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman balcony dusk",
   "text": "Al actuar así, terminas acumulando un resentimiento silencioso hacia las personas que amas y una profunda tristeza contigo misma por no saber proteger tu espacio. Te sientes atrapada en una red de obligaciones que tú misma tejiste por no atreverte a poner un límite claro.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "pan-left"
  },
  {
   "ai": "Hot tea pouring slowly into an already full ceramic cup, liquid trembling at the rim about to spill, steam curling upward, warm side light on glazed pottery, quiet visual metaphor for taking on more than one can hold, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tea pouring full cup",
   "text": "Establecer límites sanos no es un acto de egoísmo, sino una muestra de respeto hacia el don de tu propia vida. Puedes decir 'no' con amabilidad, sin necesidad de dar largas explicaciones o inventar excusas para justificar tu decisión.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman's hand gently laying a buzzing phone face down on a wooden table and sliding it away, choosing not to answer, soft evening window light, calm deliberate gesture, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "phone face down table",
   "text": "Recuerda que tu valor no depende de cuánto te desgastes por los demás, sino de la autenticidad con la que decides vivir.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "pan-right"
  },
  {
   "ai": "Hot tea pouring slowly into an already full ceramic cup, liquid trembling at the rim about to spill, steam curling upward, warm side light on glazed pottery, quiet visual metaphor for taking on more than one can hold, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman balcony dusk",
   "text": "Aprende a proteger tu espacio con amor, porque cada vez que dices sí a los demás por miedo a decepcionarlos, te estás diciendo no a ti misma.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "zoom-out"
  },
  {
   "ai": "A woman's hand gently laying a buzzing phone face down on a wooden table and sliding it away, choosing not to answer, soft evening window light, calm deliberate gesture, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tea pouring full cup",
   "text": "Si estás lista para priorizar tu bienestar, dale me gusta, compártelo y sígueme.",
   "img_style": "",
   "img_seed": 5148,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb05-tu-version-del-pasado",
 "bgm": True,
 "rate": "-8%",
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Mature hands turning the pages of an old photo album without stopping, sepia photographs passing beneath fingertips, nostalgic window light, wooden table, tender reflection on who she used to be rather than longing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "old photo album hands",
   "text": "Compararte con quien eras hace diez años es una trampa injusta que ignora todo lo que has tenido que superar.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "zoom-in"
  },
  {
   "ai": "Close-up of hands smoothing a soft folded woolen fabric with an accepting gentle gesture, warm fiber texture in raking light, quiet reconciliation with the past, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "folding wool fabric",
   "text": "Sueles mirar tus fotos antiguas o recordar tu energía de antes y te juzgas con severidad por no lucir igual o por no tener la misma resistencia. Olvidas que tu cuerpo y tu mente han tenido que adaptarse a batallas silenciosas, pérdidas y responsabilidades que antes ni siquiera imaginabas.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "pan-right"
  },
  {
   "ai": "Warm back view of a woman walking along a leafy nature path at sunset, long shadow stretching ahead of her, golden hour light through branches, moving forward carrying her whole history, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman walking path sunset",
   "text": "Este hábito constante de compararte con tu pasado te genera una insatisfacción crónica que empaña tu presente y te impide ver tu valor actual. Te sientes en deuda contigo misma, como si hubieras fallado, cuando en realidad solo has madurado y sobrevivido.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "pan-left"
  },
  {
   "ai": "Mature hands turning the pages of an old photo album without stopping, sepia photographs passing beneath fingertips, nostalgic window light, wooden table, tender reflection on who she used to be rather than longing, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "old photo album hands",
   "text": "La psicología seria nos enseña que el desarrollo humano es una constante adaptación y transformación, no una línea recta de eterna juventud. Acepta con gratitud la mujer que eres hoy, con tus marcas, tu sabiduría acumulada y tu capacidad de resiliencia.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "zoom-in"
  },
  {
   "ai": "Close-up of hands smoothing a soft folded woolen fabric with an accepting gentle gesture, warm fiber texture in raking light, quiet reconciliation with the past, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "folding wool fabric",
   "text": "Eres un ser completo en cada etapa de tu vida, sostenida por la gracia y el amor de Quien te conoce por tu nombre desde el principio.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "pan-right"
  },
  {
   "ai": "Mature hands turning the pages of an old photo album without stopping, sepia photographs passing beneath fingertips, nostalgic window light, wooden table, tender reflection on who she used to be rather than longing, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman walking path sunset",
   "text": "Honra tu momento actual, porque compararte con quien eras hace diez años es una trampa injusta que ignora todo lo que has tenido que superar.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "zoom-out"
  },
  {
   "ai": "Close-up of hands smoothing a soft folded woolen fabric with an accepting gentle gesture, warm fiber texture in raking light, quiet reconciliation with the past, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "old photo album hands",
   "text": "Si quieres reconciliarte con tu presente, dale me gusta, compártelo y sígueme para seguir sanando.",
   "img_style": "",
   "img_seed": 5185,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb06-amistades-que-drenan",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Two coffee cups on a small cafe table, one hand gently pulling its own cup closer while the other remains untouched across the table, marking a quiet boundary, soft morning light, shallow depth of field, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "two coffee cups table",
   "text": "Hay conversaciones que te dejan ligera y otras que te hacen sentir que has corrido una maratón mental.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman gently closing a tall window against the noise of a busy street, her hand resting a moment on the latch, city sounds fading, apartment growing quiet and safe, warm interior light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing window city",
   "text": "A veces mantienes vínculos por pura costumbre, compromiso social o el peso de los años compartidos, aunque sientas que ya no hay sintonía. Te sientas a tomar un café y regresas a casa con dolor de cabeza, abrumada por quejas interminables o críticas disimuladas.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "pan-right"
  },
  {
   "ai": "Lateral profile of a woman smiling faintly at a small green seedling sprouting in a terracotta pot on her windowsill, new growth after difficult seasons, soft diffused daylight, hopeful tenderness, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "seedling pot windowsill",
   "text": "Sostener estas relaciones por compromiso desgasta tu energía vital y te deja expuesta a una negatividad que no te pertenece. Terminas sintiéndote sola a pesar de estar acompañada, porque notas que en esos espacios no hay un verdadero interés por tu bienestar.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "pan-left"
  },
  {
   "ai": "Two coffee cups on a small cafe table, one hand gently pulling its own cup closer while the other remains untouched across the table, marking a quiet boundary, soft morning light, shallow depth of field, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "two coffee cups table",
   "text": "Aristóteles decía que la verdadera amistad es aquella que busca el bien mutuo y florece en la virtud, no la que se basa solo en la utilidad o el desahogo. Tienes derecho a tomar distancia de aquellos espacios que alteran tu paz, eligiendo con delicadeza a las personas que permites entrar en tu jardín interior.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman gently closing a tall window against the noise of a busy street, her hand resting a moment on the latch, city sounds fading, apartment growing quiet and safe, warm interior light, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing window city",
   "text": "Rodéate de quienes respeten tu silencio y celebren tu paz con el mismo amor con el que tú lo haces.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "pan-right"
  },
  {
   "ai": "Two coffee cups on a small cafe table, one hand gently pulling its own cup closer while the other remains untouched across the table, marking a quiet boundary, soft morning light, shallow depth of field, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "seedling pot windowsill",
   "text": "Elige bien con quién compartes tu tiempo, porque hay conversaciones que te dejan ligera y otras que te hacen sentir que has corrido una maratón mental.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "zoom-out"
  },
  {
   "ai": "A woman gently closing a tall window against the noise of a busy street, her hand resting a moment on the latch, city sounds fading, apartment growing quiet and safe, warm interior light, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "two coffee cups table",
   "text": "Si valoras tu paz mental en tus relaciones, dale me gusta, compártelo y sígueme para más consejos.",
   "img_style": "",
   "img_seed": 5222,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb07-empezar-de-forma-imperfecta",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A hand opening a blank notebook and drawing one imperfect wobbling line with a fountain pen, ink glistening, decisive beginning despite imperfection, warm desk lamp glow, close intimate framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "notebook first line pen",
   "text": "No necesitas sentirte completamente segura para dar el primer paso; la seguridad se construye en el camino.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind pushing open a weathered wooden garden door and stepping firmly onto a stone path, morning mist and greenery beyond, courage before certainty, soft golden light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "garden door opening",
   "text": "Pasas semanas buscando el curso perfecto, el libro ideal o el momento en que todas tus dudas desaparezcan para iniciar un cambio. Creer que la confianza debe llegar antes que la acción es el motivo por el cual muchos hermosos proyectos nunca ven la luz.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "pan-right"
  },
  {
   "ai": "Extreme close-up of an hourglass with grains falling in a steady rhythmic stream, each grain catching amber light, dark elegant background, patience of small consistent action, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hourglass sand falling",
   "text": "Al posponer tus decisiones esperando esa certeza absoluta, alimentas la frustración y la idea de que no eres capaz. Te quedas atrapada en un ciclo infinito de análisis que solo genera cansancio mental y te aleja de la experiencia real de aprender haciendo.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "pan-left"
  },
  {
   "ai": "A hand opening a blank notebook and drawing one imperfect wobbling line with a fountain pen, ink glistening, decisive beginning despite imperfection, warm desk lamp glow, close intimate framing, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "notebook first line pen",
   "text": "La psicología cognitiva demuestra que el cerebro gana confianza a través de la experiencia directa, no de la especulación mental. Comienza hoy con lo que sabes, permitiéndote cometer errores y ajustar el rumbo sobre la marcha sin juzgarte con dureza.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind pushing open a weathered wooden garden door and stepping firmly onto a stone path, morning mist and greenery beyond, courage before certainty, soft golden light, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "garden door opening",
   "text": "Recuerda que la vida es un don dinámico que se despliega en el movimiento y no en la espera indefinida.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "pan-right"
  },
  {
   "ai": "A hand opening a blank notebook and drawing one imperfect wobbling line with a fountain pen, ink glistening, decisive beginning despite imperfection, warm desk lamp glow, close intimate framing, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hourglass sand falling",
   "text": "Atrévete a caminar con tus dudas a cuestas, porque no necesitas sentirte completamente segura para dar el primer paso.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "zoom-out"
  },
  {
   "ai": "Woman seen from behind pushing open a weathered wooden garden door and stepping firmly onto a stone path, morning mist and greenery beyond, courage before certainty, soft golden light, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "notebook first line pen",
   "text": "Si estás lista para avanzar con imperfección, dale me gusta, compártelo y sígueme para motivarte.",
   "img_style": "",
   "img_seed": 5259,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb08-la-forma-en-que-te-hablas",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A middle-aged woman wiping condensation from a fogged bathroom mirror with her palm, her reflection gradually appearing soft and forgiving, humid warm light, intimate moment of meeting herself kindly, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "foggy mirror woman hand",
   "text": "Si le hablaras a tus seres queridos como te hablas a ti misma cuando fallas, probablemente estarías muy sola.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "zoom-in"
  },
  {
   "ai": "Detail of a hand stroking the soft nap of a cream wool blanket in slow comforting passes, fibers glowing in warm lamplight, tenderness directed inward, cozy texture study, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "wool blanket hand",
   "text": "Cuando cometes un pequeño error en tu día, tu mente suele reaccionar con un tono crítico, duro y sumamente exigente que jamás usarías con nadie más. Te tratas como a tu peor enemiga, exigiéndote un estándar de perfección que es humanamente imposible de sostener.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "pan-right"
  },
  {
   "ai": "Woman holding a hot ceramic cup against her chest with both hands, eyes closed, steam rising past her chin, wrapped in a knit cardigan, golden evening light, deep physical peace, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "cup chest eyes closed",
   "text": "Este diálogo interno hostil debilita tu autoestima y activa de forma constante las alertas de peligro en tu sistema nervioso. Terminas viviendo con miedo a equivocarte, sintiendo que tu propio hogar mental es un espacio hostil donde no hay lugar para la compasión.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "pan-left"
  },
  {
   "ai": "A middle-aged woman wiping condensation from a fogged bathroom mirror with her palm, her reflection gradually appearing soft and forgiving, humid warm light, intimate moment of meeting herself kindly, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "foggy mirror woman hand",
   "text": "Carl Rogers explicaba que la paradoja de la vida es que solo podemos cambiar cuando nos aceptamos de manera incondicional tal como somos hoy. Comienza a observar tus pensamientos sin juzgarlos y háblate con la misma ternura con la que consolarías a una amiga cansada.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "zoom-in"
  },
  {
   "ai": "Detail of a hand stroking the soft nap of a cream wool blanket in slow comforting passes, fibers glowing in warm lamplight, tenderness directed inward, cozy texture study, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "wool blanket hand",
   "text": "Eres una creación valiosa, merecedora de paciencia, respeto y un amor que empiece por ti misma.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "pan-right"
  },
  {
   "ai": "A middle-aged woman wiping condensation from a fogged bathroom mirror with her palm, her reflection gradually appearing soft and forgiving, humid warm light, intimate moment of meeting herself kindly, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "cup chest eyes closed",
   "text": "Cambia el tono de tu voz interior hoy, porque si le hablaras a tus seres queridos como te hablas a ti misma cuando fallas, probablemente estarías muy sola.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "zoom-out"
  },
  {
   "ai": "Detail of a hand stroking the soft nap of a cream wool blanket in slow comforting passes, fibers glowing in warm lamplight, tenderness directed inward, cozy texture study, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "foggy mirror woman hand",
   "text": "Si quieres aprender a tratarte con más amabilidad, dale me gusta, compártelo y sígueme.",
   "img_style": "",
   "img_seed": 5296,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb09-el-mito-del-momento-perfecto",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A set of house keys dropping onto an entryway console table beside a mail pile, motion blur frozen mid-fall, ordinary everyday arrival, warm afternoon light through frosted glass, real life happening now, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "keys falling table",
   "text": "La idea de que algún día tendrás el tiempo y el silencio perfectos para ocuparte de ti es una ilusión.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman pausing mid-step in her kitchen, eyes closed, one hand resting on the counter, taking a single deep breath amid the untidy normalcy of daily life, soft window light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "kitchen pause breath",
   "text": "Sueles decirte que vas a meditar, a caminar o a leer cuando termines la mudanza, cuando los niños crezcan o cuando baje el ritmo de tu trabajo. Sin embargo, la vida cotidiana siempre tiene una demanda nueva y esa tregua que tanto esperas parece no llegar nunca.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "pan-right"
  },
  {
   "ai": "A single sunbeam cutting through a window and illuminating thousands of dust particles suspended in the air above a wooden floor, quiet golden haze, the present moment made visible, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "dust sunbeam window",
   "text": "Mientras esperas ese escenario ideal, los años pasan y tú sigues quedando en el último lugar de tus prioridades cotidianas. Te acostumbras a vivir a medias, acumulando un vacío que intentas llenar con la promesa de un futuro tranquilo que siempre se desplaza.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "pan-left"
  },
  {
   "ai": "A set of house keys dropping onto an entryway console table beside a mail pile, motion blur frozen mid-fall, ordinary everyday arrival, warm afternoon light through frosted glass, real life happening now, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "keys falling table",
   "text": "Los estoicos enseñaban que la verdadera sabiduría consiste en actuar con virtud en medio de las circunstancias reales que nos tocan vivir. No esperes el silencio absoluto; reclama hoy mismo cinco minutos de paz en medio del ruido, respira hondo y haz algo pequeño por ti.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman pausing mid-step in her kitchen, eyes closed, one hand resting on the counter, taking a single deep breath amid the untidy normalcy of daily life, soft window light, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "kitchen pause breath",
   "text": "Tu vida no ocurre en el mañana ideal, sino en este preciso instante que tienes la gracia de habitar.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "pan-right"
  },
  {
   "ai": "A set of house keys dropping onto an entryway console table beside a mail pile, motion blur frozen mid-fall, ordinary everyday arrival, warm afternoon light through frosted glass, real life happening now, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "dust sunbeam window",
   "text": "Empieza a cuidarte en medio del desorden, porque la idea de que algún día tendrás el tiempo y el silencio perfectos para ocuparte de ti es una ilusión.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "zoom-out"
  },
  {
   "ai": "A woman pausing mid-step in her kitchen, eyes closed, one hand resting on the counter, taking a single deep breath amid the untidy normalcy of daily life, soft window light, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "keys falling table",
   "text": "Si deseas reclamar tu presente hoy, dale me gusta, compártelo y sígueme para inspirarte.",
   "img_style": "",
   "img_seed": 5333,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb10-promesas-que-te-rompes",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A hand closing a paper agenda gently but firmly after writing a single commitment inside, pen resting across the cover, warm desk light, quiet promise made to oneself, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing agenda journal",
   "text": "Cuando te prometes algo y lo cancelas para atender a otros, pierdes un poco de confianza en tu propia palabra.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "zoom-in"
  },
  {
   "ai": "Lateral view of a woman in her fifties lacing comfortable walking shoes by the front door, ready to keep a small promise to herself, morning light across the entryway tiles, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "lacing walking shoes",
   "text": "Te prometiste que esta tarde saldrías a caminar, que apagarías la computadora temprano o que tendrías un espacio para descansar. Pero bastó una llamada de última hora o un favor menor para que dejaras tus planes de lado y acudieras a resolver lo ajeno.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "pan-right"
  },
  {
   "ai": "Hands watering a small green plant with a copper watering can, delicate streams catching the light, soil darkening slowly, consistent small care, bright windowsill scene, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "watering small plant",
   "text": "Cada vez que te postergas de esta manera, le envías a tu mente el mensaje subconsciente de que tus necesidades no son importantes. Con el tiempo, experimentas una falta de autoconfianza y una apatía profunda, sintiendo que tu vida ya no te pertenece a ti.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "pan-left"
  },
  {
   "ai": "A hand closing a paper agenda gently but firmly after writing a single commitment inside, pen resting across the cover, warm desk light, quiet promise made to oneself, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing agenda journal",
   "text": "La psicología del desarrollo señala que la autoestima se alimenta de la coherencia entre lo que decidimos hacer y lo que finalmente hacemos por nosotras. Empieza a tratar las promesas que te haces a ti misma con el mismo rigor y respeto con el que tratas tus compromisos laborales o familiares.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "zoom-in"
  },
  {
   "ai": "Lateral view of a woman in her fifties lacing comfortable walking shoes by the front door, ready to keep a small promise to herself, morning light across the entryway tiles, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "lacing walking shoes",
   "text": "Cumplirte es un acto de justicia y una forma de honrar el diseño único con el que fuiste creada para vivir.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "pan-right"
  },
  {
   "ai": "A hand closing a paper agenda gently but firmly after writing a single commitment inside, pen resting across the cover, warm desk light, quiet promise made to oneself, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "watering small plant",
   "text": "Aprende a sostener tu palabra contigo misma, porque cuando te prometes algo y lo cancelas para atender a otros, pierdes un poco de confianza en ti.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "zoom-out"
  },
  {
   "ai": "Lateral view of a woman in her fifties lacing comfortable walking shoes by the front door, ready to keep a small promise to herself, morning light across the entryway tiles, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing agenda journal",
   "text": "Si estás lista para cumplirte tus promesas, dale me gusta, compártelo y sígueme.",
   "img_style": "",
   "img_seed": 5370,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb11-tu-hogar-y-tu-mente",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A hand sweeping old papers and clutter off a wooden table leaving only a single simple vase with one flower, dramatic before-and-after clarity, clean surface emerging, bright natural light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "clearing papers table vase",
   "text": "Una mente saturada suele reflejarse en espacios llenos de objetos que ya no cumplen ninguna función en tu vida.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "zoom-in"
  },
  {
   "ai": "A sheer white curtain billowing softly in a gentle breeze inside a spare uncluttered room, slow graceful movement, airy negative space, calm minimal interior bathed in daylight, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "white curtain breeze",
   "text": "Llegas a casa buscando descanso pero te encuentras con repisas colmadas, ropa amontonada y cajones que apenas cierran por el exceso de cosas acumuladas. Sin darte cuenta, tu entorno físico se convierte en un recordatorio constante de decisiones postergadas y tareas pendientes.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "pan-right"
  },
  {
   "ai": "Close-up of a hand lighting a small candle wick on a freshly cleared shelf, tiny flame blooming, wax and matches nearby, warm glow against tidy surfaces, quiet ritual of order, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "lighting candle hand",
   "text": "Esta sobrecarga visual impide que tu cerebro entre en un estado de relajación profunda al final del día, manteniéndote en alerta constante. Te sientes abrumada en tu propio espacio, como si la casa misma te exigiera un esfuerzo constante que ya no tienes energía para dar.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "pan-left"
  },
  {
   "ai": "A hand sweeping old papers and clutter off a wooden table leaving only a single simple vase with one flower, dramatic before-and-after clarity, clean surface emerging, bright natural light, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "clearing papers table vase",
   "text": "El bienestar psicológico está profundamente ligado a la armonía del espacio que habitamos y cuidamos con esmero. Dedica quince minutos a despejar una sola superficie de tu hogar, soltando aquello que ya no sirve con gratitud por la etapa en que te acompañó.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "zoom-in"
  },
  {
   "ai": "A sheer white curtain billowing softly in a gentle breeze inside a spare uncluttered room, slow graceful movement, airy negative space, calm minimal interior bathed in daylight, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "white curtain breeze",
   "text": "Tu casa debe ser un templo de paz y un reflejo de la gracia que deseas experimentar en tu interior.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "pan-right"
  },
  {
   "ai": "A hand sweeping old papers and clutter off a wooden table leaving only a single simple vase with one flower, dramatic before-and-after clarity, clean surface emerging, bright natural light, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "lighting candle hand",
   "text": "Haz espacio para que tu mente respire, porque una mente saturada suele reflejarse en espacios llenos de objetos que ya no te sirven.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "zoom-out"
  },
  {
   "ai": "A sheer white curtain billowing softly in a gentle breeze inside a spare uncluttered room, slow graceful movement, airy negative space, calm minimal interior bathed in daylight, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "clearing papers table vase",
   "text": "Si buscas crear un refugio de paz en casa, dale me gusta, compártelo y sígueme.",
   "img_style": "",
   "img_seed": 5407,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb12-cargar-con-dolores-ajenos",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Two mature hands loosely interlaced resting over a lap in a gesture of surrender and release, knuckles soft not clenched, warm low light, fabric of a simple skirt, letting go of what was never hers to carry, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hands folded lap",
   "text": "Confundir el amor con la responsabilidad de salvar a todo el mundo terminará por desgastar tu propia salud.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind standing at a lookout, watching the sun sink slowly toward the horizon in orange and rose layers, wind moving her hair gently, vast sky, handing over the day, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman horizon sunset",
   "text": "Asumes los problemas de tus hijos adultos, los dilemas de tu pareja o las tristezas de tus amigas como si fueran batallas personales que debes resolver tú sola. Te pasas las noches en vela pensando en soluciones para situaciones ajenas sobre las cuales no tienes ningún control real.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "pan-right"
  },
  {
   "ai": "Clear stream of water running freely over smooth rounded river stones, sparkling refractions, close macro detail, cool natural light, water finding its way without effort, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "stream smooth stones",
   "text": "Al actuar como el salvador de todos, les robas a los demás la oportunidad de aprender de sus propias dificultades y de madurar en el proceso. Mientras tanto, tú te desgasgatas física y emocionalmente, sintiéndote exhausta y resentida por cargar con un peso que nunca te correspondió.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "pan-left"
  },
  {
   "ai": "Two mature hands loosely interlaced resting over a lap in a gesture of surrender and release, knuckles soft not clenched, warm low light, fabric of a simple skirt, letting go of what was never hers to carry, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hands folded lap",
   "text": "El verdadero amor sabe acompañar con paciencia sin necesidad de controlar el destino o las decisiones de las personas que amamos. Aprende a entregar a tus seres queridos en manos de su Creador, confiando en que cada uno tiene su propio camino de aprendizaje y crecimiento.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind standing at a lookout, watching the sun sink slowly toward the horizon in orange and rose layers, wind moving her hair gently, vast sky, handing over the day, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman horizon sunset",
   "text": "Tu misión es amar y servir desde la paz, no sustituir la voluntad ni el esfuerzo de los demás.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "pan-right"
  },
  {
   "ai": "Two mature hands loosely interlaced resting over a lap in a gesture of surrender and release, knuckles soft not clenched, warm low light, fabric of a simple skirt, letting go of what was never hers to carry, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "stream smooth stones",
   "text": "Acompaña con amor pero suelta el control, porque confundir el amor con la responsabilidad de salvar a todo el mundo terminará por desgastar tu salud.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "zoom-out"
  },
  {
   "ai": "Woman seen from behind standing at a lookout, watching the sun sink slowly toward the horizon in orange and rose layers, wind moving her hair gently, vast sky, handing over the day, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hands folded lap",
   "text": "Si necesitas aprender a soltar con amor, dale me gusta, compártelo y sígueme para caminar juntas.",
   "img_style": "",
   "img_seed": 5444,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb13-ayudar-sin-quemarte",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Two mature hands holding a handmade ceramic bowl filled with clear water, calm and steadiness in the grip, faces absent, soft window light rippling reflections across the water surface, giving from a full place, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hands ceramic bowl water",
   "text": "Hay una gran diferencia entre servir con amor y desgastarte por miedo a no ser querida.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman in profile walking slowly through a quiet garden path at dusk, pausing to touch a green leaf between finger and thumb, low golden backlight, unhurried generous presence, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "garden walk touching leaf",
   "text": "A menudo dices que sí a favores, compromisos y cargas ajenas, creyendo que tu deber es resolver la vida de todos a costa de tu propia paz. Te convences de que ser una persona generosa y de fe significa estar siempre disponible, incluso cuando sientes un vacío inmenso y un cansancio que te consume por dentro.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "pan-right"
  },
  {
   "ai": "An open notebook resting on a wooden desk with a fountain pen lying beside measured handwritten lines, warm lamp pool of light, reflective pause after honest work, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "open notebook pen desk",
   "text": "Pero el verdadero servicio nace de la abundancia de tu corazón, no del temor al rechazo o a la soledad. Cuando te entregas hasta quedar completamente vacía, no estás ofreciendo un amor genuino, sino un sacrificio invisible que apaga tu propia luz y te aleja de tu propósito.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "pan-left"
  },
  {
   "ai": "Two mature hands holding a handmade ceramic bowl filled with clear water, calm and steadiness in the grip, faces absent, soft window light rippling reflections across the water surface, giving from a full place, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hands ceramic bowl water",
   "text": "Para sanar este hábito, aplica la pregunta de la intención honesta antes de aceptar cualquier carga que no te corresponda. Detente un segundo, respira y pregúntate en silencio: '¿Ayudo porque realmente quiero y puedo hacerlo, o porque temo que me dejen de valorar si digo que no?'.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman in profile walking slowly through a quiet garden path at dusk, pausing to touch a green leaf between finger and thumb, low golden backlight, unhurried generous presence, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "garden walk touching leaf",
   "text": "Servir al prójimo es un camino hermoso y un propósito sagrado, pero recuerda que el amor bien ordenado nunca te exigirá tu propia destrucción.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "pan-right"
  },
  {
   "ai": "Two mature hands holding a handmade ceramic bowl filled with clear water, calm and steadiness in the grip, faces absent, soft window light rippling reflections across the water surface, giving from a full place, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "open notebook pen desk",
   "text": "Porque para dar luz a los que amas, primero tu propia lámpara necesita aceite: hay una gran diferencia entre servir con amor y desgastarte por miedo a no ser querida.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "zoom-out"
  },
  {
   "ai": "A woman in profile walking slowly through a quiet garden path at dusk, pausing to touch a green leaf between finger and thumb, low golden backlight, unhurried generous presence, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hands ceramic bowl water",
   "text": "Si quieres aprender a cuidar de los tuyos sin perder tu propia paz, dale me gusta, compártelo y sígueme para más reflexiones honestas.",
   "img_style": "",
   "img_seed": 5481,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb14-el-cuerpo-avisa-antes",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Close-up of a steaming coffee mug on a rustic wooden table held by a mature hand with slightly tense knuckles, subtle strain visible in the grip, morning light revealing body tension we ignore, shallow depth of field, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "coffee mug tense hand",
   "text": "Date cuenta de cómo tienes los dientes apretados en este mismo instante.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind seated before a wide bright window, consciously lowering her shoulders and exhaling slowly, soft natural light wrapping the room, body finally being listened to, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "shoulders relaxing window",
   "text": "No es un cansancio repentino el que te tumba al final del día; tu cuerpo lleva horas, quizás días, intentando hablarte a través de la tensión acumulada en tus hombros y esa respiración tan corta que casi no notas. Vivimos tan desconectadas de nuestro propio templo físico que solo nos detenemos cuando el dolor o el agotamiento extremo nos obligan a parar por completo.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "pan-right"
  },
  {
   "ai": "A hand gently silencing the alarm on a smartphone laid face up on a hardcover book, fingertip pausing on the screen, quiet bedside light, first small check-in of the day, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "silencing phone alarm",
   "text": "Es muy fácil decirte que mañana estarás mejor o que solo es una racha difícil que debes aguantar. Sin embargo, ignorar estos avisos silenciosos no te hace más fuerte, solo acumula una factura física y emocional que tu salud tendrá que pagar tarde o temprano, casi sin que te des cuenta.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "pan-left"
  },
  {
   "ai": "Close-up of a steaming coffee mug on a rustic wooden table held by a mature hand with slightly tense knuckles, subtle strain visible in the grip, morning light revealing body tension we ignore, shallow depth of field, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "coffee mug tense hand",
   "text": "La solución no requiere que te retires a un templo de meditación, sino que implementes el método de los tres escaneos de treinta segundos. Tres veces al día, haz una pausa breve para revisar tres puntos específicos: afloja conscientemente la mandíbula, baja los hombros liberando el peso y respira profundo inflando el abdomen.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "zoom-in"
  },
  {
   "ai": "Woman seen from behind seated before a wide bright window, consciously lowering her shoulders and exhaling slowly, soft natural light wrapping the room, body finally being listened to, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "shoulders relaxing window",
   "text": "Este pequeño hábito diario regula tu sistema nervioso al instante y te devuelve el control de tu energía vital.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "pan-right"
  },
  {
   "ai": "Close-up of a steaming coffee mug on a rustic wooden table held by a mature hand with slightly tense knuckles, subtle strain visible in the grip, morning light revealing body tension we ignore, shallow depth of field, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "silencing phone alarm",
   "text": "Haz este ejercicio ahora mismo y notarás el alivio; y recuerda: date cuenta de cómo tienes los dientes apretados en este mismo instante.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "zoom-out"
  },
  {
   "ai": "Woman seen from behind seated before a wide bright window, consciously lowering her shoulders and exhaling slowly, soft natural light wrapping the room, body finally being listened to, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "coffee mug tense hand",
   "text": "Si este video te ha ayudado a respirar mejor, dale me gusta, compártelo con alguien que lo necesite y sígueme para cuidar de ti sin culpas.",
   "img_style": "",
   "img_seed": 5518,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb15-dejar-tareas-a-medias",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A woman seen from behind walking away from the kitchen sink where a neat row of clean dishes dries, leaving the task genuinely unfinished yet enough, soft overhead evening light, honest domestic realism, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "walking away kitchen sink",
   "text": "Irse a dormir con platos en el fregadero no te hace descuidada, te hace una persona que sabe elegir sus batallas.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "zoom-in"
  },
  {
   "ai": "A hand closing a bedroom door with slow gentleness, the corridor dim beyond, choosing rest over finishing everything, warm lamp glow spilling across floorboards, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing door gently",
   "text": "Te exiges mantener la casa impecable, responder cada mensaje de inmediato y cumplir con todas las demandas externas antes de permitirte un respiro. Te has convertido en esclava de un estándar de limpieza y orden que te deja sin energía para disfrutar de tu propia vida.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "pan-right"
  },
  {
   "ai": "Steam rising from a hot herbal infusion on a small wooden nightstand beside a turned-down bed, bedside lamp halo, close intimate detail, permission to stop for today, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tea nightstand steam",
   "text": "Esta autoexigencia desmedida te genera un estado constante de irritabilidad y cansancio, donde las tareas del hogar se sienten como una condena. Terminas el día de mal humor, sintiendo que eres una máquina de trabajar en lugar de una mujer que merece disfrutar de su hogar.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "pan-left"
  },
  {
   "ai": "A woman seen from behind walking away from the kitchen sink where a neat row of clean dishes dries, leaving the task genuinely unfinished yet enough, soft overhead evening light, honest domestic realism, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "walking away kitchen sink",
   "text": "El bienestar real consiste en aprender a priorizar tu paz mental y tu descanso por encima de las expectativas del orden perfecto. Permítete dejar algunas tareas pendientes para mañana cuando sientas que tu cuerpo ya no da más, reconociendo tus límites con amabilidad.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "zoom-in"
  },
  {
   "ai": "A hand closing a bedroom door with slow gentleness, the corridor dim beyond, choosing rest over finishing everything, warm lamp glow spilling across floorboards, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "closing door gently",
   "text": "Tu valor personal no se mide por la cantidad de platos limpios, sino por el amor y la paciencia con la que cuidas de ti.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "pan-right"
  },
  {
   "ai": "A woman seen from behind walking away from the kitchen sink where a neat row of clean dishes dries, leaving the task genuinely unfinished yet enough, soft overhead evening light, honest domestic realism, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "tea nightstand steam",
   "text": "Elige tu paz por encima de las tareas, porque irse a dormir con pendientes no te hace descuidada, te hace una persona que sabe elegir sus batallas.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "zoom-out"
  },
  {
   "ai": "A hand closing a bedroom door with slow gentleness, the corridor dim beyond, choosing rest over finishing everything, warm lamp glow spilling across floorboards, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "walking away kitchen sink",
   "text": "Si deseas vivir con menos exigencias externas, dale me gusta, compártelo y sígueme.",
   "img_style": "",
   "img_seed": 5555,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb16-el-exceso-de-ruido-cotidiano",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A thumb pressing the power button of a television remote, screen glow dying in the background leaving soft darkness, deliberate pause movement, living room settling into silence, warm lamp contrast, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "turning off tv remote",
   "text": "Si necesitas tener la televisión o un podcast de fondo todo el día, estás huyendo de tu propio silencio.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "zoom-in"
  },
  {
   "ai": "Lateral view of a woman standing in a simply decorated corner of her home, a chair, a plant, framed prints, considering the quiet she has built, gentle window daylight, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "simple quiet corner home",
   "text": "Llenas cada espacio vacío de tu jornada con ruidos, música, noticias o videos para evitar encontrarte con tus propios pensamientos. Creemos que la distracción constante es normal, pero en realidad es una forma sutil de acallar la incomodidad o la tristeza que llevamos dentro.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "pan-right"
  },
  {
   "ai": "A closed hardcover book resting peacefully on the arm of a comfortable upholstered armchair beside a steaming cup, reading finished for tonight, warm lamplight, stillness as company, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "book armchair lamp",
   "text": "La consecuencia de este ruido permanente es una saturación cognitiva que te deja exhausta, ansiosa y desconectada de tus verdaderas necesidades emocionales. Te resulta insoportable quedarte a solas contigo misma, perdiendo la capacidad de escuchar lo que tu alma intenta decirte.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "pan-left"
  },
  {
   "ai": "A thumb pressing the power button of a television remote, screen glow dying in the background leaving soft darkness, deliberate pause movement, living room settling into silence, warm lamp contrast, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "turning off tv remote",
   "text": "La tradición de la filosofía contemplativa nos enseña que el silencio no es un vacío incómodo, sino un espacio sagrado de restauración y autoconocimiento. Regálate al menos quince minutos al día de absoluto silencio, permitiendo que tus pensamientos se acomoden de forma natural y pacífica.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "zoom-in"
  },
  {
   "ai": "Lateral view of a woman standing in a simply decorated corner of her home, a chair, a plant, framed prints, considering the quiet she has built, gentle window daylight, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "simple quiet corner home",
   "text": "En la quietud es donde logramos escuchar la voz suave de la gracia que nos recuerda quiénes somos realmente.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "pan-right"
  },
  {
   "ai": "A thumb pressing the power button of a television remote, screen glow dying in the background leaving soft darkness, deliberate pause movement, living room settling into silence, warm lamp contrast, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "book armchair lamp",
   "text": "Atrévete a habitar tu quietud hoy, porque si necesitas ruido de fondo todo el día, estás huyendo de tu propio silencio.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "zoom-out"
  },
  {
   "ai": "Lateral view of a woman standing in a simply decorated corner of her home, a chair, a plant, framed prints, considering the quiet she has built, gentle window daylight, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "turning off tv remote",
   "text": "Si buscas recuperar la calma en tu día a día, dale me gusta, compártelo y sígueme para meditar juntas.",
   "img_style": "",
   "img_seed": 5592,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb17-esperar-que-otros-cambien",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "An open hand releasing a handful of fine sand, grains escaping freely between the fingers in golden backlit streams, impossible to hold, dark warm background, close cinematic detail, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "sand falling open hand",
   "text": "Sufrimos más por lo que esperamos de las personas que por lo que esas personas realmente hacen o dicen.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "zoom-in"
  },
  {
   "ai": "Profile of a woman at her window with the faintest peaceful smile watching the street below, arms relaxed, accepting others as they are, soft silver morning light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman window smile",
   "text": "Pasas la vida esperando que tu pareja sea más detallista, que tu familia te valide o que tus amigas actúen exactamente como tú lo harías. Esta expectativa constante se convierte en una fuente inagotable de decepciones y discusiones que desgastan tus relaciones más queridas.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "pan-right"
  },
  {
   "ai": "Two steaming tea cups set comfortably far apart on a long wooden table, generous space between them, warm afternoon light, closeness that does not crowd, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "two tea cups space",
   "text": "Al condicionar tu paz interior a la conducta de los demás, les entregas el control absoluto sobre tu estado de ánimo y tu felicidad. Te sientes frustrada y atrapada en un ciclo de reclamos silenciosos que solo genera distancia emocional y amargura en tu corazón.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "pan-left"
  },
  {
   "ai": "An open hand releasing a handful of fine sand, grains escaping freely between the fingers in golden backlit streams, impossible to hold, dark warm background, close cinematic detail, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "sand falling open hand",
   "text": "Los sabios estoicos explicaban que no podemos controlar las acciones de los demás, sino únicamente la forma en que decidimos reaccionar ante ellas. Aprende a aceptar a las personas tal como son hoy, amándolas desde su realidad imperfecta y liberándolas de la carga de cumplir tus expectativas.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "zoom-in"
  },
  {
   "ai": "Profile of a woman at her window with the faintest peaceful smile watching the street below, arms relaxed, accepting others as they are, soft silver morning light, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "woman window smile",
   "text": "Al soltar la necesidad de cambiarlos, recuperas tu propia paz y la libertad de decidir cómo deseas vivir tu vida.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "pan-right"
  },
  {
   "ai": "An open hand releasing a handful of fine sand, grains escaping freely between the fingers in golden backlit streams, impossible to hold, dark warm background, close cinematic detail, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "two tea cups space",
   "text": "Libera a los demás de tus expectativas, porque sufrimos más por lo que esperamos de las personas que por lo que ellas realmente hacen.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "zoom-out"
  },
  {
   "ai": "Profile of a woman at her window with the faintest peaceful smile watching the street below, arms relaxed, accepting others as they are, soft silver morning light, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "sand falling open hand",
   "text": "Si estás lista para relacionarte desde la libertad, dale me gusta, compártelo y sígueme.",
   "img_style": "",
   "img_seed": 5629,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb18-la-prisa-silenciosa",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A hand placing a pen down on a desk and the open palm resting flat on the wood in deliberate stillness, shoulders implied lowering, warm afternoon light raking across the grain, transition from rush to pause, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "palm resting desk pen",
   "text": "Pasar directamente de una tarea exigente a otra sin un minuto de pausa es una agresión silenciosa a tu cuerpo.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman seated in a chair doing a slow gentle neck and shoulder stretch, eyes closed, chin tilted, unwinding the invisible hurry held in the body, soft indoor daylight, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "neck stretch chair",
   "text": "Terminas de limpiar y de inmediato te pones a cocinar, o cierras una reunión de trabajo para empezar a responder mensajes familiares sin detenerte. Vivimos saltando de una actividad a otra como si el tiempo fuera un recurso que debemos exprimir hasta el último segundo.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "pan-right"
  },
  {
   "ai": "Water filling a clear glass in slow motion, light refracting through the rising level, afternoon sun glinting off the surface, simple slowness made beautiful, close macro framing, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "glass filling water light",
   "text": "Esta prisa constante mantiene activada la respuesta de estrés en tu cuerpo, dejándote con la sensación de estar siempre fatigada y sin aire. Tu mente se satura y terminas cometiendo pequeños errores que te frustran, sintiendo que el día es un maratón que nunca termina.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "pan-left"
  },
  {
   "ai": "A hand placing a pen down on a desk and the open palm resting flat on the wood in deliberate stillness, shoulders implied lowering, warm afternoon light raking across the grain, transition from rush to pause, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "palm resting desk pen",
   "text": "La psicología de la regulación emocional nos enseña la importancia de crear transiciones conscientes entre las actividades del día. Detente apenas dos minutos entre una tarea y otra, estira tus brazos, respira profundamente y permite que tu mente registre que una etapa ha concluido.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman seated in a chair doing a slow gentle neck and shoulder stretch, eyes closed, chin tilted, unwinding the invisible hurry held in the body, soft indoor daylight, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "neck stretch chair",
   "text": "Este pequeño espacio de amortiguación es el secreto para vivir el día con gracia y preservar tu energía intacta.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "pan-right"
  },
  {
   "ai": "A hand placing a pen down on a desk and the open palm resting flat on the wood in deliberate stillness, shoulders implied lowering, warm afternoon light raking across the grain, transition from rush to pause, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "glass filling water light",
   "text": "Regálate un momento de transición hoy, porque pasar de una tarea a otra sin pausa es una agresión silenciosa a tu cuerpo.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "zoom-out"
  },
  {
   "ai": "A woman seated in a chair doing a slow gentle neck and shoulder stretch, eyes closed, chin tilted, unwinding the invisible hurry held in the body, soft indoor daylight, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "palm resting desk pen",
   "text": "Si deseas aprender a vivir sin prisa, dale me gusta, compártelo y sígueme para avanzar juntas.",
   "img_style": "",
   "img_seed": 5666,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb19-la-tirania-de-la-multitarea",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "Hands folding a single garment with extreme slowness and care, fingertips aligning the seams precisely, fabric texture in warm raking light, one thing done with full attention, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "folding clothes slow hands",
   "text": "Hacer tres cosas a la vez no te hace más eficiente, solo te asegura hacerlas con la mitad de tu presencia.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman peeling an apple in one long unbroken spiral, gaze fixed entirely on the movement of her hands, kitchen window light, absorbed single-tasking as meditation, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "peeling apple spiral",
   "text": "Intentas responder un mensaje mientras cocinas y escuchas un audio, creyendo que así ahorras tiempo y eres más productiva en tu día. El resultado es que te sientes dispersa, cometes pequeños descuidos y no logras disfrutar plenamente de ninguna de las actividades que realizas.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "pan-right"
  },
  {
   "ai": "Macro detail of a paintbrush being dipped slowly into a glass jar of clean water, color blooming softly from the bristles, bright studio daylight, devotion to a single stroke, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "brush dipping water jar",
   "text": "La multitarea crónica satura tu atención, eleva tus niveles de ansiedad y te desconecta por completo del momento presente que estás viviendo. Al final del día, experimentas una sensación de vacío, como si hubieras estado en todas partes pero en ninguna con verdadera conciencia.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "pan-left"
  },
  {
   "ai": "Hands folding a single garment with extreme slowness and care, fingertips aligning the seams precisely, fabric texture in warm raking light, one thing done with full attention, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "folding clothes slow hands",
   "text": "La investigación en atención demuestra que la calidad de lo que haces depende de la presencia con la que lo haces, no de la cantidad de cosas que abarcas. Elige hacer una sola cosa a la vez con toda tu presencia, entregando tu mente y tu corazón a ese pequeño instante con sencillez.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "zoom-in"
  },
  {
   "ai": "A woman peeling an apple in one long unbroken spiral, gaze fixed entirely on the movement of her hands, kitchen window light, absorbed single-tasking as meditation, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "peeling apple spiral",
   "text": "Al unificar tu atención, disminuye el ruido mental y descubres la paz profunda que se esconde en las acciones ordinarias.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "pan-right"
  },
  {
   "ai": "Hands folding a single garment with extreme slowness and care, fingertips aligning the seams precisely, fabric texture in warm raking light, one thing done with full attention, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "brush dipping water jar",
   "text": "Dedícate por completo a lo que haces hoy, porque hacer tres cosas a la vez no te hace más eficiente, solo te resta presencia.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "zoom-out"
  },
  {
   "ai": "A woman peeling an apple in one long unbroken spiral, gaze fixed entirely on the movement of her hands, kitchen window light, absorbed single-tasking as meditation, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "folding clothes slow hands",
   "text": "Si valoras la belleza de la presencia, dale me gusta, compártelo y sígueme para más reflexiones.",
   "img_style": "",
   "img_seed": 5703,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
 "name": "fb20-paciencia-con-tu-proceso",
 "bgm": True,
 "voices": [
  "male"
 ],
 "scenes": [
  {
   "ai": "A weathered hand stroking the rough furrowed bark of an ancient park tree in slow recognition, moss and texture detail, filtered green-gold canopy light, respect for slow growth, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hand tree bark moss",
   "text": "Te exiges florecer de inmediato cuando en realidad acabas de pasar por un invierno emocional muy crudo.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "zoom-in"
  },
  {
   "ai": "A single dry leaf lying on the ground being softly covered and uncovered by the passing shadow of a cloud, autumn tones, macro intimacy, seasons that cannot be rushed, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "dry leaf cloud shadow",
   "text": "Quieres sentirte feliz, motivada y llena de energía justo después de haber vivido una pérdida, una decepción o un período de intenso estrés. Te juzgas por tu falta de entusiasmo y te presionas para estar bien, ignorando que tu cuerpo y tu alma necesitan tiempo para sanar.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "pan-right"
  },
  {
   "ai": "Woman in profile gazing at a soft gray sky from a park bench, coat collar up, expression of profound peace and acceptance, gentle diffused light, trusting her own season, slightly dimmer mood, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "bench gray sky peace",
   "text": "Esta impaciencia constante contigo misma sabotea tu proceso de recuperación natural y prolonga tu estado de tristeza y frustración interna. Te conviertes en tu juez más severo, exigiéndote una primavera inmediata en una tierra que todavía necesita descansar y procesar el frío.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "pan-left"
  },
  {
   "ai": "A weathered hand stroking the rough furrowed bark of an ancient park tree in slow recognition, moss and texture detail, filtered green-gold canopy light, respect for slow growth, closer alternate angle, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hand tree bark moss",
   "text": "La naturaleza nos enseña con sabiduría que cada estación tiene su propósito y que ninguna flor brota antes de tiempo. Respeta tu invierno emocional con paciencia, sabiendo que el descanso y el recogimiento son necesarios para que la vida vuelva a brotar con fuerza.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "zoom-in"
  },
  {
   "ai": "A single dry leaf lying on the ground being softly covered and uncovered by the passing shadow of a cloud, autumn tones, macro intimacy, seasons that cannot be rushed, closer alternate angle, brighter warmer light, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "dry leaf cloud shadow",
   "text": "Confía en el Creador que sostiene tus tiempos, sabiendo que tu primavera llegará cuando tu alma esté lista para recibirla.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "pan-right"
  },
  {
   "ai": "A weathered hand stroking the rough furrowed bark of an ancient park tree in slow recognition, moss and texture detail, filtered green-gold canopy light, respect for slow growth, wider peaceful shot echoing the opening, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "bench gray sky peace",
   "text": "Sé paciente con tu propia restauración, porque te exiges florecer de inmediato cuando apenas estás saliendo de un invierno emocional.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "zoom-out"
  },
  {
   "ai": "A single dry leaf lying on the ground being softly covered and uncovered by the passing shadow of a cloud, autumn tones, macro intimacy, seasons that cannot be rushed, warm inviting wide shot, different angle, tighter framing, photorealistic cinematic photography, emotional and warm atmosphere, realistic adult person, natural facial expression, soft dramatic lighting, muted warm colors, shallow depth of field, premium film still, vertical 9:16, no text, no letters, no subtitles, no logos, no watermark",
   "q": "hand tree bark moss",
   "text": "Si necesitas un espacio de paciencia y amor, dale me gusta, compártelo y sígueme para sanar juntas.",
   "img_style": "",
   "img_seed": 5740,
   "motion": "zoom-out",
   "static_text": [
    "DALE ME GUSTA",
    "COMPARTE",
    "SÍGUEME"
   ],
   "static_size": 90
  }
 ]
})

VIDEOS.append({
    "name": "cuerpo-habla",
    "bgm": True,
    "bright": True,
    "voices": ["male"],
    "scenes": [
        {"ai": "Medium side profile of a Latin American woman in her fifties standing in her bright kitchen surrounded by lush potted plants along the windowsill, fingertips gently noticing the tension at her own jaw, soft early morning light filtering through green leaves, terracotta pots and sage tones, calm everyday moment, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
         "q": "woman profile kitchen window",
         "text": "Suelta los dientes ahora mismo y relaja la mandíbula.",
         "img_style": "", "img_seed": 901, "motion": "zoom-in"},
        {"ai": "Close-up of a womans hands gently pressing and then releasing the tension of her own shoulder through a soft coral sweater, framed by vibrant green houseplants on a sunny windowsill behind her, a trailing pothos entering the foreground edge, bright balanced daylight, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
         "q": "relaxing shoulders woman",
         "text": "Esa tensión es tu cuerpo pidiendo un respiro.",
         "rate": "-20%", "boom": True,
         "static_text": ["ESA TENSIÓN", "ES TU CUERPO", "PIDIENDO UN RESPIRO"],
         "static_size": 96,
         "img_style": "", "img_seed": 902, "motion": "pan-right",
         "trans": {"style": "flash", "dur": 0.3}},
        {"ai": "Hands resting open on the lap of a woman seated beside a wooden shelf full of thriving green houseplants and one blooming pink flower in a terracotta pot, relaxed fingers during a short mindful pause, warm natural daylight from a bright window, cozy living room full of life, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
         "q": "hands resting lap pause",
         "text": "Tres chequeos al día de treinta segundos: observa la mandíbula, baja los hombros y respira profundo. No es meditar, es registrar cómo estás.",
         "img_style": "", "img_seed": 903, "motion": "zoom-in"},
        {"ai": "A woman wearing a casual knit cardigan seen from behind walking toward a large bright window lined with flourishing potted herbs and flowering red geraniums on the sill, her figure evenly lit by soft side daylight, sheer white curtains moving gently, lush balcony greenery visible beyond the glass, feeling of release, photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, realistic human expression, premium lifestyle film still, vertical 9:16",
         "q": "walking window tea back view",
         "text": "La próxima vez que suba la tensión... ya sabes: suelta.",
         "img_style": "", "img_seed": 904, "motion": "zoom-out"},
        {"reuse_img": True,
         "text": "Y si esto te hizo sentido, suscríbete.",
         "static_text": ["SI ESTO TE HIZO SENTIDO", "SUSCRÍBETE"],
         "static_size": 100,
         "motion": "zoom-in"},
    ],
})


SFX = (", photorealistic cinematic lifestyle photography, bright natural daylight, balanced realistic exposure, authentic skin tones, rich but natural colors, natural color variation, contemporary editorial photography, authentic everyday environment, subtle cinematic depth, premium lifestyle film still, vertical 9:16")

VIDEOS.append({
    "name": "y-manana-largo",
    "bgm": True,
    "bright": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"reuse_img": True,
         "text": "¿Y mañana qué?",
         "motion": "zoom-in"},
        {"ai": "An empty ceramic cup on a wooden kitchen table beside a window with cool early light, an unoccupied chair nearby, a small potted fern on the sill, quiet stillness of an unfinished morning" + SFX,
         "text": "A veces no es que no tengas sueños.",
         "img_seed": 951, "motion": "zoom-in"},
        {"ai": "A worn backpack resting against an apartment door at soft dawn, keys on a small table beside it, muted blue morning tones through a frosted window, the repetition of another day about to begin" + SFX,
         "text": "Es que hace demasiado tiempo que solo pensás en llegar al día siguiente. En levantarte. En cumplir. En resolver lo urgente.",
         "img_seed": 952, "motion": "pan-right"},
        {"ai": "A warm living room at night with one lamp lit, a folded blanket on an armchair and a steaming cup of tea on a side table, gentle amber calm after a long day, plants resting in dim background" + SFX,
         "text": "En que nadie necesite nada de vos. En llegar a la noche y, por fin, poder descansar.",
         "img_seed": 953, "motion": "zoom-out"},
        {"ai": "A wall calendar with small crossed-out days beside a stack of notebooks on a desk, soft even daylight from a side window, quiet accumulation of passing time" + SFX,
         "text": "Y así pasan los días. Y un día alguien te pregunta: ¿Qué querés hacer con tu vida?",
         "img_seed": 954, "motion": "zoom-in"},
        {"ai": "A tidy writing desk with an open blank notebook and a pen laid down diagonally, afternoon light falling across the pages, a green plant blurred in foreground edge, question hanging in stillness" + SFX,
         "text": "Y no sabés qué responder. No porque no quieras nada.",
         "img_seed": 955, "motion": "pan-left"},
        {"ai": "A rain-streaked window seen from inside with a small thriving plant on the sill, soft grey-blue daylight, droplets sliding down the glass, interior warmth against outside weather" + SFX,
         "text": "Sino porque hace mucho que nadie te pregunta eso.",
         "img_seed": 956, "motion": "zoom-in"},
        {"ai": "A wide train platform at dawn seen from afar, one distant person from behind standing small in frame waiting, soft grey morning light over empty rails, sense of routine survival without detail of the figure" + SFX,
         "text": "Cuando una persona pasa demasiado tiempo sobreviviendo, el futuro deja de ser un lugar que imagina. Se convierte en algo que simplemente tiene que alcanzar.",
         "img_seed": 957, "motion": "zoom-out"},
        {"ai": "Three identical coffee cups arranged in a row on an office desk near a window, each at a different stage of cooling, neutral daylight, visual metaphor of identical repeating days" + SFX,
         "text": "Otro lunes. Otro mes. Otro año.",
         "img_seed": 958, "motion": "pan-right"},
        {"ai": "The end of a home hallway toward a slightly open door letting in bright daylight, warm wood floor, a potted plant halfway along the wall, invitation to move from dimness toward light" + SFX,
         "text": "Quizás por eso sentís que estás estancada. Pero hay una diferencia enorme entre no tener un camino y estar demasiado cansada para poder verlo.",
         "img_seed": 959, "motion": "zoom-in"},
        {"ai": "A closed wooden keepsake box resting on a high shelf with soft dust motes in a slanted beam of afternoon light, books stacked beside it, something precious stored away and waiting" + SFX,
         "text": "Tal vez no perdiste tus sueños. Tal vez quedaron debajo de todas las cosas que tuviste que hacer para seguir adelante.",
         "img_seed": 960, "motion": "zoom-in"},
        {"ai": "One hand gently opening an old notebook on a table, a pressed dried flower marking the page, simple single-hand action clearly separated from objects, warm side daylight" + SFX,
         "text": "No necesitás descubrir ahora mismo qué querés hacer con los próximos diez años. Podés empezar con algo mucho más pequeño. Preguntarte:",
         "img_seed": 961, "motion": "zoom-in"},
        {"ai": "A breakfast tray with fresh fruit and bread beside a sunlit window opening to greenery, fresh flowers in a jar on the sill, generous morning light filling the room, an imagined kinder morning" + SFX,
         "text": "¿Qué me gustaría que tuviera mi mañana que hoy no tiene?",
         "img_seed": 962, "motion": "zoom-out"},
        {"ai": "A row of small terracotta pots with new seedlings and vivid red and yellow flowers on a sunny windowsill, rich varied colors, water drops on leaves, life growing again in color" + SFX,
         "text": "Más calma. Más tiempo. Más verdad. Más espacio para mí. Más de eso que alguna vez me hacía sentir viva.",
         "img_seed": 963, "motion": "pan-right"},
        {"ai": "An empty sunlit room seen from inside, its large window fully open with sheer white curtains billowing inward on a soft bright breeze, thriving green potted plants grouped on the wooden floor below the sill, nobody present, expansive airy feeling of openness and permission" + SFX,
         "text": "El futuro no empieza cuando tenés todo resuelto. Empieza cuando volvés a permitirte imaginarlo.",
         "img_seed": 964, "motion": "zoom-in"},
        {"static_text": ["¿Y MAÑANA", "QUÉ?"], "static_size": 130,
         "text": "¿Y mañana qué?",
         "reuse_img": True,
         "motion": "zoom-in"},
        {"reuse_img": True,
         "trans": {"style": "flash", "dur": 0.3},
         "text": "Suscribite, activá la campanita y no te pierdas nada.",
         "static_text": ["SUSCRIBITE,", "ACTIVÁ LA CAMPANITA", "Y NO TE PIERDAS NADA"],
         "static_size": 88,
         "motion": "zoom-in"},
    ],
})

# --- SERIE "¿SABÍAS QUE DIOS...?" — b-roll real de montañas (Pexels) ---
# Frases verificadas contra Catecismo y Biblia (GATE 1 aprobado por el usuario):
# 1: Is 43,1 + CEC "Dios llama a cada uno por su nombre" + Sal 139
# 2: Jr 1,8 "yo estoy con ustedes" · 3: CEC 356 + CEC "Dios es amor"
# 4: CEC "Sólo Dios perdona el pecado" (condicionada al arrepentimiento)
# 5: Jer 29,11 + CEC "vocación a la bienaventuranza" · 6: Mt 6 "Padre que ve en lo secreto"
# 7: Lam 3,23 "se renuevan cada mañana" · 8: Ap 3,20 "junto a la puerta y llamo" (ajustada)
_SABIAS = [
    (4, "¿Sabías que Dios nunca te deja solo y camina siempre a tu lado, "
        "especialmente en tus días más difíciles? "
        "Aprovecha ahora y dile con el corazón: Gracias, Señor, por no soltar mi mano."),
]

# La serie completa ya está definida explícita con escena de CTA aparte
# (5-10); el bucle queda solo para futuros números sin CTA.

# sabias-montana-6 (FB): igual que las demás pero con CTA "Sígueme" en escena
# SEPARADA (punto aparte visual), mismo patrón que sabias-montana-5
VIDEOS.append({
    "name": "sabias-montana-6",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"text": "¿Sabías que Dios siempre está dispuesto a perdonarte y abrazarte cuando "
                 "te arrepientes de corazón? "
                 "Háblale con tus propias palabras y pídele que llene tu alma con su paz.",
         "q": "mountain peaks aerial",
         "img_seed": 5200 + 6,
         "ai": "majestic mountain peaks under bright sky, vertical",
         "motion": "zoom-out"},
        {"text": "Si esto te hizo sentido, sígueme. ¡Bendiciones!",
         "motion": "zoom-in"},
    ],
})

# sabias-montana-5 (YT): CTA "Ayúdame suscribiéndote" en escena SEPARADA
# para que aparezca abajo, en bloque propio (punto aparte visual)
VIDEOS.append({
    "name": "sabias-montana-5",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"text": "¿Sabías que Dios te creó por puro amor y que tu existencia es un "
                 "regalo maravilloso para este mundo? "
                 "Dedícale un momento a tu Creador y reza un Padre Nuestro muy despacio.",
         "q": "mountain lake reflection sunrise",
         "img_seed": 5205,
         "ai": "majestic mountain lake at sunrise, vertical",
         "motion": "zoom-out"},
        {"reuse_img": True,
         "text": "Si esto te hizo sentido, sígueme. ¡Bendiciones!",
         "motion": "zoom-in"},
    ],
})

# sabias-montana-7 (YT): CTA "dale like y suscríbete" en escena SEPARADA,
# mismo patrón que sabias-montana-5/6
VIDEOS.append({
    "name": "sabias-montana-7",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"text": "¿Sabías que Dios tiene un plan hermoso para tu vida y desea tu felicidad "
                 "eterna más que nadie? "
                 "Haz una pequeña pausa y dile: Señor, hágase tu voluntad en mí.",
         "q": "mountain peaks aerial",
         "img_seed": 5200 + 7,
         "ai": "majestic mountain peaks under bright sky, vertical",
         "motion": "zoom-out"},
        {"text": "Si esto te hizo bien, dale like y suscríbete. ¡Bendiciones!",
         "motion": "zoom-in"},
    ],
})

# sabias-montana-8 (YT): CTA "dale like y suscríbete" en escena SEPARADA,
# mismo patrón que sabias-montana-5/6/7
VIDEOS.append({
    "name": "sabias-montana-8",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"text": "¿Sabías que Dios escucha con absoluta atención cada uno de tus suspiros y "
                 "oraciones más silenciosas? "
                 "Entrégale lo que te preocupa hoy con esta oración: Sagrado Corazón de Jesús, en ti confío.",
         "q": "mountain peaks aerial",
         "img_seed": 5200 + 8,
         "ai": "majestic mountain peaks under bright sky, vertical",
         "motion": "zoom-out"},
        {"text": "Si esto te hizo bien, dale like y suscríbete. ¡Bendiciones!",
         "motion": "zoom-in"},
    ],
})

# sabias-montana-9 (FB): CTA "Sígueme" en escena SEPARADA,
# mismo patrón que sabias-montana-5/6/7/8
VIDEOS.append({
    "name": "sabias-montana-9",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"text": "¿Sabías que Dios te regala este día de vida como una nueva oportunidad para "
                 "amar y dejarte amar por Él? "
                 "Mira al cielo un momento y dile una palabra sencilla: Gracias, Dios mío.",
         "q": "mountain peaks aerial",
         "img_seed": 5200 + 9,
         "ai": "majestic mountain peaks under bright sky, vertical",
         "motion": "zoom-out"},
        {"text": "Si esto te hizo sentido, sígueme. ¡Bendiciones!",
         "motion": "zoom-in"},
    ],
})

# sabias-montana-10 (YT): CTA "dale like y suscríbete" en escena SEPARADA,
# mismo patrón que sabias-montana-5/6/7/8/9
VIDEOS.append({
    "name": "sabias-montana-10",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        {"text": "¿Sabías que Dios te espera en tu corazón y anhela que le hables como a tu "
                 "mejor amigo? "
                 "Quédate un instante en silencio y dile con amor: Señor, te amo.",
         "q": "mountain peaks aerial",
         "img_seed": 5200 + 10,
         "ai": "majestic mountain peaks under bright sky, vertical",
         "motion": "zoom-out"},
        {"text": "Si esto te hizo bien, dale like y suscríbete. ¡Bendiciones!",
         "motion": "zoom-in"},
    ],
})

_CTA_YT = "Si esto te hizo bien, dale like y suscríbete. ¡Bendiciones!"
_CTA_FB = "Si esto te hizo sentido, sígueme. ¡Bendiciones!"

# ─── SERIE ORIGINAL: sabias-1 a sabias-10 (texto corregido, CTA separada) ───
# Textos de SABIAS_QUE/textos.txt corregidos (typos + sin "sígueme")
_VIEJAS_SABIAS = [
    (1, "¿Sabías que Dios no te pide perfección, sino tu confianza? "
        "Él conoce tus cargas y te sostiene en silencio cuando te falta la fuerza. "
        "No cargues con todo sola hoy. Respira profundamente, habla con Él un momento.",
     "mountain peaks aerial", "yt"),
    (2, "¿Sabías que Dios ya está en tu mañana cuidando de ti? "
        "Tu ansiedad por el futuro no cambia nada, pero su amor constante te sostiene en el presente. "
        "Deja tus preocupaciones en sus manos. Eleva una oración hoy.",
     "mountain lake reflection sunrise", "yt"),
    (3, "¿Sabías que Dios escucha el cansancio de tu corazón, incluso cuando no tienes palabras? "
        "No necesitas esforzarte para que Él te ame y te abrace hoy. "
        "Encuentra paz en su presencia. Entrégale tu día en oración.",
     "misty mountain morning", "yt"),
    (4, "¿Sabías que Dios no busca tu perfección, sino tu presencia en lo cotidiano? "
        "Él te acompaña en cada silencio y abraza tus cansancios con amor infinito. "
        "Dedica un minuto a conversar con Él hoy.",
     "mountain sunset golden", "yt"),
    (5, "¿Sabías que Dios no te pide perfección sino tu descanso en Él? "
        "Tu cansancio no es un fallo, es una invitación a confiar. "
        "Dile hoy lo que te pesa en una oración sencilla.",
     "mountain stream peaceful", "yt"),
    (6, "¿Sabías que Dios no te pide perfección sino solo tu presencia? "
        "Él ya conoce tus cargas y te sostiene con un amor que no exige nada a cambio.",
     "mountain valley clouds", "fb"),
    (7, "¿Sabías que Dios te cuida en los detalles más pequeños de tu día? "
        "No necesitas hacer grandes esfuerzos para merecer su bondad "
        "porque su amor te acompaña siempre.",
     "mountain meadow flowers", "fb"),
    (8, "¿Sabías que Dios ya perdonó tus errores antes de que sintieras culpa? "
        "Su mirada sobre ti es de pura ternura y está listo para aliviar esa carga que llevas sola.",
     "mountain path sunlight", "fb"),
    (9, "¿Sabías que Dios no te pide que seas perfecta, sino que te dejes cuidar? "
        "Su amor sostiene tus días más caóticos y te ofrece un descanso real en medio de tus tareas. "
        "No tienes que poder con todo sola.",
     "mountain clouds peaks", "fb"),
    (10, "¿Sabías que Dios ya conoce tus cargas antes de que se lo digas? "
         "Su bondad es un refugio silencioso que no te juzga por lo que no lograste hoy. "
         "Estás a salvo en su presencia.",
      "mountain forest path", "fb"),
]

for _n, _texto, _q, _platform in _VIEJAS_SABIAS:
    _cta = _CTA_YT if _platform == "yt" else _CTA_FB
    VIDEOS.append({
        "name": f"sabias-{_n}",
        "bgm": True,
        "rate": "-8%",
        "voices": ["male"],
        "scenes": [
            {"text": _texto,
             "q": _q,
             "stock": True,
             "img_seed": 5200 + _n,
             "ai": "majestic " + _q + ", vertical",
             "motion": "zoom-out"},
            {"text": _cta,
             "motion": "zoom-in"},
        ],
    })

# ─── NUEVA SERIE: sabias-11 a sabias-20 (texto sin CTA, CTA en escena separada) ───
# Textos generados por Gemini 2026-08-25, verificados contra frases usadas
_NUEVAS_SABIAS = [
    # (número, texto SIN "Sígueme", query b-roll, CTA platform)
    (11, "¿Sabías que Dios no te pide que seas perfecta, sino que descanses en Él? "
         "Tu valor ya está asegurado, no tienes que ganarlo sufriendo. "
         "Hoy te invito a respirar y decirle: Señor, guíame.",
     "mountain peaks aerial", "yt"),
    (12, "¿Sabías que Dios valora tu esfuerzo diario más que cualquier logro extraordinario? "
         "Tu vida ordinaria ya es un espacio sagrado para Él. "
         "Haz una pausa hoy para agradecer su presencia constante.",
     "mountain lake reflection sunrise", "yt"),
    (13, "¿Sabías que Dios ya perdonó tu pasado y solo quiere que vivas hoy en paz? "
         "La culpa no viene de Él, sino de tu propio juicio. "
         "Pídele hoy que sane tu corazón.",
     "misty mountain morning", "yt"),
    (14, "¿Sabías que Dios te sostiene con amor en tus momentos de mayor cansancio? "
         "No estás sola cargando el mundo; Él camina a tu lado. "
         "Entrégale tus preocupaciones hoy en silencio.",
     "mountain sunset golden", "yt"),
    (15, "¿Sabías que Dios no te pide perfección sino tu descanso en Él? "
         "Tu cansancio no es un fallo, es una invitación a confiar. "
         "Dile hoy lo que te pesa en una oración sencilla.",
     "mountain stream peaceful", "yt"),
    (16, "¿Sabías que Dios no te pide perfección sino solo tu presencia? "
         "Él ya conoce tus cansancios y te sostiene con un amor que no exige nada a cambio.",
     "mountain valley clouds", "fb"),
    (17, "¿Sabías que Dios te cuida en los detalles más pequeños de tu día? "
         "No necesitas hacer grandes esfuerzos para merecer su bondad "
         "porque su amor te acompaña siempre.",
     "mountain meadow flowers", "fb"),
    (18, "¿Sabías que Dios ya perdonó tus errores antes de que sintieras culpa? "
         "Su mirada sobre ti es de pura ternura y está listo para aliviar esa carga que llevas sola.",
     "mountain path sunlight", "fb"),
    (19, "¿Sabías que Dios no te pide que seas perfecta, sino que te dejes cuidar? "
         "Su amor sostiene tus días más caóticos y te ofrece un descanso real en medio de tus tareas. "
         "No tienes que poder con todo sola.",
     "mountain clouds peaks", "fb"),
    (20, "¿Sabías que Dios ya conoce tus cansancios antes de que se lo digas? "
         "Su bondad es un refugio silencioso que no te juzga por lo que no lograste hoy. "
         "Estás a salvo en su presencia.",
     "mountain forest path", "fb"),
]

for _n, _texto, _q, _platform in _NUEVAS_SABIAS:
    _cta = _CTA_YT if _platform == "yt" else _CTA_FB
    VIDEOS.append({
        "name": f"sabias-{_n}",
        "bgm": True,
        "rate": "-8%",
        "voices": ["male"],
        "scenes": [
            {"text": _texto,
             "q": _q,
             "stock": True,
             "img_seed": 5200 + _n,
             "ai": "majestic " + _q + ", vertical",
             "motion": "zoom-out"},
            {"text": _cta,
             "motion": "zoom-in"},
        ],
    })

for _n, _texto in _SABIAS:
    VIDEOS.append({
        "name": f"sabias-montana-{_n}",
        "bgm": True,
        "rate": "-8%",
        "voices": ["male"],
        "scenes": [
            {"text": _texto,
             "q": "mountain peaks aerial",
             "img_seed": 5200 + _n,
             "ai": "majestic mountain peaks under bright sky, vertical",
             "motion": "zoom-out"},
        ],
    })

VIDEOS.append({
    "name": "no-permanezcas-atrapado",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        # ESCENA 1 — HOOK (Pexels VIDEO)
        {"text": "¿Cuánto tiempo llevás intentando que una relación deje de doler?",
         "stock": True,
         "q": "woman sitting alone bedroom morning",
         "ai": "Adult woman sitting on the edge of a bed in a quiet bedroom, morning natural light from window, contemplative, intimate, warm tones",
         "motion": "zoom-in"},

        # ESCENA 2 — HOOK (IA imagen)
        {"text": "Tal vez ya aprendiste a medir cada palabra.\nA pensar dos veces antes de hablar.",
         "ai": "Close-up of feminine hands holding a smartphone, unsent message on screen, natural window light, intimate, warm tones, photorealistic",
         "q": "hands phone message",
         "motion": "zoom-in"},

        # ESCENA 3 — HOOK (Pexels VIDEO)
        {"text": "A pedir perdón… incluso cuando no sabes exactamente por qué.",
         "stock": True,
         "q": "woman sitting alone thinking home",
         "ai": "Woman sitting quietly at home after a difficult conversation, not crying, just exhausted, natural light, contemplative, warm tones",
         "motion": "static"},

        # ESCENA 4 — PSICOLOGÍA (Pexels VIDEO)
        {"text": "Cuando vivís mucho tiempo intentando evitar el conflicto, empiezas a acostumbrarte a cosas que antes te parecían inaceptables.",
         "stock": True,
         "q": "woman cleaning home alone",
         "ai": "Woman quietly tidying objects on a table in a calm home, natural light, domestic routine, intimate, warm tones, photorealistic",
         "motion": "pan-right"},

        # ESCENA 5 — GIRO ESPIRITUAL (IA imagen)
        {"text": "Pero hay algo que la fe no te pide:\nque te destruyas para demostrar que amas.",
         "ai": "Bible open on a wooden table illuminated by soft window light, peaceful home, warm tones, intimate, photorealistic, high detail",
         "q": "bible table sunlight",
         "motion": "zoom-in"},

        # ESCENA 6 — LA BIBLIA (Pexels VIDEO)
        {"text": "Proverbios dice:\n\"Déjala, no pases por ella; apártate de ella.\"",
         "static_text": ["\"Apártate de ella.\"", "Proverbios 4,15"],
         "stock": True,
         "q": "hands reading bible pages",
         "ai": "Close-up of hands gently turning pages of a Bible, warm natural light, intimate, peaceful, photorealistic",
         "motion": "static"},

        # ESCENA 7 — PERDÓN ≠ PERMITIR (IA imagen)
        {"text": "Alejarte no significa odiar.\nPerdonar no significa volver a exponerte al mismo daño.",
         "static_text": ["PERDONAR ≠ PERMITIR"],
         "static_y": 0.25,
         "static_size": 64,
         "ai": "Woman's hands placing personal belongings into a bag calmly, not desperate, natural light, domestic setting, warm tones, photorealistic, high detail",
         "q": "woman packing bag home",
         "motion": "zoom-out"},

        # ESCENA 8 — REALIDAD (Pexels VIDEO)
        {"text": "Y sé que no siempre es tan sencillo como decir:\n\"Bueno… entonces vete.\"",
         "stock": True,
         "q": "woman sitting by window thinking",
         "ai": "Woman sitting by a window with a bag beside her, looking out, doubt and sadness but also clarity, natural light, ambivalent, warm tones, photorealistic",
         "motion": "static"},

        # ESCENA 9 — ESPERANZA (IA imagen)
        {"text": "Hay vínculos, hijos, años compartidos, miedo, dependencia, recuerdos…\ny muchas veces no sabes ni por dónde empezar.",
         "ai": "Woman standing in front of an open door with sunlight streaming in from outside, hesitation and hope, warm tones, intimate, photorealistic, high detail",
         "q": "woman opening door sunlight",
         "motion": "zoom-in"},

        # ESCENA 10 — CIERRE (Pexels VIDEO)
        {"text": "Pero quizá hoy necesitabas recordar esto:\nDios puede pedirte que perdones, pero no te pide que permanezcas atrapado en aquello que destruye tu vida.\nA veces poner un límite no es dejar de amar.\nEs empezar a cuidar la vida que Dios te confió.",
         "static_text": ["PERDONAR NO ES PERMITIR.", "AMAR TAMBIÉN PUEDE SER PONER LÍMITES."],
         "stock": True,
         "q": "woman walking outside trees sunlight",
         "ai": "Woman walking slowly toward an open space with trees and natural light, serene relief, hope, warm golden light, photorealistic, high detail",
         "motion": "zoom-out"},

        # ESCENA 11 — CTA (Pexels VIDEO)
        {"text": "Si este mensaje te hizo sentido, suscríbete al canal.\nY deja tu pedido de oración en los comentarios.\nEstamos para acompañarno.\nBendiciones.",
         "stock": True,
         "q": "woman walking path sunlight peaceful",
         "ai": "Woman walking on a peaceful path with warm sunlight, serene, hopeful, natural, photorealistic",
         "motion": "zoom-out"},
    ],
})

VIDEOS.append({
    "name": "oracion_short",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        # ESCENA 1 — ORACIÓN (Pexels VIDEO: manos pidiendo protección, del largo)
        {"text": "Señor, aquí estoy.\n\n"
                 "Por unos minutos, quiero detenerme y estar contigo.\n\n"
                 "Vengo tal como estoy, con mis preocupaciones.\n\n"
                 "Y hoy te las dejo en tus manos.",
         "stock": True,
         "q": "hands prayer protection",
         "ai": "Close-up of hands together in prayer, soft warm light, tender protective mood, photorealistic, high detail",
         "motion": "zoom-in"},

        # ESCENA 2 — CTA (imagen local: hombre afro orando)
        {"text": "Si este momento de oración te hizo bien, suscríbete.",
         "ai": "African american man kneeling by his bed in prayer, hands together, soft warm window light, calm and reflective, photorealistic, cinematic, vertical 9:16",
         "q": "man praying hands",
         "motion": "zoom-in"},
    ],
})

VIDEOS.append({
    "name": "me-pongo-en-tus-manos",
    "bgm": True,
    "rate": "-8%",
    "voices": ["male"],
    "scenes": [
        # ESCENA 1 — GANCHO: oración de entrega (manos abiertas, lamparita)
        {"text": "Señor, me pongo en tus manos. [600]\n"
                 "Cuida de mí mientras duermo.",
         "ai": "Tight macro photograph of an elderly man's two open palms resting upward on a folded blanket beside a bed, the frame is cropped just above the wrists so the hands fill the entire image, aged weathered skin, soft warm gold bedside glow, calm trust, photorealistic, high detail, vertical 9:16 composition",
         "q": "open palms night lamp",
         "motion": "zoom-in",
         "light": True},

        # ESCENA 2 — FAMILIA Y HOGAR (casa de noche desde la calle, ventanas cálidas)
        {"text": "Cuida de las personas que amo. [600]\n"
                 "Protege mi hogar.",
         "ai": "Photorealistic shot of a quiet house exterior at night viewed from the street, several warm golden-lit windows glowing, cozy safe home feeling, dark blue evening sky, gentle warm atmosphere, no rain, vertical 9:16 composition",
         "q": "family photos shelf lamp night",
         "motion": "pan-left",
         "light": True},

        # ESCENA 3 — DESCANSO Y PAZ (mujer durmiendo en paz, mano al pecho)
        {"text": "Dale descanso a mi mente. [600]\n"
                 "Dale paz a mi corazón.",
         "ai": "A woman in her fifties lying peacefully in bed at night in a cozy plain bedroom, wearing a simple nightgown, eyes closed, one hand resting gently over her heart, soft warm bedside lamplight, slow calm breathing, no religious images, intimate observational photography, photorealistic, high detail, vertical 9:16 composition",
         "q": "woman sleeping peacefully bed",
         "motion": "zoom-out",
         "light": True},

        # ESCENA 4 — MAÑANA (cielo claro, recibir el nuevo día)
        {"text": "Ayúdame a recibir el nuevo día como un regalo.",
         "ai": "Sunrise over misty mountains seen through a bedroom window curtain, golden warm light flooding the room, gentle hopeful serene mood, no people, photorealistic, high detail, vertical 9:16 composition",
         "q": "sunrise mountains window",
         "motion": "zoom-in",
         "light": True},

        # ESCENA 5 — CONFIANZA (manos juntas en oración sobre la cama, soltando)
        {"text": "Enséñame a confiar más en ti. [600]\n"
                 "A preocuparme menos por aquello que no puedo controlar.",
         "ai": "Close-up of two hands gently joined in prayer resting on a bed at night, soft warm lamplight, releasing worries with trusting calm, cozy plain bedroom, no religious objects, intimate observational photography, photorealistic, high detail, vertical 9:16 composition",
         "q": "folded hands prayer bed",
         "motion": "pan-right",
         "light": True},

        # ESCENA 6 — BIEN (gesto de servicio: taza de té ofrecida)
        {"text": "A hacer el bien que sí puedo hacer. [400]\n"
                 "A amar mejor. [400]\n"
                 "A perdonar. [400]\n"
                 "A agradecer.",
         "ai": "A person's hands offering a warm cup of tea to someone else at a cozy table, soft warm kitchen light, generous kind gesture, gentle hopeful mood, faces not visible, photorealistic, high detail, vertical 9:16 composition",
         "q": "hands offering tea kindness",
         "motion": "zoom-in",
         "light": True},

        # ESCENA 7 — PAYOFF/CIERRE (visto de espaldas, primera luz en el horizonte)
        {"text": "Y a recordar que nunca estoy fuera de tu mirada.",
         "ai": "A person seen from behind standing at a bedroom window at first light of dawn, looking out at warm golden light over calm rooftops, small and held, hopeful serene mood, no religious images, intimate observational photography, photorealistic, high detail, vertical 9:16 composition",
         "q": "person window dawn rooftop",
         "motion": "zoom-out",
         "light": True},

        # ESCENA 8 — CTA YOUTUBE (reusa amanecer e07, sin caras; ~3s final)
        {"text": "Si esta oración te hizo bien,\nsuscríbete.",
         "static_text": ["SUSCRÍBETE"],
         "reuse_img": True,
         "motion": "zoom-in",
         "light": True},
    ],
})

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