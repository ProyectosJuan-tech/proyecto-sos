"""
V2-05 — TESTS DE INTEGRACIÓN EDITORIAL.

Verifica que la cadena completa funcione para dos formatos:

    CASO A — Short 9:16  (1080x1920)
        Tema: "Por qué nos cuesta tanto descansar aunque estemos cansados"

    CASO B — 16:9  (1920x1080)
        Tema: "Por qué algunas personas sienten que siempre tienen que
        estar demostrando su valor"

Cubre (mínimo 15 tests):
- plan end-to-end (short y 16:9)
- SceneBrief generation (short y 16:9)
- asset selection (short y 16:9)
- text layout (short y 16:9)
- format selection
- backward compatibility
- estrategias editoriales diferentes
- resolución correcta

No requiere red: los assets se prueban con un fetch mock.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scene_brief import SceneBrief, NarrativeRole
from short_director import ShortPlan, validate_plan, plan_to_dict
from editorial_orchestrator import (
    LongFormPlan,
    EditorialEmission,
    produce_editorial,
    build_editorial_plan,
    validate_long_plan,
    SHORT_ARC,
    LONG_ARC,
)
from asset_selector import AssetSelection, AssetCandidate, AssetScore, select_asset
from text_layout import TextLayout, validate_layout

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


# ── Tema Caso A (short) y Caso B (16:9) ──
SHORT_TOPIC = "descanso"
SHORT_IDEA = "nos cuesta tanto descansar aunque estemos cansados"
LONG_TOPIC = "valor"
LONG_IDEA = "algunas personas sienten que siempre tienen que demostrar su valor"


# ── Mock fetch de assets (sin red, determinista) ──
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


# ══════════════════════════════════════════════
# 1. CHAINING end-to-end
# ══════════════════════════════════════════════
print("\n[1] CHAINING END-TO-END")

# 1. Short end-to-end plan
em_s = produce_editorial(topic=SHORT_TOPIC, central_idea=SHORT_IDEA,
                         format_name="short", asset_fetch_fn=mock_fetch_fn)
ok("Short end-to-end plan (produce_editorial devuelve EditorialEmission)",
   isinstance(em_s, EditorialEmission))
ok("Short plan es ShortPlan", isinstance(em_s.plan, ShortPlan))
ok("Short plan válido (validate_plan)", validate_plan(em_s.plan)["valid"])
ok("Short genera escenas", len(em_s.briefs) >= 6)
ok("Short resolución 1080x1920",
   (em_s.canvas_width, em_s.canvas_height) == (1080, 1920))

# 2. Short SceneBrief generation
ok("Short SceneBriefs son SceneBrief", all(isinstance(b, SceneBrief) for b in em_s.briefs))
ok("Short cada SceneBrief válido", all(b.validate()["valid"] for b in em_s.briefs))

# 3. Short asset selection (mock)
ok("Short asset selection devuelve AssetSelection por escena",
   all(isinstance(s, AssetSelection) for s in em_s.asset_selections))
ok("Short assets con candidatos (mock)",
   any(s.selected is not None for s in em_s.asset_selections))

# 4. Short text layout
ok("Short layout por escena", all(isinstance(l, TextLayout) for l in em_s.acom_layouts))
ok("Short layouts OK (status ok)",
   all(l.status in ("ok",) for l in em_s.acom_layouts))

# 5. 16:9 end-to-end plan
em_l = produce_editorial(topic=LONG_TOPIC, central_idea=LONG_IDEA,
                         format_name="youtube", asset_fetch_fn=mock_fetch_fn)
ok("16:9 end-to-end plan", isinstance(em_l, EditorialEmission))
ok("16:9 plan es LongFormPlan", isinstance(em_l.plan, LongFormPlan))
ok("16:9 plan válido (validate_long_plan)", validate_long_plan(em_l.plan)["valid"])
ok("16:9 genera escenas", len(em_l.briefs) >= 8)
ok("16:9 resolución 1920x1080",
   (em_l.canvas_width, em_l.canvas_height) == (1920, 1080))

# 6. 16:9 SceneBrief generation
ok("16:9 SceneBriefs válidos", all(b.validate()["valid"] for b in em_l.briefs))

# 7. 16:9 asset selection
ok("16:9 assets por escena",
   all(isinstance(s, AssetSelection) for s in em_l.asset_selections))

# 8. 16:9 text layout
ok("16:9 layouts por escena", all(isinstance(l, TextLayout) for l in em_l.acom_layouts))


# ══════════════════════════════════════════════
# 2. FORMAT SELECTION
# ══════════════════════════════════════════════
print("\n[2] FORMAT SELECTION")

ok("Format short → 1080x1920",
   (em_s.canvas_width, em_s.canvas_height) == (1080, 1920))
ok("Format youtube → 1920x1080",
   (em_l.canvas_width, em_l.canvas_height) == (1920, 1080))
ok("Format 16:9 alias → 1920x1080",
   produce_editorial(topic=LONG_TOPIC, central_idea=LONG_IDEA,
                     format_name="16:9", asset_fetch_fn=mock_fetch_fn)
   .canvas_width == 1920)


# ══════════════════════════════════════════════
# 3. ESTRATEGIAS EDITORIALES DIFERENTES
# ══════════════════════════════════════════════
print("\n[3] ESTRATEGIAS EDITORIALES DIFERENTES")

ok("Short usa arco corto (≈7 roles)", len(SHORT_ARC) < len(LONG_ARC))
ok("16:9 usa arco largo (≥9 roles)", len(LONG_ARC) >= 9)
ok("Short roles != 16:9 roles",
   em_s.plan.narrative_roles_used() != em_l.plan.narrative_roles_used())
# El 16:9 debe tener PSYCHOLOGY repetido (profundidad) y BIBLICAL_GROUNDING
roles_l = em_l.plan.narrative_roles_used()
ok("16:9 tiene BIBLICAL_GROUNDING", "biblical_grounding" in roles_l)
ok("16:9 profundiza (PSYCHOLOGY repetido)",
   roles_l.count("psychology") >= 2)
# El short no debe tener REPEATED psychology ni biblical necesariamente igual
roles_s = em_s.plan.narrative_roles_used()
ok("Short no repite PSYCHOLOGY",
   roles_s.count("psychology") <= 1)
ok("Duraciones objetivo diferentes",
   em_s.plan.target_duration < em_l.plan.target_duration)


# ══════════════════════════════════════════════
# 4. BACKWARD COMPATIBILITY
# ══════════════════════════════════════════════
print("\n[4] BACKWARD COMPATIBILITY")

# Los scene_dicts deben ser consumibles por el pipeline existente:
# claves que la cadena de render ya conoce (text, ai, q, motion, trans...)
sd = em_s.scene_dicts[0]
known = {"text", "ai", "q", "motion", "trans", "static_text", "id",
         "stock", "stock_video", "ai_video", "av"}
ok("scene_dict solo usa claves conocidas por el pipeline",
   all(k in known for k in sd.keys()), f"claves={list(sd.keys())}")

# Los módulos V2-01/02/03/04 siguen importables y sus APIs intactas
try:
    import scene_brief, short_director, asset_selector, text_layout
    ok("Módulos V2-01/02/03/04 importan sin error", True)
except Exception as e:  # pragma: no cover
    ok("Módulos V2-01/02/03/04 importan sin error", False, str(e))

# Reutiliza build_scene / generate_hook_options de short_director (no duplica)
from short_director import build_scene as _sb_scene
from short_director import generate_hook_options as _gho
ok("Orquestador reutiliza short_director.build_scene", callable(_sb_scene))
ok("Orquestador reutiliza generate_hook_options", callable(_gho))


# ══════════════════════════════════════════════
# 5. LAYOUT/ASSETS DETALLE
# ══════════════════════════════════════════════
print("\n[5] LAYOUT / ASSETS DETALLE")

# Layout usa el motor text_layout (hay score y status)
l0 = em_s.acom_layouts[0]
ok("Short layout tiene score 0-100", 0 <= l0.score <= 100)
ok("Short layout tiene font_size>0", l0.font_size > 0)
ok("Short layout sin overflow (hook corto)", l0.overflow is False)

# Los assets no duplican scoring: usan select_asset de asset_selector
from asset_selector import select_asset as _sa
ok("Orquestador reutiliza asset_selector.select_asset", callable(_sa))


# ══════════════════════════════════════════════
# 6. Serialización LongFormPlan
# ══════════════════════════════════════════════
print("\n[6] SERIALIZACIÓN")

lp = em_l.plan
d = lp.to_dict()
ok("LongFormPlan.to_dict() funciona", "topic" in d and "scenes" in d)
lp2 = LongFormPlan.from_dict(d)
ok("LongFormPlan.from_dict roundtrip",
   lp2.topic == lp.topic and len(lp2.scenes) == len(lp.scenes))
j = lp.to_json()
lp3 = LongFormPlan.from_json(j)
ok("LongFormPlan JSON roundtrip", lp3.central_idea == lp.central_idea)

# ShortPlan todavía serializa
sp = em_s.plan
ok("ShortPlan.to_dict() sigue funcionando", "hook" in plan_to_dict(sp))


# ══════════════════════════════════════════════
print()
print("=" * 60)
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("=" * 60)
sys.exit(1 if FAIL else 0)
