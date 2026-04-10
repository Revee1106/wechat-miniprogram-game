import os
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi.testclient import TestClient

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.admin import api as admin_api
from app.admin.services.realm_admin_service import RealmAdminService
from app.main import app


def test_admin_realm_list_endpoint_returns_items(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("realm-api-list")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
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
    monkeypatch.setattr(
        admin_api,
        "realm_admin_service",
        RealmAdminService(base_path=base_path),
    )

    response = client.get("/admin/api/realms")

    assert response.status_code == 200
    assert [item["key"] for item in response.json()["items"]] == [
        "qi_refining_early"
    ]
    rmtree(base_path)


def test_admin_realm_detail_endpoint_returns_realm(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("realm-api-detail")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
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
    monkeypatch.setattr(
        admin_api,
        "realm_admin_service",
        RealmAdminService(base_path=base_path),
    )

    response = client.get("/admin/api/realms/qi_refining_early")

    assert response.status_code == 200
    assert response.json()["key"] == "qi_refining_early"
    rmtree(base_path)


def test_admin_realm_validate_endpoint_returns_validation_state(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("realm-api-validate")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
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
    monkeypatch.setattr(
        admin_api,
        "realm_admin_service",
        RealmAdminService(base_path=base_path),
    )

    response = client.post("/admin/api/realms/validate")

    assert response.status_code == 200
    assert response.json()["is_valid"] is True
    rmtree(base_path)


def test_admin_realm_crud_and_reload_flow(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("realm-api-crud")
    run_service = _ReloadRunService()
    monkeypatch.setattr(
        admin_api,
        "realm_admin_service",
        RealmAdminService(base_path=base_path, run_service=run_service),
    )

    create_response = client.post(
        "/admin/api/realms",
        json={
            "key": "qi_refining_early",
            "display_name": "炼气初期",
            "major_realm": "qi_refining",
            "stage_index": 1,
            "order_index": 1,
            "base_success_rate": 0.95,
            "required_cultivation_exp": 100,
            "required_spirit_stone": 20,
            "lifespan_bonus": 6,
            "base_cultivation_gain_per_advance": 3,
            "base_spirit_stone_cost_per_advance": 1,
            "failure_penalty": {},
            "is_enabled": True,
        },
    )
    update_response = client.put(
        "/admin/api/realms/qi_refining_early",
        json={
            "key": "qi_refining_early",
            "display_name": "炼气初期（更新）",
            "major_realm": "qi_refining",
            "stage_index": 1,
            "order_index": 2,
            "base_success_rate": 0.9,
            "required_cultivation_exp": 120,
            "required_spirit_stone": 25,
            "lifespan_bonus": 8,
            "base_cultivation_gain_per_advance": 4,
            "base_spirit_stone_cost_per_advance": 2,
            "failure_penalty": {"character": {"cultivation_exp": -50}},
            "is_enabled": True,
        },
    )
    delete_response = client.delete("/admin/api/realms/qi_refining_early")
    reload_response = client.post("/admin/api/realms/reload")

    assert create_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["base_cultivation_gain_per_advance"] == 4
    assert update_response.json()["base_spirit_stone_cost_per_advance"] == 2
    assert update_response.json()["failure_penalty"] == {"character": {"cultivation_exp": -50}}
    assert delete_response.status_code == 200
    assert reload_response.status_code == 200
    assert reload_response.json()["realm_count"] == 0
    assert run_service.reloaded_base_path == str(base_path)
    rmtree(base_path)


def test_admin_realm_reorder_endpoint_updates_order_indices(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("realm-api-reorder")
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
    monkeypatch.setattr(
        admin_api,
        "realm_admin_service",
        RealmAdminService(base_path=base_path),
    )

    response = client.post(
        "/admin/api/realms/reorder",
        json={"keys": ["qi_refining_mid", "qi_refining_early"]},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["key"] for item in items] == ["qi_refining_mid", "qi_refining_early"]
    assert [item["order_index"] for item in items] == [1, 2]
    rmtree(base_path)


def test_admin_realm_delete_is_blocked_when_event_references_realm(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("realm-api-delete-blocked")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
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
    monkeypatch.setattr(
        admin_api,
        "realm_admin_service",
        RealmAdminService(base_path=base_path),
    )

    response = client.delete("/admin/api/realms/qi_refining_early")

    assert response.status_code == 400
    assert "evt_realm_locked" in response.json()["detail"]
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def _create_authorized_client() -> TestClient:
    os.environ["ADMIN_PASSWORD"] = "test-password"
    os.environ["ADMIN_SESSION_SECRET"] = "test-secret"
    client = TestClient(app)
    response = client.post(
        "/admin/api/auth/login",
        json={"username": "admin", "password": "test-password"},
    )
    if response.status_code != 200:
        raise AssertionError(response.text)
    return client


class _ReloadRunService:
    def __init__(self) -> None:
        self.reloaded_base_path: str | None = None

    def reload_realm_config(self, realm_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = realm_config_base_path
