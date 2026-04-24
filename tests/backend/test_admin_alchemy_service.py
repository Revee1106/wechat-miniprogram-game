from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.alchemy_config_repository import AlchemyConfigRepository
from app.admin.services.alchemy_admin_service import AlchemyAdminService
from app.core_loop.services.run_service import RunService


def test_service_lists_levels_and_recipes() -> None:
    base_path = _make_test_base_path("alchemy-service-list")
    AlchemyConfigRepository(base_path=base_path).save(_sample_alchemy_payload())

    service = AlchemyAdminService(base_path=base_path)

    assert [item["level"] for item in service.list_levels()["items"]] == [0, 1]
    assert [item["recipe_id"] for item in service.list_recipes()["items"]] == [
        "yang_qi_dan",
        "ju_ling_dan",
    ]
    rmtree(base_path)


def test_service_updates_levels_and_recipe_crud() -> None:
    base_path = _make_test_base_path("alchemy-service-crud")
    AlchemyConfigRepository(base_path=base_path).save(_sample_alchemy_payload())
    service = AlchemyAdminService(base_path=base_path)

    updated_levels = service.update_levels(
        [
            {"level": 0, "display_name": "丹道启蒙", "required_mastery_exp": 0},
            {"level": 1, "display_name": "丹道入门", "required_mastery_exp": 18},
            {"level": 2, "display_name": "丹道精研", "required_mastery_exp": 60},
        ]
    )
    created = service.create_recipe(
        {
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
        }
    )
    updated = service.update_recipe(
        "ning_shen_dan",
        {
            "recipe_id": "ning_shen_dan",
            "display_name": "宁神丹·改",
            "category": "recovery",
            "description": "更安定心神。",
            "required_alchemy_level": 2,
            "duration_months": 2,
            "base_success_rate": 0.72,
            "ingredients": {"basic_herb": 4, "spirit_stone": 1},
            "effect_type": "status_penalty_reduce",
            "effect_value": 0.08,
            "effect_summary": "显著降低状态惩罚",
            "is_base_recipe": False,
        },
    )
    service.delete_recipe("ning_shen_dan")

    assert [item["level"] for item in updated_levels["items"]] == [0, 1, 2]
    assert created["recipe_id"] == "ning_shen_dan"
    assert updated["display_name"] == "宁神丹·改"
    assert service.list_recipes()["items"][0]["recipe_id"] == "yang_qi_dan"
    rmtree(base_path)


def test_service_reloads_runtime_config() -> None:
    base_path = _make_test_base_path("alchemy-service-reload")
    AlchemyConfigRepository(base_path=base_path).save(
        {
            "levels": [
                {"level": 0, "display_name": "丹道启蒙", "required_mastery_exp": 0},
                {"level": 1, "display_name": "丹道入门", "required_mastery_exp": 10},
            ],
            "recipes": [
                {
                    "recipe_id": "custom_dan",
                    "display_name": "自定义丹",
                    "category": "cultivation",
                    "description": "测试丹方。",
                    "required_alchemy_level": 0,
                    "duration_months": 1,
                    "base_success_rate": 0.9,
                    "ingredients": {"basic_herb": 1},
                    "effect_type": "cultivation_exp",
                    "effect_value": 5,
                    "effect_summary": "增加修为",
                    "is_base_recipe": True,
                }
            ],
        }
    )
    run_service = RunService()
    service = AlchemyAdminService(base_path=base_path, run_service=run_service)

    result = service.reload_runtime_config()
    run = run_service.create_run(player_id="alchemy")

    assert result == {"reloaded": True, "level_count": 2, "recipe_count": 1}
    assert run.alchemy_state.mastery_title == "丹道启蒙"
    assert [recipe.recipe_id for recipe in run.alchemy_state.available_recipes] == ["custom_dan"]
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
