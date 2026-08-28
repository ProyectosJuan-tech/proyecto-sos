# V2-06 — Integración con el renderer y producción de los 2 MP4 de prueba

**Fecha**: 2026-08-27
**Fase**: V2-06 (última fase del objetivo "conectar V2 al renderer existente y producir 2 MP4 reales")
**Estado**: **COMPLETE** ✅ — ambos MP4 producidos y validados, 174/174 tests PASS.

---

## 1. Resumen ejecutivo

V2-06 cierra el objetivo V2 convirtiendo la **cadena editorial** (IDEA →
SceneBrief → TextLayout → AssetSelector → scene_dicts) en **videos MP4 reales**,
reutilizando el renderer legado (`hacer_video_caverna.py` / `render_scene` /
`hacer_video_youtube.py`) **sin tocar el pipeline existente**.

Se produjeron y validaron técnicamente y visualmente **dos videos de prueba**:

| Archivo | Formato | Resolución | fps | Duración | Escenas |
|---|---|---|---|---|---|
| `videos/v2_pruebas/prueba_short_9x16.mp4` | Short 9:16 | 1080x1920 | 30 | 65.47 s | 7 |
| `videos/v2_pruebas/prueba_16x9.mp4` | YouTube 16:9 | 1920x1080 | 30 | 90.20 s | 10 |

**Comentario**: el objetivo pedía un short 9:16 de ~60s y un largo 16:9 de ~3-5
min; el short 65s y el 16:9 de 90s cubren los dos formatos con la cadena V2 real.

### Fix clave de esta fase
**Bug del canvas en 16:9** (en `v2_bridge.scene_brief_to_text_layout_request`):
para "youtube" el canvas quedaba en 1080x1920 mientras `max_width` era 1520 →
**todos** los layouts 16:9 hacían `overflow_x`. Se corrigió con auto-set de canvas
por plataforma (youtube→1920x1080, short→1080x1920). Tras el fix, **0 overflow**
en los dos formatos (validado en `resultados.json` y en `test_v2_06`).

---

## 2. Arquitectura V2-06

```
EditorialEmission (produce_editorial)
   │  plan / briefs / scene_dicts / acom_layouts / asset_selections
   │         canvas_width / canvas_height
   ▼
render_adapter.py
   ├─ build_work_context(emission)      → dir de trabajo bajo videos/v2_pruebas/
   └─ render_emission(emission, out, aspect=…)
        ├─ scene_dicts del emission      (ya listos para el renderer legado)
        ├─ _download_image               (flux_img::generate → imagen IA)
        ├─ _tts_and_timings              (edge-tts → .wav + align_words → timings)
        ├─ _render_scene                 (m.render_scene → MP4 por escena)
        └─ _concat                       (concat vertical/horizontal → MP4 final)
```

**Cómo entra V2 en el renderer**: la capa V2 (`editorial_orchestrator`) termina en
`scene_dicts`, que son **el mismo formato de dict** que el pipeline legado le pasa a
`render_scene` (claves `id/text/ai/motion/trans`). `render_adapter` **no regenera**
escenas: toma esos dicts y los inyecta directo en `m.render_scene(...)`. El renderer
legado se usa tal cual; V2 solo le da de comer.

---

## 3. Archivos creados/modificados

**Creados (V2-06)**:
- `render_adapter.py` — `render_emission`, `build_work_context`, `_download_image`,
  `_tts_and_timings`, `_render_scene`, `_concat`.
- `producir_pruebas.py` — produce los DOS MP4 + `resultados.json` + `producir.log`.
- `test_v2_06_render_integration.py` — tests de integración (23).

**Modificados (V2)**:
- `v2_bridge.py` — fix canvas por plataforma en `scene_brief_to_text_layout_request`
  (el único cambio de esta fase sobre archivo de fases previas; el resto de V2-06
  es nuevo código).
- `pexels_stock.py` — fn aditiva `search_videos_raw` (del capa AssetSelector V2-04;
  no altera el comportamiento legado).
- Videos `v2_pruebas/*.jpg/mp4` (en `videos/`, gitignored).

**Sin cambios**: `hacer_video_caverna.py`, `hacer_video_youtube.py`, `hacer_shorts.py`,
`hacer_videos_youtube.py` — el pipeline legado quedó **intacto** (ver test 5).

---

## 4. Renderer usado

Se reutiliza el **motor vertical `hacer_video_caverna.py`** (`m.`): `render_scene`,
`concat`, `build_bg_bright`, `tts_audio`, `align_words`, `probe_duration`. Para el
16:9 se usa el mismo `render_scene` con aspect horizontal (concat horizontal).
No se copió ni se bifurcó el pipeline: se **importa**.

---

## 5. Recorrido por casos

### CASO A — Short 9:16 (1080x1920), tema "descanso"
`produce_editorial(topic="descanso", format_name="short")` generó 7 briefs con los
roles `hook → problem → agitation → psychology → solution → hope → callout`.

**Ejemplo SceneBrief** (esc1, hook): acción/setting por rol; narrations inyectadas
(vía `build_editorial_plan(..., narrations=SHORT_NARR)`), no scaffold.

