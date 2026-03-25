from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse, Response


ADMIN_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "admin-console" / "dist"


def create_admin_frontend_router(dist_path: Path | None = None) -> APIRouter:
    router = APIRouter()
    build_dir = (dist_path or ADMIN_FRONTEND_DIST).resolve()

    @router.get("/admin", include_in_schema=False)
    def admin_index() -> Response:
        return _serve_admin_path(build_dir, "")

    @router.get("/admin/{full_path:path}", include_in_schema=False)
    def admin_asset(full_path: str) -> Response:
        if full_path.startswith("api/"):
            return PlainTextResponse("Not Found", status_code=404)
        return _serve_admin_path(build_dir, full_path)

    return router


def _serve_admin_path(build_dir: Path, full_path: str) -> Response:
    if not build_dir.exists():
        return PlainTextResponse("Admin console build not found.", status_code=503)

    requested_path = full_path.strip("/")
    if requested_path:
        candidate = (build_dir / requested_path).resolve()
        if _is_within_build_dir(build_dir, candidate) and candidate.is_file():
            return FileResponse(candidate)

    index_path = build_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return PlainTextResponse("Admin console build not found.", status_code=503)


def _is_within_build_dir(build_dir: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(build_dir)
    except ValueError:
        return False
    return True
