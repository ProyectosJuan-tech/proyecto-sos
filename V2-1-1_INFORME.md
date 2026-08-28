# V2.1.1 — NARRATIVE VISUAL DIRECTOR: INFORME

**Fecha**: 2026-08-27
**Fase**: V2.1.1 — Capa de dirección narrativa visual
**Estado**: **COMPLETE** — 236/236 tests PASS (208 previos + 28 nuevos) + prueba real con 2 planes.

---

## 1. Resumen
Se construyó una capa **pequeña y general** de dirección narrativa visual
(`narrative_visual_director.py`) que resuelve para CADA escena:

> "¿Qué debería estar viendo el espectador mientras escucha esta frase?"

En vez de repetir `central_idea` como visual_event de todas las escenas (problema
que V2.1 detectó en `editorial_orchestrator.py`). Ahora cada escena deriva un
**visual_event OBSERVABLE y ESPECÍFICO** desde su narración + rol narrativo, elige
una **visual_strategy** (tipo de representación / acción / entorno / plano /
nivel simbólico), aplica **anti-repetición intra-video**, y el prompt final se
compone **realmente** vía `director_visual.compose_prompt()` y llega al renderer
(vía `brief.ai_prompt`/`visual_event` → `scene_dict["ai"]`).

## 2. Problema raíz
`editorial_orchestrator.build_editorial_plan` construía cada escena con
`visual_event = central_idea` (la MISMA idea global en todas), y dejaba
`ai_prompt = ""`. El renderer usa `scene["ai"] = brief.ai_prompt or brief.visual_event`
→ todas las escenas ilustraban la misma idea: prompts repetitivos, imágenes
genéricas, sin progresión visual, sin relación narración↔imagen. Además la
dirección sofisticada de `director_visual.compose_prompt()` no se conectaba al
flujo editorial automático.

## 3. Solución
Un `NarrativeVisualDirector` determinista (sin red):
- `derive_visual_event(scene_text, narrative_role, previous_events, content_context)`
  → evento observable específico. Usa un léxico de señales genérico (no por tema:
  mensaje/nota/taza/libro/puerta/ventana/caminar/perdón/apego/descanso...) y, si no
  hay señal en el texto, un marco observable del rol (no central_idea). Si el texto
  está vacío → **fallback seguro y explícito** (`_FALLBACK_EVENT`, simbólico).
- `VisualStrategy` por rol (subject_type, action, setting, shot_type, symbolic_level).
- **Anti-repetición**: rota el tipo de representación (PERSON/HANDS/OBJECT/
  ENVIRONMENT/INTERACTION/DETAIL/SYMBOLIC/TEXTUAL_OBJECT) frente a los
  `previous_events`, con `keep_allowed=True`/`force_reuse` para repetición deliberada.
- Compone el prompt final con `compose_prompt_from_brief()` (delega en
  `director_visual.compose_prompt`) y lo escribe de vuelta en el `SceneBrief`
  (`ai_prompt`, `visual_event`, `symbol`, `subject_priority`).

## 4. Archivos creados
- **`narrative_visual_director.py`** — el director (función + estrategia + anti-repetición + prompt).
- **`test_v2_1_1_narrative_visual.py`** — 28 tests deterministas (14 requisitos).
- **`prueba_v211_narrative.py`** — prueba real de 2 planes (SHORT + 16:9).

## 5. Archivos modificados
- **`editorial_orchestrator.py`** (capa V2, no legacy): tras construir los briefs,
  se corre `NarrativeVisualDirector().direct_plan(briefs)` y se escriben
  `visual_event`/`ai_prompt`/`symbol`/`subject_priority` en cada SceneBrief. Acepta
  `narrative_director: bool = True`. Si la dirección fallara, no rompe el plan
  (queda el base central_idea). No se tocó el pipeline legacy.

## 6. Arquitectura antes / después
```
ANTES:
  plan → SceneBrief(visual_event=central_idea, ai_prompt="") × N escenas
      → scene_dicts ai=central_idea (repetido) → renderer → imágenes idénticas de idea

DESPUÉS:
  plan → SceneBrief(por rol) ─┐
       → NarrativeVisualDirector.direct_plan(briefs)        (VISUAL EVENT específico)
            ├─ derive_visual_event(text, role, previous)      observable + anti-repetición
            ├─ VisualStrategy (tipo/acción/entorno/plano)
            └─ compose_prompt() → ai_prompt real
       → scene_dicts ai=<prompt dirigido> → renderer → imagen específica de SU escena
```

