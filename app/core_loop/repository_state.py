from __future__ import annotations

from app.core_loop.types import CharacterState, ResourceState, RunState


def build_initial_run(
    run_id: str,
    player_id: str,
    permanent_luck_bonus: int = 0,
) -> RunState:
    lifespan_max = 12
    return RunState(
        run_id=run_id,
        player_id=player_id,
        round_index=0,
        character=CharacterState(
            name=f"{player_id}-wanderer",
            realm="qi_refining",
            cultivation_exp=0,
            lifespan_current=lifespan_max,
            lifespan_max=lifespan_max,
            luck=permanent_luck_bonus,
        ),
        resources=ResourceState(),
        dwelling_level=1,
    )
