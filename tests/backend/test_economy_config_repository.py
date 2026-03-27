from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.economy.repositories.economy_config_repository import EconomyConfigRepository


def test_economy_repository_loads_resource_and_settlement_config() -> None:
    base_path = _make_test_base_path("economy-config-repository")
    repository = EconomyConfigRepository(base_path=base_path)

    repository.save_resources(
        {
            "resources": [
                {
                    "key": "spirit_stone",
                    "display_name": "灵石",
                    "category": "currency",
                    "tier": 1,
                    "rarity": "common",
                    "stackable": True,
                    "tags": ["core"],
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

    assert repository.load_resources()["resources"][0]["key"] == "spirit_stone"
    assert repository.load_settlement()["weights"]["realm"] == 10
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
