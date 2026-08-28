"""
text_layout.py — Motor de composición tipográfica adaptativa.

Calcula layout de texto SIN dibujarlo. Devuelve una descripción
estructurada (TextLayout) con posiciones, tamaños, scores y warnings.

Compatible con:
  - Shorts verticales 1080x1920
  - YouTube horizontal 1920x1080
  - Facebook vertical (preparado)
  - Futuros formatos

NO dibuja texto. NO renderiza video. Solo calcula composición.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont


# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────

FONT_PATH = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_HEAVY_PATH = "/usr/share/fonts/opentype/inter/Inter-Black.otf"

INTER_WORD_GAP = 18  # px — espacio entre palabras (del pipeline existente)
LINE_HEIGHT_FACTOR = 1.55  # factor de line-height (del pipeline)


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class Platform(str, Enum):
    SHORT_VERTICAL = "short_vertical"   # 1080x1920
    YOUTUBE_HORIZONTAL = "youtube_horizontal"  # 1920x1080
    FACEBOOK_VERTICAL = "facebook_vertical"  # 1080x1920 (preparado)


class Position(str, Enum):
    TOP = "top"
    UPPER = "upper"
    CENTER = "center"
    LOWER = "lower"
    BOTTOM = "bottom"
    CUSTOM = "custom"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class NarrativeRole(str, Enum):
    HOOK = "hook"
    PROBLEM = "problem"
    AGITATION = "agitation"
    PSYCHOLOGY = "psychology"
    SOLUTION = "solution"
    BIBLICAL_GROUNDING = "biblical_grounding"
    REALITY = "reality"
    HOPE = "hope"
    CALLOUT = "callout"
    EMPHASIS = "emphasis"
    BRIDGE = "bridge"
    LOOP = "loop"


# ─────────────────────────────────────────────
# Presets por plataforma
# ─────────────────────────────────────────────

PLATFORM_PRESETS: dict[str, dict[str, Any]] = {
    Platform.SHORT_VERTICAL.value: {
        "canvas_width": 1080,
        "canvas_height": 1920,
        "safe_area": {"top": 120, "bottom": 192, "left": 90, "right": 90},
        "preferred_font_size": 76,
        "min_font_size": 56,
        "max_font_size": 120,
        "max_lines": 6,
        "wrap_width": 900,
        "line_height_factor": 1.55,
        "text_position": Position.LOWER,
        "y_center": 0.50,
    },
    Platform.YOUTUBE_HORIZONTAL.value: {
        "canvas_width": 1920,
        "canvas_height": 1080,
        "safe_area": {"top": 60, "bottom": 108, "left": 200, "right": 200},
        "preferred_font_size": 64,
        "min_font_size": 40,
        "max_font_size": 100,
        "max_lines": 5,
        "wrap_width": 1497,
        "line_height_factor": 1.45,
        "text_position": Position.LOWER,
        "y_center": 0.52,
    },
    Platform.FACEBOOK_VERTICAL.value: {
        "canvas_width": 1080,
        "canvas_height": 1920,
        "safe_area": {"top": 120, "bottom": 192, "left": 90, "right": 90},
        "preferred_font_size": 72,
        "min_font_size": 52,
        "max_font_size": 110,
        "max_lines": 6,
        "wrap_width": 900,
        "line_height_factor": 1.55,
        "text_position": Position.LOWER,
        "y_center": 0.50,
    },
}

# Ajustes por narrative_role
ROLE_ADJUSTMENTS: dict[str, dict[str, Any]] = {
    NarrativeRole.HOOK.value: {
        "font_size_bonus": 4,     # un poco más grande
        "line_height_factor": 1.45,  # más compacto = más impacto
        "max_lines": 3,
    },
    NarrativeRole.PSYCHOLOGY.value: {
        "font_size_bonus": -2,
        "line_height_factor": 1.60,  # más aire = más reflexión
        "max_lines": 5,
    },
    NarrativeRole.CALLOUT.value: {
        "font_size_bonus": 0,
        "line_height_factor": 1.40,  # CTA: lectura rápida
        "max_lines": 3,
    },
    NarrativeRole.EMPHASIS.value: {
        "font_size_bonus": 8,
        "line_height_factor": 1.40,
        "max_lines": 2,
    },
    NarrativeRole.HOPE.value: {
        "font_size_bonus": 0,
        "line_height_factor": 1.55,
        "max_lines": 4,
    },
}


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────

@dataclass
class TextLayoutRequest:
    """Solicitud de composición tipográfica."""
    text: str = ""
    canvas_width: int = 1080
    canvas_height: int = 1920
    safe_area: dict[str, int] = field(default_factory=lambda: {
        "top": 120, "bottom": 192, "left": 90, "right": 90
    })
    font_path: str = FONT_PATH
    preferred_font_size: int = 76
    min_font_size: int = 56
    max_font_size: int = 120
    max_width: int = 900
    preferred_position: Position = Position.LOWER
    alignment: Alignment = Alignment.CENTER
    narrative_role: NarrativeRole | None = None
    emphasis: list[str] = field(default_factory=list)
    duration: float = 0.0
    platform: Platform = Platform.SHORT_VERTICAL
    line_height_factor: float = LINE_HEIGHT_FACTOR
    max_lines: int = 6


@dataclass
class TextLine:
    """Una línea de texto compuesta."""
    text: str = ""
    words: list[str] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    font_size: int = 76


@dataclass
class TextLayout:
    """Resultado de la composición tipográfica."""
    lines: list[TextLine] = field(default_factory=list)
    font_size: int = 76
    font_path: str = FONT_PATH
    line_spacing: float = 0.0
    total_width: float = 0.0
    total_height: float = 0.0
    x: float = 0.0
    y: float = 0.0
    alignment: Alignment = Alignment.CENTER
    overflow: bool = False
    overflow_x: bool = False
    overflow_y: bool = False
    confidence: float = 0.0
    score: float = 0.0
    adjustments: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    split_required: bool = False
    split_candidates: list[str] = field(default_factory=list)
    status: str = "ok"  # ok | needs_split | overflow | no_solution

    def to_dict(self) -> dict[str, Any]:
        """Serializa a dict plano."""
        d = {
            "font_size": self.font_size,
            "total_width": self.total_width,
            "total_height": self.total_height,
            "x": self.x,
            "y": self.y,
            "alignment": self.alignment.value,
            "overflow": self.overflow,
            "overflow_x": self.overflow_x,
            "overflow_y": self.overflow_y,
            "confidence": self.confidence,
            "score": self.score,
            "status": self.status,
            "split_required": self.split_required,
            "line_count": len(self.lines),
            "lines": [
                {"text": l.text, "x": l.x, "y": l.y,
                 "width": l.width, "height": l.height, "font_size": l.font_size}
                for l in self.lines
            ],
            "adjustments": self.adjustments,
            "warnings": self.warnings,
            "errors": self.errors,
            "split_candidates": self.split_candidates,
        }
        return d


# ─────────────────────────────────────────────
# Medición de texto
# ─────────────────────────────────────────────

_scratch_draw: ImageDraw.ImageDraw | None = None
_scratch_img: Image.Image | None = None


def _get_draw() -> ImageDraw.ImageDraw:
    """Devuelve un ImageDraw scratch para medición (reutilizable)."""
    global _scratch_draw, _scratch_img
    if _scratch_draw is None:
        _scratch_img = Image.new("RGB", (1, 1))
        _scratch_draw = ImageDraw.Draw(_scratch_img)
    return _scratch_draw


def _get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Carga una fuente TrueType."""
    return ImageFont.truetype(path, size)


