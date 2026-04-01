import pytest

from app.core_loop.services.run_service import RunService
from app.core_loop.types import ConflictError, RunResourceStack


def test_sell_resource_converts_inventory_into_spirit_stone() -> None:
    service = RunService()
    run = service.create_run(player_id="seller")
    run.resources.spirit_stone = 20
    run.resources.herbs = 5

    updated = service.sell_resource(run.run_id, "herb", 3)

    assert updated.resources.spirit_stone == 26
    assert updated.resources.herbs == 2


def test_sell_resource_uses_resource_stacks_for_stack_only_items() -> None:
    service = RunService()
    run = service.create_run(player_id="spring-seller")
    run.resources.spirit_stone = 20
    run.resource_stacks.append(
        RunResourceStack(resource_key="spirit_spring_water", amount=2)
    )

    updated = service.sell_resource(run.run_id, "spirit_spring_water", 2)

    assert updated.resources.spirit_stone == 26
    assert all(
        stack.resource_key != "spirit_spring_water" for stack in updated.resource_stacks
    )


def test_sell_resource_rejects_invalid_amount() -> None:
    service = RunService()
    run = service.create_run(player_id="bad-amount")
    run.resources.herbs = 5

    with pytest.raises(ConflictError):
        service.sell_resource(run.run_id, "herb", 0)


def test_sell_resource_rejects_insufficient_inventory_without_partial_mutation() -> None:
    service = RunService()
    run = service.create_run(player_id="not-enough")
    run.resources.spirit_stone = 20
    run.resources.herbs = 1

    with pytest.raises(ConflictError):
        service.sell_resource(run.run_id, "herb", 2)

    assert run.resources.spirit_stone == 20
    assert run.resources.herbs == 1


def test_sell_resource_rejects_non_sellable_resource() -> None:
    service = RunService()
    run = service.create_run(player_id="forbidden")

    with pytest.raises(ConflictError):
        service.sell_resource(run.run_id, "spirit_stone", 1)


def test_convert_spirit_stone_to_cultivation_consumes_stone_and_adds_exp() -> None:
    service = RunService()
    run = service.create_run(player_id="converter")
    run.resources.spirit_stone = 10
    run.character.cultivation_exp = 7

    updated = service.convert_spirit_stone_to_cultivation(run.run_id, 3)

    assert updated.resources.spirit_stone == 7
    assert updated.character.cultivation_exp == 22


def test_convert_spirit_stone_to_cultivation_rejects_insufficient_stone() -> None:
    service = RunService()
    run = service.create_run(player_id="poor-converter")
    run.resources.spirit_stone = 2
    run.character.cultivation_exp = 4

    with pytest.raises(ConflictError):
        service.convert_spirit_stone_to_cultivation(run.run_id, 3)

    assert run.resources.spirit_stone == 2
    assert run.character.cultivation_exp == 4
