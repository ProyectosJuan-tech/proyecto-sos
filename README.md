# PROYECTO FACE / YOUTUBE — Producción de videos (caverna / despertar)

Pipeline para producir videos verticales 1080x1920 (9:16) y horizontales
1920x1080 (16:9) estilo "anti-gurú con base real", con TTS en español, karaoke
sincronizado, imágenes IA y una capa V2 de producción automatizada.

Cadena oficial y 7 GATES de aprobación: ver **`PIPELINE.md`**.
Guía de trabajo de la IA (posturas, reglas, scripts): ver **`AGENTS.md`**.

---

## Requisitos

- Python 3.10+
- `ffmpeg` en PATH (audio, render, concat)
- Fuente `DejaVuSerif-Bold.ttf` (render de texto/karaoke)

## Instalación

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Dependencias Python (ver `requirements.txt`): `edge-tts`, `faster-whisper`,
`Pillow`, `httpx`, `numpy`.

Opcional (título cinético): herramienta local `vfxkit`
(fuera del repo, en `/home/juan/tools/vfxkit`).

## Configuración de marca (identidad editorial)

- **`assets/brand/brand.config.json`** — local/privado (gitignored). Es la
  identidad editorial (tono, español neutro, mensajería fe) y la biblioteca de
  CTA. **No se publica.**
- **`assets/brand/brand.config.example.json`** — publicado como referencia de
  estructura (sin secretos).

Para crear tu config local a partir del ejemplo:

```bash
cp assets/brand/brand.config.example.json assets/brand/brand.config.json
# editar a gusto (tono, mensajería, CTAs)
```

`production_intelligence.load_brand_config()` usa la config local; si no existe
(repo recién clonado), cae automáticamente al example, así el sistema funciona
aunque aún no hayas creado tu `brand.config.json`.

## Claves / secretos (NUNCA en Git)

Se leen de variables de entorno o de archivos locales (ignorados por `.gitignore`).
TODAS son **opcionales**: el pipeline degrada con elegancia si faltan.

| Servicio | Env | Archivo local | Uso |
|---|---|---|---|
| Imágenes IA | `IMG_PROVIDER` | — | forzar proveedor (pollinations/gemini/…) |
| Gemini imagen | `GEMINI_API_KEY` | `gemini_key.txt` | gemini-2.5-flash-image |
| Cloudflare AI | `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` | `cf_account_id.txt` + `cf_token.txt` | FLUX.1-schnell/SDXL |
| HuggingFace | `HF_TOKEN` | `hf_token.txt` | FLUX/schnell |
| Pexels (b-roll video) | `PEXELS_API_KEY` | `pexels_key.txt` | stock vertical |
| Pollinations AI video | `POLLINATIONS_KEY` | `pollinations_key.txt` | clips AI |
| Critico visual (QA) | `FREEAI_KEY` | `freeai_key.txt` | qwen25-vl |

Los archivos `*_key.txt` quedan excluidos por `.gitignore` (ver sección
"SECRETS"). No los sufijes ni cambies su localización sin actualizar el ignore.

## Producir un video (V2, automatizado)

```bash
venv/bin/python3 production_intelligence.py \
  --tema "poner limites" \
  --idea "aprender a decir no sin culpa" \
  --plataforma youtube --tipo short \
  [--cta "personal"] [--sin-cta] [--no-render] [--dev]
```

Salida: MP4 en `videos/v2_produccion/` + **Production Report** automático
(tema, formato, plataforma, duración, escenas, CTA, MP4, QA, fallbacks).

## Tests

```bash
venv/bin/python3 test_v2_2_production_intelligence.py   # + resto de test_*.py
```

Regresión esperada: **284/284 PASS** (V2 + V2.1 + V2.1.1 + V2.2).
