#!/usr/bin/env python3
"""visual_critic.py — CRÍTICO VISUAL del canal (evalúa imágenes ya generadas).

No inventa prompts: PUNTÚA. Forma parte del ciclo permanente del canal:

    director_visual.py (qué escena) → flux_img (generar) → visual_critic.py
    (puntuar) → corregir UNA variable → regenerar → volver a puntuar → GIMP.

MODOS:
  gen     — puntúa una imagen GENERADA por IA en 10 dimensiones (default).
  design  — QA de miniaturas construidas en GIMP (checklist validado 2026-08-23).

Uso:
    python3 visual_critic.py <imagen> [--mode gen|design] [--brief "objetivo emocional"]
                             [--min-score 8.0] [--json]

Salida (humano):
    SCORE: 8.6/10
    HARD_FAIL: NO
    SOFT_ISSUES:
      - ...
    DIMENSIONS: ...
    RECOMMENDATION: ...

Además guarda un sidecar JSON junto a la imagen (<nombre>_critic.json) con el
historial de la evaluación, y devuelve exit code 0 solo si
PASS = score >= min-score AND no_hard_fail.

REGLA DEL CANAL (2026-08-24 v2): los hard fails mandan sobre el score. Una
imagen de 8/10 con un hard fail estructural FALLA. En design, si el CTA fue
solicitado (`--cta required`, default) sus 6 checks también son estructurales;
con `--cta none` se excluyen.

Crítico: Cloudflare llama-3.2-11b-vision (free.ai se saltea: responde genérico,
validado 2026-08-24). Credenciales: cf_account_id.txt + cf_token.txt (de ver_imagen).
"""
import base64
import datetime
import json
import os
import re
import sys

import httpx

from consumption import incr  # contabilidad de consumo (auditoría de proveedores)

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from ver_imagen import _creds, VISION_MODEL, ALT_MODEL  # noqa: E402

DEFAULT_MIN_SCORE = 8.0

# ── CONTROL DE CONSUMO (V2-FINAL) ──────────────────────────────────────────
# Latch de "visión agotada". Cuando la cascada de visión devuelve un error
# TERMINAL de cuota (free.ai 402 "No tokens remaining" / Cloudflare
# "sin contenido (¿cuota agotada?)"), se marca la visión como agotada y las
# llamadas siguientes a _ask se cortocircuitan SIN volver a golpear la red.
# Evita quemar ~N×3×attempts llamadas condenadas por render cuando la cuota ya
# se agotó. Es CONTROL DE CONSUMO: no cambia ningún puntaje ni regla de calidad.
_VISION_DOWN = False


def _vision_down() -> bool:
    """True si la visión quedó agotada (para decisión de cortocircuito)."""
    if os.environ.get("V2_FORCE_DISABLE_VISION", "").lower() in ("1", "true", "yes"):
        return True
    return _VISION_DOWN


def _mark_vision_down(reason: str) -> None:
    global _VISION_DOWN
    incr("vision.quota_fail")
    if not _VISION_DOWN:
        _VISION_DOWN = True
        print(f"  [visión] marcar AGOTADA: {reason}; cortocircuito para esta "
              f"sesión (rescatar con reset_vision_down()).", flush=True)


def reset_vision_down() -> None:
    """Rehabilita la visión tras recuperar cuota (uso manual / por sesión)."""
    global _VISION_DOWN
    _VISION_DOWN = False

# ---------------------------------------------------------------------------
# PROMPTS DE EVALUACIÓN
# ---------------------------------------------------------------------------

GEN_DIMENSIONS = """narrative_clarity = is the moment understandable in 2 seconds without audio?
emotional_fit = does it communicate this emotional objective: "{brief}"?
photorealism = real photograph feel vs plastic AI look (skin, textures, hands)?
light_quality = is the described daylight/window light actually present and luminous?
color_diversity = varied natural palette vs monotonous beige/olive mush?
anatomical_integrity = hands, fingers, limbs and body connections correct?
composition = clear subject, intentional negative space, nothing cluttered?
channel_style = intimate observational warm lifestyle photography (NOT stock, NOT dark emo)?
text_space = is there a clean zone where title/subtitle text would go?
darkness_risk = did it fall into dark/gloomy/melancholic mood? (LOW is good)"""

