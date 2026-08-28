# V2.1 — VISUAL QUALITY ENGINE: INFORME

**Fecha**: 2026-08-27
**Fase**: V2.1 — Motor de calidad visual/narrativa
**Estado**: **IMPLEMENTADO** — 208/208 tests PASS (V2-01..V2-06 + V2.1).
**Importante**: terminado según el criterio de éxito (no solo tests). Ver §19
"Resultado de las pruebas visuales" y §20 "Problemas comprobados/pendientes".

---

## 1. Resumen ejecutivo

Se creó el **Visual Quality Engine** (`visual_quality_engine.py`), un modelo
**reutilizable y general** (no por tema, no escena por escena) que mejora la
calidad VISUAL y NARRATIVA de cualquier video futuro (9:16 y 16:9). Cubre los 4
problemas:

- **A (16:9 overflow/composición)**: se corrigió la **causa raíz** — el pipeline
  V2 generaba la imagen sin aspect, con lo que un video 16:9 obtenía una 9:16 que
  el renderer recortaba al centro (= sujeto gigante/recortado). Ahora se genera
  con el aspect de la plataforma + crop inteligente (respeta el foco).
- **B (personas falsas/plásticas)**: módulo de human realism (ojos/manos/dedos/
  rostro/piel) con penalización por anomalía grave + reglas de prompt.
- **C (representación humana)**: preferencia **contextual** (no exclusión étnica)
  vía `human_representation_for`.
- **D (piel de muñeca)**: detección de léxico plástico + ancla de piel realista.

El modelo devuelve un `VisualQualityScore` con 12 dimensiones, un sistema de
**regeneración** (GENERATE → QA → SCORE → umbral → REINTENTOS → FALLBACK, sin
loops infinitos), reglas de composición por aspecto, anti-slop y visual/text
matching. **No se tocó el pipeline legacy.** 208/208 tests.

---

## 2. Problemas encontrados (auditoría, PASO 1)

| # | Dónde | Decisión | Hallazgo/problema |
|---|---|---|---|
| A1 | `render_adapter._download_image` | generación IA | Llamaba `flux_img.generate(prompt, img)` **sin aspect** → un video 16:9 generaba una imagen 9:16. |
| A2 | `hacer_video_caverna.build_bg_bright` / `hacer_video_youtube.build_bg_bright` | crop/escala/posición | Hacen **center-crop ciego** para caber en el aspect, sin respetar sujeto ni zona de texto. Un 9:16→16:9 recorta arriba/abajo y puede agrandar el sujeto (PROBLEMA A). |
| A3 | `asset_selector` (`_score_composition`/`_score_text_space`) | selección asset | Solo metadatos (resolución/fps/orientación); NO evalúa composición real ni posición del sujeto. |
| B/C/D | `editorial_orchestrator.build_editorial_plan` | prompt visual | **`visual_event = central_idea` en TODAS las escenas**, `ai_prompt=""`, `symbol=None`. O sea: el prompt IA de cada escena es la idea GLOBAL repetida → imágenes repetitivas, poco dirigidas y (con prompts desnudos) plásticas. El rico `director_visual.compose_prompt()` **NO se usa** en la cadena V2. |
| QA | `visual_critic.critique` / `ver_imagen.py` | QA visual | Existen (visión real), pero no estaban conectados al render V2 para gate por score. |

**Nada de esto asumido: se verificó línea por línea en los 14 archivos.**

---

## 3. Archivos creados

- **`visual_quality_engine.py`** — motor completo (modelo, reglas, regeneración, prompt, anti-slop, mismatch).
- **`test_v2_1_visual_quality.py`** — 34 tests deterministas (PASO 11).

## 4. Archivos modificados

- **`render_adapter.py`** (capa V2, no legacy): `_download_image` ahora pasa
  `aspect=16:9/9:16` a `flux_img.generate`; `_render_scene` aplica
  `_smart_fit_to_aspect()` (crop con `smart_crop_geometry`) antes de `build_bg*`.

*(`pexels_stock.py` seguía modificado con `search_videos_raw` desde V2-04; no lo cambió V2.1.)*

---

## 5. Arquitectura antes / después

```
ANTES (V2-06):
  EditorialEmission → scene_dicts → render_adapter
     _download_image: flux_img.generate(prompt, img)   # sin aspect → siempre 9:16
        → build_bg_bright: center-crop ciego al aspect target → sujeto recortado/agrandado
     sin gate de calidad, sin human realism, sin anti-slop, sin mismatch

DESPUÉS (V2.1):
  visual_quality_engine                       (nuevo, puro, reutilizable)
     ├─ VisualQualityScore (12 dims + hard anomalies)
     ├─ smart_crop_geometry / apply_crop       (crop por foco/aspect)
     ├─ human_realism_rule_score / anatomy_risk / face_risk / skin_risk_word
     ├─ build_quality_prompt / human_representation_for
     ├─ RegenerationEngine  (umbral/attempts/fallback)
     ├─ anti_slop_penalty / score_narrative_match / VisualQualityEngine
  render_adapter ── usa el motor ──► genera con aspect correcto + crop smart
        + anclas human-realism en el prompt
```

