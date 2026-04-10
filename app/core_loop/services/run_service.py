from __future__ import annotations

from copy import deepcopy

from app.core_loop.seeds import get_realm_configs
from app.core_loop.realm_config import load_realm_configs, resolve_realm_key
from app.core_loop.event_config import load_event_registry
from app.core_loop.services.alchemy_service import AlchemyService
from app.core_loop.repository import InMemoryRunRepository
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.event_service import EventService
from app.core_loop.services.event_resolution_service import EventResolutionService
from app.core_loop.services.progression_service import ProgressionService
from app.core_loop.services.rebirth_service import RebirthService
from app.core_loop.services.time_advance_service import TimeAdvanceService
from app.core_loop.types import BreakthroughRequirements, RebirthResult, RunState
from app.economy.services.rebirth_point_service import RebirthPointService
from app.economy.services.resource_conversion_service import ResourceConversionService
from app.economy.services.resource_sale_service import ResourceSaleService


class RunService:
    def __init__(
        self,
        event_config_base_path: str | None = None,
        realm_config_base_path: str | None = None,
        dwelling_config_base_path: str | None = None,
    ) -> None:
        self._repo = InMemoryRunRepository()
        self._event_config_base_path = event_config_base_path
        self._realm_config_base_path = (
            realm_config_base_path if realm_config_base_path is not None else event_config_base_path
        )
        self._dwelling_config_base_path = (
            dwelling_config_base_path
            if dwelling_config_base_path is not None
            else event_config_base_path
        )
        self._dwelling_service = DwellingService(base_path=self._dwelling_config_base_path)
        self._alchemy_service = AlchemyService(base_path=event_config_base_path)
        self._rebirth_service = RebirthService()
        self._rebirth_point_service = RebirthPointService(base_path=event_config_base_path)
        self._resource_sale_service = ResourceSaleService(base_path=event_config_base_path)
        self._resource_conversion_service = ResourceConversionService(
            base_path=event_config_base_path
        )
        self._realm_configs = self._load_runtime_realm_configs()
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
        run = self._repo.create(
            player_id=player_id,
            permanent_luck_bonus=profile.permanent_luck_bonus,
        )
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def get_run(self, run_id: str) -> RunState:
        run = self._repo.get(run_id)
        run = self._sync_pending_event(run)
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def advance_time(self, run_id: str) -> RunState:
        run = self._repo.get(run_id)
        run = self._sync_pending_event(run)
        profile = self._repo.get_or_create_profile(run.player_id)
        updated = self._time_advance_service.advance(
            run,
            rebirth_count=profile.total_rebirth_count,
        )
        self._hydrate_runtime_metadata(updated)
        return self._repo.save(updated)

    def resolve_event(self, run_id: str, option_id: str) -> RunState:
        run = self._repo.get(run_id)
        run = self._sync_pending_event(run)
        before_resolution = deepcopy(run)
        updated = self._event_resolution_service.resolve(run, option_id)
        self._hydrate_runtime_metadata(updated)
        self._hydrate_event_resolution_log(before_resolution, updated)
        return self._repo.save(updated)

    def breakthrough(self, run_id: str):
        run = self._repo.get(run_id)
        outcome = self._progression_service.try_breakthrough(run)
        self._hydrate_runtime_metadata(run)
        outcome.breakthrough_requirements = run.breakthrough_requirements
        self._repo.save(run)
        return outcome

    def build_dwelling_facility(self, run_id: str, facility_id: str) -> RunState:
        run = self._repo.get(run_id)
        self._dwelling_service.build_facility(run, facility_id)
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def upgrade_dwelling_facility(self, run_id: str, facility_id: str) -> RunState:
        run = self._repo.get(run_id)
        self._dwelling_service.upgrade_facility(run, facility_id)
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def start_alchemy(
        self,
        run_id: str,
        recipe_id: str,
        use_spirit_spring: bool = False,
    ) -> RunState:
        run = self._repo.get(run_id)
        self._alchemy_service.start(run, recipe_id, use_spirit_spring=use_spirit_spring)
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def consume_alchemy_item(
        self,
        run_id: str,
        item_id: str,
        quality: str | None = None,
    ) -> RunState:
        run = self._repo.get(run_id)
        self._alchemy_service.consume(run, item_id, quality=quality)
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def rebirth(self, run_id: str) -> RebirthResult:
        run = self._repo.get(run_id)
        profile = self._repo.get_or_create_profile(run.player_id)
        claimed_profile = self._rebirth_service.claim(profile, run)
        claimed_profile.rebirth_points += self._rebirth_point_service.calculate(run)
        new_run = self.create_run(player_id=run.player_id)
        self._rebirth_service.apply_permanent_bonus(claimed_profile, new_run)
        self._hydrate_runtime_metadata(new_run)
        self._repo.save(new_run)
        return RebirthResult(player_profile=claimed_profile, new_run=new_run)

    def sell_resource(self, run_id: str, resource_key: str, amount: int) -> RunState:
        run = self._repo.get(run_id)
        self._resource_sale_service.sell(run, resource_key, amount)
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def convert_spirit_stone_to_cultivation(self, run_id: str, amount: int) -> RunState:
        run = self._repo.get(run_id)
        self._resource_conversion_service.convert_spirit_stone_to_cultivation(
            run,
            amount,
            cultivation_cap=self._get_breakthrough_cultivation_cap(run),
        )
        self._hydrate_runtime_metadata(run)
        return self._repo.save(run)

    def reload_event_config(self, event_config_base_path: str | None = None) -> None:
        if event_config_base_path is not None:
            self._event_config_base_path = event_config_base_path
        self._event_registry = load_event_registry(base_path=self._event_config_base_path)
        self._rebuild_runtime_services()

    def reload_realm_config(self, realm_config_base_path: str | None = None) -> None:
        if realm_config_base_path is not None:
            self._realm_config_base_path = realm_config_base_path
        self._realm_configs = self._load_runtime_realm_configs()
        self._rebuild_runtime_services()

    def reload_dwelling_config(self, dwelling_config_base_path: str | None = None) -> None:
        if dwelling_config_base_path is not None:
            self._dwelling_config_base_path = dwelling_config_base_path
        self._dwelling_service.reload_config(base_path=self._dwelling_config_base_path)
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
            economy_base_path=self._event_config_base_path,
        )
        self._time_advance_service = TimeAdvanceService(
            self._event_service,
            self._dwelling_service,
            self._alchemy_service,
            realm_configs=self._realm_configs,
        )

    def _load_runtime_realm_configs(self):
        realm_configs = load_realm_configs(base_path=self._realm_config_base_path)
        return realm_configs or get_realm_configs()

    def _sync_pending_event(self, run: RunState) -> RunState:
        if run.current_event is None:
            return run

        run.current_event = self._event_service.refresh_pending_event(run)
        return self._repo.save(run)

    def _hydrate_runtime_metadata(self, run: RunState) -> None:
        self._dwelling_service.hydrate_run(run)
        self._alchemy_service.hydrate_run(run)
        current_index = self._get_current_realm_index(run)
        if current_index is None:
            run.character.realm_display_name = run.character.realm
            run.breakthrough_requirements = None
            return

        current_realm = self._realm_configs[current_index]
        run.character.realm_display_name = current_realm.display_name or current_realm.key
        cultivation_cap = self._get_breakthrough_cultivation_cap(run, current_index=current_index)
        if cultivation_cap is not None:
            run.character.cultivation_exp = min(
                max(0, int(run.character.cultivation_exp)),
                cultivation_cap,
            )

        if current_index >= len(self._realm_configs) - 1:
            run.breakthrough_requirements = None
            return

        next_realm = self._realm_configs[current_index + 1]
        run.breakthrough_requirements = BreakthroughRequirements(
            target_realm_key=next_realm.key,
            target_realm_display_name=next_realm.display_name or next_realm.key,
            required_cultivation_exp=self._get_cumulative_required_exp(current_index + 1),
            required_spirit_stone=next_realm.required_spirit_stone,
        )

    def _hydrate_event_resolution_log(self, before_run: RunState, after_run: RunState) -> None:
        if after_run.last_event_resolution is None:
            return

        intended_cultivation = int(
            after_run.last_event_resolution.intended_character.get("cultivation_exp", 0)
        )
        actual_cultivation = int(after_run.character.cultivation_exp) - int(
            before_run.character.cultivation_exp
        )
        after_run.last_event_resolution.actual_character["cultivation_exp"] = actual_cultivation

        capped_cultivation = max(0, intended_cultivation - actual_cultivation)
        if capped_cultivation > 0:
            after_run.last_event_resolution.capped_character["cultivation_exp"] = capped_cultivation

    def _get_current_realm_index(self, run: RunState) -> int | None:
        current_realm_key = resolve_realm_key(run.character.realm, self._realm_configs)
        return next(
            (
                index
                for index, config in enumerate(self._realm_configs)
                if config.key == current_realm_key
            ),
            None,
        )

    def _get_breakthrough_cultivation_cap(
        self,
        run: RunState,
        *,
        current_index: int | None = None,
    ) -> int | None:
        resolved_index = current_index if current_index is not None else self._get_current_realm_index(run)
        if resolved_index is None or resolved_index >= len(self._realm_configs) - 1:
            return None
        return self._get_cumulative_required_exp(resolved_index + 1)

    def _get_cumulative_required_exp(self, target_index: int) -> int:
        return sum(
            max(0, int(config.required_exp))
            for config in self._realm_configs[: target_index + 1]
        )
