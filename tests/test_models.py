from watermark_remover.models import Area, ProcessingOptions, corner_areas


def test_area_normalize_and_clamp():
    assert Area(20, 20, -10, -5).normalized() == Area(10, 15, 10, 5)
    assert Area(-5, -5, 20, 20).clamp(10, 10) == Area(0, 0, 10, 10)
    assert Area(20, 20, 5, 5).clamp(10, 10) is None


def test_corner_areas():
    assert corner_areas(1000, 500, ["top_left", "bottom_right"], 0.2) == [
        Area(0, 0, 200, 100),
        Area(800, 400, 200, 100),
    ]


def test_options_validation_restored_performance_controls():
    options = ProcessingOptions(
        method="mixed",
        radius=99,
        margin=-1,
        feather=4,
        smoothing=99,
        video_codec="unknown",
        worker_count=99,
    )
    options.validate()
    assert options.radius == 25
    assert options.margin == 0
    assert options.feather == 5
    assert options.smoothing == 31
    assert options.video_codec == "mp4v"
    assert options.worker_count == 8


def test_video_extension_matches_codec():
    assert ProcessingOptions(video_codec="mp4v").video_extension() == ".mp4"
    assert ProcessingOptions(video_codec="h264").video_extension() == ".mp4"
    assert ProcessingOptions(video_codec="xvid").video_extension() == ".avi"
