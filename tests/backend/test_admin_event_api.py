import os
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_admin_event_list_endpoint_returns_items() -> None:
    client = _create_authorized_client()

    response = client.get("/admin/api/events")

    assert response.status_code == 200
    assert "items" in response.json()


def test_admin_event_create_endpoint_persists_event(monkeypatch) -> None:
    from app.admin import api as admin_api
    from app.admin.services.event_admin_service import EventAdminService

    client = _create_authorized_client()
    base_path = _make_test_base_path("admin-api")
    monkeypatch.setattr(
        admin_api,
        "event_admin_service",
        EventAdminService(base_path=base_path),
    )

    create_response = client.post(
        "/admin/api/events",
        json={
            "event_id": "evt_admin_created",
            "event_name": "Admin Created",
            "event_type": "cultivation",
            "outcome_type": "cultivation",
            "risk_level": "normal",
            "trigger_sources": ["global"],
            "choice_pattern": "binary_choice",
            "title_text": "Admin Created",
            "body_text": "Body",
            "weight": 1,
            "is_repeatable": True,
            "option_ids": [],
        },
    )
    list_response = client.get("/admin/api/events")

    assert create_response.status_code == 200
    assert any(
        item["event_id"] == "evt_admin_created"
        for item in list_response.json()["items"]
    )
    rmtree(base_path)


def test_admin_event_list_endpoint_filters_by_type(monkeypatch) -> None:
    from app.admin import api as admin_api
    from app.admin.repositories.event_config_repository import EventConfigRepository
    from app.admin.services.event_admin_service import EventAdminService

    client = _create_authorized_client()
    base_path = _make_test_base_path("admin-api-filter")
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
                    "body_text": "Body",
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
                    "body_text": "Body",
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
    monkeypatch.setattr(
        admin_api,
        "event_admin_service",
        EventAdminService(base_path=base_path),
    )

    response = client.get("/admin/api/events", params={"event_type": "material"})

    assert response.status_code == 200
    assert [item["event_id"] for item in response.json()["items"]] == ["evt_material"]
    rmtree(base_path)


def test_admin_event_reload_endpoint_returns_counts(monkeypatch) -> None:
    from app.admin import api as admin_api
    from app.admin.repositories.event_config_repository import EventConfigRepository
    from app.admin.services.event_admin_service import EventAdminService

    client = _create_authorized_client()
    base_path = _make_test_base_path("admin-api-reload")
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
    monkeypatch.setattr(
        admin_api,
        "event_admin_service",
        EventAdminService(base_path=base_path, run_service=_ReloadRunService()),
    )

    response = client.post("/admin/api/events/reload")

    assert response.status_code == 200
    assert response.json() == {"reloaded": True, "template_count": 1, "option_count": 1}
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
    def reload_event_config(self, event_config_base_path: str | None = None) -> None:
        self.event_config_base_path = event_config_base_path
