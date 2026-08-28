"""
V2.1.1 — NARRATIVE VISUAL DIRECTOR: tests deterministas.

Cubre los 14 requisitos del spec:
  1. Dos escenas diferentes no reciben el mismo visual_event.
  2. visual_event es observable.
  3. visual_event está relacionado con scene_text.
  4. narrative_role modifica la estrategia.
  5. previous_events reduce repetición injustificada.
  6. Una repetición deliberada puede conservarse.
  7. visual_event llega a SceneBrief.
  8. SceneBrief llega a compose_prompt().
  9. compose_prompt() recibe el visual_event correcto.
 10. Short 9:16 funciona (integration).
 11. Long-form 16:9 funciona (integration).
 12. Pipeline legacy continúa funcionando.
 13. Escena sin info → fallback seguro y explícito.
 14. No hay loops infinitos ni generación externa.

Sin red: usa mocks de asset fetch. Determinista.
"""

import narrative_visual_director as nvd
from narrative_visual_director import (
    NarrativeVisualDirector,
    derive_visual_event,
    NarrativeRole,
    _FALLBACK_EVENT,
    RepresentationType,
)
from scene_brief import SceneBrief
from short_director import build_scene, ShortPlan, validate_plan
from editorial_orchestrator import produce_editorial, LongFormPlan, validate_long_plan

PASS = 0
FAIL = 0


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS — {name}" + (f" ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL — {name} {detail}")


# ── Helpers ──
def make_brief(scene_id, role, narration, symbol=None):
    return build_scene(
        scene_id=scene_id,
        role=role,
        narration=narration,
        symbol=symbol,
    )


SHORT_TOPIC = "descanso"
SHORT_IDEA = "nos cuesta tanto descansar aunque estemos cansados"
LONG_TOPIC = "valor"
LONG_IDEA = "algunas personas sienten que siempre tienen que demostrar su valor"


def mock_fetch_fn(queries, **kw):
    out = []
    for q in queries:
        out.append({
            "id": f"p_{abs(hash(q)) % 10000}",
            "url": f"https://example.com/v_{abs(hash(q)) % 10000}.mp4",
            "duration": 8.0,
            "width": 1080,
            "height": 1920,
            "orientation": "portrait",
            "fps": 30.0,
            "file_size": 1000000,
            "thumbnail": "",
            "quality": "hd",
            "source": "pexels",
        })
    return out


def observable(event, central):
    """Heurística de observabilidad: evento distinto a la idea central, con
    suficiente cuerpo cámara-mostrable y sin colgar de la frase fuente."""
    return bool(event) and event != central and len(event.split()) >= 6


print("\n[1] VISUAL EVENTS DIFERENTES")
b1 = make_brief("e01", NarrativeRole.PROBLEM, "sientes que debes demostrar tu valor")
b2 = make_brief("e02", NarrativeRole.HOPE, "abres la puerta y entra la luz")
d1, d2 = NarrativeVisualDirector().direct_brief(b1), NarrativeVisualDirector().direct_brief(b2)
ok("dos escenas → visual_events distintos", d1.visual_event != d2.visual_event,
   f"{d1.visual_event[:40]} | {d2.visual_event[:40]}")

print("\n[2] OBSERVABLE")
ok("visual_event observable (cuerpo cámara-mostrable)", observable(d1.visual_event, SHORT_IDEA))
ok("no es paráfrasis de central_idea", d1.visual_event != SHORT_IDEA and d2.visual_event != SHORT_IDEA)

print("\n[3] RELACIÓN CON SCENE_TEXT")
ev, _ = derive_visual_event("borra por tercera vez un mensaje antes de enviarlo", "psychology")
ok("evento sale de la señal del texto", ("message" in ev or "deletes" in ev or "types" in ev), ev[:50])
ev2, _ = derive_visual_event("apila los platos con cuidado para no hacer ruido", "agitation")
ok("evento 2 sale del texto (manos/platos)", ("dishes" in ev2 or "hands" in ev2), ev2[:50])

print("\n[4] ROL MODIFICA LA ESTRATEGIA")
strat_h = nvd._ROLE_STRATEGIES[NarrativeRole.HOOK]
strat_p = nvd._ROLE_STRATEGIES[NarrativeRole.PSYCHOLOGY]
ok("estrategias distintas por rol", strat_h != strat_p and strat_h.subject_type != strat_p.subject_type,
   f"{strat_h.subject_type} vs {strat_p.subject_type}")
noise = "una frase general sin señales de acción"
eh, _ = derive_visual_event(noise, "hook")
ep, _ = derive_visual_event(noise, "psychology")
ok("mismo texto, roles distintos → eventos distintos", eh != ep, f"{eh[:40]} | {ep[:40]}")

print("\n[5] ANTI-REPETICIÓN POR previous_events")
e1, t1 = derive_visual_event("borra un mensaje antes de enviarlo", "psychology", previous_events=[])
e2, t2 = derive_visual_event("borra un mensaje antes de enviarlo", "psychology", previous_events=[e1])
ok("previous_events reduce repetición", e1 != e2, f"{t1} -> {t2}")

