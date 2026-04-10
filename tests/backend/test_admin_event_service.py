from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.admin.services.event_admin_service import EventAdminService


def test_service_returns_event_detail_with_options() -> None:
    base_path = _make_test_base_path("admin-detail")
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_sample",
                    "event_name": "Sample",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "Sample",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["opt_sample"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_sample",
                    "event_id": "evt_sample",
                    "option_text": "Option",
                    "sort_order": 1,
                    "is_default": True,
                }
            ],
        }
    )
    service = EventAdminService(base_path=base_path)

    detail = service.get_event("evt_sample")

    assert detail["template"]["event_id"] == "evt_sample"
    assert detail["options"][0]["option_id"] == "opt_sample"
    rmtree(base_path)


def test_service_creates_event_template() -> None:
    base_path = _make_test_base_path("admin-create")
    service = EventAdminService(base_path=base_path)

    created = service.create_event(
        {
            "event_id": "evt_new",
            "event_name": "New Event",
            "event_type": "material",
            "outcome_type": "material",
            "risk_level": "normal",
            "trigger_sources": ["global"],
            "choice_pattern": "binary_choice",
            "title_text": "New Event",
            "body_text": "Body",
            "weight": 2,
            "is_repeatable": True,
            "option_ids": [],
        }
    )

    assert created["event_id"] == "evt_new"
    assert any(item["event_id"] == "evt_new" for item in service.list_events()["items"])
    rmtree(base_path)


def test_service_filters_events_by_type_and_keyword() -> None:
    base_path = _make_test_base_path("admin-filter")
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_cultivation",
                    "event_name": "Mountain Tide",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "Mountain Tide",
                    "body_text": "Spirit tide gathers in the mountain.",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["opt_cultivation"],
                },
                {
                    "event_id": "evt_material",
                    "event_name": "Herb Search",
                    "event_type": "material",
                    "outcome_type": "material",
                    "risk_level": "safe",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "Herb Search",
                    "body_text": "You search the valley for herbs.",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["opt_material"],
                },
            ],
            "options": [
                {
                    "option_id": "opt_cultivation",
                    "event_id": "evt_cultivation",
                    "option_text": "Absorb",
                    "sort_order": 1,
                    "is_default": True,
                },
                {
                    "option_id": "opt_material",
                    "event_id": "evt_material",
                    "option_text": "Search",
                    "sort_order": 1,
                    "is_default": True,
                },
            ],
        }
    )
    service = EventAdminService(base_path=base_path)

    filtered = service.list_events(event_type="material", keyword="herb")

    assert [item["event_id"] for item in filtered["items"]] == ["evt_material"]
    rmtree(base_path)


def test_service_reloads_runtime_config() -> None:
    base_path = _make_test_base_path("admin-reload")
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_reload",
                    "event_name": "Reload",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "Reload",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["opt_reload"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_reload",
                    "event_id": "evt_reload",
                    "option_text": "Absorb",
                    "sort_order": 1,
                    "is_default": True,
                    "result_on_success": {"resources": {"spirit_stone": 1}},
                    "result_on_failure": {"resources": {}},
                }
            ],
        }
    )
    run_service = _ReloadRunService()
    service = EventAdminService(base_path=base_path, run_service=run_service)

    result = service.reload_runtime_config()

    assert result == {"reloaded": True, "template_count": 1, "option_count": 1}
    assert run_service.reloaded_base_path == str(base_path)
    rmtree(base_path)


