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


def test_dead_character_cannot_advance_again() -> None:
    run_id = client.post("/api/run/create", json={"player_id": "p1"}).json()["run_id"]
    run = run_service.get_run(run_id)
    run.character.is_dead = True

    response = client.post("/api/run/advance", json={"run_id": run_id})

    assert response.status_code == 409


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
