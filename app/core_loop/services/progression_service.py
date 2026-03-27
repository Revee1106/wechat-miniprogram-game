from __future__ import annotations

from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.seeds import get_realm_configs
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.types import BreakthroughResult, ConflictError, RealmConfig, RunState


class ProgressionService:
    def __init__(
        self,
        dwelling_service: DwellingService,
        realm_configs: list[RealmConfig] | None = None,
    ) -> None:
        self._realm_configs = list(realm_configs) if realm_configs is not None else get_realm_configs()
        self._dwelling_service = dwelling_service

    def try_breakthrough(self, run: RunState) -> BreakthroughResult:
        if run.character.is_dead:
            raise ConflictError("dead characters cannot breakthrough")

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
            raise ConflictError(f"unknown realm '{run.character.realm}'")
        if current_index >= len(self._realm_configs) - 1:
            raise ConflictError("already at maximum realm")

        current_realm = self._realm_configs[current_index]
        next_realm = self._realm_configs[current_index + 1]
        if run.character.cultivation_exp < current_realm.required_exp:
            raise ConflictError("not enough cultivation exp to breakthrough")
        if run.resources.spirit_stone < current_realm.required_spirit_stone:
            raise ConflictError("not enough spirit stones to breakthrough")
        required_materials = current_realm.required_materials
        if required_materials:
            required_materials = dict(required_materials)

        success_rate = min(
            0.95,
            current_realm.base_success_rate
            + 0.10
            + min(run.character.breakthrough_bonus * 0.01, 0.20)
            + run.character.pill_bonus
            + run.character.technique_bonus
            - run.character.status_penalty
            + min(run.character.luck * 0.02, 0.10)
            + self._dwelling_service.get_breakthrough_bonus(run.dwelling_level),
        )

        run.resources.spirit_stone -= current_realm.required_spirit_stone
        previous_realm = run.character.realm
        run.character.realm = next_realm.key
        run.character.lifespan_max += next_realm.lifespan_bonus
        run.character.lifespan_current = min(
            run.character.lifespan_max,
            run.character.lifespan_current + next_realm.lifespan_bonus,
        )
        run.result_summary = (
            f"突破成功：{current_realm.display_name} -> {next_realm.display_name}"
        )

        return BreakthroughResult(
            success=True,
            previous_realm=previous_realm,
            new_realm=next_realm.key,
            success_rate=success_rate,
            message=run.result_summary,
            character=run.character,
            resources=run.resources,
        )
