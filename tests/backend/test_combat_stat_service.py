from app.core_loop.services.combat_stat_service import CombatStatService
from app.core_loop.types import CharacterState, RealmConfig, ResourceState, RunState


def test_build_player_combat_state_uses_realm_progress_and_hp() -> None:
    service = CombatStatService(
        realm_configs=[
            RealmConfig(
                key="qi_refining_early",
                display_name="炼气初期",
                major_realm="qi_refining",
                stage_index=1,
                order_index=1,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=0,
                required_spirit_stone=0,
                base_cultivation_gain_per_advance=6,
                base_spirit_stone_cost_per_advance=2,
            ),
            RealmConfig(
                key="qi_refining_mid",
                display_name="炼气中期",
                major_realm="qi_refining",
                stage_index=2,
                order_index=2,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=90,
                required_spirit_stone=15,
                base_cultivation_gain_per_advance=8,
                base_spirit_stone_cost_per_advance=3,
            ),
        ]
    )
    run = RunState(
        run_id="run-combat-stat",
        player_id="player-1",
        round_index=1,
        character=CharacterState(
            name="修士甲",
            realm="qi_refining",
            cultivation_exp=45,
            lifespan_current=120,
            lifespan_max=240,
            hp_current=88,
            hp_max=100,
        ),
        resources=ResourceState(),
    )

    state = service.build_player_state(run)

    assert state.name == "修士甲"
    assert state.realm_label == "炼气初期"
    assert state.hp_current == 88
    assert state.hp_max == 100
    assert state.attack == 12
    assert state.defense == 6
    assert state.speed == 8


def test_build_player_combat_state_uses_stage_local_progress_for_later_realms() -> None:
    service = CombatStatService(
        realm_configs=[
            RealmConfig(
                key="qi_refining_early",
                display_name="炼气初期",
                major_realm="qi_refining",
                stage_index=1,
                order_index=1,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=0,
                required_spirit_stone=0,
                base_cultivation_gain_per_advance=6,
                base_spirit_stone_cost_per_advance=2,
            ),
            RealmConfig(
                key="qi_refining_mid",
                display_name="炼气中期",
                major_realm="qi_refining",
                stage_index=2,
                order_index=2,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=90,
                required_spirit_stone=15,
                base_cultivation_gain_per_advance=8,
                base_spirit_stone_cost_per_advance=3,
            ),
            RealmConfig(
                key="qi_refining_late",
                display_name="炼气后期",
                major_realm="qi_refining",
                stage_index=3,
                order_index=3,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=130,
                required_spirit_stone=20,
                base_cultivation_gain_per_advance=10,
                base_spirit_stone_cost_per_advance=3,
            ),
            RealmConfig(
                key="qi_refining_peak",
                display_name="炼气大圆满",
                major_realm="qi_refining",
                stage_index=4,
                order_index=4,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=130,
                required_spirit_stone=20,
                base_cultivation_gain_per_advance=24,
                base_spirit_stone_cost_per_advance=4,
            ),
            RealmConfig(
                key="foundation_early",
                display_name="筑基初期",
                major_realm="foundation",
                stage_index=1,
                order_index=5,
                lifespan_bonus=360,
                base_success_rate=0.0,
                required_exp=220,
                required_spirit_stone=80,
                base_cultivation_gain_per_advance=30,
                base_spirit_stone_cost_per_advance=5,
            ),
            RealmConfig(
                key="foundation_mid",
                display_name="筑基中期",
                major_realm="foundation",
                stage_index=2,
                order_index=6,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=180,
                required_spirit_stone=35,
                base_cultivation_gain_per_advance=36,
                base_spirit_stone_cost_per_advance=7,
            ),
            RealmConfig(
                key="foundation_late",
                display_name="筑基后期",
                major_realm="foundation",
                stage_index=3,
                order_index=7,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=260,
                required_spirit_stone=45,
                base_cultivation_gain_per_advance=42,
                base_spirit_stone_cost_per_advance=8,
            ),
            RealmConfig(
                key="foundation_peak",
                display_name="筑基大圆满",
                major_realm="foundation",
                stage_index=4,
                order_index=8,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=360,
                required_spirit_stone=60,
                base_cultivation_gain_per_advance=50,
                base_spirit_stone_cost_per_advance=10,
            ),
        ]
    )
    run = RunState(
        run_id="run-combat-stat-2",
        player_id="player-1",
        round_index=1,
        character=CharacterState(
            name="修士乙",
            realm="foundation_peak",
            cultivation_exp=1430,
            lifespan_current=600,
            lifespan_max=960,
            hp_current=140,
            hp_max=140,
        ),
        resources=ResourceState(),
    )

    state = service.build_player_state(run)

    assert state.realm_label == "筑基大圆满"
    assert state.attack == 18
    assert state.defense == 9
    assert state.speed == 12


