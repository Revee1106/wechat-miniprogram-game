from __future__ import annotations

from app.core_loop.realm_config import load_realm_configs
from app.core_loop.event_config import load_event_registry
from app.core_loop.repository import InMemoryRunRepository
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.event_service import EventService
from app.core_loop.services.event_resolution_service import EventResolutionService
from app.core_loop.services.progression_service import ProgressionService
from app.core_loop.services.rebirth_service import RebirthService
from app.core_loop.services.time_advance_service import TimeAdvanceService
from app.core_loop.types import RebirthResult, RunState


class RunService:
    def __init__(self, event_config_base_path: str | None = None) -> None:
        self._repo = InMemoryRunRepository()
        self._event_config_base_path = event_config_base_path
        self._realm_config_base_path = event_config_base_path
        self._dwelling_service = DwellingService()
        self._rebirth_service = RebirthService()
        self._realm_configs = load_realm_configs(base_path=self._realm_config_base_path)
        self._progression_service = ProgressionService(
            self._dwelling_service,
            realm_configs=self._realm_configs,
        )
        self._event_registry = load_event_registry(base_path=event_config_base_path)
        self._rebuild_runtime_services()

    def reset(self) -> None:
        self._repo.reset()

    def create_run(self, player_id: str) -> RunState:
        profile = self._repo.get_or_create_profile(player_id)
        return self._repo.create(
            player_id=player_id,
            permanent_luck_bonus=profile.permanent_luck_bonus,
        )

    def get_run(self, run_id: str) -> RunState:
        run = self._repo.get(run_id)
        return self._sync_pending_event(run)

    def advance_time(self, run_id: str) -> RunState:
        run = self._repo.get(run_id)
        run = self._sync_pending_event(run)
        profile = self._repo.get_or_create_profile(run.player_id)
        updated = self._time_advance_service.advance(
            run,
            rebirth_count=profile.total_rebirth_count,
        )
        return self._repo.save(updated)

    def resolve_event(self, run_id: str, option_id: str) -> RunState:
        run = self._repo.get(run_id)
        run = self._sync_pending_event(run)
        updated = self._event_resolution_service.resolve(run, option_id)
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

    def reload_event_config(self, event_config_base_path: str | None = None) -> None:
        if event_config_base_path is not None:
            self._event_config_base_path = event_config_base_path
        self._event_registry = load_event_registry(base_path=self._event_config_base_path)
        self._rebuild_runtime_services()

    def reload_realm_config(self, realm_config_base_path: str | None = None) -> None:
        if realm_config_base_path is not None:
            self._realm_config_base_path = realm_config_base_path
        self._realm_configs = load_realm_configs(base_path=self._realm_config_base_path)
        self._rebuild_runtime_services()

    def _rebuild_runtime_services(self) -> None:
        self._progression_service = ProgressionService(
            self._dwelling_service,
            realm_configs=self._realm_configs,
        )
        self._event_service = EventService(
            registry=self._event_registry,
            realm_configs=self._realm_configs,
        )
        self._event_resolution_service = EventResolutionService(
            registry=self._event_registry,
            realm_configs=self._realm_configs,
        )
        self._time_advance_service = TimeAdvanceService(self._event_service)

    def _sync_pending_event(self, run: RunState) -> RunState:
        if run.current_event is None:
            return run

        run.current_event = self._event_service.refresh_pending_event(run)
        return self._repo.save(run)
