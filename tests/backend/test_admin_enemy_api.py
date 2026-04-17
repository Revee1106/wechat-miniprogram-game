import os
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_admin_enemy_list_endpoint_returns_items() -> None:
    client = _create_authorized_client()

    response = client.get("/admin/api/battle/enemies")

    assert response.status_code == 200
    assert "items" in response.json()


def test_admin_enemy_create_endpoint_persists_enemy(monkeypatch) -> None:
    from app.admin import api as admin_api
    from app.admin.services.enemy_admin_service import EnemyAdminService

    client = _create_authorized_client()
    base_path = _make_test_base_path("admin-enemy-api")
    monkeypatch.setattr(
        admin_api,
        "enemy_admin_service",
        EnemyAdminService(base_path=base_path),
    )

    create_response = client.post(
        "/admin/api/battle/enemies",
        json={
            "enemy_id": "enemy_bandit_qi_early",
            "enemy_name": "山匪",
            "enemy_realm_label": "炼气初期",
            "enemy_hp": 36,
            "enemy_attack": 8,
            "enemy_defense": 4,
            "enemy_speed": 6,
            "allow_flee": True,
            "rewards": {"resources": {"spirit_stone": 7}},
        },
    )
    list_response = client.get("/admin/api/battle/enemies")

    assert create_response.status_code == 200
    assert any(
        item["enemy_id"] == "enemy_bandit_qi_early" for item in list_response.json()["items"]
    )
    rmtree(base_path)


def test_admin_enemy_detail_endpoint_returns_enemy(monkeypatch) -> None:
    from app.admin import api as admin_api
    from app.admin.repositories.enemy_config_repository import EnemyConfigRepository
    from app.admin.services.enemy_admin_service import EnemyAdminService

    client = _create_authorized_client()
    base_path = _make_test_base_path("admin-enemy-api-detail")
    EnemyConfigRepository(base_path=base_path).save(
        {
            "items": [
                {
                    "enemy_id": "enemy_bandit_qi_early",
                    "enemy_name": "山匪",
                    "enemy_realm_label": "炼气初期",
                    "enemy_hp": 36,
                    "enemy_attack": 8,
                    "enemy_defense": 4,
                    "enemy_speed": 6,
                    "allow_flee": True,
                    "rewards": {"resources": {"spirit_stone": 7}},
                }
            ]
        }
    )
    monkeypatch.setattr(
        admin_api,
        "enemy_admin_service",
        EnemyAdminService(base_path=base_path),
    )

    response = client.get("/admin/api/battle/enemies/enemy_bandit_qi_early")

    assert response.status_code == 200
    assert response.json()["enemy_name"] == "山匪"
    rmtree(base_path)


def test_admin_enemy_reload_endpoint_returns_count(monkeypatch) -> None:
    from app.admin import api as admin_api
    from app.admin.repositories.enemy_config_repository import EnemyConfigRepository
    from app.admin.services.enemy_admin_service import EnemyAdminService

    client = _create_authorized_client()
    base_path = _make_test_base_path("admin-enemy-api-reload")
    EnemyConfigRepository(base_path=base_path).save(
        {
            "items": [
                {
                    "enemy_id": "enemy_bandit_qi_early",
                    "enemy_name": "山匪",
                    "enemy_realm_label": "炼气初期",
                    "enemy_hp": 36,
                    "enemy_attack": 8,
                    "enemy_defense": 4,
                    "enemy_speed": 6,
                    "allow_flee": True,
                    "rewards": {"resources": {"spirit_stone": 7}},
                }
            ]
        }
    )
    monkeypatch.setattr(
        admin_api,
        "enemy_admin_service",
        EnemyAdminService(base_path=base_path, run_service=_ReloadRunService()),
    )

    response = client.post("/admin/api/battle/reload")

    assert response.status_code == 200
    assert response.json() == {"reloaded": True, "enemy_count": 1}
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
    def reload_enemy_config(self, enemy_config_base_path: str | None = None) -> None:
        self.enemy_config_base_path = enemy_config_base_path
