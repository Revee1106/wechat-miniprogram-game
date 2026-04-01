from fastapi.testclient import TestClient

from app.api.core_loop import run_service
from app.main import app


client = TestClient(app)


def setup_function() -> None:
    run_service.reset()


def test_create_run_and_advance_round_trip() -> None:
    create_response = client.post("/api/run/create", json={"player_id": "p1"})
    run_id = create_response.json()["run_id"]

    advance_response = client.post("/api/run/advance", json={"run_id": run_id})

    assert create_response.status_code == 200
    assert create_response.json()["character"]["lifespan_current"] == 240
    assert advance_response.status_code == 200
    assert advance_response.json()["character"]["lifespan_current"] == 239
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
    assert convert_response.json()["character"]["cultivation_exp"] == 29


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