def test_build_player_combat_state_caps_later_realm_progress_bonus() -> None:
    service = CombatStatService(
        realm_configs=[
            RealmConfig(
                key="qi_refining_early",
                display_name="炼气初期",
                major_realm="qi_refining",
                stage_index=1,
                order_index=1,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=0,
                required_spirit_stone=0,
                base_cultivation_gain_per_advance=6,
                base_spirit_stone_cost_per_advance=2,
            ),
            RealmConfig(
                key="qi_refining_mid",
                display_name="炼气中期",
                major_realm="qi_refining",
                stage_index=2,
                order_index=2,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=90,
                required_spirit_stone=15,
                base_cultivation_gain_per_advance=8,
                base_spirit_stone_cost_per_advance=3,
            ),
            RealmConfig(
                key="qi_refining_late",
                display_name="炼气后期",
                major_realm="qi_refining",
                stage_index=3,
                order_index=3,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=130,
                required_spirit_stone=20,
                base_cultivation_gain_per_advance=10,
                base_spirit_stone_cost_per_advance=3,
            ),
            RealmConfig(
                key="qi_refining_peak",
                display_name="炼气大圆满",
                major_realm="qi_refining",
                stage_index=4,
                order_index=4,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=130,
                required_spirit_stone=20,
                base_cultivation_gain_per_advance=24,
                base_spirit_stone_cost_per_advance=4,
            ),
            RealmConfig(
                key="foundation_early",
                display_name="筑基初期",
                major_realm="foundation",
                stage_index=1,
                order_index=5,
                lifespan_bonus=360,
                base_success_rate=0.0,
                required_exp=220,
                required_spirit_stone=80,
                base_cultivation_gain_per_advance=30,
                base_spirit_stone_cost_per_advance=5,
            ),
            RealmConfig(
                key="foundation_mid",
                display_name="筑基中期",
                major_realm="foundation",
                stage_index=2,
                order_index=6,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=180,
                required_spirit_stone=35,
                base_cultivation_gain_per_advance=36,
                base_spirit_stone_cost_per_advance=7,
            ),
            RealmConfig(
                key="foundation_late",
                display_name="筑基后期",
                major_realm="foundation",
                stage_index=3,
                order_index=7,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=260,
                required_spirit_stone=45,
                base_cultivation_gain_per_advance=42,
                base_spirit_stone_cost_per_advance=8,
            ),
            RealmConfig(
                key="foundation_peak",
                display_name="筑基大圆满",
                major_realm="foundation",
                stage_index=4,
                order_index=8,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=360,
                required_spirit_stone=60,
                base_cultivation_gain_per_advance=50,
                base_spirit_stone_cost_per_advance=10,
            ),
        ]
    )
    low_progress_run = RunState(
        run_id="run-combat-stat-4",
        player_id="player-1",
        round_index=1,
        character=CharacterState(
            name="修士丁",
            realm="foundation_peak",
            cultivation_exp=1010,
            lifespan_current=600,
            lifespan_max=960,
            hp_current=140,
            hp_max=140,
        ),
        resources=ResourceState(),
    )
    high_progress_run = RunState(
        run_id="run-combat-stat-5",
        player_id="player-1",
        round_index=1,
        character=CharacterState(
            name="修士丁",
            realm="foundation_peak",
            cultivation_exp=1430,
            lifespan_current=600,
            lifespan_max=960,
            hp_current=140,
            hp_max=140,
        ),
        resources=ResourceState(),
    )

    low_progress_state = service.build_player_state(low_progress_run)
    high_progress_state = service.build_player_state(high_progress_run)

    assert high_progress_state.attack - low_progress_state.attack == 2
    assert high_progress_state.defense - low_progress_state.defense == 2
    assert high_progress_state.speed - low_progress_state.speed == 1


def test_build_player_combat_state_rejects_unknown_realm() -> None:
    service = CombatStatService(
        realm_configs=[
            RealmConfig(
                key="qi_refining_early",
                display_name="炼气初期",
                major_realm="qi_refining",
                stage_index=1,
                order_index=1,
                lifespan_bonus=0,
                base_success_rate=0.0,
                required_exp=0,
                required_spirit_stone=0,
                base_cultivation_gain_per_advance=6,
                base_spirit_stone_cost_per_advance=2,
            )
        ]
    )
    run = RunState(
        run_id="run-combat-stat-3",
        player_id="player-1",
        round_index=1,
        character=CharacterState(
            name="修士丙",
            realm="unknown_realm",
            cultivation_exp=0,
            lifespan_current=120,
            lifespan_max=240,
        ),
        resources=ResourceState(),
    )

    try:
        service.build_player_state(run)
    except Exception as error:
        assert "unknown realm" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected unknown realm to fail")
