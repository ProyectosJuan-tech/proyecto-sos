# V2-05 INFORME — INTEGRACIÓN EDITORIAL 9:16 + 16:9

**Fecha**: 2026-08-26  
**Estado**: ✅ COMPLETE  
**Tests**: 41 nuevos de integración → **Total 151/151 PASS**

---

## 1. Resumen ejecutivo

Se construyó la capa de **integración editorial V2** que permite decir
"Hagamos un short sobre X" o "Hagamos un video 16:9 sobre Y" y que el
sistema recorra la cadena completa:

```
IDEA → FORMAT → EDITORIAL PLAN → SCENE BRIEFS → ASSET SELECTION
     → TEXT LAYOUT → scene_dicts (listos para el renderer existente)
```

Todo **sin tocar ni refactorizar el pipeline de render existente**. Es una
capa 100% aditiva:

| Regla | Cumplida |
|---|---|
| NO romper el pipeline existente | ✅ (solo se agregó `pexels_stock.py` +58 líneas en V2-03, previo) |
| NO eliminar comportamiento actual | ✅ |
| Compatibilidad hacia atrás | ✅ |
| Preferir adaptadores sobre refactors | ✅ (`v2_bridge.py`) |
| No duplicar lógica 9:16/16:9 | ✅ (un solo `produce_editorial`) |
| No reglas por tema único | ✅ (scaffold genérico por rol) |
| No hardcodear relación destructiva/Dios/ansiedad | ✅ |
| No commit / no push | ✅ |

La integración **real** llega hasta la generación de `scene_dicts` +
`TextLayout` + `AssetSelection` listos y verificados para el renderer
existente. NO renderiza videos (queda para el pipeline legacy, como pide
el enunciado).

---

## 2. Archivos creados

| Archivo | Líneas | Rol |
|---|---|---|
| `v2_bridge.py` | 245 | Adaptadores V2→pipeline (enums por valor, SceneBrief→scene_dict, SceneBrief→TextLayoutRequest) |
| `editorial_orchestrator.py` | 548 | ContentPlan (ShortPlan + LongFormPlan), scaffold por rol, chain end-to-end `produce_editorial`, CLI helpers |
| `producir_video.py` | 118 | CLI `--engine=v2` con feature flag |
| `test_v2_05_integration.py` | 246 | 41 tests de integración |

## 3. Archivos modificados

- **Ninguno** de los archivos del pipeline en esta fase.
- `pexels_stock.py` (modificado en **V2-03**, previo): +58 líneas `search_videos_raw()`.

## 4. Arquitectura antes / después

**Antes (script → render):**
```
SHORTS/VIDEOS (dicts planos)
   └→ hacer_video_caverna / hacer_video_youtube (render)
        └→ hablar_scenes / *_scenes.py (producen dicts a mano)
```

**Después (layers editoriales → pipeline):**
```
produ:r_video.py --engine=v2 --formato=short|youtube
   └→ editorial_orchestrator.produce_editorial()
        ├→ build_editorial_plan()  → ShortPlan | LongFormPlan
        │     ├ short_director (hooks/validación)
        │     └ build_scene → SceneBrief[]
        ├→ asset_selector.select_asset() → AssetSelection[]
        ├→ v2_bridge.scene_brief_to_text_layout_request + compute_layout → TextLayout[]
        └→ v2_bridge.scene_brief_to_render_scene_dict → scene_dicts[]
             └→ (listos para hacer_shorts / hacer_videos_youtube - pipeline legacy)
```

ContentPlan:
```
ContentPlan
    ├── ShortPlan      (reutiliza short_director.ShortPlan)
    └── LongFormPlan   (nuevo — dataclass en editorial_orchestrator)
```

## 5. Punto exacto de integración con el pipeline

El orquestador NO renderiza. Produce `scene_dicts` planos con las **mismas
claves que la cadena de render ya consume**: `text`, `ai`, `q`, `motion`,
`trans`, `static_text`, `id`, `stock`, `stock_video`, `ai_video`, `av`.

- **Vertical**: esos dicts son lo que `hacer_shorts.py`/`hacer_videos_nuevos.py`
  ya procesan antes de `m.render_pipeline`.
- **Horizontal**: lo que `hacer_videos_youtube.py` procesa antes de
  `y.render_scene`/`y.render_scene_video`.

El punto de inserción es un **adaptador** (`scene_brief_to_render_scene_dict`),
no una reescritura: el renderer recibe exactamente lo que ya sabe leer.

## 6. git status --short

