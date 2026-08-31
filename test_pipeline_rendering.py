import sys

sys.path.insert(0, ".")


def test_pipeline_rendering_module_imports():
    import pipeline.rendering as pr

    assert hasattr(pr, "render_scene")
    assert hasattr(pr, "render_scene_video")
    assert hasattr(pr, "render_scene_draw")
    assert hasattr(pr, "render_pipeline")
    assert hasattr(pr, "parse_html_emphasis")
    assert hasattr(pr, "_layout_karaoke")


def test_rendering_parse_html_emphasis():
    import pipeline.rendering as pr

    clean, emphasis = pr.parse_html_emphasis("hola <strong>mundo</strong> y <em>tu</em>")
    assert clean == "hola mundo y tu"
    assert emphasis[1] == "strong"
    assert emphasis[3] == "em"
