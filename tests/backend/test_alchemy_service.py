import pytest

from app.admin.repositories.alchemy_config_repository import AlchemyConfigRepository
from app.core_loop.services.run_service import RunService
from app.core_loop.types import AlchemyInventoryItem, ConflictError, RunResourceStack


def test_alchemy_requires_built_alchemy_room() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")

    with pytest.raises(ConflictError):
        service.start_alchemy(run.run_id, "yang_qi_dan")


def test_alchemy_room_has_no_upgrade_level_gate() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200

    built = service.build_dwelling_facility(run.run_id, "alchemy_room")
    alchemy_room = next(
        facility for facility in built.dwelling_facilities if facility.facility_id == "alchemy_room"
    )

    assert alchemy_room.level == 1
    assert alchemy_room.status == "max_level"
    with pytest.raises(ConflictError):
        service.upgrade_dwelling_facility(run.run_id, "alchemy_room")


def test_start_alchemy_spends_materials_and_creates_job() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    run.resource_stacks.append(RunResourceStack(resource_key="basic_herb", amount=3))
    service.build_dwelling_facility(run.run_id, "alchemy_room")

    updated = service.start_alchemy(run.run_id, "yang_qi_dan")

    assert any(
        stack.resource_key == "basic_herb" and stack.amount == 1
        for stack in updated.resource_stacks
    )
    assert updated.alchemy_state.active_job is not None
    assert updated.alchemy_state.active_job.recipe_id == "yang_qi_dan"
    assert updated.alchemy_state.active_job.remaining_months == 1


def test_advance_time_completes_alchemy_job_and_adds_inventory_and_mastery() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    run.resource_stacks.append(RunResourceStack(resource_key="basic_herb", amount=3))
    service.build_dwelling_facility(run.run_id, "alchemy_room")
    expected_success_mastery_gain = run.alchemy_state.available_recipes[0].success_mastery_exp_gain
    service.start_alchemy(run.run_id, "yang_qi_dan")

    advanced = service.advance_time(run.run_id)

    assert advanced.alchemy_state.active_job is None
    assert advanced.alchemy_state.last_result is not None
    assert advanced.alchemy_state.last_result.recipe_id == "yang_qi_dan"
    assert advanced.alchemy_state.last_result.outcome in {"success", "waste"}
    assert advanced.alchemy_state.mastery_exp > 0
    if advanced.alchemy_state.last_result.outcome == "success":
        assert advanced.alchemy_state.last_result.mastery_exp_gained == expected_success_mastery_gain
        assert advanced.alchemy_state.mastery_exp == expected_success_mastery_gain
        assert advanced.alchemy_state.inventory[0].item_id == "yang_qi_dan"


def test_basic_alchemy_recipes_stay_first_after_early_mastery_gain() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    run.alchemy_state.mastery_exp = 38
    service.build_dwelling_facility(run.run_id, "alchemy_room")

    updated = service.get_run(run.run_id)

    recipe_ids = [recipe.recipe_id for recipe in updated.alchemy_state.available_recipes]
    assert recipe_ids == ["yang_qi_dan", "yang_yuan_dan"]
    assert "bi_gu_dan" not in recipe_ids


def test_non_basic_alchemy_recipes_require_learning_source() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    run.alchemy_state.mastery_exp = 60
    service.build_dwelling_facility(run.run_id, "alchemy_room")

    updated = service.get_run(run.run_id)
    recipe_ids = [recipe.recipe_id for recipe in updated.alchemy_state.available_recipes]
    assert recipe_ids == ["yang_qi_dan", "yang_yuan_dan"]

    run.alchemy_state.learned_recipe_ids.append("ju_ling_dan")
    updated = service.get_run(run.run_id)

    recipe_ids = [recipe.recipe_id for recipe in updated.alchemy_state.available_recipes]
    assert recipe_ids == ["yang_qi_dan", "yang_yuan_dan", "ju_ling_dan"]


def test_cannot_start_unlearned_non_basic_alchemy_recipe() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    run.resource_stacks.append(RunResourceStack(resource_key="basic_herb", amount=10))
    run.alchemy_state.mastery_exp = 60
    service.build_dwelling_facility(run.run_id, "alchemy_room")

    with pytest.raises(ConflictError, match="尚未习得"):
        service.start_alchemy(run.run_id, "ju_ling_dan")


def test_recipe_success_rate_uses_configured_per_level_rate(tmp_path) -> None:
    AlchemyConfigRepository(base_path=tmp_path).save(
        {
            "levels": [
                {"level": 0, "display_name": "初识丹道", "required_mastery_exp": 0},
                {"level": 1, "display_name": "初窥门径", "required_mastery_exp": 20},
                {"level": 2, "display_name": "熟手", "required_mastery_exp": 60},
            ],
            "recipes": [
                {
                    "recipe_id": "test_dan",
                    "display_name": "测试丹",
                    "category": "cultivation",
                    "description": "测试每级成丹率配置。",
                    "required_alchemy_level": 0,
                    "duration_months": 1,
                    "base_success_rate": 0.5,
                    "per_level_success_rate": 0.2,
                    "success_mastery_exp_gain": 10,
                    "ingredients": {"basic_herb": 1},
                    "effect_type": "cultivation_exp",
                    "effect_value": 1,
                    "effect_summary": "测试效果",
                    "is_base_recipe": True,
                },
            ],
        }
    )
    service = RunService(alchemy_config_base_path=str(tmp_path))
    run = service.create_run(player_id="p1")
    run.alchemy_state.mastery_exp = 60

    updated = service.get_run(run.run_id)
    recipe = updated.alchemy_state.available_recipes[0]

    assert recipe.per_level_success_rate == 0.2
    assert recipe.current_success_rate == 0.9


def test_consume_pill_applies_effect_and_reduces_inventory() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 200
    run.resource_stacks.append(RunResourceStack(resource_key="basic_herb", amount=3))
    service.build_dwelling_facility(run.run_id, "alchemy_room")
    service.start_alchemy(run.run_id, "yang_qi_dan")
    updated = service.advance_time(run.run_id)

    assert updated.alchemy_state.last_result is not None
    assert updated.alchemy_state.last_result.outcome == "success"
    updated.character.cultivation_exp = 0

    updated = service.consume_alchemy_item(
        run.run_id,
        "yang_qi_dan",
        updated.alchemy_state.last_result.quality,
    )

    assert updated.character.cultivation_exp > 0
    assert updated.alchemy_state.inventory == []


def test_consume_supreme_quality_pill_uses_configured_effect_multiplier() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.character.cultivation_exp = 0
    run.alchemy_state.inventory = [
        AlchemyInventoryItem(
            item_id="yang_qi_dan",
            display_name="养气丹",
            quality="supreme",
            amount=1,
            effect_summary="直接增加修为",
        )
    ]

    updated = service.consume_alchemy_item(run.run_id, "yang_qi_dan", "supreme")

    assert updated.character.cultivation_exp == 24
    assert updated.result_summary == "已服用 养气丹（极品）。"
