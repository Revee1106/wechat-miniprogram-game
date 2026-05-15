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


def test_validation_accepts_alchemy_event_fields() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_alchemy_scroll",
                "event_name": "Alchemy Scroll",
                "event_type": "alchemy",
                "outcome_type": "alchemy",
                "risk_level": "normal",
                "trigger_sources": ["alchemy_based"],
                "choice_pattern": "binary_choice",
                "title_text": "Alchemy Scroll",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": False,
                "required_alchemy_level": 1,
                "required_dwelling_facility_levels": {"alchemy_room": 1},
                "excluded_learned_alchemy_recipe_ids": ["ning_qi_dan"],
                "required_completed_event_ids": [],
                "option_ids": ["opt_learn_recipe"],
            }
        ],
        options=[
            {
                "option_id": "opt_learn_recipe",
                "event_id": "evt_alchemy_scroll",
                "option_text": "参悟丹方",
                "sort_order": 1,
                "result_on_success": {
                    "learned_alchemy_recipe_ids": ["ning_qi_dan"],
                    "alchemy_mastery_exp_delta": 9,
                },
            }
        ],
    )

    assert result.is_valid is True


def test_validation_rejects_invalid_progress_counter_requirements() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_progress",
                "event_name": "Progress",
                "event_type": "alchemy",
                "outcome_type": "alchemy",
                "risk_level": "normal",
                "trigger_sources": ["alchemy_based"],
                "choice_pattern": "binary_choice",
                "title_text": "Progress",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "required_progress_counters": {"": 1, "alchemy.clue": -1},
                "option_ids": ["opt_progress"],
            },
            {
                "event_id": "evt_progress_shape",
                "event_name": "Progress Shape",
                "event_type": "alchemy",
                "outcome_type": "alchemy",
                "risk_level": "normal",
                "trigger_sources": ["alchemy_based"],
                "choice_pattern": "binary_choice",
                "title_text": "Progress Shape",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "required_progress_counters": ["alchemy.clue"],
                "option_ids": ["opt_progress_shape"],
            },
        ],
        options=[
            {
                "option_id": "opt_progress",
                "event_id": "evt_progress",
                "option_text": "Progress",
                "sort_order": 1,
                "is_default": True,
            },
            {
                "option_id": "opt_progress_shape",
                "event_id": "evt_progress_shape",
                "option_text": "Progress Shape",
                "sort_order": 1,
                "is_default": True,
            },
        ],
    )

    assert result.is_valid is False
    assert any("required_progress_counters" in error for error in result.errors)


def test_validation_rejects_invalid_progress_counter_deltas() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_progress",
                "event_name": "Progress",
                "event_type": "alchemy",
                "outcome_type": "alchemy",
                "risk_level": "normal",
                "trigger_sources": ["alchemy_based"],
                "choice_pattern": "binary_choice",
                "title_text": "Progress",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_progress", "opt_progress_shape"],
            }
        ],
        options=[
            {
                "option_id": "opt_progress",
                "event_id": "evt_progress",
                "option_text": "Progress",
                "sort_order": 1,
                "result_on_success": {
                    "progress_counter_deltas": {"": 1, "alchemy.clue": "many"}
                },
            },
            {
                "option_id": "opt_progress_shape",
                "event_id": "evt_progress",
                "option_text": "Progress Shape",
                "sort_order": 2,
                "result_on_failure": {
                    "progress_counter_deltas": ["alchemy.clue"]
                },
            },
        ],
    )

    assert result.is_valid is False
    assert any("progress_counter_deltas" in error for error in result.errors)


def test_validation_rejects_invalid_result_change_chance() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_chance",
                "event_name": "Chance",
                "event_type": "cultivation",
                "outcome_type": "cultivation",
                "risk_level": "normal",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "Chance",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_chance"],
            }
        ],
        options=[
            {
                "option_id": "opt_chance",
                "event_id": "evt_chance",
                "option_text": "Chance",
                "sort_order": 1,
                "is_default": True,
                "result_on_success": {
                    "change_chance": 1.5,
                    "change_chances": {"character.lifespan_delta": 2},
                },
            }
        ],
    )

    assert result.is_valid is False
    assert any("change_chance" in error for error in result.errors)
    assert any("change_chances" in error for error in result.errors)


