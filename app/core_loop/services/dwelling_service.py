from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy

from app.core_loop.types import (
    ConflictError,
    DwellingFacilityState,
    DwellingSettlement,
    DwellingSettlementEntry,
    RunState,
)
from app.economy.services.run_resource_service import RunResourceService


@dataclass(frozen=True)
class DwellingLevelSpec:
    level: int
    maintenance_cost: dict[str, int]
    resource_yields: dict[str, int]
    cultivation_exp_gain: int = 0
    upgrade_cost: dict[str, int] | None = None


@dataclass(frozen=True)
class DwellingFacilitySpec:
    facility_id: str
    display_name: str
    facility_type: str
    summary: str
    build_cost: dict[str, int]
    max_level: int
    levels: dict[int, DwellingLevelSpec]
    function_unlock_text: str = ""


class DwellingService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)
        self._facility_specs = _build_facility_specs()

    def hydrate_run(self, run: RunState) -> None:
        facilities_by_id = {
            facility.facility_id: deepcopy(facility) for facility in run.dwelling_facilities
        }
        hydrated_facilities: list[DwellingFacilityState] = []

        for spec in self._facility_specs:
            facility = facilities_by_id.get(spec.facility_id) or DwellingFacilityState(
                facility_id=spec.facility_id,
                display_name=spec.display_name,
                facility_type=spec.facility_type,
                summary=spec.summary,
            )
            self._hydrate_facility_state(facility, spec)
            hydrated_facilities.append(facility)

        run.dwelling_facilities = hydrated_facilities
        run.dwelling_level = self._calculate_dwelling_level(run)

    def build_facility(self, run: RunState, facility_id: str) -> None:
        self.hydrate_run(run)
        facility, spec = self._get_facility(run, facility_id)
        if facility.level > 0:
            raise ConflictError(f"facility '{facility_id}' is already built")

        self._spend_cost(run, spec.build_cost)
        facility.level = 1
        facility.status = self._active_status_for_level(facility.level, spec.max_level)
        self._hydrate_facility_state(facility, spec)
        run.dwelling_level = self._calculate_dwelling_level(run)

    def upgrade_facility(self, run: RunState, facility_id: str) -> None:
        self.hydrate_run(run)
        facility, spec = self._get_facility(run, facility_id)
        if facility.level == 0:
            raise ConflictError(f"facility '{facility_id}' is not built")
        if facility.level >= spec.max_level:
            raise ConflictError(f"facility '{facility_id}' is already at max level")

        current_level_spec = spec.levels[facility.level]
        upgrade_cost = current_level_spec.upgrade_cost or {}
        self._spend_cost(run, upgrade_cost)
        facility.level += 1
        facility.status = self._active_status_for_level(facility.level, spec.max_level)
        self._hydrate_facility_state(facility, spec)
        run.dwelling_level = self._calculate_dwelling_level(run)

    def settle_month(self, run: RunState) -> DwellingSettlement:
        self.hydrate_run(run)
        settlement = DwellingSettlement(round_index=run.round_index)

        for facility in run.dwelling_facilities:
            if facility.level == 0:
                continue

            _, spec = self._get_facility(run, facility.facility_id)
            level_spec = spec.levels[facility.level]
            if not self._can_afford(run, level_spec.maintenance_cost):
                facility.status = "stalled"
                entry = DwellingSettlementEntry(
                    facility_id=facility.facility_id,
                    display_name=facility.display_name,
                    status="stalled",
                    summary=f"{facility.display_name} 本月因灵石不足而停摆。",
                )
                settlement.entries.append(entry)
                settlement.summary_lines.append(entry.summary)
                continue

            self._spend_cost(run, level_spec.maintenance_cost)
            resolved_yields = self._resolve_resource_yields(run, facility, level_spec)
            for resource_key, amount in resolved_yields.items():
                self._resource_service.add(run, resource_key, amount)
                settlement.total_resource_gains[resource_key] = (
                    settlement.total_resource_gains.get(resource_key, 0) + amount
                )
            run.character.cultivation_exp += level_spec.cultivation_exp_gain
            settlement.total_cultivation_exp_gain += level_spec.cultivation_exp_gain
            for resource_key, amount in level_spec.maintenance_cost.items():
                settlement.total_maintenance_paid[resource_key] = (
                    settlement.total_maintenance_paid.get(resource_key, 0) + amount
                )

            facility.status = self._active_status_for_level(facility.level, spec.max_level)
            entry = DwellingSettlementEntry(
                facility_id=facility.facility_id,
                display_name=facility.display_name,
                status=facility.status,
                maintenance_paid=dict(level_spec.maintenance_cost),
                resource_gains=resolved_yields,
                cultivation_exp_gain=level_spec.cultivation_exp_gain,
                summary=self._build_entry_summary(facility, level_spec, resolved_yields),
            )
            settlement.entries.append(entry)
            settlement.summary_lines.append(entry.summary)

        run.dwelling_last_settlement = settlement
        run.dwelling_level = self._calculate_dwelling_level(run)
        self.hydrate_run(run)
        return settlement

    def get_breakthrough_bonus(self, run: RunState) -> float:
        self.hydrate_run(run)
        facility = next(
            (
                item
                for item in run.dwelling_facilities
                if item.facility_id == "spirit_gathering_array"
            ),
            None,
        )
        if facility is None or facility.level == 0:
            return 0.0
        return min(0.02 * facility.level, 0.08)

    def get_mine_spirit_stone_bonus(self, run: RunState) -> float:
        self.hydrate_run(run)
        facility = next(
            (
                item
                for item in run.dwelling_facilities
                if item.facility_id == "spirit_gathering_array"
            ),
            None,
        )
        if facility is None or facility.level == 0:
            return 0.0
        return min(0.10 * facility.level, 0.30)

    def _get_facility(
        self,
        run: RunState,
        facility_id: str,
    ) -> tuple[DwellingFacilityState, DwellingFacilitySpec]:
        facility = next(
            (item for item in run.dwelling_facilities if item.facility_id == facility_id),
            None,
        )
        spec = next((item for item in self._facility_specs if item.facility_id == facility_id), None)
        if facility is None or spec is None:
            raise ConflictError(f"unknown dwelling facility '{facility_id}'")
        return facility, spec

    def _hydrate_facility_state(
        self,
        facility: DwellingFacilityState,
        spec: DwellingFacilitySpec,
    ) -> None:
        facility.display_name = spec.display_name
        facility.facility_type = spec.facility_type
        facility.summary = spec.summary
        facility.max_level = spec.max_level
        facility.build_cost = dict(spec.build_cost)
        facility.function_unlock_text = spec.function_unlock_text
        facility.is_function_unlocked = facility.level > 0 and bool(spec.function_unlock_text)

        if facility.level <= 0:
            facility.status = "unbuilt"
            facility.next_upgrade_cost = dict(spec.build_cost)
            facility.maintenance_cost = {}
            facility.monthly_resource_yields = {}
            facility.monthly_cultivation_exp_gain = 0
            return

        level_spec = spec.levels[facility.level]
        facility.maintenance_cost = dict(level_spec.maintenance_cost)
        facility.monthly_resource_yields = dict(level_spec.resource_yields)
        facility.monthly_cultivation_exp_gain = level_spec.cultivation_exp_gain
        facility.next_upgrade_cost = (
            dict(level_spec.upgrade_cost) if level_spec.upgrade_cost else {}
        )
        if facility.status != "stalled":
            facility.status = self._active_status_for_level(facility.level, spec.max_level)

    def _can_afford(self, run: RunState, cost: dict[str, int]) -> bool:
        return all(self._get_resource_amount(run, resource_key) >= amount for resource_key, amount in cost.items())

    def _spend_cost(self, run: RunState, cost: dict[str, int]) -> None:
        if not self._can_afford(run, cost):
            raise ConflictError("not enough resources for dwelling action")
        for resource_key, amount in cost.items():
            self._resource_service.add(run, resource_key, -amount)

    def _get_resource_amount(self, run: RunState, resource_key: str) -> int:
        legacy_fields = {
            "spirit_stone": "spirit_stone",
            "herb": "herbs",
            "ore": "ore",
            "beast_material": "beast_material",
            "pill": "pill",
            "craft_material": "craft_material",
        }
        legacy_field = legacy_fields.get(resource_key)
        if legacy_field is not None:
            return int(getattr(run.resources, legacy_field, 0))

        stack = next(
            (item for item in run.resource_stacks if item.resource_key == resource_key),
            None,
        )
        return stack.amount if stack is not None else 0

    def _build_entry_summary(
        self,
        facility: DwellingFacilityState,
        level_spec: DwellingLevelSpec,
        resolved_yields: dict[str, int] | None = None,
    ) -> str:
        parts = []
        if level_spec.maintenance_cost:
            parts.append(
                "维护 "
                + " / ".join(
                    f"{resource_key} -{amount}"
                    for resource_key, amount in level_spec.maintenance_cost.items()
                )
            )
        actual_yields = resolved_yields if resolved_yields is not None else level_spec.resource_yields
        if actual_yields:
            parts.append(
                "产出 "
                + " / ".join(
                    f"{resource_key} +{amount}"
                    for resource_key, amount in actual_yields.items()
                )
            )
        if level_spec.cultivation_exp_gain:
            parts.append(f"修为 +{level_spec.cultivation_exp_gain}")
        if not parts:
            parts.append("功能维持正常")
        return f"{facility.display_name}：" + "，".join(parts)

    def _calculate_dwelling_level(self, run: RunState) -> int:
        built_levels = [facility.level for facility in run.dwelling_facilities if facility.level > 0]
        return max(built_levels, default=1)

    def _resolve_resource_yields(
        self,
        run: RunState,
        facility: DwellingFacilityState,
        level_spec: DwellingLevelSpec,
    ) -> dict[str, int]:
        yields = dict(level_spec.resource_yields)
        if facility.facility_id != "mine_cave":
            return yields

        spirit_stone_gain = yields.get("spirit_stone", 0)
        if spirit_stone_gain <= 0:
            return yields

        yields["spirit_stone"] = max(
            spirit_stone_gain,
            int(spirit_stone_gain * (1 + self.get_mine_spirit_stone_bonus(run))),
        )
        return yields

    def _active_status_for_level(self, level: int, max_level: int) -> str:
        if level >= max_level:
            return "max_level"
        return "active"


