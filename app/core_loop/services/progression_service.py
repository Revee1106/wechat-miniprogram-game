from __future__ import annotations

from app.core_loop.seeds import get_realm_configs
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.types import BreakthroughResult, ConflictError, RunState


class ProgressionService:
    def __init__(self, dwelling_service: DwellingService) -> None:
        self._realm_configs = get_realm_configs()
        self._dwelling_service = dwelling_service

    def try_breakthrough(self, run: RunState) -> BreakthroughResult:
        if run.character.is_dead:
            raise ConflictError("dead characters cannot breakthrough")

        current_index = next(
            index
            for index, config in enumerate(self._realm_configs)
            if config.key == run.character.realm
        )
        if current_index >= len(self._realm_configs) - 1:
            raise ConflictError("already at maximum realm")

        current_realm = self._realm_configs[current_index]
        next_realm = self._realm_configs[current_index + 1]
        if run.character.cultivation_exp < current_realm.required_exp:
            raise ConflictError("not enough cultivation exp to breakthrough")
        if run.resources.spirit_stone < 50:
            raise ConflictError("not enough spirit stones to breakthrough")

        success_rate = min(
            0.95,
            current_realm.base_success_rate
            + 0.10
            + run.character.pill_bonus
            + run.character.technique_bonus
            - run.character.status_penalty
            + min(run.character.luck * 0.02, 0.10)
            + self._dwelling_service.get_breakthrough_bonus(run.dwelling_level),
        )

        run.resources.spirit_stone -= 50
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
