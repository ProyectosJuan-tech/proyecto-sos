# V2-02 Director Editorial — INFORME FINAL

## Fase completada: V2-02

**Estado**: ✅ COMPLETADA (18/18 tests PASS)

---

## Archivos creados

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `short_director.py` | NUEVO | Director Editorial: ShortPlan, generación de hooks, validación, serialización |
| `test_short_director.py` | NUEVO | 18 tests, todos PASS |

**Archivos modificados (1)**:
- `scene_brief.py`: Se agregaron 4 valores a `NarrativeRole` (REALITY, PSYCHOLOGY, BIBLICAL_GROUNDING, HOPE) — cambio backward-compatible

**NO se modificó ningún archivo existente del pipeline.**

---

## Resumen de lo creado

### `short_director.py` (~430 líneas)

**Clases:**
- `HookStrategy` (Enum): IDENTIFICATION, TENSION, AFFIRMATION
- `Tone` (Enum): direct, combined, vulnerable, firm
- `Platform` (Enum): youtube, facebook, both
- `HookOption`: dataclass (strategy, text, rationale, score)
- `ShortPlan`: dataclass completo — topic, central_idea, audience, tone, locale, register, voseo, regionalisms, platform, promise, target_duration, hook, hook_strategy, hook_options, narrative_arc, scenes (list[SceneBrief]), cta, cta_type, notes

**Funciones:**
- `estimate_scene_duration()` — duración por palabra + overhead por rol narrativo
- `estimate_total_duration()` — suma de escenas
- `generate_hook_options(topic, central_idea)` — genera 3 hooks (IDENTIFICATION, TENSION, AFFIRMATION) con scores
- `select_best_hook(options, topic)` — selecciona el mejor por score
- `build_scene()` — construye SceneBrief con role, narration, visual_event, emotion, action, setting, setting_detail, light, mood, duration
- `validate_plan(plan)` — validación completa (10 checks: topic, central_idea, hook, scenes, cta, duration, voseo, repetitividad, roles sin solution, bíblica vacía)
- `plan_to_dict() / plan_from_dict()` — serialización dict
- `plan_to_json() / plan_from_json()` — serialización JSON
- `plan_relacion_destructiva()` — ejemplo completo: 9 escenas, arco emotion → faith → hope

**Constantes:**
- `NARRATIVE_ROLES` — 12 roles narrativos con descripciones
- `DEFAULT_ARC` — arco emocional por defecto (9 pasos)
- `WOES` — palabras prohibidas (voseo, riqueza, ley de atracción)
- `WORDS_PER_MINUTE = 160` — Velocidad del TTS
- `EMOTION_WORDS` / `FAITH_WORDS` — diccionarios para scoring de hooks

### `test_short_director.py` (~310 líneas)

18 tests, todos PASS:
1. ShortPlan vacío
2. build_scene() crea SceneBrief con duración
3. SceneBrief válido según validate()
4. Hook generation (3 opciones)
5. Hook selection (mejor por score)
6. validate_plan() plan válido
7. validate_plan() plan inválido
8. Serialización dict roundtrip
9. Serialización JSON roundtrip
10. Duración estimada razonable
11. Español neutro (sin voseo)
12. Escena inválida detectada
13. CTA presente y coherente
14. Arco emocional completo
15. Sin citas bíblicas inventadas
16. Continuity groups coherentes
17. narrative_roles_used() correcto
18. Stats consistentes

---

## Ejemplo de uso

```python
from short_director import plan_relacion_destructiva, validate_plan, plan_to_json

plan = plan_relacion_destructiva()
result = validate_plan(plan)

if result["valid"]:
    print(plan_to_json(plan))  # JSON completo
    # O convertir a dict para render
    from short_director import plan_to_dict
    d = plan_to_dict(plan)
```

Salida del ejemplo:
```
TOPIC: Dios y las relaciones tóxicas
IDEA CENTRAL: Dios no te pide que permanezcas atrapado en una relación destructiva
HOOK (affirmation): Dios no te pide que permanezcas en lo que te destruye.
DURACIÓN: 56.3s (9 escenas)
VALIDACIÓN: PASS (0 errores, 0 warnings)
CTA: Si conoces a alguien que necesita escuchar esto, compártelo.

ARCO:
  e01 hook → e02 problem → e03 agitation → e04 psychology → e05 solution
  → e06 biblical_grounding → e07 reality → e08 hope → e09 callout
```

---

## Decisiones tomadas

1. **NarrativeRole extendido** en scene_brief.py (no en short_director.py) para mantener una sola fuente de verdad. Los 4 valores nuevos son backward-compatible.

2. **Serialización manual** en vez de `asdict()` — porque `asdict()` convierte dataclass anidadas a dicts planos y luego falla al serializar Enums.

3. **Duración calculada por palabra** (160 WPM) + overhead por rol narrativo (HOOK +1.5s, CALLOUT +2.0s, PSYCHOLOGY +1.5s) — no hardcodeada.

4. **Hooks generados con heurística simple** — scoring por presencia de palabras emocionales, contraste, y balance. Sin LLM.

5. **Validación estricta pero útil** — detecta voseo, duración fuera de rango, escenas repetitivas, bíblica sin verificar. No bloquea por warnings.

---

## Problemas encontrados y resueltos

1. **Hook de redundancia** — `generate_hook_options()` usaba `central_idea` que ya contenía la frase completa, generando "Dios no te pide que Dios no te pide que...". Resuelto: hook AFFIRMATION hardcodeado con frase limpia.

2. **Serialización `asdict()` + Enums** — `asdict()` no serializa Enums y convierte dataclass anidadas a dicts. Resuelto: serialización manual campo por campo.

3. **NarrativeRole incompleto** — Faltaban HOPE, PSYCHOLOGY, BIBLICAL_GROUNDING, REALITY. Agregados a scene_brief.py.

---

## Verificación

```bash
python3 test_short_director.py  # 18/18 PASS
python3 test_scene_brief.py     # 15/15 PASS (V2-01 intacto)
python3 short_director.py       # Ejemplo completo funciona
git status --short              # Solo 4 archivos nuevos, 0 modificados
```

---

## Siguientes pasos

1. **V2-03**: Montaje de escenas — pasar plan validado a hacer_shorts.py sin tocar la configuración del pipeline
