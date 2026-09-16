from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable

import cv2

from .engine import process_frame
from .models import Area, ProcessingOptions

Progress = Callable[[float, str], None]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"}


def media_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS: return "image"
    if suffix in VIDEO_EXTENSIONS: return "video"
    raise ValueError(f"Unsupported file type: {suffix or '<none>'}")


def first_frame(path: Path):
    kind = media_kind(path)
    if kind == "image":
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    else:
        cap = cv2.VideoCapture(str(path)); ok, frame = cap.read(); cap.release()
        if not ok: frame = None
    if frame is None: raise RuntimeError(f"Cannot read {path.name}")
    return frame


def process_image(source: Path, destination: Path, areas: list[Area], options: ProcessingOptions) -> None:
    frame = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if frame is None: raise RuntimeError(f"Cannot open image: {source}")
    result = process_frame(frame, areas, options)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), result): raise RuntimeError(f"Cannot write image: {destination}")


def _fourcc_for(path: Path) -> int:
    return cv2.VideoWriter_fourcc(*("mp4v" if path.suffix.lower() in {".mp4", ".m4v", ".mov"} else "MJPG"))


def _ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def _remux_audio(processed: Path, original: Path, destination: Path) -> bool:
    ffmpeg = _ffmpeg_exe()
    if not ffmpeg: return False
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(processed), "-i", str(original),
           "-map", "0:v:0", "-map", "1:a?", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(destination)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0 and destination.exists() and destination.stat().st_size > 0: return True
        logging.warning("Audio remux failed: %s", result.stderr[-1000:])
    except (OSError, subprocess.SubprocessError) as exc:
        logging.warning("Audio remux unavailable: %s", exc)
    return False


def process_video(source: Path, destination: Path, areas: list[Area], options: ProcessingOptions,
                  cancel_event: threading.Event | None = None, progress: Progress | None = None) -> None:
    cancel_event = cancel_event or threading.Event()
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened(): raise RuntimeError(f"Cannot open video: {source}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if width <= 0 or height <= 0:
        cap.release(); raise RuntimeError("Invalid video dimensions")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wmr_v2_") as temp_dir:
        temp_video = Path(temp_dir) / ("processed.mp4" if destination.suffix.lower() in {".mp4", ".mov", ".m4v"} else "processed.avi")
        writer = cv2.VideoWriter(str(temp_video), _fourcc_for(temp_video), fps, (width, height))
        if not writer.isOpened(): cap.release(); raise RuntimeError("Cannot initialize video encoder")
        index = 0
        try:
            while True:
                if cancel_event.is_set(): raise InterruptedError("Processing cancelled")
                ok, frame = cap.read()
                if not ok: break
                writer.write(process_frame(frame, areas, options)); index += 1
                if progress and (index == 1 or index % 5 == 0):
                    ratio = index / frame_count if frame_count > 0 else 0.0
                    progress(min(0.99, ratio), f"{index}/{frame_count or '?'}")
        finally:
            cap.release(); writer.release()
        if index == 0 or not temp_video.exists() or temp_video.stat().st_size == 0: raise RuntimeError("No frames were written")
        destination.unlink(missing_ok=True)
        if options.preserve_audio and destination.suffix.lower() in {".mp4", ".mov", ".m4v"}:
            if not _remux_audio(temp_video, source, destination): shutil.copy2(temp_video, destination)
        else:
            shutil.copy2(temp_video, destination)
        if progress: progress(1.0, "done")


def process_media(source: Path, destination: Path, areas: list[Area], options: ProcessingOptions,
                  cancel_event: threading.Event | None = None, progress: Progress | None = None) -> None:
    if media_kind(source) == "image":
        if cancel_event and cancel_event.is_set(): raise InterruptedError("Processing cancelled")
        process_image(source, destination, areas, options)
        if progress: progress(1.0, "done")
    else:
        process_video(source, destination, areas, options, cancel_event, progress)
