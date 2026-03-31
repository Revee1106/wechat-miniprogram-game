from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.core_loop.services.run_service import RunService


def test_advance_time_creates_spec_shaped_pending_event() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    assert run.character.lifespan_current == 240
    assert run.character.lifespan_max == 240
    before_lifespan = run.character.lifespan_current

    result = service.advance_time(run.run_id)

    assert result.current_event is not None
    assert result.current_event.status == "pending"
    assert result.current_event.event_id
    assert result.current_event.event_type
    assert result.current_event.outcome_type
    assert result.current_event.risk_level
    assert result.current_event.choice_pattern in {"binary_choice", "single_outcome"}
    assert result.current_event.title_text
    assert result.current_event.body_text
    assert result.current_event.region
    assert result.current_event.options
    assert [option.sort_order for option in result.current_event.options] == sorted(
        option.sort_order for option in result.current_event.options
    )
    assert any(option.is_default for option in result.current_event.options)
    for option in result.current_event.options:
        assert option.option_id
        assert option.option_text
        assert option.requires_resources == {}
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
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
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
                    "required_cultivation_exp": 180,
                    "required_spirit_stone": 12,
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
        assert run.breakthrough_requirements.required_cultivation_exp == 100
        assert run.breakthrough_requirements.required_spirit_stone == 0
    finally:
        rmtree(base_path)


def test_create_run_exposes_dwelling_facilities_and_empty_last_settlement() -> None:
    service = RunService()

    run = service.create_run(player_id="p1")

    assert run.dwelling_level == 1
    assert run.dwelling_last_settlement is None
    assert [facility.facility_id for facility in run.dwelling_facilities] == [
        "spirit_field",
        "mine_cave",
        "alchemy_room",
        "spirit_gathering_array",
    ]
    assert all(facility.level == 0 for facility in run.dwelling_facilities)
    assert all(facility.status == "unbuilt" for facility in run.dwelling_facilities)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
