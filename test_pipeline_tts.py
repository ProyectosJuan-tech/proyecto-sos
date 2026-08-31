import sys

sys.path.insert(0, ".")


def test_pipeline_tts_module_imports():
    import pipeline.tts as ptts

    assert hasattr(ptts, "has_pauses")
    assert hasattr(ptts, "split_pauses")
    assert hasattr(ptts, "tts_audio")
    assert hasattr(ptts, "align_words")
    assert hasattr(ptts, "mix_boom")


def test_hacer_video_caverna_compat_wrappers():
    import hacer_video_caverna as m

    assert callable(m.has_pauses)
    assert callable(m.split_pauses)
    assert callable(m.tts_audio)
    assert callable(m.align_words)
    assert callable(m.mix_boom)


def test_scene_generation_module_imports():
    import pipeline.scene_generation as psg

    assert hasattr(psg, "strip_img_metadata")
    assert hasattr(psg, "find_local_img")
    assert hasattr(psg, "find_local_video")
    assert hasattr(psg, "download_image")
