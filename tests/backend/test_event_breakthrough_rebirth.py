from app.core_loop.services.run_service import RunService


def test_resolve_event_applies_choice_rewards() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    advanced = service.advance_time(run.run_id)
    before_spirit_stone = advanced.resources.spirit_stone

    result = service.resolve_event(
        run.run_id,
        option_id="opt_mountain_spirit_tide_001_absorb",
    )

    assert result.current_event is None
    assert result.resources.spirit_stone >= before_spirit_stone
    assert result.character.cultivation_exp > 0


def test_forage_choice_increases_herbs() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    service.advance_time(run.run_id)
    service.resolve_event(run.run_id, option_id="opt_mountain_spirit_tide_001_withdraw")
    advanced = service.advance_time(run.run_id)
    before_herbs = advanced.resources.herbs

    result = service.resolve_event(
        run.run_id,
        option_id="opt_secluded_room_breathing_002_forage",
    )

    assert result.resources.herbs > before_herbs


def test_evil_cultist_branch_can_cause_death() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    for _ in range(12):
        advanced = service.advance_time(run.run_id)
        if advanced.current_event.event_id == "evt_evil_cultist_012":
            break
        default_option = next(
            option.option_id
            for option in advanced.current_event.options
            if option.is_default
        )
        service.resolve_event(run.run_id, option_id=default_option)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected evil cultist event to appear within 12 rounds")

    result = service.resolve_event(
        run.run_id,
        option_id="opt_evil_cultist_012_pursue",
    )

    assert result.character.is_dead is True


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