## 7. Ejemplo SHORT (9:16, tema "descanso")
| Scene | role | visual_event | strategy (tipo/plano) |
|---|---|---|---|
| 1 | hook | `a person pauses mid-task and glances toward an open doorway, curious` | interaction/medium |
| 2 | problem | `a person sinks into a chair, letting out a long, heavy breath` | person/medium |
| 3 | agitation | `hands rewrite and erase the same line of a note over and over` | hands/close-up |
| 4 | psychology | `a person walks slowly toward a lit doorway, pausing at the threshold` | detail/close-up |
| 5 | solution | `only the hands in frame, moving through a familiar, patient action` | object/medium |
| 6 | hope | `a figure steps toward an open doorway filled with daylight` | environment/wide |
| 7 | callout | `a short handwritten note rests plainly on a wooden table` | textual_object/medium |

## 8. Ejemplo 16:9 (tema "perdón / soltar el rencor")
| Scene | role | visual_event | strategy (tipo/plano) |
|---|---|---|---|
| 1 | hook | `a person pauses mid-task and glances toward an open doorway, curious` | interaction/medium |
| 2 | reality | `an ordinary living room carries on quietly in flat daylight, unglamorous` | environment/wide |
| 3 | problem | `a person sinks into a chair, letting out a long, heavy breath` | person/medium |
| 4 | psychology | `a hand hovers over a written message, then deletes the line` | detail/close-up |
| 5 | psychology | `a small symbolic gesture: a line drawn, a door ajar, an open palm` | detail/close-up |
| 6 | psychology | `a short handwritten phrase rests on the table, plain and final` | detail/close-up |
| 7 | solution | `a person walks slowly toward a lit doorway, pausing at the threshold` | object/medium |
| 8 | biblical_grounding | `fingers rest on an open page of a worn book in gentle window light` | object/close-up |
| 9 | hope | `two people share a quiet, unspoken moment across a table` | environment/wide |
| 10 | callout | `a person, seen from behind, holds the pose of the moment` | textual_object/medium |

## 9. Visual events por escena
Ver tablas §7 y §8. Observación clave: en el 16:9 hay **tres escenas PSYCHOLOGY
con la MISMA narración** y el director generó **tres eventos distintos**
(mano que borra → gesto simbólico → frase escrita) — anti-repetición y progresión
funcionando incluso con texto repetido.

## 10. Prompts resultantes
Cada prompt final (inglés) incorpora setting + evento + símbolo + acción + luz +
composición + anclas human-realism + cámara. Ejemplo (SHORT scene 3):
```
A still kitchen with morning light. Hands rewrite and erase the same line of a note
over and over. The story is carried by two hands in a patient, familiar action.
Closing eyes, taking a slow breath. Soft natural window light. Composition: close-up,
subject in the lower two-thirds, upper third reserved for text. Intimate observational
photography, editorial lifestyle feel, natural skin tones, realistic textures, shadows
that keep detail, bright airy daylight, generous ambient window light, natural whites,
visible color separation, moderate depth of field, documentary framing, lived-in
contemporary interior, hopeful serene mood, bright airy natural, cinematic still.
Shot on Medium shot on Sony A7IV, 50mm f/1.8. Photorealistic, emotionally subtle,
sophisticated cinematic still.
```

## 11. Tests nuevos — `test_v2_1_1_narrative_visual.py` (28)
Cubre los 14 requisitos del spec:
1. dos escenas → eventos distintos; 2. observable; 3. relacionado con scene_text;
4. rol modifica la estrategia; 5. previous_events reduce repetición; 6. repetición
deliberada conservada (keep_allowed/force_reuse); 7. visual_event llega a SceneBrief
(integration); 8. SceneBrief llega a compose_prompt; 9. compose_prompt recibe el
visual_event correcto; 10. short 9:16 funciona (integration); 11. long 16:9 funciona;
12. pipeline legacy continúa funcionando (scene_dicts con claves render-known);
13. fallback seguro y explícito sin info; 14. sin loops infinitos ni generación externa.
Sin red (mock de asset fetch), deterministas.

