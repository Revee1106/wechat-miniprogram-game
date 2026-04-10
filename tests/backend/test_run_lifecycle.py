from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.core_loop.event_config import EventRegistry
from app.core_loop.services.combat_service import CombatService
from app.core_loop.services.run_service import RunService
from app.core_loop.types import (
    AlchemyInventoryItem,
    ConflictError,
    CurrentEvent,
    CurrentEventOption,
    EventOptionConfig,
    EventResultPayload,
    EventTemplateConfig,
)


def test_advance_time_creates_spec_shaped_pending_event() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    assert run.character.lifespan_current == 720
    assert run.character.lifespan_max == 720
    before_lifespan = run.character.lifespan_current

    result = service.advance_time(run.run_id)

    assert result.current_event is not None
    assert result.current_event.status == "pending"
    assert result.current_event.event_id
    assert result.current_event.event_type
    assert result.current_event.outcome_type
    assert result.current_event.risk_level
    assert result.current_event.choice_pattern in {
        "binary_choice",
        "single_outcome",
        "multi_choice",
    }
    assert result.current_event.title_text
    assert result.current_event.body_text
    assert result.current_event.region
    assert result.current_event.options
    assert [option.sort_order for option in result.current_event.options] == sorted(
        option.sort_order for option in result.current_event.options
    )
    if result.current_event.choice_pattern != "multi_choice":
        assert any(option.is_default for option in result.current_event.options)
    for option in result.current_event.options:
        assert option.option_id
        assert option.option_text
        assert isinstance(option.requires_resources, dict)
        assert option.is_available is True
        assert option.disabled_reason is None
    assert result.character.lifespan_current == before_lifespan - 1


def test_run_state_exposes_runtime_realm_display_and_breakthrough_requirements() -> None:
    base_path = _make_test_base_path("run-realm-runtime-metadata")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0,
                    "required_cultivation_exp": 0,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
                {
                    "key": "qi_refining_mid",
                    "display_name": "炼气中期",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 0.9,
                    "required_cultivation_exp": 60,
                    "required_spirit_stone": 12,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
                {
                    "key": "qi_refining_late",
                    "display_name": "炼气后期",
                    "major_realm": "qi_refining",
                    "stage_index": 3,
                    "order_index": 3,
                    "base_success_rate": 0.85,
                    "required_cultivation_exp": 90,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
            ]
        }
    )

    try:
        service = RunService(event_config_base_path=str(base_path))
        run = service.create_run(player_id="p1")

        assert run.character.realm_display_name == "炼气初期"
        assert run.breakthrough_requirements is not None
        assert run.breakthrough_requirements.target_realm_key == "qi_refining_mid"
        assert run.breakthrough_requirements.target_realm_display_name == "炼气中期"
        assert run.breakthrough_requirements.required_cultivation_exp == 60
        assert run.breakthrough_requirements.required_spirit_stone == 12
    finally:
        rmtree(base_path)


def test_create_run_exposes_dwelling_facilities_and_empty_last_settlement() -> None:
    service = RunService()

    run = service.create_run(player_id="p1")

    assert run.resources.spirit_stone == 100
    assert run.dwelling_level == 1
    assert run.dwelling_last_settlement is None
    assert [facility.facility_id for facility in run.dwelling_facilities] == [
        "spirit_field",
        "spirit_spring",
        "mine_cave",
        "alchemy_room",
        "spirit_gathering_array",
    ]
    assert all(facility.level == 0 for facility in run.dwelling_facilities)
    assert all(facility.status == "unbuilt" for facility in run.dwelling_facilities)
    assert run.alchemy_state is not None
    assert run.alchemy_state.active_job is None
    assert run.alchemy_state.last_result is None
    assert run.alchemy_state.inventory == []
    assert len(run.alchemy_state.available_recipes) >= 6