GEN_TEMPLATE = """You are the strict visual critic of a warm lifestyle YouTube channel (audience women 35-64). Evaluate ONE generated image.

Evaluate EXACTLY these 10 dimensions:
{dims}

STRUCTURAL FAILURES (any of these is a HARD FAIL, regardless of the score):
- clearly incorrect anatomy, deformed hands, deformed eyes
- physically fused objects (plants merging with people, elements melting into each other)
- composition that fails to communicate the scene's event
- clearly dark/emo/gloomy aesthetic when the direction asks for luminous/hopeful
- severely underexposed image
- main subject accidentally cut off by the frame
- requested composition/text space missing or unusable

Answer in EXACTLY this format, no extra prose before or after:

SCORE: <one number from 0 to 10>/10
DIMENSIONS:
narrative_clarity = GOOD|OK|WEAK|FAIL - one short reason
emotional_fit = GOOD|OK|WEAK|FAIL - one short reason
photorealism = GOOD|OK|WEAK|FAIL - one short reason
light_quality = GOOD|OK|WEAK|FAIL - one short reason
color_diversity = GOOD|OK|WEAK|FAIL - one short reason
anatomical_integrity = OK|ISSUES - one short reason
composition = GOOD|OK|WEAK|FAIL - one short reason
channel_style = GOOD|OK|WEAK|FAIL - one short reason
text_space = GOOD|OK|WEAK|FAIL - one short reason
darkness_risk = LOW|MEDIUM|HIGH - one short reason
HARD_FAIL: YES|NO
HARD_FAILS:
<only if YES: "- <name> = <short reason>" for each structural failure; write "none" if NO>
SOFT_ISSUES:
<minor issues only, as "- issue"; write "none" if empty>
RECOMMENDATION:
<if no hard fails and score >= 9: "approved". Otherwise ONE concrete regeneration instruction that changes exactly ONE variable (exposure, palette, light direction or composition), keeping the SAME subject and action. Maximum 2 sentences.>"""


DESIGN_CHECKS = """CORE:
1_title_dominant = is the big red title dominant and readable?
2_subtitle_legible = is the smaller cream subtitle readable?
3_nothing_covered = does any text cover face, hands, main plants or key narrative objects?
4_margins_ok = do all texts respect safe margins from borders?
5_photo_protagonist = does the photograph remain luminous, natural and the protagonist?
6_photo_undistorted = is the photograph free of warping/stretching artifacts?
7_hierarchy_clear = title > subtitle > CTA hierarchy clear and unbroken?
CTA BLOCK (evaluate ONLY if a CTA block was requested/present):
cta_present = is there a CTA block at the bottom?
cta_readable = are ALL its words readable?
cta_hierarchy_ok = does the CTA stay visually below title/subtitle without competing?
cta_icons_valid = are its icons recognizable and consistent with the piece?
cta_aligned = are icon(s) and text aligned to each other and to the editorial column?
cta_not_competing = does the CTA avoid competing with the title for attention?
DESIGN SCORES (rate EACH 0-10, one short reason each):
typography = <n>/10 - type hierarchy clear (title >> subtitle >> CTA), max 3 families, sizes deliberate?
composition = <n>/10 - single focal point, deliberate balance and negative space?
color = <n>/10 - restrained palette (max 3 chromatic colors + neutrals), every color with a function?
craft = <n>/10 - alignment, spacing, kerning, edges: meticulous execution?
aesthetic_fit = <n>/10 - warm, luminous, human feel matching the channel?
identity_fit = <n>/10 - could this belong ONLY to this channel (red Anton title, editorial photo)?
anti_slop = <n>/10 - every element earns its place; nothing decorative filling space?"""

