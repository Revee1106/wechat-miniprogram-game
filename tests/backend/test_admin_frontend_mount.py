from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.admin.api import router as admin_api_router
from app.admin.auth import install_admin_auth
from app.admin.static import create_admin_frontend_router


def test_admin_frontend_is_served(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "test-secret")
    base_path = Path.cwd() / ".pytest_tmp" / f"admin-frontend-{uuid4().hex}"
    dist_path = base_path / "admin-console" / "dist"
    assets_path = dist_path / "assets"
    assets_path.mkdir(parents=True, exist_ok=True)
    (dist_path / "index.html").write_text("<html><body>Admin Console</body></html>", encoding="utf-8")
    (assets_path / "app.js").write_text("console.log('admin');", encoding="utf-8")

    app = FastAPI()
    install_admin_auth(app)
    app.include_router(admin_api_router)
    app.include_router(create_admin_frontend_router(dist_path))
    client = TestClient(app)

    redirect_response = client.get("/admin", follow_redirects=False)
    login_response = client.get("/admin/login")
    client.post(
        "/admin/api/auth/login",
        json={"username": "admin", "password": "test-password"},
    )
    response = client.get("/admin")
    asset_response = client.get("/admin/assets/app.js")
    api_response = client.get("/admin/api/events")

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "/admin/login"
    assert login_response.status_code == 200
    assert response.status_code == 200
    assert "Admin Console" in response.text
    assert asset_response.status_code == 200
    assert "console.log" in asset_response.text
    assert api_response.status_code == 200
    rmtree(base_path)
