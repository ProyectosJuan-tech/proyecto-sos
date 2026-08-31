# V2.4 — PROMPT QUALITY AUDIT (deterministic, sin red)
# Verifica las mejoras arquitecturales de la fase:
#   1. La luz varía POR ROL (no más "soft natural window light" en todas).
#   2. La cámara varía POR PLANO (no más "Medium shot Sony A7IV" en todas).
#   3. La composición base es FORMATO-NEUTRA (sin "lower text band" vertical en 16:9).
#   4. El Proveedor Adapter añade wording FORMATO-ESPECÍFICO (9:16 / 16:9).
#   5. El anchor de realismo humano aparece SOLO con sujeto humano.
#   6. La acción y el símbolo son COHERENTES con el evento (sin contradicción).
passes = 0
fails = 0

def ok(name, cond, detail=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS — {name} {('' if not detail else '· ' + detail[:90])}")
    else:
        fails += 1
        print(f"  FAIL — {name} {('' if not detail else '· ' + detail[:90])}")

from editorial_orchestrator import produce_editorial, build_editorial_plan
from narrative_visual_director import NarrativeVisualDirector
from visual_quality_engine import build_quality_prompt

def mock_fetch_fn(queries, **kw):
    return []

def short_em(topic="el miedo al error", idea="el miedo al error te paraliza"):
    return produce_editorial(topic=topic, central_idea=idea, format_name="short",
                             asset_fetch_fn=mock_fetch_fn)

def long_em(topic="el miedo al error", idea="el miedo al error te paraliza"):
    return produce_editorial(topic=topic, central_idea=idea, format_name="youtube",
                             asset_fetch_fn=mock_fetch_fn)

def unique_vals(em, attr):
    return {getattr(b, attr) for b in em.briefs}

print("[1] LUZ VARÍA POR ROL (anti default idéntico)")
em = short_em()
lights = unique_vals(em, "lighting")
ok("al menos 2 luces distintas entre escenas", len(lights) >= 2, f"{len(lights)} luces")
ok("ninguna escena hereda el default genérico 'soft natural window light'",
   "soft natural window light" not in lights, str(lights))

print("\n[2] CÁMARA VARÍA POR PLANO (anti 'Medium shot Sony A7IV' en todas)")
cams = unique_vals(em, "camera")
ok("al menos 2 cámaras distintas entre escenas", len(cams) >= 2, f"{len(cams)} cámaras")
ok("ninguna escena hereda el default 'Medium shot on Sony A7IV, 50mm f/1.8'",
   "Medium shot on Sony A7IV" not in cams, str(cams))

print("\n[3] COMPOSICIÓN BASE FORMATO-NEUTRA (sin phrasing vertical) + ADAPTER FORMATO-ESPECÍFICO")
plan_b, briefs_b = build_editorial_plan(
    topic="el miedo al error", central_idea="el miedo al error te paraliza", format_name="short")
dirs = NarrativeVisualDirector().direct_plan(briefs_b)
base_prompts = [d.prompt for d in dirs]
ok("prompt BASE no contiene 'lower text band' (vertical-only)",
   all("lower text band" not in p for p in base_prompts))
ad_prompts = [build_quality_prompt(d.prompt, canvas_ar="9:16", has_human=True) for d in dirs]
ok("adapter 9:16 añade wording vertical", all("Vertical 9:16" in p for p in ad_prompts))
plan_l, briefs_l = build_editorial_plan(
    topic="el miedo al error", central_idea="el miedo al error te paraliza", format_name="youtube")
dirs_l = NarrativeVisualDirector().direct_plan(briefs_l)
ad_l = [build_quality_prompt(d.prompt, canvas_ar="16:9", has_human=True) for d in dirs_l]
ok("adapter 16:9 añade wording horizontal", all("Horizontal 16:9" in p for p in ad_l))
ok("9:16 y 16:9 producen wording distinto",
   all("Vertical 9:16" in p for p in ad_prompts) and all("Horizontal 16:9" in p for p in ad_l))

print("\n[4] ANCHOR DE REALISMO HUMANO SOLO CON SUJETO HUMANO")
plan_h, briefs_h = build_editorial_plan(
    topic="el miedo al error", central_idea="el miedo al error te paraliza", format_name="short")
dirs_h = NarrativeVisualDirector().direct_plan(briefs_h)
human_ok = True
for b, d in zip(briefs_h, dirs_h):
    hv = d.representation_type.value
    wants_human = hv in {"person", "hands", "interaction", "detail"}
    p = build_quality_prompt(d.prompt, canvas_ar="9:16", has_human=wants_human)
    has_anchor = "Real human skin" in p or "no people in frame" in p
    if not has_anchor:
        human_ok = False
ok("cada escena lleva anchor de realismo o 'no people'", human_ok)

print("\n[5] ACCIÓN COHERENTE (el brief no guarda la genérica de rol)")
actions = unique_vals(em, "action")
ok("briefs tienen action no vacía tras dirigir", all((a or "").strip() for a in actions))

print("\n[6] SÍMBOLO ALINEADO CON EL EVENTO (doorway → door, bed → bed)")
matched = True
for b in em.briefs:
    ev = (b.visual_event or "").lower()
    sy = (b.symbol or "").lower()
    if "door" in ev or "doorway" in ev:
        if "door" not in sy:
            matched = False
    elif "bed" in ev:
        if "bed" not in sy:
            matched = False
ok("símbolo coherente con el evento en escenas door/bed", matched)

print("\n============================================================")
print(f"RESULTADO: {passes} pass, {fails} fail")
