from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.progression_service import ProgressionService
from app.core_loop.types import CharacterState, RealmConfig, ResourceState, RunState


def test_breakthrough_still_uses_cultivation_and_spirit_stone_after_economy_refactor() -> None:
    current_realm, next_realm = _build_realm_chain()
    run = _build_run()
    run.character.cultivation_exp = 100
    run.resources.spirit_stone = 20

    result = ProgressionService(
        DwellingService(),
        realm_configs=[current_realm, next_realm],
    ).try_breakthrough(run)

    assert result.success is True
    assert result.resources.spirit_stone == 0


def test_breakthrough_requirement_shape_supports_future_material_keys() -> None:
    current_realm, next_realm = _build_realm_chain(
        required_materials={"basic_breakthrough_material": 2}
    )
    run = _build_run()
    run.character.cultivation_exp = 100
    run.resources.spirit_stone = 20

    result = ProgressionService(
        DwellingService(),
        realm_configs=[current_realm, next_realm],
    ).try_breakthrough(run)

    assert current_realm.required_materials == {"basic_breakthrough_material": 2}
    assert result.success is True


def _build_realm_chain(
    required_materials: dict[str, int] | None = None,
) -> tuple[RealmConfig, RealmConfig]:
    return (
        RealmConfig(
            key="qi_refining_early",
            display_name="Qi Refining Early",
            major_realm="qi_refining",
            stage_index=1,
            order_index=1,
            lifespan_bonus=6,
            base_success_rate=0.95,
            required_exp=100,
            required_spirit_stone=20,
            required_materials=required_materials or {},
        ),
        RealmConfig(
            key="qi_refining_mid",
            display_name="Qi Refining Mid",
            major_realm="qi_refining",
            stage_index=2,
            order_index=2,
            lifespan_bonus=6,
            base_success_rate=0.90,
            required_exp=200,
            required_spirit_stone=30,
        ),
    )


def _build_run() -> RunState:
    return RunState(
        run_id="run-test",
        player_id="player-test",
        round_index=1,
        character=CharacterState(
            name="player-test-wanderer",
            realm="qi_refining_early",
            cultivation_exp=0,
            lifespan_current=240,
            lifespan_max=240,
            luck=0,
        ),
        resources=ResourceState(
            spirit_stone=0,
            herbs=3,
            iron_essence=0,
        ),
    )