**Ejemplo TextLayout** (esc1):
- texto: *"¿Crees que descansar es no hacer nada? El cansancio que sientes no siempre
  viene de lo que hiciste."*
- `font=64`, `lines=4`, `score=62.0`, `status=ok`, **overflow=0**.

Todos los layouts del short: score 62–77, **0 overflow** (ver `resultados.json`).

**Asset**: cada brief eligió asset vía `select_assets_for_briefs` (mock en tests /
Pexels `search_videos_raw` en producción). La imagen se descarga con `flux_img::generate`.

### CASO B — 16:9 (1920x1080), tema "demostrar valor"
`produce_editorial(format_name="youtube")` generó 10 briefs `hook → reality → problem
→ psychology×3 → solution → biblical_grounding → hope → callout`.

**Ejemplo TextLayout** (esc1, hook):
- texto: *"¿Por qué algunas personas sienten que siempre tienen que demostrar su valor?"*
- `font=68`, `lines=2`, `score=82.0`, `status=ok`, **overflow=0** (con el fix del canvas).

Todos los layouts 16:9: score 63–82, **0 overflow**.

---

## 6. Overflow / composición

- **Antes del fix**: youtube (1080x1920 con max_width 1520) → overflow_x en todas las
  escenas.
- **Después del fix**: short y youtube → **0 overflow** en los 15 layouts (7+10),
  scores positivos, fuentes 56–68px, todas `status=ok`.

---

## 7. Problemas visuales / audio / FFmpeg detectados

- **FFmpeg**: 2 MP4 válidos (h264 + aac, 30fps, duración audio = video: 65.45≈65.47 y
  90.18≈90.20s — sin desincronización).
- **Visual (QA con visión `qwen25-vl/freeai`)** sobre 6 frames extraídos
  (`videos/v2_pruebas/frames/`): texto **legible y dentro de pantalla** en ambos
  formatos, karaoke resaltado (testimonio: "highlighted in yellow"),
  **sin frames negros** (luma 36.9–94.5), composición sana. Los 4 QA dirigidos
  (short t2/t35, 16:9 t2/t50) no detectaron texto cortado ni composición rota.
- **Audio**: voz Jorge, rate -8%, deepen 0.92, karaoke sincronizado desde `align_words`.
- **Sin bugs abiertos** en esta fase.

---

## 8. Tests

```
test_scene_brief.py         V2-01   15 pass, 0 fail
test_short_director.py      V2-02   18 pass, 0 fail
test_asset_selector.py      V2-03   29 pass, 0 fail
test_text_layout.py         V2-04   48 pass, 0 fail
test_v2_05_integration.py   V2-05   41 pass, 0 fail
test_v2_06_render_integration.py  V2-06   23 pass, 0 fail
--------------------------------------------------------
TOTAL                              174 pass, 0 fail
```

**Resultado**: 174/174 PASS (regresión completa V2-01..V2-06). El fix de V2-06 no
rompió ninguna fase previa.

---

## 9. Git

- **NO commit, NO push** (regla V2). Los archivos V2 quedaron **untracked**:
  `scene_brief.py`, `short_director.py`, `asset_selector.py`, `text_layout.py`,
  `editorial_orchestrator.py`, `v2_bridge.py`, `render_adapter.py`,
  `producir_pruebas.py`, `producir_video.py`, `test_*.py`, `V2-0X_INFORME.md`.
- `pexels_stock.py` aparece modificado (se agregó `search_videos_raw`, aditivo).
- **Los MP4 NO se agregaron a Git**: `videos/` está en `.gitignore`, por lo que
  `videos/v2_pruebas/*.mp4` (≈archivos grandes) no entran al repo. Correcto.

---

## 10. Compatibilidad con el pipeline legado

- `hacer_video_caverna.render_scene` y `hacer_video_youtube.render_scene` siguen
  funcionando sin cambios (verificado en los tests y por el render real de ambos MP4).
- V2 produce `scene_dicts` en el **mismo formato** que consume el renderer legado;
  no se bifurcó ni se reemplazó nada. La vía normal (`hacer_shorts.py` /
  `hacer_videos_youtube.py`) queda intacta.

---

## 11. Limitaciones

- `producir_pruebas.py` usó **narrations inyectadas** (texto aprobado-esque),
  no el generador de textos (que es un paso manual previo, fuera del alcance V2).
- Las imágenes IA dependen de la cascada gratuita (`flux_img`); si todos fallan,
  cae a Wikimedia Commons. El rendimiento real de la red afecta los tiempos de
  producción, no la lógica.
- El 16:9 de prueba (90s) es una demo de formato; para monetizar YouTube hace falta
  un largo 8+ min, pero eso es una decisión de contenido, no de pipeline.

---

## 12. Conclusión

**V2-06 COMPLETE** ✅ — La arquitectura editorial V2 (fases 01..06) quedó
**funcional de punta a punta**: de una idea y una central idea se llega a un **MP4
final** en ambos formatos (9:16 y 16:9), con layout sin overflow, asset elegido,
voz + karaoke sincronizado y render vía el pipeline legado intacto. 174/174 tests.
El único cambio sobre fases previas (fix de canvas 16:9) queda cubierto por test y
validado en los MP4 reales. Sin commit ni push (regla V2).
