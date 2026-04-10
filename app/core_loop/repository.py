from __future__ import annotations

from uuid import uuid4

from app.core_loop.repository_state import build_initial_run
from app.core_loop.types import NotFoundError, PlayerProfile, RepositoryState, RunState


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._state = RepositoryState()

    def reset(self) -> None:
        self._state = RepositoryState()

    def create(self, player_id: str, permanent_luck_bonus: int = 0) -> RunState:
        run_id = uuid4().hex
        run = build_initial_run(
            run_id=run_id,
            player_id=player_id,
            permanent_luck_bonus=permanent_luck_bonus,
        )
        self._state.runs[run_id] = run
        return run

    def get(self, run_id: str) -> RunState:
        try:
            return self._state.runs[run_id]
        except KeyError as error:
            raise NotFoundError(
                f"run '{run_id}' not found",
                code="core.run.not_found",
                params={"run_id": run_id},
            ) from error

    def save(self, run: RunState) -> RunState:
        self._state.runs[run.run_id] = run
        return run

    def get_or_create_profile(self, player_id: str) -> PlayerProfile:
        if player_id not in self._state.profiles:
            self._state.profiles[player_id] = PlayerProfile(player_id=player_id)
        return self._state.profiles[player_id]
