from __future__ import annotations

from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.seeds import get_realm_configs
from app.core_loop.services.equipment_service import EquipmentService
from app.core_loop.types import CombatActorState, ConflictError, RealmConfig, RunState


class CombatStatService:
    def __init__(self, realm_configs: list[RealmConfig] | None = None) -> None:
        self._realm_configs = list(realm_configs) if realm_configs is not None else get_realm_configs()

    def build_player_state(self, run: RunState) -> CombatActorState:
        realm_key = resolve_realm_key(run.character.realm, self._realm_configs)
        current_index = next(
            (index for index, config in enumerate(self._realm_configs) if config.key == realm_key),
            None,
        )
        if current_index is None:
            raise ConflictError(
                f"unknown realm '{run.character.realm}'",
                code="core.realm.unknown",
                params={"realm": run.character.realm},
            )
        realm_config = self._realm_configs[current_index]

        progress_bonus = self._resolve_progress_bonus(run, current_index)
        equipment_bonus = self._resolve_equipment_bonus(run)
        hp_max = run.character.hp_max + equipment_bonus["hp_max"]
        hp_current = min(hp_max, run.character.hp_current + equipment_bonus["hp_max"])
        return CombatActorState(
            name=run.character.name,
            realm_label=realm_config.display_name,
            hp_current=hp_current,
            hp_max=hp_max,
            attack=(
                10
                + realm_config.order_index * 2
                + progress_bonus
                + equipment_bonus["attack"]
            ),
            defense=(
                3
                + realm_config.stage_index * 2
                + progress_bonus
                + realm_config.order_index // 4
                + equipment_bonus["defense"]
            ),
            speed=(
                6
                + realm_config.stage_index
                + (progress_bonus // 2)
                + realm_config.order_index // 5
                + equipment_bonus["speed"]
            ),
        )

    def _resolve_equipment_bonus(self, run: RunState) -> dict[str, int]:
        if run.equipment_inventory:
            bonus = {
                "attack": 0,
                "defense": 0,
                "speed": 0,
                "hp_max": 0,
            }
            equipped_ids = set(run.character.equipped_items.values())
            for item in run.equipment_inventory:
                if not item.is_equipped and item.item_id not in equipped_ids:
                    continue
                bonus["attack"] += int(item.attack)
                bonus["defense"] += int(item.defense)
                bonus["speed"] += int(item.speed)
                bonus["hp_max"] += int(item.hp_max)
            return bonus
        return EquipmentService().get_equipped_stat_bonus(run)

    def _resolve_progress_bonus(self, run: RunState, current_index: int) -> int:
        local_progress = max(
            0,
            run.character.cultivation_exp - self._get_stage_entry_exp(current_index),
        )
        return min(6, local_progress // 30)

    def _get_stage_entry_exp(self, current_index: int) -> int:
        return sum(
            max(0, int(config.required_exp))
            for config in self._realm_configs[:current_index]
        )

    def _get_stage_progress_target(self, current_index: int) -> int:
        current_required_exp = max(0, int(self._realm_configs[current_index].required_exp))
        if current_required_exp > 0:
            return current_required_exp

        for config in self._realm_configs[current_index + 1 :]:
            if config.major_realm == self._realm_configs[current_index].major_realm:
                return max(0, int(config.required_exp))
        return 60
