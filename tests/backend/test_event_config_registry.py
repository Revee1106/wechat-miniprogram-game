from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.core_loop.event_config import load_event_registry
from app.core_loop.types import EventOptionConfig, EventResultPayload, EventTemplateConfig


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
    assert template.is_repeatable is True
    assert template.cooldown_rounds >= 0
    assert template.max_trigger_per_run >= 1
    assert template.required_statuses == []
    assert template.excluded_statuses == []
    assert template.required_techniques == []
    assert template.required_equipment_tags == []
    assert template.required_resources == {}
    assert template.required_rebirth_count == 0
    assert template.required_karma_min is None
    assert template.required_luck_min == 0
    assert template.flags == []
    assert options[0].sort_order < options[1].sort_order
    assert options[0].is_default is True
    assert options[1].is_default is False
    assert options[0].event_id == template.event_id
    assert options[1].event_id == template.event_id
    assert options[0].requires_statuses == []
    assert options[0].requires_techniques == []
    assert options[0].requires_equipment_tags == []
    assert options[0].next_event_id is None
    assert isinstance(options[0].result_on_success, EventResultPayload)
    assert isinstance(options[0].result_on_failure, EventResultPayload)


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
        "breakthrough",
        "karma",
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
        assert template.cooldown_rounds >= 0
        assert template.max_trigger_per_run >= 1
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


def test_event_registry_rejects_invalid_next_event_and_equipment_mutation(monkeypatch) -> None:
    from app.core_loop import event_config

    monkeypatch.setattr(
        event_config,
        "EVENT_TEMPLATE_CONFIGS",
        [
            EventTemplateConfig(
                "evt_template",
                "Template",
                "encounter",
                ["opt_bad"],
            )
        ],
    )
    monkeypatch.setattr(
        event_config,
        "EVENT_OPTION_CONFIGS",
        [
            EventOptionConfig(
                "opt_bad",
                "evt_template",
                "Bad option",
                next_event_id="evt_missing",
                result_on_success=EventResultPayload(
                    equipment_add=["token"],
                    equipment_remove=["token"],
                ),
            )
        ],
    )

    try:
        load_event_registry()
    except ValueError as exc:
        message = str(exc)
        assert "next_event_id" in message or "equipment" in message
    else:  # pragma: no cover - defensive
        raise AssertionError("expected next event or equipment payload validation to fail")


def test_runtime_registry_loads_from_repository_files() -> None:
    base_path = _make_test_base_path("registry")
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_from_json",
                    "event_name": "From Json",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "From Json",
                    "body_text": "Body",
                    "weight": 3,
                    "is_repeatable": True,
                    "option_ids": ["opt_from_json"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_from_json",
                    "event_id": "evt_from_json",
                    "option_text": "Take It",
                    "sort_order": 1,
                    "is_default": True,
                    "result_on_success": {"character": {"cultivation_exp": 2}},
                }
            ],
        }
    )

    registry = load_event_registry(base_path=base_path)

    assert "evt_from_json" in registry.templates
    assert "opt_from_json" in registry.options
    rmtree(base_path)


def test_registry_normalizes_single_outcome_template_to_one_option() -> None:
    base_path = _make_test_base_path("registry-single-outcome-normalize")
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_single",
                    "event_name": "Single",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "safe",
                    "trigger_sources": ["global"],
                    "choice_pattern": "single_outcome",
                    "title_text": "Single",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["opt_first", "opt_default"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_first",
                    "event_id": "evt_single",
                    "option_text": "First",
                    "sort_order": 1,
                    "is_default": False,
                    "result_on_success": {"character": {"cultivation_exp": 1}},
                },
                {
                    "option_id": "opt_default",
                    "event_id": "evt_single",
                    "option_text": "Default",
                    "sort_order": 2,
                    "is_default": True,
                    "result_on_success": {"character": {"cultivation_exp": 5}},
                },
            ],
        }
    )

    registry = load_event_registry(base_path=base_path)

    assert registry.templates["evt_single"].option_ids == ["opt_default"]
    assert [option.option_id for option in registry.get_options_for_event("evt_single")] == [
        "opt_default"
    ]
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
