from app.admin.services.enemy_validation_service import validate_enemy_config


def test_validate_enemy_config_accepts_valid_enemy_template() -> None:
    result = validate_enemy_config(
        enemies=[
            {
                "enemy_id": "enemy_bandit_qi_early",
                "enemy_name": "山匪",
                "enemy_realm_label": "炼气初期",
                "enemy_hp": 36,
                "enemy_attack": 8,
                "enemy_defense": 4,
                "enemy_speed": 6,
                "allow_flee": True,
                "rewards": {
                    "resources": {"spirit_stone": 7},
                    "character": {"cultivation_exp": 5},
                },
            }
        ]
    )

    assert result.is_valid is True
    assert result.errors == []


def test_validate_enemy_config_rejects_duplicate_enemy_ids() -> None:
    result = validate_enemy_config(
        enemies=[
            {
                "enemy_id": "enemy_bandit_qi_early",
                "enemy_name": "山匪",
                "enemy_realm_label": "炼气初期",
                "enemy_hp": 36,
                "enemy_attack": 8,
                "enemy_defense": 4,
                "enemy_speed": 6,
                "allow_flee": True,
                "rewards": {},
            },
            {
                "enemy_id": "enemy_bandit_qi_early",
                "enemy_name": "山匪头目",
                "enemy_realm_label": "炼气中期",
                "enemy_hp": 48,
                "enemy_attack": 10,
                "enemy_defense": 6,
                "enemy_speed": 7,
                "allow_flee": False,
                "rewards": {},
            },
        ]
    )

    assert result.is_valid is False
    assert "duplicate enemy_id: enemy_bandit_qi_early" in result.errors


def test_validate_enemy_config_rejects_invalid_numeric_bounds() -> None:
    result = validate_enemy_config(
        enemies=[
            {
                "enemy_id": "enemy_invalid",
                "enemy_name": "失衡傀儡",
                "enemy_realm_label": "炼气初期",
                "enemy_hp": 0,
                "enemy_attack": -1,
                "enemy_defense": -1,
                "enemy_speed": -1,
                "allow_flee": True,
                "rewards": {},
            }
        ]
    )

    assert result.is_valid is False
    assert any("enemy_hp" in error for error in result.errors)
    assert any("enemy_attack" in error for error in result.errors)
    assert any("enemy_defense" in error for error in result.errors)
    assert any("enemy_speed" in error for error in result.errors)


def test_validate_enemy_config_rejects_nested_battle_payload_in_rewards() -> None:
    result = validate_enemy_config(
        enemies=[
            {
                "enemy_id": "enemy_nested_battle",
                "enemy_name": "镜中影",
                "enemy_realm_label": "炼气初期",
                "enemy_hp": 20,
                "enemy_attack": 4,
                "enemy_defense": 2,
                "enemy_speed": 5,
                "allow_flee": True,
                "rewards": {
                    "battle": {
                        "enemy_name": "不应嵌套",
                    }
                },
            }
        ]
    )

    assert result.is_valid is False
    assert any("rewards" in error and "battle" in error for error in result.errors)
