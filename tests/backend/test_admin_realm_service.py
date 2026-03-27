from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.admin.services.realm_admin_service import RealmAdminService
from app.core_loop.services.run_service import RunService


def test_service_lists_realms() -> None:
    base_path = _make_test_base_path("realm-service-list")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "鐐兼皵鍒濇湡",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                }
            ]
        }
    )

    service = RealmAdminService(base_path=base_path)

    result = service.list_realms()

    assert [item["key"] for item in result["items"]] == ["qi_refining_early"]
    rmtree(base_path)


def test_service_returns_realm_detail() -> None:
    base_path = _make_test_base_path("realm-service-detail")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "鐐兼皵鍒濇湡",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                }
            ]
        }
    )

    service = RealmAdminService(base_path=base_path)

    result = service.get_realm("qi_refining_early")

    assert result["key"] == "qi_refining_early"
    rmtree(base_path)


def test_service_creates_updates_and_deletes_realms() -> None:
    base_path = _make_test_base_path("realm-service-crud")
    service = RealmAdminService(base_path=base_path)

    created = service.create_realm(
        {
            "key": "qi_refining_early",
            "display_name": "鐐兼皵鍒濇湡",
            "major_realm": "qi_refining",
            "stage_index": 1,
            "order_index": 1,
            "base_success_rate": 0.95,
            "required_cultivation_exp": 100,
            "required_spirit_stone": 20,
            "lifespan_bonus": 6,
            "is_enabled": True,
        }
    )
    updated = service.update_realm(
        "qi_refining_early",
        {
            "key": "qi_refining_early",
            "display_name": "鐐兼皵鍒濇湡锛堟洿鏂帮級",
            "major_realm": "qi_refining",
            "stage_index": 1,
            "order_index": 2,
            "base_success_rate": 0.9,
            "required_cultivation_exp": 120,
            "required_spirit_stone": 25,
            "lifespan_bonus": 8,
            "is_enabled": True,
        },
    )
    deleted = service.delete_realm("qi_refining_early")

    assert created["key"] == "qi_refining_early"
    assert updated["display_name"] == "鐐兼皵鍒濇湡锛堟洿鏂帮級"
    assert deleted is True
    rmtree(base_path)


def test_service_blocks_deleting_referenced_realm() -> None:
    base_path = _make_test_base_path("realm-service-delete-blocked")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "鐐兼皵鍒濇湡",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                }
            ]
        }
    )
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_realm_locked",
                    "event_name": "Realm Locked",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "Realm Locked",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "realm_min": "qi_refining_early",
                    "option_ids": ["opt_realm_locked"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_realm_locked",
                    "event_id": "evt_realm_locked",
                    "option_text": "Absorb",
                    "sort_order": 1,
                    "is_default": True,
                }
            ],
        }
    )

    service = RealmAdminService(base_path=base_path)

    try:
        service.delete_realm("qi_refining_early")
    except ValueError as error:
        assert "evt_realm_locked" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected delete to be blocked")
    rmtree(base_path)


def test_service_blocks_disabling_referenced_realm() -> None:
    base_path = _make_test_base_path("realm-service-disable-blocked")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "鐐兼皵鍒濇湡",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                }
            ]
        }
    )
    EventConfigRepository(base_path=base_path).save(
        {
            "templates": [
                {
                    "event_id": "evt_realm_locked",
                    "event_name": "Realm Locked",
                    "event_type": "cultivation",
                    "outcome_type": "cultivation",
                    "risk_level": "normal",
                    "trigger_sources": ["global"],
                    "choice_pattern": "binary_choice",
                    "title_text": "Realm Locked",
                    "body_text": "Body",
                    "weight": 1,
                    "is_repeatable": True,
                    "realm_max": "qi_refining_early",
                    "option_ids": ["opt_realm_locked"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_realm_locked",
                    "event_id": "evt_realm_locked",
                    "option_text": "Absorb",
                    "sort_order": 1,
                    "is_default": True,
                }
            ],
        }
    )

    service = RealmAdminService(base_path=base_path)

    try:
        service.update_realm(
            "qi_refining_early",
            {
                "key": "qi_refining_early",
                "display_name": "鐐兼皵鍒濇湡",
                "major_realm": "qi_refining",
                "stage_index": 1,
                "order_index": 1,
                "base_success_rate": 0.95,
                "required_cultivation_exp": 100,
                "required_spirit_stone": 20,
                "lifespan_bonus": 6,
                "is_enabled": False,
            },
        )
    except ValueError as error:
        assert "evt_realm_locked" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected update to be blocked")
    rmtree(base_path)


def test_service_reloads_runtime_config() -> None:
    base_path = _make_test_base_path("realm-service-reload")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "鐐兼皵鍒濇湡",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                }
            ]
        }
    )
    run_service = _ReloadRunService()
    service = RealmAdminService(base_path=base_path, run_service=run_service)

    result = service.reload_runtime_config()

    assert result["reloaded"] is True
    assert result["realm_count"] == 1
    assert run_service.reloaded_base_path == str(base_path)
    rmtree(base_path)


def test_service_reorders_realms_by_key_sequence() -> None:
    base_path = _make_test_base_path("realm-service-reorder")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "Qi Refining Early",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.95,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 20,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
                {
                    "key": "qi_refining_mid",
                    "display_name": "Qi Refining Mid",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 0.9,
                    "required_cultivation_exp": 180,
                    "required_spirit_stone": 30,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
            ]
        }
    )

    service = RealmAdminService(base_path=base_path)

    result = service.reorder_realms(["qi_refining_mid", "qi_refining_early"])

    assert [item["key"] for item in result["items"]] == ["qi_refining_mid", "qi_refining_early"]
    assert [item["order_index"] for item in result["items"]] == [1, 2]
    rmtree(base_path)


def test_run_service_reloads_realm_config_into_runtime_services() -> None:
    base_path = _make_test_base_path("realm-service-runtime-reload")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "custom_early",
                    "display_name": "Custom Early",
                    "major_realm": "custom",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.5,
                    "required_cultivation_exp": 10,
                    "required_spirit_stone": 3,
                    "lifespan_bonus": 2,
                    "is_enabled": True,
                }
            ]
        }
    )

    service = RunService()
    service.reload_realm_config(realm_config_base_path=str(base_path))

    assert service._progression_service._realm_configs[0].key == "custom_early"
    assert service._event_service._realm_configs[0].key == "custom_early"
    rmtree(base_path)


def test_run_service_initializes_realm_configs_from_event_base_path() -> None:
    base_path = _make_test_base_path("realm-service-init-base-path")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "custom_early",
                    "display_name": "Custom Early",
                    "major_realm": "custom",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.5,
                    "required_cultivation_exp": 10,
                    "required_spirit_stone": 3,
                    "lifespan_bonus": 2,
                    "is_enabled": True,
                }
            ]
        }
    )

    service = RunService(event_config_base_path=str(base_path))

    assert service._realm_configs[0].key == "custom_early"
    assert service._progression_service._realm_configs[0].key == "custom_early"
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


class _ReloadRunService:
    def __init__(self) -> None:
        self.reloaded_base_path: str | None = None

    def reload_realm_config(self, realm_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = realm_config_base_path


