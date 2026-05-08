from __future__ import annotations

import json

import pytest

from app.admin.services.equipment_admin_service import EquipmentAdminService
from app.admin.services.equipment_validation_service import validate_equipment_config
from app.core_loop.services.run_service import RunService


def test_equipment_validation_enforces_slot_rules() -> None:
    result = validate_equipment_config(
        items=[
            {
                "equipment_id": "bad_sword",
                "display_name": "Bad Sword",
                "slot": "weapon",
                "attack": 2,
                "defense": 1,
                "hp_max": 0,
                "special_effects": {},
            },
            {
                "equipment_id": "bad_robe",
                "display_name": "Bad Robe",
                "slot": "armor",
                "attack": 1,
                "defense": 2,
                "hp_max": 6,
                "special_effects": {},
            },
            {
                "equipment_id": "plain_ring",
                "display_name": "Plain Ring",
                "slot": "accessory",
                "attack": 0,
                "defense": 0,
                "hp_max": 0,
                "special_effects": {},
            },
        ]
    )

    assert not result.is_valid
    assert "weapon 'bad_sword' may only provide attack" in result.errors
    assert "armor 'bad_robe' may only provide defense and hp_max" in result.errors
    assert "accessory 'plain_ring' must provide special_effects" in result.errors


def test_equipment_admin_service_saves_and_reloads_runtime_config(tmp_path) -> None:
    fake_run_service = FakeRunService()
    service = EquipmentAdminService(base_path=str(tmp_path), run_service=fake_run_service)

    created = service.create_item(
        {
            "equipment_id": "test_sword",
            "display_name": "Test Sword",
            "slot": "weapon",
            "description": "For tests",
            "attack": 3,
            "defense": 0,
            "hp_max": 0,
            "special_effects": {},
        }
    )

    assert created["equipment_id"] == "test_sword"
    assert service.list_items()["items"][0]["display_name"] == "Test Sword"

    result = service.reload_runtime_config()

    assert result == {"reloaded": True, "equipment_count": 1}
    assert fake_run_service.reloaded_base_path == str(tmp_path)


def test_run_service_uses_equipment_config_for_combat_stats(tmp_path) -> None:
    config_dir = tmp_path / "config" / "equipment"
    config_dir.mkdir(parents=True)
    (config_dir / "items.json").write_text(
        json.dumps(
            [
                {
                    "equipment_id": "test_sword",
                    "display_name": "Test Sword",
                    "slot": "weapon",
                    "description": "For tests",
                    "attack": 7,
                    "defense": 0,
                    "hp_max": 0,
                    "special_effects": {},
                },
                {
                    "equipment_id": "test_armor",
                    "display_name": "Test Armor",
                    "slot": "armor",
                    "description": "For tests",
                    "attack": 0,
                    "defense": 3,
                    "hp_max": 20,
                    "special_effects": {},
                },
            ]
        ),
        encoding="utf-8",
    )

    service = RunService(equipment_config_base_path=str(tmp_path))
    run = service.create_run(player_id="p1")
    run.character.equipment_tags = ["test_sword", "test_armor"]

    base_attack = service.get_run(run.run_id).character.hp_max
    equipped = service.equip_item(run.run_id, "test_sword")
    equipped = service.equip_item(run.run_id, "test_armor")

    sword = next(item for item in equipped.equipment_inventory if item.item_id == "test_sword")
    armor = next(item for item in equipped.equipment_inventory if item.item_id == "test_armor")
    assert sword.attack == 7
    assert sword.speed == 0
    assert armor.defense == 3
    assert armor.hp_max == 20
    assert equipped.character.equipped_items == {
        "weapon": "test_sword",
        "armor": "test_armor",
    }
    assert service.get_run(run.run_id).character.hp_max == base_attack


def test_equipment_admin_service_rejects_invalid_updates(tmp_path) -> None:
    service = EquipmentAdminService(base_path=str(tmp_path))
    service.create_item(
        {
            "equipment_id": "test_sword",
            "display_name": "Test Sword",
            "slot": "weapon",
            "description": "",
            "attack": 3,
            "defense": 0,
            "hp_max": 0,
            "special_effects": {},
        }
    )

    with pytest.raises(ValueError, match="may only provide attack"):
        service.update_item(
            "test_sword",
            {
                "equipment_id": "test_sword",
                "display_name": "Test Sword",
                "slot": "weapon",
                "description": "",
                "attack": 3,
                "defense": 1,
                "hp_max": 0,
                "special_effects": {},
            },
        )


class FakeRunService:
    def __init__(self) -> None:
        self.reloaded_base_path: str | None = None

    def reload_equipment_config(self, equipment_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = equipment_config_base_path
