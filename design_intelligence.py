"""DESIGN INTELLIGENCE — capa de conocimiento y decisiones de diseño.

NO reemplaza ni duplica: el prompt final lo compone director_visual.compose_prompt,
el MOBILE_120PX_TEST vive en visual_critic, los presets CTA en assets/brand/cta,
la identidad (fuentes/colores/señales/estilos/metáforas) en assets/brand/brand.config.json.

Esta capa interviene ANTES de decidir la composición y entrega decisiones
justificadas: contexto obligatorio, paleta por emoción, contraste WCAG real
(calculado, no adivinado), tipografía por función, jerarquía, plan de
composición, identity fit y el Design Decision Report completo.

Uso:
    from design_intelligence import DesignContext, decision_report, contrast_report
    ctx = DesignContext(producto=..., formato=..., audiencia=..., mensaje=...,
                        meta_emocional=..., accion_primaria=..., rol_foto=...,
                        rol_marca=..., emocion="alivio", style_family="D_...")
    print(decision_report(ctx, brief))   # brief = dict para director_visual
"""
import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
_BRAND_PATH = os.path.join(_BASE, "assets", "brand", "brand.config.json")

with open(_BRAND_PATH) as _f:
    BRAND = json.load(_f)

# ---------------------------------------------------------------------------
# 1. CONTEXTO DE DISEÑO (obligatorio — no se diseña sin esto)
# ---------------------------------------------------------------------------

_CAMPOS_OBLIGATORIOS = ("producto", "formato", "audiencia", "mensaje",
                        "meta_emocional", "accion_primaria", "rol_foto",
                        "rol_marca")


class DesignContext(dict):
    """Contexto de diseño. Falla rápido si falta un campo obligatorio."""

    def __init__(self, emocion="", style_family="", **kw):
        super().__init__(**kw)
        faltan = [k for k in _CAMPOS_OBLIGATORIOS if not kw.get(k)]
        if faltan:
            raise ValueError(f"DesignContext incompleto, faltan: {faltan}")
        self["emocion"] = emocion
        self["style_family"] = style_family


# ---------------------------------------------------------------------------
# 3. PALETAS POR EMOCIÓN (emocional ≠ desaturado, profundo ≠ oscuro)
# ---------------------------------------------------------------------------

PALETAS_EMOCION = {
    "calma":        {"PRIMARY": "#7FA98E", "SECONDARY": "#F5EBDD", "ACCENT": "#D9A441",
                     "NEUTRAL": "#2C2925", "BACKGROUND": "#F7F3EC", "TEXT": "#2C2925",
                     "PORQUE": "cremas + verdes suaves + madera clara; ritmo bajo"},
    "esperanza":    {"PRIMARY": "#6FA85C", "SECONDARY": "#FFF7E8", "ACCENT": "#E8B84B",
                     "NEUTRAL": "#3A342C", "BACKGROUND": "#FBF6EA", "TEXT": "#3A342C",
                     "PORQUE": "verdes vivos + crema + amarillo suave; luz creciente"},
    "alivio":       {"PRIMARY": "#8FBFAE", "SECONDARY": "#FFF7E8", "ACCENT": "#D9A441",
                     "NEUTRAL": "#33302A", "BACKGROUND": "#FAF6EE", "TEXT": "#33302A",
                     "PORQUE": "blancos cálidos + verdes + celestes; apertura y aire"},
    "introspeccion": {"PRIMARY": "#6E87A8", "SECONDARY": "#EAD9C8", "ACCENT": "#C06B4A",
                      "NEUTRAL": "#2E2B27", "BACKGROUND": "#F2EDE4", "TEXT": "#2E2B27",
                      "PORQUE": "azules suaves + terracota + neutros cálidos; mirada adentro"},
    "cambio":       {"PRIMARY": "#E52323", "SECONDARY": "#F5EBDD", "ACCENT": "#D9A441",
                     "NEUTRAL": "#2C2925", "BACKGROUND": "#F7F2E9", "TEXT": "#2C2925",
                     "PORQUE": "neutros + UN acento fuerte; el contraste ES el cambio"},
    "dolor":        {"PRIMARY": "#5E6B7A", "SECONDARY": "#E9E2D6", "ACCENT": "#C98A4B",
                     "NEUTRAL": "#2A2723", "BACKGROUND": "#F0EBE1", "TEXT": "#2A2723",
                     "PORQUE": "profundos pero luminosos; el dolor NO se rinde a estética dark"},
    "crecimiento":  {"PRIMARY": "#5E9C4E", "SECONDARY": "#F3F0E4", "ACCENT": "#E8B84B",
                     "NEUTRAL": "#33302A", "BACKGROUND": "#F8F5EB", "TEXT": "#33302A",
                     "PORQUE": "verde + luz + variedad natural; proceso visible"},
    "perdona_soltar": {"PRIMARY": "#D9A441", "SECONDARY": "#FFF7E8", "ACCENT": "#7FA98E",
                       "NEUTRAL": "#33302A", "BACKGROUND": "#FBF7EF", "TEXT": "#33302A",
                       "PORQUE": "espacios abiertos + neutrales + UN acento de posibilidad"},
}

