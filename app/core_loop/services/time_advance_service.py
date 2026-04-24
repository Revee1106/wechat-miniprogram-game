from __future__ import annotations

from copy import deepcopy

from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.seeds import get_realm_configs
from app.core_loop.services.alchemy_service import AlchemyService
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.event_service import EventService
from app.core_loop.types import ConflictError, RealmConfig, RunState


class TimeAdvanceService:
    def __init__(
        self,
        event_service: EventService,
        dwelling_service: DwellingService | None = None,
        alchemy_service: AlchemyService | None = None,
        realm_configs: list[RealmConfig] | None = None,
    ) -> None:
        self._event_service = event_service
        self._dwelling_service = dwelling_service or DwellingService()
        self._alchemy_service = alchemy_service or AlchemyService()
        self._realm_configs = list(realm_configs) if realm_configs is not None else get_realm_configs()

    def advance(
        self,
        run: RunState,
        rebirth_count: int = 0,
        allow_cultivation_penalty: bool = False,
    ) -> RunState:
        if run.character.is_dead:
            raise ConflictError(
                "dead characters cannot advance time",
                code="core.time.dead_character_cannot_advance",
            )
        if run.current_event is not None:
            raise ConflictError(
                "resolve the current event before advancing time",
                code="core.time.resolve_event_before_advance",
            )

        next_run = deepcopy(run)
        current_realm = self._get_current_realm_config(next_run)
        spirit_stone_cost = current_realm.base_spirit_stone_cost_per_advance
        penalty_summary = ""
        if next_run.resources.spirit_stone < spirit_stone_cost:
            if not allow_cultivation_penalty:
                raise ConflictError(
                    "not enough spirit stones to advance time",
                    code="core.time.not_enough_spirit_stones",
                )
            penalty = self._get_cultivation_penalty(next_run)
            next_run.character.cultivation_exp = max(
                0,
                int(next_run.character.cultivation_exp) - penalty,
            )
            penalty_summary = f"灵石不足，修为下降 {penalty} 点，时间继续推进。"
        else:
            next_run.resources.spirit_stone -= spirit_stone_cost
            next_run.character.cultivation_exp += current_realm.base_cultivation_gain_per_advance

        next_run.result_summary = ""
        next_run.round_index += 1
        next_run.character.lifespan_current -= 1
        next_run.dwelling_last_settlement = self._dwelling_service.settle_month(next_run)
        self._alchemy_service.advance_month(next_run)
        next_run.event_cooldowns = {
            event_id: remaining - 1
            for event_id, remaining in next_run.event_cooldowns.items()
            if remaining - 1 > 0
        }

        if next_run.character.lifespan_current <= 0:
            next_run.character.lifespan_current = 0
            next_run.character.is_dead = True
            next_run.result_summary = "寿元耗尽，此身行至终点。"
            return next_run

        next_run.current_event = self._event_service.select_event(
            next_run,
            rebirth_count=rebirth_count,
        )
        next_run.result_summary = penalty_summary or "时间推进一月，洞府完成本月结算。"
        return next_run

    def _get_current_realm_config(self, run: RunState) -> RealmConfig:
        current_realm_key = resolve_realm_key(run.character.realm, self._realm_configs)
        current_realm = next(
            (config for config in self._realm_configs if config.key == current_realm_key),
            None,
        )
        if current_realm is None:
            raise ConflictError(
                f"unknown realm '{run.character.realm}'",
                code="core.realm.unknown",
                params={"realm": run.character.realm},
            )
        return current_realm

    def _get_cultivation_penalty(self, run: RunState) -> int:
        current_realm_key = resolve_realm_key(run.character.realm, self._realm_configs)
        current_index = next(
            (
                index
                for index, config in enumerate(self._realm_configs)
                if config.key == current_realm_key
            ),
            None,
        )
        if current_index is None or current_index >= len(self._realm_configs) - 1:
            return 0
        required_exp = sum(
            max(0, int(config.required_exp))
            for config in self._realm_configs[: current_index + 2]
        )
        return max(0, int(required_exp * 0.1))
