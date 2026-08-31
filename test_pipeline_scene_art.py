def test_scene_art_build_bg_smoke():
    from PIL import Image

    import pipeline.scene_art as sa

    src = Image.new("RGB", (2000, 3000), (120, 110, 100))
    src_path = "/tmp/scene_art_src.jpg"
    out_path = "/tmp/scene_art_bg.jpg"
    src.save(src_path)

    sa.build_bg(src_path, out_path)
    img = Image.open(out_path)
    assert img.size == (1080, 1920)
    assert img.mode == "RGB"


def test_scene_art_make_walking_smoke():
    import pipeline.scene_art as sa

    out = "/tmp/scene_art_walking.jpg"
    sa.make_walking(out)
    from PIL import Image
    img = Image.open(out)
    assert img.size == (1080, 1920)
