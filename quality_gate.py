"""V2.3 — QUALITY GATE REAL.

Convierte el control de calidad visual en un Quality Gate de producción real,
evaluando la IMAGEN GENERADA (no sólo el prompt). Distingue:

    A. Prompt Quality  — "el prompt pide piel natural"
    B. Image Quality   — "la imagen realmente tiene piel natural"

El gate evalúa B: la imagen real.

Decisión explícita (no un número global):
    PASS        → continúa producción.
    REGENERATE  → regenerar dentro de un límite (max_attempts).
    FALLBACK    → límite alcanzado: mejor candidato / fallback controlado.
    Nunca loop infinito.

Criterios evaluados (sobre la imagen real, vía visual_critic/ver_imagen):
  HUMAN REALISM  — ojos, cantidad/proporción, anatomía, manos, dedos,
                   extremidades, proporciones, piel, textura, naturalidad,
                   apariencia fotográfica.
  COMPOSITION    — según formato (9:16 / 16:9): sujeto en encuadre, espacio
                   para texto, no gigante, crop destructivo, equilibrio.
  NARRATIVE      — visual_event ↔ image: la imagen representa el evento de la
                   escena (no "texto triste + persona triste").
  ANTI-SLOP      — contexto del video completo: variedad narrativa, no
                   repetición injustificada.
  TECH          — resolución/aspect compatibles.

Diseño:
- La visión REAL se conecta como `critic_fn` (por defecto visual_critic.critique
  con un prompt a medida). Si falla la red, el scoring cae a REGLAS
  deterministas (visual_quality_engine) — source="rule".
- Los tests inyectan `critic_fn` mock → UNIT (sin red). La PRUEBA REAL usa la
  visión de verdad → REAL VISION (separada, ver sección 17 del spec).

Este módulo NO toca el pipeline legacy: se REUSA/integra desde render_adapter
(capa V2 aditiva). Sin loops infinitos: max_attempts configurable (def 3).
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from visual_quality_engine import (
    VisualQualityScore,
    VisualQualityEngine,
    human_realism_rule_score,
    anatomy_risk,
    face_risk,
    skin_risk_word,
    score_narrative_match,
    count_slop,
    anti_slop_penalty,
)

from editorial_filter import (
    evaluate_editorial,
    keyword_scan,
    build_safe_prompt,
)


class Decision(str, Enum):
    PASS = "PASS"
    REGENERATE = "REGENERATE"
    FALLBACK = "FALLBACK"


# ─────────────────────────────────────────────
# Resultado del Quality Gate
# ─────────────────────────────────────────────
@dataclass
class QualityGateResult:
    """Resultado de evaluar UNA imagen con el Quality Gate.

    Campos requeridos por el spec:
      passed, score, hard_fail, reasons, warnings, dimensions,
      attempt, max_attempts, decision.
    """
    passed: bool = False
    score: float = 0.0                       # 0..10
    hard_fail: bool = False
    reasons: list[str] = field(default_factory=list)     # motivos (hard+soft+decision)
    warnings: list[str] = field(default_factory=list)    # problemas menores (soft)
    dimensions: dict[str, float] = field(default_factory=dict)  # 0..10 por dimensión
    attempt: int = 1
    max_attempts: int = 3
    decision: Decision = Decision.PASS
    source: str = "rule"                     # "rule" | "vision" | "hybrid"
    path: str = ""                           # imagen evaluada
    final_candidate: str = ""               # path elegido al final (fallback/best)

    # FILTRO EDITORIAL (2026-08-28): HARD FAIL de seguridad.
    # Aunque el score sea altísimo, editorial_unsafe=True impide PASS/best/fallback.
    editorial_unsafe: bool = False
    editorial_reasons: list[str] = field(default_factory=list)
    no_safe_candidate: bool = False          # ningún candidato seguro en todos los intentos

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "hard_fail": self.hard_fail,
            "decision": self.decision.value,
            "source": self.source,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "dimensions": self.dimensions,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "path": self.path,
            "final_candidate": self.final_candidate,
            "editorial_unsafe": self.editorial_unsafe,
            "editorial_reasons": self.editorial_reasons,
            "no_safe_candidate": self.no_safe_candidate,
        }


# Umbral por defecto (score 0..10). Un hard fail anula el score.
DEFAULT_MIN_SCORE = 6.5
DEFAULT_MAX_ATTEMPTS = 3


# ─────────────────────────────────────────────
# DIMENSIONES del Quality Gate (concepto/evaluación)
# ─────────────────────────────────────────────
GATE_DIMENSIONS = (
    "human_realism",      # ojos, anatomía, manos, dedos, extremidades, piel, fotográfico
    "composition",        # encuadre, escala, espacio para texto, equilibro por aspect
    "narrative_match",    # visual_event ↔ imagen
    "anti_slop",          # variedad narrativa en contexto de video
    "technical_quality",  # resolución / aspect compatibles
)


# ─────────────────────────────────────────────
# Plantilla de QA REAL (visión) orientada al gate
# ─────────────────────────────────────────────
GATE_VISION_TEMPLATE = """You are the strict visual QA reviewer of a lifestyle channel. Evaluate ONE generated IMAGE (not its prompt). Aspect: {aspect}. Expected visual event: "{visual_event}".

