from __future__ import annotations

from pathlib import Path

from app.admin.repositories.equipment_config_repository import EquipmentConfigRepository
from app.admin.services.equipment_validation_service import validate_equipment_config
from app.core_loop.types import NotFoundError


class EquipmentAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = EquipmentConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_items(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        return {
            "items": sorted(
                payload["items"],
                key=lambda item: (
                    _slot_sort_index(str(item.get("slot", ""))),
                    str(item.get("equipment_id", "")),
                ),
            )
        }

    def get_item(self, equipment_id: str) -> dict[str, object]:
        item = self._find_item(equipment_id)
        if item is None:
            raise NotFoundError(f"equipment '{equipment_id}' not found")
        return item

    def create_item(self, item_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        equipment_id = str(item_payload.get("equipment_id", "")).strip()
        if not equipment_id:
            raise ValueError("equipment_id is required")
        if any(str(item.get("equipment_id", "")) == equipment_id for item in payload["items"]):
            raise ValueError(f"equipment '{equipment_id}' already exists")
        payload["items"].append(dict(item_payload))
        self._save_payload(payload)
        return self.get_item(equipment_id)

    def update_item(self, equipment_id: str, item_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        index = self._find_item_index(payload["items"], equipment_id)
        if index is None:
            raise NotFoundError(f"equipment '{equipment_id}' not found")

        normalized_equipment_id = str(item_payload.get("equipment_id", "")).strip()
        if normalized_equipment_id and normalized_equipment_id != equipment_id:
            raise ValueError("equipment_id is immutable")

        next_item = dict(item_payload)
        next_item["equipment_id"] = equipment_id
        payload["items"][index] = next_item
        self._save_payload(payload)
        return self.get_item(equipment_id)

    def delete_item(self, equipment_id: str) -> None:
        payload = self._repository.load()
        before_count = len(payload["items"])
        payload["items"] = [
            item for item in payload["items"] if str(item.get("equipment_id", "")) != equipment_id
        ]
        if len(payload["items"]) == before_count:
            raise NotFoundError(f"equipment '{equipment_id}' not found")
        self._repository.save(payload)

    def validate_current_config(self):
        payload = self._repository.load()
        return validate_equipment_config(items=payload["items"])

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        validation_result = validate_equipment_config(items=payload["items"])
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid equipment config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_equipment_config(equipment_config_base_path=str(self._base_path))
        return {"reloaded": True, "equipment_count": len(payload["items"])}

    def _save_payload(self, payload: dict[str, list[dict[str, object]]]) -> None:
        validation_result = validate_equipment_config(items=payload["items"])
        if not validation_result.is_valid:
            raise ValueError("; ".join(validation_result.errors))
        self._repository.save(payload)

    def _find_item(self, equipment_id: str) -> dict[str, object] | None:
        payload = self._repository.load()
        return next(
            (
                item
                for item in payload["items"]
                if str(item.get("equipment_id", "")) == equipment_id
            ),
            None,
        )

    def _find_item_index(
        self,
        items: list[dict[str, object]],
        equipment_id: str,
    ) -> int | None:
        for index, item in enumerate(items):
            if str(item.get("equipment_id", "")) == equipment_id:
                return index
        return None


def _slot_sort_index(slot: str) -> int:
    return {"weapon": 0, "armor": 1, "accessory": 2, "artifact": 3}.get(slot, 99)
