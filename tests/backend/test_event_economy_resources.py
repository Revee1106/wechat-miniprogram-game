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


def test_event_payload_can_write_to_run_resource_stacks() -> None:
    registry = EventRegistry(
        templates={
            "evt_herb_reward": EventTemplateConfig(
                event_id="evt_herb_reward",
                event_name="Herb Reward",
                event_type="material",
                option_ids=["opt_reward"],
            )
        },
        options={
            "opt_reward": EventOptionConfig(
                option_id="opt_reward",
                event_id="evt_herb_reward",
                option_text="Take herbs",
                is_default=True,
                success_rate_formula="1.0",
                result_on_success=EventResultPayload(resources={"basic_herb": 2}),
                result_on_failure=EventResultPayload(),
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_reward")

    assert any(
        stack.resource_key == "basic_herb" and stack.amount == 2
        for stack in resolved.resource_stacks
    )
    assert resolved.resources.herbs == 3


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
