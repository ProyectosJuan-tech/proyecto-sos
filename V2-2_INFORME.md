# V2.2 — PRODUCTION INTELLIGENCE & CHANNEL IDENTITY — INFORME

Fase V2.2 (cerrada, single phase). Objetivo cumplido: el pipeline V2 se convierte
en una **máquina de producción** que recibe una instrucción sencilla y toma
automáticamente las decisiones editoriales recurrentes (identidad, plataforma,
CTA, reporte) SIN repetir config por prompt ni cambiar el mensaje central.

Repositorio: `PROYECTO_FACE_YOUTUBE`. NO commit, NO push (regla V2).

---

## 1. QUÉ SE CONSTRUYÓ

Un único módulo de producción `production_intelligence.py` con CUATRO capas,
todas deterministas (identidad/plataforma/CTA/reporte no usan red; el render
real usa la cadena V2 existente). No es pipeline nuevo ni renderer: **orquesta**
`produce_editorial` + `render_emission`.

Punto de entrada CLI para producción: `producir_v22.py` no existe como archivo
separado; la experiencia de producción vive en `production_intelligence.main()`
y en el driver `pruebas_v22.py` (que produjo las dos producciones reales).

Config central: `assets/brand/brand.config.json` (gitignored) — se añadieron las
secciones `language`, `tone`, `emotional_priority`, `emotional_avoid`,
`forbidden_tone`, `messaging` y `cta.cta_text` (biblioteca de CTA extensible).

### Capa 1 — IDENTIDAD EDITORIAL GLOBAL (central/configured)
- Carga reglas permanentes desde config: español neutro latino (tuteo, no voseo),
  registro conversacional, prioridades emocionales (comprensión→reflexión→esperanza→
  acción), evita miedo/culpa/presión, y la dimensión de fe integrada sin moralizar.
- `EditorialIdentity()` se crea UNA vez y se reutiliza (no se repite por prompt).
- `neutralize()` normaliza el contenido autogenerado (CTA/scaffold) a neutro.
- `guard()` anti-gurú / anti-sermón / anti-toxic / español neutral (PASS/FAIL).
- NO corrige el texto que el usuario provee explícitamente (solo el autogenerado).

### Capa 2 — PLATFORM INTELLIGENCE
- Resuelve plataforma o PIDE si falta (`resolve_platform_request` → NEED_PLATFORM).
- Auto-formato: 9:16 → short/reel (1080x1920); 16:9 → long (1920x1080).
- `editorial_strategy()` adapta estructura/hook/duración/prioridades de CTA por
  plataforma, **sin tocar el mensaje central** (message_unchanged=True).

### Capa 3 — CTA ENGINE (extensible, contextual, NO random)
- Bibliotecas en config (`cta_text`): SUSCRIPCION_SUAVE, CONTINUIDAD, AYUDA,
  UTILIDAD, MENSAJE, COMUNIDAD, FE_COMUNIDAD, ORACION, INTERACCION.
- Selección por puntaje contextual (plataforma, enfoque, cierre) + rotación que
  evita el CTA recién usado. Determinista.
- Máximo 1 CTA principal; secundario solo cuando corresponde (fe+esperanzador →
  oración; experiencias → interacción).
- CTA personal del usuario gana ("source=custom"); `--sin-cta` deshabilita.
- Agregar variantes/familias no toca el selector (extensible).

### Capa 4 — PRODUCTION REPORT
- Se genera SOLO (sin que el usuario lo pida) al producir.
- Incluye: tema, formato, plataforma, duración, cantidad de escenas, CTA,
  ruta MP4, resumen de assets, QA, warnings, fallbacks.
- Modo dev: `git status --short` + `git diff --stat`.
- `ProductionReport.error()` reporte de error estructurado.

## 2. ESCRITURA DE LA CONFIG CENTRAL (cambio editorial)

`assets/brand/brand.config.json` (archivo **gitignored**, no versionado): se
sumaron las claves de identidad/mensajería y la biblioteca de CTA. La verificación
on-disk confirma: `language.default=es_neutro_lat`, 10 reglas `forbidden_tone`,
9 familias CTA.

## 3. ARQUITECTURA (sin duplicar / sin pipeline paralelo)

Se reutilizó el `Platform` de `short_director.py` (no se duplicó). La cadena
editorial V2 (`produce_editorial` → `render_emission`) se mantiene intacta; el
módulo nuevo la orquesta. Regla: NO se tocaron los archivos del pipeline legacy
salvo la config (que es dato, no código) y `pexels_stock.py` (cambio del usuario,
no de esta fase).

## 4. TESTS (deterministas, sin red)

`test_v2_2_production_intelligence.py` — 48 asserts cubriendo los **35 puntos**:

| Bloques | Puntos | Estado |
|---|---|---|
| IDENTIDAD | 1-6 | PASS |
| PLATAFORMA | 7-12 | PASS |
| CTA | 13-24 | PASS |
| REPORTE | 25-33 | PASS |
| REGRESIÓN | 34-35 | PASS |

**Regresión completa (9 archivos)**: 15 + 18 + 29 + 48 + 41 + 23 + 34 + 28 + 48 =
**284/284 PASS, 0 fail**.

