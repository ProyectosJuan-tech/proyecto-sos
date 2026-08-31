"""topic_lock.py — TOPIC/IDEA LOCK (defensa simple, robusta y explicable).

Garantiza que la idea entregada por el USUARIO sea la fuente de verdad del
contenido. El sistema puede mejorar título, guion, desarrollo psicológico,
dimensión de fe, narrativa e imágenes, pero NO puede sustituir el tema central.

Principio de la defensa (anti-sustitución de tema):
  El plan editorial que se va a renderizar debe contener anclas léxicas del
  tema/idea SOLICITADOS por el usuario. Si el token principal del tema
  solicitado no aparece en el plan (topic + idea + hook + textos de escena),
  es una sustitución silenciosa de tema => se frena la producción con un error.

Es deliberadamente NO semántico: usa solapamiento de tokens-ancla tras
normalizar (minúsculas, sin acentos, sin puntuación). Simple, explicable y
suficiente para el caso real (pasar un guion de "límites"/"paz" cuando la idea
era "el perdón").

La validación es determinista: no hace llamadas a IA, visión ni proveedores.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

_STOPWORDS = {
    "el", "la", "los", "las", "lo", "un", "una", "unos", "unas", "uno",
    "de", "del", "que", "te", "si", "a", "en", "es", "son", "tu", "su",
    "se", "y", "o", "por", "para", "con", "me", "mi", "tus", "sus",
    "mas", "pero", "como", "cuando", "quien", "ya", "no", "ni", "al",
    "hay", "ser", "estar", "hace", "esto", "ese", "esa", "este", "esta",
    "the", "a", "an", "of", "to", "and", "or", "for", "with", "that",
    "it", "is", "are", "do", "does", "not", "your", "you", "have",
}


def normalize(text: str) -> str:
    """Minúsculas, sin acentos, sin puntuación."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


def _tokens(text: str) -> set[str]:
    return {t for t in normalize(text).split() if t and t not in _STOPWORDS}


def anchors(topic: str, idea: str) -> set[str]:
    """Anclas léxicas de la idea solicitada (tema + idea central)."""
    return _tokens(topic) | _tokens(idea)


def plan_pool(plan: Any) -> str:
    """Todo el texto del plan que determina el contenido real a renderizar."""
    parts: list[str] = []
    for attr in ("topic", "central_idea", "hook" if hasattr(plan, "hook") else "promise",
                 "promise", "cta"):
        val = getattr(plan, attr, None)
        if isinstance(val, str) and val:
            parts.append(val)
    scenes = getattr(plan, "scenes", None) or []
    for s in scenes:
        n = getattr(s, "narration", None)
        if isinstance(n, str) and n:
            parts.append(n)
    idea = getattr(plan, "central_idea", None) or ""
    for s in scenes:
        ev = getattr(s, "visual_event", None)
        if isinstance(ev, str) and ev:
            parts.append(ev)
    if idea:
        parts.append(idea)
    return " ".join(parts)


def topic_keyword(topic: str) -> str | None:
    """Token principal del tema solicitado (el más informativo), o None."""
    toks = _tokens(topic)
    if not toks:
        return None
    order = ["perdon", "limite", "paz", "rencor", "culpa", "amor", "soledad",
             "ansiedad", "miedo", "habito", "disciplina", "relacion", "fe",
             "propósito", "gratitud", "perdonar", "perdona"]
    for w in order:
        if w in toks:
            return w
    return min(toks, key=len) if toks else None


def mismatch(
    *,
    requested_topic: str,
    requested_idea: str,
    plan: Any,
) -> str | None:
    """Devuelve la razón del desajuste de tema o None si el plan respeta la idea.

    Regla (robusta y explicable):
      1. El token PRINCIPAL del tema solicitado debe aparecer en el pool del plan.
      2. Al menos UNA ancla (de tema+idea) debe aparecer en el pool del plan.
    Si no se cumple => sustitución silenciosa de tema.
    """
    pool = normalize(plan_pool(plan))
    pool_toks = set(pool.split())

    anchor_set = anchors(requested_topic, requested_idea)
    if not anchor_set:
        return None  # no hay anclas que exigir (tema vacío): no interfiere

    principal = topic_keyword(requested_topic)
    if principal is not None and principal not in pool_toks:
        return (
            f"el tema central solicitado ('{requested_topic}') no aparece en el "
            f"plan editorial (pool: topic+idea+escenas). Posible sustitución "
            f"silenciosa de tema. Solicitado principal='{principal}'."
        )

    present = [a for a in sorted(anchor_set) if a in pool_toks]
    if not present:
        return (
            f"ninguna ancla de la idea solicitada ('{requested_topic}': "
            f"{sorted(anchor_set)}) aparece en el contendido del plan; el plan "
            f"responde a otro tema."
        )
    return None


class TopicLockError(Exception):
    """El plan editorial NO corresponde a la idea solicitada por el usuario."""


def assert_topic_locked(*, requested_topic: str, requested_idea: str, plan: Any) -> None:
    reason = mismatch(
        requested_topic=requested_topic,
        requested_idea=requested_idea,
        plan=plan,
    )
    if reason:
        detail = f"topic_plan='{getattr(plan,'topic',None)}' idea_plan='{getattr(plan,'central_idea',None)}'"
        raise TopicLockError(f"TOPIC LOCK: {reason} [{detail}]")
