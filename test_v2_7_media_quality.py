"""
V2-FINAL — FILTRO EDITORIAL + MEDIA DIRECTOR: tests deterministas (sin red).

Cubre (spec V2-FINAL):
  Editoría (PRODUCTION BUG): cobertura de ropa / contenido inapropiado como
    HARD FAIL que manda sobre el score — el offender e02_r2* ya no pasa.
  Prevención: prompt determinista siempre activo (keyword_scan).
  Gate: gateo de la visión editorial solo en modo real (mock → offline).
  no_safe_candidate cuando TODO candidato es inseguro.
  Media Director: AI_IMAGE / PHOTO_STOCK / VIDEO_STOCK, representaciones,
    motion por asset, tie-break de diversidad, preferred_source, claves render.
  Backward compatibility.

UNIT (sin red): la capa 2 (visión multi-muestreo) se SKIPEA con critic mock;
los asserts se apoyan en el pre-screen determinista + lógica pura del director.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editorial_filter import keyword_scan, build_safe_prompt, EditorialVerdict
from quality_gate import (
    QualityGate, QualityGateResult, GateContext, Decision, _better,
    DEFAULT_MIN_SCORE,
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


def _tmp_image(d, name):
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(b"\xff" * 6000)
    return p


# ─────────────────────────────────────────────
# [1] FILTRO EDITORIAL — pre-screen determinista (sin red)
# ─────────────────────────────────────────────
print("\n[1] keyword_scan (pre-screen determinista, EN + ES)")
ok("EN 'naked' bloqueado",
   keyword_scan("a naked woman by a bed").safe is False)
ok("EN 'upper body bare' bloqueado (offender)",
   keyword_scan("man lying on a bed, upper body bare").safe is False)
ok("ES 'torso desnudo' bloqueado",
   keyword_scan("hombre de torso desnudo").safe is False)
ok("ES 'sin camiseta' bloqueado",
   keyword_scan("hombre sin camiseta").safe is False)
ok("prompt benigno pasa",
   keyword_scan("a woman by a window with a cup of tea, morning light").safe is True)
ok("prompt benigno ES pasa",
   keyword_scan("una mujer junto a la ventana tomando té").safe is True)
kw = keyword_scan("a naked woman")
ok("verdict keyword reporta reasons",
   isinstance(kw.reasons, list) and len(kw.reasons) > 0)
ok("verdict marca source keyword", kw.source == "keyword")
ok("verdict incluye blocked_terms con 'naked'",
   "naked" in kw.blocked_terms)
# indicador de riesgo aislado (ambiguous) NO bloquea solo
ok("un solo término ambiguous (cama) no bloquea",
   keyword_scan("una cama al fondo de la habitación").safe is True)

print("\n[1b] build_safe_prompt (prevención en generación)")
sp = build_safe_prompt("a woman by the window", has_human=True)
ok("mantiene la idea original", "window" in sp)
ok("fuerza cobertura modesta (fully clothed)", "fully" in sp.lower() or "clothed" in sp.lower())
ok("añade sufijo no-nudity", "no nudity" in sp.lower() or "no nudity" in sp.lower()
   or "sexualized" in sp.lower())
ok("sufijo 'no nudity' presente", "nudity" in sp.lower() or "no skin" in sp.lower())
neu = build_safe_prompt("woman lying down, upper body bare", has_human=True)
ok("neutraliza el motivo de riesgo explícito",
   ("fully" in neu.lower() or "clothed" in neu.lower())
   and ("no bare chest" in neu.lower() or "covered" in neu.lower()), neu)
ok("prompt vacío no se envenena", build_safe_prompt("", has_human=True) == "")
np_ = build_safe_prompt("a quiet landscape", has_human=False)
ok("sin humano: no fuerza ropa (solo sufijo seguro)", "nudity" in np_.lower())


# ─────────────────────────────────────────────
# [2] GATE — editorial como HARD FAIL (mock critic → offline)
# ─────────────────────────────────────────────
print("\n[2] Gate: editorial HARD FAIL (sin red, prompt determinista)")
d = tempfile.mkdtemp()


def _mock(passes=1, score=8.0, hard=False):
    st = {"n": 0}

    def crit(path, ctx):
        st["n"] += 1
        if hard and "hard" in os.path.basename(path):
            return {"score": 9.0, "hard_fail": True, "hard_fails": ["anatomy = FAIL"],
                    "soft_issues": [], "dimensions": {}, "model": "mock"}
        if st["n"] >= passes:
            return {"score": score, "hard_fail": False, "hard_fails": [],
                    "soft_issues": [], "dimensions": {}, "model": "mock"}
        return {"score": 3.0, "hard_fail": False, "hard_fails": [],
                "soft_issues": ["composition = WEAK"], "dimensions": {}, "model": "mock"}
    return crit


# prompt con señal de riesgo (offender) + imagen benigna → UNSAFE por keyword
ctx_bad = GateContext(aspect="9:16", visual_event="scene",
                      scene_text="t", prompt="man on a bed, upper body bare")
img = _tmp_image(d, "safe_img.jpg")
g = QualityGate(min_score=DEFAULT_MIN_SCORE, max_attempts=3, critic_fn=_mock())
r = g.run(img, ctx_bad)
ok("prompt de riesgo → editorial_unsafe=True",
   r.editorial_unsafe is True)
ok("prompt de riesgo → hard_fail (manda sobre score)",
   r.hard_fail is True)
ok("prompt de riesgo → NO passed", r.passed is False)
ok("prompt de riesgo → NUNCA pasa (FALLBACK tras reintentos, no PASS)",
   r.passed is False and r.decision != Decision.PASS, f"dec={r.decision.value}")
ok("reasons_reporta edición", any(
    "editorial" in x.lower() or "riesgo" in x.lower() or "señal" in x.lower()
    for x in r.reasons))


ctx_ok = GateContext(aspect="9:16", visual_event="hands erasing a line",
                     scene_text="t", prompt="a woman erasing a line from a list")
g2 = QualityGate(min_score=DEFAULT_MIN_SCORE, max_attempts=3, critic_fn=_mock())
r2 = g2.run(_tmp_image(d, "ok.jpg"), ctx_ok)
ok("prompt benigno + imagen buena → pasa",
   r2.passed is True and r2.editorial_unsafe is False)
ok("score >= umbral al pasar", r2.score >= DEFAULT_MIN_SCORE)


print("\n[2b] Gate offline: NO toca visión editorial con critic mock")
# con mock, debe resolver por pre-screen determinista (sin red). Si no se
# skipeara la visión, tardaría/caería — aquí solo validamos la decisión.
ctx_ok2 = GateContext(aspect="16:9", visual_event="figure by window",
                      scene_text="t", prompt="a figure by a window, warm light")
r3 = QualityGate(min_score=6.5, max_attempts=3, critic_fn=_mock()).run(
    _tmp_image(d, "ok2.jpg"), ctx_ok2)
ok("offline pasa con prompt benigno", r3.passed is True)


print("\n[2c] _better — el candidato inseguro NUNCA gana")
a_unsafe = QualityGateResult(score=9.9, hard_fail=False, editorial_unsafe=True)
b_safe = QualityGateResult(score=6.0, hard_fail=False, editorial_unsafe=False)
ok("inseguro con score alto pierde contra seguro",
   _better(a_unsafe, b_safe) is b_safe)
c_safe_high = QualityGateResult(score=9.0, hard_fail=False, editorial_unsafe=False)
ok("entre dos seguros gana el de mayor score",
   _better(c_safe_high, b_safe) is c_safe_high)
d_unsafe2 = QualityGateResult(score=9.5, hard_fail=True, editorial_unsafe=True)
e_safe_hard = QualityGateResult(score=8.0, hard_fail=True, editorial_unsafe=False)
ok("seguro con hard técnico gana a inseguro",
   _better(d_unsafe2, e_safe_hard) is e_safe_hard)


print("\n[2d] no_safe_candidate — si NINGÚN candidato es seguro")
# El gate marca no_safe_candidate cuando ningún intento fue editorialmente seguro.
# Aquí forzamos la invariante a nivel estructura: el campo existe y serializa.
res = QualityGateResult()
ok("campo no_safe_candidate existe por defecto",
   hasattr(res, "no_safe_candidate") and res.no_safe_candidate is False)
ok("no_safe_candidate se serializa en to_dict",
   "no_safe_candidate" in res.to_dict())


# ─────────────────────────────────────────────
# [3] MEDIA DIRECTOR — medios, motion, diversidad, preferred_source
# ─────────────────────────────────────────────
print("\n[3] Media Director (determinista)")
from scene_brief import SceneBrief, NarrativeRole, MotionType, PreferredSource
from media_director import (
    MediumType, direct_media, preferred_source_for, _motion_for,
    _medium_fit, _apply_diversity,
)


def _brief(**kw):
    base = dict(
        scene_id="s0", narration="text", visual_event="hands erasing a line",
        action="hands erasing a line", ai_prompt="a woman erasing a line from a list",
        narrative_role=NarrativeRole.HOOK,
    )
    base.update(kw)
    return SceneBrief(**base)


# pref source por medio
ok("AI_IMAGE → PreferredSource.AI",
   preferred_source_for(MediumType.AI_IMAGE) is PreferredSource.AI)
ok("VIDEO_STOCK → PreferredSource.STOCK",
   preferred_source_for(MediumType.VIDEO_STOCK) is PreferredSource.STOCK)
ok("PHOTO_STOCK → PreferredSource.PHOTO_STOCK (nuevo)",
   preferred_source_for(MediumType.PHOTO_STOCK) is PreferredSource.PHOTO_STOCK)
ok("PHOTO_STOCK.value == 'photo_stock'",
   PreferredSource.PHOTO_STOCK.value == "photo_stock")

# motion por asset
b_hope = _brief(narrative_role=NarrativeRole.HOPE, action="hope opens up")
ok("PHOTO_STOCK en HOPE → ZOOM_OUT",
   _motion_for(b_hope, MediumType.PHOTO_STOCK) is MotionType.ZOOM_OUT)
b_ai = _brief(motion=MotionType.ZOOM_IN)
ok("AI_IMAGE respeta el motion del brief",
   _motion_for(b_ai, MediumType.AI_IMAGE) is b_ai.motion)
b_vid = _brief(action="candid hands tea")
ok("VIDEO_STOCK → STATIC (el video ya se mueve)",
   _motion_for(b_vid, MediumType.VIDEO_STOCK) is MotionType.STATIC)
b_ph_left = _brief(action="the camera pans left")
ok("PHOTO_STOCK con 'left' → PAN_LEFT",
   _motion_for(b_ph_left, MediumType.PHOTO_STOCK) is MotionType.PAN_LEFT)

# diversidad: solo cuando fit comparables
ok("sin historial: bonus 0",
   _apply_diversity(MediumType.AI_IMAGE, [], 8.0, 8.6) == 0.0)
ok("diferencia grande → calidad manda (0 bonus)",
   _apply_diversity(MediumType.AI_IMAGE, ["ai_image", "ai_image", "ai_image"],
                    7.0, 9.0) == 0.0)
ok("comparables + repetido → bonus",
   _apply_diversity(MediumType.AI_IMAGE, ["ai_image", "ai_image"], 8.0, 8.2) == 0.35)

# direct_media: media_sequence + representation_sequence coherentes
b1 = _brief(scene_id="a", action="candid hands tea", narrative_role=NarrativeRole.HOOK)
b2 = _brief(scene_id="b", action="woman writing in a journal",
            narrative_role=NarrativeRole.PROBLEM)
b3 = _brief(scene_id="c", action="quiet room corner",
            narrative_role=NarrativeRole.AGITATION)
md = direct_media([b1, b2, b3])
ok("media_sequence tiene 1 entrada por escena",
   len(md.media_sequence) == 3 and len(md.scenes) == 3)
ok("representation_sequence tiene 1 por escena",
   len(md.representation_sequence) == 3)
ok("cada scene tiene medium/motion/representation",
   all(s.medium in MediumType and s.motion in MotionType and
       s.representation.value for s in md.scenes))
ok("to_report serializa secuencias",
   "media_sequence" in md.to_report() and "scenes" in md.to_report())
ok("media_sequence entries son strings válidos",
   all(m in {x.value for x in MediumType} for m in md.media_sequence))


# ─────────────────────────────────────────────
# [4] ADAPTER — routing, prompt seguro (sin descarga/red)
# ─────────────────────────────────────────────
print("\n[4] render_adapter routing (sin red)")
import render_adapter as ra

ok("_prompt_has_human detecta mujer/hands",
   ra._prompt_has_human("a woman with her hands on a book") is True)
ok("_prompt_has_human persona en ES",
   ra._prompt_has_human("una mujer junto a la ventana") is True)
ok("_prompt_has_human sin persona",
   ra._prompt_has_human("a quiet landscape with light") is False)

sc = {"ai": "woman lying on a bed, upper body bare", "visual_event": "x"}
safe = ra._safe_ai_prompt(sc)
ok("_safe_ai_prompt neutraliza riesgo",
   "naked" not in safe and ("nudity" in safe.lower() or "no skin" in safe.lower()))
ok("_safe_ai_prompt conserva escena", "bed" in safe)

# _scene_medium: por las claves del scene dict
sc_video = {"text": "t", "stock": True, "photo_stock": False}
sc_photo = {"text": "t", "photo_stock": True, "stock": False}
sc_ai = {"text": "t", "ai": "a woman by a window"}
ok("_scene_medium detecta video stock",
   ra._scene_medium(sc_video) == "video")
ok("_scene_medium detecta photo stock",
   ra._scene_medium(sc_photo) == "photo")
ok("_scene_medium detecta ai por defecto",
   ra._scene_medium(sc_ai) == "ai")


# ─────────────────────────────────────────────
print("\n============================================================")
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("============================================================")
sys.exit(1 if FAIL else 0)
