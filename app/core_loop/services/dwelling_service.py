from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from app.admin.repositories.dwelling_config_repository import DwellingConfigRepository
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
    entry_cost: dict[str, int]
    maintenance_cost: dict[str, int]
    resource_yields: dict[str, int]
    cultivation_exp_gain: int = 0
    special_effects: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class DwellingFacilitySpec:
    facility_id: str
    display_name: str
    facility_type: str
    summary: str
    function_unlock_text: str
    levels: dict[int, DwellingLevelSpec]

    @property
    def max_level(self) -> int:
        return max(self.levels.keys(), default=0)

    @property
    def build_cost(self) -> dict[str, int]:
        level_one = self.levels.get(1)
        return dict(level_one.entry_cost) if level_one is not None else {}


class DwellingService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)
        self._repository = DwellingConfigRepository(base_path=base_path)
        self._facility_specs: list[DwellingFacilitySpec] = []
        self._specs_by_id: dict[str, DwellingFacilitySpec] = {}
        self.reload_config(base_path=base_path)

    def reload_config(self, base_path: str | None = None) -> None:
        if base_path is not None:
            self._resource_service = RunResourceService(base_path=base_path)
            self._repository = DwellingConfigRepository(base_path=base_path)

        payload = self._repository.load()
        self._facility_specs = _load_facility_specs(payload.get("facilities", []))
        self._specs_by_id = {
            facility_spec.facility_id: facility_spec for facility_spec in self._facility_specs
        }

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

        next_level_spec = spec.levels[facility.level + 1]
        self._spend_cost(run, next_level_spec.entry_cost)
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
        return self._get_array_special_effect(run, "breakthrough_bonus_rate")

    def get_mine_spirit_stone_bonus(self, run: RunState) -> float:
        return self._get_array_special_effect(run, "mine_spirit_stone_bonus_rate")

    def _get_array_special_effect(self, run: RunState, effect_key: str) -> float:
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

        spec = self._specs_by_id.get("spirit_gathering_array")
        if spec is None:
            return 0.0
        level_spec = spec.levels.get(facility.level)
        if level_spec is None:
            return 0.0
        return float(level_spec.special_effects.get(effect_key, 0.0) or 0.0)

    def _get_facility(
        self,
        run: RunState,
        facility_id: str,
    ) -> tuple[DwellingFacilityState, DwellingFacilitySpec]:
        facility = next(
            (item for item in run.dwelling_facilities if item.facility_id == facility_id),
            None,
        )
        spec = self._specs_by_id.get(facility_id)
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
        facility.build_cost = spec.build_cost
        facility.function_unlock_text = spec.function_unlock_text
        facility.is_function_unlocked = facility.level > 0 and bool(spec.function_unlock_text)

        if facility.level <= 0:
            facility.status = "unbuilt"
            facility.next_upgrade_cost = spec.build_cost
            facility.maintenance_cost = {}
            facility.monthly_resource_yields = {}
            facility.monthly_cultivation_exp_gain = 0
            return

        level_spec = spec.levels[facility.level]
        facility.maintenance_cost = dict(level_spec.maintenance_cost)
        facility.monthly_resource_yields = dict(level_spec.resource_yields)
        facility.monthly_cultivation_exp_gain = level_spec.cultivation_exp_gain
        next_level_spec = spec.levels.get(facility.level + 1)
        facility.next_upgrade_cost = (
            dict(next_level_spec.entry_cost) if next_level_spec is not None else {}
        )
        if facility.status != "stalled":
            facility.status = self._active_status_for_level(facility.level, spec.max_level)

    def _can_afford(self, run: RunState, cost: dict[str, int]) -> bool:
        return all(
            self._get_resource_amount(run, resource_key) >= amount
            for resource_key, amount in cost.items()
        )

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

        bonus_rate = self.get_mine_spirit_stone_bonus(run)
        yields["spirit_stone"] = max(
            spirit_stone_gain,
            int(spirit_stone_gain * (1 + bonus_rate)),
        )
        return yields

    def _active_status_for_level(self, level: int, max_level: int) -> str:
        if level >= max_level:
            return "max_level"
        return "active"


def _load_facility_specs(facilities: list[dict[str, object]]) -> list[DwellingFacilitySpec]:
    specs: list[DwellingFacilitySpec] = []
    for facility in facilities:
        facility_id = str(facility.get("facility_id", "")).strip()
        if not facility_id:
            continue

        levels_payload = facility.get("levels") or []
        levels: dict[int, DwellingLevelSpec] = {}
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                level = _coerce_int(level_payload.get("level"), default=0)
                if level <= 0:
                    continue
                levels[level] = DwellingLevelSpec(
                    level=level,
                    entry_cost=_coerce_int_map(level_payload.get("entry_cost")),
                    maintenance_cost=_coerce_int_map(level_payload.get("maintenance_cost")),
                    resource_yields=_coerce_int_map(level_payload.get("resource_yields")),
                    cultivation_exp_gain=_coerce_int(
                        level_payload.get("cultivation_exp_gain"),
                        default=0,
                    ),
                    special_effects=_coerce_float_map(level_payload.get("special_effects")),
                )

        specs.append(
            DwellingFacilitySpec(
                facility_id=facility_id,
                display_name=str(facility.get("display_name", "")).strip(),
                facility_type=str(facility.get("facility_type", "")).strip(),
                summary=str(facility.get("summary", "")).strip(),
                function_unlock_text=str(facility.get("function_unlock_text", "")).strip(),
                levels=dict(sorted(levels.items(), key=lambda item: item[0])),
            )
        )
    return specs


def _coerce_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_int_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        resource_key = str(key).strip()
        if not resource_key:
            continue
        result[resource_key] = _coerce_int(raw, default=0)
    return result


def _coerce_float_map(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, float] = {}
    for key, raw in value.items():
        effect_key = str(key).strip()
        if not effect_key or isinstance(raw, bool):
            continue
        try:
            result[effect_key] = float(raw)
        except (TypeError, ValueError):
            continue
    return result