def test_resolve_event_exposes_capped_cultivation_log_metadata() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.character.realm = "qi_refining_peak"
    run.character.cultivation_exp = 570
    run.current_event = CurrentEvent(
        event_id="evt_mountain_spirit_tide_001",
        event_name="晨雾吐纳",
        event_type="cultivation",
        outcome_type="cultivation",
        risk_level="low",
        trigger_sources=[],
        choice_pattern="multi_choice",
        title_text="晨雾吐纳",
        body_text="雾中灵气流转。",
        region="mountain",
        status="pending",
        options=[
          CurrentEventOption(
              option_id="opt_mountain_spirit_tide_001_absorb",
              option_text="顺着雾中灵气缓缓引导",
              sort_order=1,
              is_default=True,
          )
        ],
    )

    resolved = service.resolve_event(run.run_id, "opt_mountain_spirit_tide_001_absorb")

    assert resolved.character.cultivation_exp == 570
    assert resolved.resources.spirit_stone == 96
    assert resolved.last_event_resolution is not None
    assert resolved.last_event_resolution.option_id == "opt_mountain_spirit_tide_001_absorb"
    assert resolved.last_event_resolution.intended_character["cultivation_exp"] == 16
    assert resolved.last_event_resolution.actual_character["cultivation_exp"] == 0
    assert resolved.last_event_resolution.capped_character["cultivation_exp"] == 16


def test_advance_time_applies_current_realm_base_gain_and_cost() -> None:
    base_path = _make_test_base_path("run-advance-base-gain-cost")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0,
                    "required_cultivation_exp": 0,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 0,
                    "base_cultivation_gain_per_advance": 7,
                    "base_spirit_stone_cost_per_advance": 3,
                    "is_enabled": True,
                },
                {
                    "key": "qi_refining_mid",
                    "display_name": "炼气中期",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 1,
                    "required_cultivation_exp": 60,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 0,
                    "base_cultivation_gain_per_advance": 9,
                    "base_spirit_stone_cost_per_advance": 4,
                    "is_enabled": True,
                },
            ]
        }
    )

    try:
        service = RunService(realm_config_base_path=str(base_path))
        run = service.create_run(player_id="p1")
        run.resources.spirit_stone = 20
        run.character.cultivation_exp = 10

        result = service.advance_time(run.run_id)

        assert result.resources.spirit_stone == 17
        assert result.character.cultivation_exp == 17
    finally:
        rmtree(base_path)


def test_advance_time_blocks_when_current_realm_spirit_stone_cost_is_unaffordable() -> None:
    base_path = _make_test_base_path("run-advance-base-cost-conflict")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0,
                    "required_cultivation_exp": 0,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 0,
                    "base_cultivation_gain_per_advance": 5,
                    "base_spirit_stone_cost_per_advance": 4,
                    "is_enabled": True,
                }
            ]
        }
    )

    try:
        service = RunService(realm_config_base_path=str(base_path))
        run = service.create_run(player_id="p1")
        run.resources.spirit_stone = 3
        run.character.cultivation_exp = 12
        before_spirit_stone = run.resources.spirit_stone
        before_cultivation_exp = run.character.cultivation_exp
        before_round_index = run.round_index

        try:
            service.advance_time(run.run_id)
        except ConflictError as error:
            assert "not enough spirit stones" in str(error)
        else:  # pragma: no cover - defensive
            raise AssertionError("expected advance_time to be blocked")

        assert run.resources.spirit_stone == before_spirit_stone
        assert run.character.cultivation_exp == before_cultivation_exp
        assert run.round_index == before_round_index
    finally:
        rmtree(base_path)


def test_advance_time_base_gain_still_respects_breakthrough_cultivation_cap() -> None:
    base_path = _make_test_base_path("run-advance-base-gain-cap")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0,
                    "required_cultivation_exp": 0,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 0,
                    "base_cultivation_gain_per_advance": 20,
                    "base_spirit_stone_cost_per_advance": 1,
                    "is_enabled": True,
                },
                {
                    "key": "qi_refining_mid",
                    "display_name": "炼气中期",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 1,
                    "required_cultivation_exp": 60,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 0,
                    "base_cultivation_gain_per_advance": 0,
                    "base_spirit_stone_cost_per_advance": 0,
                    "is_enabled": True,
                },
            ]
        }
    )

    try:
        service = RunService(realm_config_base_path=str(base_path))
        run = service.create_run(player_id="p1")
        run.resources.spirit_stone = 5
        run.character.cultivation_exp = 55

        result = service.advance_time(run.run_id)

        assert result.resources.spirit_stone == 4
        assert result.character.cultivation_exp == 60
    finally:
        rmtree(base_path)


