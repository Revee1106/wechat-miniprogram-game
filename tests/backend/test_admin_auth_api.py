from fastapi.testclient import TestClient

from app.main import app


def test_admin_api_requires_login(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "secret-password")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "secret-signing-key")
    client = TestClient(app)

    response = client.get("/admin/api/events")

    assert response.status_code == 401


def test_admin_login_sets_cookie_and_allows_access(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "secret-password")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "secret-signing-key")
    client = TestClient(app)

    login_response = client.post(
        "/admin/api/auth/login",
        json={"username": "admin", "password": "secret-password"},
    )
    events_response = client.get("/admin/api/events")

    assert login_response.status_code == 200
    assert "admin_session" in client.cookies
    assert events_response.status_code == 200


def test_admin_logout_clears_cookie_and_blocks_follow_up_requests(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "secret-password")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "secret-signing-key")
    client = TestClient(app)
    client.post(
        "/admin/api/auth/login",
        json={"username": "admin", "password": "secret-password"},
    )

    logout_response = client.post("/admin/api/auth/logout")
    events_response = client.get("/admin/api/events")

    assert logout_response.status_code == 200
    assert events_response.status_code == 401


def test_admin_page_redirects_to_login_when_unauthenticated(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "secret-password")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "secret-signing-key")
    client = TestClient(app)

    response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/admin/login"
