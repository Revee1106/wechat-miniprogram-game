from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.core_loop.services.run_service import RunService
from app.core_loop.types import ConflictError, CurrentEvent, CurrentEventOption


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


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
