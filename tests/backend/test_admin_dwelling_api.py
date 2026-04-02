import os
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi.testclient import TestClient

from app.admin import api as admin_api
from app.admin.repositories.dwelling_config_repository import DwellingConfigRepository
from app.admin.services.dwelling_admin_service import DwellingAdminService
from app.main import app


def test_admin_dwelling_list_endpoint_returns_facilities(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("dwelling-api-list")
    DwellingConfigRepository(base_path=base_path).save({"facilities": [_sample_facility()]})
    monkeypatch.setattr(
        admin_api,
        "dwelling_admin_service",
        DwellingAdminService(base_path=base_path),
    )

    response = client.get("/admin/api/dwelling/facilities")

    assert response.status_code == 200
    assert response.json()["items"][0]["facility_id"] == "spirit_field"
    assert response.json()["items"][0]["max_level"] == 3
    rmtree(base_path)


def test_admin_dwelling_detail_endpoint_returns_facility(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("dwelling-api-detail")
    DwellingConfigRepository(base_path=base_path).save({"facilities": [_sample_facility()]})
    monkeypatch.setattr(
        admin_api,
        "dwelling_admin_service",
        DwellingAdminService(base_path=base_path),
    )

    response = client.get("/admin/api/dwelling/facilities/spirit_field")

    assert response.status_code == 200
    assert response.json()["facility_id"] == "spirit_field"
    assert response.json()["levels"][2]["level"] == 3
    rmtree(base_path)


def test_admin_dwelling_update_endpoint_persists_new_level(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("dwelling-api-update")
    DwellingConfigRepository(base_path=base_path).save({"facilities": [_sample_facility()]})
    monkeypatch.setattr(
        admin_api,
        "dwelling_admin_service",
        DwellingAdminService(base_path=base_path),
    )

    payload = _sample_facility()
    payload["levels"].append(
        {
            "level": 4,
            "entry_cost": {"spirit_stone": 70},
            "maintenance_cost": {"spirit_stone": 5},
            "resource_yields": {"basic_herb": 7},
            "cultivation_exp_gain": 1,
            "special_effects": {},
        }
    )

    response = client.put("/admin/api/dwelling/facilities/spirit_field", json=payload)

    assert response.status_code == 200
    assert response.json()["levels"][3]["level"] == 4
    reloaded = DwellingConfigRepository(base_path=base_path).load()
    assert reloaded["facilities"][0]["levels"][3]["entry_cost"] == {"spirit_stone": 70}
    rmtree(base_path)


def test_admin_dwelling_reload_endpoint_calls_run_service(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("dwelling-api-reload")
    run_service = _ReloadRunService()
    DwellingConfigRepository(base_path=base_path).save({"facilities": [_sample_facility()]})
    monkeypatch.setattr(
        admin_api,
        "dwelling_admin_service",
        DwellingAdminService(base_path=base_path, run_service=run_service),
    )

    response = client.post("/admin/api/dwelling/reload")

    assert response.status_code == 200
    assert response.json()["facility_count"] == 1
    assert run_service.reloaded_base_path == str(base_path)
    rmtree(base_path)


def _sample_facility() -> dict[str, object]:
    return {
        "facility_id": "spirit_field",
        "display_name": "灵田",
        "facility_type": "production",
        "summary": "提供灵植",
        "function_unlock_text": "",
        "levels": [
            {
                "level": 1,
                "entry_cost": {"spirit_stone": 50},
                "maintenance_cost": {"spirit_stone": 2},
                "resource_yields": {"basic_herb": 2},
                "cultivation_exp_gain": 0,
                "special_effects": {},
            },
            {
                "level": 2,
                "entry_cost": {"spirit_stone": 40},
                "maintenance_cost": {"spirit_stone": 3},
                "resource_yields": {"basic_herb": 3},
                "cultivation_exp_gain": 0,
                "special_effects": {},
            },
            {
                "level": 3,
                "entry_cost": {"spirit_stone": 55},
                "maintenance_cost": {"spirit_stone": 4},
                "resource_yields": {"basic_herb": 5},
                "cultivation_exp_gain": 0,
                "special_effects": {},
            },
        ],
    }


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

    def reload_dwelling_config(self, dwelling_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = dwelling_config_base_path
