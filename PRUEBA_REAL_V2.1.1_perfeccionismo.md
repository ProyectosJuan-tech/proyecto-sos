# PRUEBA REAL V2.1.1 — TEMA DE VALIDACIÓN: "superar el perfeccionismo"

**Fecha**: 2026-08-27
**Formato**: SHORT 9:16 → VIDEO 16:9 (FE + PSICOLOGÍA)
**Script**: `prueba_v211_perfeccionismo.py` (determinista, SIN red, sin optimización manual).
**Comando**: `/home/juan/tools/tts-venv/bin/python3 prueba_v211_perfeccionismo.py`

---

## 1. Qué se probó (y qué NO)

Se inyectaron SOLO las narraciones (el texto, como en producción vía Gemini) y se
dejó que el `NarrativeVisualDirector` derivara la dirección visual **tal cual**.
NO se tocó manualmente ningún visual_event ni prompt. Esto representa el
**comportamiento real** del sistema.

Lo que SÍ se comprobó:
- el sistema construye una narrativa visual DISTINTA por escena;
- variedad de tipos de representación (no persona→persona);
- NO hay "persona mirando por la ventana" como solución automática (0 ocurrencias);
- NO hay "persona + notebook" en todas las escenas (0 ocurrencias);
- no se paraphrasea `central_idea`;
- cada prompt final incorpora su visual_event.

## 2. Resultado estructurado

### SHORT 9:16 (1080x1920) — 7/7 eventos distintos, 6 tipos
| # | role | text | visual_event | strategy |
|---|---|---|---|---|
| 1 | hook | miedo a equivocarte | pauses mid-task, glance toward doorway | interaction/medium |
| 2 | problem | revisas, borras, vuelves a empezar | sits at edge of bed, rubbing tired eyes | person/medium |
| 3 | agitation | esperar lo perfecto te deja detenida | sits still, hands folded, waiting | hands/close-up |
| 4 | psychology | confundió hacerlo bien con perfecto | hand hovers over a message, deletes line | detail/close-up |
| 5 | solution | hacerlo bien y seguir avanzando | only hands in frame, patient action | object/medium |
| 6 | hope | Dios no exige perfecto para amarte | figure steps toward daylight doorway | environment/wide |
| 7 | callout | compártelo | short handwritten note on wooden table | textual_object/medium |

### VIDEO 16:9 (1920x1080) — 10/10 eventos distintos, 7 tipos
| # | role | text | visual_event | strategy |
|---|---|---|---|---|
| 1 | hook | miedo a que te rechacen | pause, glance toward doorway | interaction/medium |
| 2 | reality | revisar, borrar, postergar, no publicar | ordinary living room in flat daylight | environment/wide |
| 3 | problem | miedo a perder el control | open palms flat on table, releasing | person/medium |
| 4 | psychology | no entregar hasta que esté perfecto | hand hovers over message, deletes line | detail/close-up |
| 5 | psychology | (misma narración) | symbolic gesture: line/door/open palm | detail/close-up |
| 6 | psychology | (misma narración) | short handwritten phrase on table | detail/close-up |
| 7 | solution | de "perfecto" a "suficientemente bien" | hand sets object down firmly | object/medium |
| 8 | biblical_grounding | la gracia: no tiene que ser perfecto | fingers on open page of worn book | object/close-up |
| 9 | hope | alivio, no culpa; Dios te acepta | two people share a quiet moment | environment/wide |
| 10 | callout | compártelo | person seen from behind, pose of moment | textual_object/medium |

Escenas de persona: short 2/7, long 1/10. `mirando por ventana`: 0. `notebook`: 0.

## 3. Hallazgos honestos (lo que la prueba REAL revela)

El criterio de aceptación de V2.1.1 ya se cumplió (narrativa visual distinta,
llega al prompt, anti-repetición, variedad, 236/236 tests, 2 plan completo).
Esta prueba de validación lo confirma estructuralmente PERO expone **una
limitación real del derivador de eventos**:

1. **El texto autorado mayormente NO llegó a seedear el visual_event.** Muchas
   escenas cayeron al marco-observable-del-rol en vez de reflejar la acción
   específica de SU texto:
   - Scene 2 (short) "Revisas. Borras. Vuelves a empezar" → `rubbing tired eyes`
     (persona cansada genérica), NO "revisar/borrar".
   - Scene 2 (long, reality) "Revisar, borrar, postergar, no publicar" → salón
     genérico, NO la acción de no entregar.
   - Scene 3 (long) "miedo a perder el control" → `open palms` (por la señal
     `soltar/dejar ir`, match parcial, no ideal para "control").
   Causa: el **léxico de señales es pequeño y por palabra clave**; cuando el
   texto no contiene ninguna palabra del léxico, se usa el marco del rol. Estos
   marcos son observables y no repetidos, pero NO siempre ilustran la acción
   específica del texto.

2. Las escenas cuya narración SÍ tocó el léxico funcionan bien:
   - "quedarse detenida" → `waiting without checking the clock` (buen match);
   - "mensaje" → `hand deletes the line`;
   - "biblia/gracias" → `fingers on open page` (fe, alineado);
   - "avanzando/avanzar" → `hand sets object down firmly`.
   Esto confirma que el mecanismo funciona cuando hay señal, y que el fallo es
   de COBERTURA del léxico, no de arquitectura.

3. Hay un motivo repetido puerta/luz en hook y hope (arc de apertura → cierre).
   Es progresión legítima (callback visual del recorrido), pero visible.

## 4. Conclusión / estado

- **Estructura y diseño: correctos y validados.** El sistema SIEMPRE da un
  visual_event observable, específico, no-central_idea, y lo lleva al prompt.
- **Limitación real identificada (NO oculta): el derivador por señales tiene
  cobertura limitada**; si un texto no toca el léxico, el evento es un marco de
  rol (correcto pero genérico).

Según la **REGLA DE "ALTA"** de V2.1.1, **no** se inicia aquí una mejora
automática (V2.1.2). Esta limitación queda DOCUMENTADA como candidata de la
próxima fase separada solo si en videos reales (ya renderizados y publicados)
aparece un problema suficientemente importante.

**NO commit, NO push.**
