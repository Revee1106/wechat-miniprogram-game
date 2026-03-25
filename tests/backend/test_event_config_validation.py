from app.admin.services.event_validation_service import validate_event_config


def test_validation_rejects_missing_option_reference() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_one",
                "event_name": "One",
                "event_type": "cultivation",
                "outcome_type": "cultivation",
                "risk_level": "normal",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "One",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_missing"],
            }
        ],
        options=[],
    )

    assert result.is_valid is False
    assert any("opt_missing" in error for error in result.errors)


def test_validation_rejects_conflicting_equipment_mutation() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_one",
                "event_name": "One",
                "event_type": "equipment",
                "outcome_type": "equipment",
                "risk_level": "normal",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "One",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_one"],
            }
        ],
        options=[
            {
                "option_id": "opt_one",
                "event_id": "evt_one",
                "option_text": "Option One",
                "sort_order": 1,
                "result_on_success": {
                    "equipment_add": ["jade_token"],
                    "equipment_remove": ["jade_token"],
                },
            }
        ],
    )

    assert result.is_valid is False
    assert any("equipment" in error for error in result.errors)
