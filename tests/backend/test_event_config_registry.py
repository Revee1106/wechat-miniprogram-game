from app.core_loop.event_config import load_event_registry
from app.core_loop.types import EventOptionConfig, EventTemplateConfig


def test_event_registry_loads_twelve_seed_events() -> None:
    registry = load_event_registry()

    assert len(registry.templates) == 12
    assert "evt_cultivation_spirit_tide_001" in registry.templates
    assert "opt_cultivation_spirit_tide_absorb" in registry.options

    for template in registry.templates.values():
        assert template.option_ids
        for option_id in template.option_ids:
            option = registry.options[option_id]
            assert option.event_id == template.event_id


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
