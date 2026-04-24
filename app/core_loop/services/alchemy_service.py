from __future__ import annotations

from dataclasses import dataclass

from app.admin.repositories.alchemy_config_repository import AlchemyConfigRepository
from app.core_loop.types import (
    AlchemyInventoryItem,
    AlchemyJob,
    AlchemyRecipeState,
    AlchemyResult,
    AlchemyState,
    ConflictError,
    RunState,
)
from app.economy.services.run_resource_service import RunResourceService


@dataclass(frozen=True)
class AlchemyMasteryLevelSpec:
    level: int
    display_name: str
    required_mastery_exp: int


@dataclass(frozen=True)
class AlchemyRecipeSpec:
    recipe_id: str
    display_name: str
    category: str
    description: str
    required_alchemy_level: int
    duration_months: int
    base_success_rate: float
    ingredients: dict[str, int]
    effect_type: str
    effect_value: float
    effect_summary: str
    is_base_recipe: bool = False


class AlchemyService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)
        self._repository = AlchemyConfigRepository(base_path=base_path)
        self._mastery_levels: list[AlchemyMasteryLevelSpec] = []
        self._recipe_specs: list[AlchemyRecipeSpec] = []
        self._recipe_specs_by_id: dict[str, AlchemyRecipeSpec] = {}
        self.reload_config(base_path=base_path)

    def reload_config(self, base_path: str | None = None) -> None:
        if base_path is not None:
            self._resource_service = RunResourceService(base_path=base_path)
            self._repository = AlchemyConfigRepository(base_path=base_path)

        payload = self._repository.load()
        self._mastery_levels = _load_mastery_levels(payload.get("levels", []))
        self._recipe_specs = _load_recipe_specs(payload.get("recipes", []))
        self._recipe_specs_by_id = {
            recipe_spec.recipe_id: recipe_spec for recipe_spec in self._recipe_specs
        }

    def hydrate_run(self, run: RunState) -> None:
        if run.alchemy_state is None:
            run.alchemy_state = AlchemyState()

        run.alchemy_state.mastery_level = _resolve_mastery_level(
            run.alchemy_state.mastery_exp,
            self._mastery_levels,
        )
        run.alchemy_state.mastery_title = _resolve_mastery_title(
            run.alchemy_state.mastery_level,
            self._mastery_levels,
        )
        run.alchemy_state.available_recipes = [
            self._build_recipe_state(run, spec)
            for spec in self._recipe_specs
            if self._is_recipe_known(run, spec)
        ]
        self._sync_pill_counter(run)

    def start(self, run: RunState, recipe_id: str, use_spirit_spring: bool = False) -> None:
        self.hydrate_run(run)
        if run.alchemy_state.active_job is not None:
            raise ConflictError("there is already an active alchemy job")

        recipe = self._get_recipe(recipe_id)
        recipe_state = self._build_recipe_state(run, recipe)
        if not recipe_state.can_start:
            raise ConflictError(recipe_state.disabled_reason or "recipe cannot be started")

        self._spend_resources(run, recipe.ingredients)
        if use_spirit_spring:
            self._spend_resources(run, {"spirit_spring_water": 1})

        run.alchemy_state.active_job = AlchemyJob(
            recipe_id=recipe.recipe_id,
            recipe_name=recipe.display_name,
            total_months=recipe.duration_months,
            remaining_months=recipe.duration_months,
            use_spirit_spring=use_spirit_spring,
        )
        run.result_summary = f"已开炉炼制 {recipe.display_name}。"
        self.hydrate_run(run)

    def advance_month(self, run: RunState) -> AlchemyResult | None:
        self.hydrate_run(run)
        job = run.alchemy_state.active_job
        if job is None:
            return None

        job.remaining_months = max(0, job.remaining_months - 1)
        if job.remaining_months > 0:
            return None

        recipe = self._get_recipe(job.recipe_id)
        mastery_level = run.alchemy_state.mastery_level
        score = (
            recipe.base_success_rate
            + mastery_level * 0.04
            + (0.08 if job.use_spirit_spring else 0.0)
        )
        outcome_rank, outcome, quality = _resolve_outcome(score)
        mastery_gain = 5 if outcome == "waste" else 10 + outcome_rank * 3

        if outcome == "success":
            self._add_inventory_item(
                run,
                recipe_id=recipe.recipe_id,
                display_name=recipe.display_name,
                quality=quality,
                effect_summary=recipe.effect_summary,
                effect_type=recipe.effect_type,
                effect_value=recipe.effect_value,
            )

        result = AlchemyResult(
            recipe_id=recipe.recipe_id,
            recipe_name=recipe.display_name,
            outcome=outcome,
            quality=quality,
            outcome_rank=outcome_rank,
            amount=1 if outcome == "success" else 0,
            mastery_exp_gained=mastery_gain,
            summary=_build_result_summary(recipe.display_name, outcome, quality),
        )
        run.alchemy_state.active_job = None
        run.alchemy_state.last_result = result
        run.alchemy_state.mastery_exp += mastery_gain
        self.hydrate_run(run)
        return result

    def consume(self, run: RunState, item_id: str, quality: str | None = None) -> None:
        self.hydrate_run(run)
        inventory_item = next(
            (
                item
                for item in run.alchemy_state.inventory
                if item.item_id == item_id and (quality is None or item.quality == quality)
            ),
            None,
        )
        if inventory_item is None:
            inventory_item = next(
                (item for item in run.alchemy_state.inventory if item.item_id == item_id),
                None,
            )
        if inventory_item is None:
            raise ConflictError(f"alchemy item '{item_id}' is not available")

        recipe = self._get_recipe(item_id)
        multiplier = {"low": 1.0, "mid": 1.25, "high": 1.5}.get(inventory_item.quality, 1.0)
        effect_value = recipe.effect_value * multiplier

        if recipe.effect_type == "cultivation_exp":
            run.character.cultivation_exp += int(effect_value)
        elif recipe.effect_type == "hp_restore":
            run.character.hp_current = min(
                run.character.hp_max,
                run.character.hp_current + int(effect_value),
            )
        elif recipe.effect_type == "lifespan_restore":
            run.character.lifespan_current = min(
                run.character.lifespan_max,
                run.character.lifespan_current + int(effect_value),
            )
        elif recipe.effect_type == "status_penalty_reduce":
            run.character.status_penalty = max(
                0.0,
                run.character.status_penalty - effect_value,
            )
        elif recipe.effect_type == "breakthrough_bonus":
            run.character.breakthrough_bonus += int(effect_value)

        inventory_item.amount -= 1
        if inventory_item.amount <= 0:
            run.alchemy_state.inventory = [
                item for item in run.alchemy_state.inventory if item.amount > 0
            ]

        run.result_summary = f"已服用 {inventory_item.display_name}（{_quality_label(inventory_item.quality)}）。"
        self.hydrate_run(run)

    def _get_recipe(self, recipe_id: str) -> AlchemyRecipeSpec:
        recipe = self._recipe_specs_by_id.get(recipe_id)
        if recipe is None:
            raise ConflictError(f"unknown alchemy recipe '{recipe_id}'")
        return recipe

    def _build_recipe_state(self, run: RunState, recipe: AlchemyRecipeSpec) -> AlchemyRecipeState:
        room_level = self._get_dwelling_level(run, "alchemy_room")
        mastery_level = run.alchemy_state.mastery_level
        disabled_reason = None

        if room_level <= 0:
            disabled_reason = "尚未建成炼丹房。"
        elif mastery_level < recipe.required_alchemy_level:
            disabled_reason = f"炼丹术需达到 {recipe.required_alchemy_level} 级。"
        elif not self._is_recipe_known(run, recipe):
            disabled_reason = "尚未习得该丹方。"
        elif run.alchemy_state.active_job is not None:
            disabled_reason = "当前已有炼制中的炉次。"
        elif not self._has_resources(run, recipe.ingredients):
            disabled_reason = "材料不足。"

        return AlchemyRecipeState(
            recipe_id=recipe.recipe_id,
            display_name=recipe.display_name,
            category=recipe.category,
            description=recipe.description,
            effect_summary=recipe.effect_summary,
            effect_type=recipe.effect_type,
            effect_value=recipe.effect_value,
            required_alchemy_level=recipe.required_alchemy_level,
            duration_months=recipe.duration_months,
            base_success_rate=recipe.base_success_rate,
            ingredients=dict(recipe.ingredients),
            can_start=disabled_reason is None,
            disabled_reason=disabled_reason,
        )

    def _get_dwelling_level(self, run: RunState, facility_id: str) -> int:
        facility = next(
            (item for item in run.dwelling_facilities if item.facility_id == facility_id),
            None,
        )
        return facility.level if facility is not None else 0

    def _is_recipe_known(self, run: RunState, recipe: AlchemyRecipeSpec) -> bool:
        if recipe.is_base_recipe:
            return True
        return recipe.recipe_id in set(run.alchemy_state.learned_recipe_ids)

    def _has_resources(self, run: RunState, costs: dict[str, int]) -> bool:
        return all(self._get_resource_amount(run, key) >= value for key, value in costs.items())

    def _spend_resources(self, run: RunState, costs: dict[str, int]) -> None:
        if not self._has_resources(run, costs):
            raise ConflictError("not enough resources for alchemy")
        for resource_key, amount in costs.items():
            self._resource_service.add(run, resource_key, -amount)

    def _get_resource_amount(self, run: RunState, resource_key: str) -> int:
        if resource_key == "herb":
            return run.resources.herbs
        if resource_key == "ore":
            return run.resources.ore
        if resource_key == "spirit_stone":
            return run.resources.spirit_stone
        stack = next(
            (item for item in run.resource_stacks if item.resource_key == resource_key),
            None,
        )
        return stack.amount if stack is not None else 0

    def _add_inventory_item(
        self,
        run: RunState,
        recipe_id: str,
        display_name: str,
        quality: str,
        effect_summary: str,
        effect_type: str,
        effect_value: float,
    ) -> None:
        existing = next(
            (
                item
                for item in run.alchemy_state.inventory
                if item.item_id == recipe_id and item.quality == quality
            ),
            None,
        )
        if existing is not None:
            existing.amount += 1
            return

        run.alchemy_state.inventory.append(
            AlchemyInventoryItem(
                item_id=recipe_id,
                display_name=display_name,
                quality=quality,
                amount=1,
                effect_summary=effect_summary,
                effect_type=effect_type,
                effect_value=effect_value,
            )
        )

    def _sync_pill_counter(self, run: RunState) -> None:
        run.resources.pill = sum(item.amount for item in run.alchemy_state.inventory)


