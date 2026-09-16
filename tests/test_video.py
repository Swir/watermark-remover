from pathlib import Path
import cv2
import numpy as np
import pytest
from watermark_remover.models import Area, ProcessingOptions
from watermark_remover.video import first_frame, media_kind, process_image

def test_media_kind():
    assert media_kind(Path("photo.png"))=="image"; assert media_kind(Path("movie.mp4"))=="video"
    with pytest.raises(ValueError): media_kind(Path("notes.exe"))

def test_image_pipeline(tmp_path: Path):
    source=tmp_path/"source.png"; destination=tmp_path/"result.png"; frame=np.full((80,120,3),(70,100,140),dtype=np.uint8); cv2.rectangle(frame,(45,25),(75,55),(255,255,255),-1); assert cv2.imwrite(str(source),frame)
    assert first_frame(source).shape==frame.shape; process_image(source,destination,[Area(45,25,31,31)],ProcessingOptions(method="telea",radius=3)); result=cv2.imread(str(destination)); assert destination.exists() and result is not None and result.shape==frame.shape
