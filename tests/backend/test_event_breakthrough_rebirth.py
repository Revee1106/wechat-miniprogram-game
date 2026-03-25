from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.core_loop.services.run_service import RunService


def test_resolve_event_applies_selected_option_rewards() -> None:
    base_path = _make_test_base_path("run-service-event")
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_reward",
                    "event_name": "Reward",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "safe",
                    "trigger_sources": ["global"],
                    "choice_pattern": "single_outcome",
                    "title_text": "Reward",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["opt_reward"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_reward",
                    "event_id": "evt_reward",
                    "option_text": "Take reward",
                    "sort_order": 1,
                    "is_default": True,
                    "success_rate_formula": "1.0",
                    "result_on_success": {
                        "resources": {"spirit_stone": 2, "herb": 1},
                        "character": {"cultivation_exp": 4},
                    },
                    "result_on_failure": {"resources": {}},
                    "log_text_success": "reward granted",
                }
            ],
        }
    )

    try:
        service = RunService(event_config_base_path=str(base_path))
        run = service.create_run(player_id="p1")
        advanced = service.advance_time(run.run_id)
        before_spirit_stone = advanced.resources.spirit_stone
        before_cultivation_exp = advanced.character.cultivation_exp
        before_herbs = advanced.resources.herbs
        option_id = next(
            option.option_id for option in advanced.current_event.options if option.is_default
        )

        result = service.resolve_event(
            run.run_id,
            option_id=option_id,
        )

        assert result.current_event is None
        assert result.result_summary == "reward granted"
        assert result.event_trigger_counts == {"evt_reward": 1}
        assert result.resources.spirit_stone == before_spirit_stone + 2
        assert result.character.cultivation_exp == before_cultivation_exp + 4
        assert result.resources.herbs == before_herbs + 1
    finally:
        rmtree(base_path)


def test_resolve_event_keeps_run_progressing_under_random_selection() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    for _ in range(5):
        advanced = service.advance_time(run.run_id)
        option_id = next(
            option.option_id for option in advanced.current_event.options if option.is_default
        )
        result = service.resolve_event(run.run_id, option_id=option_id)
        assert result.current_event is None
        assert result.character.is_dead is False


def test_random_event_pool_excludes_evil_cultist_event() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    seen_event_ids: set[str] = set()
    for _ in range(20):
        advanced = service.advance_time(run.run_id)
        seen_event_ids.add(advanced.current_event.event_id)
        default_option = next(
            option.option_id
            for option in advanced.current_event.options
            if option.is_default
        )
        service.resolve_event(run.run_id, option_id=default_option)

    assert "evt_evil_cultist_012" not in seen_event_ids


def test_breakthrough_success_updates_realm_and_lifespan() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    before_realm = run.character.realm
    before_lifespan_max = run.character.lifespan_max
    run.character.cultivation_exp = 100
    run.resources.spirit_stone = 50

    result = service.breakthrough(run.run_id)

    assert result.success is True
    assert result.new_realm != before_realm
    assert result.character.lifespan_max > before_lifespan_max


def test_rebirth_creates_new_run_with_permanent_bonus() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.character.is_dead = True

    result = service.rebirth(run.run_id)

    assert result.player_profile.total_rebirth_count == 1
    assert result.new_run.run_id != run.run_id
    assert result.new_run.character.luck == result.player_profile.permanent_luck_bonus
    assert result.new_run.character.luck == 1
    assert result.new_run.resources.spirit_stone == 21


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
