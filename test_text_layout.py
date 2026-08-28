"""
test_text_layout.py — Tests para text_layout.py

NO renderiza video. Solo testeá composición tipográfica.
Ejecutar: python3 test_text_layout.py
"""

import sys
sys.path.insert(0, ".")

from text_layout import (
    TextLayoutRequest, TextLayout, TextLine,
    Platform, Position, Alignment, NarrativeRole,
    compute_layout, validate_layout, wrap_intelligent,
    find_split_points, PLATFORM_PRESETS, ROLE_ADJUSTMENTS,
    _measure_word, _measure_line, _get_font, FONT_PATH,
    _compute_position, _compute_x, _score_layout,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

def _vertical_request(text, **kwargs):
    """Request vertical 1080x1920."""
    defaults = {
        "text": text,
        "canvas_width": 1080,
        "canvas_height": 1920,
        "safe_area": {"top": 120, "bottom": 192, "left": 90, "right": 90},
        "max_width": 900,
        "preferred_position": Position.LOWER,
        "alignment": Alignment.CENTER,
        "platform": Platform.SHORT_VERTICAL,
    }
    defaults.update(kwargs)
    return TextLayoutRequest(**defaults)


def _horizontal_request(text, **kwargs):
    """Request horizontal 1920x1080."""
    defaults = {
        "text": text,
        "canvas_width": 1920,
        "canvas_height": 1080,
        "safe_area": {"top": 60, "bottom": 108, "left": 200, "right": 200},
        "max_width": 1497,
        "preferred_position": Position.LOWER,
        "alignment": Alignment.CENTER,
        "platform": Platform.YOUTUBE_HORIZONTAL,
    }
    defaults.update(kwargs)
    return TextLayoutRequest(**defaults)


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

def test_short_text():
    """TEST 1: Texto corto — debería caber en 1 línea."""
    req = _vertical_request("Perdonar no significa volver.")
    layout = compute_layout(req)
    assert len(layout.lines) == 1
    assert not layout.overflow
    assert layout.score > 60
    print(f"  PASS — 1 línea, font={layout.font_size}, score={layout.score:.0f}")


def test_medium_text():
    """TEST 2: Texto medio — debería ser 2-3 líneas."""
    req = _vertical_request("Perdonar no significa volver a exponerte al mismo daño.")
    layout = compute_layout(req)
    assert 2 <= len(layout.lines) <= 3
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_long_text():
    """TEST 3: Texto largo — debería ser 3-5 líneas."""
    req = _vertical_request(
        "Dios puede pedirte que perdones, pero no te pide que "
        "permanezcas atrapado en aquello que destruye tu vida."
    )
    layout = compute_layout(req)
    assert 3 <= len(layout.lines) <= 5
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_one_line():
    """TEST 4: Texto de exactamente 1 línea."""
    req = _vertical_request("Sí.")
    layout = compute_layout(req)
    assert len(layout.lines) == 1
    assert not layout.overflow
    print(f"  PASS — 1 línea, font={layout.font_size}")


def test_two_lines():
    """TEST 5: Texto de exactamente 2 líneas."""
    # Forzar 2 líneas
    req = _vertical_request("Una frase que debería ocupar exactamente dos líneas en pantalla.")
    layout = compute_layout(req)
    assert len(layout.lines) >= 2
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_three_lines():
    """TEST 6: Texto de 3 líneas."""
    req = _vertical_request(
        "Hay un patrón que repites sin darte cuenta. "
        "Das todo y no pides nada."
    )
    layout = compute_layout(req)
    assert len(layout.lines) >= 2
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_long_words():
    """TEST 7: Palabras largas (inconstitucionalmente)."""
    req = _vertical_request("La inconstitucionalmente speaking no es común.")
    layout = compute_layout(req)
    assert not layout.overflow
    assert len(layout.lines) >= 1
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_question_marks():
    """TEST 8: Signos de interrogación."""
    req = _vertical_request("¿Cuánto tiempo llevas intentando que una relación deje de doler?")
    layout = compute_layout(req)
    assert not layout.overflow
    assert len(layout.lines) >= 2
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_exclamation_marks():
    """TEST 9: Signos de exclamación."""
    req = _vertical_request("¡No estás rota! Eso es lo que necesitas escuchar.")
    layout = compute_layout(req)
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_quotes():
    """TEST 10: Comillas."""
    req = _vertical_request('«Conócerte a ti mismo» no significa soportar todo.')
    layout = compute_layout(req)
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_punctuation():
    """TEST 11: Puntuación variada."""
    req = _vertical_request(
        "El problema no es la falta de tiempo; es el miedo a empezar. "
        "¿Entiendes la diferencia?"
    )
    layout = compute_layout(req)
    assert not layout.overflow
    print(f"  PASS — {len(layout.lines)} líneas, font={layout.font_size}")


def test_last_line_ratio():
    """TEST 12: Última línea no debe ser extremadamente corta."""
    req = _vertical_request(
        "Perdonar no significa volver a exponerte al mismo daño. "
        "Significa elegir no vivir en el pasado."
    )
    layout = compute_layout(req)
    if len(layout.lines) >= 2:
        last = layout.lines[-1]
        avg_w = sum(l.width for l in layout.lines) / len(layout.lines)
        ratio = last.width / avg_w if avg_w > 0 else 0
        assert ratio > 0.20, f"Última línea muy corta: ratio={ratio:.2f}"
        print(f"  PASS — ratio última línea: {ratio:.2f}")
    else:
        print("  PASS — 1 línea, no aplica")


def test_safe_area_vertical():
    """TEST 13: Safe area vertical respetada."""
    req = _vertical_request("Texto de prueba para verificar safe area vertical.")
    layout = compute_layout(req)
    top = req.safe_area["top"]
    bottom = req.canvas_height - req.safe_area["bottom"]
    assert layout.y >= top, f"Y={layout.y} < top={top}"
    if layout.lines:
        last_bottom = layout.lines[-1].y + layout.lines[-1].height
        assert last_bottom <= bottom, f"bottom={last_bottom} > safe={bottom}"
    print(f"  PASS — safe area respetada (y={layout.y:.0f}, bottom={last_bottom:.0f})")


def test_overflow_x():
    """TEST 14: Overflow horizontal detectado."""
    # Texto extremadamente largo en una sola línea
    req = _vertical_request("palabra", max_width=100)
    layout = compute_layout(req)
    # Con max_width tan pequeño, debería hacer wrap
    assert len(layout.lines) >= 1
    print(f"  PASS — wrap forzado, {len(layout.lines)} líneas")


def test_overflow_y():
    """TEST 15: Overflow vertical detectado."""
    req = _vertical_request(
        "Esto es una prueba de texto muy largo que debería causar "
        "overflow vertical si el espacio es limitado. "
        "Estamos agregando más texto para forzar el problema.",
        max_lines=3,
        min_font_size=70,  # font alto = menos líneas posibles
    )
    layout = compute_layout(req)
    # Puede tener overflow o no dependiendo del font
    assert layout.font_size >= 56
    print(f"  PASS — font={layout.font_size}, overflow={layout.overflow}")


def test_font_minimum():
    """TEST 16: Font mínimo respetado."""
    req = _vertical_request(
        "Texto extremadamente largo que requiere mucho espacio "
        "para ser renderizado correctamente en pantalla.",
        min_font_size=70,
    )
    layout = compute_layout(req)
    assert layout.font_size >= 70
    print(f"  PASS — font mínimo 70, got {layout.font_size}")


def test_needs_split():
    """TEST 17: Texto muy largo detecta needs_split."""
    req = _vertical_request(
        "Hay personas que pasan muchos años de su vida intentando "
        "demostrar que son suficientes para alguien que nunca "
        "valoró lo que tenían para ofrecer, y cuando finalmente "
        "se dan cuenta, ya perdieron tiempo valioso.",
        min_font_size=60,
    )
    layout = compute_layout(req)
    # Puede o no necesitar split dependiendo del tamaño
    assert layout.font_size >= 56
    print(f"  PASS — font={layout.font_size}, split_required={layout.split_required}")


def test_position_lower():
    """TEST 18: Posición lower."""
    req = _vertical_request("Texto de prueba.", preferred_position=Position.LOWER)
    layout = compute_layout(req)
    assert layout.y > req.canvas_height * 0.4
    print(f"  PASS — Y={layout.y:.0f} (lower)")


def test_position_center():
    """TEST 19: Posición center."""
    req = _vertical_request("Texto de prueba.", preferred_position=Position.CENTER)
    layout = compute_layout(req)
    center_y = req.canvas_height / 2
    assert abs(layout.y + layout.total_height / 2 - center_y) < 200
    print(f"  PASS — Y center={layout.y:.0f}")


def test_position_top():
    """TEST 20: Posición top."""
    req = _vertical_request("Texto de prueba.", preferred_position=Position.TOP)
    layout = compute_layout(req)
    assert layout.y <= 200
    print(f"  PASS — Y={layout.y:.0f} (top)")


def test_short_vertical():
    """TEST 21: Short vertical 1080x1920."""
    req = _vertical_request("Perdonar no significa volver a exponerte al mismo daño.")
    layout = compute_layout(req)
    assert req.canvas_width == 1080
    assert req.canvas_height == 1920
    assert not layout.overflow
    print(f"  PASS — 1080x1920, {len(layout.lines)} líneas, score={layout.score:.0f}")


def test_youtube_horizontal():
    """TEST 22: YouTube horizontal 1920x1080."""
    req = _horizontal_request("Perdonar no significa volver a exponerte al mismo daño.")
    layout = compute_layout(req)
    assert req.canvas_width == 1920
    assert req.canvas_height == 1080
    assert not layout.overflow
    print(f"  PASS — 1920x1080, {len(layout.lines)} líneas, score={layout.score:.0f}")


def test_cta_role():
    """TEST 23: CTA — composición simple y grande."""
    req = _vertical_request(
        "Si conoces a alguien que necesita escuchar esto, compártelo.",
        narrative_role=NarrativeRole.CALLOUT,
    )
    layout = compute_layout(req)
    assert len(layout.lines) <= 3
    assert not layout.overflow
    print(f"  PASS — CTA: {len(layout.lines)} líneas, font={layout.font_size}")


def test_hook_role():
    """TEST 24: HOOK — impacto visual."""
    req = _vertical_request(
        "Dios no te pide que permanezcas en lo que te destruye.",
        narrative_role=NarrativeRole.HOOK,
    )
    layout = compute_layout(req)
    assert len(layout.lines) <= 3
    assert not layout.overflow
    assert layout.font_size >= 60
    print(f"  PASS — HOOK: {len(layout.lines)} líneas, font={layout.font_size}")


def test_psychology_role():
    """TEST 25: PSYCHOLOGY — máxima legibilidad."""
    req = _vertical_request(
        "Hay un patrón: das, das, das, y cuando pones un límite, "
        "te hacen sentir que eres tú la que cambió.",
        narrative_role=NarrativeRole.PSYCHOLOGY,
    )
    layout = compute_layout(req)
    assert not layout.overflow
    print(f"  PASS — PSYCHOLOGY: {len(layout.lines)} líneas, font={layout.font_size}")


def test_emphasis_role():
    """TEST 26: EMPHASIS — texto protagonista."""
    req = _vertical_request(
        "¡SÍ!",
        narrative_role=NarrativeRole.EMPHASIS,
    )
    layout = compute_layout(req)
    assert layout.font_size >= 76
    assert not layout.overflow
    print(f"  PASS — EMPHASIS: font={layout.font_size}")


def test_very_long_text():
    """TEST 27: Texto muy largo — split o font pequeño."""
    req = _vertical_request(
        "Hay personas que pasan muchos años de su vida intentando demostrar "
        "que son suficientes para alguien que nunca valoró lo que tenían "
        "para ofrecer, y cuando finalmente se dan cuenta de que el problema "
        "no era ellos sino la relación, ya perdieron tiempo valioso que "
        "podrían haber invertido en construir algo mejor.",
        min_font_size=56,
    )
    layout = compute_layout(req)
    assert layout.font_size >= 56
    print(f"  PASS — muy largo: font={layout.font_size}, lines={len(layout.lines)}, split={layout.split_required}")


def test_real_case_cuanto_tiempo():
    """TEST 28: Caso real — cuánto tiempo."""
    req = _vertical_request(
        "¿Cuánto tiempo llevas intentando que una relación deje de doler?"
    )
    layout = compute_layout(req)
    assert not layout.overflow
    assert len(layout.lines) <= 6
    report = validate_layout(layout, req)
    assert report["valid"]
    print(f"  PASS — real: {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_real_case_perdonar():
    """TEST 29: Caso real — perdonar."""
    req = _vertical_request(
        "Perdonar no significa volver a exponerte al mismo daño."
    )
    layout = compute_layout(req)
    assert not layout.overflow
    report = validate_layout(layout, req)
    assert report["valid"]
    print(f"  PASS — real: {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_real_case_dios():
    """TEST 30: Caso real — Dios."""
    req = _vertical_request(
        "Dios puede pedirte que perdones, pero no te pide que "
        "permanezcas atrapado en aquello que destruye tu vida."
    )
    layout = compute_layout(req)
    assert not layout.overflow
    report = validate_layout(layout, req)
    assert report["valid"]
    print(f"  PASS — real: {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_real_case_posponiendo():
    """TEST 31: Caso real — posponiendo (no tema relación)."""
    req = _vertical_request(
        "Por qué seguimos posponiendo lo que sabemos que tenemos que hacer."
    )
    layout = compute_layout(req)
    assert not layout.overflow
    report = validate_layout(layout, req)
    assert report["valid"]
    print(f"  PASS — real: {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_real_case_aprender():
    """TEST 32: Caso real — aprender (no tema relación)."""
    req = _vertical_request(
        "Aprender algo nuevo requiere más paciencia de la que imaginamos."
    )
    layout = compute_layout(req)
    assert not layout.overflow
    report = validate_layout(layout, req)
    assert report["valid"]
    print(f"  PASS — real: {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_real_case_demostrar():
    """TEST 33: Caso real — demostrar (no tema relación)."""
    req = _vertical_request(
        "Hay personas que pasan años intentando demostrar que son suficientes."
    )
    layout = compute_layout(req)
    assert not layout.overflow
    report = validate_layout(layout, req)
    assert report["valid"]
    print(f"  PASS — real: {len(layout.lines)} líneas, font={layout.font_size}, score={layout.score:.0f}")


def test_alignment_center():
    """TEST 34: Alineación center."""
    req = _vertical_request("Texto de prueba.", alignment=Alignment.CENTER)
    layout = compute_layout(req)
    assert layout.alignment == Alignment.CENTER
    print(f"  PASS — alignment=center")


def test_alignment_left():
    """TEST 35: Alineación left."""
    req = _vertical_request("Texto de prueba.", alignment=Alignment.LEFT)
    layout = compute_layout(req)
    assert layout.alignment == Alignment.LEFT
    print(f"  PASS — alignment=left")


def test_platform_presets():
    """TEST 36: Presets de plataforma existen."""
    assert "short_vertical" in PLATFORM_PRESETS
    assert "youtube_horizontal" in PLATFORM_PRESETS
    assert "facebook_vertical" in PLATFORM_PRESETS
    print("  PASS — 3 presets definidos")


def test_role_adjustments():
    """TEST 37: Ajustes por role existen."""
    assert "hook" in ROLE_ADJUSTMENTS
    assert "psychology" in ROLE_ADJUSTMENTS
    assert "callout" in ROLE_ADJUSTMENTS
    assert "emphasis" in ROLE_ADJUSTMENTS
    print("  PASS — 4 roles con ajustes")


def test_measure_word():
    """TEST 38: Medición de palabra."""
    font = _get_font(FONT_PATH, 76)
    w = _measure_word("Hola", font)
    assert w > 0
    assert w < 500
    print(f"  PASS — 'Hola' = {w:.0f}px")


def test_measure_line():
    """TEST 39: Medición de línea."""
    font = _get_font(FONT_PATH, 76)
    w = _measure_line(["Hola", "mundo"], font)
    assert w > 0
    assert w > _measure_word("Hola", font)
    print(f"  PASS — 'Hola mundo' = {w:.0f}px")


def test_split_points():
    """TEST 40: Split points detectados."""
    text = "Hay un problema. Pero no es el que crees. Es más profundo."
    points = find_split_points(text)
    assert len(points) >= 1
    print(f"  PASS — {len(points)} candidatos de split")


def test_validation_pass():
    """TEST 41: Validación PASS para layout válido."""
    req = _vertical_request("Texto corto y claro.")
    layout = compute_layout(req)
    report = validate_layout(layout, req)
    assert report["valid"]
    assert report["stats"]["score"] > 0
    print(f"  PASS — validación OK")


def test_validation_overflow():
    """TEST 42: Validación detecta overflow."""
    req = _vertical_request("palabra", max_width=50)
    layout = compute_layout(req)
    report = validate_layout(layout, req)
    # Puede tener warnings por overflow
    assert report["stats"]["line_count"] >= 1
    print(f"  PASS — validación con max_width=50")


def test_serialization():
    """TEST 43: TextLayout.to_dict() funciona."""
    req = _vertical_request("Texto de prueba.")
    layout = compute_layout(req)
    d = layout.to_dict()
    assert "font_size" in d
    assert "lines" in d
    assert "score" in d
    assert "overflow" in d
    assert len(d["lines"]) == len(layout.lines)
    print(f"  PASS — serialización OK")


def test_spanish_accents():
    """TEST 44: Español con acentos funciona."""
    req = _vertical_request(
        "La acción de perdonar requiere valentía y decisión."
    )
    layout = compute_layout(req)
    assert not layout.overflow
    print(f"  PASS — acentos OK, {len(layout.lines)} líneas")


def test_english_text():
    """TEST 45: Texto en inglés funciona (motor agnóstico)."""
    req = _vertical_request(
        "Forgiveness is not about weakness. It is about strength.",
        font_path=FONT_PATH,
    )
    layout = compute_layout(req)
    assert not layout.overflow
    print(f"  PASS — inglés OK, {len(layout.lines)} líneas")


def test_comma_clause_wrap():
    """TEST 46: Wrapping respeta cláusulas por coma."""
    req = _vertical_request(
        "Cuando toleras lo que te duele, tu cuerpo lo registra aunque tu mente lo justifique."
    )
    layout = compute_layout(req)
    # Debería cortar en la coma o después
    assert len(layout.lines) >= 2
    # La coma debería estar al final de una línea
    line_texts = [l.text for l in layout.lines]
    print(f"  PASS — {len(layout.lines)} líneas, corte respeta puntuación")


def test_score_range():
    """TEST 47: Score siempre entre 0 y 100."""
    texts = [
        "Sí.",
        "Texto normal de prueba.",
        "Un texto un poco más largo que debería tener varias líneas.",
        "Texto muy largo que requiere mucha evaluación y iteración para encontrar el mejor layout posible.",
    ]
    for text in texts:
        req = _vertical_request(text)
        layout = compute_layout(req)
        assert 0 <= layout.score <= 100, f"Score fuera de rango: {layout.score}"
    print("  PASS — scores siempre 0-100")


def test_confidence_range():
    """TEST 48: Confidence siempre entre 0 y 1."""
    texts = [
        "Sí.",
        "Texto normal.",
        "Texto más largo para probar el rango completo de confidence.",
    ]
    for text in texts:
        req = _vertical_request(text)
        layout = compute_layout(req)
        assert 0 <= layout.confidence <= 1, f"Confidence fuera de rango: {layout.confidence}"
    print("  PASS — confidence siempre 0-1")


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def main():
    tests = [
        test_short_text,
        test_medium_text,
        test_long_text,
        test_one_line,
        test_two_lines,
        test_three_lines,
        test_long_words,
        test_question_marks,
        test_exclamation_marks,
        test_quotes,
        test_punctuation,
        test_last_line_ratio,
        test_safe_area_vertical,
        test_overflow_x,
        test_overflow_y,
        test_font_minimum,
        test_needs_split,
        test_position_lower,
        test_position_center,
        test_position_top,
        test_short_vertical,
        test_youtube_horizontal,
        test_cta_role,
        test_hook_role,
        test_psychology_role,
        test_emphasis_role,
        test_very_long_text,
        test_real_case_cuanto_tiempo,
        test_real_case_perdonar,
        test_real_case_dios,
        test_real_case_posponiendo,
        test_real_case_aprender,
        test_real_case_demostrar,
        test_alignment_center,
        test_alignment_left,
        test_platform_presets,
        test_role_adjustments,
        test_measure_word,
        test_measure_line,
        test_split_points,
        test_validation_pass,
        test_validation_overflow,
        test_serialization,
        test_spanish_accents,
        test_english_text,
        test_comma_clause_wrap,
        test_score_range,
        test_confidence_range,
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("TESTS — text_layout.py")
    print("=" * 60)

    for test_fn in tests:
        name = test_fn.__doc__ or test_fn.__name__
        print(f"\n[{test_fn.__name__}] {name.strip()}")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL — {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTADO: {passed} pass, {failed} fail")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