def test_service_create_option_repairs_blank_option_id_records() -> None:
    base_path = _make_test_base_path("admin-repair-blank-option")
    repository = EventConfigRepository(base_path=base_path)
    repository.save(
        {
            "templates": [
                {
                    "event_id": "evt_repair",
                    "event_name": "Repair",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "multi_choice",
                    "title_text": "Repair",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["", "evt_repair_option_2", "evt_repair_option_3"],
                }
            ],
            "options": [
                {
                    "option_id": "",
                    "event_id": "evt_repair",
                    "option_text": "First",
                    "sort_order": 1,
                    "is_default": True,
                },
                {
                    "option_id": "evt_repair_option_2",
                    "event_id": "evt_repair",
                    "option_text": "Second",
                    "sort_order": 2,
                    "is_default": False,
                },
                {
                    "option_id": "evt_repair_option_3",
                    "event_id": "evt_repair",
                    "option_text": "Third",
                    "sort_order": 3,
                    "is_default": False,
                },
            ],
        }
    )
    service = EventAdminService(base_path=base_path)

    created = service.create_option(
        "evt_repair",
        {
          "option_id": "evt_repair_option_1",
          "event_id": "evt_repair",
          "option_text": "First",
          "sort_order": 1,
          "is_default": True,
        },
    )

    payload = repository.load()

    assert created["option_id"] == "evt_repair_option_1"
    assert payload["templates"][0]["option_ids"] == [
        "evt_repair_option_1",
        "evt_repair_option_2",
        "evt_repair_option_3",
    ]
    assert all(option["option_id"] for option in payload["options"])
    assert len([option for option in payload["options"] if option["event_id"] == "evt_repair"]) == 3
    rmtree(base_path)


def test_service_create_option_generates_id_when_payload_is_blank() -> None:
    base_path = _make_test_base_path("admin-generate-blank-option-id")
    repository = EventConfigRepository(base_path=base_path)
    repository.save(
        {
            "templates": [
                {
                    "event_id": "evt_generate",
                    "event_name": "Generate",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "multi_choice",
                    "title_text": "Generate",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["", "evt_generate_option_2", "evt_generate_option_3"],
                }
            ],
            "options": [
                {
                    "option_id": "",
                    "event_id": "evt_generate",
                    "option_text": "First",
                    "sort_order": 1,
                    "is_default": True,
                },
                {
                    "option_id": "evt_generate_option_2",
                    "event_id": "evt_generate",
                    "option_text": "Second",
                    "sort_order": 2,
                    "is_default": False,
                },
                {
                    "option_id": "evt_generate_option_3",
                    "event_id": "evt_generate",
                    "option_text": "Third",
                    "sort_order": 3,
                    "is_default": False,
                },
            ],
        }
    )
    service = EventAdminService(base_path=base_path)

    created = service.create_option(
        "evt_generate",
        {
          "option_id": "",
          "event_id": "evt_generate",
          "option_text": "First",
          "sort_order": 1,
          "is_default": True,
        },
    )

    payload = repository.load()

    assert created["option_id"] == "evt_generate_option_1"
    assert payload["templates"][0]["option_ids"] == [
        "evt_generate_option_1",
        "evt_generate_option_2",
        "evt_generate_option_3",
    ]
    assert all(option["option_id"] for option in payload["options"])
    rmtree(base_path)


def test_service_create_option_repairs_blank_template_reference_without_blank_option_record() -> None:
    base_path = _make_test_base_path("admin-repair-blank-template-ref")
    repository = EventConfigRepository(base_path=base_path)
    repository.save(
        {
            "templates": [
                {
                    "event_id": "evt_template_ref",
                    "event_name": "Template Ref",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "multi_choice",
                    "title_text": "Template Ref",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "option_ids": ["", "evt_template_ref_option_2", "evt_template_ref_option_3"],
                }
            ],
            "options": [
                {
                    "option_id": "evt_template_ref_option_2",
                    "event_id": "evt_template_ref",
                    "option_text": "Second",
                    "sort_order": 2,
                    "is_default": False,
                },
                {
                    "option_id": "evt_template_ref_option_3",
                    "event_id": "evt_template_ref",
                    "option_text": "Third",
                    "sort_order": 3,
                    "is_default": False,
                },
            ],
        }
    )
    service = EventAdminService(base_path=base_path)

    created = service.create_option(
        "evt_template_ref",
        {
            "option_id": "evt_template_ref_option_1",
            "event_id": "evt_template_ref",
            "option_text": "First",
            "sort_order": 1,
            "is_default": True,
        },
    )

    payload = repository.load()

    assert created["option_id"] == "evt_template_ref_option_1"
    assert payload["templates"][0]["option_ids"] == [
        "evt_template_ref_option_1",
        "evt_template_ref_option_2",
        "evt_template_ref_option_3",
    ]
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


class _ReloadRunService:
    def __init__(self) -> None:
        self.reloaded_base_path: str | None = None

    def reload_event_config(self, event_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = event_config_base_path