```
 M pexels_stock.py          ← modificación de V2-03 (previa), no de esta fase
?? V2-02_INFORME.md
?? V2-03_INFORME.md
?? V2-04_INFORME.md
?? asset_selector.py
?? editorial_orchestrator.py
?? producir_video.py
?? scene_brief.py
?? short_director.py
?? test_asset_selector.py
?? test_scene_brief.py
?? test_short_director.py
?? test_text_layout.py
?? test_v2_05_integration.py
?? text_layout.py
?? v2_bridge.py
```

## 7. git diff

```diff
--- a/pexels_stock.py
+++ b/pexels_stock.py
+ def search_videos_raw(...)  (+58 líneas)  // V2-03 — NO tocar, previo
```
No hay diff de V2-05 sobre archivos versionados: todos los archivos de V2-05
son nuevos (untracked).

## 8. Archivos nuevos untracked

Se listan en la sección 2. Contenido completo de `v2_bridge.py` y
`editorial_orchestrator.py` disponible en el repo (no copiado aquí por
extensión). `test_v2_05_integration.py` incluido.

---

## 9. Tests nuevos (V2-05) — lista completa

**[1] CHAINING END-TO-END** (18)
1. Short end-to-end plan (EditorialEmission)
2. Short plan es ShortPlan
3. Short plan válido (validate_plan)
4. Short genera escenas (≥6)
5. Short resolución 1080x1920
6. Short SceneBriefs son SceneBrief
7. Short cada SceneBrief válido
8. Short asset selection → AssetSelection por escena
9. Short assets con candidatos (mock)
10. Short layout por escena (TextLayout)
11. Short layouts OK
12. 16:9 end-to-end plan
13. 16:9 plan es LongFormPlan
14. 16:9 plan válido (validate_long_plan)
15. 16:9 genera escenas (≥8)
16. 16:9 resolución 1920x1080
17. 16:9 SceneBriefs válidos
18. 16:9 assets por escena
19. 16:9 layouts por escena

**[2] FORMAT SELECTION** (3)
20. short → 1080x1920
21. youtube → 1920x1080
22. "16:9" alias → 1920x1080

**[3] ESTRATEGIAS EDITORIALES DIFERENTES** (7)
23. Short arco corto < 16:9 arco largo
24. 16:9 arco ≥9 roles
25. Short roles != 16:9 roles
26. 16:9 tiene BIBLICAL_GROUNDING
27. 16:9 profundiza (PSYCHOLOGY repetido)
28. Short no repite PSYCHOLOGY
29. Duraciones objetivo diferentes

**[4] BACKWARD COMPATIBILITY** (6)
30. scene_dict solo claves conocidas por pipeline
31. Módulos V2-01/02/03/04 importan
32. Reutiliza short_director.build_scene
33. Reutiliza generate_hook_options
34. Layout tiene score 0-100
35. Layout font_size>0
36. Layout sin overflow (hook corto)
37. Reutiliza asset_selector.select_asset

**[6] SERIALIZACIÓN** (4)
38. LongFormPlan.to_dict()
39. LongFormPlan.from_dict roundtrip
40. LongFormPlan JSON roundtrip
41. ShortPlan.to_dict() sigue funcionando

## 10. Tests totales

| Fase | Tests | Estado |
|---|---|---|
| V2-01 SceneBrief | 15 | ✅ |
| V2-02 Director Editorial | 18 | ✅ |
| V2-03 Asset Intelligence | 29 | ✅ |
| V2-04 Text Layout | 48 | ✅ |
| V2-05 Integración | 41 | ✅ |
| **TOTAL** | **151** | **151/151 PASS** |

## 11. Resultado

**151/151 PASS · 0 fail**

---

## 12. Recorrido completo — CASO Short

Tema: **"Por qué nos cuesta tanto descansar aunque estemos cansados"**

| Escena | Rol | Duración | Layout (font/lines/score) | Asset (query) |
|---|---|---|---|---|
| e01 | HOOK | 6.0s | 60px/3/75 | pausing think, indoors |
| e02 | PROBLEM | 6.9s | 56px/4/75 | rubbing tired, indoors |
| e03 | AGITATION | 6.1s | 64px/4/75 | closing eyes, at home |
| e04 | PSYCHOLOGY | 7.2s | 58px/4/75 | writing note, indoors |
| e05 | SOLUTION | 5.8s | 64px/4/73 | opening book, near window |
| e06 | HOPE | 5.4s | 68px/4/75 | walking toward, indoors |
| e07 | CALLOUT | 5.4s | 60px/2/77 | passing something, indoors |
| **Total** | | **42.8s** | | |

