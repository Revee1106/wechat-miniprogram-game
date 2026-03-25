from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EventConfigRepository:
    def __init__(self, base_path: Path | str | None = None) -> None:
        root = Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        self._events_dir = root / "config" / "events"
        self._templates_path = self._events_dir / "templates.json"
        self._options_path = self._events_dir / "options.json"

    def load(self) -> dict[str, list[dict[str, Any]]]:
        self._ensure_files_exist()
        return {
            "templates": self._read_json(self._templates_path),
            "options": self._read_json(self._options_path),
        }

    def save(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self._events_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self._templates_path, payload.get("templates", []))
        self._write_json(self._options_path, payload.get("options", []))

    def _ensure_files_exist(self) -> None:
        if self._templates_path.exists() and self._options_path.exists():
            return
        self.save({"templates": [], "options": []})

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: Path, value: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