def _measure_word(word: str, font: ImageFont.FreeTypeFont) -> float:
    """Mide el ancho de una palabra en px."""
    return _get_draw().textlength(word, font=font)


def _measure_line(words: list[str], font: ImageFont.FreeTypeFont) -> float:
    """Mide el ancho total de una línea de palabras con gaps."""
    if not words:
        return 0.0
    total = sum(_measure_word(w, font) for w in words)
    total += INTER_WORD_GAP * (len(words) - 1)
    return total


def _get_line_height(font: ImageFont.FreeTypeFont, factor: float) -> float:
    """Obtiene la altura de línea (ascent + descent) escalada por factor."""
    ascent, descent = font.getmetrics()
    return (ascent + descent) * factor


# ─────────────────────────────────────────────
# Wrapping inteligente
# ─────────────────────────────────────────────

# Puntuación que sugiere punto de corte
_CLAUSE_BREAKS = {",", ";", ":", "—", "–"}
_SENTENCE_BREAKS = {".", "!", "?", "¡", "¿"}

# Conectores que no deberían quedar solos al inicio de línea
_WEAK_STARTERS = {"de", "del", "la", "el", "los", "las", "un", "una",
                  "que", "y", "o", "pero", "por", "para", "con", "sin",
                  "a", "al", "en", "se", "te", "me", "le", "lo",
                  "the", "a", "an", "of", "to", "in", "for", "and",
                  "or", "but", "with", "on", "at", "by"}


