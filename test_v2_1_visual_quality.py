"""
V2.1 — TESTS DEL VISUAL QUALITY ENGINE.

Cubre PASO 11 (mínimo 15 tests):
 1. 16:9 asset demasiado grande (subject scale)
 2. 16:9 crop (smart_crop_geometry + apply_crop)
 3. 16:9 text-safe area
 4. 9:16 safe area
 5. human realism score
 6. skin realism score
 7. anatomy penalty
 8. facial quality penalty
 9. visual/text mismatch
10. anti-slop repetition
11. regeneration threshold
12. max regeneration attempts
13. fallback
14. prompt construction
15. backward compatibility

Todos DETERMINISTAS: sin red, sin API externa, sin imágenes reales.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visual_quality_engine import (
    VisualQualityScore,
    VisualQualityEngine,
    RegenerationEngine,
    RegenerationResult,
    smart_crop_geometry,
    apply_crop,
    score_composition_16x9,
    score_composition_9x16,
    check_subject_scale,
    check_text_space,
    anatomy_risk,
    face_risk,
    skin_risk_word,
    human_realism_rule_score,
    score_narrative_match,
    count_slop,
    anti_slop_penalty,
    build_quality_prompt,
    human_representation_for,
    DEFAULT_SLOP_MOTIFS,
)

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


# ══════════════════════════════════════════════
print("[1] 16:9 — ASSET DEMASIADO GRANDE (PROBLEMA A)")
# ══════════════════════════════════════════════
# Un sujeto que ocupa >85% del canvas = composición rota
s, why = check_subject_scale((0.0, 0.0, 1.0, 1.0))   # ocupa todo
ok("sujeto a todo el canvas → escala baja (mala)",
   s < 5.0, f"score={s}")
s2, _ = check_subject_scale((0.28, 0.25, 0.72, 0.65))  # normal medio
ok("sujeto proporcionado → escala alta (buena)",
   s2 > 8.0, f"score={s2}")

print("\n[2] 16:9 — CROP")
# ══════════════════════════════════════════════
box = smart_crop_geometry(1080, 1920, target_ar="16:9")   # 9:16 → 16:9
w = box[2] - box[0]; h = box[3] - box[1]
ok("smart_crop 9:16→16:9 produce rect 16:9 (w/h≈1.78)",
   abs((w / h) - (16 / 9)) < 0.01, f"w={w} h={h}")
box2 = smart_crop_geometry(1920, 1080, target_ar="9:16")   # 16:9 → 9:16
w2 = box2[2] - box2[0]; h2 = box2[3] - box2[1]
ok("smart_crop 16:9→9:16 produce rect 9:16 (w/h≈0.5625)",
   abs((w2 / h2) - (9 / 16)) < 0.01, f"w={w2} h={h2}")

# apply_crop con PIL determinista
from PIL import Image
im = Image.new("RGB", (1080, 1920), (120, 120, 120))
cropped = apply_crop(im, smart_crop_geometry(1080, 1920, "16:9"))
ok("apply_crop recorta a la geometría calculada",
   cropped.width > 0 and abs((cropped.width / cropped.height) - (16 / 9)) < 0.01,
   f"{cropped.width}x{cropped.height}")

print("\n[3] 16:9 — TEXT-SAFE AREA")
# ══════════════════════════════════════════════
# sujeto que invade la franja inferior de texto → penalizado
s, _ = check_text_space((0.1, 0.1, 0.9, 0.85), (0.0, 0.74, 1.0, 1.0), "16:9")
s2, _ = check_text_space((0.1, 0.1, 0.9, 0.60), (0.0, 0.74, 1.0, 1.0), "16:9")
ok("sujeto entra en zona de texto 16:9 → baja",
   s < s2 and s < 5.0, f"invade={s} respeta={s2}")

print("\n[4] 9:16 — SAFE AREA")
# ══════════════════════════════════════════════
cs = score_composition_9x16(subject_box=(0.2, 0.18, 0.8, 0.62),  # sujeto en tercio superior
                            focal_point=(0.5, 0.4))
cs_bad = score_composition_9x16(subject_box=(0.0, 0.0, 1.0, 0.95),  # invade todo/toca bordes
                                focal_point=(0.5, 0.9))
ok("9:16 composición sana > mala", cs[0] > cs_bad[0], f"{cs[0]} vs {cs_bad[0]}")

print("\n[5] HUMAN REALISM")
# ══════════════════════════════════════════════
ok("prompt con realismo explícito puntúa alto",
   human_realism_rule_score(
       "Woman with natural skin texture, visible pores, small blemishes, "
       "candid, realistic skin") > 8.0,
   human_realism_rule_score("natural skin texture, candid"))
ok("prompt sin señales de realismo puntúa neutral-bajo",
   human_realism_rule_score("A woman") < 7.0)

print("\n[6] SKIN REALISM")
# ══════════════════════════════════════════════
ok("léxico 'porcelain/doll/plastic' → HARD (piel muñeca)",
   skin_risk_word("flawless porcelain doll skin, plastic") == "hard")
ok("léxico 'natural texture/pores/imperfections' → ok",
   skin_risk_word("natural skin texture with visible pores and small imperfections") != "hard")

print("\n[7] ANATOMY PENALTY (PROBLEMA B)")
# ══════════════════════════════════════════════
ok("anatomía HIGH con manos/dedos/abrazos complejos",
   anatomy_risk("woman embracing a plant with both hands, interlaced fingers") == "high")
ok("anatomía LOW sin manos ni interacción fina",
   anatomy_risk("a woman standing by a window") == "low")
# integración: anomalía grave reduce el score total
e = VisualQualityEngine(aspect="16:9")
sc = e.assess(scene_prompt="woman embracing a plant with both hands, interlaced fingers",
              scene_text="una persona abrazando una planta", img_w=1920, img_h=1080)
ok("hands/anatomy HIGH entra a hard_anomalies",
   any("anatomy" in a for a in sc.hard_anomalies), str(sc.hard_anomalies))

print("\n[8] FACIAL QUALITY PENALTY (PROBLEMA B)")
# ══════════════════════════════════════════════
ok("face/eyes de alto riesgo → riesgo facial HIGH",
   face_risk("close-up of her face, looking at camera with visible eyes") == "high")
ok("escena sin rostro → risco facial LOW",
   face_risk("hands placing a cup on the table, no faces visible") == "low")

print("\n[9] VISUAL / TEXT MISMATCH (PASO 8)")
# ══════════════════════════════════════════════
_, _, mism = score_narrative_match(
    "aprendiste a medir cada palabra",
    "A person walking along a beach alone, no one else")
_, _, match = score_narrative_match(
    "aprendiste a medir cada palabra antes de enviarla",
    "A woman hesitating before sending a message on her phone, hand paused")
ok("visual ambient-genérico vs texto con acción → mismatch", mism is True)
ok("visual con micro-acción coherente → match", match is False)
sc = e.assess(scene_prompt="A person walking alone along a beach, generic landscape",
              scene_text="aprendiste a medir cada palabra", img_w=1920, img_h=1080)
ok("mismatch añade hard_anomaly 'visual_text_mismatch'",
   "visual_text_mismatch" in sc.hard_anomalies)

print("\n[10] ANTI-SLOP REPETICIÓN")
# ══════════════════════════════════════════════
once = ["person looking out the window alone"]
repeated = ["person looking out the window", "another looking out the window",
            "and gazing out the window"]
ok("un solo uso de un motivo → sin penalización",
   anti_slop_penalty(once)[0] == 0)
pen, rep = anti_slop_penalty(repeated)
ok("motivo repetido en varias escenas → penalización",
   pen > 0 and "person looking out window" in rep, f"pen={pen} rep={rep}")

print("\n[11] REGENERATION — UMBRAL")
# ══════════════════════════════════════════════
# Evaluador determinista inyectado: path "img_N" → score fijo (sin red/visión)
def make_engine(threshold, max_attempts, path_scores):
    eng = RegenerationEngine(threshold=threshold, max_attempts=max_attempts)

    def _eval(path):
        for pfx, score in path_scores:
            if path == pfx:
                return score, []
        return 0.0, ["sin path"]

    eng.evaluate = _eval
    return eng


def paths(*names):
    n = [0]
    def gen(attempt):
        if n[0] < len(names):
            v = names[n[0]]; n[0] += 1
            return v
        return None
    return gen


# nuances: img_0=5.0, img_1=4.0, img_2=7.0 → pasa en el tercer intento (>=6.5)
eng = make_engine(6.5, 3, [("img_0", 5.0), ("img_1", 4.0), ("img_2", 7.0)])
r = eng.run(paths("img_0", "img_1", "img_2"))
ok("regenera hasta superar el umbral",
   r.ok and r.attempts == 3 and len(r.scores) == 3 and round(r.scores[2], 1) == 7.0,
   f"attempts={r.attempts} scores={r.scores} ok={r.ok}")
# si el segundo ya pasa, corta a los 2 intentos
eng2 = make_engine(6.5, 3, [("img_0", 5.0), ("img_1", 8.0)])
r2 = eng2.run(paths("img_0", "img_1"))
ok("corta al primer intento que pasa el umbral",
   r2.ok and r2.attempts == 2 and r2.scores == [5.0, 8.0],
   f"attempts={r2.attempts}")

print("\n[12] REGENERATION — MÁXIMO DE INTENTOS")
# ══════════════════════════════════════════════
rcap = make_engine(8.0, 2, [("a", 3.0), ("b", 4.0)])   # nunca llega a 8
r2 = rcap.run(paths("a", "b"))
ok("respeta max_attempts sin loop infinito",
   r2.ok is False and r2.attempts == 2 and len(r2.scores) == 2,
   f"attempts={r2.attempts} ok={r2.ok}")

print("\n[13] REGENERATION — FALLBACK")
# ══════════════════════════════════════════════
r3 = rcap.run(paths("a", "b"))
ok("al agotar intentos → fallback activado",
   r3.used_fallback is True and r3.ok is False and r3.final_path is None,
   f"fb={r3.used_fallback}")

print("\n[14] PROMPT CONSTRUCTION")
# ══════════════════════════════════════════════
base = "A woman writing in her journal by a window. Shot on Fujifilm X-T5."
p16 = build_quality_prompt(base, canvas_ar="16:9", has_human=True)
p9 = build_quality_prompt(base, canvas_ar="9:16", has_human=True)
ok("prompt 16:9 incluye ancla composición horizontal",
   "16:9" in p16 and "Horizontal 16:9" in p16)
ok("prompt 9:16 incluye ancla composición vertical",
   "9:16" in p9 and "Vertical 9:16" in p9)
ok("prompt con humano incluye ancla de piel realista",
   "natural texture" in p16 and "doll-like" in p16)
rep = human_representation_for(setting="Buenos Aires, warm kitchen")
ok("representación contextual (Problem C) no excluye por etnia",
   "Latin" in rep and "natural" in rep.lower(), rep)
rep_default = human_representation_for(setting="")
ok("default contextual occidental diverso sin clonar",
   "everyperson" in rep_default)

print("\n[15] BACKWARD COMPATIBILITY")
# ══════════════════════════════════════════════
# el módulo no rompe nada del pipeline legacy
import hacer_video_caverna
import hacer_video_youtube
ok("hacer_video_caverna todavía importable",
   hasattr(hacer_video_caverna, "render_scene"))
ok("hacer_video_youtube todavía importable",
   hasattr(hacer_video_youtube, "render_scene"))
render_adapter_ok = True
try:
    import render_adapter
    ok("render_adapter usa aspect por plataforma (V2.1)",
       hasattr(render_adapter, "_smart_fit_to_aspect"))
except Exception as exc:  # noqa: BLE001
    render_adapter_ok = False
    ok("render_adapter importable", False, str(exc))
# VisualQualityScore construye y computa
scs = VisualQualityScore(dimensions={k: 8.0 for k in VisualQualityScore.DIMENSIONS})
scs.hard_anomalies = ["anatomy"]
scs.compute_total()
ok("VisualQualityScore.compute_total refleja hard anomalies",
   scs.total < 8.0, f"total={scs.total}")


# ══════════════════════════════════════════════
print()
print("=" * 60)
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("=" * 60)
sys.exit(1 if FAIL else 0)
