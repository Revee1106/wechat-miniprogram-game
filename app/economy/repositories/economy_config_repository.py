from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EconomyConfigRepository:
    def __init__(self, base_path: Path | str | None = None) -> None:
        root = Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        self._economy_dir = root / "config" / "economy"
        self._resources_path = self._economy_dir / "resources.json"
        self._settlement_path = self._economy_dir / "settlement.json"

    def load_resources(self) -> dict[str, Any]:
        self._ensure_files_exist()
        return {"resources": self._read_json(self._resources_path)}

    def save_resources(self, payload: dict[str, Any]) -> None:
        self._economy_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self._resources_path, payload.get("resources", []))

    def load_settlement(self) -> dict[str, Any]:
        self._ensure_files_exist()
        return self._read_object(self._settlement_path)

    def save_settlement(self, payload: dict[str, Any]) -> None:
        self._economy_dir.mkdir(parents=True, exist_ok=True)
        self._write_object(self._settlement_path, payload)

    def _ensure_files_exist(self) -> None:
        if not self._resources_path.exists():
            self.save_resources({"resources": []})
        if not self._settlement_path.exists():
            self.save_settlement({"weights": {}})

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: Path, value: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)

    def _read_object(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_object(self, path: Path, value: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
