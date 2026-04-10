from __future__ import annotations

import random
from collections.abc import Callable

from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.seeds import get_realm_configs
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.types import BreakthroughResult, ConflictError, RealmConfig, RunState


class ProgressionService:
    def __init__(
        self,
        dwelling_service: DwellingService,
        realm_configs: list[RealmConfig] | None = None,
        rng: Callable[[], float] | None = None,
    ) -> None:
        self._realm_configs = list(realm_configs) if realm_configs is not None else get_realm_configs()
        self._dwelling_service = dwelling_service
        self._rng = rng if rng is not None else random.random

    def try_breakthrough(self, run: RunState) -> BreakthroughResult:
        if run.character.is_dead:
            raise ConflictError(
                "dead characters cannot breakthrough",
                code="core.breakthrough.dead_character_cannot_breakthrough",
            )

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
            raise ConflictError(
                f"unknown realm '{run.character.realm}'",
                code="core.realm.unknown",
                params={"realm": run.character.realm},
            )
        if current_index >= len(self._realm_configs) - 1:
            raise ConflictError(
                "already at maximum realm",
                code="core.breakthrough.already_at_maximum_realm",
            )

        current_realm = self._realm_configs[current_index]
        target_realm = self._realm_configs[current_index + 1]
        required_cultivation_exp = self._get_cumulative_required_exp(current_index + 1)
        if run.character.cultivation_exp < required_cultivation_exp:
            raise ConflictError(
                "not enough cultivation exp to breakthrough",
                code="core.breakthrough.not_enough_cultivation_exp",
            )
        if run.resources.spirit_stone < target_realm.required_spirit_stone:
            raise ConflictError(
                "not enough spirit stones to breakthrough",
                code="core.breakthrough.not_enough_spirit_stones",
            )

        success_rate = min(
            1.0,
            target_realm.base_success_rate
            + 0.10
            + min(run.character.breakthrough_bonus * 0.01, 0.20)
            + run.character.pill_bonus
            + run.character.technique_bonus
            - run.character.status_penalty
            + min(run.character.luck * 0.02, 0.10)
            + self._dwelling_service.get_breakthrough_bonus(run),
        )

        run.resources.spirit_stone -= target_realm.required_spirit_stone
        previous_realm = run.character.realm

        if self._rng() < success_rate:
            run.character.realm = target_realm.key
            run.character.lifespan_max += target_realm.lifespan_bonus
            run.character.lifespan_current = min(
                run.character.lifespan_max,
                run.character.lifespan_current + target_realm.lifespan_bonus,
            )
            run.result_summary = (
                f"breakthrough success: {current_realm.display_name} -> {target_realm.display_name}"
            )
            return BreakthroughResult(
                success=True,
                previous_realm=previous_realm,
                new_realm=target_realm.key,
                success_rate=success_rate,
                message=run.result_summary,
                character=run.character,
                resources=run.resources,
            )

        cultivation_penalty = target_realm.failure_penalty.get("character", {}).get(
            "cultivation_exp",
            0,
        )
        run.character.cultivation_exp = max(
            0,
            run.character.cultivation_exp + cultivation_penalty,
        )
        run.result_summary = (
            f"breakthrough failed: {current_realm.display_name} -> {target_realm.display_name}"
        )
        return BreakthroughResult(
            success=False,
            previous_realm=previous_realm,
            new_realm=previous_realm,
            success_rate=success_rate,
            message=run.result_summary,
            character=run.character,
            resources=run.resources,
        )

    def _get_cumulative_required_exp(self, target_index: int) -> int:
        return sum(
            max(0, int(config.required_exp))
            for config in self._realm_configs[: target_index + 1]
        )
