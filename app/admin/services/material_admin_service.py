from __future__ import annotations

from pathlib import Path

from app.admin.repositories.material_config_repository import MaterialConfigRepository
from app.admin.services.material_validation_service import validate_material_config
from app.core_loop.types import NotFoundError


class MaterialAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = MaterialConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_items(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        return {
            "items": sorted(
                payload["items"],
                key=lambda item: (
                    str(item.get("source", "")),
                    str(item.get("category", "")),
                    int(item.get("tier", 0) or 0),
                    str(item.get("material_id", "")),
                ),
            )
        }

    def get_item(self, material_id: str) -> dict[str, object]:
        item = self._find_item(material_id)
        if item is None:
            raise NotFoundError(f"material '{material_id}' not found")
        return item

    def create_item(self, item_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        material_id = str(item_payload.get("material_id", "")).strip()
        if not material_id:
            raise ValueError("material_id is required")
        if any(str(item.get("material_id", "")) == material_id for item in payload["items"]):
            raise ValueError(f"material '{material_id}' already exists")
        payload["items"].append(dict(item_payload))
        self._save_payload(payload)
        return self.get_item(material_id)

    def update_item(self, material_id: str, item_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        index = self._find_item_index(payload["items"], material_id)
        if index is None:
            raise NotFoundError(f"material '{material_id}' not found")

        normalized_material_id = str(item_payload.get("material_id", "")).strip()
        if normalized_material_id and normalized_material_id != material_id:
            raise ValueError("material_id is immutable")

        next_item = dict(item_payload)
        next_item["material_id"] = material_id
        payload["items"][index] = next_item
        self._save_payload(payload)
        return self.get_item(material_id)

    def delete_item(self, material_id: str) -> None:
        payload = self._repository.load()
        before_count = len(payload["items"])
        payload["items"] = [
            item for item in payload["items"] if str(item.get("material_id", "")) != material_id
        ]
        if len(payload["items"]) == before_count:
            raise NotFoundError(f"material '{material_id}' not found")
        self._repository.save(payload)

    def validate_current_config(self):
        payload = self._repository.load()
        return validate_material_config(items=payload["items"])

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        validation_result = validate_material_config(items=payload["items"])
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid material config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_material_config(material_config_base_path=str(self._base_path))
        return {"reloaded": True, "material_count": len(payload["items"])}

    def _save_payload(self, payload: dict[str, list[dict[str, object]]]) -> None:
        validation_result = validate_material_config(items=payload["items"])
        if not validation_result.is_valid:
            raise ValueError("; ".join(validation_result.errors))
        self._repository.save(payload)

    def _find_item(self, material_id: str) -> dict[str, object] | None:
        payload = self._repository.load()
        return next(
            (
                item
                for item in payload["items"]
                if str(item.get("material_id", "")) == material_id
            ),
            None,
        )

    def _find_item_index(
        self,
        items: list[dict[str, object]],
        material_id: str,
    ) -> int | None:
        for index, item in enumerate(items):
            if str(item.get("material_id", "")) == material_id:
                return index
        return None
