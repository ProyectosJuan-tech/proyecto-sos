# V2-04 INFORME — Motor de Composición Tipográfica Adaptativa

**Fecha**: 2026-08-26  
**Estado**: ✅ COMPLETE  
**Archivos**: `text_layout.py` (~580 líneas) + `test_text_layout.py` (48 tests)

---

## Problema que resuelve

El rendering actual (`hacer_video_caverna.py` / `hacer_video_youtube.py`) usa `wrap_lines()` que divide por espacio más cercano al límite, sin considerar:
- Puntuación (cortes después de comas/puntos)
- Jerarquía narrativa (CTA vs HOOK vs EMPHASIS)
- Plataforma (vertical vs horizontal)
- Balance visual de líneas
- Calidad del layout (score 0-100)

## Qué hace

`text_layout.py` es un módulo autónomo que:
1. **Calcula el mejor font size** iterando de 76px a 56px
2. **Envuelve inteligentemente** respetando puntuación y significado
3. **Genera 3 candidatos de texto** para prompting IA
4. **Score 0-100** evaluando legibilidad, balance, overflow, utilización
5. **Detecta needs_split** para textos que exceden max_lines
6. **Presets por plataforma** (vertical/short/youtube)

## Nuevos components de SceneBrief (ya creados)

| Componente | Archivo | Líneas |
|---|---|---|
| TextLayoutRequest | `text_layout.py` | Dataclass con todos los parámetros |
| TextLayout | `text_layout.py` | Resultado con lines, score, status |
| TextLine | `text_layout.py` | Línea individual con x, y, width |
| Platform | `text_layout.py` | Enum: vertical/short/youtube |
| Position | `text_layout.py` | Enum: top/center/lower |
| Alignment | `text_layout.py` | Enum: left/center/right |
| NarrativeRole | `text_layout.py` | Hooks CTA/EMPHASIS/CONTRAST |

## Tests ejecutados

| # | Test | Resultado |
|---|---|---|
| 1-11 | Wrapping (corto, medio, largo, puntuación) | ✅ |
| 12-16 | Overflow (X, Y, safe area) | ✅ |
| 17 | needs_split detection | ✅ |
| 18-20 | Posiciones (top/center/lower) | ✅ |
| 21-22 | Plataformas (vertical/horizontal) | ✅ |
| 23-26 | Narrative roles (CTA/HOOK/PSYCHOLOGY/EMPHASIS) | ✅ |
| 27-33 | Casos reales del canal | ✅ |
| 34-39 | Utilización y medición | ✅ |
| 40 | Split points | ✅ |
| 41-42 | Validación | ✅ |
| 43 | Serialización | ✅ |
| 44-45 | Español/inglés | ✅ |
| 46 | Cláusulas por coma | ✅ |
| 47-48 | Score/confidence ranges | ✅ |

**TOTAL: 48/48 PASS**

## Realidad check

### 5 composiciones generadas (candidatos)

| Texto | Font | Líneas | Score | Status |
|---|---|---|---|---|
| "Sí." | 76 | 1 | 62 | ok |
| "Perdonar no significa volver..." | 64 | 2 | 77 | ok |
| "Dios puede pedirte que perdones..." | 60 | 4 | 75 | ok |
| "Dios no te pide que permanezcas..." (HOOK) | 80 | 3 | 80 | ok |
| "Hay un patrón: das, das, das..." (PSYCHOLOGY) | 70 | 4 | 75 | ok |

### 3 detecciones de needs_split

| Texto | Líneas | Score | Split candidates |
|---|---|---|---|
| "Hay personas que pasan muchos años..." (max_lines=3) | 12 | 57 | 5 |
| "Cuando toleras lo que te duele..." (max_lines=3) | 7 | 60 | 5 |
| "Dios puede pedirte que perdones..." (max_lines=3) | 8 | 62 | 4 |

### Score breakdown

- Base: 60
- +5 por ≤2 líneas, +3 por ≤4
- +10 por líneas equilibradas (CV < 0.15)
- +5 por utilización 60-90%
- -30 por overflow X, -25 por overflow Y
- -10 por > max_lines
- -8 por última línea huérfana

## Bugs found and fixed

| Bug | Ubicación | Fix |
|---|---|---|
| needs_split no propagaba al layout final | `compute_layout()` línea 720 | Copiar `split_required` y `split_candidates` a `best_layout` |
| Generador de candidatos truncaba a 30 chars | `find_split_points()` línea 343 | Cambiar a 60 chars |

## Integración pendiente

El módulo **no modifica** el pipeline existente. Para integrar:
1. En `hacer_video_caverna.py`: reemplazar `wrap_lines()` por `compute_layout()` para scene blocks
2. En `hacer_video_youtube.py`: igual
3. Agregar `"text_layout": True` al dict de escenas para activar el motor

## Siguiente fase

- V2-05: Integración con SceneBrief (pipeline actual)
- V2-06: Testing end-to-end (renderizar 3 shorts con motor adaptativo)