print("\n[6] REPETICIÓN DELIBERADA PRESERVADA")
er, _ = derive_visual_event("borra un mensaje antes de enviarlo", "psychology",
                            previous_events=[e1], keep_allowed=True)
ok("keep_allowed=True conserva el evento", er == e1)
plan_d = NarrativeVisualDirector().direct_plan(
    [b1, make_brief("e03", NarrativeRole.PSYCHOLOGY, "borra un mensaje antes de enviarlo")],
    force_reuse={e1})
ok("force_reuse enlaza evento repetido", plan_d[1].visual_event == e1)

print("\n[7] VISUAL_EVENT LLEGA A SCENEBRIEF (integration)")
em_s = produce_editorial(topic=SHORT_TOPIC, central_idea=SHORT_IDEA,
                         format_name="short", asset_fetch_fn=mock_fetch_fn)
events_s = [b.visual_event for b in em_s.briefs]
ok("briefs tienen ai_prompt y visual_event", all(b.ai_prompt and b.visual_event for b in em_s.briefs))
ok("visual_events variados (no todos iguales)", len(set(events_s)) > 1,
   f"{len(set(events_s))} únicos / {len(events_s)} escenas")

print("\n[8] SCENEBRIEF LLEGA A COMPOSE_PROMPT (direct_plan)")
dirs8 = NarrativeVisualDirector().direct_plan(em_s.briefs)
ok("prompt no vacío por escena", all(d.prompt for d in dirs8))
ok("compose_prompt sin excepción", len(dirs8) == len(em_s.briefs))

print("\n[9] COMPOSE_PROMPT RECIBE EL VISUAL_EVENT CORRECTO")
ok("el prompt contiene su visual_event",
   all((d.visual_event.split(".")[0][:20].lower() in d.prompt.lower())
       or (d.visual_event.split(",")[0][:20].lower() in d.prompt.lower())
       for d in dirs8))

print("\n[10] SHORT 9:16 FUNCIONA")
ok("short devuelve plan+1080x1920", (em_s.canvas_width, em_s.canvas_height) == (1080, 1920))
ok("short plan válido", validate_plan(em_s.plan)["valid"])
ok("short escenas distantes en variedad de representación",
   len({d.representation_type for d in dirs8}) >= 3)

print("\n[11] LONG 16:9 FUNCIONA")
em_l = produce_editorial(topic=LONG_TOPIC, central_idea=LONG_IDEA,
                         format_name="youtube", asset_fetch_fn=mock_fetch_fn)
dirs_l = NarrativeVisualDirector().direct_plan(em_l.briefs)
ok("long devuelve plan+1920x1080", (em_l.canvas_width, em_l.canvas_height) == (1920, 1080))
ok("long plan válido", validate_long_plan(em_l.plan)["valid"])
ok("long visual_events variados", len({b.visual_event for b in em_l.briefs}) > 3,
   f"{len({b.visual_event for b in em_l.briefs})} únicos / {len(em_l.briefs)}")
ok("long tipos variados (anti persona->persona)", len({d.representation_type for d in dirs_l}) >= 3)

print("\n[12] PIPELINE LEGACY CONT. FUNCIONANDO (scene_dicts render-known)")
sd0 = em_s.scene_dicts[0]
ok("scene_dict usa claves que el renderer conoce",
   {"id", "text", "ai", "motion", "trans"} <= set(sd0.keys()),
   str(sorted(sd0.keys())[:10]))
ok("ai (prompt) poblado en scene_dict", bool(sd0.get("ai")))

print("\n[13] FALLBACK SEGURO Y EXPLÍCITO SIN INFORMACIÓN")
empty_brief = make_brief("e99", NarrativeRole.PSYCHOLOGY, " ")
dfb = NarrativeVisualDirector().direct_brief(empty_brief)
ok("marca fallback_used", dfb.fallback_used is True)
ok("usa evento fallback explícito", dfb.visual_event == _FALLBACK_EVENT)

print("\n[14] SIN LOOPS INFINITOS NI GENERACIÓN EXTERNA")
prev = [f"evento visual previo {i} con elementos repetidos de manos y mesa" for i in range(20)]
evf, _ = derive_visual_event("borra un mensaje antes de enviarlo", "psychology", previous_events=prev)
ok("termina con 20 previous_events (sin loop)", bool(evf))
# reiterar anti repetición en cadena determinista
series = []
for _ in range(5):
    ev, _ = derive_visual_event("borra un mensaje antes de enviarlo", "psychology", previous_events=series)
    series.append(ev)
ok("serie sin repetición consecutiva",
   all(series[i] != series[i+1] for i in range(len(series)-1)))

print("\n============================================================")
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("============================================================")
raise SystemExit(1 if FAIL else 0)
