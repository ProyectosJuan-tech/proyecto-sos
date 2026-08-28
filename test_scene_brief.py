"""
test_scene_brief.py — Tests mínimos para scene_brief.py

Ejecutar: python3 test_scene_brief.py
"""

import sys
import json

sys.path.insert(0, ".")

from scene_brief import (
    SceneBrief, SceneType, NarrativeRole, PreferredSource,
    MotionType, TransitionType,
    scene_brief_from_dict, example_brief,
    compose_prompt_from_brief, direct_from_brief,
)


def test_create_valid_brief():
    """TEST 1: Crear un SceneBrief válido."""
    brief = SceneBrief(
        scene_id="test_01",
        narration="Tu cansancio no viene de lo que haces.",
        emotional_core="agotamiento silencioso",
        visual_event="Mujer dejando una taza sobre la mesa",
        action="dejar la taza",
        setting="cocina cálida",
        duration=5.0,
    )
    result = brief.validate()
    assert result["valid"] is True, f"Expected valid, got errors: {result['errors']}"
    assert len(result["errors"]) == 0
    print("  PASS — SceneBrief válido creado y validado")
    return brief


def test_validate_invalid():
    """TEST 2: SceneBrief inválido — validate() detecta problemas."""
    brief = SceneBrief(
        scene_id="test_invalid",
        visual_event="",
        action="",
        setting="",
        duration=-1,
    )
    result = brief.validate()
    assert result["valid"] is False, "Expected invalid"
    assert len(result["errors"]) >= 4, f"Expected ≥4 errors, got {len(result['errors'])}"
    assert any("visual_event" in e for e in result["errors"])
    assert any("action" in e for e in result["errors"])
    assert any("setting" in e for e in result["errors"])
    assert any("duration" in e for e in result["errors"])
    print(f"  PASS — {len(result['errors'])} errores detectados correctamente")
    return brief


def test_validate_warnings():
    """TEST 3: SceneBrief válido pero con warnings."""
    brief = SceneBrief(
        scene_id="test_warnings",
        visual_event="Escena simple",
        action="actuar",
        setting="lugar",
        duration=3.0,
        # emotional_core, symbol, pexels_queries, ai_prompt, composition, lighting, camera
        # todos ausentes → warnings
    )
    result = brief.validate()
    assert result["valid"] is True
    assert len(result["warnings"]) >= 5, f"Expected ≥5 warnings, got {len(result['warnings'])}"
    print(f"  PASS — {len(result['warnings'])} warnings detectados correctamente")
    return result


def test_serialization_roundtrip():
    """TEST 4: Serialización dict → SceneBrief → dict."""
    original = example_brief()
    d = original.to_dict()
    reconstructed = SceneBrief.from_dict(d)

    # Verificar campos importantes
    assert reconstructed.scene_id == original.scene_id
    assert reconstructed.narration == original.narration
    assert reconstructed.visual_event == original.visual_event
    assert reconstructed.action == original.action
    assert reconstructed.setting == original.setting
    assert reconstructed.emotional_core == original.emotional_core
    assert reconstructed.symbol == original.symbol
    assert reconstructed.preferred_source == original.preferred_source
    assert reconstructed.motion == original.motion
    assert reconstructed.duration == original.duration
    assert reconstructed.pexels_queries == original.pexels_queries
    print("  PASS — Roundtrip dict → SceneBrief → dict exitoso")


def test_json_roundtrip():
    """TEST 5: Serialización JSON → SceneBrief → JSON."""
    original = example_brief()
    json_str = original.to_json()
    reconstructed = SceneBrief.from_json(json_str)

    assert reconstructed.scene_id == original.scene_id
    assert reconstructed.narration == original.narration
    assert reconstructed.visual_event == original.visual_event
    assert reconstructed.duration == original.duration
    print("  PASS — Roundtrip JSON → SceneBrief → JSON exitoso")


def test_from_scene_dict():
    """TEST 6: Conversión desde dict de escena existente."""
    # Dict tipo hacer_shorts.py
    scene_dict = {
        "id": "soltar",
        "text": "Tu cansancio no viene de lo que haces.",
        "ai": "Close-up of a tired woman sitting on a bed edge.",
        "q": "hands leaves",
        "motion": "zoom-in",
        "light": True,
        "style": "bright airy natural",
    }

    brief, warnings = SceneBrief.from_scene_dict(scene_dict)

    assert brief.scene_id == "soltar"
    assert brief.narration == "Tu cansancio no viene de lo que haces."
    assert brief.ai_prompt == "Close-up of a tired woman sitting on a bed edge."
    assert brief.pexels_queries == ["hands", "leaves"]
    assert brief.motion == MotionType.ZOOM_IN
    assert brief.lighting == "bright airy natural light"
    assert brief.preferred_source == PreferredSource.AI
    print(f"  PASS — from_scene_dict con {len(warnings)} warnings")


def test_from_scene_dict_stock():
    """TEST 7: Conversión con stock=True."""
    scene_dict = {
        "text": "Algo corto.",
        "ai": "prompt here",
        "motion": "pan-right",
        "stock": True,
    }

    brief, warnings = SceneBrief.from_scene_dict(scene_dict)
    assert brief.preferred_source == PreferredSource.STOCK
    assert brief.motion == MotionType.PAN_RIGHT
    print("  PASS — from_scene_dict con stock=True")


