from app.core_loop.repository import InMemoryRunRepository


def test_new_run_contains_economy_resource_stacks() -> None:
    repository = InMemoryRunRepository()

    run = repository.create(player_id="p1")

    assert isinstance(run.resource_stacks, list)
    assert run.resource_stacks == []


def test_player_profile_stores_rebirth_points() -> None:
    repository = InMemoryRunRepository()

    profile = repository.get_or_create_profile("p1")

    assert profile.rebirth_points == 0
