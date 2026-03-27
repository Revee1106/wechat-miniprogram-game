from __future__ import annotations

from pathlib import Path

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.admin.services.realm_validation_service import validate_realm_config
from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.types import NotFoundError, RealmConfig


class RealmAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = RealmConfigRepository(base_path=self._base_path)
        self._event_repository = EventConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_realms(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        return {"items": self._sort_realms(payload["realms"])}

    def get_realm(self, realm_key: str) -> dict[str, object]:
        realm = self._find_realm(realm_key)
        if realm is None:
            raise NotFoundError(f"realm '{realm_key}' not found")
        return realm

    def create_realm(self, realm_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        realm_key = self._normalize_key(realm_payload.get("key"))
        if not realm_key:
            raise ValueError("realm key is required")
        if any(realm.get("key") == realm_key for realm in payload["realms"]):
            raise ValueError(f"realm '{realm_key}' already exists")

        payload["realms"].append(self._normalize_realm_payload(realm_payload, realm_key))
        self._save_payload(payload)
        return self._find_realm(realm_key) or {}

    def update_realm(self, realm_key: str, realm_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        index = self._find_realm_index(payload["realms"], realm_key)
        if index is None:
            raise NotFoundError(f"realm '{realm_key}' not found")

        normalized_key = self._normalize_key(realm_payload.get("key"))
        if normalized_key and normalized_key != realm_key:
            raise ValueError("realm key is immutable")

        normalized_realm = self._normalize_realm_payload(realm_payload, realm_key)
        if normalized_realm.get("is_enabled", True) is not True:
            references = self._find_realm_references(realm_key, payload["realms"])
            if references:
                raise ValueError(
                    f"realm '{realm_key}' is referenced by events: {', '.join(references)}"
                )

        payload["realms"][index] = normalized_realm
        self._save_payload(payload)
        return self._find_realm(realm_key) or {}

    def delete_realm(self, realm_key: str) -> bool:
        payload = self._repository.load()
        index = self._find_realm_index(payload["realms"], realm_key)
        if index is None:
            raise NotFoundError(f"realm '{realm_key}' not found")

        references = self._find_realm_references(realm_key, payload["realms"])
        if references:
            raise ValueError(
                f"realm '{realm_key}' is referenced by events: {', '.join(references)}"
            )

        payload["realms"] = [
            realm for realm in payload["realms"] if realm.get("key") != realm_key
        ]
        self._save_payload(payload)
        return True

    def validate_current_config(self):
        payload = self._repository.load()
        return validate_realm_config(realms=payload["realms"])

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        validation_result = validate_realm_config(realms=payload["realms"])
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid realm config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_realm_config(
            realm_config_base_path=str(self._base_path),
        )
        return {"reloaded": True, "realm_count": len(payload["realms"])}

    def reorder_realms(self, keys: list[str]) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        realms = payload["realms"]
        existing_keys = [str(realm.get("key", "")) for realm in realms if str(realm.get("key", ""))]
        normalized_keys = [self._normalize_key(key) for key in keys]

        if sorted(existing_keys) != sorted(normalized_keys):
            raise ValueError("realm reorder keys must match the current realm set")

        index_map = {str(realm.get("key", "")): realm for realm in realms}
        reordered: list[dict[str, object]] = []
        for order_index, key in enumerate(normalized_keys, start=1):
            realm = dict(index_map[key])
            realm["order_index"] = order_index
            reordered.append(realm)

        payload["realms"] = reordered
        self._save_payload(payload)
        return {"items": self._sort_realms(payload["realms"])}

    def _save_payload(self, payload: dict[str, list[dict[str, object]]]) -> None:
        validation_result = validate_realm_config(realms=payload["realms"])
        if not validation_result.is_valid:
            raise ValueError("; ".join(validation_result.errors))
        payload["realms"] = self._sort_realms(payload["realms"])
        self._repository.save(payload)

    def _find_realm(self, realm_key: str) -> dict[str, object] | None:
        payload = self._repository.load()
        return next(
            (realm for realm in payload["realms"] if realm.get("key") == realm_key),
            None,
        )

    def _find_realm_index(
        self,
        realms: list[dict[str, object]],
        realm_key: str,
    ) -> int | None:
        for index, realm in enumerate(realms):
            if realm.get("key") == realm_key:
                return index
        return None

    def _find_realm_references(
        self,
        realm_key: str,
        realms: list[dict[str, object]],
    ) -> list[str]:
        realm_models = self._build_realm_models(realms)
        target_key = resolve_realm_key(realm_key, realm_models)
        target_index = self._index_map(realm_models).get(target_key)
        if target_index is None:
            return []

        payload = self._event_repository.load()
        references: list[str] = []
        for template in payload["templates"]:
            event_id = str(template.get("event_id", ""))
            min_key = template.get("realm_min")
            max_key = template.get("realm_max")
            if not min_key and not max_key:
                continue

            minimum_key = (
                resolve_realm_key(str(min_key), realm_models, boundary="min")
                if min_key
                else None
            )
            maximum_key = (
                resolve_realm_key(str(max_key), realm_models, boundary="max")
                if max_key
                else None
            )
            minimum_index = (
                self._index_map(realm_models).get(minimum_key) if minimum_key else None
            )
            maximum_index = (
                self._index_map(realm_models).get(maximum_key) if maximum_key else None
            )
            if minimum_index is not None and target_index < minimum_index:
                continue
            if maximum_index is not None and target_index > maximum_index:
                continue
            if event_id:
                references.append(event_id)
        return references

    def _normalize_realm_payload(
        self,
        realm_payload: dict[str, object],
        realm_key: str,
    ) -> dict[str, object]:
        normalized = dict(realm_payload)
        normalized["key"] = realm_key
        return normalized

    def _normalize_key(self, value: object) -> str:
        return str(value or "").strip()

    def _sort_realms(self, realms: list[dict[str, object]]) -> list[dict[str, object]]:
        return sorted(
            realms,
            key=lambda realm: (
                int(realm.get("order_index", 0) or 0),
                str(realm.get("key", "")),
            ),
        )

    def _build_realm_models(self, realms: list[dict[str, object]]) -> list[RealmConfig]:
        return sorted(
            [
                RealmConfig(
                    key=str(realm.get("key", "")),
                    display_name=str(realm.get("display_name", "")),
                    major_realm=str(realm.get("major_realm", "")),
                    stage_index=int(realm.get("stage_index", 0) or 0),
                    order_index=int(realm.get("order_index", 0) or 0),
                    lifespan_bonus=int(realm.get("lifespan_bonus", 0) or 0),
                    base_success_rate=float(realm.get("base_success_rate", 0) or 0),
                    required_exp=int(realm.get("required_cultivation_exp", 0) or 0),
                    required_spirit_stone=int(realm.get("required_spirit_stone", 0) or 0),
                    is_enabled=realm.get("is_enabled", True) is True,
                )
                for realm in realms
                if str(realm.get("key", ""))
            ],
            key=lambda config: (config.order_index, config.key),
        )

    def _index_map(self, realm_models: list[RealmConfig]) -> dict[str, int]:
        return {config.key: index for index, config in enumerate(realm_models)}