def test_sell_resource_reactivates_stalled_dwelling_when_maintenance_becomes_affordable() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")

    mine_cave = next(
        facility for facility in run.dwelling_facilities if facility.facility_id == "mine_cave"
    )
    mine_cave.level = 1
    mine_cave.status = "stalled"
    mine_cave.maintenance_cost = {"spirit_stone": 5}
    mine_cave.next_upgrade_cost = {"spirit_stone": 40}
    run.dwelling_last_settlement = None
    run.resources.spirit_stone = 4
    run.resources.herbs = 3

    updated = service.sell_resource(run.run_id, "herb", 1)

    refreshed_mine_cave = next(
        facility for facility in updated.dwelling_facilities if facility.facility_id == "mine_cave"
    )

    assert updated.resources.spirit_stone == 6
    assert refreshed_mine_cave.status == "active"


def test_get_run_marks_all_unaffordable_dwelling_facilities_as_stalled() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200

    service.build_dwelling_facility(run.run_id, "spirit_field")
    service.build_dwelling_facility(run.run_id, "mine_cave")

    run.resources.spirit_stone = 0

    refreshed = service.get_run(run.run_id)

    spirit_field = next(
        facility for facility in refreshed.dwelling_facilities if facility.facility_id == "spirit_field"
    )
    mine_cave = next(
        facility for facility in refreshed.dwelling_facilities if facility.facility_id == "mine_cave"
    )

    assert spirit_field.status == "stalled"
    assert mine_cave.status == "stalled"


def test_combat_victory_applies_success_payload_and_clears_event() -> None:
    service = RunService()
    _attach_combat_registry(service)
    service._combat_service = CombatService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 5
    run.alchemy_state.inventory = [
        AlchemyInventoryItem(
            item_id="yang_qi_dan",
            display_name="养气丹",
            quality="low",
            amount=1,
            effect_summary="恢复修为",
        )
    ]
    run.current_event = CurrentEvent(
        event_id="evt_bandit",
        event_name="山匪拦路",
        event_type="encounter",
        outcome_type="mixed",
        risk_level="risky",
        trigger_sources=[],
        choice_pattern="binary_choice",
        title_text="山匪拦路",
        body_text="前路有山匪盘踞。",
        region="mountain",
        status="pending",
        options=[
            CurrentEventOption(
                option_id="opt_fight",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
            )
        ],
    )

    resolved = service.resolve_event(run.run_id, "opt_fight")
    assert resolved.active_battle is not None
    resolved.active_battle.enemy.hp_current = 1

    finished = service.perform_battle_action(run.run_id, "attack")

    assert finished.current_event is None
    assert finished.active_battle is None
    assert finished.resources.spirit_stone == 12
    assert finished.character.cultivation_exp == 5
    assert finished.character.lifespan_current == 718
    assert finished.result_summary == "victory log（额外耗时2个月）"
    assert finished.last_event_resolution is not None
    assert finished.last_event_resolution.time_cost_months == 2


def test_combat_flee_success_ends_event_without_applying_payload() -> None:
    service = RunService()
    _attach_combat_registry(service)
    service._combat_service = CombatService(rng=lambda: 0.0)
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 5
    run.alchemy_state.inventory = [
        AlchemyInventoryItem(
            item_id="yang_qi_dan",
            display_name="养气丹",
            quality="low",
            amount=1,
            effect_summary="恢复修为",
        )
    ]
    run.current_event = CurrentEvent(
        event_id="evt_bandit",
        event_name="山匪拦路",
        event_type="encounter",
        outcome_type="mixed",
        risk_level="risky",
        trigger_sources=[],
        choice_pattern="binary_choice",
        title_text="山匪拦路",
        body_text="前路有山匪盘踞。",
        region="mountain",
        status="pending",
        options=[
            CurrentEventOption(
                option_id="opt_fight",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
            )
        ],
    )

    resolved = service.resolve_event(run.run_id, "opt_fight")
    assert resolved.active_battle is not None

    finished = service.perform_battle_action(run.run_id, "flee")

    assert finished.current_event is None
    assert finished.active_battle is None
    assert finished.resources.spirit_stone == 5
    assert finished.character.cultivation_exp == 0
    assert finished.result_summary == "脱身成功"


