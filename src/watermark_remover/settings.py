from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .i18n import detect_language
from .models import Area, ProcessingOptions


def app_data_dir() -> Path:
    base = Path.home() / ".watermark_remover_pro"
    base.mkdir(parents=True, exist_ok=True)
    return base


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_data_dir() / "settings.json"

    def load(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "language": detect_language(), "output_dir": str(Path.home() / "Videos"),
            "last_options": asdict(ProcessingOptions()), "areas": [],
        }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict): defaults.update(data)
        except (OSError, json.JSONDecodeError):
            pass
        return defaults

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    @staticmethod
    def areas_from(data: Any) -> list[Area]:
        if not isinstance(data, list): return []
        result: list[Area] = []
        for item in data:
            if isinstance(item, dict):
                try: result.append(Area.from_dict(item))
                except (TypeError, ValueError): continue
        return result
