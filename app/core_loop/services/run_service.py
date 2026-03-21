from __future__ import annotations

from app.core_loop.repository import InMemoryRunRepository
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.event_service import EventService
from app.core_loop.services.progression_service import ProgressionService
from app.core_loop.services.rebirth_service import RebirthService
from app.core_loop.services.time_advance_service import TimeAdvanceService
from app.core_loop.types import RebirthResult, RunState


class RunService:
    def __init__(self) -> None:
        self._repo = InMemoryRunRepository()
        self._event_service = EventService()
        self._dwelling_service = DwellingService()
        self._time_advance_service = TimeAdvanceService(self._event_service)
        self._progression_service = ProgressionService(self._dwelling_service)
        self._rebirth_service = RebirthService()

    def reset(self) -> None:
        self._repo.reset()

    def create_run(self, player_id: str) -> RunState:
        profile = self._repo.get_or_create_profile(player_id)
        return self._repo.create(
            player_id=player_id,
            permanent_luck_bonus=profile.permanent_luck_bonus,
        )

    def get_run(self, run_id: str) -> RunState:
        return self._repo.get(run_id)

    def advance_time(self, run_id: str) -> RunState:
        run = self._repo.get(run_id)
        updated = self._time_advance_service.advance(run)
        return self._repo.save(updated)

    def resolve_event(self, run_id: str, choice_key: str) -> RunState:
        run = self._repo.get(run_id)
        updated = self._event_service.resolve_choice(run, choice_key)
        return self._repo.save(updated)

    def breakthrough(self, run_id: str):
        run = self._repo.get(run_id)
        outcome = self._progression_service.try_breakthrough(run)
        self._repo.save(run)
        return outcome

    def rebirth(self, run_id: str) -> RebirthResult:
        run = self._repo.get(run_id)
        profile = self._repo.get_or_create_profile(run.player_id)
        claimed_profile = self._rebirth_service.claim(profile, run)
        new_run = self.create_run(player_id=run.player_id)
        self._rebirth_service.apply_permanent_bonus(claimed_profile, new_run)
        self._repo.save(new_run)
        return RebirthResult(player_profile=claimed_profile, new_run=new_run)
