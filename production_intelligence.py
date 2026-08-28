"""
V2.2 — PRODUCTION INTELLIGENCE & CHANNEL IDENTITY.

Capa ÚNICA de producción que recibe una instrucción sencilla y toma
automáticamente las decisiones editoriales recurrentes. NO es un pipeline
nuevo ni un renderer: integra y orquesta las capas V2 existentes
(produce_editorial + render_emission) sobre cuatro bloques:

  1. IDENTIDAD EDITORIAL GLOBAL   — reglas permanentes (config central, no se
                                    repiten en cada prompt).
  2. PLATFORM INTELLIGENCE        — plataforma destino → formato/canvas/estrategia.
  3. CTA ENGINE                   — biblioteca contextual de CTAs + rotación.
  4. PRODUCTION REPORT            — informe automático + reporte de errores.

Config central: assets/brand/brand.config.json (secciones language/tone/
emotional/forbidden_tone/messaging/cta).

Reutiliza short_director.Platform; no duplica responsabilidades. Determinista
(sin red para identidad/plataforma/CTA/reporte; el render real usa la cadena V2).
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from short_director import Platform


# ─────────────────────────────────────────────
# Config central (identidad)
# ─────────────────────────────────────────────

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "assets" / "brand" / "brand.config.json"
_EXAMPLE_CONFIG_PATH = Path(__file__).parent / "assets" / "brand" / "brand.config.example.json"


def load_brand_config(path=None) -> dict:
    """Carga la config local; si no existe (repo sin config), cae al example
    para que el sistema siga funcionando en una instalación nueva."""
    candidates = []
    if path:
        candidates.append(Path(path))
    candidates.append(_DEFAULT_CONFIG_PATH)
    candidates.append(_EXAMPLE_CONFIG_PATH)
    for p in candidates:
        try:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            continue
    return {}


def _identity(cfg: dict) -> dict:
    return {
        "language": cfg.get("language", {}),
        "tone": cfg.get("tone", {}),
        "emotional_priority": cfg.get("emotional_priority", []),
        "emotional_avoid": cfg.get("emotional_avoid", []),
        "forbidden_tone": cfg.get("forbidden_tone", []),
        "messaging": cfg.get("messaging", {}),
        "cta": cfg.get("cta", {}),
    }


# ─────────────────────────────────────────────
# 1. IDENTIDAD EDITORIAL GLOBAL
# ─────────────────────────────────────────────

_VOSEO_PAIRS = [
    ("quierés", "quieres"), ("podés", "puedes"),
    ("suscribite", "suscríbete"), ("seguí", "sigue"),
    ("dejá", "deja"), ("sentís", "sientes"), ("tenés", "tienes"),
    ("sos", "eres"), ("estás", "estás"), ("fijate", "fíjate"),
    ("hacé", "haz"), ("decime", "dime"), ("contame", "cuéntame"),
    ("mirá", "mira"), ("esperá", "espera"), ("pensá", "piensa"),
    ("poné", "pon"), ("vení", "ven"), ("escuchame", "escúchame"),
    ("entendés", "entiendes"), ("sabés", "sabes"), ("querías", "querías"),
    ("necesitás", "necesitas"), ("buscás", "buscas"), ("amás", "amas"),
    ("hablás", "hablas"), ("vivís", "vives"), ("disfrutás", "disfrutas"),
]


class EditorialIdentity:
    """Reglas editoriales permanentes del canal (cargadas UNA vez)."""

    def __init__(self, config=None):
        cfg = config or load_brand_config()
        idn = _identity(cfg)
        self.language = idn["language"] or {}
        self.tone = idn["tone"] or {}
        self.emotional_priority = idn["emotional_priority"] or [
            "comprension", "reflexion", "esperanza", "accion_posible"]
        self.emotional_avoid = idn["emotional_avoid"] or ["miedo", "culpa", "presion"]
        self.forbidden_tone = idn["forbidden_tone"] or []
        self.messaging = idn["messaging"] or {}
        self._voseo_pairs = list(_VOSEO_PAIRS)
        cfg_evitar = self.language.get("evitar", [])
        cfg_preferir = self.language.get("preferir", [])
        if cfg_evitar and cfg_preferir:
            # config central primero (puede extender o corregir); defaults de respaldo
            cfg_pairs = [p for p in zip(cfg_evitar, cfg_preferir)
                         if p[0] and p[1] and p[0] != p[1]]
            known = {a for a, _ in cfg_pairs}
            self._voseo_pairs = cfg_pairs + [p for p in _VOSEO_PAIRS if p[0] not in known]

    # -- español neutro (default) --
    def neutralize(self, text: str) -> str:
        """Normaliza el español DE CONTENIDO AUTOGENERADO a neutro latino
        (tuteo). NO corrige el texto que el usuario provea explícitamente:
        solo se invoca en la capa de producción sobre CTA/scaffold."""
        if not text:
            return text
        out = text
        for vos, tu in self._voseo_pairs:
            out = out.replace(vos, tu)
        out = out.replace(" ¿viste?", " ¿verdad?").replace("viste que", "¿sabes que")
        return out

    def is_neutral(self, text: str) -> bool:
        """True si el texto no usa marcas de voseo por defecto."""
        low = text.lower()
        for vos, _ in self._voseo_pairs:
            if vos in low:
                return False
        return True

    # -- anti-gurú / anti-coach (reglas) --
    def anti_guru_ok(self, text: str) -> bool:
        low = (text or "").lower()
        for w in ["hazte rico", "multiplica tu", "éxito garantizado", "solo los fuertes",
                  "los demás no", "tú también puedes en 3 días", "gana 5000", "nunca más"]:
            if w in low:
                return False
        return True

    def anti_sermon_ok(self, text: str) -> bool:
        low = (text or "").lower()
        for w in ["debes arrepentirte", "estás pecando", "Dios te castiga", "si no crees",
                  "tienes que obedecer", "le debes a Dios", "vive como yo te digo"]:
            if w in low:
                return False
        return True

    def anti_toxic_ok(self, text: str) -> bool:
        low = (text or "").lower()
        for w in ["solo piensa positivo y todo cambiará", "el dinero es la raíz de todo",
                  "nunca más tendrás miedo", "el secreto está en creer sin dudar",
                  "todo es tu culpa"]:
            if w in low:
                return False
        return True

    def guard(self, text: str, foundation: str = "any") -> dict:
        """Guarda anti-(gurú/sermón/toxic) + spanish neutral. Devuelve PASS/FAIL."""
        checks = {
            "spanish_neutral": self.is_neutral(text),
            "anti_guru": self.anti_guru_ok(text),
            "anti_sermon": self.anti_sermon_ok(text),
            "anti_toxic": self.anti_toxic_ok(text),
        }
        return {"pass": all(checks.values()), "checks": checks}

    @property
    def identity_summary(self) -> dict:
        return {
            "language": self.language.get("default", "es_neutro_lat"),
            "voseo_default": self.language.get("voseo_default", False),
            "tone": {k: v for k, v in self.tone.items() if isinstance(v, bool) and v},
            "emotional_priority": self.emotional_priority,
            "emotional_avoid": self.emotional_avoid,
        }


# ─────────────────────────────────────────────
# 2. PLATFORM INTELLIGENCE
# ─────────────────────────────────────────────

NEED_PLATFORM = "__need_platform__"


@dataclass
class ResolvedTarget:
    platform: Platform
    kind: str            # "short" | "long"
    format_name: str     # "short" | "youtube"
    width: int
    height: int
    is_short: bool = False
    aspect: str = "vertical"


def normalize_platform(value) -> Platform:
    """'youtube'/'yt' → YOUTUBE; 'facebook'/'fb' → FACEBOOK; 'ambas'/'both' → BOTH."""
    if isinstance(value, Platform):
        return value
    s = (value or "").lower()
    if s in ("fb", "facebook", "reel", "reels"):
        return Platform.FACEBOOK
    if s in ("yt", "youtube", "short", "shorts", "video", "video youtube"):
        return Platform.YOUTUBE
    if s in ("both", "ambas", "ambos", "todas", "todos"):
        return Platform.BOTH
    return None


class PlatformIntelligence:
    """Resuelve plataforma + formato/canvas sin obligar a repetir el formato."""

    @staticmethod
    def platform_prompt() -> str:
        return "¿Para qué plataforma? YouTube, Facebook o ambas."

    # -- resolución de solicitud de plataforma --
    def resolve_platform_request(self, platform=None, default=None):
        """Devuelve (platform, asked) o (NEED_PLATFORM, False) si no se pudo
        resolver y no hay default. 'asked'=True si se tuvo que preguntar."""
        if platform:
            p = normalize_platform(platform)
            return p, False
        if default is not None:
            p = normalize_platform(default)
            return p, True
        return NEED_PLATFORM, True

    # -- formato automático (canvas) --
    def resolve_target(self, platform, content_type: str = "short") -> ResolvedTarget:
        """content_type: 'short'/'reel' (9:16) o 'video'/'long' (16:9)."""
        p = normalize_platform(platform) or Platform.YOUTUBE
        if content_type in ("long", "video", "youtube", "16:9", "16x9"):
            return ResolvedTarget(
                platform=p, kind="long", format_name="youtube",
                width=1920, height=1080, is_short=False, aspect="horizontal")
        return ResolvedTarget(
            platform=p, kind="short", format_name="short",
            width=1080, height=1920, is_short=True, aspect="vertical")

    # -- estrategia editorial por plataforma (no cambia el mensaje central) --
    def editorial_strategy(self, target: ResolvedTarget) -> dict:
        s = {
            "structure": "short_arc" if target.is_short else "long_arc",
            "duration_note": "60-90s" if target.is_short else "8+ min",
            "hook": "gancho en 3s, payoff antes de la mitad",
            "cta_priorities": self._cta_priorities(target.platform),
            "message_unchanged": True,
        }
        return s

    @staticmethod
    def _cta_priorities(platform: Platform) -> list[str]:
        if platform == Platform.FACEBOOK:
            return ["INTERACCION", "COMUNIDAD", "MENSAJE"]
        if platform == Platform.BOTH:
            return ["COMUNIDAD", "MENSAJE", "SUSCRIPCION_SUAVE"]
        return ["SUSCRIPCION_SUAVE", "CONTINUIDAD", "COMUNIDAD", "ORACION"]


# ─────────────────────────────────────────────
# 3. CTA ENGINE
# ─────────────────────────────────────────────

class CtaEngine:
    """Selección contextual + biblioteca extensible de CTAs.

    La biblioteca vive en brand.config.json (cta.cta_text). Agregar una familia
    o variante NO requiere tocar el selector.
    """

    _FAMILY_ORDER = [
        "SUSCRIPCION_SUAVE", "CONTINUIDAD", "AYUDA", "UTILIDAD",
        "MENSAJE", "COMUNIDAD", "FE_COMUNIDAD", "ORACION", "INTERACCION",
    ]

    def __init__(self, config=None):
        cfg = config if config is not None else load_brand_config()
        cta = cfg.get("cta", {})
        self.library = cta.get("cta_text", {}) or {}
        self.max_principales = int(cta.get("max_principales", 1))

    # -- extensibilidad: variantes accesibles --
    def families(self) -> list[str]:
        return [k for k in self._FAMILY_ORDER if self.library.get(k)]

    def family_texts(self, family: str) -> list[str]:
        return self.library.get(family, [])

    # -- español neutro --
    @staticmethod
    def validate_spanish(text: str) -> bool:
        idn = EditorialIdentity()
        return idn.is_neutral(text)

    # -- selección contextual (determinista, con rotación) --
    def _family_score(self, family: str, context: dict) -> int:
        platform = normalize_platform(context.get("platform")) or Platform.YOUTUBE
        focus = (context.get("focus") or "").lower()
        closure = (context.get("closure") or "").lower()
        s = 0
        # plataforma
        if platform == Platform.FACEBOOK:
            if family in ("INTERACCION", "COMUNIDAD", "MENSAJE"):
                s += 2
            elif family in ("SUSCRIPCION_SUAVE", "UTILIDAD", "FE_COMUNIDAD", "ORACION"):
                s += 1
        else:  # youtube / both
            if family in ("SUSCRIPCION_SUAVE", "CONTINUIDAD", "AYUDA", "UTILIDAD",
                          "MENSAJE", "COMUNIDAD", "FE_COMUNIDAD"):
                s += 2
            elif family in ("ORACION", "INTERACCION"):
                s += 1
        # enfoque
        if "fe" in focus:
            if family in ("FE_COMUNIDAD", "ORACION"):
                s += 3
        if focus in ("psicologia", "educativo", "habitos"):
            if family in ("UTILIDAD", "SUSCRIPCION_SUAVE", "MENSAJE", "CONTINUIDAD"):
                s += 2
        if focus == "emocional":
            if family in ("MENSAJE", "COMUNIDAD", "SUSCRIPCION_SUAVE"):
                s += 2
        if focus in ("experiencias", "compartir"):
            if family == "INTERACCION":
                s += 2
        # cierre
        if "esperanza" in closure or "alivio" in closure:
            if family in ("FE_COMUNIDAD", "ORACION", "COMUNIDAD", "UTILIDAD"):
                s += 1
        if "reflexivo" in closure:
            if family in ("SUSCRIPCION_SUAVE", "MENSAJE", "UTILIDAD"):
                s += 1
        return s

    def _pick(self, ranked, recent: list[str]) -> str:
        if not ranked:
            return None
        # preferir el de mayor score NO recién usado; si todos usados, el top.
        for _, fam in ranked:
            if fam not in recent:
                return fam
        return ranked[0][1]

    def select(self, context: dict, recent: list[str] | None = None) -> tuple[str | None, str | None]:
        """Devuelve (family, text) o (None, None) si sin-CTA."""
        recent = list(recent or [])
        ranked = sorted([(self._family_score(f, context), f) for f in self.families()],
                        key=lambda x: (-x[0], self._FAMILY_ORDER.index(x[1])))
        family = self._pick(ranked, recent)
        if family is None:
            return None, None
        return family, self.library[family][0]

    # -- CTA secundario (solo cuando tiene sentido narrativo) --
    def secondary(self, context: dict) -> str | None:
        focus = (context.get("focus") or "").lower()
        closure = (context.get("closure") or "").lower()
        if "fe" in focus:
            # fe + esperanzador → oración como secundario natural
            return self.library.get("ORACION", [None])[0]
        if focus in ("experiencias", "compartir"):
            return self.library.get("INTERACCION", [None])[0]
        return None

    # -- control del usuario --
    def apply(self, *, user_cta=None, sin_cta=False, context=None, recent=None) -> dict:
        """Devuelve {'family','primary','secondary','source','disabled'}."""
        if sin_cta:
            return {"family": None, "primary": None, "secondary": None,
                    "source": "sin_cta", "disabled": True}
        if user_cta:
            return {"family": "CUSTOM", "primary": user_cta, "secondary": None,
                    "source": "custom", "disabled": False}
        family, primary = self.select(context or {}, recent)
        if family is None:
            return {"family": None, "primary": None, "secondary": None,
                    "source": "auto", "disabled": True}
        sec = self.secondary(context or {})
        cta = {
            "family": family, "primary": primary, "secondary": sec,
            "source": "auto", "disabled": False,
        }
        # combinar principal + secundario en un solo texto p/ el CALLOUT
        if sec:
            cta["combined"] = f"{primary} Además, {_lcf(sec)}"
        else:
            cta["combined"] = primary
        return cta


def _lcf(s: str) -> str:
    if not s:
        return s
    return s[0].lower() + s[1:]


# ─────────────────────────────────────────────
# 4. PRODUCTION REPORT
# ─────────────────────────────────────────────

@dataclass
class ProductionRecord:
    topic: str = ""
    format_name: str = ""
    platform: str = ""
    duration_s: float = 0.0
    n_scenes: int = 0
    cta_primary: str = ""
    cta_family: str = ""
    mp4: str = ""
    assets: str = ""
    qa: str = "PASS"
    warnings: list = field(default_factory=list)
    fallbacks: list = field(default_factory=list)


class ProductionReport:
    """Informe automático de producción (sin que el usuario lo pida)."""

    @staticmethod
    def build(record: ProductionRecord) -> dict:
        return {
            "tema": record.topic,
            "formato": record.format_name,
            "plataforma": record.platform,
            "duracion_s": round(record.duration_s, 1),
            "cantidad_escenas": record.n_scenes,
            "cta": record.cta_primary,
            "cta_familia": record.cta_family,
            "mp4": record.mp4,
            "assets": record.assets,
            "qa": record.qa,
            "warnings": {"cantidad": len(record.warnings), "detalle": record.warnings},
            "fallbacks": {"cantidad": len(record.fallbacks), "detalle": record.fallbacks},
        }

    @staticmethod
    def markdown_blocks(r: dict) -> str:
        w = r["warnings"]
        f = r["fallbacks"]
        out = [
            "## PRODUCCIÓN COMPLETADA", "",
            f"Tema: {r['tema']}",
            f"Formato: {r['formato']}",
            f"Plataforma: {r['plataforma']}",
            f"Duración: {r['duracion_s']}s",
            f"Cantidad de escenas: {r['cantidad_escenas']}",
            f"CTA seleccionado: {r['cta']}",
            "",
            "MP4:",
            f"ruta: {r['mp4'] or '(no renderizado)'}",
            "",
            "Assets:",
            f"resumen: {r['assets'] or '-'}",
            "",
            f"QA: {r['qa']}",
            "",
            f"Warnings: {w['cantidad']}",
        ]
        out += [f"  - {x}" for x in w["detalle"]] or ["  (ninguno)"]
        out += ["", f"Fallbacks: {f['cantidad']}"]
        out += [f"  - {x}" for x in f["detalle"]] or ["  (ninguno)"]
        return "\n".join(out)

    @staticmethod
    def dev_section() -> str:
        try:
            status = subprocess.run(["git", "status", "--short"],
                                    capture_output=True, text=True,
                                    cwd=_DEFAULT_CONFIG_PATH.parent).stdout.strip()
            stat = subprocess.run(["git", "diff", "--stat"],
                                  capture_output=True, text=True,
                                  cwd=_DEFAULT_CONFIG_PATH.parent).stdout.strip()
        except Exception:
            status, stat = "(no git)", ""
        return ("git status --short:\n" + (status or "(limpio)")
                + "\n\ngit diff --stat:\n" + (stat or "(sin cambios)"))

    @staticmethod
    def error(etapa: str, causa: str, ultimo_artefacto: str = "",
              fallback: str = "", accion: str = "") -> dict:
        return {
            "estado": "ERROR",
            "etapa_que_fallo": etapa,
            "causa_conocida": causa,
            "ultimo_artefacto_valido": ultimo_artefacto or "(ninguno)",
            "fallback_disponible": fallback or "(ninguno)",
            "que_puede_hacer": accion or "Revisar la causa y reintentar.",
        }


# ─────────────────────────────────────────────
# Producción orquestada (experiencia V2.2)
# ─────────────────────────────────────────────

def produce_v2(
    *,
    tema: str,
    idea: str,
    plataforma=None,
    tipo: str = "short",
    cta_usuario=None,
    sin_cta=False,
    narrations=None,
    render: bool = True,
    output_mp4: str = "",
    config=None,
    asset_fetch_fn=None,
    recent_ctas: list[str] | None = None,
) -> dict:
    """Experiencia única de producción V2.2.

    apply identidad → platform intelligence → narrativa/visual → CTA Engine →
    produce_editorial (+ render_emission si render=True) → Production Report.
    """
    identity = EditorialIdentity(config)
    plt = PlatformIntelligence()
    cta_engine = CtaEngine(config)

    target = plt.resolve_target(plataforma, tipo)

    # CTA Engine (aplica identidad neutra al auto)
    context = {
        "platform": target.platform.value,
        "focus": "fe_psicologia" if _is_faith(idea, narrations) else "psicologia",
        "closure": "esperanzador",
    }
    cta_res = cta_engine.apply(user_cta=cta_usuario, sin_cta=sin_cta,
                               context=context, recent=recent_ctas)
    primary = cta_res.get("combined") or cta_res.get("primary")
    primary_neutral = identity.neutralize(primary) if primary else ""

    from editorial_orchestrator import produce_editorial
    em = produce_editorial(
        topic=tema,
        central_idea=idea,
        format_name=target.format_name,
        cta=primary_neutral,
        narrations=narrations,
        asset_fetch_fn=asset_fetch_fn,
    )

    record = ProductionRecord(
        topic=tema,
        format_name=target.format_name,
        platform=target.platform.value,
        duration_s=sum(b.duration for b in em.briefs),
        n_scenes=len(em.briefs),
        cta_primary=primary_neutral,
        cta_family=cta_res.get("family") or "",
        assets=f"{len(em.asset_selections)} seleccionados",
        qa="PASS",
    )

    mp4 = ""
    if render:
        from render_adapter import render_emission, build_work_context
        if not output_mp4:
            out_dir = Path(os.environ.get("V2_OUT", "videos/v2_produccion"))
            out_dir.mkdir(parents=True, exist_ok=True)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in tema)[:40]
            output_mp4 = str(out_dir / f"{safe}_{target.aspect}.mp4")
        try:
            mp4 = render_emission(
                em, output_mp4,
                work_dir=build_work_context(em),
                aspect=target.aspect,
            )
            record.mp4 = mp4
        except Exception as e:
            record.qa = "FAIL"
            record.fallbacks.append(f"render: {e}")
            report = ProductionReport.build(record)
            report["error"] = ProductionReport.error(
                "render", str(e), ultimo_artefacto=output_mp4,
                fallback="regenerar con otra semilla / revisar imágen",
                accion="Verificar red/imágenes y reintentar (los scene_dicts siguen válidos).")
            return report

    record.mp4 = record.mp4 or output_mp4
    return ProductionReport.build(record)


def _is_faith(idea: str, narrations=None) -> bool:
    text = (idea or "") + " " + " ".join((narrations or {}).values())
    low = text.lower()
    return any(w in low for w in ["dios", "fe", "oracion", "gracia", "biblia",
                                  "alma", "creado", "señor", "espiritual", "perdón"])


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Producción V2.2")
    parser.add_argument("--tema", required=True)
    parser.add_argument("--idea", required=True)
    parser.add_argument("--plataforma", default="",
                        help="youtube | facebook | ambas (o yt/fb)")
    parser.add_argument("--tipo", default="short", choices=["short", "video", "long"])
    parser.add_argument("--cta", default="", help="CTA personalizado")
    parser.add_argument("--sin-cta", action="store_true")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--dev", action="store_true", help="incluye git status/diff")
    args = parser.parse_args(argv)

    plt = PlatformIntelligence()
    plat, asked = plt.resolve_platform_request(args.plataforma)
    if plat is NEED_PLATFORM:
        # interacción real: preguntar
        print(plt.platform_prompt())
        resp = input("> ").strip()
        plat = normalize_platform(resp) or Platform.YOUTUBE

    report = produce_v2(
        tema=args.tema, idea=args.idea,
        plataforma=plat.value if plat else None,
        tipo=args.tipo, cta_usuario=args.cta or None, sin_cta=args.sin_cta,
        render=not args.no_render,
    )
    print("\n" + ProductionReport.markdown_blocks(report))
    if args.dev:
        print("\n" + ProductionReport.dev_section())
    if report.get("estado") == "ERROR":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
