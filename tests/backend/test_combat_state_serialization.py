from app.api.schemas import (
    serialize_breakthrough_result,
    serialize_rebirth_result,
    serialize_run_state,
)
from app.core_loop.types import (
    ActiveBattleState,
    BreakthroughResult,
    CharacterState,
    CombatActorState,
    PlayerProfile,
    RebirthResult,
    ResourceState,
    RunState,
)


def test_serialize_run_state_includes_active_battle_snapshot() -> None:
    run = RunState(
        run_id="run-combat",
        player_id="player-combat",
        round_index=7,
        character=CharacterState(
            name="修士甲",
            realm="qi_refining",
            cultivation_exp=18,
            lifespan_current=120,
            lifespan_max=240,
        ),
        resources=ResourceState(
            spirit_stone=36,
            herbs=2,
            pill=1,
        ),
        active_battle=ActiveBattleState(
            source_event_id="evt_bandit",
            source_option_id="opt_fight_bandit",
            round_index=3,
            allow_flee=False,
            flee_base_rate=0.35,
            player=CombatActorState(
                name="修士甲",
                realm_label="炼气初期",
                hp_current=88,
                hp_max=100,
                attack=12,
                defense=6,
                speed=8,
            ),
            enemy=CombatActorState(
                name="山匪",
                realm_label="凡人",
                hp_current=45,
                hp_max=45,
                attack=9,
                defense=4,
                speed=5,
            ),
            log_lines=[
                "你运起灵力，准备迎战。",
                "山匪挥刀袭来。",
            ],
        ),
    )

    serialized = serialize_run_state(run)

    assert serialized["active_battle"]["source_event_id"] == "evt_bandit"
    assert serialized["active_battle"]["source_option_id"] == "opt_fight_bandit"
    assert serialized["active_battle"]["round_index"] == 3
    assert serialized["active_battle"]["allow_flee"] is False
    assert serialized["active_battle"]["flee_base_rate"] == 0.35
    assert serialized["active_battle"]["player"]["hp_current"] == 88
    assert serialized["active_battle"]["player"]["attack"] == 12
    assert serialized["active_battle"]["enemy"]["name"] == "山匪"
    assert serialized["active_battle"]["enemy"]["speed"] == 5
    assert serialized["active_battle"]["log_lines"] == [
        "你运起灵力，准备迎战。",
        "山匪挥刀袭来。",
    ]


def test_serialize_run_state_includes_computed_character_combat_stats() -> None:
    run = RunState(
        run_id="run-combat-summary",
        player_id="player-combat-summary",
        round_index=1,
        character=CharacterState(
            name="修士",
            realm="qi_refining_early",
            cultivation_exp=32,
            lifespan_current=720,
            lifespan_max=720,
        ),
        resources=ResourceState(),
    )

    serialized = serialize_run_state(run)

    assert serialized["character"]["hp_current"] == 100
    assert serialized["character"]["hp_max"] == 100
    assert serialized["character"]["attack"] == 11
    assert serialized["character"]["defense"] == 5
    assert serialized["character"]["speed"] == 8


def test_serialize_breakthrough_result_includes_computed_character_combat_stats() -> None:
    result = BreakthroughResult(
        success=True,
        previous_realm="qi_refining_early",
        new_realm="qi_refining_mid",
        success_rate=1.0,
        message="breakthrough success",
        character=CharacterState(
            name="修士",
            realm="qi_refining_mid",
            cultivation_exp=60,
            lifespan_current=900,
            lifespan_max=900,
        ),
        resources=ResourceState(spirit_stone=20),
    )

    serialized = serialize_breakthrough_result(result)

    assert serialized["character"]["attack"] > 0
    assert serialized["character"]["defense"] > 0
    assert serialized["character"]["speed"] > 0


def test_serialize_rebirth_result_includes_new_run_combat_stats() -> None:
    result = RebirthResult(
        player_profile=PlayerProfile(player_id="player-1"),
        new_run=RunState(
            run_id="run-reborn",
            player_id="player-1",
            round_index=0,
            character=CharacterState(
                name="修士",
                realm="qi_refining_early",
                cultivation_exp=0,
                lifespan_current=720,
                lifespan_max=720,
            ),
            resources=ResourceState(),
        ),
    )

    serialized = serialize_rebirth_result(result)

    assert serialized["new_run"]["character"]["attack"] > 0
    assert serialized["new_run"]["character"]["defense"] > 0
    assert serialized["new_run"]["character"]["speed"] > 0