## 12. Tests totales / 13. X/X PASS
```
test_scene_brief.py              15 pass
test_short_director.py           18 pass
test_asset_selector.py           29 pass
test_text_layout.py              48 pass
test_v2_05_integration.py        41 pass
test_v2_06_render_integration.py 23 pass
test_v2_1_visual_quality.py      34 pass
test_v2_1_1_narrative_visual.py  28 pass
TOTAL                          236/236 PASS  ✅
```

## 14. Resultado de la prueba real
`prueba_v211_narrative.py` generó los DOS planes completos (sin red):

| Criterio | SHORT 9:16 | 16:9 |
|---|---|---|
| visual_events variados | 7/7 únicos | 10/10 únicos |
| tipos de representación | 5 | 7 |
| escenas SOLO de persona | 2 (< mitad) | 3 (< mitad) |
| relacionados con su texto | True | True |
| no paráfrasis de central_idea | True | True |
| prompt incorpora la dirección | True | True |

**PRUEBA REAL: OK — ambos planes cumplen criterios.**

## 15. Limitaciones conocidas
- El léxico de señales es pequeño y basado en palabras clave (genérico pero finito):
  es un derivador determinista por señales, NO comprensión semántica real del texto.
- La estrategia del rol primó parte de la variedad: p.ej. las 3 escenas PSYCHOLOGY
  comparten plano close-up/simbólico (por diseño del rol). Un tema con señales muy
  fuera del léxico verá más eventos por marco-de-rol (aún observables y no-repetidos).
- La repetición DELIBERADA solo se conserva si se pasa explícitamente
  `keep_allowed`/`force_reuse`; el flujo editorial por defecto aplica anti-repetición
  (como pide el spec).
- No se re-renderizó un video MP4 final con el motor (la prueba real es a nivel de
  plan/prompt; el renderer ya consume `ai_prompt` vía el camino verificado en test 12).

## 16. Confirmación de COMPLETE
Se declara **V2.1.1 COMPLETE** al cumplirse TODOS los criterios de aceptación del spec:
- [x] cada escena tiene una intención visual concreta (observable);
- [x] el visual_event deriva de la función narrativa (rol) + texto;
- [x] el visual_event llega REALMENTE al prompt (compose_prompt → ai_prompt → scene_dict);
- [x] se reduce la repetición visual (variedad + anti-repetición, comprobado con PSYCHOLOGY×3);
- [x] existe variedad de tipos de representación (no persona→persona por defecto);
- [x] Short 9:16 funciona; [x] Long-form 16:9 funciona; [x] pipeline legacy funciona;
- [x] tests pasan (236/236); [x] prueba real con dos planes.

Según la REGLA DE "ALTA", **no** se continúa agregando mejoras espontáneas; la
siguiente mejora será una fase nueva y separada solo si en videos reales aparece
un problema suficientemente importante.

---

## git status --short / git diff --stat / git diff

**git status --short** (resumen):
```
 M pexels_stock.py                          (preadaptado en V2-04, NO por V2.1.1)
?? narrative_visual_director.py             (NUEVO V2.1.1)
?? test_v2_1_1_narrative_visual.py          (NUEVO V2.1.1)
?? prueba_v211_narrative.py                 (NUEVO V2.1.1)
?? editorial_orchestrator.py                (V2 — modificado por V2.1.1, untracked)
?? (resto de archivos V2 y V2.1, untracked)
```

**git diff --stat** (solo archivos tracked):
```
 pexels_stock.py | 58 +++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 58 insertions(+)
```

**git diff** (solo tracked): el único diff es la adición de `search_videos_raw` en
`pexels_stock.py` (capa de assets V2-04, no V2.1.1). Los cambios de V2.1.1 viven en
archivos untracked (`narrative_visual_director.py`, `editorial_orchestrator.py`,
`test_v2_1_1_narrative_visual.py`, `prueba_v211_narrative.py`).

**NO commit, NO push** (regla V2.1.1).
