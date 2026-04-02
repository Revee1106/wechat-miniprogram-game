from app.admin.services.dwelling_validation_service import validate_dwelling_config


def test_validate_dwelling_config_accepts_valid_per_level_payload() -> None:
    result = validate_dwelling_config(
        facilities=[
            {
                "facility_id": "spirit_gathering_array",
                "display_name": "聚灵阵",
                "facility_type": "boost",
                "summary": "提供修为与增益",
                "function_unlock_text": "已解锁",
                "levels": [
                    {
                        "level": 1,
                        "entry_cost": {"spirit_stone": 100},
                        "maintenance_cost": {"spirit_stone": 4},
                        "resource_yields": {},
                        "cultivation_exp_gain": 6,
                        "special_effects": {
                            "breakthrough_bonus_rate": 0.02,
                            "mine_spirit_stone_bonus_rate": 0.1,
                        },
                    },
                    {
                        "level": 2,
                        "entry_cost": {"spirit_stone": 70},
                        "maintenance_cost": {"spirit_stone": 5},
                        "resource_yields": {},
                        "cultivation_exp_gain": 10,
                        "special_effects": {
                            "breakthrough_bonus_rate": 0.04,
                            "mine_spirit_stone_bonus_rate": 0.2,
                        },
                    },
                ],
            }
        ]
    )

    assert result.is_valid is True
    assert result.errors == []


def test_validate_dwelling_config_rejects_non_contiguous_levels() -> None:
    result = validate_dwelling_config(
        facilities=[
            {
                "facility_id": "spirit_field",
                "display_name": "灵田",
                "facility_type": "production",
                "summary": "提供灵植",
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
                        "level": 3,
                        "entry_cost": {"spirit_stone": 55},
                        "maintenance_cost": {"spirit_stone": 4},
                        "resource_yields": {"basic_herb": 5},
                        "cultivation_exp_gain": 0,
                        "special_effects": {},
                    },
                ],
            }
        ]
    )

    assert result.is_valid is False
    assert "levels must start at 1 and be contiguous" in result.errors[0]


def test_validate_dwelling_config_rejects_unknown_special_effect_key() -> None:
    result = validate_dwelling_config(
        facilities=[
            {
                "facility_id": "spirit_gathering_array",
                "display_name": "聚灵阵",
                "facility_type": "boost",
                "summary": "提供修为与增益",
                "function_unlock_text": "已解锁",
                "levels": [
                    {
                        "level": 1,
                        "entry_cost": {"spirit_stone": 100},
                        "maintenance_cost": {"spirit_stone": 4},
                        "resource_yields": {},
                        "cultivation_exp_gain": 6,
                        "special_effects": {"unknown_bonus": 1},
                    }
                ],
            }
        ]
    )

    assert result.is_valid is False
    assert "unknown special effect" in result.errors[0]
