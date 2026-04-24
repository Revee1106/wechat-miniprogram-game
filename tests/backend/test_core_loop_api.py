from fastapi.testclient import TestClient

from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.api.core_loop import run_service
from app.core_loop.event_config import EventRegistry
from app.core_loop.services.combat_service import CombatService
from app.core_loop.types import (
    CurrentEvent,
    CurrentEventOption,
    EventOptionConfig,
    EventResultPayload,
    EventTemplateConfig,
    RunResourceStack,
)
from app.main import app


client = TestClient(app)


def setup_function() -> None:
    run_service.reset()


def test_create_run_and_advance_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]

    advance_response = client.post("/api/run/advance", json={"run_id": run_id})

    assert create_response.status_code == 200
    assert create_response.json()["character"]["lifespan_current"] == 720
    assert advance_response.status_code == 200
    assert advance_response.json()["character"]["lifespan_current"] == 719
    assert advance_response.json()["current_event"]["status"] == "pending"
    assert advance_response.json()["current_event"]["event_id"]
    assert advance_response.json()["current_event"]["options"][0]["option_id"]


def test_resolve_event_accepts_option_id_contract() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    advance_response = client.post("/api/run/advance", json={"run_id": run_id})
    option_id = advance_response.json()["current_event"]["options"][0]["option_id"]

    resolve_response = client.post(
        "/api/run/resolve",
        json={"run_id": run_id, "option_id": option_id},
    )

    assert resolve_response.status_code == 200
    assert resolve_response.json()["current_event"] is None
    assert resolve_response.json()["result_summary"]


def test_resolve_event_accepts_choice_key_field_with_option_id_value() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    advance_response = client.post("/api/run/advance", json={"run_id": run_id})
    option_id = advance_response.json()["current_event"]["options"][0]["option_id"]

    resolve_response = client.post(
        "/api/run/resolve",
        json={"run_id": run_id, "choice_key": option_id},
    )

    assert resolve_response.status_code == 200
    assert resolve_response.json()["current_event"] is None


def test_dead_character_cannot_advance_again() -> None:
    run_id = client.post("/api/run/create", json={"player_id": "p1"}).json()["run_id"]
    run = run_service.get_run(run_id)
    run.character.is_dead = True

    response = client.post("/api/run/advance", json={"run_id": run_id})

    assert response.status_code == 409


def test_advance_returns_structured_error_detail_when_spirit_stones_are_insufficient() -> None:
    run_id = client.post("/api/run/create", json={"player_id": "p1"}).json()["run_id"]
    run = run_service.get_run(run_id)
    run.resources.spirit_stone = 0

    response = client.post("/api/run/advance", json={"run_id": run_id})

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "core.time.not_enough_spirit_stones",
        "message": "not enough spirit stones to advance time",
        "params": {},
    }


def test_advance_can_apply_cultivation_penalty_when_spirit_stones_are_insufficient() -> None:
    run_id = client.post("/api/run/create", json={"player_id": "p1"}).json()["run_id"]
    run = run_service.get_run(run_id)
    run.resources.spirit_stone = 0
    run.character.cultivation_exp = 50

    response = client.post(
        "/api/run/advance",
        json={"run_id": run_id, "allow_cultivation_penalty": True},
    )

    assert response.status_code == 200
    assert response.json()["round_index"] == 1
    assert response.json()["resources"]["spirit_stone"] == 0
    assert response.json()["character"]["cultivation_exp"] < 50


def test_build_and_upgrade_dwelling_facility_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    run = run_service.get_run(run_id)
    run.resources.spirit_stone = 300

    build_response = client.post(
        "/api/run/dwelling/build",
        json={"run_id": run_id, "facility_id": "spirit_field"},
    )
    upgrade_response = client.post(
        "/api/run/dwelling/upgrade",
        json={"run_id": run_id, "facility_id": "spirit_field"},
    )

    assert build_response.status_code == 200
    assert (
        build_response.json()["dwelling_facilities"][0]["facility_id"] == "spirit_field"
    )
    assert build_response.json()["dwelling_facilities"][0]["level"] == 1
    assert upgrade_response.status_code == 200
    assert upgrade_response.json()["dwelling_facilities"][0]["level"] == 2


def test_start_and_consume_alchemy_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    run = run_service.get_run(run_id)
    run.resources.spirit_stone = 200
    run.resource_stacks.append(RunResourceStack(resource_key="basic_herb", amount=3))
    run_service.build_dwelling_facility(run_id, "alchemy_room")

    start_response = client.post(
        "/api/run/alchemy/start",
        json={"run_id": run_id, "recipe_id": "yang_qi_dan", "use_spirit_spring": False},
    )
    run_service.get_run(run_id).current_event = None
    run_service.advance_time(run_id)
    consume_response = client.post(
        "/api/run/alchemy/consume",
        json={"run_id": run_id, "item_id": "yang_qi_dan", "quality": "low"},
    )

    assert start_response.status_code == 200
    assert start_response.json()["alchemy_state"]["active_job"]["recipe_id"] == "yang_qi_dan"
    assert consume_response.status_code == 200
    assert consume_response.json()["character"]["cultivation_exp"] > 0


def test_sell_resource_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    run = run_service.get_run(run_id)
    run.resources.herbs = 4
    run.resources.spirit_stone = 20

    sell_response = client.post(
        "/api/run/resource/sell",
        json={"run_id": run_id, "resource_key": "herb", "amount": 3},
    )

    assert sell_response.status_code == 200
    assert sell_response.json()["resources"]["spirit_stone"] == 26
    assert sell_response.json()["resources"]["herbs"] == 1