DESIGN_TEMPLATE = """You are the strict design QA reviewer of a warm lifestyle YouTube channel. Evaluate ONE vertical thumbnail (1080x1920).

Answer ALL these checks about THIS image:
{checks}

STRUCTURAL FAILURES (any = HARD FAIL, regardless of the score):
- unreadable title
- unreadable subtitle
- CTA missing or unreadable when it was requested
- text over face, hands or the main narrative element
- clearly violated safety margin
- distorted/stretched photograph
- photograph globally darkened just to fit text
- broken visual hierarchy

Answer in EXACTLY this format, no extra prose before or after:

SCORE: <overall quality from 0 to 10>/10
DIMENSIONS:
1_title_dominant = YES|NO - one short reason
2_subtitle_legible = YES|NO - one short reason
3_nothing_covered = YES|NO - one short reason
4_margins_ok = YES|NO - one short reason
5_photo_protagonist = YES|NO - one short reason
6_photo_undistorted = YES|NO - one short reason
7_hierarchy_clear = YES|NO - one short reason
cta_present = YES|NO - one short reason
cta_readable = YES|NO - one short reason
cta_hierarchy_ok = YES|NO - one short reason
cta_icons_valid = YES|NO - one short reason
cta_aligned = YES|NO - one short reason
cta_not_competing = YES|NO - one short reason
DESIGN_SCORES:
typography = <0-10>/10 - one short reason
composition = <0-10>/10 - one short reason
color = <0-10>/10 - one short reason
craft = <0-10>/10 - one short reason
aesthetic_fit = <0-10>/10 - one short reason
identity_fit = <0-10>/10 - one short reason
anti_slop = <0-10>/10 - one short reason
HARD_FAIL: YES|NO
HARD_FAILS:
<only if YES: "- <name> = <short reason>"; write "none" if NO>
SOFT_ISSUES:
<minor issues only, as "- issue"; write "none" if empty>
RECOMMENDATION:
<if no hard fails and nothing relevant: "approved". Otherwise the ONE most important fix (size up text, stronger local shadow behind ONLY the failing block, reposition one element). Never darken the whole photo. Maximum 2 sentences.>"""


def _build_prompt(mode, brief):
    if mode == "design":
        return DESIGN_TEMPLATE.format(checks=DESIGN_CHECKS)
    return GEN_TEMPLATE.format(dims=GEN_DIMENSIONS.format(brief=brief or "warm hopeful everyday life"))


def _expected_keys(mode):
    if mode == "design":
        import re as _re
        return [k for k in _re.findall(r"\d*_?([a-z_]+)\s*=", DESIGN_CHECKS)]
    return list(GEN_HARD_STATUS) + ["emotional_fit", "photorealism",
                                    "color_diversity", "channel_style",
                                    "darkness_risk"]


# ---------------------------------------------------------------------------
# REGLAS DE HARD FAIL (programáticas — mandan aunque el modelo no las declare)
# ---------------------------------------------------------------------------

# gen: dimension = estados que son hard fail
GEN_HARD_STATUS = {
    "anatomical_integrity": {"ISSUES", "FAIL"},   # anatomía/manos/ojos mal
    "narrative_clarity": {"FAIL"},                # no comunica el evento
    "composition": {"FAIL"},                      # composición rota
    "text_space": {"FAIL"},                       # espacio solicitado inexistente
    "light_quality": {"FAIL"},                    # subexpuesta extrema
}
# gen: reglas de valor fijo
GEN_HARD_DARKNESS_HIGH = True   # dark/emo cuando la dirección pide luminoso

# design: check = estados que son hard fail
DESIGN_HARD_STATUS = {
    "title_dominant": {"NO"},          # título ilegible
    "subtitle_legible": {"NO"},        # subtítulo ilegible
    "nothing_covered": {"NO"},         # texto sobre rostro/manos/elemento
    "margins_ok": {"NO"},              # margen violado
    "photo_protagonist": {"NO"},       # foto oscurecida para acomodar texto
    "photo_undistorted": {"NO"},       # fotografía deformada
    "hierarchy_clear": {"NO"},         # jerarquía rota
}
# design: checks CTA que son hard fail SOLO si el CTA fue solicitado
DESIGN_HARD_CTA = {
    "cta_present", "cta_readable", "cta_hierarchy_ok",
    "cta_icons_valid", "cta_aligned", "cta_not_competing",
}


# ---------------------------------------------------------------------------
# LLAMADA AL MODELO DE VISIÓN
# ---------------------------------------------------------------------------

