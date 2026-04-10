from __future__ import annotations

from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.seeds import get_realm_configs
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
        return CombatActorState(
            name=run.character.name,
            realm_label=realm_config.display_name,
            hp_current=run.character.hp_current,
            hp_max=run.character.hp_max,
            attack=8 + realm_config.order_index + progress_bonus,
            defense=2 + realm_config.stage_index + progress_bonus + realm_config.order_index // 5,
            speed=6 + realm_config.stage_index + (progress_bonus // 2) + realm_config.order_index // 5,
        )

    def _resolve_progress_bonus(self, run: RunState, current_index: int) -> int:
        local_progress = max(
            0,
            run.character.cultivation_exp - self._get_stage_entry_exp(current_index),
        )
        progress_bonus = local_progress // 15
        if self._get_stage_progress_target(current_index) >= 180:
            return min(2, progress_bonus)
        return min(3, progress_bonus)

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
