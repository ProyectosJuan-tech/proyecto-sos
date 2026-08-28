"""
PRUEBA REAL V2.1.1 — TEMA DE VALIDACIÓN:
"Esta es la manera de superar el perfeccionismo"  (FE + PSICOLOGÍA)

Objetivo: comprobar si el sistema construye una narrativa visual DISTINTA para
cada escena, SIN optimización manual de los resultados (comportamiento real).

Se inyectan SOLO las narraciones (el texto, equivalente a lo que en producción
viene de Gemini vía generar_textos.py); la dirección visual la hace el sistema
NarrativeVisualDirector tal cual. Determinista, SIN red (mock de asset fetch).

Instrucción de la prueba: NO mirar por la ventana como solución automática,
NO solo personas tristes, NO persona+notebook en todas las escenas; y cada
imagen debe agregar información narrativa, no repetir el texto.
"""

from narrative_visual_director import NarrativeVisualDirector, RepresentationType
from editorial_orchestrator import produce_editorial


def mock_fetch_fn(queries, **kw):
    return [{
        "id": f"p_{abs(hash(q)) % 10000}",
        "url": f"https://example.com/v_{abs(hash(q)) % 10000}.mp4",
        "duration": 8.0, "width": 1080, "height": 1920,
        "orientation": "portrait", "fps": 30.0, "file_size": 1000000,
        "thumbnail": "", "quality": "hd", "source": "pexels",
    } for q in queries]


TOPIC = "perfeccionismo"
IDEA = "el perfeccionismo no nace de querer hacer las cosas bien, sino del miedo a equivocarse"

# Narraciones por rol (texto humano; la dirección visual es del sistema)
SHORT_NARR = {
    "hook": "Quizás no estás intentando hacerlo perfecto porque seas exigente. Quizás tienes miedo a equivocarte.",
    "problem": "Revisas una y otra vez. Borras. Vuelves a empezar. Y lo que nunca terminas de entregar te agota.",
    "agitation": "El problema no es querer hacer las cosas bien: es que esperar la perfección te deja detenida.",
    "psychology": "Tu mente confundió 'hacerlo bien' con 'tener que ser perfecto'. Y detrás de esa exigencia hay miedo.",
    "solution": "Puedes cambiarlo: no esperar a estar perfecto, hacerlo suficientemente bien y seguir avanzando.",
    "hope": "Dios no exige una versión perfecta de ti para amarte. Puedes descansar de esa exigencia.",
    "callout": "Si esto te resonó, compártelo con alguien que necesite soltar la perfección.",
}

LONG_NARR = {
    "hook": "Quizás no es exigencia. Quizás es miedo a equivocarte, a que te rechacen, a no ser suficiente.",
    "reality": "Revisar, borrar, postergar, no publicar, no entregar hasta sentir que está perfecto.",
    "problem": "Parece exigencia, pero muchas veces es miedo a perder el control de lo que otros van a pensar.",
    "psychology_0": "Esperar a estar perfecto puede convertirse en otra forma de quedarse detenido.",
    "psychology_1": "El miedo a perder el control te hace corregir una y otra vez la misma cosa.",
    "psychology_2": "No entregar nada hasta que esté perfecto: así protegías tu valor, pero también te detenía.",
    "solution": "Pasa de 'tiene que estar perfecto' a 'puedo hacerlo suficientemente bien y seguir avanzando'.",
    "biblical_grounding": "La gracia no dice 'esfuérzate más'. Dice: no tiene que ser perfecto para ser amado.",
    "hope": "Puedes terminar sintiendo alivio, no culpa. Dios te conoce y te acepta como eres.",
    "callout": "Si esto te resonó, compártelo con alguien que necesite soltar la perfección.",
}


def show(label, format_name, narr_by_role, roles, check_idea):
    narr = dict(narr_by_role)
    # para roles repetidos (psychology x3 en long), usar los textos _0.._2
    narrations = {}
    role_counts = {}
    for role in roles:
        key = role.value
        role_counts[key] = role_counts.get(key, 0)
        idx = role_counts[key]
        role_counts[key] += 1
        suffix = "" if idx == 0 else f"_{idx}"
        narrations[key] = narr.get(f"{key}{suffix}") or narr.get(key)

    em = produce_editorial(
        topic=TOPIC, central_idea=IDEA, format_name=format_name,
        narrations=narrations, asset_fetch_fn=mock_fetch_fn,
    )
    dirs = NarrativeVisualDirector().direct_plan(em.briefs)

    print("\n" + "=" * 100)
    print(f"PLAN: {label}  ({em.canvas_width}x{em.canvas_height})")
    print("=" * 100)
    events, types = [], []
    for i, (b, d) in enumerate(zip(em.briefs, dirs), 1):
        s = d.strategy
        events.append(d.visual_event)
        types.append(d.representation_type)
        print(f"\nScene {i}  [{b.narrative_role.value}]")
        print(f"  text           : {b.narration}")
        print(f"  visual_event   : {d.visual_event}")
        print(f"  strategy       : type={s.subject_type} shot={s.shot_type} symbolic={s.symbolic_level}")
        print(f"  final_prompt   : {d.prompt}")

    print("\n" + "-" * 100)
    uniq = len(set(events))
    n_person = sum(1 for t in types if t == RepresentationType.PERSON)
    n_window = sum(1 for e in events if "window" in e and "looking" in e)
    n_notebook = sum(1 for e in events if "notebook" in e)
    print(f"  visual_events distintos : {uniq}/{len(events)}")
    print(f"  tipos de representación : {sorted(t.value for t in set(types))}")
    print(f"  escenas de persona      : {n_person} | 'mirando por ventana' : {n_window} | 'notebook': {n_notebook}")
    print(f"  no paráfrasis de idea   : {all(e != check_idea for e in events)}")
    print(f"  prompt incorpora evento : {all(d.visual_event.split('.')[0][:20].lower() in d.prompt.lower() or d.visual_event.split(',')[0][:20].lower() in d.prompt.lower() for d in dirs)}")
    return uniq, types


ok_all = True
for label, fmt, narr, roles, idea in [
    ("SHORT 9:16", "short", SHORT_NARR,
     [r for r in __import__("editorial_orchestrator", fromlist=["SHORT_ARC"]).SHORT_ARC], IDEA),
    ("VIDEO 16:9", "youtube", LONG_NARR,
     [r for r in __import__("editorial_orchestrator", fromlist=["LONG_ARC"]).LONG_ARC], IDEA),
]:
    uniq, types = show(label, fmt, narr, roles, idea)
    if uniq <= 1 or len(set(types)) < 3:
        ok_all = False

print("\n" + "=" * 100)
print(f"PRUEBA REAL (perfeccionismo): {'OK' if ok_all else 'FALLO'}")
print("=" * 100)
raise SystemExit(0 if ok_all else 1)
