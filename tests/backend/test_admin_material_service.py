from __future__ import annotations

import json

import pytest

from app.admin.services.material_admin_service import MaterialAdminService
from app.admin.services.material_validation_service import validate_material_config
from app.core_loop.services.run_service import RunService
from app.api.schemas import serialize_run_state
from app.economy.resource_catalog import load_resource_definitions


def test_material_validation_requires_identity_and_metadata() -> None:
    result = validate_material_config(
        items=[
            {
                "material_id": "bad_material",
                "display_name": "",
                "category": "",
                "tier": 0,
                "rarity": "",
                "source": "",
                "description": "",
                "tags": [""],
            },
            {
                "material_id": "bad_material",
                "display_name": "Duplicate",
                "category": "herb",
                "tier": 1,
                "rarity": "common",
                "source": "dwelling",
                "description": "",
                "tags": ["basic"],
            },
        ]
    )

    assert not result.is_valid
    assert "duplicate material_id: bad_material" in result.errors
    assert "material 'bad_material' has empty display_name" in result.errors
    assert "material 'bad_material' has invalid tier" in result.errors


def test_material_admin_service_saves_and_reloads_runtime_config(tmp_path) -> None:
    fake_run_service = FakeRunService()
    service = MaterialAdminService(base_path=str(tmp_path), run_service=fake_run_service)

    created = service.create_item(
        {
            "material_id": "moonlit_herb",
            "display_name": "Moonlit Herb",
            "category": "herb",
            "tier": 1,
            "rarity": "common",
            "source": "dwelling",
            "description": "For tests",
            "tags": ["alchemy", "dwelling"],
        }
    )

    assert created["material_id"] == "moonlit_herb"
    assert service.list_items()["items"][0]["display_name"] == "Moonlit Herb"

    result = service.reload_runtime_config()

    assert result == {"reloaded": True, "material_count": 1}
    assert fake_run_service.reloaded_base_path == str(tmp_path)


def test_resource_catalog_prefers_material_config_over_economy_resource(tmp_path) -> None:
    economy_dir = tmp_path / "config" / "economy"
    economy_dir.mkdir(parents=True)
    (economy_dir / "resources.json").write_text(
        json.dumps(
            [
                {
                    "key": "basic_herb",
                    "display_name": "Old Herb",
                    "category": "legacy",
                    "tier": 2,
                    "rarity": "common",
                    "stackable": True,
                    "tags": ["old"],
                }
            ]
        ),
        encoding="utf-8",
    )
    materials_dir = tmp_path / "config" / "materials"
    materials_dir.mkdir(parents=True)
    (materials_dir / "items.json").write_text(
        json.dumps(
            [
                {
                    "material_id": "basic_herb",
                    "display_name": "基础灵草",
                    "category": "herb",
                    "tier": 1,
                    "rarity": "common",
                    "source": "dwelling",
                    "description": "",
                    "tags": ["alchemy"],
                }
            ]
        ),
        encoding="utf-8",
    )

    definitions = load_resource_definitions(base_path=tmp_path)
    herb = next(item for item in definitions if item.key == "basic_herb")

    assert herb.display_name == "基础灵草"
    assert herb.category == "herb"
    assert herb.tier == 1
    assert herb.tags == ["alchemy"]


def test_run_service_uses_material_config_for_stack_resources(tmp_path) -> None:
    materials_dir = tmp_path / "config" / "materials"
    materials_dir.mkdir(parents=True)
    (materials_dir / "items.json").write_text(
        json.dumps(
            [
                {
                    "material_id": "moonlit_herb",
                    "display_name": "Moonlit Herb",
                    "category": "herb",
                    "tier": 1,
                    "rarity": "common",
                    "source": "dwelling",
                    "description": "",
                    "tags": ["alchemy"],
                }
            ]
        ),
        encoding="utf-8",
    )

    service = RunService(material_config_base_path=str(tmp_path))
    run = service.create_run(player_id="p1")

    service._alchemy_service._resource_service.add(run, "moonlit_herb", 3)

    assert run.resource_stacks[0].resource_key == "moonlit_herb"
    assert run.resource_stacks[0].amount == 3


def test_serialized_run_exposes_configured_resource_definitions() -> None:
    service = RunService()
    run = service.create_run(player_id="resource-labels")

    serialized = serialize_run_state(run)
    definitions = {
        item["key"]: item["display_name"]
        for item in serialized["resource_definitions"]
    }

    assert definitions["basic_herb"] == "基础灵草"
    assert definitions["basic_ore"] == "基础矿材"
    assert definitions["spirit_spring_water"] == "灵泉水"


def test_material_admin_service_rejects_invalid_updates(tmp_path) -> None:
    service = MaterialAdminService(base_path=str(tmp_path))
    service.create_item(
        {
            "material_id": "basic_herb",
            "display_name": "Basic Herb",
            "category": "herb",
            "tier": 1,
            "rarity": "common",
            "source": "dwelling",
            "description": "",
            "tags": ["alchemy"],
        }
    )

    with pytest.raises(ValueError, match="invalid tier"):
        service.update_item(
            "basic_herb",
            {
                "material_id": "basic_herb",
                "display_name": "Basic Herb",
                "category": "herb",
                "tier": 0,
                "rarity": "common",
                "source": "dwelling",
                "description": "",
                "tags": ["alchemy"],
            },
        )


class FakeRunService:
    def __init__(self) -> None:
        self.reloaded_base_path: str | None = None

    def reload_material_config(self, material_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = material_config_base_path
