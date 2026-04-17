from __future__ import annotations

from pathlib import Path

from app.admin.repositories.enemy_config_repository import EnemyConfigRepository
from app.admin.services.enemy_validation_service import validate_enemy_config
from app.core_loop.types import NotFoundError


class EnemyAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = EnemyConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_enemies(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        items = sorted(
            payload["items"],
            key=lambda enemy: (str(enemy.get("enemy_realm_label", "")), str(enemy.get("enemy_id", ""))),
        )
        return {"items": items}

    def get_enemy(self, enemy_id: str) -> dict[str, object]:
        enemy = self._find_enemy(enemy_id)
        if enemy is None:
            raise NotFoundError(f"enemy '{enemy_id}' not found")
        return enemy

    def create_enemy(self, enemy_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        enemy_id = str(enemy_payload.get("enemy_id", "")).strip()
        if not enemy_id:
            raise ValueError("enemy_id is required")
        if any(str(item.get("enemy_id", "")) == enemy_id for item in payload["items"]):
            raise ValueError(f"enemy '{enemy_id}' already exists")
        payload["items"].append(dict(enemy_payload))
        self._save_payload(payload)
        return self.get_enemy(enemy_id)

    def update_enemy(self, enemy_id: str, enemy_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        index = self._find_enemy_index(payload["items"], enemy_id)
        if index is None:
            raise NotFoundError(f"enemy '{enemy_id}' not found")

        normalized_enemy_id = str(enemy_payload.get("enemy_id", "")).strip()
        if normalized_enemy_id and normalized_enemy_id != enemy_id:
            raise ValueError("enemy_id is immutable")

        next_enemy = dict(enemy_payload)
        next_enemy["enemy_id"] = enemy_id
        payload["items"][index] = next_enemy
        self._save_payload(payload)
        return self.get_enemy(enemy_id)

    def delete_enemy(self, enemy_id: str) -> None:
        payload = self._repository.load()
        before_count = len(payload["items"])
        payload["items"] = [
            enemy for enemy in payload["items"] if str(enemy.get("enemy_id", "")) != enemy_id
        ]
        if len(payload["items"]) == before_count:
            raise NotFoundError(f"enemy '{enemy_id}' not found")
        self._repository.save(payload)

    def validate_current_config(self):
        payload = self._repository.load()
        return validate_enemy_config(enemies=payload["items"])

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        validation_result = validate_enemy_config(enemies=payload["items"])
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid enemy config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_enemy_config(enemy_config_base_path=str(self._base_path))
        return {"reloaded": True, "enemy_count": len(payload["items"])}

    def _save_payload(self, payload: dict[str, list[dict[str, object]]]) -> None:
        validation_result = validate_enemy_config(enemies=payload["items"])
        if not validation_result.is_valid:
            raise ValueError("; ".join(validation_result.errors))
        self._repository.save(payload)

    def _find_enemy(self, enemy_id: str) -> dict[str, object] | None:
        payload = self._repository.load()
        return next(
            (
                enemy
                for enemy in payload["items"]
                if str(enemy.get("enemy_id", "")) == enemy_id
            ),
            None,
        )

    def _find_enemy_index(
        self,
        enemies: list[dict[str, object]],
        enemy_id: str,
    ) -> int | None:
        for index, enemy in enumerate(enemies):
            if str(enemy.get("enemy_id", "")) == enemy_id:
                return index
        return None
