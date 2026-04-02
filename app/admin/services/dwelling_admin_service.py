from __future__ import annotations

from pathlib import Path

from app.admin.repositories.dwelling_config_repository import DwellingConfigRepository
from app.admin.services.dwelling_validation_service import validate_dwelling_config
from app.core_loop.types import NotFoundError


class DwellingAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = DwellingConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_facilities(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        return {
            "items": [
                {
                    "facility_id": str(facility.get("facility_id", "")),
                    "display_name": str(facility.get("display_name", "")),
                    "facility_type": str(facility.get("facility_type", "")),
                    "summary": str(facility.get("summary", "")),
                    "max_level": len(list(facility.get("levels", []))),
                    "level_count": len(list(facility.get("levels", []))),
                }
                for facility in payload["facilities"]
            ]
        }

    def get_facility(self, facility_id: str) -> dict[str, object]:
        facility = self._find_facility(facility_id)
        if facility is None:
            raise NotFoundError(f"dwelling facility '{facility_id}' not found")
        return facility

    def update_facility(
        self,
        facility_id: str,
        facility_payload: dict[str, object],
    ) -> dict[str, object]:
        payload = self._repository.load()
        index = self._find_facility_index(payload["facilities"], facility_id)
        if index is None:
            raise NotFoundError(f"dwelling facility '{facility_id}' not found")

        normalized_facility_id = str(facility_payload.get("facility_id", "")).strip()
        if normalized_facility_id and normalized_facility_id != facility_id:
            raise ValueError("facility_id is immutable")

        next_facility = dict(facility_payload)
        next_facility["facility_id"] = facility_id
        payload["facilities"][index] = next_facility
        self._save_payload(payload)
        return self._find_facility(facility_id) or {}

    def validate_current_config(self):
        payload = self._repository.load()
        return validate_dwelling_config(facilities=payload["facilities"])

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        validation_result = validate_dwelling_config(facilities=payload["facilities"])
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid dwelling config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_dwelling_config(dwelling_config_base_path=str(self._base_path))
        return {"reloaded": True, "facility_count": len(payload["facilities"])}

    def _save_payload(self, payload: dict[str, list[dict[str, object]]]) -> None:
        validation_result = validate_dwelling_config(facilities=payload["facilities"])
        if not validation_result.is_valid:
            raise ValueError("; ".join(validation_result.errors))
        self._repository.save(payload)

    def _find_facility(self, facility_id: str) -> dict[str, object] | None:
        payload = self._repository.load()
        return next(
            (
                facility
                for facility in payload["facilities"]
                if str(facility.get("facility_id", "")) == facility_id
            ),
            None,
        )

    def _find_facility_index(
        self,
        facilities: list[dict[str, object]],
        facility_id: str,
    ) -> int | None:
        for index, facility in enumerate(facilities):
            if str(facility.get("facility_id", "")) == facility_id:
                return index
        return None

