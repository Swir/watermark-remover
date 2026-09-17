from pathlib import Path

import cv2
import numpy as np
import pytest

from watermark_remover.models import Area, ProcessingOptions
from watermark_remover.video import (
    _codec_candidates,
    _image_write_params,
    first_frame,
    media_kind,
    process_image,
)


def test_media_kind():
    assert media_kind(Path("photo.png")) == "image"
    assert media_kind(Path("movie.mp4")) == "video"
    with pytest.raises(ValueError):
        media_kind(Path("notes.exe"))


def test_image_pipeline(tmp_path: Path):
    source = tmp_path / "source.png"
    destination = tmp_path / "result.png"
    frame = np.full((80, 120, 3), (70, 100, 140), dtype=np.uint8)
    cv2.rectangle(frame, (45, 25), (75, 55), (255, 255, 255), -1)
    assert cv2.imwrite(str(source), frame)
    assert first_frame(source).shape == frame.shape
    process_image(
        source,
        destination,
        [Area(45, 25, 31, 31)],
        ProcessingOptions(method="telea", radius=3, output_quality="high"),
    )
    result = cv2.imread(str(destination))
    assert destination.exists() and result is not None and result.shape == frame.shape


def test_quality_presets_generate_real_image_encoder_parameters():
    fast = _image_write_params(Path("out.jpg"), "fast")
    high = _image_write_params(Path("out.jpg"), "high")
    assert fast[0] == cv2.IMWRITE_JPEG_QUALITY
    assert high[0] == cv2.IMWRITE_JPEG_QUALITY
    assert fast[1] < high[1]


def test_codec_fallback_order_preserves_legacy_choices():
    assert _codec_candidates("mp4v", ".mp4") == ["mp4v"]
    assert _codec_candidates("h264", ".mp4")[-1] == "mp4v"
    assert _codec_candidates("xvid", ".avi") == ["XVID", "MJPG"]