def test_validation_rejects_invalid_event_prerequisite_fields() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_unlock",
                "event_name": "Unlock",
                "event_type": "material",
                "outcome_type": "material",
                "risk_level": "normal",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "Unlock",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "required_completed_event_ids": ["evt_missing"],
                "required_dwelling_facility_levels": {"spirit_field": 0},
                "excluded_learned_alchemy_recipe_ids": [123],
                "option_ids": ["opt_unlock"],
            }
        ],
        options=[
            {
                "option_id": "opt_unlock",
                "event_id": "evt_unlock",
                "option_text": "Unlock",
                "sort_order": 1,
                "is_default": True,
            }
        ],
    )

    assert result.is_valid is False
    assert any("required_completed_event_id" in error for error in result.errors)
    assert any("required_dwelling_facility_levels" in error for error in result.errors)
    assert any("excluded_learned_alchemy_recipe_ids" in error for error in result.errors)


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


def test_validation_rejects_combat_option_without_battle_config() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_combat",
                "event_name": "Combat Event",
                "event_type": "encounter",
                "outcome_type": "mixed",
                "risk_level": "risky",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "Combat Event",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_combat"],
            }
        ],
        options=[
            {
                "option_id": "opt_combat",
                "event_id": "evt_combat",
                "option_text": "Fight",
                "sort_order": 1,
                "resolution_mode": "combat",
                "result_on_success": {
                    "resources": {"spirit_stone": 2},
                },
            }
        ],
    )

    assert result.is_valid is False
    assert any("battle" in error for error in result.errors)


def test_validation_accepts_combat_option_with_minimal_battle_config() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_combat",
                "event_name": "Combat Event",
                "event_type": "encounter",
                "outcome_type": "mixed",
                "risk_level": "risky",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "Combat Event",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_combat"],
            }
        ],
        options=[
            {
                "option_id": "opt_combat",
                "event_id": "evt_combat",
                "option_text": "Fight",
                "sort_order": 1,
                "resolution_mode": "combat",
                "result_on_success": {
                    "battle": {
                        "enemy_name": "山匪",
                        "enemy_realm_label": "炼气初期",
                        "enemy_hp": 36,
                        "enemy_attack": 8,
                        "enemy_defense": 4,
                        "enemy_speed": 6,
                        "allow_flee": True,
                        "flee_base_rate": 0.35,
                        "pill_heal_amount": 30,
                    }
                },
            }
        ],
    )

    assert result.is_valid is True


def test_validation_rejects_combat_option_with_missing_enemy_template_id() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_combat",
                "event_name": "Combat Event",
                "event_type": "encounter",
                "outcome_type": "mixed",
                "risk_level": "risky",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "Combat Event",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_combat"],
            }
        ],
        options=[
            {
                "option_id": "opt_combat",
                "event_id": "evt_combat",
                "option_text": "Fight",
                "sort_order": 1,
                "resolution_mode": "combat",
                "enemy_template_id": "enemy_missing",
                "result_on_success": {"resources": {"spirit_stone": 2}},
            }
        ],
        enemy_ids={"enemy_bandit_qi_early"},
    )

    assert result.is_valid is False
    assert any("enemy_template_id" in error and "enemy_missing" in error for error in result.errors)


def test_validation_accepts_combat_option_with_enemy_template_id() -> None:
    result = validate_event_config(
        templates=[
            {
                "event_id": "evt_combat",
                "event_name": "Combat Event",
                "event_type": "encounter",
                "outcome_type": "mixed",
                "risk_level": "risky",
                "trigger_sources": ["global"],
                "choice_pattern": "binary_choice",
                "title_text": "Combat Event",
                "body_text": "Body",
                "weight": 1,
                "is_repeatable": True,
                "option_ids": ["opt_combat"],
            }
        ],
        options=[
            {
                "option_id": "opt_combat",
                "event_id": "evt_combat",
                "option_text": "Fight",
                "sort_order": 1,
                "resolution_mode": "combat",
                "enemy_template_id": "enemy_bandit_qi_early",
                "result_on_success": {"resources": {"spirit_stone": 2}},
            }
        ],
        enemy_ids={"enemy_bandit_qi_early"},
    )

    assert result.is_valid is True
