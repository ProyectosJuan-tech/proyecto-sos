#!/usr/bin/env python3
"""Escenas del largo "No te falta fuerza de voluntad: te falta un sistema".

Guion congelado 2026-08-15 (v3). Tabla de producción: 38 bloques de render para
33 escenas de voz. Pipeline YT horizontal 16:9 con static_text (frases pilar),
boom (golpes) y transiciones fade.

SISTEMA VISUAL 2026-08-15: 8 imágenes OBJETO-PRIMERO (N1-N8) en vez de retratos.
Cada imagen la cuentan los objetos (zapatilla, libro, calendario, taza, puerta);
solo N7/N8 muestran persona, de espaldas (consistencia de protagonista sin cara
que mantener). Dirección cinematográfica en director_visual.py (PASO 1 + PASO 2).

Arco visual (38 bloques → 8 imágenes):
N1 la promesa de noche  / N2 la mañana que no arranca / N3 el entorno que manda
N4 la señal (taza+libro) / N5 la preparación (ropa lista) / N6 el registro (calendario)
N7 el volver (zapatilla, de espaldas) / N8 la salida al amanecer (de espaldas)
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Prompts N1-N8 desde director_visual.py (PASO 1 dirección + PASO 2 prompt final).
# NO escribir prompts a mano: editar SCENES en director_visual.py y regenerar.
import director_visual as dv

E_PROMPTS = {name: dv.build_prompt(name) for name in dv.SCENES}

# Palabra/s fallback Wikimedia Commons (keywords cortas, en inglés).
Q = {
    "N1": "bedroom night bed alarm",
    "N2": "bedroom empty bed morning",
    "N3": "kitchen table coffee cookie",
    "N4": "coffee cup book table hand",
    "N5": "sneakers clothes by door",
    "N6": "hand marking calendar wall",
    "N7": "woman tying shoelaces bed",
    "N8": "woman walking out door dawn",
}

MOTIONS = [
    "pan-left", "pan-right", "zoom-in", "zoom-in", "zoom-out", "pan-right",
    "zoom-in", "zoom-out", "zoom-in", "pan-right", "pan-left", "pan-right",
    "pan-left", "zoom-in", "zoom-in", "zoom-out", "pan-left", "zoom-in",
    "pan-right", "zoom-out", "zoom-in", "zoom-in", "pan-right", "pan-left",
    "zoom-in", "pan-right", "pan-right", "zoom-in", "zoom-in", "zoom-in",
    "pan-right", "zoom-in", "pan-left", "zoom-in", "zoom-out", "pan-right",
    "pan-right", "zoom-out",
]

IMG = [
    "N1", "N2", "N1", "N6", "N2", "N3", "N6", "N4", "N3", "N4",
    "N7", "N7", "N4", "N4", "N3", "N4", "N3", "N5", "N5", "N5",
    "N6", "N4", "N4", "N5", "N7", "N6", "N4", "N6", "N7", "N2",
    "N7", "N6", "N7", "N1", "N8", "N4", "N1", "N8",
]

# Noche/promesa rota = oscuro; el resto cálido (bienestar).
LIGHT = {
    "N1": False, "N2": False, "N3": True, "N4": True, "N5": True,
    "N6": True, "N7": True, "N8": True,
}


def _scene(text, idx):
    e = IMG[idx]
    return {
        "text": text,
        "ai": E_PROMPTS[e],
        "q": Q[e],
        "motion": MOTIONS[idx],
        "img": e,
        "light": LIGHT[e],
    }


def scenes():
    E = []

    def add(text, **kw):
        s = _scene(text, len(E))
        s.update(kw)
        E.append(s)

    # CAP 1 — No te falta fuerza de voluntad
    add("Te lo prometés de noche. Mañana empiezo. Mañana hago ejercicio. "
        "Mañana leo. Mañana ordeno todo.")
    add("Y mañana llega... y volvés a hacer exactamente lo mismo.")
    add("Entonces pensás que te falta disciplina. ¿Y si el problema no fueras vos?",
        static_text=["¿Y si el problema no fueras vos?"])
    add("En este video no te voy a pedir más disciplina. Te voy a mostrar cómo "
        "armar un hábito que necesite menos fuerza de voluntad. Al final, un "
        "sistema de cuatro pasos para empezar esta semana.")
    add("Pensalo así: la motivación sube y baja. Hay días que querés cambiarlo "
        "todo, y días que no querés ni levantarte. Si tu hábito está parado "
        "sobre eso, es frágil. Se cae con el primer día malo.")
    add("Y acá viene lo incómodo: muchas veces no te falta fuerza. Te sobran "
        "obstáculos.",
        static_text=["No te falta fuerza.", "Te sobran obstáculos."], boom=True)
    add("Esto no es magia. Es repetición. Cuando una conducta se repite en un "
        "contexto parecido, empieza a necesitar menos esfuerzo consciente. Así "
        "de simple. Y bastante aburrido.")
    add("Aristóteles ya pensaba en esta dirección: la virtud no se construye "
        "diciendo quién querés ser. Se construye practicando. Lo que repetís, "
        "te va formando.")
    add("Entonces, si se entrena... ¿por qué te sigue costando tanto? Porque lo "
        "estás entrenando de la manera más cara: a pura voluntad.")

    # CAP 2 — El hábito empieza antes de hacerlo
    add("¿Sabés cuándo se te cae un hábito? No el día que no lo hiciste. El día "
        "que decidís que para hacerlo bien tenés que hacerlo entero.",
        static_text=["No el día que no lo hiciste."])
    add("Querés leer, una hora. Correr, cinco kilómetros. Meditar, veinte "
        "minutos. Estás armando la versión final desde el día uno. Y la versión "
        "final no arranca: asusta.",
        static_text=["La versión final no arranca: asusta."])
    add("Pero tu objetivo inicial no es hacer mucho. Es enseñarle a tu rutina "
        "que esto ahora es parte de tu vida. Dos minutos alcanzan para arrancar. "
        "No porque dos minutos hagan magia: porque bajan el costo de empezar.")
    add("Después del café, dos páginas. Después de lavarte los dientes, hilo "
        "dental. Después de ponerte las zapatillas, caminás. No estás inventando "
        "un momento nuevo: te estás colgando de uno que ya existe.")
    add("Una forma simple de pensarlo: algo te dispara la acción, la acción se "
        "repite, y lo que pasa después te ayuda a seguir. Con eso ya alcanza "
        "para empezar.")

    # CAP 3 — Diseñá tu entorno
    add("Te hago una pregunta incómoda: cuando estás cansado, ¿quién gana? "
        "¿Vos, o lo que tenés a la vista?",
        static_text=["Cuando estás cansado,", "¿quién gana?"])
    add("Si querés leer más, no escondas el libro en la biblioteca. Ponelo donde "
        "te sentás.")
    add("Si querés comer mejor, no pongas tu fuerza de voluntad contra una "
        "galletita abierta sobre la mesa. Perdés.",
        static_text=["Perdés."], static_size=160)
    add("Si querés entrenar, dejá la ropa preparada. Eso ya es media decisión "
        "tomada.")
    add("Cada obstáculo que sacás hoy, es una decisión que no vas a tener que "
        "tomar mañana.",
        static_text=["Cada obstáculo que sacás hoy", "es una decisión menos mañana."])
    add("No intentes volverte una persona disciplinada. Diseñá una vida donde "
        "hacer lo correcto sea más fácil. Eso es todo.",
        static_text=["No te vuelvas más fuerte.", "Hacé más fácil lo correcto."])

    # CAP 4 — El sistema de cuatro pasos
    add("Te prometí cuatro pasos. Acá van. No los hagas perfectos: arrancalos "
        "esta semana.")
    add("Uno: elegí UNA conducta. No quiero estar en forma. Sí: después del "
        "café, camino diez minutos.")
    add("Dos: anclala. Después de X, hago Y. Te colgás de un hábito que ya "
        "tenés.")
    add("Tres: reducí la fricción. Dejá todo listo: ropa, agua, libro. La "
        "decisión ya la tomaste anoche.")
    add("Cuatro: volvé rápido si fallás. El error no es caer: es quedarte en el "
        "piso. Y un día malo no tiene por qué volverse una semana mala.",
        static_text=["El error no es caer.", "Es quedarte en el piso."], boom=True)
    add("Fijate la lógica: los primeros tres hacen que empezar sea fácil. El "
        "cuarto hace que un fracaso no destruya todo.",
        static_text=["Los 3 primeros: empezar fácil.", "El 4º: fallar no destruye."])
    add("Hagámoslo juntos, con uno real. Quiero leer más. Después de cenar, "
        "cuando dejo el plato en la cocina, abro el libro que ya dejé sobre la "
        "mesa y leo dos páginas.")
    add("El celular queda en otra habitación. Y marco el día cuando termino. Eso "
        "es un sistema.",
        static_text=["Eso es un sistema."])
    add("Y una cosa más: esperás tener ganas para empezar. Pero a veces es al "
        "revés: empezás, y la gana aparece después. No necesitás motivación para "
        "actuar. Necesitás actuar un poquito para que aparezca algo de "
        "motivación.")

    # CAP 5 — Aprendé a volver
    add("Ahora viene lo que nadie te dice: vas a fallar. Está bien. Va a haber "
        "una semana que no sostiene nada. El hábito se va a romper.")
    add("Lo que define tu vida no es que se rompa. Es que lo volvés a atar. Al "
        "otro día. Sin drama, sin castigarte.")
    add("Y quizás hay una medida del hábito de la que nadie habla: no cuántos "
        "días seguidos lo hiciste, sino cuánto tardás en volver cuando lo "
        "rompés.",
        static_text=["¿Cuánto tardás en volver?"])
    add("Antes necesitabas tres semanas para volver. Ahora volvés al día "
        "siguiente. Eso también es progreso.",
        static_text=["No cuántos días seguidos."])
    add("Volvamos a la pregunta del principio. ¿Por qué prometés cambiar, y "
        "después no lo hacés? Quizás no necesitás ser otra persona. Quizás "
        "necesitás dejar de construir tu vida alrededor de cómo te sentís ese "
        "día. Porque mañana vas a estar cansado. Vas a tener otro problema. Y "
        "quizás no tengas ganas.")
    add("Por eso no diseñes tu hábito para el día perfecto. Diseñalo para el día "
        "difícil. Empezá pequeño. Prepará el camino. Y cuando falles, volvé. No "
        "necesitás cambiar tu vida mañana. Necesitás hacer más fácil una cosa. Y "
        "repetirla.",
        static_text=["Diseñalo para el día difícil."], boom=True)
    add("Ahora, algo que te pido: escribime en los comentarios un solo hábito "
        "que querés construir. Pero no me escribas quiero leer más. Escribime "
        "exactamente esto: Después de, voy a. Por ejemplo: Después de cenar, voy "
        "a leer dos páginas.",
        static_text=["Después de ___,", "voy a ___"])
    add("Si conocés a alguien que hace meses viene diciendo mañana empiezo, "
        "mandale este video. Tal vez sea el sistema que le faltaba.")
    add("Y suscribite si querés más filosofía práctica para una vida con más "
        "criterio y menos ruido.")
    return E