def _ask(image_path, prompt, expect=()):
    # CORTO CIRCUITO DE CONSUMO: si la visión ya se agotó, no volver a golpear
    # la red (cada intento condenado cuesta 402/429 + retry de la cascada).
    if _vision_down():
        incr("vision.quota_fail")
        raise RuntimeError("visión AGOTADA (cortocircuitado — no se vuelve a llamar)")
    incr("vision.requests")
    b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    acct, token = _creds()

    def _call(model, p):
        url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}"
        with httpx.Client(timeout=90.0) as client:
            r = client.post(
                url,
                json={"prompt": p, "image": "data:image/jpeg;base64," + b64},
                headers={"Authorization": f"Bearer {token}"},
            )
        if r.status_code != 200:
            return None
        return r.json().get("result", {}).get("response", "")

    def _incomplete(out):
        low = out.lower()
        if not out or "recommendation" not in low:
            return True
        # Respuesta degenerada: el modelo omitió dimensiones esperadas
        # (sucede aunque la respuesta no esté cortada).
        found = sum(1 for k in expect if k in low)
        return bool(expect) and found < len(expect)

    for model in (VISION_MODEL, ALT_MODEL):
        try:
            out = _call(model, prompt)
            if out and _incomplete(out):
                # Respuesta truncada O parcial (límite de tokens / distracción
                # del modelo): reintentar UNA vez pidiendo brevedad.
                out2 = _call(model, prompt + (
                    "\n\nIMPORTANT: your previous answer was incomplete. "
                    "Repeat the FULL evaluation with EVERY listed field "
                    "(score, all dimensions, HARD_FAIL, HARD_FAILS, SOFT_ISSUES, "
                    "RECOMMENDATION), keeping every reason under 6 words "
                    "(total under 180 words)."))
                if out2 and not _incomplete(out2):
                    out = out2
            if out:
                incr("vision.ok")
                return model, out
            print(f"  vision {model} sin contenido (¿cuota agotada?); "
                  "probando siguiente juez...", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  vision {model} error: {e}", flush=True)
    _ask_maybe_down_cloudflare("cuota agotada en ambos modelos Cloudflare")
    # FALLBACK: qwen25-vl de Free.ai (cuota independiente de Cloudflare)
    try:
        from freeai_edit import describe_image
        out = describe_image(image_path, prompt)
        if out:
            incr("vision.ok")
            return "free.ai/qwen25-vl", out
    except Exception as e:  # noqa: BLE001
        print(f"  vision free.ai error: {e}", flush=True)
        if _is_terminal_quota(str(e)):
            _mark_vision_down("free.ai sin tokens (402/429)")
    raise RuntimeError("ningún modelo de visión respondió")


def _is_terminal_quota(msg: str) -> bool:
    """Detecta un error TERMINAL de cuota en la cascada de visión."""
    low = msg.lower()
    return any(k in low for k in (
        "no tokens remaining", "tokens remaining", "sin tokens", "402",
        "429", "quota", "rate limit", "quota agotada", "exceeded"))


# Marcar agotada también si Cloudflare devolvió "sin contenido (¿cuota agotada?)"
# para ambos modelos (señal de cuota del proveedor) sin que free.ai responda.
def _ask_maybe_down_cloudflare(text: str) -> None:
    if _is_terminal_quota(text):
        _mark_vision_down(text)


# ---------------------------------------------------------------------------
# PARSEO
# ---------------------------------------------------------------------------

def _grab_block(text, header_re, stop_re):
    m = re.search(header_re, text, re.I)
    if not m:
        return []
    body = text[m.end():]
    s = re.search(stop_re, body, re.I)
    if s:
        body = body[:s.start()]
    items = []
    for line in body.splitlines():
        line = line.replace("*", "").strip().lstrip("-").strip()
        if not line or line.lower() == "none":
            continue
        items.append(re.sub(r"\s+", " ", line))
    return items


def _parse(text):
    """Parseo TOLERANTE del formato v2 (SCORE/DIMENSIONS/HARD_FAIL/SOFT_ISSUES).
    Acepta además markdown libre de llama-vision y el formato v1 (FAIL:) por
    retrocompatibilidad con raws viejos."""
    out = {"dimensions": {}, "fails": [], "recommendation": "", "score": None,
           "hard_flag": None, "hard_claimed": [], "soft_issues": []}
    clean = lambda s: s.replace("*", "").replace("_", " ").strip()  # noqa: E731

    m = re.search(r"score\D{0,6}([0-9]+(?:[.,][0-9]+)?)\s*/\s*10", text, re.I)
    if m:
        out["score"] = float(m.group(1).replace(",", "."))

    hm = re.search(r"hard_fail(?!\w*\s*:)\W{0,6}(YES|NO)\b", text, re.I)
    if hm:
        out["hard_flag"] = hm.group(1).upper()

    status_re = r"(YES|NO|GOOD|OK|WEAK|FAIL|ISSUES|LOW|MEDIUM|HIGH)\b"
    line_re = re.compile(
        r"^(?:\d+[\.\)]?\s*|\d+_)?\s*[*_]{0,2}\s*([A-Za-z][A-Za-z0-9_ /]{2,40}?)"
        r"\s*[*_]{0,2}\s*[:=]\s*[*_]{0,2}\s*" + status_re + r"\s*[-–:]?\s*(.*)$"
    )
    skip_prefixes = ("score", "recommendation", "checks", "dimensions", "fail", "hard")
    for line in text.splitlines():
        lm = line_re.match(line.strip())
        if not lm:
            continue
        name = re.sub(r"[^a-z0-9_]+", "_", clean(lm.group(1)).lower()).strip("_")
        if not name or name.startswith(skip_prefixes):
            continue
        entry = {"status": lm.group(2)}
        reason = clean(lm.group(3))
        if reason:
            entry["reason"] = reason
        out["dimensions"][name] = entry

    out["fails"] = _grab_block(
        text, r"fails?\*{0,2}:?(?!\s*(YES|NO))",
        r"\*{0,2}(soft_issues|hard_fail\b|recommendation)")
    bad = {"NO", "FAIL", "WEAK", "ISSUES"}
    derived = [
        f"{n} = {i['status']}" +
        (f" ({i['reason']})" if i.get("reason") else "")
        for n, i in out["dimensions"].items()
        if i["status"] in bad or (n == "darkness_risk" and i["status"] == "HIGH")
    ]
    for dline in derived:
        key = dline.split(" = ")[0][:12]
        if not any(key in f for f in out["fails"]):
            out["fails"].append(dline)

    claimed = _grab_block(text, r"hard_fails\*{0,2}:",
                          r"\*{0,2}(soft_issues|recommendation)")
    out["hard_claimed"] = [c for c in claimed if "=" in c]

    out["soft_issues"] = _grab_block(
        text, r"soft_issues\*{0,2}:", r"\*{0,2}recommendation")

    rm = re.search(r"recommendation\*{0,2}:?\s*\*{0,2}\s*(.+)", text, re.I | re.S)
    if rm:
        rec = clean(rm.group(1))
        out["recommendation"] = re.sub(r"\s+", " ", rec).strip()

    # DESIGN_SCORES: dimensiones numéricas separadas (el score global no debe
    # ocultar una dimensión mala).
    num_re = re.compile(
        r"^[*_]{0,2}(typography|composition|color|craft|aesthetic_fit|"
        r"identity_fit|anti_slop)[*_]{0,2}\s*[:=]\s*[*_]{0,2}"
        r"([0-9]+(?:[.,][0-9]+)?)\s*(?:/\s*10)?\s*[-–:]?\s*(.*)$", re.I)
    out["design_scores"] = {}
    for line in text.splitlines():
        nm = num_re.match(line.strip())
        if nm:
            reason = clean(nm.group(3))
            out["design_scores"][nm.group(1).lower()] = {
                "score": float(nm.group(2).replace(",", ".")),
                **({"reason": reason} if reason else {})}
    return out


# ---------------------------------------------------------------------------
# MOTOR DE HARD FAILS (lo estructural manda sobre el score)
# ---------------------------------------------------------------------------

def _evaluate_hard_fails(parsed, mode, require_cta):
    """Devuelve (hard_fail_bool, hard_fails[], soft_issues[]).

    Regla del canal: PASS = score_ok AND no_hard_fail. Las reglas programáticas
    aplican SIEMPRE aunque el modelo olvide declararlas; lo que el modelo declara
    en HARD_FAILS se suma."""
    dims = parsed["dimensions"]
    table = dict(GEN_HARD_STATUS if mode == "gen" else DESIGN_HARD_STATUS)
    if mode == "design" and require_cta:
        for k in DESIGN_HARD_CTA:
            table[k] = {"NO"}
    hard = []
    for name, bad_status in table.items():
        info = dims.get(name)
        if not info:
            continue
        st = str(info.get("status", "")).upper()
        if st in bad_status:
            reason = info.get("reason", "")
            hard.append(f"{name} = {st}" + (f" ({reason})" if reason else ""))
    if mode == "gen" and GEN_HARD_DARKNESS_HIGH:
        info = dims.get("darkness_risk", {})
        if str(info.get("status", "")).upper() == "HIGH":
            reason = info.get("reason", "")
            hard.append("darkness_risk = HIGH" +
                        (f" ({reason})" if reason else " (cae a oscuro/emo)"))

    for claimed in parsed.get("hard_claimed", []):
        key = claimed.split("=")[0].strip()[:12]
        if not any(key in h for h in hard):
            hard.append(claimed)

    soft = list(dict.fromkeys(parsed.get("soft_issues", [])))
    return (bool(hard), hard, soft)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def _mobile_120px_test(image_path):
    """Test de feed móvil: reducir a ~120px de ancho (tamaño real en el feed)
    y preguntar al juez si la pieza sigue comunicando. Devuelve dict."""
    from PIL import Image
    import tempfile
    from ver_imagen import _ver_cloudflare
    im = Image.open(image_path)
    small = im.resize((120, int(im.height * 120 / im.width)), Image.LANCZOS)
    fd, tiny = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    small.save(tiny)

    def _ask_judge(q):
        try:
            r = _ver_cloudflare(tiny, q)
            if r:
                return r, "cloudflare"
            print("  mobile judge cloudflare sin contenido; free.ai...", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  mobile judge cloudflare error: {e}; free.ai...", flush=True)
        from freeai_edit import describe_image
        return describe_image(tiny, q), "free.ai/qwen25-vl"

    try:
        q = ("This is the same thumbnail reduced to feed size (~120px wide). "
             "Evaluate ONLY what you can actually distinguish. Answer exactly:\n"
             "title = YES|NO - can you identify a large title text (say its color)?\n"
             "focus = YES|NO - is there one clear main visual focus (name it)?\n"
             "detail = CLEAR|MUSH - distinct elements or an unclear blur?\n"
             "hierarchy = YES|NO - does the title still read FIRST at this size?\n"
             "noise = LOW|HIGH - clean and simple vs cluttered/busy?")
        r, judge = _ask_judge(q)
        low = (r or "").lower()
        out = {
            "title_identifiable": "YES" if re.search(r"title[^a-z]{0,8}yes", low) else "NO",
            "focus_clear": "YES" if re.search(r"focus[^a-z]{0,8}yes", low) else "NO",
            "not_mush": "MUSH" if re.search(r"detail[^a-z]{0,8}mush", low) else "YES",
            "hierarchy_first": "NO" if re.search(r"hierarchy[^a-z]{0,8}no", low) else "YES",
            "noise_level": "HIGH" if re.search(r"noise[^a-z]{0,8}high", low) else "LOW",
            "juez": judge,
        }
        if judge != "cloudflare":
            # qwen25-vl responde en prosa, no obedece el formato YES/NO: el
            # parseo automático NO es confiable con este juez (ver raw).
            out["advertencia"] = ("juez de fallback en modo descripción: "
                                  "verificar 'raw' visualmente antes de aceptar "
                                  "un FAIL")
        out["raw"] = " ".join(r.split())[:200]
        return out
    finally:
        os.unlink(tiny)


# Umbral: una dimensión de diseño por debajo de esto se reporta aunque el
# score global sea alto (el global no oculta una dimensión mala).
WEAK_DIMENSION_MIN = 7.0


def critique(image_path, mode="gen", brief="", min_score=DEFAULT_MIN_SCORE,
             save_sidecar=True, require_cta=True):
    prompt = _build_prompt(mode, brief)
    expect = _expected_keys(mode)
    model, raw = _ask(image_path, prompt, expect=expect)
    if not raw:
        raise RuntimeError(f"el modelo de visión ({model}) no respondió "
                           "contenido utilizable (posible rate limit); reintentar")
    parsed = _parse(raw)
    hard_fail, hard_fails, soft_issues = _evaluate_hard_fails(parsed, mode, require_cta)
    score_ok = parsed["score"] is not None and parsed["score"] >= min_score
    mobile = None
    if mode == "design":
        try:
            mobile = _mobile_120px_test(image_path)
            if mobile.get("title_identifiable") == "NO":
                hard_fail = True
                hard_fails.append("mobile_120px_title_identifiable = NO (el título no se identifica en tamaño feed)")
            if mobile.get("not_mush") == "MUSH":
                soft_issues.append("mobile_120px: la pieza colapsa a ruido en tamaño feed")
            if mobile.get("hierarchy_first") == "NO":
                soft_issues.append("mobile_120px: el título no se lee primero en tamaño feed")
            if mobile.get("noise_level") == "HIGH":
                soft_issues.append("mobile_120px: ruido visual alto en tamaño feed")
        except Exception as e:  # noqa: BLE001
            mobile = {"error": str(e)}
    weak = [f"{k} = {v['score']}" + (f" ({v.get('reason', '')})" if v.get("reason") else "")
            for k, v in parsed.get("design_scores", {}).items()
            if v["score"] < WEAK_DIMENSION_MIN]
    result = {
        "image": os.path.abspath(image_path),
        "mode": mode,
        "brief": brief,
        "model": model,
        "score": parsed["score"],
        "score_ok": score_ok,
        "hard_fail": hard_fail,
        "hard_fails": hard_fails,
        "soft_issues": soft_issues,
        "cta_required": bool(mode == "design" and require_cta),
        "mobile_120px": mobile,
        "design_scores": parsed.get("design_scores", {}),
        "weak_dimensions": weak,
        "pass": bool(score_ok and not hard_fail),   # regla del canal: mandan los hard fails
        "min_score": float(min_score),
        "dimensions": parsed["dimensions"],
        "fails": parsed["fails"],
        "recommendation": parsed["recommendation"],
        "raw": raw,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    if save_sidecar:
        sidecar = os.path.splitext(image_path)[0] + "_critic.json"
        with open(sidecar, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        result["sidecar"] = sidecar
    return result


def _render(result):
    print(f"SCORE: {'?' if result['score'] is None else result['score']}/10  "
          f"[{'PASS' if result['pass'] else 'FAIL'}]  ({result['model']})")
    print(f"HARD_FAIL: {'YES' if result['hard_fail'] else 'NO'}")
    if result.get("mobile_120px"):
        print(f"MOBILE_120PX: {result['mobile_120px']}")
    if result["hard_fails"]:
        print("HARD_FAILS:")
        for f in result["hard_fails"]:
            print(f"  - {f}")
    print("SOFT_ISSUES:")
    if result["soft_issues"]:
        for s in result["soft_issues"]:
            print(f"  - {s}")
    else:
        print("  none")
    print("DIMENSIONS:")
    for name, info in result["dimensions"].items():
        reason = f" - {info['reason']}" if info.get("reason") else ""
        print(f"  {name} = {info['status']}{reason}")
    if result.get("design_scores"):
        print("DESIGN_SCORES:")
        for name, info in result["design_scores"].items():
            reason = f" - {info['reason']}" if info.get("reason") else ""
            print(f"  {name.upper()} = {info['score']}{reason}")
        if result.get("weak_dimensions"):
            print(f"WEAK_DIMENSIONS (<{WEAK_DIMENSION_MIN}): el score global "
                  "NO las oculta — corregir ANTES de aceptar:")
            for w in result["weak_dimensions"]:
                print(f"  - {w}")
    print("RECOMMENDATION:")
    print(f"  {result['recommendation']}")
    if result.get("sidecar"):
        print(f"sidecar: {result['sidecar']}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(2)
    image = args[0]
    mode, brief, min_score, as_json = "gen", "", DEFAULT_MIN_SCORE, False
    require_cta = True
    it = iter(args[1:])
    for a in it:
        if a == "--mode":
            mode = next(it)
        elif a == "--brief":
            brief = next(it)
        elif a == "--min-score":
            min_score = float(next(it))
        elif a == "--cta":
            require_cta = next(it).lower() != "none"
        elif a == "--json":
            as_json = True
        elif a.startswith("--"):
            print(f"flag desconocida: {a}", flush=True)
    if mode not in ("gen", "design"):
        print(f"modo inválido: {mode} (gen|design)")
        sys.exit(2)
    if not os.path.exists(image):
        print(f"ERROR: no existe {image}")
        sys.exit(2)

    result = critique(image, mode=mode, brief=brief, min_score=min_score,
                      require_cta=require_cta)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _render(result)
    # exit 1 si falla el score O hay cualquier hard fail
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()