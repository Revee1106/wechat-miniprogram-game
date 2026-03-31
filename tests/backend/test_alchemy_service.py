import pytest

from app.core_loop.services.run_service import RunService
from app.core_loop.types import ConflictError, RunResourceStack


def test_alchemy_requires_built_alchemy_room() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")

    with pytest.raises(ConflictError):
        service.start_alchemy(run.run_id, "yang_qi_dan")


def test_start_alchemy_spends_materials_and_creates_job() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    service.build_dwelling_facility(run.run_id, "alchemy_room")

    updated = service.start_alchemy(run.run_id, "yang_qi_dan")

    assert updated.resources.herbs == 1
    assert updated.alchemy_state.active_job is not None
    assert updated.alchemy_state.active_job.recipe_id == "yang_qi_dan"
    assert updated.alchemy_state.active_job.remaining_months == 1


def test_advance_time_completes_alchemy_job_and_adds_inventory_and_mastery() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    service.build_dwelling_facility(run.run_id, "alchemy_room")
    service.start_alchemy(run.run_id, "yang_qi_dan")

    advanced = service.advance_time(run.run_id)

    assert advanced.alchemy_state.active_job is None
    assert advanced.alchemy_state.last_result is not None
    assert advanced.alchemy_state.last_result.recipe_id == "yang_qi_dan"
    assert advanced.alchemy_state.last_result.outcome in {"success", "waste"}
    assert advanced.alchemy_state.mastery_exp > 0
    if advanced.alchemy_state.last_result.outcome == "success":
        assert advanced.alchemy_state.inventory[0].item_id == "yang_qi_dan"


def test_spirit_spring_auxiliary_improves_alchemy_result() -> None:
    service = RunService()

    base_run = service.create_run(player_id="base")
    base_run.resources.spirit_stone = 200
    base_run.resources.herbs = 10
    service.build_dwelling_facility(base_run.run_id, "alchemy_room")
    service.upgrade_dwelling_facility(base_run.run_id, "alchemy_room")
    base_run.alchemy_state.mastery_exp = 60
    base = service.start_alchemy(base_run.run_id, "ju_ling_dan")
    base = service.advance_time(base.run_id)

    spring_run = service.create_run(player_id="spring")
    spring_run.resources.spirit_stone = 200
    spring_run.resources.herbs = 10
    spring_run.resource_stacks.append(
        RunResourceStack(resource_key="spirit_spring_water", amount=1)
    )
    service.build_dwelling_facility(spring_run.run_id, "alchemy_room")
    service.upgrade_dwelling_facility(spring_run.run_id, "alchemy_room")
    spring_run.alchemy_state.mastery_exp = 60
    spring = service.start_alchemy(spring_run.run_id, "ju_ling_dan", use_spirit_spring=True)
    spring = service.advance_time(spring.run_id)

    assert spring.alchemy_state.last_result is not None
    assert base.alchemy_state.last_result is not None
    assert spring.alchemy_state.last_result.outcome_rank >= base.alchemy_state.last_result.outcome_rank


def test_consume_pill_applies_effect_and_reduces_inventory() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    service.build_dwelling_facility(run.run_id, "alchemy_room")
    service.start_alchemy(run.run_id, "yang_qi_dan")
    updated = service.advance_time(run.run_id)

    assert updated.alchemy_state.last_result is not None
    assert updated.alchemy_state.last_result.outcome == "success"
    updated.character.cultivation_exp = 0

    updated = service.consume_alchemy_item(
        run.run_id,
        "yang_qi_dan",
        updated.alchemy_state.last_result.quality,
    )

    assert updated.character.cultivation_exp > 0
    assert updated.alchemy_state.inventory == []
