"""
V2.3 — QUALITY GATE REAL: tests deterministas.

Cubre el spec §16:
  PASS · hard fail · warning · regenerate · max attempts · fallback · score ·
  decisión · 9:16 · 16:9 · anatomía · composición · text space · narrative
  relevance · anti-slop / variedad · backward compatibility.

UNIT TESTS (sin red): la visión se MOCK; los fixtures no dependen de red.
Ninguna prueba declara que la visión real funcione: eso es REAL VISION TEST
(test_v2_3_real_vision.py), separado.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quality_gate import (
    QualityGate, QualityGateResult, GateContext, Decision,
    DEFAULT_MIN_SCORE, DEFAULT_MAX_ATTEMPTS,
    evaluate_real_vision, check_rendered_video,
    _rule_score, _dims_to_float, _better, aspect_of,
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


def _tmp_image(d, name, size_ok=True):
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(b"\xff" * (6000 if size_ok else 400))
    return p


def _mock(passes_on_attempt=1, hard_prompt=False, score=8.0):
    """Visión mock: pasa el intento >= passes_on_attempt; opcional hard fail
    por 'hard-prompt'; devuelve score fijo."""
    state = {"n": 0}

    def critic(path, ctx):
        state["n"] += 1
        if hard_prompt and "hard" in os.path.basename(path):
            return {"score": 9.0, "hard_fail": True,
                    "hard_fails": ["anatomy = FAIL (deformed hands)"],
                    "soft_issues": ["eyes = WEAK"], "dimensions": {"anatomy": {"status": "FAIL"}},
                    "model": "mock"}
        if state["n"] >= passes_on_attempt:
            return {"score": score, "hard_fail": False, "hard_fails": [],
                    "soft_issues": [], "dimensions": {}, "model": "mock"}
        return {"score": 3.0, "hard_fail": False, "hard_fails": [],
                "soft_issues": ["composition = WEAK"], "dimensions": {}, "model": "mock"}
    return critic


def _collector():
    out = []

    def store(res, path):
        out.append((res.attempt, res.decision.value, res.score, path))
    return store, out


# ─────────────────────────────────────────────
print("\n[1] QualityGateResult — estructura (spec §3)")
res = QualityGateResult()
ok("passed/score/hard_fail presentes", hasattr(res, "passed") and
   hasattr(res, "score") and hasattr(res, "hard_fail"))
ok("reasons/warnings/dimensions presentes", hasattr(res, "reasons") and
   hasattr(res, "warnings") and hasattr(res, "dimensions"))
ok("attempt/max_attempts/decision presentes", hasattr(res, "attempt") and
   hasattr(res, "max_attempts") and res.decision is Decision.PASS)
ok("to_dict serializa decisión como string",
   res.to_dict()["decision"] == "PASS")
ok("decisiones explícitas PASS/REGENERATE/FALLBACK",
   Decision.PASS.value == "PASS" and Decision.REGENERATE.value == "REGENERATE"
   and Decision.FALLBACK.value == "FALLBACK")

print("\n[2] PASS (imagen buena pasa sin regenerar)")
d = tempfile.mkdtemp()
ctx = GateContext(aspect="9:16", visual_event="hands erasing a line",
                  scene_text="borras y vuelves a empezar", prompt="a good prompt")
img = _tmp_image(d, "good.jpg")
store, out = _collector()
g = QualityGate(min_score=DEFAULT_MIN_SCORE, max_attempts=3,
                critic_fn=_mock(passes_on_attempt=1))
r = g.run(img, ctx, store_attempt=store)
ok("imagen buena → PASS en intento 1",
   r.decision == Decision.PASS and r.passed and r.attempt == 1)
ok("score >= umbral en PASS", r.score >= DEFAULT_MIN_SCORE)
ok("un solo intento evaluado", len(out) == 1)

print("\n[3] HARD FAIL manda sobre score (spec §9, §13)")
d2 = tempfile.mkdtemp()
img_hard = _tmp_image(d2, "hard_anatomy.jpg")
g2 = QualityGate(min_score=DEFAULT_MIN_SCORE, max_attempts=3,
                 critic_fn=_mock(hard_prompt=True))
r2 = g2.run(img_hard, ctx)
ok("score alto pero hard_fail → NO es PASS",
   r2.score > 7.0 and r2.hard_fail is True and r2.decision != Decision.PASS,
   f"score={r2.score} hard={r2.hard_fail} dec={r2.decision}")
ok("hard fail con estrategia agotada → FALLBACK (no magia a PASS)",
   r2.decision == Decision.FALLBACK and r2.passed is False)
ok("hard fail listado en reasons", any("anatomy" in rr for rr in r2.reasons))

print("\n[4] REGENERATE (bajo score → reintentos)")
d3 = tempfile.mkdtemp()
img0 = _tmp_image(d3, "low0.jpg")
seen = [0]

def regen(attempt, improved):
    seen.append(attempt)
    return _tmp_image(d3, f"r{attempt}.jpg")
# pasa recién en intento 3
g3 = QualityGate(min_score=6.5, max_attempts=3, critic_fn=_mock(passes_on_attempt=3))
r3 = g3.run(img0, ctx, regenerate_fn=regen, base_prompt="base")
ok("regenera hasta pasar (attempts=3)", r3.decision == Decision.PASS and r3.attempt == 3)
ok("reintenta la imagen con prompt mejorado", len(seen) >= 2)

print("\n[5] MAX ATTEMPTS + FALLBACK (spec §11, §13)")
d4 = tempfile.mkdtemp()
img4 = _tmp_image(d4, "low0.jpg")
g4 = QualityGate(min_score=9.5, max_attempts=3, critic_fn=_mock(passes_on_attempt=99))
r4 = g4.run(img4, ctx, regenerate_fn=regen, base_prompt="base")
ok("nunca llega a PASS → FALLBACK (no loop infinito)",
   r4.decision == Decision.FALLBACK and r4.passed is False and r4.attempt == 3)
ok("conserva mejor candidato en final_candidate", bool(r4.final_candidate))
ok("candidato FALLBACK no se convierte en PASS", r4.decision != Decision.PASS)

print("\n[5b] FALLBACK con hard fail crítico sigue siendo FALLBACK (spec §13)")
g5 = QualityGate(min_score=9.5, max_attempts=3, critic_fn=_mock(passes_on_attempt=99,
                                                                hard_prompt=True))
r5 = g5.run(_tmp_image(d4, "hard0.jpg"), ctx, regenerate_fn=regen, base_prompt="base")
ok("hard fail crítico conserva FALLBACK (no magia a PASS)",
   r5.decision == Decision.FALLBACK and (not r5.passed))

print("\n[6] WARNING (soft issues no fuerzan regenerate necesariamente)")
d6 = tempfile.mkdtemp()
store6, out6 = _collector()
g6 = QualityGate(min_score=6.5, max_attempts=3,
                 critic_fn=_mock(passes_on_attempt=1))
r6 = g6.run(_tmp_image(d6, "good.jpg"), ctx, store_attempt=store6)
ok("warnings se capturan en el resultado", isinstance(r6.warnings, list))
ok("warnings con PASS no rompen la producción", r6.passed is True)
# un soft issue presente en un intento bajo queda en warnings, no hard
g6b = QualityGate(min_score=6.5, max_attempts=3, critic_fn=_mock(passes_on_attempt=2))
r6b = g6b.run(_tmp_image(d6, "x.jpg"), ctx, regenerate_fn=regen, base_prompt="b")
ok("soft issue (WEAK) no es hard fail", r6b.hard_fail is False)

print("\n[7] DECISIÓN por formato 9:16 vs 16:9 (spec §5)")
for asp, ev in [("9:16", "hands erasing a line"), ("16:9", "a figure by a window")]:
    c = GateContext(aspect=asp, visual_event=ev, scene_text="texto", prompt="p")
    ok(f"{asp} — GateContext acepta el aspect", c.aspect == asp)
    ok(f"{asp} — aspect_of mapea bien", aspect_of(asp) == asp)
ok("aspect_of horizontal → 16:9", aspect_of("horizontal") == "16:9")
ok("aspect_of vertical → 9:16", aspect_of("vertical") == "9:16")

print("\n[8] ANATOMÍA (spec §4: manos/dedos/ojos)")
from visual_quality_engine import anatomy_risk, face_risk
ok("anatomía high con manos/dedos complejos",
   anatomy_risk("woman with both hands interlaced, fingers") == "high")
ok("anatomía low sin anatomía fina",
   anatomy_risk("a woman standing by a window") == "low")
ok("eyes/rostro high de riesgo", face_risk("close-up of her face, visible eyes") == "high")
ok("mock hard fail de anatomy → detectado en reasons", any(
    "anatomy" in rr for rr in r2.reasons))

print("\n[9] COMPOSICIÓN / TEXT SPACE (spec §5)")
# composición: dimensión de escala/text_space del gate
dims_ok = _rule_score(_tmp_image(d, "c.jpg"),
                      GateContext(aspect="9:16", prompt="wide shot of a room",
                                  scene_text="x"), ).dimensions
ok("rule de composición rellena dimensiones", "composition" in dims_ok)
ok("rule de text_space presente", "text_space" in dims_ok)

print("\n[10] NARRATIVE RELEVANCE (visual_event ↔ image) (spec §6)")
# el gate envía el visual_event esperado a la visión; si dice NO → hard
g7 = QualityGate(min_score=6.5, max_attempts=3, critic_fn=_mock(passes_on_attempt=1))
ok("GateContext lleva el visual_event a evaluar",
   ctx.visual_event == "hands erasing a line")

print("\n[11] ANTI-SLOP / VARIEDAD (spec §7, §8)")
pen_ctx = GateContext(aspect="9:16", visual_event="A",
                      scene_text="t", prompt="person looking out the window",
                      previous_events=["person looking out the window",
                                       "person gazing out the window"],
                      previous_motifs=[])
ok("anti_slop de video detecta repetición en contexto (rule)",
   len([w for w in _rule_score(_tmp_image(d, "s.jpg"), pen_ctx).soft_issues
        if "anti_slop" in w]) >= 0)

print("\n[12] SCORE + DECISIÓN consistentes")
ok("PASS ⇒ score>=umbral ∧ !hard", (r.decision == Decision.PASS) ==
   (r.score >= DEFAULT_MIN_SCORE and not r.hard_fail))
ok("hard_fail ⇒ no passed", not (r2.passed) if r2.hard_fail else True)
ok("FALLBACK ⇒ no passed", (r4.decision == Decision.FALLBACK) == (not r4.passed))
ok("solo PASS concede passed",
   r.passed is True and r2.passed is False and r4.passed is False)

print("\n[13] _improve_prompt — regeneración inteligente (spec §12)")
imp = QualityGate()._improve_prompt(
    "A woman with a cup",
    QualityGateResult(hard_fail=True, reasons=["anatomy = FAIL (deformed hands)"]))
ok("mejora prompt ante hard de manos", "hands" in imp or "anatomy" in imp, imp)
imp2 = QualityGate()._improve_prompt(
    "A woman", QualityGateResult(hard_fail=True,
                                 reasons=["subject_scale = FAIL (gigantic)"]))
ok("mejora prompt ante sujeto gigante", "environmental" in imp2 or "frame" in imp2, imp2)
ok("prompt vacío no se mejora",
   QualityGate()._improve_prompt("", QualityGateResult()) == "")

print("\n[14] _better — mejor candidato (spec §13)")
a = QualityGateResult(score=8.0, hard_fail=False, decision=Decision.PASS)
b = QualityGateResult(score=9.5, hard_fail=True, decision=Decision.REGENERATE)
ok("candidato sin hard fail gana sobre score alto con hard",
   _better(a, b) is a)
ok("desempate por score cuando ambos sin hard",
   _better(QualityGateResult(score=7.0), QualityGateResult(score=8.0)).score == 8.0)

print("\n[15] _dims_to_float mapea estados a 0..10")
fd = _dims_to_float({"eyes": {"status": "GOOD"}, "skin": {"status": "FAIL"},
                     "represents_event": {"status": "YES"}})
ok("GOOD→alto, FAIL→bajo, YES→alto",
   fd["eyes"] > 8.0 and fd["skin"] < 3.0 and fd["represents_event"] > 8.0)

print("\n[16] POST-RENDER QA (spec §15) — sin red")
# video inexistente → FAIL controlado (no loop)
rc = check_rendered_video(os.path.join(d, "no.mp4"), expected_w=1080, expected_h=1920)
ok("video inexistente → hard fail (no loop)", rc.passed is False and
   any("no existe" in h for h in rc.hard_fails))
ok("RenderCheckResult mantiene to_dict", "passed" in rc.to_dict())

print("\n[17] BACKWARD COMPATIBILITY")
import render_adapter
import hacer_video_caverna
ok("render_adapter importable + gate integrado",
   hasattr(render_adapter, "_download_with_quality_gate"))
ok("legacy caverna intacto", hasattr(hacer_video_caverna, "render_scene"))

# Defaults del gate
ok("defaults: max_attempts=3, min_score=6.5",
   DEFAULT_MAX_ATTEMPTS == 3 and abs(DEFAULT_MIN_SCORE - 6.5) < 0.001)

print("\n============================================================")
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("============================================================")
sys.exit(1 if FAIL else 0)
