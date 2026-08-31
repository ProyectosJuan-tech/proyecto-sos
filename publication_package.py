# V2.5 — PAQUETE DE PUBLICACIÓN
#
# Genera, junto al MP4 final de una producción, un único archivo .md listo para
# revisar y publicar. NO inventa información: cada dato sale del contexto de
# producción REAL (dict) que el driver/caller le pasa; si falta un dato escribe
# "No disponible".
#
# El tema/idea es fuente de verdad: no se cambia nada del contenido. Solo se
# genera empaque (título/descripción/copy/CTA/hashtags) para YouTube y/o
# Facebook, respetando español neutro + tuteo e identidad editorial.
#
# El CTA es el que ya eligió Production Intelligence (o el que vino en la
# producción): este módulo NO crea un segundo sistema de CTA.
from __future__ import annotations

import os
import re


PLATFORMS = ("youtube", "facebook", "both")


def _slug(text: str) -> str:
    """Nombre de archivo seguro derivado de un texto (minúsculas, _, sin acentos)."""
    s = (text or "").strip().lower()
    s = re.sub(r"[áàäãâ]", "a", s)
    s = re.sub(r"[éèëê]", "e", s)
    s = re.sub(r"[íìïî]", "i", s)
    s = re.sub(r"[óòöõô]", "o", s)
    s = re.sub(r"[úùüû]", "u", s)
    s = re.sub(r"ñ", "n", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "produccion"


def _get(data: dict, *keys) -> str:
    """Extrae el primer valor no vacío de una lista de claves (o 'No disponible')."""
    for k in keys:
        v = data.get(k)
        if v not in (None, "", "None"):
            return str(v)
    return "No disponible"


def _fmt_duration(sec):
    if sec in (None, "", "None"):
        return "No disponible"
    try:
        sec = float(sec)
    except (TypeError, ValueError):
        return str(sec)
    m = int(sec // 60)
    s = int(round(sec % 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d}"


# ─────────────────────────────────────────────
# Título / descripción recomendados (deterministas, no clickbait)
# ─────────────────────────────────────────────

def _hook_question(topic: str, idea: str) -> str:
    t = (topic or "").strip()
    i = (idea or "").strip()
    if i and t:
        return f"{i.capitalize()} — reflexionamos sobre {t}."
    if i:
        return i.capitalize()
    return t.capitalize() if t else "Una reflexión"


def _youtube_title(ctx: dict) -> str:
    title = ctx.get("title")
    if title:
        return str(title).strip()
    return _hook_question(ctx.get("topic"), ctx.get("idea"))


def _youtube_description(ctx: dict, cta: str) -> str:
    hook = _hook_question(ctx.get("topic"), ctx.get("idea"))
    callback = (
        " Una pausa honesta para quienes quieren vivir desde la paz y la libertad, "
        "sin culpa ni autoexigencia."
    )
    lines = [
        f"{hook}{callback}",
        "",
        f"Tema: {_get(ctx, 'topic', 'requested_topic')}",
        "",
        f"CTA del video: {cta or 'No disponible'}",
        "",
        "Si te resultó útil, suscríbete y activa la campanita para no perderte "
        "la próxima reflexión.",
    ]
    return "\n".join(lines)


def _youtube_hashtags(ctx: dict) -> str:
    topic = _slug(_get(ctx, "topic", "requested_topic"))
    idea = _slug(_get(ctx, "idea", "requested_idea", "central_idea"))
    tags = ["#bienestar", "#saludemocional", "#reflexion"]
    if "perdon" in topic or "perdon" in idea:
        tags.append("#perdon")
    if "paz" in topic or "paz" in idea:
        tags.append("#pazinterior")
    if tags and len(tags) > 6:
        tags = tags[:6]
    return " ".join(tags)


# ─────────────────────────────────────────────
# Adaptación Facebook (copy distinta a YT, no copia mecánica)
# ─────────────────────────────────────────────

def _facebook_copy(ctx: dict, cta: str) -> str:
    hook = _hook_question(ctx.get("topic"), ctx.get("idea"))
    lines = [
        f"{hook}",
        "",
        "Esta reflexión fue pensada para quienes quieren soltar cargas que no "
        "les pertenecen y volver a vivir su día con paz.",
        "",
        "Compártela si crees que puede acompañar a alguien que lo necesite.",
    ]
    return "\n".join(lines)


def _facebook_hashtags(ctx: dict) -> str:
    topic = _slug(_get(ctx, "topic", "requested_topic"))
    idea = _slug(_get(ctx, "idea", "requested_idea", "central_idea"))
    tags = ["#bienestar", "#reflexion"]
    if "perdon" in topic or "perdon" in idea:
        tags.append("#perdon")
    return " ".join(tags)


# ─────────────────────────────────────────────
# Info técnica
# ─────────────────────────────────────────────

def _aspect_label(aspect) -> str:
    a = str(aspect or "").lower().replace("_", " ")
    # Orientación explícita gana
    if "vertical" in a:
        return "vertical 9:16"
    if "horizontal" in a or "16x9" in a or "16:9" in a:
        return "horizontal 16:9"
    if "9x16" in a or "9:16" in a:
        return "vertical 9:16"
    if a in ("short", "reel", "shorts"):
        return "vertical 9:16"
    if a in ("youtube", "video", "long", "largo"):
        return "horizontal 16:9"
    return a or "No disponible"


def _warnings_block(ctx: dict) -> list:
    items = list(ctx.get("warnings") or []) + list(ctx.get("fallbacks") or [])
    if not items:
        return ["- (ninguno registrado)"]
    return [f"- {w}" for w in items]


def _providers(ctx: dict) -> str:
    prov = ctx.get("providers") or ctx.get("assets")
    if isinstance(prov, list):
        return ", ".join(str(x) for x in prov)
    return str(prov) if prov else "No disponible"


# ─────────────────────────────────────────────
# Ensamblado del .md
# ─────────────────────────────────────────────

def _markdown_document(ctx: dict, platform: str, cta: str) -> str:
    """Construye el markdown completo para 'youtube' | 'facebook' | 'both'."""
    aspect = _aspect_label(ctx.get("aspect"))
    filename = ctx.get("filename") or f"{_slug(ctx.get('title') or ctx.get('idea'))}_{_slug(aspect)}"

    groups = []
    groups.append(f"# PAQUETE DE PUBLICACIÓN — {_get(ctx, 'title', 'tag', 'idea').capitalize()}")

    # ── Información de producción ──
    groups += [
        "## Información de producción",
        f"- **Título:** {_get(ctx, 'title', 'tag', 'idea')}",
        f"- **Tema:** {_get(ctx, 'topic', 'requested_topic')}",
        f"- **Idea original:** {_get(ctx, 'idea', 'requested_idea', 'central_idea')}",
        f"- **Enfoque editorial:** {_get(ctx, 'enfoque', 'editorial_focus')}",
        f"- **Formato:** {_get(ctx, 'formato', 'format_name')} ({aspect})",
        f"- **Relación de aspecto:** {aspect}",
        f"- **Duración real:** {_fmt_duration(ctx.get('duracion_s', ctx.get('duration_s')))}",
        f"- **Cantidad de escenas:** {_get(ctx, 'n_scenes', 'cantidad_escenas')}",
        f"- **Ruta del MP4:** {_get(ctx, 'mp4', 'ruta_mp4')}",
        f"- **Fecha de producción:** {_get(ctx, 'fecha', 'production_date')}",
        f"- **CTA utilizado:** {cta or 'No disponible'}",
        f"- **Proveedor(es) visual(es):** {_providers(ctx)}",
        "- **Warnings/fallbacks:**",
    ]
    groups += _warnings_block(ctx)

    # ── YouTube ──
    if platform in ("youtube", "both"):
        groups += [
            "",
            "## YouTube",
            "### Título recomendado",
            _youtube_title(ctx),
            "",
            "### Descripción",
            _youtube_description(ctx, cta),
            "",
            "### CTA",
            cta or "No disponible",
            "",
            "### Hashtags",
            _youtube_hashtags(ctx),
        ]

    # ── Facebook ──
    if platform in ("facebook", "both"):
        groups += [
            "",
            "## Facebook",
            "### Texto / título de publicación",
            _hook_question(ctx.get("topic"), ctx.get("idea")),
            "",
            "### Descripción / copy",
            _facebook_copy(ctx, cta),
            "",
            "### CTA",
            cta or "No disponible",
            "",
            "### Hashtags",
            _facebook_hashtags(ctx),
        ]

    groups += [
        "",
        "---",
        "",
        "> Paquete generado a partir de la producción real. Ningún dato inventado; "
        "los campos sin valor figuran como «No disponible».",
    ]
    return "\n".join(groups)


def generate_publication_package(
    *,
    context: dict,
    platform: str = "both",
    cta: str | None = None,
    output_path: str = "",
) -> str:
    """Genera el .md del paquete de publicación.

    Args:
        context: dict con los datos REALES de la producción (title/topic/idea/
                 formato/aspect/duration/scenes/mp4/fecha/cta/warnings/providers...).
        platform: 'youtube' | 'facebook' | 'both'.
        cta: CTA real usado por la producción. Si no se pasa, usa
             context['cta'] (el que eligió Production Intelligence).
        output_path: si se da, escribe el .md ahí y devuelve ese path.
                     Si no, devuelve SOLO el contenido markdown.

    Returns:
        El contenido del .md (y escribe el archivo si output_path está dado).
    """
    if platform not in PLATFORMS:
        platform = "both"

    cta = cta or context.get("cta") or context.get("cta_primary")

    md = _markdown_document(context, platform, cta)

    if output_path:
        with open(output_path, "w") as f:
            f.write(md)
        return output_path
    return md


def default_package_path(ctx: dict, aspect: str = "") -> str:
    """Ruta por defecto del .md junto al MP4 (derivada del nombre real)."""
    mp4 = ctx.get("mp4") or ""
    if mp4 and mp4.lower().endswith(".mp4"):
        base = mp4[:-4]
        return f"{base}_publicacion.md"
    aspect = _aspect_label(aspect or ctx.get("aspect"))
    name = f"{_slug(ctx.get('title') or ctx.get('idea'))}_{_slug(aspect)}"
    return f"{name}_publicacion.md"


def write_beside_mp4(*, context: dict, platform: str = "both",
                     cta: str | None = None) -> str | None:
    """Escribe el .md en la misma carpeta que el MP4 (junto al MP4 final)."""
    if not context.get("mp4"):
        return None
    if not os.path.exists(context["mp4"]):
        return None
    out = default_package_path(context)
    generate_publication_package(context=context, platform=platform,
                                 cta=cta, output_path=out)
    return out
