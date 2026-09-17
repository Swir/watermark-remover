from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class Area:
    x: int
    y: int
    width: int
    height: int

    def normalized(self) -> "Area":
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        return Area(int(x), int(y), max(1, int(w)), max(1, int(h)))

    def clamp(self, frame_width: int, frame_height: int) -> "Area | None":
        a = self.normalized()
        x1 = max(0, min(frame_width, a.x))
        y1 = max(0, min(frame_height, a.y))
        x2 = max(0, min(frame_width, a.x + a.width))
        y2 = max(0, min(frame_height, a.y + a.height))
        if x2 <= x1 or y2 <= y1:
            return None
        return Area(x1, y1, x2 - x1, y2 - y1)

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Area":
        return cls(
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            width=int(data.get("width", data.get("w", 1))),
            height=int(data.get("height", data.get("h", 1))),
        ).normalized()


@dataclass(slots=True)
class ProcessingOptions:
    method: str = "mixed"
    radius: int = 7
    margin: int = 12
    feather: int = 5
    smoothing: int = 0
    denoise: bool = False
    sharpen: bool = False
    color_correction: bool = False
    preserve_audio: bool = True
    output_quality: str = "high"
    video_codec: str = "mp4v"
    worker_count: int = 4
    hardware_acceleration: bool = True
    buffering: bool = True

    def validate(self) -> None:
        if self.method not in {"mixed", "telea", "ns"}:
            raise ValueError("Unsupported inpainting method")
        self.radius = max(1, min(25, int(self.radius)))
        self.margin = max(0, min(100, int(self.margin)))
        self.feather = max(0, min(31, int(self.feather)))
        if self.feather % 2 == 0 and self.feather > 0:
            self.feather += 1
        self.smoothing = max(0, min(31, int(self.smoothing)))
        if self.output_quality not in {"fast", "balanced", "high"}:
            self.output_quality = "high"
        if self.video_codec not in {"mp4v", "h264", "xvid"}:
            self.video_codec = "mp4v"
        self.worker_count = max(1, min(8, int(self.worker_count)))
        self.hardware_acceleration = bool(self.hardware_acceleration)
        self.buffering = bool(self.buffering)

    def video_extension(self) -> str:
        self.validate()
        return ".avi" if self.video_codec == "xvid" else ".mp4"


@dataclass(slots=True)
class Job:
    source: Path
    destination: Path
    areas: list[Area]
    options: ProcessingOptions


def corner_areas(
    width: int,
    height: int,
    corners: Iterable[str],
    fraction: float = 0.22,
) -> list[Area]:
    fraction = max(0.05, min(0.5, float(fraction)))
    w = max(1, round(width * fraction))
    h = max(1, round(height * fraction))
    mapping = {
        "top_left": Area(0, 0, w, h),
        "top_right": Area(width - w, 0, w, h),
        "bottom_left": Area(0, height - h, w, h),
        "bottom_right": Area(width - w, height - h, w, h),
    }
    return [mapping[name] for name in corners if name in mapping]
