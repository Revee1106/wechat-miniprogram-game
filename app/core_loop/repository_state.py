from __future__ import annotations

from app.core_loop.realm_config import load_realm_configs
from app.core_loop.types import CharacterState, ResourceState, RunState


MONTHS_PER_YEAR = 12
INITIAL_LIFESPAN_YEARS = 60


def build_initial_run(
    run_id: str,
    player_id: str,
    permanent_luck_bonus: int = 0,
) -> RunState:
    lifespan_max = INITIAL_LIFESPAN_YEARS * MONTHS_PER_YEAR
    initial_hp_max = _get_initial_hp_max()
    return RunState(
        run_id=run_id,
        player_id=player_id,
        round_index=0,
        character=CharacterState(
            name=f"{player_id}-wanderer",
            realm="qi_refining_early",
            cultivation_exp=0,
            lifespan_current=lifespan_max,
            lifespan_max=lifespan_max,
            hp_current=initial_hp_max,
            hp_max=initial_hp_max,
            luck=permanent_luck_bonus,
        ),
        resources=ResourceState(),
        dwelling_level=1,
        dwelling_facilities=[],
        dwelling_last_settlement=None,
    )


def _get_initial_hp_max() -> int:
    initial_realm = next(
        (realm for realm in load_realm_configs() if realm.key == "qi_refining_early"),
        None,
    )
    if initial_realm is None or initial_realm.hp_max <= 0:
        return 100
    return initial_realm.hp_max
