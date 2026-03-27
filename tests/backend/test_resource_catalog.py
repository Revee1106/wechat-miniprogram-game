from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.economy.repositories.economy_config_repository import EconomyConfigRepository
from app.economy.resource_catalog import load_resource_definitions


def test_resource_catalog_loads_minimal_resource_set() -> None:
    base_path = _make_test_base_path("resource-catalog")
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
                },
                {
                    "key": "basic_herb",
                    "display_name": "普通灵植",
                    "category": "herb",
                    "tier": 2,
                    "rarity": "common",
                    "stackable": True,
                    "tags": ["basic"],
                },
            ]
        }
    )

    definitions = load_resource_definitions(base_path=base_path)

    assert [item.key for item in definitions] == ["spirit_stone", "basic_herb"]
    assert definitions[0].display_name == "灵石"
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
