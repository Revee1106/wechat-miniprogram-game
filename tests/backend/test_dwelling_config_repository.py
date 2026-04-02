from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.dwelling_config_repository import DwellingConfigRepository


def test_dwelling_config_repository_creates_and_loads_default_file() -> None:
    base_path = _make_test_base_path("dwelling-config-repository-default")

    payload = DwellingConfigRepository(base_path=base_path).load()

    assert payload == {"facilities": []}
    assert (base_path / "config" / "dwelling" / "facilities.json").exists()
    rmtree(base_path)


def test_dwelling_config_repository_persists_facility_levels() -> None:
    base_path = _make_test_base_path("dwelling-config-repository-save")
    repository = DwellingConfigRepository(base_path=base_path)
    repository.save(
        {
            "facilities": [
                {
                    "facility_id": "spirit_field",
                    "display_name": "灵田",
                    "facility_type": "production",
                    "summary": "提供基础灵植产出",
                    "function_unlock_text": "",
                    "levels": [
                        {
                            "level": 1,
                            "entry_cost": {"spirit_stone": 50},
                            "maintenance_cost": {"spirit_stone": 2},
                            "resource_yields": {"basic_herb": 2},
                            "cultivation_exp_gain": 0,
                            "special_effects": {},
                        },
                        {
                            "level": 2,
                            "entry_cost": {"spirit_stone": 40},
                            "maintenance_cost": {"spirit_stone": 3},
                            "resource_yields": {"basic_herb": 3},
                            "cultivation_exp_gain": 0,
                            "special_effects": {},
                        },
                    ],
                }
            ]
        }
    )

    reloaded = repository.load()

    assert reloaded["facilities"][0]["facility_id"] == "spirit_field"
    assert reloaded["facilities"][0]["levels"][1]["level"] == 2
    assert reloaded["facilities"][0]["levels"][1]["entry_cost"] == {"spirit_stone": 40}
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path

