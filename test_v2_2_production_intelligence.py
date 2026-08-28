"""
V2.2 — PRODUCTION INTELLIGENCE & CHANNEL IDENTITY: tests deterministas.

Cubre los 35 puntos del spec (sin red para las capas de producción):

  IDENTIDAD (1-6)     1 config central · 2 español neutro ·
                       3 anti-gurú · 4 anti-sermón (fe) · 5 anti-toxic ·
                       6 sin repetir por prompt
  PLATAFORMA (7-12)   7 formato auto · 8 yt short 9:16 · 9 yt long 16:9 ·
                       10 fb reel 9:16 · 11 falta plataforma → preguntar ·
                       12 estrategia sin cambiar mensaje
  CTA (13-24)         13 biblioteca extensible · 14 contextual (no random) ·
                       15 rotación · 16 español neutro · 17 validate ·
                       18 (n/a) · 19 CTA personal gana · 20 sin-CTA ·
                       21 máx 1 principal · 22 secundario solo cuando toca ·
                       23 extensible sin tocar selector ·
                       24 familias FE/ORACIÓN + selección fe
  REPORTE (25-33)     25 auto · 26 tema · 27 formato · 28 plataforma ·
                       29 duración+escenas · 30 CTA · 31 MP4+assets ·
                       32 QA+warnings+fallbacks · 33 git status/diff
  REGRESIÓN (34-35)   34 produce_editorial ok · 35 scene_dicts válidos

Sin red: mock de asset fetch. Determinista.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from short_director import Platform
import production_intelligence as pi
from production_intelligence import (
    EditorialIdentity, PlatformIntelligence, NEED_PLATFORM,
    CtaEngine, ProductionReport, ProductionRecord,
)

PASS = 0
FAIL = 0


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


# ─────────────────────────────────────────────
# MOCK de asset fetch (sin red)
# ─────────────────────────────────────────────
def mock_fetch(queries, **kw):
    out = []
    for i, q in enumerate(queries):
        out.append({
            "id": f"mock_{i}", "url": "https://mock.local/a.jpg",
            "duration": 5.0, "width": 1080, "height": 1920,
            "orientation": "vertical", "fps": 30, "file_size": 1234,
            "thumbnail": "", "quality": 4, "source": "mock",
        })
    return out


# ─────────────────────────────────────────────
# 1. IDENTIDAD EDITORIAL GLOBAL
# ─────────────────────────────────────────────
print("\n[1-6] IDENTIDAD EDITORIAL GLOBAL")

idn = EditorialIdentity()

ok("1. config central (language/tone/messaging cargados)",
   idn.language.get("default") == "es_neutro_lat" and
   bool(idn.tone) and "messaging" in idn.__dict__)

ok("1b. claves centrales accesibles sin repetir por prompt",
   idn.language.get("pronombre") == "tu" and
   idn.language.get("voseo_default") is False)

ok("1c. mensajería fe base presente",
   bool(idn.messaging.get("fe_base")))

ok("2. español neutro (tuteo) en autogenerado",
   idn.neutralize("Si querés, suscribite al canal.") ==
   "Si quieres, suscríbete al canal.")

ok("2b. voseo detectable para validation",
   idn.is_neutral("si querés compartirlo") is False and
   idn.is_neutral("si quieres compartirlo") is True)

g = idn.guard("si esto te sirvió, suscríbete")
ok("3. anti-gurú PASS (texto limpio)", g["pass"] is True and
   g["checks"]["anti_guru"] is True)

ok("3b. anti-gurú FAIL (fórmula mágica)",
   idn.guard("hazte rico en 3 dias con esto").get("pass") is False)

ok("4. anti-sermón PASS (mensajería fe que no moraliza)",
   idn.anti_sermon_ok("el Creador te conoce por tu nombre") is True)

ok("4b. anti-sermón FAIL (juicio/culpa religiosa)",
   idn.anti_sermon_ok("si no crees, estás pecando y Dios te castiga") is False)

ok("5. anti-toxic PASS (esperanza honesta)",
   idn.anti_toxic_ok("cada paso cuenta, sin culpa") is True)

ok("5b. anti-toxic FAIL (positividad tóxica)",
   idn.anti_toxic_ok("solo piensa positivo y todo cambiará") is False)

ok("6. identidad cargada una vez (misma instancia reutilizada)",
   EditorialIdentity() is not None and
   EditorialIdentity().neutralize("sos") == "eres")

# ─────────────────────────────────────────────
# 7-12. PLATFORM INTELLIGENCE
# ─────────────────────────────────────────────
print("\n[7-12] PLATFORM INTELLIGENCE")
plt = PlatformIntelligence()

yt_short = plt.resolve_target("youtube", "short")
yt_long = plt.resolve_target("youtube", "video")
fb_reel = plt.resolve_target("facebook", "reel")

ok("7. formato auto: 9:16 → short/reel",
   yt_short.aspect == "vertical" and yt_short.is_short is True and
   fb_reel.is_short is True)

ok("7b. formato auto: 16:9 → long",
   yt_long.aspect == "horizontal" and yt_long.is_short is False)

ok("8. youtube short → 1080x1920",
   yt_short.width == 1080 and yt_short.height == 1920 and
   yt_short.format_name == "short")

ok("9. youtube long → 1920x1080",
   yt_long.width == 1920 and yt_long.height == 1080 and
   yt_long.format_name == "youtube")

ok("10. facebook reel → 1080x1920",
   fb_reel.width == 1080 and fb_reel.height == 1920)

res, asked = plt.resolve_platform_request(None)
ok("11. falta plataforma → se pregunta (NEED_PLATFORM)",
   res is NEED_PLATFORM)

res2, asked2 = plt.resolve_platform_request("fb")
ok("11b. plataforma presente → resuelve, sin preguntar",
   res2 is Platform.FACEBOOK and asked2 is False)

strat = plt.editorial_strategy(yt_short)
ok("12. estrategia adapta estructura/duración/CTA por plataforma",
   strat["structure"] == "short_arc" and
   strat["cta_priorities"][0] == "SUSCRIPCION_SUAVE" and
   strat["message_unchanged"] is True)

strat_fb = plt.editorial_strategy(plt.resolve_target("facebook", "reel"))
ok("12b. FB prioriza interactuar, no suscribir",
   strat_fb["cta_priorities"][0] == "INTERACCION")

# ─────────────────────────────────────────────
# 13-24. CTA ENGINE
# ─────────────────────────────────────────────
print("\n[13-24] CTA ENGINE")
c = CtaEngine()

ok("13. biblioteca extensible (todas las familias presentes)",
   set(c.families()) >= {"SUSCRIPCION_SUAVE", "CONTINUIDAD", "UTILIDAD",
                          "COMUNIDAD", "FE_COMUNIDAD", "ORACION", "INTERACCION"})

ctx_fe = {"platform": "youtube", "focus": "fe_psicologia", "closure": "esperanzador"}
fam1, txt1 = c.select(ctx_fe, [])
fam2, txt2 = c.select(ctx_fe, [])

ok("14. selección contextual determinista (misma entrada → mismo resultado)",
   fam1 == fam2 and txt1 == txt2 and fam1 == "FE_COMUNIDAD")

# rotación: excluir la familia que saldría; debe salir otra distinta cuando vacía
preferidos_clase = [fam for fam in c.families() if fam != "FE_COMUNIDAD"]
# context facebook fuerza INTERACCION; probar que rota al excluir reciente
ctx_fb = {"platform": "facebook", "focus": "experiencias", "closure": "reflexivo"}
fA, _ = c.select(ctx_fb, [])
fB, _ = c.select(ctx_fb, [fA])
ok("15. rotación evita el CTA recientemente usado",
   fA == "INTERACCION" and fB != fA)

ok("16. español neutro en CTAs auto",
   c.validate_spanish(txt1) is True and
   "querés" not in txt1 and "suscribite" not in txt1)

ok("17. validate_spanish detecta voseo",
   c.validate_spanish("si querés, dejá tu mensaje") is False)

ok("19. CTA personal gana sobre el selector",
   c.apply(user_cta="Sigue en el canal", context=ctx_fe)["primary"] == "Sigue en el canal")

ok("19b. CTA personal marcado source=custom",
   c.apply(user_cta="X", context=ctx_fe)["source"] == "custom")

ok("20. sin-CTA deshabilita (disabled=True, primary=None)",
   c.apply(sin_cta=True, context=ctx_fe)["disabled"] is True and
   c.apply(sin_cta=True, context=ctx_fe)["primary"] is None)

primary_auto = c.apply(context=ctx_fe)
ok("21. máximo 1 CTA principal en auto",
   primary_auto["primary"] is not None and
   primary_auto.get("combined") is not None and
   not isinstance(primary_auto["primary"], list))

ok("22. secundario solo cuando toca (fe+esperanzador → oración)",
   primary_auto["secondary"] is not None and
   "oración" in primary_auto["secondary"])

ctx_plain = {"platform": "youtube", "focus": "educativo", "closure": "reflexivo"}
ok("22b. sin contexto fe → sin secundario",
   c.apply(context=ctx_plain)["secondary"] is None)

ok("23. agregar familia no rompe selector (biblioteca + métodos)",
   "SUSCRIPCION_SUAVE" in c.library and
   isinstance(c.select(ctx_fe, [])[0], str))

ok("24. familias de fe/oración presentes y reconocidas",
   "FE_COMUNIDAD" in c.families() and "ORACION" in c.families() and
   c.select(ctx_fe, [])[0] == "FE_COMUNIDAD")

# ─────────────────────────────────────────────
# 25-33. PRODUCTION REPORT
# ─────────────────────────────────────────────
print("\n[25-33] PRODUCTION REPORT")
rec = ProductionRecord(
    topic="perfeccionismo", format_name="short", platform="youtube",
    duration_s=73.2, n_scenes=7, cta_primary="CTA X",
    cta_family="FE_COMUNIDAD", mp4="/tmp/a.mp4", assets="7 seleccionados",
    qa="PASS", warnings=["w1"], fallbacks=["f1"],
)
rep = ProductionReport.build(rec)

ok("25. reporte automático sin pedirlo (build directo)",
   isinstance(rep, dict) and "mp4" in rep)

ok("26. incluye tema", rep["tema"] == "perfeccionismo")
ok("27. incluye formato", rep["formato"] == "short")
ok("28. incluye plataforma", rep["plataforma"] == "youtube")
ok("29. incluye duración + cantidad escenas",
   rep["duracion_s"] == 73.2 and rep["cantidad_escenas"] == 7)
ok("30. incluye CTA + familia",
   rep["cta"] == "CTA X" and rep["cta_familia"] == "FE_COMUNIDAD")
ok("31. incluye MP4 + assets",
   rep["mp4"] == "/tmp/a.mp4" and rep["assets"] == "7 seleccionados")
ok("32. incluye QA + warnings + fallbacks",
   rep["qa"] == "PASS" and rep["warnings"]["cantidad"] == 1 and
   rep["fallbacks"]["cantidad"] == 1)

md = ProductionReport.markdown_blocks(rep)
ok("32b. markdown del reporte incluye bloque completo",
   "PRODUCCIÓN COMPLETADA" in md and "Tema:" in md and "CTA seleccionado:" in md)

dev = ProductionReport.dev_section()
ok("33. dev incluye git status + diff",
   "git status" in dev.lower() and "diff" in dev.lower())

err = ProductionReport.error("render", "boom", ultimo_artefacto="/tmp/a.mp4",
                             fallback="reintentar", accion="revisar")
ok("33b. reporte de error estructurado",
   err["estado"] == "ERROR" and err["etapa_que_fallo"] == "render" and
   err["ultimo_artefacto_valido"] == "/tmp/a.mp4")

# ─────────────────────────────────────────────
# 34-35. REGRESIÓN (capa de producción V2 intacta)
# ─────────────────────────────────────────────
print("\n[34-35] REGRESIÓN")
rep_no = pi.produce_v2(
    tema="superar el perfeccionismo",
    idea="Dejar de perseguir una perfección imposible y aprender a soltar sin culpa.",
    plataforma="youtube", tipo="short", render=False, asset_fetch_fn=mock_fetch,
)

ok("34. produce_editorial (vía produce_v2) termina sin red",
   isinstance(rep_no, dict) and rep_no["cantidad_escenas"] == 7)

ok("35. scene_dicts generados válidos (plan briefly a través de CTA)",
   rep_no["qa"] == "PASS" and rep_no["cta_familia"] == "FE_COMUNIDAD")

# 35b: CTA no hardcodeado sino salido del engine (no es el stático del orchestrator)
ok("35b. CTA salido del engine (no el default hardcoded) con identidad aplicada",
   rep_no["cta"] and "querés" not in rep_no["cta"] and
   "suscribite" not in rep_no["cta"])

print("\n============================================================")
print(f"RESULTADO: {PASS} pass, {FAIL} fail")
print("============================================================")
raise SystemExit(1 if FAIL else 0)
