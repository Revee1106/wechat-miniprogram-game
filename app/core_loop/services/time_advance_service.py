from __future__ import annotations

from app.core_loop.services.event_service import EventService
from app.core_loop.types import ConflictError, RunState


class TimeAdvanceService:
    def __init__(self, event_service: EventService) -> None:
        self._event_service = event_service

    def advance(self, run: RunState) -> RunState:
        if run.character.is_dead:
            raise ConflictError("dead characters cannot advance time")
        if run.current_event is not None:
            raise ConflictError("resolve the current event before advancing time")

        run.round_index += 1
        run.character.lifespan_current -= 1

        if run.character.lifespan_current <= 0:
            run.character.is_dead = True
            run.result_summary = "寿元归零，本局结束。"
            return run

        run.current_event = self._event_service.select_event_for_realm(
            run.character.realm,
            run.round_index,
        )
        run.result_summary = "新的事件已经出现。"
        return run