def wrap_intelligent(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: float,
    max_lines: int = 6,
) -> tuple[list[str], list[str]]:
    """
    Wrapping inteligente que busca balance visual y respeta puntuación.

    Returns:
        (lines, warnings) — lista de líneas y advertencias
    """
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text.strip())
    words = text.split()

    if not words:
        return [], []

    warnings: list[str] = []

    # Medir todas las palabras
    word_widths = [_measure_word(w, font) for w in words]

    # Primera pasada: wrapping greedy con puntos de corte suaves
    lines = _greedy_wrap(words, word_widths, max_width)

    # Segunda pasada: intentar mejorar el balance
    lines = _balance_lines(lines, words, word_widths, max_width)

    # Verificar líneas huérfanas (1 palabra muy corta al final)
    if len(lines) > 1:
        last_words = lines[-1]
        if len(last_words) == 1:
            last_w = last_words[0]
            last_w_lower = last_w.lower().rstrip(".,;:!?")
            if last_w_lower in _WEAK_STARTERS or len(last_w) <= 3:
                # Intentar mover la última palabra a la línea anterior
                if len(lines) >= 2:
                    prev = lines[-2]
                    test_line = prev + [last_w]
                    test_width = _measure_line(test_line, font)
                    if test_width <= max_width:
                        lines[-2] = test_line
                        lines.pop()

    # Validar número de líneas
    if len(lines) > max_lines:
        warnings.append(
            f"demasiadas líneas ({len(lines)} > {max_lines}) — considerar dividir"
        )

    line_texts = [" ".join(l) for l in lines]
    return line_texts, warnings


def _greedy_wrap(
    words: list[str],
    word_widths: list[float],
    max_width: float,
) -> list[list[str]]:
    """Wrapping greedy: agrega palabra a línea actual, flush si excede."""
    lines: list[list[str]] = []
    current: list[str] = []
    current_width = 0.0

    for i, (word, ww) in enumerate(zip(words, word_widths)):
        if not current:
            current.append(word)
            current_width = ww
            continue

        test_width = current_width + INTER_WORD_GAP + ww
        if test_width > max_width:
            lines.append(current)
            current = [word]
            current_width = ww
        else:
            current.append(word)
            current_width = test_width

    if current:
        lines.append(current)

    return lines


def _balance_lines(
    lines: list[list[str]],
    all_words: list[str],
    word_widths: list[float],
    max_width: float,
) -> list[list[str]]:
    """
    Intenta mejorar el balance entre líneas.

    Objetivos:
    - Evitar última línea excesivamente corta (< 30% del ancho promedio)
    - Evitar primera línea enorme y segunda mínima
    - Mantener consistencia visual
    """
    if len(lines) < 2:
        return lines

    # Calcular anchos de línea
    line_widths = [_measure_line(l, ImageFont.truetype(FONT_PATH, 76))
                   for l in lines]

    avg_width = sum(line_widths) / len(line_widths)

    # Si la última línea es muy corta, intentar mover una palabra de la penúltima
    if len(lines) >= 2:
        last_width = line_widths[-1]
        if last_width < avg_width * 0.35 and len(lines[-1]) == 1:
            # última línea tiene 1 palabra muy corta
            prev = lines[-2]
            if len(prev) >= 2:
                # Mover la última palabra de la penúltima a la última
                moved_word = prev[-1]
                test_prev = prev[:-1]
                test_last = [moved_word] + lines[-1]
                test_prev_w = _measure_line(test_prev, ImageFont.truetype(FONT_PATH, 76))
                test_last_w = _measure_line(test_last, ImageFont.truetype(FONT_PATH, 76))
                if test_prev_w <= max_width and test_last_w <= max_width:
                    # Verificar que el balance mejoró
                    old_diff = abs(line_widths[-2] - avg_width) + abs(last_width - avg_width)
                    new_diff = abs(test_prev_w - avg_width) + abs(test_last_w - avg_width)
                    if new_diff < old_diff:
                        lines[-2] = test_prev
                        lines[-1] = test_last
                        return lines

    return lines


