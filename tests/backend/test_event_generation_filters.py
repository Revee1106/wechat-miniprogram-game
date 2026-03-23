from app.core_loop.event_config import EventRegistry
from app.core_loop.services.event_service import EventService
from app.core_loop.services.time_advance_service import TimeAdvanceService
from app.core_loop.types import ConflictError
from app.core_loop.types import (
    CharacterState,
    EventOptionConfig,
    EventTemplateConfig,
    ResourceState,
    RunState,
)


def _build_run() -> RunState:
    return RunState(
        run_id="run-test",
        player_id="player-test",
        round_index=1,
        character=CharacterState(
            name="player-test-wanderer",
            realm="qi_refining",
            cultivation_exp=0,
            lifespan_current=240,
            lifespan_max=240,
            luck=0,
        ),
        resources=ResourceState(
            spirit_stone=20,
            herbs=3,
            iron_essence=0,
        ),
    )


def _build_registry(*templates: EventTemplateConfig) -> EventRegistry:
    options = {
        option.option_id: option
        for template in templates
        for option in [
            EventOptionConfig(
                option_id=template.option_ids[0],
                event_id=template.event_id,
                option_text=f"{template.event_id}-option",
                is_default=True,
            )
        ]
    }
    return EventRegistry(
        templates={template.event_id: template for template in templates},
        options=options,
    )


def test_event_selection_skips_realm_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_foundation_only",
                event_name="Foundation Only",
                event_type="cultivation",
                option_ids=["opt_foundation_only"],
                realm_min="foundation",
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="cultivation",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_resource_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_needs_herbs",
                event_name="Needs Herbs",
                event_type="material",
                option_ids=["opt_needs_herbs"],
                required_resources={"herbs": 5},
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="material",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_luck_and_rebirth_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_needs_meta_progress",
                event_name="Meta Progress",
                event_type="encounter",
                option_ids=["opt_needs_meta_progress"],
                required_rebirth_count=1,
                required_luck_min=3,
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="encounter",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_templates_with_no_available_options() -> None:
    registry = EventRegistry(
        templates={
            "evt_blocked": EventTemplateConfig(
                event_id="evt_blocked",
                event_name="Blocked",
                event_type="material",
                option_ids=["opt_blocked"],
            ),
            "evt_fallback": EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="material",
                option_ids=["opt_fallback"],
            ),
        },
        options={
            "opt_blocked": EventOptionConfig(
                option_id="opt_blocked",
                event_id="evt_blocked",
                option_text="Blocked option",
                requires_resources={"herbs": 99},
                is_default=True,
            ),
            "opt_fallback": EventOptionConfig(
                option_id="opt_fallback",
                event_id="evt_fallback",
                option_text="Fallback option",
                is_default=True,
            ),
        },
    )
    run = _build_run()

    selected = EventService(registry=registry).select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_time_advance_does_not_mutate_run_when_no_event_is_eligible() -> None:
    registry = EventRegistry(
        templates={
            "evt_blocked": EventTemplateConfig(
                event_id="evt_blocked",
                event_name="Blocked",
                event_type="material",
                option_ids=["opt_blocked"],
                required_resources={"herbs": 99},
            ),
        },
        options={
            "opt_blocked": EventOptionConfig(
                option_id="opt_blocked",
                event_id="evt_blocked",
                option_text="Blocked option",
                requires_resources={"herbs": 99},
                is_default=True,
            ),
        },
    )
    run = _build_run()
    before_round = run.round_index
    before_lifespan = run.character.lifespan_current

    try:
        TimeAdvanceService(EventService(registry=registry)).advance(run, rebirth_count=0)
    except ConflictError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("expected advance to fail when no config event is eligible")

    assert run.round_index == before_round
    assert run.character.lifespan_current == before_lifespan
    assert run.current_event is None
