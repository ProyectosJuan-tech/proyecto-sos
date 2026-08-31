def test_visual_parse_html_emphasis():
    import pipeline.visual as pv

    clean, emphasis = pv.parse_html_emphasis("hola <strong>mundo</strong> y <em>tu</em>")
    assert clean == "hola mundo y tu"
    assert emphasis[1] == "strong"
    assert emphasis[3] == "em"


def test_visual_resolve_visual_adds_defaults():
    import pipeline.visual as pv

    scene = {
        "text": "Necesitas integrar.",
        "visual": {
            "type": "object_closeup",
            "subject": "woman hands",
            "action": "holding old book",
            "mood": "reflective",
        },
        "emphasis": ["integrar"],
    }

    out = pv.resolve_visual(scene)
    assert out["ai"].startswith("woman hands")
    assert out["motion"] == "zoom-in"
    assert "<strong>integrar</strong>" in out["text"]
