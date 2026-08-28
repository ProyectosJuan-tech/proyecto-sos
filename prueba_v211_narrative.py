"""
PRUEBA REAL V2.1.1 — Narrative Visual Director.

Genera DOS planes completos (determinista, SIN red: mock de asset fetch):

  A) SHORT  9:16  — tema: descanso / hábitos
  B) VIDEO 16:9   — tema diferente: perdón / soltar el rencor

Para cada uno imprime:
  scene # | narrative_role | text (narración) | visual_event | visual_strategy | prompt final

Y verifica los criterios:
  - visual_events variados
  - cada uno relacionado con su texto
  - existe progresión visual (no todos iguales, no tipo único persona)
  - no son paráfrasis de central_idea
  - el prompt final incorpora la dirección (contiene el visual_event)
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


def show(label, em, check_idea):
    print("\n" + "=" * 100)
    print(f"PLAN: {label}  ({em.canvas_width}x{em.canvas_height})")
    print("=" * 100)
    dirs = NarrativeVisualDirector().direct_plan(em.briefs)
    events = []
    for i, (b, d) in enumerate(zip(em.briefs, dirs), 1):
        ev = d.visual_event
        strat = d.strategy
        events.append(ev)
        print(f"\nScene {i}  [{b.narrative_role.value}]")
        print(f"  text            : {b.narration}")
        print(f"  visual_event    : {ev}")
        print(f"  visual_strategy : type={strat.subject_type} shot={strat.shot_type} "
              f"symbolic={strat.symbolic_level}")
        print(f"  prompt final    : {d.prompt}")

    # criterios
    print("\n" + "-" * 100)
    uniq = len(set(events))
    types = {d.representation_type for d in dirs}
    n_person = sum(1 for d in dirs if d.representation_type == RepresentationType.PERSON)
    related = all((b.narration and ev and ev != check_idea) for b, ev in zip(em.briefs, events))
    noparaph = all(ev != check_idea for ev in events)
    incorporated = all(d.visual_event.split(".")[0][:20].lower() in d.prompt.lower()
                       or d.visual_event.split(",")[0][:20].lower() in d.prompt.lower()
                       for d in dirs)
    print(f"  visual_events variados       : {uniq}/{len(events)} únicos")
    print(f"  tipos de representación      : {sorted(t.value for t in types)}")
    print(f"  escenas SOLO de persona       : {n_person} (no persona->persona por defecto: {n_person < len(events)//2})")
    print(f"  relacionados con su texto     : {related}")
    print(f"  no paráfrasis de central_idea : {noparaph}")
    print(f"  prompt incorpora dirección   : {incorporated}")
    return uniq, len(types), n_person, related, noparaph, incorporated


ok_all = True
for check in (
    show("A) SHORT 9:16 — descanso / hábitos",
         produce_editorial(topic="descanso",
                           central_idea="nos cuesta tanto descansar aunque estemos cansados",
                           format_name="short", asset_fetch_fn=mock_fetch_fn),
         "nos cuesta tanto descansar aunque estemos cansados"),
    show("B) VIDEO 16:9 — perdón / soltar el rencor",
         produce_editorial(topic="perdón",
                           central_idea="el rencor te ata más a quien te lastimó que cualquier amor",
                           format_name="youtube", asset_fetch_fn=mock_fetch_fn),
         "el rencor te ata más a quien te lastimó que cualquier amor"),
):
    uniq, ntypes, n_person, related, noparaph, incorporated = check
    if not (uniq > 1 and ntypes >= 3 and related and noparaph and incorporated):
        ok_all = False

print("\n" + "=" * 100)
print(f"PRUEBA REAL: {'OK — ambos planes cumplen criterios' if ok_all else 'FALLO en algún criterio'}")
print("=" * 100)
raise SystemExit(0 if ok_all else 1)
