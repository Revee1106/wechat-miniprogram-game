from __future__ import annotations

from dataclasses import dataclass

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


BASE_ALCHEMY_RECIPE_IDS = {"yang_qi_dan", "yang_yuan_dan"}


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


class AlchemyService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)
        self._recipe_specs = _build_recipe_specs()

    def hydrate_run(self, run: RunState) -> None:
        if run.alchemy_state is None:
            run.alchemy_state = AlchemyState()

        run.alchemy_state.mastery_level = _resolve_mastery_level(run.alchemy_state.mastery_exp)
        run.alchemy_state.mastery_title = _resolve_mastery_title(run.alchemy_state.mastery_level)
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
        recipe = next((item for item in self._recipe_specs if item.recipe_id == recipe_id), None)
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
        if recipe.recipe_id in BASE_ALCHEMY_RECIPE_IDS:
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


def _resolve_mastery_level(exp: int) -> int:
    thresholds = [0, 20, 50, 90, 140, 210]
    level = 0
    for index, threshold in enumerate(thresholds):
        if exp >= threshold:
            level = index
    return level


def _resolve_mastery_title(level: int) -> str:
    titles = [
        "初识丹道",
        "初窥门径",
        "略有所得",
        "熟能生巧",
        "丹道小成",
        "丹道精进",
    ]
    return titles[min(level, len(titles) - 1)]


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


def _build_recipe_specs() -> list[AlchemyRecipeSpec]:
    return [
        AlchemyRecipeSpec(
            recipe_id="yang_qi_dan",
            display_name="养气丹",
            category="cultivation",
            description="前期主力修炼丹，服用后可直接增长修为。",
            required_alchemy_level=0,
            duration_months=1,
            base_success_rate=0.86,
            ingredients={"basic_herb": 2},
            effect_type="cultivation_exp",
            effect_value=12,
            effect_summary="直接增加修为",
        ),
        AlchemyRecipeSpec(
            recipe_id="yang_yuan_dan",
            display_name="养元丹",
            category="recovery",
            description="恢复气血的基础丹药，用于外出后的调息。",
            required_alchemy_level=0,
            duration_months=1,
            base_success_rate=0.80,
            ingredients={"basic_herb": 2, "spirit_stone": 2},
            effect_type="hp_restore",
            effect_value=25,
            effect_summary="恢复气血",
        ),
        AlchemyRecipeSpec(
            recipe_id="ning_shen_dan",
            display_name="宁神丹",
            category="recovery",
            description="安定心神，缓解修炼与事件带来的心神损耗。",
            required_alchemy_level=1,
            duration_months=1,
            base_success_rate=0.76,
            ingredients={"basic_herb": 3},
            effect_type="status_penalty_reduce",
            effect_value=0.05,
            effect_summary="降低状态惩罚",
        ),
        AlchemyRecipeSpec(
            recipe_id="ju_ling_dan",
            display_name="聚灵丹",
            category="cultivation",
            description="中期修炼丹，借灵泉与丹室凝聚灵力。",
            required_alchemy_level=2,
            duration_months=1,
            base_success_rate=0.64,
            ingredients={"basic_herb": 4, "spirit_stone": 2},
            effect_type="cultivation_exp",
            effect_value=24,
            effect_summary="较高幅度增加修为",
        ),
        AlchemyRecipeSpec(
            recipe_id="gu_yuan_dan",
            display_name="固元丹",
            category="breakthrough",
            description="稳定元气，为破境前的最后准备提供支撑。",
            required_alchemy_level=2,
            duration_months=1,
            base_success_rate=0.60,
            ingredients={"basic_herb": 3, "ore": 1, "spirit_stone": 3},
            effect_type="breakthrough_bonus",
            effect_value=6,
            effect_summary="提高突破辅助值",
        ),
    ]
