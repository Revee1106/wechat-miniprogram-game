from app.core_loop.event_config import EventRegistry
from app.core_loop.services.event_resolution_service import EventResolutionService
from app.core_loop.services.event_service import EventService
from app.core_loop.types import (
    CharacterState,
    EventOptionConfig,
    EventResultPayload,
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
            lifespan_current=120,
            lifespan_max=240,
            luck=0,
        ),
        resources=ResourceState(
            spirit_stone=20,
            herbs=3,
            iron_essence=0,
        ),
    )


def test_resolve_event_applies_success_payload_and_summary() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="cultivation",
                option_ids=["opt_payload_gain"],
            )
        },
        options={
            "opt_payload_gain": EventOptionConfig(
                option_id="opt_payload_gain",
                event_id="evt_payload",
                option_text="Take the gain",
                is_default=True,
                success_rate_formula="1.0",
                result_on_success="cultivation_exp:+4,spirit_stone:+2,lifespan:+3",
                result_on_failure="cultivation_exp:+0",
                log_text_success="success log",
                log_text_failure="failure log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_payload_gain")

    assert resolved.current_event is None
    assert resolved.character.cultivation_exp == 4
    assert resolved.resources.spirit_stone == 22
    assert resolved.character.lifespan_current == 123
    assert resolved.result_summary == "success log"


def test_resolve_event_applies_failure_death_payload() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="survival",
                option_ids=["opt_payload_death"],
            )
        },
        options={
            "opt_payload_death": EventOptionConfig(
                option_id="opt_payload_death",
                event_id="evt_payload",
                option_text="Take the risk",
                is_default=True,
                success_rate_formula="0.0",
                result_on_success="cultivation_exp:+1",
                result_on_failure="death:true,lifespan:-999",
                log_text_success="success log",
                log_text_failure="death log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_payload_death")

    assert resolved.current_event is None
    assert resolved.character.is_dead is True
    assert resolved.result_summary == "death log"


def test_resolve_event_does_not_partially_mutate_run_on_invalid_payload() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="material",
                option_ids=["opt_payload_invalid"],
            )
        },
        options={
            "opt_payload_invalid": EventOptionConfig(
                option_id="opt_payload_invalid",
                event_id="evt_payload",
                option_text="Break the payload",
                is_default=True,
                success_rate_formula="1.0",
                result_on_success=EventResultPayload(
                    resource_deltas={"spirit_stone": 2, "unknown_resource": 1}
                ),
                log_text_success="success log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)
    before_spirit_stone = run.resources.spirit_stone
    before_cultivation = run.character.cultivation_exp

    try:
        EventResolutionService(registry=registry).resolve(run, "opt_payload_invalid")
    except Exception as error:
        assert "unknown resource" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected invalid payload to fail")

    assert run.resources.spirit_stone == before_spirit_stone
    assert run.character.cultivation_exp == before_cultivation
