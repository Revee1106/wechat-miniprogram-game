import os
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi.testclient import TestClient

from app.admin import api as admin_api
from app.admin.repositories.alchemy_config_repository import AlchemyConfigRepository
from app.admin.services.alchemy_admin_service import AlchemyAdminService
from app.main import app


def test_admin_alchemy_list_endpoints_return_levels_and_recipes(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("alchemy-api-list")
    AlchemyConfigRepository(base_path=base_path).save(_sample_alchemy_payload())
    monkeypatch.setattr(
        admin_api,
        "alchemy_admin_service",
        AlchemyAdminService(base_path=base_path),
    )

    levels_response = client.get("/admin/api/alchemy/levels")
    recipes_response = client.get("/admin/api/alchemy/recipes")

    assert levels_response.status_code == 200
    assert recipes_response.status_code == 200
    assert levels_response.json()["items"][0]["display_name"] == "初识丹道"
    assert recipes_response.json()["items"][0]["recipe_id"] == "yang_qi_dan"
    rmtree(base_path)


def test_admin_alchemy_recipe_crud_endpoint_persists_changes(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("alchemy-api-crud")
    AlchemyConfigRepository(base_path=base_path).save(_sample_alchemy_payload())
    monkeypatch.setattr(
        admin_api,
        "alchemy_admin_service",
        AlchemyAdminService(base_path=base_path),
    )

    create_response = client.post(
        "/admin/api/alchemy/recipes",
        json={
            "recipe_id": "ning_shen_dan",
            "display_name": "宁神丹",
            "category": "recovery",
            "description": "安定心神。",
            "required_alchemy_level": 1,
            "duration_months": 1,
            "base_success_rate": 0.7,
            "ingredients": {"basic_herb": 3},
            "effect_type": "status_penalty_reduce",
            "effect_value": 0.05,
            "effect_summary": "降低状态惩罚",
            "is_base_recipe": False,
        },
    )
    update_response = client.put(
        "/admin/api/alchemy/recipes/ning_shen_dan",
        json={
            "recipe_id": "ning_shen_dan",
            "display_name": "宁神丹·改",
            "category": "recovery",
            "description": "更安定心神。",
            "required_alchemy_level": 1,
            "duration_months": 2,
            "base_success_rate": 0.72,
            "ingredients": {"basic_herb": 4},
            "effect_type": "status_penalty_reduce",
            "effect_value": 0.08,
            "effect_summary": "显著降低状态惩罚",
            "is_base_recipe": False,
        },
    )
    delete_response = client.delete("/admin/api/alchemy/recipes/ning_shen_dan")

    assert create_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["duration_months"] == 2
    assert delete_response.status_code == 200
    assert all(
        recipe["recipe_id"] != "ning_shen_dan"
        for recipe in AlchemyConfigRepository(base_path=base_path).load()["recipes"]
    )
    rmtree(base_path)


def test_admin_alchemy_reload_endpoint_calls_run_service(monkeypatch) -> None:
    client = _create_authorized_client()
    base_path = _make_test_base_path("alchemy-api-reload")
    run_service = _ReloadRunService()
    AlchemyConfigRepository(base_path=base_path).save(_sample_alchemy_payload())
    monkeypatch.setattr(
        admin_api,
        "alchemy_admin_service",
        AlchemyAdminService(base_path=base_path, run_service=run_service),
    )

    response = client.post("/admin/api/alchemy/reload")

    assert response.status_code == 200
    assert response.json()["recipe_count"] == 2
    assert run_service.reloaded_base_path == str(base_path)
    rmtree(base_path)


def _sample_alchemy_payload() -> dict[str, list[dict[str, object]]]:
    return {
        "levels": [
            {"level": 0, "display_name": "初识丹道", "required_mastery_exp": 0},
            {"level": 1, "display_name": "初窥门径", "required_mastery_exp": 20},
        ],
        "recipes": [
            {
                "recipe_id": "yang_qi_dan",
                "display_name": "养气丹",
                "category": "cultivation",
                "description": "增加修为。",
                "required_alchemy_level": 0,
                "duration_months": 1,
                "base_success_rate": 0.86,
                "ingredients": {"basic_herb": 2},
                "effect_type": "cultivation_exp",
                "effect_value": 12,
                "effect_summary": "直接增加修为",
                "is_base_recipe": True,
            },
            {
                "recipe_id": "ju_ling_dan",
                "display_name": "聚灵丹",
                "category": "cultivation",
                "description": "中期修炼丹。",
                "required_alchemy_level": 1,
                "duration_months": 1,
                "base_success_rate": 0.64,
                "ingredients": {"basic_herb": 4, "spirit_stone": 2},
                "effect_type": "cultivation_exp",
                "effect_value": 24,
                "effect_summary": "较高幅度增加修为",
                "is_base_recipe": False,
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

    def reload_alchemy_config(self, alchemy_config_base_path: str | None = None) -> None:
        self.reloaded_base_path = alchemy_config_base_path
