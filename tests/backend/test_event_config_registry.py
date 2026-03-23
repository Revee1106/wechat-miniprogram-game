from app.core_loop.event_config import load_event_registry
from app.core_loop.types import EventOptionConfig, EventTemplateConfig


def test_event_registry_loads_twelve_seed_events() -> None:
    registry = load_event_registry()

    assert len(registry.templates) == 12
    assert "evt_mountain_spirit_tide_001" in registry.templates
    assert "opt_mountain_spirit_tide_001_absorb" in registry.options

    for template in registry.templates.values():
        assert template.option_ids
        for option_id in template.option_ids:
            option = registry.options[option_id]
            assert option.event_id == template.event_id


def test_event_registry_exposes_spec_fields_and_sorted_options() -> None:
    registry = load_event_registry()
    template = registry.templates["evt_herb_gathering_003"]
    options = registry.get_options_for_event("evt_herb_gathering_003")

    assert template.event_id == "evt_herb_gathering_003"
    assert template.event_type == "material"
    assert template.outcome_type == "material"
    assert template.risk_level == "normal"
    assert template.choice_pattern == "binary_choice"
    assert template.title_text
    assert template.body_text
    assert template.realm_min is None
    assert template.realm_max is None
    assert template.region == "forest"
    assert template.weight > 0
    assert template.required_resources == {}
    assert template.required_rebirth_count == 0
    assert template.required_luck_min == 0
    assert template.flags == []
    assert options[0].sort_order < options[1].sort_order
    assert options[0].is_default is True
    assert options[1].is_default is False
    assert options[0].event_id == template.event_id
    assert options[1].event_id == template.event_id


def test_event_registry_seed_data_uses_allowed_vocab_and_unique_option_links() -> None:
    registry = load_event_registry()

    allowed_event_types = {
        "cultivation",
        "material",
        "technique",
        "equipment",
        "encounter",
        "survival",
    }
    allowed_risk_levels = {"normal", "risky"}
    allowed_trigger_sources = {
        "realm_based",
        "region_based",
        "dwelling_based",
        "technique_based",
        "equipment_based",
        "status_based",
        "karma_based",
        "luck_based",
        "rebirth_based",
        "global",
    }
    allowed_outcome_types = {
        "cultivation",
        "material",
        "technique",
        "equipment",
        "lifespan",
        "status",
        "luck",
        "mixed",
    }

    referenced_option_ids: set[str] = set()
    option_reference_counts: dict[str, int] = {
        option_id: 0 for option_id in registry.options
    }
    for template in registry.templates.values():
        assert template.event_type in allowed_event_types
        assert template.outcome_type in allowed_outcome_types
        assert template.risk_level in allowed_risk_levels
        assert template.realm_min is None
        assert template.realm_max is None
        assert set(template.trigger_sources).issubset(allowed_trigger_sources)
        assert len(template.option_ids) == len(set(template.option_ids))
        referenced_option_ids.update(template.option_ids)
        for option_id in template.option_ids:
            option_reference_counts[option_id] += 1

    assert referenced_option_ids == set(registry.options)
    assert all(count == 1 for count in option_reference_counts.values())


def test_event_registry_rejects_orphan_and_duplicate_option_references(monkeypatch) -> None:
    from app.core_loop import event_config

    monkeypatch.setattr(
        event_config,
        "EVENT_TEMPLATE_CONFIGS",
        [
            EventTemplateConfig(
                "evt_one",
                "One",
                "cultivation",
                ["opt_shared"],
            ),
            EventTemplateConfig(
                "evt_two",
                "Two",
                "material",
                ["opt_shared"],
            ),
        ],
    )
    monkeypatch.setattr(
        event_config,
        "EVENT_OPTION_CONFIGS",
        [
            EventOptionConfig("opt_shared", "evt_one", "Shared"),
            EventOptionConfig("opt_orphan", "evt_two", "Orphan"),
        ],
    )

    try:
        load_event_registry()
    except ValueError as exc:
        message = str(exc)
        assert "duplicate option reference" in message or "orphan option" in message
    else:  # pragma: no cover - defensive
        raise AssertionError("expected option reference validation to fail")


def test_event_registry_rejects_unknown_event_option_lookup() -> None:
    registry = load_event_registry()

    try:
        registry.get_options_for_event("evt_missing")
    except ValueError as exc:
        assert "unknown event_id" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected unknown event lookup to fail")


def test_event_registry_rejects_duplicate_event_ids(monkeypatch) -> None:
    from app.core_loop import event_config

    monkeypatch.setattr(
        event_config,
        "EVENT_TEMPLATE_CONFIGS",
        [
            EventTemplateConfig("evt_duplicate", "First", "test", ["opt_first"]),
            EventTemplateConfig("evt_duplicate", "Second", "test", ["opt_second"]),
        ],
    )
    monkeypatch.setattr(
        event_config,
        "EVENT_OPTION_CONFIGS",
        [
            EventOptionConfig("opt_first", "evt_duplicate", "First"),
            EventOptionConfig("opt_second", "evt_duplicate", "Second"),
        ],
    )

    try:
        load_event_registry()
    except ValueError as exc:
        assert "duplicate event_id" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected duplicate event_id to fail")


def test_event_registry_rejects_duplicate_option_ids(monkeypatch) -> None:
    from app.core_loop import event_config

    monkeypatch.setattr(
        event_config,
        "EVENT_TEMPLATE_CONFIGS",
        [EventTemplateConfig("evt_template", "Template", "test", ["opt_first"])],
    )
    monkeypatch.setattr(
        event_config,
        "EVENT_OPTION_CONFIGS",
        [
            EventOptionConfig("opt_first", "evt_template", "First"),
            EventOptionConfig("opt_first", "evt_template", "Duplicate"),
        ],
    )

    try:
        load_event_registry()
    except ValueError as exc:
        assert "duplicate option_id" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected duplicate option_id to fail")


def test_event_registry_rejects_missing_or_mismatched_option_links(monkeypatch) -> None:
    from app.core_loop import event_config

    monkeypatch.setattr(
        event_config,
        "EVENT_TEMPLATE_CONFIGS",
        [
            EventTemplateConfig(
                "evt_template",
                "Template",
                "test",
                ["opt_missing", "opt_wrong_event"],
            )
        ],
    )
    monkeypatch.setattr(
        event_config,
        "EVENT_OPTION_CONFIGS",
        [
            EventOptionConfig("opt_wrong_event", "evt_other", "Wrong event"),
        ],
    )

    try:
        load_event_registry()
    except ValueError as exc:
        message = str(exc)
        assert "missing option_id" in message or "event_id mismatch" in message
    else:  # pragma: no cover - defensive
        raise AssertionError("expected option linkage validation to fail")