---

## 6. Nuevo VisualQualityScore

12 dimensiones (0..10), generales:
`composition, framing, subject_visibility, text_space, human_realism, skin_realism,
anatomy, facial_quality, photographic_realism, visual_coherence, diversity, technical_quality`.

- `total = promedio(dimensiones) − 4.0 × n_anomalías_graves` (clamp 0..10).
- `hard_anomalies` (mandan): `aspect_mismatch`, `anatomy:hands_high_risk`,
  `skin_porcelain_language`, `visual_text_mismatch`.
- `passed` = total ≥ umbral (default 6.5) y sin anomalías que bloqueen.

Scores de la prueba visual (7 prompts, regla): **A 7.47, B 7.37, C 7.37, D 6.90,
E 6.87, F 7.34, G 7.28** — todos PASS sin hard anomalies.

---

## 7. Reglas de human realism

- `anatomy_risk`: interacción fina (manos/dedos/abrazos) = HIGH/med/LOW.
- `face_risk`: ojos/rostro al cámara = HIGH (respeta "no faces visible").
- `skin_risk_word`: léxico "porcelain/doll/plastic/flawless" = HARD.
- `human_realism_rule_score`: base 7.0, resta por riesgo alto, suma por realismo
  explícito (texture/pores/imperfections/candid).
- Anomalía grave (anatomy HIGH, piel muñeca) → **reduce mucho el total** y entra a
  `hard_anomalies`. No es un detector solo por palabras del prompt: se integra con
  la evaluación visual (`critic_fn`/`visual_critic`) cuando hay visión disponible
  y cae a reglas deterministas en tests (sin red).

---

## 8. Reglas de composición 16:9 (PROBLEMA A)

`score_composition_16x9(subject_box, focal_point, margins, text_zone)`:
- subject scale (0.12–0.85 fracción) — sujeto gigante = penalizado;
- crop → `smart_crop_geometry` alinea al aspect respetando el foco (no centro ciego);
- focal area / visual balance / headroom / margins / text-safe: el sujeto NO invade
  la franja inferior de texto (0.74→1.0).

## 9. Reglas de composición 9:16

`score_composition_9x16(...)`: sujeto legible y a escala natural (0.10–0.88),
foco en tercio medio-superior, respeta zona de karaoke inferior, safe zones con
bordes (MIN_EDGE 0.06).

---

## 10. Reglas anti-slop

`DEFAULT_SLOP_MOTIFS` (ventana, persona triste sentada, manos en mesa, café+notebook,
caminar sola, planta genérica, silueta al horizonte). `anti_slop_penalty`: un uso
= aceptable; repetido en varias escenas = penaliza `diversity`. Los motivos siguen
permitidos si la narrativa los pide; no son defaults.

## 11. Reglas de visual/text matching

`score_narrative_match(texto ES, visual_event EN)`: léxico bilingüe de conceptos
(persona/paisaje/manos/escribir/descansar/hablar…). Penaliza:
- texto espera persona y visual es paisaje genérico sin sujeto;
- visual es "ambiente genérico" (playa/caminar sola/horizonte) sin la **micro-acción**
  que pide el texto ("persona caminando por la playa" vs "persona duda antes de enviar");
- texto menciona acción y el visual no la insinúa.
Premia: micro-acción concreta presente, sujeto humano coherente. `mismatch` añade
hard anomaly.

---

## 12. Sistema de regeneración (PASO 4)

`RegenerationEngine(threshold, max_attempts, fallback)`:
`run(generate_fn)` → por cada intento: `generate_fn(attempt)` → `evaluate(path)` →
si score ≥ umbral corta (ok); si no, reintenta hasta `max_attempts` y luego activa
`fallback`. Registra `attempts / scores / reject_reasons / used_fallback / final_path`.
**Sin loops infinitos.** La QA se inyecta (tests deterministas) o usa `visual_critic`
(visión real).

## 13. Fallback

Al agotar intentos sin pasar el umbral → `used_fallback=True`, `final_path=None`,
mismo contrato que el fallback Commons del pipeline (no rompe el render).

---

## 14. Tests nuevos — `test_v2_1_visual_quality.py` (34)

15 bloques requeridos cubiertos:
1. 16:9 asset demasiado grande; 2. 16:9 crop; 3. 16:9 text-safe; 4. 9:16 safe area;
5. human realism; 6. skin realism; 7. anatomy penalty; 8. facial quality penalty;
9. visual/text mismatch; 10. anti-slop; 11. regeneration threshold; 12. max attempts;
13. fallback; 14. prompt construction; 15. backward compatibility. Todos deterministas (sin red).

## 15. Tests totales / 16. X/X PASS

```
test_scene_brief.py              15 pass, 0 fail
test_short_director.py           18 pass, 0 fail
test_asset_selector.py           29 pass, 0 fail
test_text_layout.py              48 pass, 0 fail
test_v2_05_integration.py        41 pass, 0 fail
test_v2_06_render_integration.py 23 pass, 0 fail
test_v2_1_visual_quality.py      34 pass, 0 fail
TOTAL                          208/208 PASS  ✅
```