def _build_facility_specs() -> list[DwellingFacilitySpec]:
    return [
        DwellingFacilitySpec(
            facility_id="spirit_field",
            display_name="灵田",
            facility_type="production",
            summary="提供稳定灵植产出，为后续丹药与事件需求打底。",
            build_cost={"spirit_stone": 50},
            max_level=3,
            levels={
                1: DwellingLevelSpec(
                    level=1,
                    maintenance_cost={"spirit_stone": 2},
                    resource_yields={"basic_herb": 2},
                    upgrade_cost={"spirit_stone": 40},
                ),
                2: DwellingLevelSpec(
                    level=2,
                    maintenance_cost={"spirit_stone": 3},
                    resource_yields={"basic_herb": 3},
                    upgrade_cost={"spirit_stone": 55},
                ),
                3: DwellingLevelSpec(
                    level=3,
                    maintenance_cost={"spirit_stone": 4},
                    resource_yields={"basic_herb": 5},
                ),
            },
        ),
        DwellingFacilitySpec(
            facility_id="spirit_spring",
            display_name="灵泉",
            facility_type="production",
            summary="提供炼丹辅用灵泉水，作为中期炼丹品质与成功率的稳定辅助。",
            build_cost={"spirit_stone": 70},
            max_level=3,
            function_unlock_text="灵泉已通，可为丹房额外提供灵泉水。",
            levels={
                1: DwellingLevelSpec(
                    level=1,
                    maintenance_cost={"spirit_stone": 3},
                    resource_yields={"spirit_spring_water": 1},
                    upgrade_cost={"spirit_stone": 50},
                ),
                2: DwellingLevelSpec(
                    level=2,
                    maintenance_cost={"spirit_stone": 4},
                    resource_yields={"spirit_spring_water": 2},
                    upgrade_cost={"spirit_stone": 65},
                ),
                3: DwellingLevelSpec(
                    level=3,
                    maintenance_cost={"spirit_stone": 5},
                    resource_yields={"spirit_spring_water": 3},
                ),
            },
        ),
        DwellingFacilitySpec(
            facility_id="mine_cave",
            display_name="矿洞",
            facility_type="production",
            summary="提供稳定灵石与基础矿材，是洞府最直接的保底现金流来源。",
            build_cost={"spirit_stone": 60},
            max_level=3,
            levels={
                1: DwellingLevelSpec(
                    level=1,
                    maintenance_cost={"spirit_stone": 3},
                    resource_yields={"spirit_stone": 4, "basic_ore": 1},
                    upgrade_cost={"spirit_stone": 45},
                ),
                2: DwellingLevelSpec(
                    level=2,
                    maintenance_cost={"spirit_stone": 4},
                    resource_yields={"spirit_stone": 7, "basic_ore": 2},
                    upgrade_cost={"spirit_stone": 60},
                ),
                3: DwellingLevelSpec(
                    level=3,
                    maintenance_cost={"spirit_stone": 5},
                    resource_yields={"spirit_stone": 10, "basic_ore": 3},
                ),
            },
        ),
        DwellingFacilitySpec(
            facility_id="alchemy_room",
            display_name="炼丹房",
            facility_type="function",
            summary="承载后续炼丹系统，本次只开放设施本体与入口占位。",
            build_cost={"spirit_stone": 80},
            max_level=3,
            function_unlock_text="炼丹入口已解锁，完整炼丹玩法将在后续版本补齐。",
            levels={
                1: DwellingLevelSpec(
                    level=1,
                    maintenance_cost={"spirit_stone": 3},
                    resource_yields={},
                    upgrade_cost={"spirit_stone": 55},
                ),
                2: DwellingLevelSpec(
                    level=2,
                    maintenance_cost={"spirit_stone": 4},
                    resource_yields={},
                    upgrade_cost={"spirit_stone": 70},
                ),
                3: DwellingLevelSpec(
                    level=3,
                    maintenance_cost={"spirit_stone": 5},
                    resource_yields={},
                ),
            },
        ),
        DwellingFacilitySpec(
            facility_id="spirit_gathering_array",
            display_name="聚灵阵",
            facility_type="boost",
            summary="按月提供固定修为，并持续辅助突破准备。",
            build_cost={"spirit_stone": 100},
            max_level=3,
            function_unlock_text="聚灵阵正在运转，可持续辅助修炼与突破。",
            levels={
                1: DwellingLevelSpec(
                    level=1,
                    maintenance_cost={"spirit_stone": 4},
                    resource_yields={},
                    cultivation_exp_gain=6,
                    upgrade_cost={"spirit_stone": 70},
                ),
                2: DwellingLevelSpec(
                    level=2,
                    maintenance_cost={"spirit_stone": 5},
                    resource_yields={},
                    cultivation_exp_gain=10,
                    upgrade_cost={"spirit_stone": 90},
                ),
                3: DwellingLevelSpec(
                    level=3,
                    maintenance_cost={"spirit_stone": 6},
                    resource_yields={},
                    cultivation_exp_gain=14,
                ),
            },
        ),
    ]
