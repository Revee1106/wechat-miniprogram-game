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
        rng=lambda: 0.0,
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
        rng=lambda: 0.0,
    ).try_breakthrough(run)

    assert next_realm.required_materials == {"basic_breakthrough_material": 2}
    assert result.success is True


def test_breakthrough_failure_applies_target_realm_penalty_to_cultivation() -> None:
    current_realm, next_realm = _build_realm_chain(
        target_success_rate=0.1,
        failure_penalty={"character": {"cultivation_exp": -40}},
    )
    run = _build_run()
    run.character.cultivation_exp = 150
    run.resources.spirit_stone = 20

    result = ProgressionService(
        DwellingService(),
        realm_configs=[current_realm, next_realm],
        rng=lambda: 0.95,
    ).try_breakthrough(run)

    assert result.success is False
    assert result.previous_realm == "qi_refining_early"
    assert result.new_realm == "qi_refining_early"
    assert result.character.realm == "qi_refining_early"
    assert result.character.cultivation_exp == 110
    assert result.resources.spirit_stone == 0


def _build_realm_chain(
    required_materials: dict[str, int] | None = None,
    target_success_rate: float = 0.95,
    failure_penalty: dict[str, dict[str, int]] | None = None,
) -> tuple[RealmConfig, RealmConfig]:
    return (
        RealmConfig(
            key="qi_refining_early",
            display_name="Qi Refining Early",
            major_realm="qi_refining",
            stage_index=1,
            order_index=1,
            lifespan_bonus=6,
            base_success_rate=0,
            required_exp=0,
            required_spirit_stone=0,
        ),
        RealmConfig(
            key="qi_refining_mid",
            display_name="Qi Refining Mid",
            major_realm="qi_refining",
            stage_index=2,
            order_index=2,
            lifespan_bonus=6,
            base_success_rate=target_success_rate,
            required_exp=100,
            required_spirit_stone=20,
            required_materials=required_materials or {},
            failure_penalty=failure_penalty or {},
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
