"""
V2.4 — PASO 2/3: Auditoría de prompts REALES producidos por el sistema.

Reconstruye la cadena completa para escenas reales (determinista, sin red):
IDEA → narración → role → visual_event → strategy → FINAL PROMPT (ai_prompt).

NO genera imágenes; solo muestra los prompts que el render ENVIARÍA al proveedor.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scene_brief import NarrativeRole
from editorial_orchestrator import build_editorial_plan
from narrative_visual_director import NarrativeVisualDirector
from short_director import build_scene


def audit_plan(name, *, topic, central_idea, format_name, roles, narrations):
    plan, briefs = build_editorial_plan(
        topic=topic, central_idea=central_idea, format_name=format_name,
        narrations=narrations, roles_override=roles,
    )
    print(f"\n{'#'*78}")
    print(f"PLAN: {name}  [{format_name}]  tema='{topic}'")
    print(f"  idea central: {central_idea}")
    print(f"  roles: {[b.narrative_role.value for b in briefs]}")
    print(f"{'#'*78}")
    lines = []
    for b in briefs:
        lines.append({
            "scene": b.scene_id,
            "role": b.narrative_role.value,
            "narration": b.narration,
            "visual_event": b.visual_event,
            "subject_priority": b.subject_priority or "",
            "ai_prompt": b.ai_prompt,
            "setting": b.setting,
            "lighting": b.lighting or "",
            "camera": b.camera or "",
            "composition": b.composition or "",
        })
        print(f"\n--- {b.scene_id} | role={b.narrative_role.value} | "
              f"priority={b.subject_priority or '-'} ---")
        print(f"  NARRACIÓN : {b.narration}")
        print(f"  EVENT     : {b.visual_event}")
        print(f"  SETTING   : {b.setting}")
        print(f"  LIGHT(cam) : '{b.lighting}'  CAMERA: '{b.camera}'")
        print(f"  COMPOS    : '{b.composition}'")
        print(f"  FINAL PROMPT (ai_prompt):")
        print(f"    {b.ai_prompt}")
    return lines


# ---- Temas de prueba real (PASO 11) ----
narrations_short = {
    "hook": "¿Alguna vez has sentido que el miedo al error te paraliza antes de empezar?",
    "problem": "El problema no es tu falta de talento, es el miedo a equivocarte.",
    "agitation": "Y mientras tanto, cada borrador que descartas te aleja de tu propia voz.",
    "psychology": "Tu mente confunde equivocarte con ser un fracaso. Son cosas distintas.",
    "solution": "Da el primer paso aunque salga mal: la práctica corrige lo que el miedo congela.",
    "hope": "Cada error es un dato, no una sentencia. Y eso te libera.",
    "callout": "Si esto te resonó, compártelo con quien esté atrapado en el perfeccionismo.",
}

narrations_fe = {
    "hook": "¿Alguna vez cargas el peso de ser perfecto para los demás y te agota?",
    "problem": "Ese peso no viene de ti: es la trampa de buscar aprobación en todo.",
    "agitation": "Y aunque lo logres, nunca alcanza, porque la aprobación no llena.",
    "psychology": "Hay un patrón: confundir tu valor con lo que los otros opinan de ti.",
    "solution": "Encuentra tu descanso en lo que eres por dentro, no en el aplauso.",
    "hope": "Quien te conoce por tu nombre no te pide perfección, solo fidelidad.",
    "callout": "Si esto te resonó, compártelo con quien lo necesite.",
}

narrations_habitos = {
    "hook": "¿Y si tu día no empieza cuando suena la alarma, sino cuando eliges el primer movimiento?",
    "problem": "El problema no es la falta de tiempo, es cómo empiezas cada mañana.",
    "agitation": "Y así, un día tras otro, la rutina te pilotea en vez de que tú la pilotees.",
    "psychology": "Hay un patrón: tu cerebro automatiza lo que haces apenas te despiertas.",
    "solution": "Elige un ritual mínimo de diez minutos: eso reencuadra todo tu día.",
    "hope": "Con una pequeña ancla diaria, tus hábitos empiezan a trabajar a tu favor.",
    "callout": "Si esto te resonó, compártelo con quien quiera recuperar sus mañanas.",
}

LONG_ROLES = [
    NarrativeRole.HOOK, NarrativeRole.REALITY, NarrativeRole.PROBLEM,
    NarrativeRole.PSYCHOLOGY, NarrativeRole.PSYCHOLOGY, NarrativeRole.PSYCHOLOGY,
    NarrativeRole.SOLUTION, NarrativeRole.BIBLICAL_GROUNDING,
    NarrativeRole.HOPE, NarrativeRole.CALLOUT,
]

out = {}

print("=" * 78)
print("AUDITORÍA V2.4 — PROMPTS REALES (lo que el generador recibe)")
print("=" * 78)

out["short_psicologia"] = audit_plan(
    "Short 9:16 · Psicología/Perfeccionismo", topic="perfeccionismo",
    central_idea="el miedo al error te paraliza",
    format_name="short", roles=None, narrations=narrations_short)

out["short_fe"] = audit_plan(
    "Short 9:16 · Fe + Psicología/Aprobación", topic="aprobación",
    central_idea="tu valor no depende de la aprobación ajena",
    format_name="short", roles=None, narrations=narrations_fe)

out["short_habitos"] = audit_plan(
    "Short 9:16 · Hábitos/Mañanas", topic="hábitos de mañana",
    central_idea="cómo empiezas la mañana define tu día",
    format_name="short", roles=None, narrations=narrations_habitos)

out["long_psicologia"] = audit_plan(
    "Video 16:9 · Psicología/Perfeccionismo (largo)", topic="perfeccionismo",
    central_idea="el miedo al error te paraliza",
    format_name="youtube", roles=LONG_ROLES, narrations=narrations_short)

out["long_fe"] = audit_plan(
    "Video 16:9 · Fe + Psicología/Aprobación (largo)", topic="aprobación",
    central_idea="tu valor no depende de la aprobación ajena",
    format_name="youtube", roles=LONG_ROLES, narrations=narrations_fe)

out["long_habitos"] = audit_plan(
    "Video 16:9 · Hábitos/Mañanas (largo)", topic="hábitos de mañana",
    central_idea="cómo empiezas la mañana define tu día",
    format_name="youtube", roles=LONG_ROLES, narrations=narrations_habitos)

os.makedirs("/tmp/opencode/v24_audit", exist_ok=True)
with open("/tmp/opencode/v24_audit/prompts_reales_audit.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n\nGuardado: /tmp/opencode/v24_audit/prompts_reales_audit.json")