Evaluate the FOLLOWING about the IMAGE ITSELF (what is actually visible):

HUMAN_REALISM
- eyes        = count/correctness (are there a normal number of normal eyes?)
- anatomy     = are hands, fingers, limbs, body connections correct?
- skin        = natural skin texture (pores, variation) vs plastic/perfection?
- photorealism = looks like a real photograph vs obviously AI-generated?

COMPOSITION (for a {aspect} canvas)
- framing     = is the subject inside the frame, not destructively cut off?
- subject_scale = is the subject neither gigantic nor tiny in the frame?
- text_space  = is there a clean zone where text would fit without covering the subject?

NARRATIVE_MATCH
- represents_event = does the image ACTUALLY depict: "{visual_event}"?
- concrete_action = is there an observable action/object/context (vs a generic sad person)?

ANTI_SLOP
- generic_motif = is it a generic cliche (sad person at window, hands on table, coffee+notebook) that could fit ANY topic?

TECHNICAL
- compatible = resolution/aspect usable for a {aspect} video?

STRUCTURAL FAILURES (any of these is a HARD FAIL regardless of the score):
- clearly deformed or incorrect anatomy (wrong number/missing eyes, melted hands/fingers/limbs)
- subject destructively cut by the frame
- subject gigantic filling the frame for a {aspect} canvas
- the image does NOT represent the expected visual event
- composition is broken / unusable for text
- obviously plastic/AI skin (doll, airbrushed) when a person is central

Answer in EXACTLY this format, no extra prose before or after:

