from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
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
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    raise ValueError(f"Unsupported file type: {suffix or '<none>'}")


def _open_capture(path: Path, hardware_acceleration: bool = False) -> cv2.VideoCapture:
    if hardware_acceleration and hasattr(cv2, "VIDEO_ACCELERATION_ANY"):
        try:
            cap = cv2.VideoCapture(
                str(path),
                cv2.CAP_FFMPEG,
                [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY],
            )
            if cap.isOpened():
                logging.info("Opened %s with requested hardware acceleration", path.name)
                return cap
            cap.release()
        except (cv2.error, TypeError):
            logging.info("Hardware accelerated open is unavailable for %s; falling back", path.name)
    return cv2.VideoCapture(str(path))


def first_frame(path: Path):
    kind = media_kind(path)
    if kind == "image":
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    else:
        cap = _open_capture(path, False)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            frame = None
    if frame is None:
        raise RuntimeError(f"Cannot read {path.name}")
    return frame


def _image_write_params(destination: Path, quality: str) -> list[int]:
    quality = quality if quality in {"fast", "balanced", "high"} else "high"
    suffix = destination.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        value = {"fast": 88, "balanced": 94, "high": 98}[quality]
        return [cv2.IMWRITE_JPEG_QUALITY, value]
    if suffix == ".png":
        value = {"fast": 6, "balanced": 3, "high": 1}[quality]
        return [cv2.IMWRITE_PNG_COMPRESSION, value]
    if suffix == ".webp" and hasattr(cv2, "IMWRITE_WEBP_QUALITY"):
        value = {"fast": 88, "balanced": 94, "high": 98}[quality]
        return [cv2.IMWRITE_WEBP_QUALITY, value]
    return []


def process_image(source: Path, destination: Path, areas: list[Area], options: ProcessingOptions) -> None:
    options.validate()
    frame = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"Cannot open image: {source}")
    result = process_frame(frame, areas, options)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), result, _image_write_params(destination, options.output_quality)):
        raise RuntimeError(f"Cannot write image: {destination}")


def _codec_candidates(codec: str, suffix: str) -> list[str]:
    if codec == "h264":
        return ["H264", "avc1", "mp4v"]
    if codec == "xvid":
        return ["XVID", "MJPG"]
    if suffix.lower() == ".avi":
        return ["XVID", "MJPG"]
    return ["mp4v"]


def _open_writer(path: Path, codec: str, fps: float, size: tuple[int, int]) -> tuple[cv2.VideoWriter, str]:
    for candidate in _codec_candidates(codec, path.suffix):
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*candidate), fps, size)
        if writer.isOpened():
            if candidate.lower() != codec.lower():
                logging.warning("Requested video codec %s unavailable; using %s", codec, candidate)
            return writer, candidate
        writer.release()
    raise RuntimeError(f"Cannot initialize video encoder for codec {codec}")


def _ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def _remux_audio(processed: Path, original: Path, destination: Path) -> bool:
    ffmpeg = _ffmpeg_exe()
    if not ffmpeg:
        return False
    cmd = [
        ffmpeg, "-y", "-loglevel", "error", "-i", str(processed), "-i", str(original),
        "-map", "0:v:0", "-map", "1:a?", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(destination),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0 and destination.exists() and destination.stat().st_size > 0:
            return True
        logging.warning("Audio remux failed: %s", result.stderr[-1000:])
    except (OSError, subprocess.SubprocessError) as exc:
        logging.warning("Audio remux unavailable: %s", exc)
    return False


def _write_completed(
    pending: list[tuple[int, Future]],
    writer: cv2.VideoWriter,
    count: int,
    frame_count: int,
    cancel_event: threading.Event,
    progress: Progress | None,
    flush_all: bool = False,
) -> int:
    while pending and (flush_all or len(pending) >= count):
        if cancel_event.is_set():
            raise InterruptedError("Processing cancelled")
        index, future = pending.pop(0)
        writer.write(future.result())
        completed = index + 1
        if progress and (completed == 1 or completed % 5 == 0 or completed == frame_count):
            ratio = completed / frame_count if frame_count > 0 else 0.0
            progress(min(0.99, ratio), f"{completed}/{frame_count or '?'}")
    return len(pending)


def process_video(
    source: Path,
    destination: Path,
    areas: list[Area],
    options: ProcessingOptions,
    cancel_event: threading.Event | None = None,
    progress: Progress | None = None,
) -> None:
    cancel_event = cancel_event or threading.Event()
    options.validate()
    cap = _open_capture(source, options.hardware_acceleration)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {source}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError("Invalid video dimensions")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_suffix = options.video_extension()
    with tempfile.TemporaryDirectory(prefix="wmr_v21_") as temp_dir:
        temp_video = Path(temp_dir) / f"processed{temp_suffix}"
        writer, actual_codec = _open_writer(temp_video, options.video_codec, fps, (width, height))
        logging.info(
            "Processing %s with codec=%s workers=%d buffering=%s hw_accel=%s",
            source.name, actual_codec, options.worker_count, options.buffering, options.hardware_acceleration,
        )
        submitted = 0
        buffer_limit = max(options.worker_count, 10 if options.buffering else options.worker_count)
        pending: list[tuple[int, Future]] = []
        executor = ThreadPoolExecutor(max_workers=options.worker_count, thread_name_prefix="wmr-frame")
        try:
            while True:
                if cancel_event.is_set():
                    raise InterruptedError("Processing cancelled")
                ok, frame = cap.read()
                if not ok:
                    break
                pending.append((submitted, executor.submit(process_frame, frame, areas, options)))
                submitted += 1
                if len(pending) >= buffer_limit:
                    _write_completed(pending, writer, buffer_limit, frame_count, cancel_event, progress)
            _write_completed(pending, writer, 1, frame_count, cancel_event, progress, flush_all=True)
        finally:
            cap.release()
            writer.release()
            executor.shutdown(wait=True, cancel_futures=cancel_event.is_set())

        if submitted == 0 or not temp_video.exists() or temp_video.stat().st_size == 0:
            raise RuntimeError("No frames were written")
        destination.unlink(missing_ok=True)
        if options.preserve_audio and destination.suffix.lower() in {".mp4", ".mov", ".m4v"}:
            if not _remux_audio(temp_video, source, destination):
                shutil.copy2(temp_video, destination)
        else:
            shutil.copy2(temp_video, destination)
        if progress:
            progress(1.0, "done")


def process_media(
    source: Path,
    destination: Path,
    areas: list[Area],
    options: ProcessingOptions,
    cancel_event: threading.Event | None = None,
    progress: Progress | None = None,
) -> None:
    if media_kind(source) == "image":
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Processing cancelled")
        process_image(source, destination, areas, options)
        if progress:
            progress(1.0, "done")
    else:
        process_video(source, destination, areas, options, cancel_event, progress)
