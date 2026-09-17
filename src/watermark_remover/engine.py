from __future__ import annotations

from collections.abc import Iterable

import cv2
import numpy as np

from .models import Area, ProcessingOptions


def build_mask(shape: tuple[int, ...], areas: Iterable[Area], margin: int = 0, feather: int = 0) -> np.ndarray:
    height, width = shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    margin = max(0, int(margin))
    for area in areas:
        clamped = area.clamp(width, height)
        if clamped is None:
            continue
        x1 = max(0, clamped.x - margin); y1 = max(0, clamped.y - margin)
        x2 = min(width, clamped.x + clamped.width + margin); y2 = min(height, clamped.y + clamped.height + margin)
        cv2.rectangle(mask, (x1, y1), (max(x1, x2 - 1), max(y1, y2 - 1)), 255, thickness=-1)
    feather = max(0, int(feather))
    if feather:
        if feather % 2 == 0: feather += 1
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=max(1, feather // 5))
        mask = cv2.GaussianBlur(mask, (feather, feather), 0)
        _, mask = cv2.threshold(mask, 24, 255, cv2.THRESH_BINARY)
    return mask


def _choose_method(frame: np.ndarray, mask: np.ndarray, requested: str) -> int:
    if requested == "telea": return cv2.INPAINT_TELEA
    if requested == "ns": return cv2.INPAINT_NS
    ys, xs = np.where(mask > 0)
    if xs.size == 0: return cv2.INPAINT_TELEA
    x1, x2 = max(0, xs.min() - 12), min(frame.shape[1], xs.max() + 13)
    y1, y2 = max(0, ys.min() - 12), min(frame.shape[0], ys.max() + 13)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0: return cv2.INPAINT_TELEA
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    texture = float(np.std(cv2.Laplacian(gray, cv2.CV_32F)))
    return cv2.INPAINT_TELEA if texture >= 16.0 else cv2.INPAINT_NS


def _auto_color_correct(frame: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _sharpen(frame: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(frame, (0, 0), 1.2)
    return cv2.addWeighted(frame, 1.35, blur, -0.35, 0)


def _smooth_repaired_region(frame: np.ndarray, mask: np.ndarray, strength: int) -> np.ndarray:
    strength = max(0, min(31, int(strength)))
    if strength <= 1:
        return frame
    filtered = cv2.bilateralFilter(frame, d=strength, sigmaColor=100, sigmaSpace=100)
    alpha = (mask.astype(np.float32) / 255.0)[..., None]
    blended = frame.astype(np.float32) * (1.0 - alpha) + filtered.astype(np.float32) * alpha
    return np.clip(blended, 0, 255).astype(np.uint8)


def process_frame(frame: np.ndarray, areas: Iterable[Area], options: ProcessingOptions) -> np.ndarray:
    if frame is None or frame.size == 0: raise ValueError("Frame is empty")
    options.validate(); areas = list(areas)
    if not areas: return frame.copy()
    mask = build_mask(frame.shape, areas, options.margin, options.feather)
    if not np.any(mask): return frame.copy()
    result = cv2.inpaint(frame, mask, float(options.radius), _choose_method(frame, mask, options.method))
    result = _smooth_repaired_region(result, mask, options.smoothing)
    if options.denoise: result = cv2.fastNlMeansDenoisingColored(result, None, 3, 3, 7, 21)
    if options.sharpen: result = _sharpen(result)
    if options.color_correction: result = _auto_color_correct(result)
    return result