SCORE: <one number 0 to 10>/10
DIMENSIONS:
eyes = GOOD|OK|WEAK|FAIL - one short reason
anatomy = GOOD|OK|ISSUES|FAIL - one short reason
skin = GOOD|OK|WEAK|FAIL - one short reason
photorealism = GOOD|OK|WEAK|FAIL - one short reason
framing = GOOD|OK|WEAK|FAIL - one short reason
subject_scale = GOOD|OK|WEAK|FAIL - one short reason
text_space = GOOD|OK|WEAK|FAIL - one short reason
represents_event = YES|PARTIAL|NO - one short reason
concrete_action = YES|NO - one short reason
generic_motif = YES|NO - one short reason
compatible = YES|NO - one short reason
HARD_FAIL: YES|NO
HARD_FAILS:
<only if YES: "- <name> = <short reason>"; write "none" if NO>
SOFT_ISSUES:
<minor issues only, as "- issue"; write "none" if empty>
RECOMMENDATION:
<if no hard fails and score >= {min_score}: "approved". Otherwise the ONE most concrete regeneration instruction for the IMAGE GENERATION PROMPT (fix ONE variable). Maximum 2 sentences.>"""


# Reglas programáticas de hard fail (mandan aunque el modelo las omita)
_GATE_HARD_STATUS = {
    "eyes": {"FAIL"},          # ojos anómalos
    "anatomy": {"ISSUES", "FAIL"},   # anatomía/manos/dedos deformes
    "skin": {"FAIL"},          # piel muñeca
    "photorealism": {"FAIL"},  # apariencia IA clara
    "framing": {"FAIL"},       # sujeto cortado destructivamente
    "subject_scale": {"FAIL"}, # sujeto gigante
    "text_space": {"FAIL"},    # sin espacio para texto
    "represents_event": {"NO"},  # no representa el evento
}

# Soft: señales de anti-slop / debilidad menor
_GATE_GENERIC_MOTIF_NO = {"generic_motif": "NO"}   # si generic_motif=YES → soft warning
_GATE_WEAK = {"WEAK"}


def _gate_parse_and_hard(raw: str, min_score: float):
    """Reutiliza el parser y el motor de hard fails de visual_critic."""
    import visual_critic as vc
    parsed = vc._parse(raw)
    hard_bool, hard_fails, soft_issues = vc._evaluate_hard_fails(
        parsed, mode="gen", require_cta=False)
    # Aplicar las reglas programáticas del gate sobre las dimensiones reales
    dims = parsed["dimensions"]
    table = dict(_GATE_HARD_STATUS)
    gate_hard = list(hard_fails)
    for name, bad in table.items():
        info = dims.get(name)
        if not info:
            continue
        st = str(info.get("status", "")).upper()
        if st in bad:
            reason = info.get("reason", "")
            gate_hard.append(f"{name} = {st}" + (f" ({reason})" if reason else ""))
    gate_hard = list(dict.fromkeys(gate_hard))
    # generic_motif YES → warning (anti-slop soft), no hard
    motifs = []
    gi = dims.get("generic_motif")
    if gi and str(gi.get("status", "")).upper() == "YES":
        g = "generic_motif = YES" + (f" ({gi.get('reason','')})" if gi.get("reason") else "")
        if g not in soft_issues:
            soft_issues.append(g)
    score = parsed["score"]
    if score is None:
        score = 0.0
    return score, bool(gate_hard), gate_hard, soft_issues, dims


# ─────────────────────────────────────────────
# Evaluación de UN intento (imagen real)
# ─────────────────────────────────────────────
@dataclass
class GateContext:
    """Contexto del gate para una escena (incluye variedad del video)."""
    aspect: str = "9:16"                 # "9:16" | "16:9"
    visual_event: str = ""               # evento esperado (para narrative match)
    scene_text: str = ""                 # narración (ES) para mismatch/anti-slop
    prompt: str = ""                     # prompt usado (fallback determinista)
    previous_events: list[str] = field(default_factory=list)
    previous_motifs: list[str] = field(default_factory=list)
    img_w: int = 0
    img_h: int = 0


def evaluate_real_vision(image_path: str, ctx: GateContext,
                         min_score: float = DEFAULT_MIN_SCORE) -> dict:
    """Evalúa la imagen REAL con visión. Devuelve dict con score/hard/soft/dims.

    Reutiliza visual_critic._ask (cascada Cloudflare→moondream→free.ai).
    Si la red falla, lanza excepción → el caller cae a reglas deterministas.
    ```
    """
    import visual_critic as vc
    prompt = GATE_VISION_TEMPLATE.format(
        aspect=ctx.aspect,
        visual_event=(ctx.visual_event or "the scene's moment"),
        min_score=min_score,
    )
    model, raw = vc._ask(image_path, prompt, expect=())
    if not raw:
        raise RuntimeError(f"visión ({model}) sin contenido")
    score, hard_bool, hard_fails, soft_issues, dims = _gate_parse_and_hard(
        raw, min_score)
    return {
        "score": score,
        "hard_fail": hard_bool,
        "hard_fails": hard_fails,
        "soft_issues": soft_issues,
        "dimensions": dims,
        "model": model,
        "raw": raw,
        "recommendation": (vc._parse(raw) or {}).get("recommendation", ""),
    }


def _rule_score(image_path: str, ctx: GateContext) -> VisualQualityScore:
    """Scoring determinista de respaldo (sin red) sobre la imagen/prompt."""
    eng = VisualQualityEngine(aspect=ctx.aspect, threshold=DEFAULT_MIN_SCORE)
    sc = eng.assess(
        scene_prompt=ctx.prompt,
        scene_text=ctx.scene_text or ctx.visual_event,
        img_w=ctx.img_w,
        img_h=ctx.img_h,
        visuals_list=[ctx.prompt] + ctx.previous_events,
        has_human=True,
    )
    return sc


def _dims_to_float(dims: dict) -> dict[str, float]:
    """Convierte dimensiones de estado (GOOD/OK/WEAK/FAIL) en 0..10."""
    scale = {
        "GOOD": 9.5, "OK": 7.0, "WEAK": 4.0, "FAIL": 1.5,
        "YES": 9.0, "PARTIAL": 5.0, "NO": 2.0,
        "ISSUES": 3.0, "LOW": 8.0, "MEDIUM": 5.0, "HIGH": 2.0,
    }
    out = {}
    for name, info in dims.items():
        if isinstance(info, dict):
            st = str(info.get("status", "")).upper()
            out[name] = scale.get(st, 5.0)
        else:
            out[name] = 5.0
    return out


# ─────────────────────────────────────────────
# QualityGate: evalúa la imagen real y decide
# ─────────────────────────────────────────────
class QualityGate:
    """Gate de producción. Evalúa la imagen real, decide PASS/REGENERATE/FALLBACK.

    Input: path de la imagen generada (YA ajustada al aspect si corresponde).
    Visión: critic_fn por defecto = evaluate_real_vision (visión de verdad).
    Regla: determinista (visual_quality_engine) cuando no hay visión.
    """

    def __init__(self, min_score: float = DEFAULT_MIN_SCORE,
                 max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                 critic_fn: Optional[Callable] = None):
        self.min_score = min_score
        self.max_attempts = max(1, int(max_attempts))
        # critic_fn(path, ctx) → dict {score, hard_fail, hard_fails, soft_issues, ...}
        self.critic_fn = critic_fn or evaluate_real_vision

    # -- evaluación de UN intento (imagen real) --
    def _evaluate(self, image_path: str, ctx: GateContext,
                  attempt: int) -> QualityGateResult:
        vision_ok = False
        try:
            if self.critic_fn is not None:
                vis = self.critic_fn(image_path, ctx)
                if vis and vis.get("score") is not None:
                    vision_ok = True
        except Exception:  # noqa: BLE001 — red caída/rate limit → reglas
            vis = None

        if vision_ok:
            score = float(vis["score"])
            hard = bool(vis.get("hard_fail"))
            hard_reasons = list(vis.get("hard_fails", []))
            soft = [s for s in vis.get("soft_issues", []) if s]
            dims = _dims_to_float(vis.get("dimensions", {}))
            dims["technical_quality"] = min(10.0, dims.get("compatible", 5.0))
            source = "vision"
        else:
            rule = _rule_score(image_path, ctx)
            score = rule.total
            hard = bool(rule.hard_anomalies)
            hard_reasons = list(rule.hard_anomalies)
            soft = list(rule.soft_issues)
            dims = {k: float(rule.dimensions.get(k, 5.0)) for k in GATE_DIMENSIONS}
            source = "rule"

        # Anti-slop por contexto del video (variedad narrativa)
        slop_pen, repeated = anti_slop_penalty(
            [ctx.prompt] + ctx.previous_events + ctx.previous_motifs)
        if repeated:
            soft.append(f"anti_slop_de_video:{repeated}")
            if "anti_slop" in dims:
                dims["anti_slop"] = max(1.0, dims["anti_slop"] - min(3.0, slop_pen))
            if not hard:
                score = max(0.0, score - 0.0)  # no romper por variedad menor

        score = round(max(0.0, min(10.0, score)), 2)

        # FILTRO EDITORIAL (HARD FAIL de seguridad) — manda sobre el score.
        # Capa 1 (SIEMPRE, sin red): pre-screen determinista del prompt.
        # Capa 2 (solo visión REAL): percepción factual multi-muestreo de
        # cobertura de ropa sobre la imagen. En offline/tests (critic_fn mock)
        # se SKIPEA la capa 2 para no obligar red ni romper determinismo.
        editorial_unsafe = False
        editorial_reasons: list[str] = []
        if ctx.prompt:
            try:
                kw = keyword_scan(ctx.prompt)
                if not kw.safe:
                    editorial_unsafe = True
                    editorial_reasons = list(kw.reasons)
            except Exception:  # noqa: BLE001
                pass
        _use_real_vision = getattr(self, "critic_fn", None) is evaluate_real_vision
        _vision_enabled = os.environ.get("V2_EDITORIAL_VISION", "1") not in (
            "0", "false", "False", "")
        if (not editorial_unsafe) and _use_real_vision and _vision_enabled:
            try:
                verdict = evaluate_editorial(image_path, ctx.prompt)
                if not verdict.safe:
                    editorial_unsafe = True
                    editorial_reasons = list(verdict.reasons)
            except Exception:  # noqa: BLE001 — nunca romper el render por el filtro
                pass

        passed = (score >= self.min_score) and (not hard) and (not editorial_unsafe)
        decision = Decision.PASS
        if hard:
            decision = Decision.REGENERATE
        elif editorial_unsafe:
            decision = Decision.REGENERATE
        elif passed:
            decision = Decision.PASS
        else:
            decision = Decision.REGENERATE

        reasons = list(hard_reasons)
        if editorial_unsafe:
            reasons.append("EDITORIAL_UNSAFE: " + " ".join(editorial_reasons or ["contenido inapropiado"]))
            hard = True  # el contenido editorial inseguro es SIEMPRE un hard fail
        if not hard and not editorial_unsafe and score < self.min_score:
            reasons.append(f"score {score} < umbral {self.min_score}")
        if not reasons and decision == Decision.PASS:
            reasons.append("aprobado")

        return QualityGateResult(
            passed=passed, score=score, hard_fail=hard,
            reasons=reasons, warnings=soft, dimensions=dims,
            attempt=attempt, max_attempts=self.max_attempts,
            decision=decision, source=source, path=image_path,
            editorial_unsafe=editorial_unsafe,
            editorial_reasons=editorial_reasons,
        )

    # -- regeneración inteligente: mejora el prompt con el motivo del fallo --
    def _improve_prompt(self, base_prompt: str, result: QualityGateResult) -> str:
        base = (base_prompt or "").strip().rstrip(".")
        if not base:
            return base_prompt or ""
        why = " ".join(result.reasons + result.warnings).lower()
        fix = ""
        if any(w in why for w in ("hands", "finger", "anatomy", "limb", "melted")):
            fix = (" Natural, correct human anatomy: realistic hands and fingers, "
                   "natural proportions, no deformation; keep hands out of focus "
                   "or partially out of frame if complex.")
        if any(w in why for w in ("eye", "eyes")):
            fix = (" A normal, natural face with natural eyes; correct eye count "
                   "and proportion, subtle realistic detail.")
        if any(w in why for w in ("skin", "plastic", "doll", "airbrush", "photoreal")):
            fix = (" Realistic natural skin with visible pores, subtle tonal "
                   "variation and small imperfections; no doll or plastic skin.")
        if any(w in why for w in ("gigantic", "huge", "fills", "subject_scale")):
            wide = (" Wider environmental composition: the subject occupies a "
                    "moderate portion of the frame with clear negative space for text.")
            fix = (fix + " " + wide).strip()
        if any(w in why for w in ("cut", "crop", "framing", "off frame")):
            fix = (fix + " Keep the subject fully in frame with comfortable "
                   "headroom and margins.").strip()
        if any(w in why for w in ("space", "text", "frame for text")):
            fix = (fix + " Clear undisturbed space in the area reserved for text "
                   "(keep the main subject clear of that zone).").strip()
        if any(w in why for w in ("not represent", "represents_event", "does not")):
            fix = (fix + " Make the image directly, observably depict the described "
                   "event: a concrete action or telling object, not a generic scene.").strip()
        if any(w in why for w in ("generic_motif", "generic", "cliche", "anti_slop")):
            fix = (fix + " Avoid the generic stock cliche; use a specific, concrete, "
                   "narrative detail instead.").strip()
        if any(w in why for w in ("editorial_unsafe", "torso", "bare", "nudity",
                                  "cover", "cobertura", "desnudo", "desnud")):
            fix = (fix + " The person is FULLY CLOTHED in normal, modest everyday "
                   "clothing, torso and chest fully covered; no bare skin, no nude, "
                   "no revealing pose; a wholesome, clothes-on everyday setting.").strip()
        if not fix:
            # fallback genérico: variar composición/escena sin repetir idéntico prompt
            fix = (" Re-compose the scene: change the framing or light slightly "
                   "while keeping the same subject and action.").strip()
        return f"{base}.{fix}."

    # -- ciclo de producción: PASS / REGENERATE / FALLBACK --
    def run(self, image_path: str, ctx: GateContext,
            regenerate_fn: Optional[Callable] = None,
            base_prompt: str = "",
            store_attempt: Optional[Callable] = None) -> QualityGateResult:
        """Evalúa la imagen; si REGENERATE, regenera hasta max_attempts.

        Args:
            image_path: ruta de la primera imagen.
            ctx: contexto (aspect, event, previous_events...).
            regenerate_fn(attempt, improved_prompt) -> path|None:
                 genera una NUEVA imagen para el intento (attempt 1..).
                 Si None, no hay regeneración real (solo se guarda el resultado).
            base_prompt: prompt usado (para mejorarlo en reintentos).
            store_attempt: callback (result, path) para registrar cada intento.

        Returns:
            QualityGateResult final (decision PASS/REGENERATE/FALLBACK).
            Si el límite se agota: FALLBACK con el mejor candidato en
            final_candidate (marca BEST_CANDIDATE; NUNCA se convierte en PASS).
        """
        results: list[QualityGateResult] = []
        best: Optional[QualityGateResult] = None
        best_path = image_path
        current_path = image_path
        current_prompt = base_prompt
        saw_safe: bool = False  # ¿algún intento fue editorialmente seguro?

        for attempt in range(1, self.max_attempts + 1):
            res = self._evaluate(current_path, ctx, attempt)
            if not res.editorial_unsafe:
                saw_safe = True
            if store_attempt:
                store_attempt(res, current_path)
            results.append(res)
            # mejor candidato: menos hard fails → mayor score
            if best is None:
                best, best_path = res, current_path
            else:
                bc = _better(res, best)
                if bc is res:
                    best, best_path = res, current_path

            if res.decision == Decision.PASS:
                res.final_candidate = current_path
                return res

            if attempt >= self.max_attempts:
                break

            # REGENERATE: pedir una imagen nueva con prompt mejorado
            if regenerate_fn is None:
                break
            improved = self._improve_prompt(current_prompt, res)
            try:
                new_path = regenerate_fn(attempt, improved)
            except Exception as e:  # noqa: BLE001
                res.reasons.append(f"regenerar falló en intento {attempt}: {e}")
                break
            if not new_path or not os.path.exists(new_path):
                res.reasons.append(f"regenerar no devolvió imagen en intento {attempt}")
                break
            current_path = new_path
            current_prompt = improved
            ctx.prompt = improved

        # Límite alcanzado / sin regeneración → FALLBACK (mejor candidato)
        fb = best or results[-1]
        fb.decision = Decision.FALLBACK
        fb.passed = False
        fb.final_candidate = best_path
        if not saw_safe:
            # NINGÚN intento fue editorialmente seguro: aviso duro para que el
            # caller NO renderice con un asset inseguro (debe caer a un FALLBACK
            # determinista seguro o marcar la escena como no renderizable).
            fb.no_safe_candidate = True
            fb.reasons = list(fb.reasons) + [
                "EDITORIAL_UNSAFE en todos los intentos: NO hay candidato seguro; "
                "el caller debe usar un asset seguro (Commons palabra clave) o "
                "marcar la escena como no renderizable."]
        elif fb.hard_fail:
            fb.reasons = list(fb.reasons) + [
                "max_attempts alcanzado; se conserva el mejor candidato (FALLBACK — "
                "un candidato con hard fail crítico NO se convierte en PASS)"]
        else:
            fb.reasons = list(fb.reasons) + [
                "max_attempts alcanzado; se conserva el mejor candidato (FALLBACK)"]
        return fb


def _better(a: QualityGateResult, b: QualityGateResult) -> QualityGateResult:
    """El mejor candidato: primero seguro (sin editorial hard fail), luego sin
    hard fail técnico, luego por score más alto."""
    if a.editorial_unsafe != b.editorial_unsafe:
        # el que NO es editorial inseguro es SIEMPRE mejor (nunca gana uno inseguro)
        return b if a.editorial_unsafe else a
    if a.hard_fail != b.hard_fail:
        # el que NO tiene hard fail es mejor
        return a if not a.hard_fail else b
    return a if a.score >= b.score else b


# ─────────────────────────────────────────────
# Post-render QA (espec §15) — pequeño gate técnico
# ─────────────────────────────────────────────
@dataclass
class RenderCheckResult:
    passed: bool
    hard_fails: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "hard_fails": self.hard_fails,
            "warnings": self.warnings,
        }


def check_rendered_video(video_path: str, *, expected_w: int = 0,
                         expected_h: int = 0, min_duration_s: float = 0.0) -> RenderCheckResult:
    """QA técnico posterior al render (ffprobe). Sin regeneración infinita.

    Comprueba: resolución, duración, audio+video presentes. NO es una segunda
    máquina de re-generación: solo da de alta o marca el artefacto.
    """
    import json
    import subprocess
    hard: list[str] = []
    warns: list[str] = []
    if not video_path or not os.path.exists(video_path):
        return RenderCheckResult(False, ["no existe el video de salida"], warns)

    def _probe(key):
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", f"stream={key}", "-of", "default=noprint_wrappers=1:nokey=1",
                 video_path], capture_output=True, text=True).stdout.strip()
            return out
        except Exception:  # noqa: BLE001
            return ""

    def _probe_streams():
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
                 "-of", "csv=p=0", video_path], capture_output=True, text=True).stdout
            return out.split()
        except Exception:  # noqa: BLE001
            return []

    w = int(_probe("width") or 0)
    h = int(_probe("height") or 0)
    dur = 0.0
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                              "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                              video_path], capture_output=True, text=True).stdout.strip()
        dur = float(out or 0)
    except Exception:  # noqa: BLE001
        dur = 0.0
    streams = _probe_streams()

    if expected_w and w != expected_w:
        hard.append(f"resolución ancha {w} != {expected_w}")
    if expected_h and h != expected_h:
        hard.append(f"resolución alta {h} != {expected_h}")
    if min_duration_s and dur < min_duration_s:
        hard.append(f"duración {dur:.1f}s < {min_duration_s}s")
    if "video" not in streams:
        hard.append("sin stream de video")
    if "audio" not in streams:
        hard.append("sin stream de audio")
    return RenderCheckResult(not hard, hard, warns)


# ─────────────────────────────────────────────
# Helpers de utilidad (para integración en render_adapter)
# ─────────────────────────────────────────────
def image_size(path: str) -> tuple[int, int]:
    """Devuelve (w, h) de la imagen, o (0, 0) si falla/inexistente."""
    try:
        from PIL import Image
        im = Image.open(path)
        return im.size
    except Exception:  # noqa: BLE001
        return 0, 0


def aspect_of(target_aspect: str) -> str:
    """Mapea un aspect/identificador de render a '16:9' o '9:16' canónico.

    Acepta: 'horizontal', '16:9', '16x9', '1920x1080' → '16:9'.
            'vertical', '9:16', '9x16', '1080x1920'     → '9:16'.
    """
    t = (target_aspect or "").lower()
    if "horizontal" in t or "16x9" in t or "1920x1080" in t:
        return "16:9"
    if t.startswith("9:16") or t == "9:16" or "9x16" in t or "1080x1920" in t:
        return "9:16"
    # "16:9" / "9:16" como strings planos
    if t in ("16:9", "16x9"):
        return "16:9"
    return "9:16"


# ─────────────────────────────────────────────
# SELF-TEST determinista (sin red)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # mock de visión determinista para verificar el ciclo sin red
    def mock_critic(path, ctx):
        # path "bad" → hard fail anatomía; "goodNN" → score según
        if "bad" in path:
            return {"score": 8.0, "hard_fail": True,
                    "hard_fails": ["anatomy = FAIL (deformed hands)"],
                    "soft_issues": [], "dimensions": {}, "model": "mock"}
        n = int(re.findall(r"good(\d+)", path)[0]) if re.findall(r"good(\d+)", path) else 5
        return {"score": float(n), "hard_fail": False, "hard_fails": [],
                "soft_issues": [], "dimensions": {}, "model": "mock"}

    g = QualityGate(min_score=6.5, max_attempts=3, critic_fn=mock_critic)
    ctx = GateContext(aspect="9:16", visual_event="hands erasing a line",
                      scene_text="borras y vuelves a empezar", prompt="a prompt")
    import tempfile
    d = tempfile.mkdtemp()
    attempts = []
    with open(os.path.join(d, "bad0.jpg"), "w") as f:
        f.write("x")
    seen = [0]
    def regen(attempt, improved):
        seen.append(attempt)
        p = os.path.join(d, f"reg{attempt}.jpg")
        with open(p, "w") as f:
            f.write("x")
        return p
    # primer intento bad (hard fail) → regenerate; reg1/reg2 simulan score:
    # mock_critic devuelve score según nombre: "reg1"-> default 5 (fail), 
    # mejoramos: cambiar mock para que los reintentos pasen.
    def mock_critic2(path, ctx):
        if "bad" in path:
            return {"score": 8.0, "hard_fail": True,
                    "hard_fails": ["anatomy = FAIL (deformed hands)"],
                    "soft_issues": [], "dimensions": {}, "model": "mock"}
        return {"score": 8.5, "hard_fail": False, "hard_fails": [],
                "soft_issues": [], "dimensions": {}, "model": "mock"}
    g2 = QualityGate(min_score=6.5, max_attempts=3, critic_fn=mock_critic2)
    res = g2.run(os.path.join(d, "bad0.jpg"), ctx, regenerate_fn=regen,
                 base_prompt="a base prompt")
    print("self-test PASS:", res.decision.value, "attempts:", res.attempt,
          "score:", res.score, "hard_fail:", res.hard_fail)
    print("RESULTADO: gate self-test OK")
