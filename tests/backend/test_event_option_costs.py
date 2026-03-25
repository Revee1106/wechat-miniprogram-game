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


def test_meditate_option_consumes_required_spirit_stone() -> None:
    registry = EventRegistry(
        templates={
            "evt_meditate": EventTemplateConfig(
                event_id="evt_meditate",
                event_name="Meditate",
                event_type="cultivation",
                option_ids=["opt_meditate"],
            )
        },
        options={
            "opt_meditate": EventOptionConfig(
                option_id="opt_meditate",
                event_id="evt_meditate",
                option_text="Meditate",
                is_default=True,
                requires_resources={"spirit_stone": 1},
                success_rate_formula="1.0",
                result_on_success=EventResultPayload(
                    resources={"spirit_stone": -1},
                    character={"cultivation_exp": 2},
                ),
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)
    before_spirit_stone = run.resources.spirit_stone

    result = EventResolutionService(registry=registry).resolve(run, "opt_meditate")

    assert result.resources.spirit_stone == before_spirit_stone - 1