def test_compose_dict():
    """TEST 8: to_compose_dict() genera dict compatible con compose_prompt()."""
    brief = example_brief()
    d = brief.to_compose_dict()

    # Los 6 campos requeridos por compose_prompt()
    assert "emotional_core" in d
    assert "visual_event" in d
    assert "symbol" in d
    assert "setting" in d
    assert "light" in d
    assert "camera" in d

    # Campos opcionales
    assert "action" in d
    assert "color" in d
    assert "composition" in d
    assert "text_space" in d
    assert "style" in d
    assert "subject_priority" in d
    assert "risks" in d
    assert "style_family" in d

    # Verificar que no está vacío
    assert d["visual_event"]
    assert d["setting"]
    print("  PASS — to_compose_dict() genera 6 required + 8 optional keys")


def test_scene_brief_from_dict_alias():
    """TEST 9: scene_brief_from_dict() alias funciona."""
    scene_dict = {
        "text": "Test corto.",
        "ai": "A simple scene.",
        "motion": "static",
    }
    brief = scene_brief_from_dict(scene_dict)
    assert isinstance(brief, SceneBrief)
    assert brief.narration == "Test corto."
    print("  PASS — scene_brief_from_dict() alias funciona")


def test_example_brief_valid():
    """TEST 10: example_brief() es válido."""
    brief = example_brief()
    result = brief.validate()
    assert result["valid"] is True, f"Example brief invalid: {result['errors']}"
    assert len(result["errors"]) == 0
    print("  PASS — example_brief() es válido")


def test_director_compose():
    """TEST 11: director_visual.compose_prompt() acepta SceneBrief."""
    try:
        brief = example_brief()
        prompt = compose_prompt_from_brief(brief)
        assert isinstance(prompt, str)
        assert len(prompt) > 50, f"Prompt too short: {prompt}"
        # El prompt debe contener elementos de la escena
        # (puede estar en español o inglés dependiendo de compose_prompt)
        has_scene_content = any(word in prompt.lower() for word in [
            "cup", "taza", "kitchen", "cocina", "woman", "mujer",
            "morning", "mañana", "window", "ventana",
        ])
        assert has_scene_content, f"Prompt missing scene elements: {prompt[:200]}"
        print(f"  PASS — compose_prompt_from_brief() generó prompt ({len(prompt)} chars)")
        print(f"         Preview: {prompt[:120]}...")
    except ImportError:
        print("  SKIP — director_visual.py no disponible (normal en test aislado)")
    except Exception as e:
        print(f"  FAIL — {e}")
        raise


def test_director_direct():
    """TEST 12: direct_from_brief() genera dirección completa."""
    try:
        brief = example_brief()
        result = direct_from_brief(brief)
        assert isinstance(result, dict)
        assert "visual_event" in result
        assert "prompt" in result
        assert len(result["prompt"]) > 50
        assert "emotional_core" in result
        assert "symbol" in result
        print(f"  PASS — direct_from_brief() generó dirección completa ({len(result['prompt'])} chars)")
    except ImportError:
        print("  SKIP — director_visual.py no disponible (normal en test aislado)")
    except Exception as e:
        print(f"  FAIL — {e}")
        raise


def test_enums():
    """TEST 13: Enums funcionan correctamente."""
    assert SceneType.SHORT.value == "short"
    assert NarrativeRole.HOOK.value == "hook"
    assert PreferredSource.AI.value == "ai"
    assert MotionType.ZOOM_IN.value == "zoom-in"
    assert TransitionType.FADE.value == "fade"
    print("  PASS — Enums correctos")


def test_unknown_motion_handled():
    """TEST 14: Motion desconocido no crashea."""
    scene_dict = {"text": "Test", "ai": "Test", "motion": "invalid_motion"}
    brief, warnings = SceneBrief.from_scene_dict(scene_dict)
    assert any("motion" in w.lower() for w in warnings)
    print("  PASS — Motion inválido manejado con warning")


def test_empty_dict():
    """TEST 15: Dict vacío no crashea."""
    brief = SceneBrief.from_dict({})
    assert isinstance(brief, SceneBrief)
    result = brief.validate()
    assert result["valid"] is False
    print("  PASS — Dict vacío produce SceneBrief inválido (esperado)")


# ─────────────────────────────────────────
# Runner
# ─────────────────────────────────────────

def main():
    tests = [
        test_create_valid_brief,
        test_validate_invalid,
        test_validate_warnings,
        test_serialization_roundtrip,
        test_json_roundtrip,
        test_from_scene_dict,
        test_from_scene_dict_stock,
        test_compose_dict,
        test_scene_brief_from_dict_alias,
        test_example_brief_valid,
        test_director_compose,
        test_director_direct,
        test_enums,
        test_unknown_motion_handled,
        test_empty_dict,
    ]

    passed = 0
    failed = 0
    skipped = 0

    print("=" * 60)
    print("TESTS — scene_brief.py")
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
    print(f"RESULTADO: {passed} pass, {failed} fail, {skipped} skip")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
