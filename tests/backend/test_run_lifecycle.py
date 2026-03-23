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
    assert result.current_event.choice_pattern == "binary_choice"
    assert result.current_event.title_text
    assert result.current_event.body_text
    assert result.current_event.region
    assert result.current_event.options[0].option_id
    assert result.current_event.options[0].option_text
    assert result.current_event.options[0].sort_order == 10
    assert result.current_event.options[0].is_default is True
    assert result.current_event.options[0].requires_resources == {}
    assert result.current_event.options[0].is_available is True
    assert result.current_event.options[0].disabled_reason is None
    assert result.character.lifespan_current == before_lifespan - 1