## 5. DOS PRODUCCIONES REALES (render + red + ffprobe)

### PRUEBA REAL A — Short 9:16, YouTube
- Tema: "superar el perfeccionismo" (fe+psicología). Plataforma dada: youtube, tipo short.
- **System-driven**: sin escenas manuales, sin imágenes manuales, sin CTA manual.
- CTA auto del engine: familia FE_COMUNIDAD + oración (secundario).
- MP4: `videos/v2_produccion/superar_el_perfeccionismo_vertical.mp4`
- ffprobe: **1080x1920, h264, 99s, AAC mono** → QA PASS (7 escenas, 88s narrados).

### PRUEBA REAL B — Video 16:9 (tema distinto), YouTube
- Tema: "poner límites sin sentir culpa" (distinto de perfeccionismo).
- CTA auto del engine: familia UTILIDAD.
- MP4: `videos/v2_produccion/poner_límites_sin_sentir_culpa_horizontal.mp4`
- ffprobe: **1920x1080, h264, 100s, AAC mono** → QA PASS.

Reports guardados en `pruebas_v22/` (A y B `.report.md` + `reports_v22.json`).

## 6. VERIFICACIÓN DE CRITERIOS DE ACEPTACIÓN (checklist)

- [x] EDITORIAL IDENTITY GLOBAL central/configured (config JSON), aplica a futuros videos.
- [x] PLATFORM INTELLIGENCE: formato auto 9:16↔16:9, estrategia sin cambiar mensaje.
- [x] CTA ENGINE: biblioteca extensible + selección contextual (no random) + rotación.
- [x] Español neutro LATAM (tuteo) por defecto.
- [x] Máx 1 CTA principal; 1 secundario opcional (fe→oración).
- [x] Usuario puede aceptar/digitar/override/suprimir; sin-CTA permite.
- [x] CTA personal gana; rotación sin ciclos rígidos (evita el recién usado).
- [x] PRODUCTION REPORT automático completo.
- [x] Fase única cerrada: sin V2.2.1 auto, sin mejoras espontáneas nuevas.
- [x] Regresión completa PASS (284/284).
- [x] 35 tests deterministas (identidad 1-6, plataforma 7-12, CTA 13-24, reporte 25-33, regresión 34-35).
- [x] Dos producciones reales e2e (A short 9:16 YouTube; B video 16:9 tema distinto).
- [x] Informe final (este) + git status + diff --stat.
- [x] NO commit, NO push.

## 7. LIMITACIONES DOCUMENTADAS (honestidad)

1. El CTA secundario combinado puede leer un poco redundante ("Además, si quieres,
   puedes dejar..."). Es aceptable pero afinable; queda como nota, NO se abre fase.
2. `brand.config.json` está **gitignored**: la identidad central vive solo en disco.
   Si se clona/versiona el repo, hay que asegurar esa config. Pendiente de
   decisión del usuario (no se versiona en esta fase).
3. El QA del reporte es técnico (render OK + ffprobe); la crítica visual fina por
   `visual_critic.py` es un paso humano opcional previo a publicación, fuera del
   reporte automático.

---

## ANEXO — git status --short

```
 M pexels_stock.py
?? V2-02_INFORME.md
?? V2-03_INFORME.md
?? V2-04_INFORME.md
?? V2-05_INFORME.md
?? V2-06_INFORME.md
?? V2-1-1_INFORME.md
?? V2-1_INFORME.md
?? PRUEBA_REAL_V2.1.1_perfeccionismo.md
?? asset_selector.py
?? editorial_orchestrator.py
?? narrative_visual_director.py
?? producir_pruebas.py
?? producir_video.py
?? production_intelligence.py        <-- V2.2
?? prueba_v211_narrative.py
?? prueba_v211_perfeccionismo.py
?? pruebas_v22.py                    <-- V2.2 (driver)
?? pruebas_v22/                      <-- V2.2 (reports)
?? render_adapter.py
?? scene_brief.py
?? short_director.py
?? test_asset_selector.py
?? test_scene_brief.py
?? test_short_director.py
?? test_text_layout.py
?? test_v2_05_integration.py
?? test_v2_06_render_integration.py
?? test_v2_1_1_narrative_visual.py
?? test_v2_1_visual_quality.py
?? test_v2_2_production_intelligence.py  <-- V2.2
?? text_layout.py
?? v2_bridge.py
?? visual_quality_engine.py
```

> Nota: `assets/brand/brand.config.json` no aparece porque está gitignored.

## ANEXO — git diff --stat

```
 pexels_stock.py | 58 +++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 58 insertions(+)
```

> `pexels_stock.py` fue modificado por el USUARIO (no por esta fase; no se tocó).
> La fase V2.2 solo agregó archivos nuevos (`production_intelligence.py`,
> `pruebas_v22.py`, `test_v2_2_production_intelligence.py`) y la config ignorada.
> Sin commit, sin push.

## ANEXO — git diff (pexels_stock.py, contenido del usuario, sin cambios de V2.2)

La fase no modificó `pexels_stock.py`; su diff (58 inserciones) corresponde a un
cambio externo del usuario y se respeta sin tocar. No se incluye el diff completo
por brevedad; disponible con `git diff pexels_stock.py`.
