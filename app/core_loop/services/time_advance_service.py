from __future__ import annotations

from copy import deepcopy

from app.core_loop.services.event_service import EventService
from app.core_loop.types import ConflictError, RunState


class TimeAdvanceService:
    def __init__(self, event_service: EventService) -> None:
        self._event_service = event_service

    def advance(self, run: RunState, rebirth_count: int = 0) -> RunState:
        if run.character.is_dead:
            raise ConflictError("dead characters cannot advance time")
        if run.current_event is not None:
            raise ConflictError("resolve the current event before advancing time")

        next_run = deepcopy(run)
        next_run.round_index += 1
        next_run.character.lifespan_current -= 1
        next_run.event_cooldowns = {
            event_id: remaining - 1
            for event_id, remaining in next_run.event_cooldowns.items()
            if remaining - 1 > 0
        }

        if next_run.character.lifespan_current <= 0:
            next_run.character.lifespan_current = 0
            next_run.character.is_dead = True
            run.round_index = next_run.round_index
            run.character.lifespan_current = next_run.character.lifespan_current
            run.character.is_dead = next_run.character.is_dead
            run.result_summary = "瀵垮厓褰掗浂锛屾湰灞€缁撴潫銆?"
            return run

        next_event = self._event_service.select_event(
            next_run,
            rebirth_count=rebirth_count,
        )
        run.round_index = next_run.round_index
        run.character.lifespan_current = next_run.character.lifespan_current
        run.current_event = next_event
        run.result_summary = "鏂扮殑浜嬩欢宸茬粡鍑虹幇銆?"
        return run