def _resolve_mastery_level(exp: int, levels: list[AlchemyMasteryLevelSpec]) -> int:
    level = 0
    for spec in levels:
        if exp >= spec.required_mastery_exp:
            level = spec.level
    return level


def _resolve_mastery_title(level: int, levels: list[AlchemyMasteryLevelSpec]) -> str:
    matching = next((spec for spec in levels if spec.level == level), None)
    if matching is not None:
        return matching.display_name
    if levels:
        return levels[0].display_name
    return "丹道未入门"


def _resolve_outcome(score: float) -> tuple[int, str, str]:
    if score >= 0.85:
        return 3, "success", "high"
    if score >= 0.68:
        return 2, "success", "mid"
    if score >= 0.5:
        return 1, "success", "low"
    return 0, "waste", "low"


def _quality_label(quality: str) -> str:
    return {"low": "下品", "mid": "中品", "high": "上品"}.get(quality, quality)


def _build_result_summary(recipe_name: str, outcome: str, quality: str) -> str:
    if outcome == "success":
        return f"{recipe_name} 成丹，品质为{_quality_label(quality)}。"
    return f"{recipe_name} 炼制失手，只余废丹。"


def _load_mastery_levels(levels: list[dict[str, object]]) -> list[AlchemyMasteryLevelSpec]:
    return sorted(
        [
            AlchemyMasteryLevelSpec(
                level=int(level.get("level", 0) or 0),
                display_name=str(level.get("display_name", "")).strip(),
                required_mastery_exp=int(level.get("required_mastery_exp", 0) or 0),
            )
            for level in levels
        ],
        key=lambda item: item.level,
    )


def _load_recipe_specs(recipes: list[dict[str, object]]) -> list[AlchemyRecipeSpec]:
    return [
        AlchemyRecipeSpec(
            recipe_id=str(recipe.get("recipe_id", "")).strip(),
            display_name=str(recipe.get("display_name", "")).strip(),
            category=str(recipe.get("category", "")).strip(),
            description=str(recipe.get("description", "")).strip(),
            required_alchemy_level=int(recipe.get("required_alchemy_level", 0) or 0),
            duration_months=int(recipe.get("duration_months", 0) or 0),
            base_success_rate=float(recipe.get("base_success_rate", 0) or 0),
            ingredients={
                str(key): int(value)
                for key, value in dict(recipe.get("ingredients", {})).items()
            },
            effect_type=str(recipe.get("effect_type", "")).strip(),
            effect_value=float(recipe.get("effect_value", 0) or 0),
            effect_summary=str(recipe.get("effect_summary", "")).strip(),
            is_base_recipe=recipe.get("is_base_recipe") is True,
        )
        for recipe in recipes
        if str(recipe.get("recipe_id", "")).strip()
    ]
