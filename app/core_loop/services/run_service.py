from __future__ import annotations

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
    def __init__(self, event_config_base_path: str | None = None) -> None:
        self._repo = InMemoryRunRepository()
        self._event_config_base_path = event_config_base_path
        self._realm_config_base_path = event_config_base_path
        self._dwelling_service = DwellingService(base_path=event_config_base_path)
        self._alchemy_service = AlchemyService(base_path=event_config_base_path)
        self._rebirth_service = RebirthService()
        self._rebirth_point_service = RebirthPointService(base_path=event_config_base_path)
        self._resource_sale_service = ResourceSaleService(base_path=event_config_base_path)
        self._resource_conversion_service = ResourceConversionService(
            base_path=event_config_base_path
        )
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
        updated = self._event_resolution_service.resolve(run, option_id)
        self._hydrate_runtime_metadata(updated)
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
        self._resource_conversion_service.convert_spirit_stone_to_cultivation(run, amount)
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
            economy_base_path=self._event_config_base_path,
        )
        self._time_advance_service = TimeAdvanceService(
            self._event_service,
            self._dwelling_service,
            self._alchemy_service,
        )

    def _sync_pending_event(self, run: RunState) -> RunState:
        if run.current_event is None:
            return run

        run.current_event = self._event_service.refresh_pending_event(run)
        return self._repo.save(run)

    def _hydrate_runtime_metadata(self, run: RunState) -> None:
        self._dwelling_service.hydrate_run(run)
        self._alchemy_service.hydrate_run(run)
        current_realm_key = resolve_realm_key(run.character.realm, self._realm_configs)
        current_index = next(
            (
                index
                for index, config in enumerate(self._realm_configs)
                if config.key == current_realm_key
            ),
            None,
        )
        if current_index is None:
            run.character.realm_display_name = run.character.realm
            run.breakthrough_requirements = None
            return

        current_realm = self._realm_configs[current_index]
        run.character.realm_display_name = current_realm.display_name or current_realm.key

        if current_index >= len(self._realm_configs) - 1:
            run.breakthrough_requirements = None
            return

        next_realm = self._realm_configs[current_index + 1]
        run.breakthrough_requirements = BreakthroughRequirements(
            target_realm_key=next_realm.key,
            target_realm_display_name=next_realm.display_name or next_realm.key,
            required_cultivation_exp=current_realm.required_exp,
            required_spirit_stone=current_realm.required_spirit_stone,
        )
