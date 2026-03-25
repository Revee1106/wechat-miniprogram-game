from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from time import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse


SESSION_COOKIE_NAME = "admin_session"
SESSION_TTL_SECONDS = 60 * 60 * 8


class AdminAuthError(Exception):
    def __init__(self, detail: str, status_code: int = 401) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class AdminSession:
    username: str


def install_admin_auth(app: FastAPI) -> None:
    @app.middleware("http")
    async def admin_auth_middleware(request: Request, call_next):
        path = request.url.path
        if not _is_admin_path(path) or _is_exempt_admin_path(path):
            return await call_next(request)

        try:
            get_admin_session(request)
        except AdminAuthError as error:
            if path.startswith("/admin/api/"):
                return JSONResponse(
                    status_code=error.status_code,
                    content={"detail": error.detail},
                )
            if error.status_code == 503:
                return PlainTextResponse(error.detail, status_code=503)
            return RedirectResponse(url="/admin/login")

        return await call_next(request)


def authenticate_admin(username: str, password: str) -> AdminSession:
    config = _get_admin_auth_config()
    if not config.password:
        raise AdminAuthError("admin auth is not configured", status_code=503)
    if username != config.username or password != config.password:
        raise AdminAuthError("invalid admin credentials", status_code=401)
    return AdminSession(username=config.username)


def get_admin_session(request: Request) -> AdminSession:
    config = _get_admin_auth_config()
    if not config.password:
        raise AdminAuthError("admin auth is not configured", status_code=503)

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise AdminAuthError("admin login required", status_code=401)

    try:
        username, expires_at_raw, signature = token.split(":", 2)
        expires_at = int(expires_at_raw)
    except ValueError as error:
        raise AdminAuthError("invalid admin session", status_code=401) from error

    expected_signature = _sign_session(username, expires_at, config.secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise AdminAuthError("invalid admin session", status_code=401)
    if expires_at <= int(time()):
        raise AdminAuthError("admin session expired", status_code=401)
    if username != config.username:
        raise AdminAuthError("invalid admin session", status_code=401)

    return AdminSession(username=username)


def set_admin_session(response: Response, session: AdminSession) -> None:
    config = _get_admin_auth_config()
    expires_at = int(time()) + SESSION_TTL_SECONDS
    signature = _sign_session(session.username, expires_at, config.secret)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=f"{session.username}:{expires_at}:{signature}",
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        samesite="lax",
    )


def clear_admin_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME)


@dataclass(frozen=True)
class _AdminAuthConfig:
    username: str
    password: str | None
    secret: str


def _get_admin_auth_config() -> _AdminAuthConfig:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")
    secret = os.getenv("ADMIN_SESSION_SECRET") or password or "admin-dev-secret"
    return _AdminAuthConfig(username=username, password=password, secret=secret)


def _sign_session(username: str, expires_at: int, secret: str) -> str:
    message = f"{username}:{expires_at}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _is_admin_path(path: str) -> bool:
    return path == "/admin" or path.startswith("/admin/")


def _is_exempt_admin_path(path: str) -> bool:
    return (
        path.startswith("/admin/api/auth/")
        or path == "/admin/login"
        or path.startswith("/admin/assets/")
    )
