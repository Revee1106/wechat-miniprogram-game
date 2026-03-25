from app.core_loop.services.run_service import RunService


def test_meditate_option_consumes_required_spirit_stone() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    service.advance_time(run.run_id)
    service.resolve_event(run.run_id, option_id="opt_mountain_spirit_tide_001_withdraw")
    advanced = service.advance_time(run.run_id)
    before_spirit_stone = advanced.resources.spirit_stone

    result = service.resolve_event(
        run.run_id,
        option_id="opt_secluded_room_breathing_002_meditate",
    )

    assert result.resources.spirit_stone == before_spirit_stone - 1
