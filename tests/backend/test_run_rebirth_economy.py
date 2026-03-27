from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.core_loop.services.run_service import RunService
from app.core_loop.types import RunResourceStack
from app.economy.repositories.economy_config_repository import EconomyConfigRepository


def test_rebirth_clears_run_resources_and_keeps_rebirth_points() -> None:
    base_path = _make_test_base_path("run-rebirth-economy")
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

    service = RunService(event_config_base_path=str(base_path))
    run = service.create_run(player_id="p1")
    run.character.realm = "qi_refining_mid"
    run.round_index = 12
    run.character.is_dead = True
    run.resource_stacks = [RunResourceStack(resource_key="rare_material", amount=2)]

    result = service.rebirth(run.run_id)

    assert result.player_profile.rebirth_points == 38
    assert result.new_run.resource_stacks == []
    assert result.new_run.resources.spirit_stone == 21
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
