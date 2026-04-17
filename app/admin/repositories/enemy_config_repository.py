from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EnemyConfigRepository:
    def __init__(self, base_path: Path | str | None = None) -> None:
        root = Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        self._config_dir = root / "config" / "battle"
        self._enemies_path = self._config_dir / "enemies.json"

    def load(self) -> dict[str, list[dict[str, Any]]]:
        self._ensure_file_exists()
        return {"items": self._read_json(self._enemies_path)}

    def save(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self._enemies_path, payload.get("items", []))

    def _ensure_file_exists(self) -> None:
        if self._enemies_path.exists():
            return
        self.save({"items": []})

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: Path, value: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
