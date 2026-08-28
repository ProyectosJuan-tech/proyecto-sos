"""
test_short_director.py — Tests para short_director.py

Ejecutar: python3 test_short_director.py
"""

import sys
import json

sys.path.insert(0, ".")

from scene_brief import SceneBrief, NarrativeRole, MotionType
from short_director import (
    ShortPlan, HookOption, HookStrategy, Tone, Platform,
    estimate_scene_duration, estimate_total_duration,
    generate_hook_options, select_best_hook,
    build_scene, validate_plan,
    plan_to_dict, plan_from_dict, plan_to_json, plan_from_json,
    plan_relacion_destructiva,
)


def test_create_short_plan():
    """TEST 1: Crear un ShortPlan vacío."""
    plan = ShortPlan()
    assert plan.topic == ""
    assert plan.scenes == []
    print("  PASS — ShortPlan vacío creado")
    return plan


def test_build_scene():
    """TEST 2: build_scene() crea SceneBrief con duración estimada."""
    scene = build_scene(
        scene_id="test_01",
        role=NarrativeRole.HOOK,
        narration="Esta es una frase de prueba con suficientes palabras para estimar duración.",
        emotional_core="prueba",
        visual_event="Escena de prueba",
        action="actuar",
        setting="lugar de prueba",
    )
    assert isinstance(scene, SceneBrief)
    assert scene.scene_id == "test_01"
    assert scene.narrative_role == NarrativeRole.HOOK
    assert scene.duration > 0
    print(f"  PASS — SceneBrief creado con duración {scene.duration}s")
    return scene


def test_scene_brief_valid():
    """TEST 3: SceneBrief generado por build_scene() es válido."""
    scene = build_scene(
        scene_id="test_02",
        role=NarrativeRole.SOLUTION,
        narration="Una frase más larga para verificar que la validación funciona correctamente con el sistema de escenas.",
        emotional_core="esperanza",
        visual_event="Alguien abriendo una puerta",
        action="abrir la puerta",
        setting="pasillo iluminado",
    )
    result = scene.validate()
    assert result["valid"] is True, f"SceneBrief inválido: {result['errors']}"
    print("  PASS — SceneBrief válido según validate()")
    return scene


def test_hook_generation():
    """TEST 4: generate_hook_options() genera 3 opciones."""
    options = generate_hook_options("amor propio", "quererse a uno mismo")
    assert len(options) == 3
    strategies = [o.strategy for o in options]
    assert HookStrategy.IDENTIFICATION in strategies
    assert HookStrategy.TENSION in strategies
    assert HookStrategy.AFFIRMATION in strategies
    print("  PASS — 3 hooks generados con estrategias correctas")
    return options


def test_hook_selection():
    """TEST 5: select_best_hook() elige el mejor."""
    options = generate_hook_options("relación", "salir de una relación tóxica")
    best = select_best_hook(options, "relación")
    assert isinstance(best, HookOption)
    assert best.text
    assert best.strategy in [o.strategy for o in options]
    print(f"  PASS — Hook seleccionado: {best.strategy.value} = {best.text[:50]}...")
    return best


def test_validate_plan_valid():
    """TEST 6: validate_plan() con plan válido."""
    plan = plan_relacion_destructiva()
    result = validate_plan(plan)
    assert result["valid"] is True, f"Plan inválido: {result['errors']}"
    assert len(result["errors"]) == 0
    print(f"  PASS — Plan válido, {len(result['warnings'])} warnings")
    return result


def test_validate_plan_invalid():
    """TEST 7: validate_plan() detecta plan inválido."""
    plan = ShortPlan()  # vacío
    result = validate_plan(plan)
    assert result["valid"] is False
    assert len(result["errors"]) >= 3
    print(f"  PASS — {len(result['errors'])} errores detectados en plan vacío")
    return result


def test_serialization_roundtrip():
    """TEST 8: Serialización dict → ShortPlan → dict."""
    original = plan_relacion_destructiva()
    d = plan_to_dict(original)
    reconstructed = plan_from_dict(d)

    assert reconstructed.topic == original.topic
    assert reconstructed.central_idea == original.central_idea
    assert reconstructed.hook == original.hook
    assert len(reconstructed.scenes) == len(original.scenes)
    assert reconstructed.cta == original.cta

    # Verificar que los scenes se preservan
    for orig_s, recon_s in zip(original.scenes, reconstructed.scenes):
        assert recon_s.scene_id == orig_s.scene_id
        assert recon_s.narration == orig_s.narration
        assert recon_s.narrative_role == orig_s.narrative_role

    print("  PASS — Roundtrip dict → ShortPlan → dict exitoso")


def test_json_roundtrip():
    """TEST 9: Serialización JSON → ShortPlan → JSON."""
    original = plan_relacion_destructiva()
    json_str = plan_to_json(original)
    reconstructed = plan_from_json(json_str)

    assert reconstructed.topic == original.topic
    assert len(reconstructed.scenes) == len(original.scenes)
    assert reconstructed.hook_strategy == original.hook_strategy
    print("  PASS — Roundtrip JSON → ShortPlan → JSON exitoso")