scene_dict de e01 (listo para el renderer):
```python
{'id': 'e01', 'text': '¿Alguna vez has sentido que nos cuesta tanto descansar aunque estemos cansados?',
 'ai': 'nos cuesta tanto descansar...', 'motion': 'zoom-in', 'trans': {'style': 'fade', 'dur': 0.5}}
```
Resolución: **1080x1920** ✓

## 13. Recorrido completo — CASO 16:9

Tema: **"Por qué algunas personas sienten que siempre tienen que demostrar su valor"**

| Escena | Rol | Layout (font/lines/score) |
|---|---|---|
| e01 | HOOK | 56px/2/77 |
| e02 | REALITY | 60px/2/77 |
| e03 | PROBLEM | 64px/3/75 |
| e04 | PSYCHOLOGY | 58px/2/77 |
| e05 | PSYCHOLOGY | 58px/2/77 |
| e06 | PSYCHOLOGY | 58px/2/77 |
| e07 | SOLUTION | 64px/3/63 |
| e08 | BIBLICAL_GROUNDING | 56px/2/77 |
| e09 | HOPE | 56px/2/77 |
| e10 | CALLOUT | 56px/1/65 |
| **Total** | | **66.0s** |

Resolución: **1920x1080** ✓

## 14. Ejemplos SceneBrief / Asset / TextLayout

**SceneBrief (e02 short):**
```python
SceneBrief(
  scene_id='e02', scene_type='short', narrative_role='problem',
  narration='La mayoría piensa que el problema es el cansancio...',
  action='rubbing tired eyes, dropping shoulders',
  setting='a quiet bedside at dawn',
  camera_motion='zoom-in', preferred_source='ai', motion='zoom-in',
  transition='fade', duration=6.9,
)
```

**Asset seleccionado (e01 short):**
```python
AssetSelection(
  selected=AssetCandidate(id='p_123', url='https://ex.com/123.mp4',
    duration=8.0, width=1080, height=1920, orientation='portrait',
    fps=30.0, quality='hd', source='pexels'),
  query_used='pausing think, indoors',
  status='ok', confidence=0.73,
)
```

**TextLayout (e03 short):**
```python
TextLayout(
  lines=[TextLine(text='...', x=..., y=..., width=..., height=..., font_size=64), ...],
  font_size=64, total_width=..., total_height=...,
  alignment='center', overflow=False, score=75.0, status='ok',
)
```

## 15. Resolución confirmada

- **Short = 1080x1920** (9:16) ✓
- **YouTube = 1920x1080** (16:9) ✓

## 16. Estrategias editoriales diferentes

CONFIRMADO con datos:
- Short: arco de **7** roles, sin repetir PSYCHOLOGY, duración ~43s.
- 16:9: arco de **10** roles, **repite PSYCHOLOGY 3 veces** (profundización),
  incluye **REALITY + BIBLICAL_GROUNDING**, duración objetivo superior.
- Los roles usados difieren entre ambos formatos (assert en tests).

## 17. Rutas legacy continúan funcionando

- Los scripts existentes NO fueron modificados.
- `scene_brief/asset_selector/short_director/text_layout` intactos y sus tests
  siguen pasando.
- Los `scene_dicts` que genera el orquestador usan **solo claves que el pipeline
  ya conoce**, verificable por el test de compatibilidad (#30).
- Feature flag explícito `--engine=v2`; sin él, `producir_video.py` no corre.

## 18. Limitaciones

1. **Narración scaffold determinista**: en modo sin `narrations`, el tema se
   inserta en plantillas genéricas por rol. En producción el llamador inyecta
   los textos **aprobados de Gemini** (`narrations=`). El texto actual es
   funcional para probar la cadena, no para publicar.
2. **Asset selection con fetch real** requiere red + clave Pexels; en tests se
   usa fetch mock (la cadena se verifica, no se descargan assets).
3. **La integración NO renderiza**: termina en `scene_dicts` listos. Conectar
   esos dicts al renderero legacy (paso de materialización) no está hecho en
   esta fase por diseño.
4. **Repeated-role scaffold** genera narraciones idénticas por rol repetido
   (e04-e06 16:9) — esperado en scaffold; con textos de Gemini se diferencian.
5. `text_layout.NarrativeRole` y `scene_brief.NarrativeRole` son enums
   independientes; el bridge los traduce por valor (funciona, pero son tipos
   distintos — no compartidos).

## 19 & 20. NO commit / NO push

Respetado: no se hizo commit ni push. Todos los archivos quedan sin trackear
(hasta que el usuario lo pida).