def test_combat_finalization_syncs_remaining_hp_back_to_character_state() -> None:
    service = RunService()
    _attach_combat_registry(service)
    service._combat_service = CombatService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 5
    run.current_event = CurrentEvent(
        event_id="evt_bandit",
        event_name="山匪拦路",
        event_type="encounter",
        outcome_type="mixed",
        risk_level="risky",
        trigger_sources=[],
        choice_pattern="binary_choice",
        title_text="山匪拦路",
        body_text="前路有山匪盘踞。",
        region="mountain",
        status="pending",
        options=[
            CurrentEventOption(
                option_id="opt_fight",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
            )
        ],
    )

    resolved = service.resolve_event(run.run_id, "opt_fight")
    assert resolved.active_battle is not None
    resolved.active_battle.player.hp_current = 18
    resolved.active_battle.enemy.hp_current = 1

    finished = service.perform_battle_action(run.run_id, "attack")

    assert finished.active_battle is None
    assert finished.character.hp_current == 18


def test_combat_use_pill_consumes_pill_and_persists_after_refresh() -> None:
    service = RunService()
    _attach_combat_registry(service)
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 5
    run.resources.pill = 1
    run.alchemy_state.inventory = [
        AlchemyInventoryItem(
            item_id="yang_qi_dan",
            display_name="养气丹",
            quality="low",
            amount=1,
            effect_summary="恢复修为",
        )
    ]
    run.current_event = CurrentEvent(
        event_id="evt_bandit",
        event_name="山匪拦路",
        event_type="encounter",
        outcome_type="mixed",
        risk_level="risky",
        trigger_sources=[],
        choice_pattern="binary_choice",
        title_text="山匪拦路",
        body_text="前路有山匪盘踞。",
        region="mountain",
        status="pending",
        options=[
            CurrentEventOption(
                option_id="opt_fight",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
            )
        ],
    )

    resolved = service.resolve_event(run.run_id, "opt_fight")
    assert resolved.active_battle is not None

    updated = service.perform_battle_action(run.run_id, "use_pill")
    refreshed = service.get_run(run.run_id)

    assert updated.active_battle is not None
    assert updated.active_battle.pill_count == 0
    assert updated.resources.pill == 0
    assert updated.alchemy_state.inventory == []
    assert refreshed.resources.pill == 0


def _attach_combat_registry(service: RunService) -> None:
    registry = EventRegistry(
        templates={
            "evt_bandit": EventTemplateConfig(
                event_id="evt_bandit",
                event_name="山匪拦路",
                event_type="encounter",
                outcome_type="mixed",
                risk_level="risky",
                trigger_sources=["global"],
                choice_pattern="binary_choice",
                title_text="山匪拦路",
                body_text="前路有山匪盘踞。",
                weight=1,
                is_repeatable=True,
                option_ids=["opt_fight"],
            )
        },
        options={
            "opt_fight": EventOptionConfig(
                option_id="opt_fight",
                event_id="evt_bandit",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
                resolution_mode="combat",
                time_cost_months=2,
                result_on_success=EventResultPayload(
                    resources={"spirit_stone": 7},
                    character={"cultivation_exp": 5},
                    battle={
                        "enemy_name": "山匪",
                        "enemy_realm_label": "炼气初期",
                        "enemy_hp": 1,
                        "enemy_attack": 1,
                        "enemy_defense": 0,
                        "enemy_speed": 1,
                        "allow_flee": True,
                        "flee_base_rate": 0.35,
                        "pill_heal_amount": 12,
                        "victory_log": "victory log",
                        "defeat_log": "defeat log",
                        "flee_success_log": "脱身成功",
                        "flee_failure_log": "逃跑失败",
                    },
                ),
                result_on_failure=EventResultPayload(
                    resources={"spirit_stone": -3},
                    character={"lifespan_delta": -2},
                    battle={
                        "enemy_name": "山匪",
                        "enemy_realm_label": "炼气初期",
                        "enemy_hp": 1,
                        "enemy_attack": 1,
                        "enemy_defense": 0,
                        "enemy_speed": 1,
                        "allow_flee": True,
                        "flee_base_rate": 0.35,
                        "pill_heal_amount": 12,
                        "victory_log": "victory log",
                        "defeat_log": "defeat log",
                        "flee_success_log": "脱身成功",
                        "flee_failure_log": "逃跑失败",
                    },
                ),
            )
        },
    )
    service._event_registry = registry
    service._rebuild_runtime_services()


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
