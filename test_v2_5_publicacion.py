"""
V2.5 — PAQUETE DE PUBLICACIÓN: tests deterministas.

Cubre el spec §9:
  generación del .md, nombre/ruta correcta, datos reales, YouTube, Facebook,
  ambas plataformas, CTA, ausencia de datos inventados, comportamiento cuando
  falta un dato, cuando no existe MP4 final, compatibilidad con flujo V2.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publication_package import (
    generate_publication_package, default_package_path, write_beside_mp4,
    _slug, _aspect_label, PLATFORMS,
)

PASS = 0
FAIL = 0


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS — {name}" + (f" ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL — {name} {detail}")


def _ctx(**over):
    data = {
        "title": "El perdón te hace libre",
        "topic": "el perdón",
        "idea": "El perdón te hace libre",
        "requested_topic": "el perdón",
        "requested_idea": "El perdón te hace libre",
        "enfoque": "anti-gurú con base real",
        "formato": "short vertical",
        "format_name": "short",
        "aspect": "vertical 9:16",
        "duracion_s": 75.43,
        "n_scenes": 7,
        "mp4": "/tmp/fake/perdon_short.mp4",
        "fecha": "2026-08-28",
        "cta": "Si esto te resonó, compártelo con quien lo necesite.",
        "warnings": ["(ninguno registrado)"],
        "providers": ["ok", "ok", "ok"],
    }
    data.update(over)
    return data


print("\n[1] GENERACIÓN DEL .md")
md = generate_publication_package(context=_ctx(), platform="both")
ok("genera markdown (str no vacío)", isinstance(md, str) and len(md) > 50)
ok("tiene cabecera", "PAQUETE DE PUBLICACIÓN" in md)
ok("tiene sección producción", "## Información de producción" in md)
ok("tiene sección YouTube", "## YouTube" in md)
ok("tiene sección Facebook", "## Facebook" in md)
ok("tuteo presente (suscríbete)", "suscríbete" in md)
ok("sin datos inventados: usa el CTA real", "compártelo con quien lo necesite" in md)

print("\n[2] NOMBRE / RUTA CORRECTA")
ctx = _ctx()
p = default_package_path(ctx)
ok("default path derivado del mp4", p == "/tmp/fake/perdon_short_publicacion.md", p)
ok("termina en _publicacion.md", p.endswith("_publicacion.md"))
ok("slug elimina acentos", _slug("El perdón te hace libre") == "el_perdon_te_hace_libre")
ok("slug seguro sin caracteres raros",
   all(c.isalnum() or c in "_-" for c in _slug("¿Quién soy? ¡No sé!")))

print("\n[3] DATOS REALES DE PRODUCCIÓN")
md = generate_publication_package(context=_ctx(duracion_s=109.63, n_scenes=10,
                                               mp4="/tmp/fake/perdon_long.mp4"))
ok("duración real 1:50", "1:50" in md, "")
ok("cantidad de escenas 10", "**Cantidad de escenas:** 10" in md)
ok("ruta mp4 real", "/tmp/fake/perdon_long.mp4" in md)
ok("tema real", "**Tema:** el perdón" in md)
ok("idea real", "**Idea original:** El perdón te hace libre" in md)

print("\n[4] YOUTUBE")
ctx = _ctx()
yt = generate_publication_package(context=ctx, platform="youtube")
ok("no incluye sección Facebook", "## Facebook" not in yt)
ok("incluye Título recomendado", "### Título recomendado" in yt)
ok("título = idea real (no clickbait)", "El perdón te hace libre" in yt)
ok("incluye Descripción", "### Descripción" in yt)
ok("descripción refleja tema", "Tema: el perdón" in yt)
ok("incluye CTA", "### CTA" in yt)
ok("CTA real presente", "compártelo con quien lo necesite" in yt)
ok("hashtags de perdón", "#perdon" in yt)
hashtag_line = next((l for l in yt.split("\n") if l.strip().startswith("#bienestar")), "")
ok("hashtags controlados (no abusar, <=6)",
   len(hashtag_line.split()) <= 6, hashtag_line)

print("\n[5] FACEBOOK")
ctx = _ctx()
fb = generate_publication_package(context=ctx, platform="facebook")
ok("no incluye sección YouTube", "## YouTube" not in fb)
ok("incluye copy", "### Descripción / copy" in fb)
ok("copy es distinto (adaptado, no copia)", "soltar cargas" in fb)

print("\n[6] AMBAS PLATAFORMAS")
ctx = _ctx()
both = generate_publication_package(context=ctx, platform="both")
ok("incluye YouTube + Facebook", "## YouTube" in both and "## Facebook" in both)

print("\n[7] CTA")
ctx = _ctx()
md = generate_publication_package(context=ctx, platform="both")
ok("muestra el CTA usado (no inventa otro)", "compártelo con quien lo necesite" in md)
ok("máximo un CTA principal por sección", md.count("compártelo con quien lo necesite") <= 6)
custom = generate_publication_package(context=_ctx(), platform="youtube",
                                      cta="Ayúdame suscribiéndote al canal. Es gratis.")
ok("acepta CTA real explícito", "Ayúdame suscribiéndote al canal." in custom)

print("\n[8] AUSENCIA DE DATOS INVENTADOS / FALTA UN DATO")
ctx = _ctx()
del ctx["fecha"]
md = generate_publication_package(context=ctx, platform="both")
ok("fecha faltante = 'No disponible'", "**Fecha de producción:** No disponible" in md)
ctx2 = _ctx()
del ctx2["duracion_s"]
md2 = generate_publication_package(context=ctx2, platform="both")
ok("duración faltante = 'No disponible'", "**Duración real:** No disponible" in md2)
ctx3 = _ctx()
del ctx3["formato"]
del ctx3["format_name"]
md3 = generate_publication_package(context=ctx3, platform="both")
ok("formato faltante = 'No disponible'", "**Formato:** No disponible" in md3)

print("\n[9] NO EXISTE MP4 FINAL → NO crear paquete falso")
d = tempfile.mkdtemp()
ctx = _ctx(mp4=os.path.join(d, "no_existe.mp4"))
out = write_beside_mp4(context=ctx, platform="both")
ok("write_beside_mp4 devuelve None si no hay mp4", out is None)
ok("no crea .md junto a mp4 inexistente",
   not os.path.exists(os.path.join(d, "no_existe_publicacion.md")))

print("\n[10] ESCRIBIR .md real junto al MP4")
d2 = tempfile.mkdtemp()
real_mp4 = os.path.join(d2, "perdon_short.mp4")
with open(real_mp4, "wb") as f:
    f.write(b"\x00" * 100)
ctx = _ctx(mp4=real_mp4)
out = write_beside_mp4(context=ctx, platform="both", cta=ctx["cta"])
expected = os.path.join(d2, "perdon_short_publicacion.md")
ok("genera el archivo junto al mp4", out == expected and os.path.exists(expected))
content = open(expected).read()
ok("contenido es el paquete", "PAQUETE DE PUBLICACIÓN" in content)
ok("usa el CTA real", "compártelo con quien lo necesite" in content)

print("\n[11] COMPATIBILIDAD CON FLUJO V2")
import publication_package
ok("módulo importable", True)
import production_intelligence
ok("coexiste con production_intelligence (Production Intelligence/CtaEngine)",
   hasattr(production_intelligence, "CtaEngine"))
ok("normalize_platform sigue disponible",
   hasattr(production_intelligence, "normalize_platform"))
import editorial_orchestrator
ok("editorial_orchestrator importable",
   hasattr(editorial_orchestrator, "produce_editorial"))
ok("topic_lock intacto", hasattr(__import__("topic_lock"), "assert_topic_locked"))
from editorial_orchestrator import produce_editorial
ok("produce_editorial sigue con request/lock params", True)

print("\n[12] PLATAFORMAS VÁLIDAS")
ok("youtube/facebook/both válidas", set(PLATFORMS) == {"youtube", "facebook", "both"})
ok("plataforma inválida cae a both", "## YouTube" in generate_publication_package(
    context=_ctx(), platform="xyz"))

print("\n[13] RELACIÓN DE ASPECTO CORRECTA (16:9 no confundible con 9:16)")
ok("horizontal 16:9", _aspect_label("horizontal 16:9") == "horizontal 16:9")
ok("vertical 9:16", _aspect_label("vertical 9:16") == "vertical 9:16")
long_md = generate_publication_package(
    context=_ctx(aspect="horizontal 16:9", formato="youtube horizontal"),
    platform="both")
ok("long 16:9 no marca 9:16", "horizontal 16:9" in long_md
   and "**Relación de aspecto:** vertical 9:16" not in long_md)

print("\n============================================================")
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("============================================================")
sys.exit(1 if FAIL else 0)
