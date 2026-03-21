from app.core_loop.services.run_service import RunService


def test_advance_time_creates_pending_event() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    before_lifespan = run.character.lifespan_current

    result = service.advance_time(run.run_id)

    assert result.current_event is not None
    assert result.current_event.status == "pending"
    assert result.character.lifespan_current == before_lifespan - 1