def test_duration_estimation():
    """TEST 10: Estimación de duración es razonable."""
    plan = plan_relacion_destructiva()
    total = plan.estimate_total_duration()
    # 9 escenas de ~5-8s cada una = 45-70s
    assert 30 <= total <= 90, f"Duración fuera de rango: {total}s"
    print(f"  PASS — Duración total: {total}s (rango esperado 30-90s)")


def test_spanish_neutral():
    """TEST 11: No hay voseo ni regionalismos."""
    plan = plan_relacion_destructiva()
    result = validate_plan(plan)
    voseo_warnings = [w for w in result["warnings"] if "voseo" in w.lower()]
    assert len(voseo_warnings) == 0, f"Voseo detectado: {voseo_warnings}"

    # Verificar que el plan tiene los flags correctos
    assert plan.voseo is False
    assert plan.regionalisms is False
    assert plan.register == "conversational"
    print("  PASS — Español neutro confirmado (sin voseo)")


def test_invalid_scene_detection():
    """TEST 12: Escena inválida detectada por validate_plan()."""
    plan = ShortPlan(
        topic="test",
        central_idea="test idea",
        hook="test hook",
        cta="test cta",
        scenes=[
            SceneBrief(
                scene_id="bad",
                visual_event="",
                action="",
                setting="",
                duration=-1,
            )
        ],
    )
    result = validate_plan(plan)
    assert result["valid"] is False
    # Debe detectar los errores de la escena
    scene_errors = [e for e in result["errors"] if "bad" in e or "escena" in e]
    assert len(scene_errors) >= 3, f"Expected ≥3 scene errors, got {len(scene_errors)}: {scene_errors}"
    print(f"  PASS — Escena inválida detectada ({len(scene_errors)} errores)")


def test_cta_present():
    """TEST 13: CTA está presente y es coherente."""
    plan = plan_relacion_destructiva()
    assert plan.cta
    assert len(plan.cta) > 10
    assert len(plan.cta.split()) <= 20  # CTA corto
    # No debe ser genérico
    assert "dale like" not in plan.cta.lower()
    assert "suscríbete y" not in plan.cta.lower()
    print(f"  PASS — CTA: {plan.cta[:60]}...")


def test_relacion_destructiva_arc():
    """TEST 14: Caso de prueba tiene el arco correcto."""
    plan = plan_relacion_destructiva()
    roles = plan.narrative_roles_used()
    assert "hook" in roles
    assert "problem" in roles
    assert "agitation" in roles
    assert "psychology" in roles
    assert "solution" in roles
    assert "biblical_grounding" in roles
    assert "reality" in roles
    assert "hope" in roles
    assert "callout" in roles
    print(f"  PASS — Arco completo: {len(roles)} roles narrativos")


def test_no_invented_biblical_citations():
    """TEST 15: No hay citas bíblicas inventadas como textuales."""
    plan = plan_relacion_destructiva()
    for scene in plan.scenes:
        # No debe contener comillas latinas (cita textual)
        if "«" in scene.narration and "»" in scene.narration:
            # Si hay cita, debe ser genérica, no específica
            assert "salmo" not in scene.narration.lower() or \
                   "conócerte" in scene.narration.lower(), \
                f"Cita bíblica potencialmente inventada en {scene.scene_id}"
    print("  PASS — Sin citas bíblicas inventadas como textuales")


def test_continuity_groups():
    """TEST 16: continuity_groups están presentes y son coherentes."""
    plan = plan_relacion_destructiva()
    groups = plan.continuity_groups()
    assert len(groups) >= 2
    # Las primeras escenas deben estar en el mismo grupo
    assert plan.scenes[0].continuity_group == plan.scenes[1].continuity_group
    print(f"  PASS — {len(groups)} continuity groups: {groups}")


def test_narrative_roles_used():
    """TEST 17: narrative_roles_used() devuelve los roles correctos."""
    plan = plan_relacion_destructiva()
    roles = plan.narrative_roles_used()
    assert isinstance(roles, list)
    assert all(isinstance(r, str) for r in roles)
    assert len(roles) == len(plan.scenes)
    print(f"  PASS — {len(roles)} roles usados")


def test_plan_stats():
    """TEST 18: Stats del plan son consistentes."""
    plan = plan_relacion_destructiva()
    result = validate_plan(plan)
    stats = result["stats"]
    assert stats["total_duration"] > 0
    assert stats["scene_count"] == len(plan.scenes)
    assert stats["avg_scene_duration"] > 0
    assert len(stats["roles_used"]) == len(plan.scenes)
    print(f"  PASS — Stats: {stats['scene_count']} escenas, {stats['total_duration']}s total")


# ─────────────────────────────────────────
# Runner
# ─────────────────────────────────────────

def main():
    tests = [
        test_create_short_plan,
        test_build_scene,
        test_scene_brief_valid,
        test_hook_generation,
        test_hook_selection,
        test_validate_plan_valid,
        test_validate_plan_invalid,
        test_serialization_roundtrip,
        test_json_roundtrip,
        test_duration_estimation,
        test_spanish_neutral,
        test_invalid_scene_detection,
        test_cta_present,
        test_relacion_destructiva_arc,
        test_no_invented_biblical_citations,
        test_continuity_groups,
        test_narrative_roles_used,
        test_plan_stats,
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("TESTS — short_director.py")
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
