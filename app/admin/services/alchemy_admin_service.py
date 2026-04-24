from __future__ import annotations

from pathlib import Path

from app.admin.repositories.alchemy_config_repository import AlchemyConfigRepository
from app.admin.services.alchemy_validation_service import validate_alchemy_config
from app.core_loop.types import NotFoundError


class AlchemyAdminService:
    def __init__(self, base_path: str | None = None, run_service: object | None = None) -> None:
        self._base_path = (
            Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        )
        self._repository = AlchemyConfigRepository(base_path=self._base_path)
        self._run_service = run_service

    def list_recipes(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        return {
            "items": sorted(
                payload["recipes"],
                key=lambda recipe: (
                    int(recipe.get("required_alchemy_level", 0) or 0),
                    str(recipe.get("recipe_id", "")),
                ),
            )
        }

    def get_recipe(self, recipe_id: str) -> dict[str, object]:
        recipe = self._find_recipe(recipe_id)
        if recipe is None:
            raise NotFoundError(f"alchemy recipe '{recipe_id}' not found")
        return recipe

    def create_recipe(self, recipe_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        recipe_id = str(recipe_payload.get("recipe_id", "")).strip()
        if not recipe_id:
            raise ValueError("recipe_id is required")
        if any(str(item.get("recipe_id", "")) == recipe_id for item in payload["recipes"]):
            raise ValueError(f"alchemy recipe '{recipe_id}' already exists")
        payload["recipes"].append(dict(recipe_payload))
        self._save_payload(payload)
        return self.get_recipe(recipe_id)

    def update_recipe(self, recipe_id: str, recipe_payload: dict[str, object]) -> dict[str, object]:
        payload = self._repository.load()
        index = self._find_recipe_index(payload["recipes"], recipe_id)
        if index is None:
            raise NotFoundError(f"alchemy recipe '{recipe_id}' not found")

        normalized_recipe_id = str(recipe_payload.get("recipe_id", "")).strip()
        if normalized_recipe_id and normalized_recipe_id != recipe_id:
            raise ValueError("recipe_id is immutable")

        next_recipe = dict(recipe_payload)
        next_recipe["recipe_id"] = recipe_id
        payload["recipes"][index] = next_recipe
        self._save_payload(payload)
        return self.get_recipe(recipe_id)

    def delete_recipe(self, recipe_id: str) -> None:
        payload = self._repository.load()
        before_count = len(payload["recipes"])
        payload["recipes"] = [
            recipe for recipe in payload["recipes"] if str(recipe.get("recipe_id", "")) != recipe_id
        ]
        if len(payload["recipes"]) == before_count:
            raise NotFoundError(f"alchemy recipe '{recipe_id}' not found")
        self._save_payload(payload)

    def list_levels(self) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        return {
            "items": sorted(
                payload["levels"],
                key=lambda level: int(level.get("level", 0) or 0),
            )
        }

    def update_levels(self, levels: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
        payload = self._repository.load()
        payload["levels"] = [dict(level) for level in levels]
        self._save_payload(payload)
        return self.list_levels()

    def validate_current_config(self):
        payload = self._repository.load()
        return validate_alchemy_config(
            levels=payload["levels"],
            recipes=payload["recipes"],
        )

    def reload_runtime_config(self) -> dict[str, object]:
        payload = self._repository.load()
        validation_result = validate_alchemy_config(
            levels=payload["levels"],
            recipes=payload["recipes"],
        )
        if not validation_result.is_valid:
            raise ValueError("cannot reload invalid alchemy config")

        run_service = self._run_service
        if run_service is None:
            from app.api import core_loop as core_loop_api

            run_service = core_loop_api.run_service

        run_service.reload_alchemy_config(alchemy_config_base_path=str(self._base_path))
        return {
            "reloaded": True,
            "level_count": len(payload["levels"]),
            "recipe_count": len(payload["recipes"]),
        }

    def _save_payload(self, payload: dict[str, list[dict[str, object]]]) -> None:
        validation_result = validate_alchemy_config(
            levels=payload["levels"],
            recipes=payload["recipes"],
        )
        if not validation_result.is_valid:
            raise ValueError("; ".join(validation_result.errors))
        self._repository.save(payload)

    def _find_recipe(self, recipe_id: str) -> dict[str, object] | None:
        payload = self._repository.load()
        return next(
            (
                recipe
                for recipe in payload["recipes"]
                if str(recipe.get("recipe_id", "")) == recipe_id
            ),
            None,
        )

    def _find_recipe_index(
        self,
        recipes: list[dict[str, object]],
        recipe_id: str,
    ) -> int | None:
        for index, recipe in enumerate(recipes):
            if str(recipe.get("recipe_id", "")) == recipe_id:
                return index
        return None