# ─────────────────────────────────────────────
# Splitting
# ─────────────────────────────────────────────

def find_split_points(text: str) -> list[str]:
    """
    Encuentra puntos naturales de división para textos largos.

    Devuelve candidatos de texto dividido, ordenados de mejor a peor.
    """
    candidates: list[str] = []

    # Buscar por puntuación fuerte (oraciones)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 1:
        # Dividir por la mitad de las oraciones
        mid = len(sentences) // 2
        part1 = " ".join(sentences[:mid])
        part2 = " ".join(sentences[mid:])
        candidates.append(f"{part1}\n{part2}")

    # Buscar por comas/punto y coma (cláusulas)
    clauses = re.split(r'(?<=[,;])\s+', text)
    if len(clauses) > 2:
        mid = len(clauses) // 2
        part1 = " ".join(clauses[:mid])
        part2 = " ".join(clauses[mid:])
        candidates.append(f"{part1}\n{part2}")

    # Buscar por conectores largos
    connectors = [" pero ", " y ", " o ", " que ", " porque ", " cuando ",
                  " aunque ", " sin ", " con ", " para "]
    for conn in connectors:
        idx = text.find(conn)
        if idx > 0 and idx < len(text) - 1:
            part1 = text[:idx + len(conn) // 2]
            part2 = text[idx + len(conn) // 2 + 1:]
            candidate = f"{part1.strip()}\n{part2.strip()}"
            if candidate not in candidates:
                candidates.append(candidate)

    return candidates[:5]


# ─────────────────────────────────────────────
# Scoring de composición
# ─────────────────────────────────────────────

def _score_layout(
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    canvas_width: int,
    canvas_height: int,
    safe_area: dict[str, int],
    line_height_factor: float,
    max_lines: int,
    alignment: Alignment,
) -> tuple[float, float, float, bool, bool, list[str]]:
    """
    Evalúa la composición del layout.

    Returns:
        (score, overflow_x, overflow_y, has_overflow, warnings)
    """
    if not lines:
        return 0.0, False, False, False, ["sin líneas"]

    score = 60.0  # base
    warnings: list[str] = []
    overflow_x = False
    overflow_y = False

    usable_width = canvas_width - safe_area.get("left", 90) - safe_area.get("right", 90)
    usable_height = canvas_height - safe_area.get("top", 120) - safe_area.get("bottom", 192)

    # Medir líneas
    line_widths = [_measure_line(l.split(), font) for l in lines]
    ascent, descent = font.getmetrics()
    lh = (ascent + descent) * line_height_factor

    total_height = lh * len(lines)
    max_line_w = max(line_widths) if line_widths else 0

    # ── Overflow checks ──
    if max_line_w > usable_width:
        overflow_x = True
        score -= 30

    if total_height > usable_height:
        overflow_y = True
        score -= 25

    has_overflow = overflow_x or overflow_y

    # ── Número de líneas ──
    if len(lines) > max_lines:
        score -= 10
        warnings.append(f"{len(lines)} líneas > máximo {max_lines}")
    elif len(lines) <= 2:
        score += 5  # bonus por composición simple
    elif len(lines) <= 4:
        score += 3

    # ── Balance de líneas ──
    if len(line_widths) >= 2:
        avg_w = sum(line_widths) / len(line_widths)
        if avg_w > 0:
            # Coeficiente de variación
            variance = sum((w - avg_w) ** 2 for w in line_widths) / len(line_widths)
            cv = (variance ** 0.5) / avg_w if avg_w > 0 else 0

            if cv < 0.15:
                score += 10  # muy equilibrado
            elif cv < 0.25:
                score += 5   # aceptable
            elif cv > 0.40:
                score -= 5   # desequilibrado
                warnings.append("líneas desequilibradas")

    # ── Última línea ──
    if line_widths:
        last_w = line_widths[-1]
        if len(lines) >= 2:
            avg_w = sum(line_widths) / len(line_widths)
            if avg_w > 0:
                ratio = last_w / avg_w
                if ratio < 0.25:
                    score -= 8
                    warnings.append("última línea excesivamente corta (huérfana)")
                elif ratio < 0.40:
                    score -= 3
                elif ratio > 0.85:
                    score += 2  # buena utilización

    # ── Utilización del espacio ──
    if usable_width > 0 and max_line_w > 0:
        utilization = max_line_w / usable_width
        if 0.60 <= utilization <= 0.90:
            score += 5  # buena utilización
        elif utilization < 0.40:
            score -= 3
            warnings.append("baja utilización del ancho disponible")

    # ── Block height ──
    if usable_height > 0 and total_height > 0:
        block_ratio = total_height / usable_height
        if block_ratio > 0.60:
            score -= 3
            warnings.append("bloque de texto excesivamente alto")

    # ── Padding from safe zones ──
    # (el layout final se ajusta, pero score penaliza si está muy pegado)
    if total_height > usable_height * 0.80:
        score -= 2

    # Clamp
    score = max(0.0, min(100.0, score))

    return score, overflow_x, overflow_y, has_overflow, warnings


# ─────────────────────────────────────────────
# Posicionamiento
# ─────────────────────────────────────────────

def _compute_position(
    total_height: float,
    canvas_height: int,
    safe_area: dict[str, int],
    position: Position,
    y_center: float,
) -> float:
    """Calcula la posición Y inicial del bloque de texto."""
    top = safe_area.get("top", 120)
    bottom = safe_area.get("bottom", 192)
    usable = canvas_height - top - bottom

    if position == Position.TOP:
        return float(top)
    elif position == Position.UPPER:
        return float(top + usable * 0.15)
    elif position == Position.CENTER:
        return float(top + (usable - total_height) / 2)
    elif position == Position.LOWER:
        # Centrar alrededor de y_center (del pipeline existente)
        y0 = canvas_height * y_center - total_height / 2
        return max(float(top), min(y0, canvas_height - bottom - total_height))
    elif position == Position.BOTTOM:
        return float(canvas_height - bottom - total_height)
    else:
        # custom: center by default
        y0 = canvas_height * y_center - total_height / 2
        return max(float(top), min(y0, canvas_height - bottom - total_height))


def _compute_x(
    line_width: float,
    canvas_width: int,
    safe_area: dict[str, int],
    alignment: Alignment,
) -> float:
    """Calcula la posición X de una línea."""
    left = safe_area.get("left", 90)
    right = safe_area.get("right", 90)
    usable = canvas_width - left - right

    if alignment == Alignment.LEFT:
        return float(left)
    elif alignment == Alignment.RIGHT:
        return float(canvas_width - right - line_width)
    else:  # center
        return float(left + (usable - line_width) / 2)


# ─────────────────────────────────────────────
# Función principal
# ─────────────────────────────────────────────

def compute_layout(request: TextLayoutRequest) -> TextLayout:
    """
    Calcula el layout óptimo para un texto dado.

    Itera sobre múltiples tamaños de fuente para encontrar
    la mejor composición. Devuelve TextLayout con score y warnings.
    """
    result = TextLayout()
    text = request.text.strip()

    if not text:
        result.errors.append("texto vacío")
        result.status = "no_solution"
        return result

    # Aplicar ajustes por narrative_role
    pref_size = request.preferred_font_size
    min_size = request.min_font_size
    lh_factor = request.line_height_factor
    max_lines = request.max_lines

    if request.narrative_role:
        adj = ROLE_ADJUSTMENTS.get(request.narrative_role.value, {})
        pref_size += adj.get("font_size_bonus", 0)
        lh_factor = adj.get("line_height_factor", lh_factor)
        max_lines = adj.get("max_lines", max_lines)

    # Verificar si necesita split — más de max_lines en tamaño preferido
    test_font = _get_font(request.font_path, pref_size)
    test_lines, _ = wrap_intelligent(text, test_font, request.max_width, 99)
    if len(test_lines) > max_lines + 2:
        # Texto muy largo — ofrecer candidatos de split
        result.split_required = True
        result.split_candidates = find_split_points(text)
        if not result.split_candidates:
            result.split_candidates = [text]
        result.status = "needs_split"

    # Generar candidatos iterando tamaños
    candidates: list[tuple[int, TextLayout]] = []

    size = min(pref_size, request.max_font_size)
    while size >= min_size:
        layout = _layout_at_size(text, size, request, lh_factor, max_lines)
        candidates.append((size, layout))

        if not layout.overflow and layout.score >= 75:
            break  # solución buena encontrada

        size -= 4

    if not candidates:
        result.errors.append("no se pudo generar ningún layout")
        result.status = "no_solution"
        return result

    # Seleccionar el mejor candidato por score
    best_size, best_layout = max(candidates, key=lambda c: c[1].score)

    # Si el mejor tiene overflow pero es el único, reportarlo
    if best_layout.overflow:
        best_layout.status = "overflow"

    # Propagar split info si se detectó antes del loop de candidatos
    if result.split_required:
        best_layout.split_required = True
        best_layout.split_candidates = result.split_candidates
        best_layout.adjustments.append(f"needs_split: {len(result.split_candidates)} candidatos")

    return best_layout


def _layout_at_size(
    text: str,
    font_size: int,
    request: TextLayoutRequest,
    line_height_factor: float,
    max_lines: int,
) -> TextLayout:
    """Calcula layout para un tamaño de fuente específico."""
    font = _get_font(request.font_path, font_size)

    # Wrapping
    raw_lines, wrap_warnings = wrap_intelligent(
        text, font, request.max_width, max_lines
    )

    if not raw_lines:
        layout = TextLayout()
        layout.errors.append("no se pudieron generar líneas")
        layout.status = "no_solution"
        return layout

    # Medir
    line_widths = [_measure_line(l.split(), font) for l in raw_lines]
    ascent, descent = font.getmetrics()
    lh = (ascent + descent) * line_height_factor

    total_height = lh * len(raw_lines)
    max_line_w = max(line_widths) if line_widths else 0

    # Posición Y
    y0 = _compute_position(
        total_height, request.canvas_height, request.safe_area,
        request.preferred_position, request.y_center if hasattr(request, 'y_center') else 0.50
    )

    # Construir TextLines con posiciones X
    text_lines: list[TextLine] = []
    y = y0
    for i, line_text in enumerate(raw_lines):
        words = line_text.split()
        lw = line_widths[i]
        x = _compute_x(lw, request.canvas_width, request.safe_area, request.alignment)
        text_lines.append(TextLine(
            text=line_text,
            words=words,
            x=x,
            y=y,
            width=lw,
            height=lh,
            font_size=font_size,
        ))
        y += lh

    # Scoring
    score, ox, oy, has_overflow, scoring_warnings = _score_layout(
        raw_lines, font,
        request.canvas_width, request.canvas_height,
        request.safe_area, line_height_factor, max_lines,
        request.alignment,
    )

    # Construir resultado
    layout = TextLayout(
        lines=text_lines,
        font_size=font_size,
        font_path=request.font_path,
        line_spacing=lh,
        total_width=max_line_w,
        total_height=total_height,
        x=text_lines[0].x if text_lines else 0,
        y=y0,
        alignment=request.alignment,
        overflow=has_overflow,
        overflow_x=ox,
        overflow_y=oy,
        score=score,
        warnings=wrap_warnings + scoring_warnings,
    )

    # Confidence
    if has_overflow:
        layout.confidence = max(0.0, score / 100.0 - 0.2)
    elif score >= 80:
        layout.confidence = 0.90
    elif score >= 65:
        layout.confidence = 0.75
    else:
        layout.confidence = 0.50

    # Status
    if font_size < request.min_font_size:
        layout.status = "needs_split"
        layout.split_required = True
        layout.split_candidates = find_split_points(text)
    elif has_overflow:
        layout.status = "overflow"
    else:
        layout.status = "ok"

    # Ajustes realizados
    if font_size < request.preferred_font_size:
        layout.adjustments.append(
            f"font reducido de {request.preferred_font_size} a {font_size}"
        )

    return layout


# ─────────────────────────────────────────────
# Validación
# ─────────────────────────────────────────────

def validate_layout(layout: TextLayout, request: TextLayoutRequest) -> dict[str, Any]:
    """
    Valida un TextLayout y devuelve un reporte.

    Returns:
        dict con valid (bool), errors, warnings, stats
    """
    errors: list[str] = list(layout.errors)
    warnings: list[str] = list(layout.warnings)
    stats: dict[str, Any] = {}

    # ── Errors ──
    if layout.overflow:
        errors.append("overflow detectado")
    if layout.font_size < request.min_font_size:
        errors.append(f"font size {layout.font_size} < mínimo {request.min_font_size}")
    if not layout.lines:
        errors.append("sin líneas de texto")

    # ── Warnings ──
    if len(layout.lines) > request.max_lines:
        warnings.append(
            f"{len(layout.lines)} líneas > máximo {request.max_lines}"
        )

    # Bloque demasiado alto
    usable_h = request.canvas_height - request.safe_area.get("top", 120) - request.safe_area.get("bottom", 192)
    if layout.total_height > usable_h * 0.70:
        warnings.append("bloque de texto ocupa >70% del espacio vertical usable")

    # Font pequeño
    if layout.font_size < request.preferred_font_size * 0.75:
        warnings.append(f"font size reducido significativamente ({layout.font_size}px)")

    # ── Stats ──
    stats = {
        "font_size": layout.font_size,
        "line_count": len(layout.lines),
        "total_height": round(layout.total_height, 1),
        "total_width": round(layout.total_width, 1),
        "score": round(layout.score, 1),
        "confidence": layout.confidence,
        "overflow": layout.overflow,
        "status": layout.status,
    }

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("TEXT LAYOUT ENGINE — Demo")
    print("=" * 60)

    test_texts = [
        ("Corto", "Perdonar no significa volver."),
        ("Medio", "Perdonar no significa volver a exponerte al mismo daño."),
        ("Largo", "Dios puede pedirte que perdones, pero no te pide que permanezcas atrapado en aquello que destruye tu vida."),
        ("Muy largo", "Hay personas que pasan muchos años de su vida intentando demostrar que son suficientes para alguien que nunca valoró lo que tenían para ofrecer."),
    ]

    for label, text in test_texts:
        print(f"\n{'─' * 50}")
        print(f"CASO: {label}")
        print(f"Texto: {text[:70]}...")
        print()

        req = TextLayoutRequest(
            text=text,
            platform=Platform.SHORT_VERTICAL,
            preferred_position=Position.LOWER,
        )
        layout = compute_layout(req)
        report = validate_layout(layout, req)

        print(f"  Font size: {layout.font_size}px")
        print(f"  Líneas: {len(layout.lines)}")
        for i, line in enumerate(layout.lines):
            print(f"    L{i+1}: \"{line.text}\" ({line.width:.0f}px)")
        print(f"  Total: {layout.total_width:.0f}w × {layout.total_height:.0f}h")
        print(f"  Posición: ({layout.x:.0f}, {layout.y:.0f})")
        print(f"  Overflow: {layout.overflow}")
        print(f"  Score: {layout.score:.1f}/100")
        print(f"  Confidence: {layout.confidence:.2f}")
        print(f"  Status: {layout.status}")
        if layout.warnings:
            print(f"  Warnings: {layout.warnings}")
        if layout.adjustments:
            print(f"  Ajustes: {layout.adjustments}")
        print(f"  Valid: {report['valid']}")
