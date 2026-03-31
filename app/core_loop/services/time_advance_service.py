from __future__ import annotations

from copy import deepcopy

from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.event_service import EventService
from app.core_loop.types import ConflictError, RunState


class TimeAdvanceService:
    def __init__(
        self,
        event_service: EventService,
        dwelling_service: DwellingService | None = None,
    ) -> None:
        self._event_service = event_service
        self._dwelling_service = dwelling_service or DwellingService()

    def advance(self, run: RunState, rebirth_count: int = 0) -> RunState:
        if run.character.is_dead:
            raise ConflictError("dead characters cannot advance time")
        if run.current_event is not None:
            raise ConflictError("resolve the current event before advancing time")

        next_run = deepcopy(run)
        next_run.round_index += 1
        next_run.character.lifespan_current -= 1
        next_run.dwelling_last_settlement = self._dwelling_service.settle_month(next_run)
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
        next_run.result_summary = "时间推进一月，洞府完成本月结算。"
        return next_run