---

## 17. Ejemplos de prompts antes/después

**Antes (V2)** — `visual_event = central_idea` (idéntico en todas las escenas) y
`flux_img.generate` sin aspect:
```
A woman hesitating before sending a message   →  flux_img.generate(p, img)  # 9:16 aunque el video sea 16:9
```

**Después (V2.1)** — `build_quality_prompt(..., canvas_ar="16:9", has_human=True,
human_representation=...)` + aspect correcto:
```
A woman hesitating before sending a message on her phone, hand paused over the screen.
Shot on Fujifilm X-T5, 35mm f/2. Contemporary western everyperson, natural and unscripted,
realistic diverse appearance matched to the setting. Real human skin with natural texture,
visible pores, subtle tonal variation and small imperfections; no doll-like plastic skin.
Horizontal 16:9 cinematic composition, subject well proportioned within the frame, balanced
negative space, subject clear of the lower text band, comfortable headroom and margins.
```

## 18. Ejemplos de scores

- Escena buena (micro-acción coherente + human realism): **7.55 PASS**, sin hard.
- Escena mala en 16:9 con asset 9:16 (aspect mismatch) + texto/visual mismatch:
  **0.0 FAIL**, hard = `['aspect_mismatch', 'visual_text_mismatch']`.
- `smart_crop_geometry(576,1024,"16:9")` → `(0, 350, 576, 674)` = rect 16:9 centrado
  en la porción útil, no recorte ciego.

---

## 19. Resultado de las pruebas visuales (PASO 12)

Se generaron las 7 imágenes requeridas (Pollinations, con anclas V2.1 y aspect
correcto) en `videos/v2_1_pruebas/imgs/` y se evaluaron con la visión real
(`ver_imagen.py` → qwen25-vl/freeai):

| Img | Escena | Aspect | QA visual (visión) | Score regla |
|---|---|---|---|---|
| A | persona en interior luminoso | 9:16 | persona natural, luz suave, no plástica ✅ | 7.47 |
| B | persona conversando | 9:16 | 2 mujeres naturales, sin manos raras ✅ | 7.37 |
| C | persona escribiendo | 9:16 | persona natural, luz de ventana ✅ | 7.37 |
| D | manos en acción | 9:16 | manos con piel natural, sin dedos deformes ✅ | 6.90 |
| E | sin personas | 9:16 | escena limpia, sin elementos deformes ✅ | 6.87 |
| F | 16:9 con texto | 16:9 | composición balanceada, espacio arriba/abajo ✅ | 7.34 |
| G | 9:16 con texto | 9:16 | sujeto bien colocado, inferior despejada ✅ | 7.28 |

**Verificado de verdad** (no solo tests): 7/7 imágenes generadas con el aspect
correcto (F=1024x576, resto 576x1024), sin pronounced artifacts de ojos/manos/piel
según la visión, y con composiciones despejadas para texto. El fix de aspect de la
**causa raíz A** quedó comprobado en imágenes reales.

---

## 20. Problemas comprobados y pendientes (criterio de éxito)

**Reducido/comprobado en esta fase:**
- overflow/composición incorrecta en 16:9 → causa raíz (aspect) corregida y comprobada (F).
- mismatch texto↔imagen → detectado y penalizado (caso playa del pitch).
- repetición visual → anti-slop funcional.
- piel plástica/personas falsas → anclas de prompt + rule scoring + QA visual de D/A.

**Pendientes / a validar en producción real:**
- **Regeneración end-to-end con visión real**: `RegenerationEngine` está probado con
  inyección determinista y conectable a `visual_critic`, pero NO se corrió un ciclo
  real generate→critique→retry (depende de keys/red y tardaría). El gate no se
  impuso como hard-block en el render V2 por defecto (regla PASO 10): queda como
  componente opcional a activar.
- El **connect visual de asset_selector con composición real** (solo metadatos hoy)
  sigue pendiente: requiere análisis de la imagen, no del prompt.
- No se re-renderizó un video completo V2 con el motor activado (los 2 MP4 de V2-06
  son anteriores al gate). El siguiente video nuevo ya puede usar
  `_smart_fit_to_aspect` + aspect correcto de forma transparente.

Conclusión: la arquitectura V2.1 está **implementada, testeada (208/208) y
validada visualmente en imágenes reales**; la regeneración con visión y el análisis
de composición *de la imagen* (no del prompt) quedan como pasos de producción a
consolidar.

---

## 21. git status --short / git diff

```
 M pexels_stock.py            (preadaptado en V2-04, no por V2.1)
?? visual_quality_engine.py
?? test_v2_1_visual_quality.py
?? render_adapter.py  + resto de archivos V2 (V2-01..V2-06)
?? V2-0X_INFORME.md
```
**NO commit, NO push** (regla V2). `render_adapter.py` y `visual_quality_engine.py`
son untracked (el `git diff` de untracked no muestra nada hasta `git add`; no se
añadió). MP4/imágenes van a `videos/` (gitignored).
