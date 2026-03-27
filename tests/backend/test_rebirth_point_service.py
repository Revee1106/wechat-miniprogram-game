from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.core_loop.types import CharacterState, ResourceState, RunResourceStack, RunState
from app.economy.repositories.economy_config_repository import EconomyConfigRepository
from app.economy.services.rebirth_point_service import RebirthPointService


def test_rebirth_points_are_awarded_from_fixed_performance_dimensions() -> None:
    base_path = _make_test_base_path("rebirth-point-service")
    repository = EconomyConfigRepository(base_path=base_path)
    repository.save_resources(
        {
            "resources": [
                {
                    "key": "rare_material",
                    "display_name": "Rare Material",
                    "category": "rare_material",
                    "tier": 3,
                    "rarity": "rare",
                    "stackable": True,
                    "tags": ["rare"],
                }
            ]
        }
    )
    repository.save_settlement(
        {
            "weights": {
                "realm": 10,
                "survival_rounds": 1,
                "rare_resources": 3,
                "special_events": 5,
            }
        }
    )
    run = RunState(
        run_id="run-1",
        player_id="player-1",
        round_index=12,
        character=CharacterState(
            name="player-1-wanderer",
            realm="qi_refining_mid",
            cultivation_exp=0,
            lifespan_current=120,
            lifespan_max=240,
        ),
        resources=ResourceState(),
        resource_stacks=[RunResourceStack(resource_key="rare_material", amount=2)],
    )

    points = RebirthPointService(base_path=base_path).calculate(run, special_event_count=2)

    assert points == 48
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
