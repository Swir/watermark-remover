import cv2
import numpy as np
from watermark_remover.engine import build_mask, process_frame
from watermark_remover.models import Area, ProcessingOptions

def sample_image():
    img=np.zeros((140,220,3),dtype=np.uint8)
    for x in range(img.shape[1]): img[:,x]=(40+x//3,70+x//5,110+x//6)
    cv2.rectangle(img,(85,48),(135,92),(255,255,255),-1); cv2.putText(img,"WM",(91,78),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,0,0),2,cv2.LINE_AA); return img

def test_mask_is_bounded():
    mask=build_mask((100,100,3),[Area(-10,-10,30,30)],margin=3,feather=0); assert mask.shape==(100,100); assert mask[0,0]==255; assert mask[25,25]==0

def test_process_frame_preserves_shape_and_changes_target():
    img=sample_image(); result=process_frame(img,[Area(85,48,51,45)],ProcessingOptions(method="telea",radius=5,margin=2)); assert result.shape==img.shape and result.dtype==img.dtype
    target=np.mean(np.abs(result[48:93,85:136].astype(np.int16)-img[48:93,85:136].astype(np.int16))); outside=np.mean(np.abs(result[:30,:30].astype(np.int16)-img[:30,:30].astype(np.int16))); assert target>3 and outside<0.5

def test_empty_area_returns_copy():
    img=sample_image(); result=process_frame(img,[],ProcessingOptions()); assert np.array_equal(img,result) and result is not img
