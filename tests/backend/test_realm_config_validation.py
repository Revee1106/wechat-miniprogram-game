from app.admin.services.realm_validation_service import validate_realm_config


def test_validation_rejects_duplicate_keys_and_invalid_fields() -> None:
    result = validate_realm_config(
        realms=[
            {
                "key": "qi_refining_early",
                "display_name": "炼气初期",
                "major_realm": "qi_refining",
                "stage_index": 1,
                "order_index": 1,
                "base_success_rate": 0.85,
                "required_cultivation_exp": 100,
                "required_spirit_stone": 50,
                "lifespan_bonus": 12,
            },
            {
                "key": "qi_refining_early",
                "display_name": "",
                "major_realm": "",
                "stage_index": 0,
                "order_index": 1,
                "base_success_rate": 1.2,
                "required_cultivation_exp": -1,
                "required_spirit_stone": -2,
                "lifespan_bonus": -3,
            },
        ]
    )

    assert result.is_valid is False
    assert "duplicate realm key: qi_refining_early" in result.errors
    assert "duplicate order_index: 1" in result.errors
    assert any("display_name" in error for error in result.errors)
    assert any("base_success_rate" in error for error in result.errors)
    assert any("required_cultivation_exp" in error for error in result.errors)
    assert any("required_spirit_stone" in error for error in result.errors)
    assert any("lifespan_bonus" in error for error in result.errors)
    assert any("major_realm" in error for error in result.errors)
    assert any("stage_index" in error for error in result.errors)


def test_validation_collects_errors_for_non_numeric_string_fields() -> None:
    result = validate_realm_config(
        realms=[
            {
                "key": "qi_refining_early",
                "display_name": "炼气初期",
                "major_realm": "qi_refining",
                "stage_index": "one",
                "order_index": 1,
                "base_success_rate": "high",
                "required_cultivation_exp": "a lot",
                "required_spirit_stone": "many",
                "lifespan_bonus": "bonus",
            }
        ]
    )

    assert result.is_valid is False
    assert any("stage_index" in error for error in result.errors)
    assert any("base_success_rate" in error for error in result.errors)
    assert any("required_cultivation_exp" in error for error in result.errors)
    assert any("required_spirit_stone" in error for error in result.errors)
    assert any("lifespan_bonus" in error for error in result.errors)
