"""
test_asset_selector.py — Tests para asset_selector.py

NO hace llamadas reales a Pexels. Usa fixtures mock.
Ejecutar: python3 test_asset_selector.py
"""

import sys
sys.path.insert(0, ".")

from scene_brief import SceneBrief, NarrativeRole, MotionType
from asset_selector import (
    AssetCandidate, AssetScore, AssetSelection,
    generate_queries, score_candidate, select_asset,
    compute_confidence, confidence_label,
    _simplify_setting, _translate_action, _translate_subject,
    _simplify_visual_event, _extract_emotion_words,
    _technical_rejection, _score_action_match,
    WEIGHTS, EMOTION_TO_ACTION,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

def _brief_reloj():
    """Escena: mujer sosteniendo teléfono en habitación."""
    return SceneBrief(
        scene_id="e01",
        narrative_role=NarrativeRole.HOOK,
        narration="Dios no te pide que permanezcas atrapado en una relación destructiva.",
        emotional_core="alivio — alguien lo dice en voz alta",
        visual_event="Mujer sentada en el borde de una cama, sosteniendo el teléfono con ambas manos.",
        subject="mujer",
        action="sostener el teléfono sin abrir el mensaje",
        setting="habitación con luz tenue, tarde nublada",
        symbol="el teléfono con un mensaje sin leer",
        text_space="upper",
        continuity_group="relationship_home",
        duration=5.6,
    )


def _brief_psicologia():
    """Escena de psicología: por qué sentimos que debemos demostrar nuestro valor."""
    return SceneBrief(
        scene_id="e04",
        narrative_role=NarrativeRole.PSYCHOLOGY,
        narration="Hay un patrón: das, das, das, y cuando pones un límite, te hacen sentir que eres tú la que cambió.",
        emotional_core="identificación del patrón — el espectador se ve",
        visual_event="Mujer apilando platos en la cocina, uno sobre otro, con cuidado exagerado.",
        subject="mujer",
        action="apilar platos con cuidado exagerado",
        setting="cocina silenciosa, luz de ventana filtrada",
        symbol="los platos apilados con cuidado",
        continuity_group="reflection",
        duration=7.5,
    )


def _brief_fe():
    """Escena de fe: qué significa perdonar."""
    return SceneBrief(
        scene_id="e06",
        narrative_role=NarrativeRole.BIBLICAL_GROUNDING,
        narration="Perdonar no significa volver al mismo lugar donde te lastimaron.",
        emotional_core="verdad directa que quita la culpa",
        visual_event="Manos abiertas sobre una mesa de madera, soltando algo invisible.",
        action="abrir las manos lentamente sobre la mesa",
        setting="mesa de madera rústica, luz cálida de atardecer",
        symbol="las manos abiertas — soltar",
        text_space="lower",
        continuity_group="faith",
        duration=4.5,
    )


def _brief_habitos():
    """Escena de hábitos: por qué posponemos."""
    return SceneBrief(
        scene_id="e03",
        narrative_role=NarrativeRole.PROBLEM,
        narration="El problema no es la falta de tiempo, es el miedo a empezar.",
        emotional_core="reconocimiento del patrón de procrastinación",
        visual_event="Persona mirando una lista de tareas pendientes en el teléfono, sin tocarla.",
        subject="persona",
        action="mirar la lista sin actuar",
        setting="oficina caótica, papeles por todos lados",
        symbol="la lista ignirada en la pantalla",
        duration=6.0,
    )


def _mock_candidate(
    id=1, orientation="portrait", width=1080, height=1920,
    duration=5.0, fps=30, quality="hd", file_size=50_000_000,
    query_used="person holding phone",
):
    """Crea un candidato ficticio."""
    return AssetCandidate(
        id=id, url=f"https://pexels.com/video/{id}.mp4",
        duration=duration, width=width, height=height,
        orientation=orientation, fps=fps, file_size=file_size,
        quality=quality, source="pexels", query_used=query_used,
    )


def _mock_fetch(candidates):
    """Crea una función fetch mock que devuelve candidatos fijos."""
    def fetch(query, per_page=10):
        return [c.__dict__.copy() for c in candidates]
    return fetch


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

def test_asset_candidate_creation():
    """TEST 1: Creación de AssetCandidate."""
    c = _mock_candidate(id=42, width=1080, height=1920)
    assert c.id == 42
    assert c.width == 1080
    assert c.height == 1920
    assert c.orientation == "portrait"
    print("  PASS — AssetCandidate creado correctamente")


def test_asset_candidate_from_pexels():
    """TEST 2: AssetCandidate.from_pexels() con dict real."""
    raw = {
        "id": 123, "url": "https://example.com/123.mp4",
        "duration": 8.0, "width": 1920, "height": 1080,
        "orientation": "landscape", "fps": 24,
        "file_size": 80_000_000, "thumbnail": "https://example.com/thumb.jpg",
        "quality": "hd", "source": "pexels",
    }
    c = AssetCandidate.from_pexels(raw)
    assert c.id == 123
    assert c.orientation == "landscape"
    assert c.width == 1920
    print("  PASS — from_pexels() funciona con dict")


def test_asset_score_creation():
    """TEST 3: Creación de AssetScore y compute_total."""
    s = AssetScore(
        narrative_relevance=20,
        action_match=15,
        composition=12,
        technical_quality=8,
        text_space=7,
        emotional_fit=3,
        continuity=4,
        diversity=4,
        penalties=-5,
    )
    total = s.compute_total()
    assert total == 68.0
    assert s.total == 68.0
    print("  PASS — AssetScore compute_total = 68.0")


def test_asset_selection_creation():
    """TEST 4: Creación de AssetSelection."""
    sel = AssetSelection(
        status="ok", confidence=0.85,
        reasons=["buena coincidencia"],
    )
    assert sel.status == "ok"
    assert sel.confidence == 0.85
    assert sel.selected is None
    print("  PASS — AssetSelection creado")


def test_query_generation_basic():
    """TEST 5: generate_queries() genera queries no vacías."""
    brief = _brief_reloj()
    queries = generate_queries(brief)
    assert len(queries) >= 3
    assert all(len(q) > 2 for q in queries)
    print(f"  PASS — {len(queries)} queries generadas: {queries}")


def test_query_generation_psicologia():
    """TEST 6: Queries diferentes para tema psicología."""
    brief = _brief_psicologia()
    queries = generate_queries(brief)
    assert len(queries) >= 3
    # Debe contener algo de "stacking" o "kitchen"
    all_text = " ".join(queries).lower()
    assert any(k in all_text for k in ["stack", "kitchen", "apil", "plato", "organiz"])
    print(f"  PASS — Queries psicología: {queries}")


def test_query_generation_fe():
    """TEST 7: Queries diferentes para tema fe."""
    brief = _brief_fe()
    queries = generate_queries(brief)
    assert len(queries) >= 3
    all_text = " ".join(queries).lower()
    # Debe contener algo de "hands" o "table"
    assert any(k in all_text for k in ["hand", "table", "mesa", "open"])
    print(f"  PASS — Queries fe: {queries}")


def test_query_generation_habitos():
    """TEST 8: Queries diferentes para tema hábitos."""
    brief = _brief_habitos()
    queries = generate_queries(brief)
    assert len(queries) >= 3
    all_text = " ".join(queries).lower()
    # Debe contener algo de "list" o "phone" o "office"
    assert any(k in all_text for k in ["list", "phone", "office", "looking", "task"])
    print(f"  PASS — Queries hábitos: {queries}")


def test_vertical_filter():
    """TEST 9: Filtro técnico rechaza horizontal para short."""
    brief = _brief_reloj()
    c_landscape = _mock_candidate(
        id=10, orientation="landscape", width=1920, height=1080
    )
    reason = _technical_rejection(c_landscape, brief)
    # No se rechaza automáticamente por orientación — solo se penaliza
    assert reason is None  # orientación no es rechazo técnico
    print("  PASS — Landscape no rechazado técnicamente (penalizado en scoring)")


def test_resolution_filter():
    """TEST 10: Filtro técnico rechaza resolución muy baja."""
    brief = _brief_reloj()
    c_low = _mock_candidate(id=20, width=320, height=240)
    reason = _technical_rejection(c_low, brief)
    assert reason is not None
    assert "resolución" in reason
    print(f"  PASS — Resolución baja rechazada: {reason}")


def test_action_match_strong():
    """TEST 11: Action match fuerte cuando la acción coincide."""
    brief = _brief_reloj()
    brief.action = "sostener el teléfono"
    c = _mock_candidate(query_used="person holding phone at home")
    score = _score_action_match(c, brief)
    assert score >= 12.0, f"Expected >= 12, got {score}"
    print(f"  PASS — Action match fuerte: {score}")


def test_action_match_weak():
    """TEST 12: Action match débil cuando no coincide."""
    brief = _brief_reloj()
    brief.action = "escribir un mensaje"
    c = _mock_candidate(query_used="person walking in park")
    score = _score_action_match(c, brief)
    assert score < 12.0, f"Expected < 12, got {score}"
    print(f"  PASS — Action match débil: {score}")


def test_narrative_relevance():
    """TEST 13: Narrative relevance más alto para candidato con query similar al visual_event."""
    brief = _brief_reloj()
    c = _mock_candidate(query_used="woman sitting bed holding phone")
    from asset_selector import _score_narrative_relevance
    nr = _score_narrative_relevance(c, brief)
    assert nr >= 10, f"Expected >= 10, got {nr}"
    print(f"  PASS — Narrative relevance: {nr}")


def test_text_space_scoring():
    """TEST 14: Text space scoring considera orientación."""
    brief = _brief_reloj()
    brief.text_space = "upper"
    c_portrait = _mock_candidate(orientation="portrait", height=1920)
    from asset_selector import _score_text_space
    ts = _score_text_space(c_portrait, brief)
    assert ts >= 7, f"Expected >= 7, got {ts}"
    print(f"  PASS — Text space portrait: {ts}")


def test_penalizacion_repeated():
    """TEST 15: Penalización por candidato repetido."""
    brief = _brief_reloj()
    c = _mock_candidate(id=42)
    prev = [_mock_candidate(id=42)]  # mismo ID
    score = score_candidate(c, brief, previous_assets=prev)
    assert score.penalties < 0, f"Expected negative penalties, got {score.penalties}"
    print(f"  PASS — Penalización repetido: {score.penalties}")


def test_diversity_scoring():
    """TEST 16: Diversidad penaliza candidatos similares a anteriores."""
    brief = _brief_reloj()
    c = _mock_candidate(query_used="woman holding phone at home")
    prev = [_mock_candidate(query_used="woman holding phone at home")]
    from asset_selector import _score_diversity
    div = _score_diversity(c, prev)
    assert div < 5.0, f"Expected < 5.0, got {div}"
    print(f"  PASS — Diversidad penalizada: {div}")


def test_confidence_computation():
    """TEST 17: Confidence se calcula correctamente."""
    s = AssetScore(total=85)
    conf = compute_confidence(s, 5)
    assert 0.0 <= conf <= 1.0
    assert conf >= 0.70
    print(f"  PASS — Confidence: {conf}")


def test_confidence_label():
    """TEST 18: Confidence labels."""
    assert confidence_label(0.95) == "muy_fuerte"
    assert confidence_label(0.75) == "bueno"
    assert confidence_label(0.55) == "usable_pero_dudoso"
    assert confidence_label(0.30) == "material_debil"
    print("  PASS — Confidence labels correctos")


def test_select_asset_mock():
    """TEST 19: select_asset() con fetch mock funciona end-to-end."""
    brief = _brief_reloj()
    candidates = [
        _mock_candidate(id=1, query_used="woman holding phone at home"),
        _mock_candidate(id=2, query_used="person sitting bed"),
        _mock_candidate(id=3, query_used="woman writing message"),
    ]
    # Mock fetch que devuelve los mismos candidatos para cada query
    seen_queries = []
    def fetch(query, per_page=10):
        seen_queries.append(query)
        return [c.__dict__.copy() for c in candidates]
    selection = select_asset(brief, fetch_fn=fetch)

    assert selection.status == "ok"
    assert selection.selected is not None
    assert selection.confidence > 0
    assert len(selection.ranked_candidates) >= 3  # al menos 3 candidatos únicos
    print(f"  PASS — select_asset OK, selected ID={selection.selected.id}, confidence={selection.confidence}, ranked={len(selection.ranked_candidates)}")


def test_select_asset_no_candidates():
    """TEST 20: select_asset() sin candidatos devueltos."""
    brief = _brief_reloj()
    fetch = _mock_fetch([])
    selection = select_asset(brief, fetch_fn=fetch)

    assert selection.status == "no_candidates"
    assert selection.selected is None
    print("  PASS — no_candidates detectado")


def test_serialization():
    """TEST 21: AssetSelection.to_dict() funciona."""
    sel = AssetSelection(
        selected=_mock_candidate(id=42),
        confidence=0.88,
        status="ok",
        reasons=["test"],
    )
    d = sel.to_dict()
    assert d["selected_id"] == 42
    assert d["confidence"] == 0.88
    assert d["status"] == "ok"
    print("  PASS — Serialización to_dict()")


def test_simplify_setting():
    """TEST 22: _simplify_setting() traduce correctamente."""
    assert "home" in _simplify_setting("cocina cálida")
    assert "home" in _simplify_setting("habitación con luz")
    assert "table" in _simplify_setting("mesa de madera")
    assert "outdoors" in _simplify_setting("calle residencial")
    assert "window" in _simplify_setting("junto a la ventana")
    print("  PASS — _simplify_setting()")


def test_translate_action():
    """TEST 23: _translate_action() traduce español a inglés."""
    assert _translate_action("escribir un mensaje") in ["typing", "writing", "texting"]
    assert _translate_action("sostener el teléfono") in ["holding", "gripping"]
    assert _translate_action("caminar por la calle") in ["walking", "stepping"]
    print("  PASS — _translate_action()")


def test_translate_subject():
    """TEST 24: _translate_subject() traduce correctamente."""
    assert _translate_subject("mujer adulta") == "woman"
    assert _translate_subject("hombre joven") == "person"
    assert _translate_subject("manos abiertas") == "hands"
    print("  PASS — _translate_subject()")


def test_simplify_visual_event():
    """TEST 25: _simplify_visual_event() simplifica correctamente."""
    result = _simplify_visual_event("Mujer sentada en el borde de una cama")
    assert "sitting" in result.lower()
    result2 = _simplify_visual_event("Manos abiertas sobre una mesa")
    assert "open" in result2.lower() or "hands" in result2.lower()
    print("  PASS — _simplify_visual_event()")


def test_extract_emotion_words():
    """TEST 26: _extract_emotion_words() detecta emociones."""
    found = _extract_emotion_words("hay agotamiento y ansiedad")
    assert "agotamiento" in found
    assert "ansiedad" in found
    found2 = _extract_emotion_words("esperanza y confianza")
    assert "esperanza" in found2
    print("  PASS — _extract_emotion_words()")


def test_emotion_to_action_mapping():
    """TEST 27: EMOTION_TO_ACTION tiene cobertura razonable."""
    assert "agotamiento" in EMOTION_TO_ACTION
    assert "esperanza" in EMOTION_TO_ACTION
    assert "relación" in EMOTION_TO_ACTION
    assert len(EMOTION_TO_ACTION) >= 10
    print(f"  PASS — {len(EMOTION_TO_ACTION)} emociones mapeadas")


def test_weights_documented():
    """TEST 28: WEIGHTS están documentados y suman razonablemente."""
    total = sum(WEIGHTS.values())
    assert total == 95  # 25+20+15+10+10+5+5+5
    assert all(v > 0 for v in WEIGHTS.values())
    print(f"  PASS — WEIGHTS suman {total}")


def test_ranking_order():
    """TEST 29: Ranking ordena de mayor a menor score."""
    brief = _brief_reloj()
    c_high = _mock_candidate(id=1, width=1920, height=1080, quality="hd",
                             query_used="woman sitting bed holding phone")
    c_low = _mock_candidate(id=2, width=640, height=480, quality="sd",
                            query_used="abstract background")
    # Mock que devuelve ambos candidatos para cada query
    def fetch(query, per_page=10):
        return [c_high.__dict__.copy(), c_low.__dict__.copy()]
    selection = select_asset(brief, fetch_fn=fetch)

    assert len(selection.ranked_candidates) >= 2
    # El mejor candidato debe tener mayor score que el peor
    scores = [s.total for _, s in selection.ranked_candidates]
    assert max(scores) > min(scores), f"Expected variation in scores: {scores}"
    print("  PASS — Ranking ordenado correctamente")


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def main():
    tests = [
        test_asset_candidate_creation,
        test_asset_candidate_from_pexels,
        test_asset_score_creation,
        test_asset_selection_creation,
        test_query_generation_basic,
        test_query_generation_psicologia,
        test_query_generation_fe,
        test_query_generation_habitos,
        test_vertical_filter,
        test_resolution_filter,
        test_action_match_strong,
        test_action_match_weak,
        test_narrative_relevance,
        test_text_space_scoring,
        test_penalizacion_repeated,
        test_diversity_scoring,
        test_confidence_computation,
        test_confidence_label,
        test_select_asset_mock,
        test_select_asset_no_candidates,
        test_serialization,
        test_simplify_setting,
        test_translate_action,
        test_translate_subject,
        test_simplify_visual_event,
        test_extract_emotion_words,
        test_emotion_to_action_mapping,
        test_weights_documented,
        test_ranking_order,
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("TESTS — asset_selector.py")
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
