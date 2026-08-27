# PIPELINE OFICIAL DEL CANAL (congelado 2026-08-24)

> **REGLA MAESTRA**: ante "reeditar" o "hacer un video nuevo", SEGUIR ESTE PIPELINE
> EN ORDEN. Los GATES son bloqueos duros: no se avanza sin aprobación explícita.
> Cadena central: IDEA → GUION → **APROBACIÓN** → VOZ → ESCENAS → IMÁGENES →
> CRÍTICO → MOTION → KARAOKE → AUDIO → MONTAJE → QA → MINIATURAS → SUBTÍTULOS →
> SEO → PUBLICACIÓN → APRENDIZAJE.

## Etapas y herramientas (qué usa cada una)

| # | Etapa | Herramienta/skill del repo | Notas |
|---|---|---|---|
| 1 | Idea/objetivo | `DesignContext` (design_intelligence) | tema, problema, idea central, emoción, audiencia, formato |
| 2 | Guion | `generar_textos.py` (Gemini) | NUNCA a mano; gancho/desarrollo/payoff/cierre/CTA; versión HABLADA; duración objetivo |
| 3 | **GATE 1: GUION** | — | bloqueo: no hay imágenes ni TTS hasta "✅ GUION APROBADO" del usuario |
| 4 | TTS/voz | edge-tts (jorge, rate/deepen por escena) | LA VOZ VA ANTES DE LAS IMÁGENES: el timing real determina escenas, duraciones, karaoke y cortes |
| 5 | Mapa de escenas | `director_visual` (briefs + style_family) | tabla: escena / voz / idea visual / emoción / acción / símbolo / duración (del timing real) |
| 6 | Imágenes | `flux_img` (seed fija si personaje) | brief → compose_prompt → FLUX → `visual_critic --mode gen` → corregir UNA variable → repetir hasta PASS sin hard fails |
| 7 | Edición/selección | GIMP MCP | mejor versión, crop, resize, color, encuadre para motion |
| 8 | QA de imágenes | `visual_critic` + QA dirigido (`ver_imagen`) | anatomía, composición, luz, emoción + **STYLE CONSISTENCY**: escena 1 y 8 de la misma película |
| 9 | Motion | skill generacion-videos | zoom/pan/easing calculados desde timing TTS real; dirección según narrativa |
| 10 | Karaoke | pipeline caverna (whisper timings) | SIEMPRE del texto exacto aprobado (guion→TTS→timing→karaoke); 1 idea por escena |
| 11 | Montaje | `hacer_video_caverna` / `hacer_videos_*` | voz+imágenes+motion+karaoke+silencios+transiciones (dip-to-white) + BGM |
| 12 | Mezcla de audio | `post_procesar.py` | voz/música/SFX, ducking, normalización LUFS (-16 YT / -14 FB), sin clipping, sync |
| 13 | Render maestro | ffmpeg CRF18 -tune film | UN master del que derivan todas las versiones; nunca regenerar cada versión desde cero |
| 14 | **GATE 5: QA técnico** | skill editor-video | duración, FPS, resolución, audio, clipping, sync, frames negros/corruptos, silencios |
| 15 | Miniatura YouTube | GIMP + diseno-canal + `visual_critic --mode design` + MOBILE_120PX | foto/título/subtítulo/CTA logo/branding/contraste WCAG; **GATE 6: DESIGN QA PASS** |
| 16 | Miniatura Facebook | misma disciplina, pieza adaptada | proporción/CTA/jerarquía/lenguaje FB (no clonar la de YT) |
| 17 | Subtítulos YouTube | desde el AUDIO FINAL | .srt/.vtt — el audio real manda, no el guion crudo |
| 18 | Empaquetado YouTube | skill seo-youtube | título, descripción, capítulos, tags, comentario fijado, nombre de archivo, thumbnail |
| 19 | Empaquetado Facebook | métricas FB del wiki | copy/caption/CTA/thumbnail/hashtags adaptados |
| 20 | Archivo del proyecto | carpeta estructurada | ver abajo |
| 21 | Post-mortem | wiki + métricas | aprender → mejorar → volver a crear |

## GATES (bloqueos duros)

```
GATE 1  GUION       borrador → ✅ GUION APROBADO (usuario, explícito)
GATE 2  VOZ         TTS → QA de audio → aprobado
GATE 3  ESCENAS     briefs/mapa → aprobado
GATE 4  IMÁGENES    generadas → CRITIC PASS (score ∧ sin hard fails)
GATE 5  VIDEO       montado → QA técnico PASS
GATE 6  DISEÑO      miniatura → DESIGN QA PASS (incluye mobile 120px)
GATE 7  PUBLICACIÓN SEO + subtítulos + assets → LISTO PARA PUBLICAR
```

## Estructura de archivo por proyecto

```
MINIATURAS/ + videos/<nombre>/
videos/<nombre>/
├── 01_guion/        (versión aprobada + cambios)
├── 02_audio/        (wav final + timings)
├── 03_briefs/       (mapa de escenas + briefs JSON)
├── 04_imagenes/     (elegidas + critic JSONs + seeds)
├── 05_motion/       (parámetros por escena)
├── 06_karaoke/
├── 07_video/        (master + derivados)
├── 08_miniaturas/   (→ copia en MINIATURAS/)
├── 09_subtitulos/   (.srt/.vtt)
├── 10_seo/          (títulos/descripciones/empaquetado)
└── 11_qa/           (reportes critic + editor-video + gates)
```

Debe permitir reproducir/corregir el video meses después: prompts, seeds,
imágenes elegidas, critic JSON, decisiones de diseño, versión de guion,
audio final, miniaturas y subtítulos quedan archivados.

## Post-mortem (etapa 21 — obligatoria tras publicar)

Guardar por video: CTR del título, thumbnail que funcionó, hook que retuvo,
escenas que funcionaron, comentarios repetidos, errores, malentendidos de la
audiencia → alimentar de vuelta `cerebro/wiki/contenido/` (estudios) y
`referencias_visuales/`. Ciclo: crear → publicar → aprender → mejorar → crear.

## Excepciones permitidas

- Re-render de UN video existente con cambio puntual: saltar a la etapa afectada
  y sus gates downstream (ej: cambiar una imagen → GATE 4-7).
- Los cambios globales de pipeline se prueban SOLO en el video en curso
  (regla existente de AGENTS.md).
