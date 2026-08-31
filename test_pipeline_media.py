def test_media_utils_smoke():
    import pipeline.media as pm

    assert pm.norm("¿Qué pasa? ") == "quépasa"
    assert pm.run is not None


def test_media_generate_bgm_creates_file(tmp_path):
    import pipeline.media as pm

    out = tmp_path / "bgm.wav"
    pm.generate_bgm(str(out), duration=1)
    assert out.exists()
    assert out.stat().st_size > 1000