# La marca es referencia, no obligación: la paleta se deriva de
# EMOCIÓN + MENSAJE + FOTOGRAFÍA + MARCA + LEGIBILIDAD.
_MARCA = {"PRIMARY": "#E52323", "SECONDARY": "#FFF7E8",
          "ACCENT": "#D9A441", "NEUTRAL": "#2C2925"}


def palette_for(emocion):
    """Paleta por rol para una emoción, anclada a la marca donde corresponde."""
    p = dict(PALETAS_EMOCION.get(emocion.lower(), {}))
    if not p:
        raise ValueError(f"emoción sin paleta: {emocion}. "
                         f"Opciones: {', '.join(PALETAS_EMOCION)}")
    # El rojo de marca se reserva para el título (rol TEXT/brand), no se fuerza
    # en la foto: la fotografía mantiene sus propios colores naturales.
    p["BRAND_TITLE"] = _MARCA["PRIMARY"]
    p["PORQUE_MARCA"] = ("rojo/crema/dorado reservados a la capa gráfica; "
                         "la foto conserva su paleta natural")
    return p


# ---------------------------------------------------------------------------
# 4. ACCESIBILIDAD — contraste WCAG 2.x REAL (matemática, no a ojo)
# ---------------------------------------------------------------------------

def _lum(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg_hex, bg_lum):
    """Ratio WCAG entre un color HEX y una luminancia de fondo (0..1).
    bg_lum puede ser float (muestreo de foto) o hex string."""
    bg = _lum(bg_lum) if isinstance(bg_lum, str) else float(bg_lum)
    l1, l2 = sorted((_lum(fg_hex), bg), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def sample_background_luminance(image_path, box):
    """Luminancia media + desvío estándar de una zona (x0,y0,x1,y1) de la foto.
    Si el desvío es alto, el fondo es variable → CONTRAST_REQUIRES_VISUAL_QA."""
    from PIL import Image, ImageStat
    im = Image.open(image_path).convert("L").crop(box)
    st = ImageStat.Stat(im)
    return st.mean[0] / 255.0, st.stddev[0]


_ESCALERA = ("1. mover el texto", "2. cambiar color del texto",
             "3. sombra local", "4. halo",
             "5. degradado/máscada detrás del texto",
             "6. retocar la foto SOLO en la zona necesaria")


def contrast_report(text_hex, bg_lum, texto_grande=True, stddev=None):
    """Informe de contraste. Texto grande (≥24px o ≥19px bold) target AA 3:1;
    normal 4.5:1. Nunca recomienda oscurecer toda la foto."""
    target = 3.0 if texto_grande else 4.5
    ratio = contrast_ratio(text_hex, bg_lum)
    out = {"TEXT_COLOR": text_hex, "BACKGROUND_SAMPLE": round(float(bg_lum), 3),
           "CONTRAST_RATIO": round(ratio, 2), "TARGET_RATIO": target,
           "PASS": ratio >= target}
    if stddev is not None and stddev > 60:
        out["CONTRAST_REQUIRES_VISUAL_QA"] = True
        out["NOTA"] = f"fondo variable (stddev {stddev:.0f}) — verificar con crítico visual"
    if not out["PASS"]:
        out["ESCALERA_CORRECCION"] = list(_ESCALERA)
        out["PROHIBIDO"] = "oscurecer toda la fotografía"
    return out


# ---------------------------------------------------------------------------
# 2. VISUAL PHILOSOPHY (método canvas-design: filosofía → expresión visual)
# ---------------------------------------------------------------------------
# NO es un layout ni una plantilla: es la sensación que gobierna las decisiones
# posteriores (composición, luz, color, escala). Se deriva de emoción +
# metáfora + anclas de marca, nunca de un ejemplo copiado.

_FILOSOFIA_POR_EMOCION = {
    "calma": ("quiet order", "espacio ordenado y contenido", "luz suave y estable",
              "colores bajados, sin saltos", "escala serena, sin dominaciones bruscas",
              "respiración amplia entre elementos"),
    "esperanza": ("growing light", "espacio que se abre hacia el fondo", "luz natural creciente, entra y avanza",
                  "cromática cálida con UN punto de energía", "lo pequeño crece dentro de lo grande",
                  "aire delante del sujeto: lugar hacia donde ir"),
    "alivio": ("exhale", "espacio que se expande tras una tensión", "luz difusa de ventana, sin dureza",
               "paleta clara que se aclara hacia arriba", "el peso visual baja, el aire sube",
               "composición respirada: nada aprieta"),
    "introspeccion": ("inward gaze", "profundidad en capas, mirada adentro", "luz lateral suave, media sombra con detalle",
                      "contrastes contenidos, un acento terroso", "sujeto pequeño en ambiente grande",
                      "el vacío sostiene el pensamiento"),
    "cambio": ("threshold", "umbral: dos zonas, antes y después", "luz que cruza el borde entre zonas",
               "neutros + UN solo acento fuerte: el contraste ES el cambio", "el elemento clave rompe la escala esperada",
               "la zona vacía es el futuro posible"),
    "dolor": ("dignified weight", "espacio contenido pero luminoso", "luz baja cálida, nunca penumbra total",
              "profundos pero con luz: el dolor no se rinde a la estética dark", "peso abajo, cielo arriba",
              "silencio visual alrededor del objeto"),
    "crecimiento": ("visible process", "espacio en progresión, diagonal ascendente", "luz de mañana, dirección clara",
                    "verde vivo sobre neutros claros", "lo pequeño nítido contra fondo amplio",
                    "espacio por donde seguir creciendo"),
    "perdona_soltar": ("open hands, open space", "espacio que queda disponible tras soltar", "luz natural plena, ausencia significativa",
                       "pocos objetos, paleta clara con UN acento de posibilidad", "la ausencia ocupa más marco que la presencia",
                       "composición respirada: lo que falta ES el mensaje"),
}


def visual_philosophy(ctx):
    """VISUAL PHILOSOPHY previa al diseño: qué sensación buscamos y cómo se
    comportan espacio/luz/color/escala/vacío. Genera decisiones, no decoración."""
    emocion = (ctx.get("emocion") or ctx.get("meta_emocional") or "").lower()
    base = _FILOSOFIA_POR_EMOCION.get(
        emocion, ("clear warmth", "espacio habitable y luminoso",
                  "luz natural con sombras con detalle", "cromática cálida contenida",
                  "un foco claro, escala honesta", "aire suficiente para respirar"))
    meta = BRAND.get("metaphor_families", {})
    fam = next((k for k, v in meta.items()
                if k != "regla_general" and isinstance(v, str)
                and any(w in v.lower() for w in emocion.split("_"))), None)
    return {
        "NOMBRE": base[0],
        "MENSAJE": ctx.get("mensaje", ""),
        "SENSACION_ESPACIAL": base[1],
        "LUZ": base[2],
        "COLOR": base[3],
        "ESCALA": base[4],
        "ESPACIO_NEGATIVO": base[5],
        "METAFORA_FAMILIA": f"{fam} — {meta.get(fam, '')}" if fam else meta.get("regla_general", ""),
        "REGLA": "la filosofía gobierna las decisiones siguientes; si una "
                 "decisión la contradice, cambia la decisión o cambia la filosofía",
    }


# ---------------------------------------------------------------------------
# ANTI-SLOP (adaptado de sboghossian/design-skill a miniatura 9:16/16:9)
# ---------------------------------------------------------------------------
# Cada elemento debe tener una razón. No es minimalismo obligatorio.
# Check programático PRE-GIMP sobre las decisiones ya tomadas.

def anti_slop(fuentes=(), colores=(), elementos=(), estilo_familia=""):
    """Verifica las decisiones de diseño declaradas.
    - fuentes: lista de familias tipográficas usadas
    - colores: lista de dicts {"hex","funcion"} (solo cromáticos)
    - elementos: lista de dicts {"nombre","porque"}
    - estilo_familia: familia elegida (vacía = composición por defecto = sospechosa)
    Devuelve ANTI_SLOP PASS|FAIL con MÁXIMO 3 problemas concretos."""
    problemas = []
    if len(set(fuentes)) > BRAND.get("typography", {}).get("max_familias_por_pieza", 3):
        problemas.append(f"{len(set(fuentes))} familias tipográficas: máximo 3; "
                         "jerarquía viene de tamaño/peso/espacio, no de más fuentes")
    sin_funcion = [c["hex"] for c in colores if not (c or {}).get("funcion")]
    if len(sin_funcion):
        problemas.append(f"color(es) sin función declarada: {', '.join(sin_funcion[:3])}")
    elif len(colores) > 3:
        problemas.append(f"{len(colores)} colores cromáticos: cada color adicional "
                         "diluye la jerarquía; máximo 3 + neutros")
    sin_razon = [e["nombre"] for e in elementos if not (e or {}).get("porque")]
    if sin_razon:
        problemas.append("elemento(s) agregado(s) 'porque quedan bien': "
                         f"{', '.join(sin_razon[:3])}")
    if not estilo_familia:
        problemas.append("sin style_family: composición genérica, podría "
                         "pertenecer a cualquier canal")
    return {"ANTI_SLOP": "FAIL" if problemas else "PASS",
            "PROBLEMAS": problemas[:3],
            "CRITERIO": "cada elemento debe tener una razón comunicable en "
                        "una frase; el espacio vacío NO es problema a resolver"}


# ---------------------------------------------------------------------------
# 6. COLOR — teoría consolidada (HSL, temperatura, armonía, restricción)
# ---------------------------------------------------------------------------

def hex_to_hsl(hex_color):
    """HEX → (H 0-360, S 0-100, L 0-100)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, round(l * 100, 1)
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        hh = ((g - b) / d + (6 if g < b else 0)) / 6
    elif mx == g:
        hh = ((b - r) / d + 2) / 6
    else:
        hh = ((r - g) / d + 4) / 6
    return round(hh * 360, 1), round(s * 100, 1), round(l * 100, 1)


# Cromaticidad REAL (chroma = max-min): la S de HSL se dispara en casi-blancos
# y casi-negros (un crema #FFF7E8 da S≈100 sin tener color), así que la
# clasificación usa chroma, no S.
def _chroma(hex_color):
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (max(rgb) - min(rgb)) * 100


_UMBRAL_CROMA = 15.0


def _temperatura(hex_color):
    h, s, _l = hex_to_hsl(hex_color)
    if _chroma(hex_color) < _UMBRAL_CROMA:
        return "neutral"
    if h <= 70 or h >= 320:
        return "calido"
    if 160 <= h <= 280:
        return "frio"
    return "intermedio"


def _armonia(colores):
    crom = []
    for hx in colores:
        h, _s, _l = hex_to_hsl(hx)
        if _chroma(hx) >= _UMBRAL_CROMA:
            crom.append(h)
    if len(crom) == 0:
        return "acromatico"
    if len(crom) == 1:
        return "neutral + acento"
    diffs = [min(abs(a - b), 360 - abs(a - b)) for i, a in enumerate(crom)
             for b in crom[i + 1:]]
    if all(155 <= d <= 205 for d in diffs):
        return "complementaria"
    if all(d <= 60 for d in diffs):
        return "análoga"
    return "mixta (revisar intención)"


def color_report(palette):
    """Análisis cromático completo de una paleta por roles:
    HSL, temperatura, armonía global y restricción."""
    analisis, hues_chroma, crom = {}, [], 0
    for rol, v in palette.items():
        hexv = v if isinstance(v, str) else v.get("hex", "")
        if not hexv.startswith("#"):
            continue
        h, s, l = hex_to_hsl(hexv)
        analisis[rol] = {"hex": hexv.upper(), "hue": h, "sat": s, "lum": l,
                         "temperatura": _temperatura(hexv)}
        if _chroma(hexv) >= _UMBRAL_CROMA:
            hues_chroma.append((h, _chroma(hexv)))
            crom += 1
    return {"COLORES": analisis,
            "ARMONIA": _armonia([hx for v in analisis.values()
                                 for hx in [v["hex"]]]),
            "CROMATICOS": crom,
            "RESTRICCION_PASS": crom <= 3,
            "JERARQUIA_ROLES": [r for r in ("PRIMARY", "SECONDARY", "ACCENT",
                                            "NEUTRAL", "BACKGROUND", "TEXT")
                                if r in analisis],
            "NOTA": "la elección parte de contexto+emoción+fotografía+marca+"
                    "accesibilidad, nunca de 'cálido = beige'"}


# ---------------------------------------------------------------------------
# 5-6. TIPOGRAFÍA POR FUNCIÓN + JERARQUÍA
# ---------------------------------------------------------------------------

def typography_plan(formato="thumbnail_9x16"):
    """Roles tipográficos desde la identidad (brand.config.json) con función.
    La identidad actual es referencia, no obligación universal."""
    b = BRAND["brand"]
    t = BRAND.get("typography", {}).get("roles", {})
    def _wn(key):
        return t.get(key, {}).get("when_not", "")
    roles = {
        "DISPLAY_FONT": {"font": b["title_font"], "ROLE": "título",
                         "WHY": "display condensada de alto impacto: forma gráfica, domina antes de entender la foto",
                         "WHEN_NOT": _wn("title") or "NO para texto corrido ni frases largas",
                         "SERIF": False},
        "BODY_FONT": {"font": b["subtitle_font"], "ROLE": "subtítulo / capa emocional",
                      "WHY": "serif humana: contraste fuerza+humanidad, tono editorial",
                      "WHEN_NOT": _wn("subtitle") or "NO para CTA ni tamaños funcionales pequeños",
                      "SERIF": True},
        "CTA_FONT": {"font": b["cta_font"], "ROLE": "CTA / info funcional",
                     "WHY": "sans contemporánea funcional: affordance de interfaz",
                     "WHEN_NOT": _wn("cta") or "NO como título: neutraliza la personalidad",
                     "SERIF": False},
    }
    jerarquia = {"thumbnail_9x16": {"TITLE": (90, 160), "SUBTITLE": (42, 70), "CTA": (34, 60)},
                 "thumbnail_16x9": {"TITLE": (110, 200), "SUBTITLE": (48, 84), "CTA": (36, 64)},
                 "short": {"TITLE": (70, 120), "SUBTITLE": (40, 64), "CTA": (32, 52)}}
    return {"ROLES": roles, "JERARQUIA_PX": jerarquia.get(formato, jerarquia["thumbnail_9x16"]),
            "CRITERIO": "TITLE >> SUBTITLE >> CTA (3 niveles, de general a "
                        "específico); los rangos son orientativos. Diferencias "
                        "SUTILES entre niveles no funcionan: cada nivel debe "
                        "distinguirse claramente (tamaño y peso)"}


# ---------------------------------------------------------------------------
# 7-8. COMPOSICIÓN + GRID (calculado, no por costumbre)
# ---------------------------------------------------------------------------

def grid_1080x1920(w=1080, h=1920):
    """Grid relativo al canvas: márgenes, eje, baseline de bloques."""
    m = round(w * 0.059)  # 64px @1080 — margen editorial
    return {"margen_lateral": m, "eje_principal": "izquierda",
            "columna_texto_hasta": round(w * 0.55),
            "baseline_titulo": round(h * 0.52),
            "zona_cta_y": round(h * 0.855),
            "safe_area": {"x": m, "y": round(h * 0.045),
                          "w": w - 2 * m, "h": round(h * 0.91)}}


def composition_plan(focal_point, text_zone, secondary_zone, negative_space,
                     visual_flow, crop_strategy, con_grid=True):
    """COMPOSITION PLAN obligatorio antes de diseñar.
    Cada zona debe JUSTIFICARSE para ESTA fotografía: 'texto arriba a la
    izquierda' no es una explicación suficiente — explicar por qué esa zona
    tiene sentido (qué hay en la foto, por dónde mira el ojo, qué se respira)."""
    return {"FOCAL_POINT": focal_point, "TEXT_ZONE": text_zone,
            "SECONDARY_ZONE": secondary_zone, "NEGATIVE_SPACE": negative_space,
            "VISUAL_FLOW": visual_flow, "CROP_STRATEGY": crop_strategy,
            "GRID": grid_1080x1920() if con_grid else None,
            "SAFE_MARGINS": grid_1080x1920()["safe_area"],
            "JUSTIFICACION_OBLIGATORIA": ("cada zona: describir + POR QUÉ tiene "
                                          "sentido para esta fotografía"),
            "PRINCIPIOS": ("UN solo punto focal (si todo es igual, nada destaca); "
                           "jerarquía con diferencias CLARAS (las señales sutiles "
                           "no funcionan); balance asimétrico (grande balancea "
                           "chico, intenso balancea neutro); espacio negativo "
                           "activo da poder al focal; pregunta rectora: "
                           "¿qué se entiende en 1 segundo?"),
            "REGLA_EXTENSION": ("el acento domina ocupando MENOS área que el "
                                "neutro/fondo (Itten: contraste de extensión)")}


_ZONAS_PLAN = ("FOCAL_POINT", "TEXT_ZONE", "SECONDARY_ZONE", "NEGATIVE_SPACE",
               "VISUAL_FLOW", "CROP_STRATEGY")


def composition_warnings(plan):
    """Advierte zonas descritas sin justificación (ubicación sola no alcanza).
    Heurística: <35 caracteres o sin verbo/conector de razón ('porque', 'para',
    'así', 'ya que', 'deja', 'guía')."""
    avisos = []
    claves = ("porque", "para ", "así", "aí ", "ya que", "deja", "guía",
              "aprovecha", "contraste", "respira", "sostiene", "equilibra",
              "entra", "sale", "baja", "sube", "ruta", "recorre", "invita",
              "evita", "conserva", "protege", "destaca")
    for z in _ZONAS_PLAN:
        txt = str(plan.get(z, ""))
        if len(txt) < 35 or not any(c in txt.lower() for c in claves):
            avisos.append(f"{z}: justificación insuficiente ('{txt[:40]}') — "
                          "explicar por qué esa zona sirve para ESTA fotografía")
    return avisos


# ---------------------------------------------------------------------------
# 10. MOBILE TEST — delega en visual_critic (NO duplicar)
# ---------------------------------------------------------------------------

def mobile_test(image_path):
    from visual_critic import _mobile_120px_test
    r = _mobile_120px_test(image_path)
    r["MOBILE_TEST"] = "FAIL" if (r.get("title_identifiable") == "NO"
                                  or r.get("not_mush") == "MUSH") else "PASS"
    r["ORDEN_CORRECCION"] = ["título", "focal point", "exceso de elementos", "contraste"]
    r["PROHIBIDO"] = "corregir agregando decoración"
    return r


# ---------------------------------------------------------------------------
# 11. CTA — delega en presets existentes (NO reinventar)
# ---------------------------------------------------------------------------

def cta_component(nombre_preset):
    with open(os.path.join(_BASE, "assets", "brand", "cta", "presets.json")) as f:
        presets = json.load(f)
    if nombre_preset not in presets:
        raise ValueError(f"preset CTA inexistente: {nombre_preset}. "
                         f"Opciones: {', '.join(k for k in presets if k != 'suscribite_logo')}")
    return presets[nombre_preset]


# ---------------------------------------------------------------------------
# 13. IDENTITY FIT — principios, no repetición literal
# ---------------------------------------------------------------------------

def identity_fit(señales_presentes):
    """IDENTITY_FIT 0-10 según cuántas señales de identidad cumple la pieza.
    Emparejamiento por tokens (acepta español o inglés: 'Anton', 'rojo',
    'editorial'...). No premia repetición literal: 10/10 no es obligatorio."""
    stop = {"de", "la", "el", "y", "con", "para", "un", "una", "the", "of", "and"}
    alias = {"red": "rojo", "cream": "crema", "title": "titulo", "subtitle": "subtitulo",
             "luminous": "luminosa", "photography": "fotografia", "photo": "foto",
             "graphic": "grafico", "growth": "crecimiento", "secondary": "secundario",
             "human": "humano", "natural": "natural", "large": "grande", "big": "grande",
             "depth": "profundidad", "serif": "serif", "anton": "anton",
             "georgia": "georgia", "cta": "cta", "editorial": "editorial"}
    def _tokens(txt):
        out = set()
        for w in txt.lower().replace("á", "a").replace("é", "e").replace("í", "i")\
                       .replace("ó", "o").replace("ú", "u").split():
            w = "".join(c for c in w if c.isalnum())
            if len(w) >= 3 and w not in stop:
                out.add(alias.get(w, w))
        return out
    prov = _tokens(" ".join(señales_presentes))
    presentes, faltan = [], []
    for s in BRAND["identity_signals"]:
        st = _tokens(s)
        (presentes if st & prov else faltan).append(s)
    return {"IDENTITY_FIT": round(10 * len(presentes) / max(len(BRAND["identity_signals"]), 1), 1),
            "CUMPLE": presentes, "FALTAN": faltan,
            "NOTA": "la identidad vive en principios: una pieza puede ser 7/10 "
                    "y ser correcta si rompe con intención"}


# ---------------------------------------------------------------------------
# 14-16. DESIGN DECISION REPORT (delega el prompt en director_visual)
# ---------------------------------------------------------------------------

def decision_report(ctx, brief, image_path=None):
    """Bloque completo ANTES de GIMP. brief = dict para director_visual
    (debe incluir style_family coherente con ctx)."""
    import director_visual as dv
    pal = palette_for(ctx["emocion"])
    tip = typography_plan("thumbnail_16x9" if "16x9" in ctx["formato"] else
                          ("short" if "short" in ctx["formato"] else "thumbnail_9x16"))
    fams = BRAND["style_families"]
    fam = ctx.get("style_family", "")
    rep = {
        "CONTEXT": {k: ctx[k] for k in _CAMPOS_OBLIGATORIOS},
        "AUDIENCE": ctx["audiencia"],
        "EMOTIONAL_GOAL": ctx["meta_emocional"],
        "VISUAL_PHILOSOPHY": visual_philosophy(ctx),
        "VISUAL_CONCEPT": BRAND["metaphor_families"].get("regla_general", ""),
        "STYLE_SELECTED": f"{fam} — {fams.get(fam, '(sin familia)')}" if fam else "(sin elegir)",
        "COLOR_PALETTE": {k: v for k, v in pal.items() if not k.startswith("PORQUE")},
        "HEX_CODES": pal.get("PORQUE", "") + " | " + pal.get("PORQUE_MARCA", ""),
        "COLOR_ANALYSIS": color_report({k: v for k, v in pal.items()
                                        if not k.startswith(("PORQUE", "BRAND"))}),
        "TYPOGRAPHY": tip,
        "ANTI_SLOP": anti_slop(
            fuentes=[r["font"] for r in tip["ROLES"].values()],
            colores=[{"hex": v, "funcion": f"rol {k} de la paleta emocional"}
                     for k, v in pal.items()
                     if isinstance(v, str) and v.startswith("#")
                     and _chroma(v) >= _UMBRAL_CROMA],
            estilo_familia=fam),
        "COMPOSITION": brief.get("composition_plan", "(falta composition_plan)"),
    }
    if isinstance(rep["COMPOSITION"], dict):
        avisos = composition_warnings(rep["COMPOSITION"])
        if avisos:
            rep["COMPOSITION_WARNINGS"] = avisos
    rep.update({
        "CTA": ctx.get("cta_preset", "suscribite_logo"),
        "ACCESSIBILITY": "ver contrast_report() sobre la foto generada; "
                         "escala: mover texto > color > sombra local > halo > "
                         "máscara > retoque zonal. NUNCA oscurecer toda la foto.",
        "MOBILE_TEST": mobile_test(image_path) if image_path else
                       "pendiente: correr tras generar (visual_critic --mode design)",
        "FINAL_IMAGE_PROMPT": dv.compose_prompt(brief),
    })
    return rep


# ---------------------------------------------------------------------------
# 18. REGLA DE CALIDAD (puerta final)
# ---------------------------------------------------------------------------

_CALIDAD = ("se_entiende_en_1_segundo", "emocion_correcta", "principal_claro",
            "color_con_intencion", "tipografia_con_funcion", "composicion_jerarquia",
            "cta_accionable", "contraste_suficiente", "funciona_en_movil",
            "foto_y_diseno_misma_marca", "nada_eliminar_sin_perder_significado")


def quality_gate(respuestas):
    """Puerta de calidad. Si 'nada_eliminar...' es False → ELIMINAR lo sobrante."""
    faltan = [k for k in _CALIDAD if not respuestas.get(k)]
    if faltan:
        return {"LISTA": False, "FALLA": faltan,
                "REGLA": "si algo puede eliminarse sin perder significado: ELIMINARLO. "
                         "CLARIDAD + JERARQUÍA + EMOCIÓN + FUNCIÓN, nunca decoración."}
    return {"LISTA": True}


if __name__ == "__main__":
    import sys
    ctx = DesignContext(
        producto=sys.argv[1] if len(sys.argv) > 1 else "video del canal",
        formato="thumbnail_9x16",
        audiencia="mujeres 35-64, bienestar, feed móvil",
        mensaje="idea principal de la pieza",
        meta_emocional="alivio",
        accion_primaria="click al video",
        rol_foto="simbolizar",
        rol_marca="título rojo Anton + CTA logo + columna editorial",
        emocion="alivio", style_family="D_espacio_vacio_contemplativo")
    print(json.dumps(palette_for(ctx["emocion"]), ensure_ascii=False, indent=2))
    print(json.dumps(typography_plan(), ensure_ascii=False, indent=2)[:400])