def test_convert_spirit_stone_to_cultivation_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    run = run_service.get_run(run_id)
    run.resources.spirit_stone = 12
    run.character.cultivation_exp = 9

    convert_response = client.post(
        "/api/run/resource/convert-cultivation",
        json={"run_id": run_id, "amount": 4},
    )

    assert convert_response.status_code == 200
    assert convert_response.json()["resources"]["spirit_stone"] == 8
    assert convert_response.json()["character"]["cultivation_exp"] == 21


def test_battle_action_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]
    _attach_combat_registry()
    run_service._combat_service = CombatService()
    run = run_service.get_run(run_id)
    run.current_event = CurrentEvent(
        event_id="evt_bandit",
        event_name="山匪拦路",
        event_type="encounter",
        outcome_type="mixed",
        risk_level="risky",
        trigger_sources=[],
        choice_pattern="binary_choice",
        title_text="山匪拦路",
        body_text="前路有山匪盘踞。",
        region="mountain",
        status="pending",
        options=[
            CurrentEventOption(
                option_id="opt_fight",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
            )
        ],
    )

    resolve_response = client.post(
        "/api/run/resolve",
        json={"run_id": run_id, "option_id": "opt_fight"},
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["active_battle"] is not None

    battle_response = client.post(
        "/api/run/battle/action",
        json={"run_id": run_id, "action": "attack"},
    )

    assert battle_response.status_code == 200
    assert battle_response.json()["active_battle"] is None
    assert battle_response.json()["current_event"] is None
    assert battle_response.json()["resources"]["spirit_stone"] == 107
    assert battle_response.json()["character"]["cultivation_exp"] == 5


def test_battle_action_returns_conflict_without_active_battle() -> None:
    run_id = client.post("/api/run/create", json={"player_id": "p1"}).json()["run_id"]

    response = client.post(
        "/api/run/battle/action",
        json={"run_id": run_id, "action": "attack"},
    )

    assert response.status_code == 409


def test_advance_round_trip_uses_current_realm_base_gain_and_cost() -> None:
    from pathlib import Path
    from shutil import rmtree
    from uuid import uuid4

    base_path = Path.cwd() / ".pytest_tmp" / f"core-loop-api-advance-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0,
                    "required_cultivation_exp": 0,
                    "required_spirit_stone": 0,
                    "lifespan_bonus": 0,
                    "base_cultivation_gain_per_advance": 6,
                    "base_spirit_stone_cost_per_advance": 2,
                    "is_enabled": True,
                }
            ]
        }
    )

    try:
        run_service.reload_realm_config(realm_config_base_path=str(base_path))
        run_service.reset()

        create_response = client.post("/api/run/create", json={"player_id": "p1"})
        run_id = create_response.json()["run_id"]
        run = run_service.get_run(run_id)
        run.resources.spirit_stone = 10
        run.character.cultivation_exp = 3

        advance_response = client.post("/api/run/advance", json={"run_id": run_id})

        assert advance_response.status_code == 200
        assert advance_response.json()["resources"]["spirit_stone"] == 8
        assert advance_response.json()["character"]["cultivation_exp"] == 9
    finally:
        run_service.reload_realm_config(realm_config_base_path=str(Path.cwd()))
        run_service.reset()
        rmtree(base_path)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _attach_combat_registry() -> None:
    registry = EventRegistry(
        templates={
            "evt_bandit": EventTemplateConfig(
                event_id="evt_bandit",
                event_name="山匪拦路",
                event_type="encounter",
                outcome_type="mixed",
                risk_level="risky",
                trigger_sources=["global"],
                choice_pattern="binary_choice",
                title_text="山匪拦路",
                body_text="前路有山匪盘踞。",
                weight=1,
                is_repeatable=True,
                option_ids=["opt_fight"],
            )
        },
        options={
            "opt_fight": EventOptionConfig(
                option_id="opt_fight",
                event_id="evt_bandit",
                option_text="迎战山匪",
                sort_order=1,
                is_default=True,
                resolution_mode="combat",
                time_cost_months=2,
                result_on_success=EventResultPayload(
                    resources={"spirit_stone": 7},
                    character={"cultivation_exp": 5},
                    battle={
                        "enemy_name": "山匪",
                        "enemy_realm_label": "炼气初期",
                        "enemy_hp": 1,
                        "enemy_attack": 1,
                        "enemy_defense": 0,
                        "enemy_speed": 1,
                        "allow_flee": True,
                        "flee_base_rate": 0.35,
                        "pill_heal_amount": 12,
                        "victory_log": "victory log",
                        "defeat_log": "defeat log",
                        "flee_success_log": "脱身成功",
                        "flee_failure_log": "逃跑失败",
                    },
                ),
                result_on_failure=EventResultPayload(
                    resources={"spirit_stone": -3},
                    character={"lifespan_delta": -2},
                    battle={
                        "enemy_name": "山匪",
                        "enemy_realm_label": "炼气初期",
                        "enemy_hp": 1,
                        "enemy_attack": 1,
                        "enemy_defense": 0,
                        "enemy_speed": 1,
                        "allow_flee": True,
                        "flee_base_rate": 0.35,
                        "pill_heal_amount": 12,
                        "victory_log": "victory log",
                        "defeat_log": "defeat log",
                        "flee_success_log": "脱身成功",
                        "flee_failure_log": "逃跑失败",
                    },
                ),
            )
        },
    )
    run_service._event_registry = registry
    run_service._rebuild_runtime_services()
