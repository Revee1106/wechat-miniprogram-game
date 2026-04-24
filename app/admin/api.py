from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.admin.auth import (
    AdminAuthError,
    authenticate_admin,
    clear_admin_session,
    get_admin_session,
    set_admin_session,
)
from app.admin.schemas import AdminLoginRequest, AdminSessionResponse
from app.admin.services.alchemy_admin_service import AlchemyAdminService
from app.admin.services.dwelling_admin_service import DwellingAdminService
from app.admin.services.enemy_admin_service import EnemyAdminService
from app.admin.services.event_admin_service import EventAdminService
from app.admin.services.realm_admin_service import RealmAdminService
from app.core_loop.types import NotFoundError


router = APIRouter(prefix="/admin/api", tags=["admin"])
event_admin_service = EventAdminService()
realm_admin_service = RealmAdminService()
dwelling_admin_service = DwellingAdminService()
enemy_admin_service = EnemyAdminService()
alchemy_admin_service = AlchemyAdminService()


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, AdminAuthError):
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    if isinstance(error, NotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, ValueError):
        raise HTTPException(status_code=400, detail=str(error)) from error
    raise error


@router.post("/auth/login")
def login(payload: AdminLoginRequest, response: Response) -> dict[str, object]:
    try:
        session = authenticate_admin(payload.username, payload.password)
        set_admin_session(response, session)
        return AdminSessionResponse(username=session.username).model_dump()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/auth/logout")
def logout(response: Response) -> dict[str, bool]:
    clear_admin_session(response)
    return {"authenticated": False}


@router.get("/auth/session")
def session(request: Request) -> dict[str, object]:
    try:
        current_session = get_admin_session(request)
        return AdminSessionResponse(username=current_session.username).model_dump()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.get("/events")
def list_events(
    event_type: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
) -> dict[str, object]:
    return event_admin_service.list_events(
        event_type=event_type,
        risk_level=risk_level,
        keyword=keyword,
    )


@router.get("/battle/enemies")
def list_enemies() -> dict[str, object]:
    return enemy_admin_service.list_enemies()


@router.get("/alchemy/recipes")
def list_alchemy_recipes() -> dict[str, object]:
    return alchemy_admin_service.list_recipes()


@router.get("/alchemy/recipes/{recipe_id}")
def get_alchemy_recipe(recipe_id: str) -> dict[str, object]:
    try:
        return alchemy_admin_service.get_recipe(recipe_id)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/alchemy/recipes")
def create_alchemy_recipe(payload: dict[str, object]) -> dict[str, object]:
    try:
        return alchemy_admin_service.create_recipe(payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.put("/alchemy/recipes/{recipe_id}")
def update_alchemy_recipe(recipe_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return alchemy_admin_service.update_recipe(recipe_id, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.delete("/alchemy/recipes/{recipe_id}")
def delete_alchemy_recipe(recipe_id: str) -> dict[str, object]:
    try:
        alchemy_admin_service.delete_recipe(recipe_id)
        return {"deleted": True}
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.get("/alchemy/levels")
def list_alchemy_levels() -> dict[str, object]:
    return alchemy_admin_service.list_levels()


@router.put("/alchemy/levels")
def update_alchemy_levels(payload: dict[str, object]) -> dict[str, object]:
    try:
        return alchemy_admin_service.update_levels(list(payload.get("items", [])))
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/alchemy/validate")
def validate_alchemy() -> dict[str, object]:
    result = alchemy_admin_service.validate_current_config()
    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/alchemy/reload")
def reload_alchemy() -> dict[str, object]:
    try:
        return alchemy_admin_service.reload_runtime_config()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.get("/battle/enemies/{enemy_id}")
def get_enemy(enemy_id: str) -> dict[str, object]:
    try:
        return enemy_admin_service.get_enemy(enemy_id)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/battle/enemies")
def create_enemy(payload: dict[str, object]) -> dict[str, object]:
    try:
        return enemy_admin_service.create_enemy(payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.put("/battle/enemies/{enemy_id}")
def update_enemy(enemy_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return enemy_admin_service.update_enemy(enemy_id, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.delete("/battle/enemies/{enemy_id}")
def delete_enemy(enemy_id: str) -> dict[str, object]:
    try:
        enemy_admin_service.delete_enemy(enemy_id)
        return {"deleted": True}
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/battle/validate")
def validate_enemies() -> dict[str, object]:
    result = enemy_admin_service.validate_current_config()
    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/battle/reload")
def reload_enemies() -> dict[str, object]:
    try:
        return enemy_admin_service.reload_runtime_config()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.get("/events/{event_id}")
def get_event(event_id: str) -> dict[str, object]:
    try:
        return event_admin_service.get_event(event_id)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/events")
def create_event(payload: dict[str, object]) -> dict[str, object]:
    try:
        return event_admin_service.create_event(payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.put("/events/{event_id}")
def update_event(event_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return event_admin_service.update_event(event_id, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.delete("/events/{event_id}")
def delete_event(event_id: str) -> dict[str, object]:
    try:
        event_admin_service.delete_event(event_id)
        return {"deleted": True}
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/events/{event_id}/options")
def create_option(event_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return event_admin_service.create_option(event_id, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.put("/options/{option_id}")
def update_option(option_id: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return event_admin_service.update_option(option_id, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.delete("/options/{option_id}")
def delete_option(option_id: str) -> dict[str, object]:
    try:
        event_admin_service.delete_option(option_id)
        return {"deleted": True}
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/events/validate")
def validate_events() -> dict[str, object]:
    result = event_admin_service.validate_current_config()
    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/events/reload")
def reload_events() -> dict[str, object]:
    try:
        return event_admin_service.reload_runtime_config()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.get("/realms")
def list_realms() -> dict[str, object]:
    return realm_admin_service.list_realms()


@router.get("/dwelling/facilities")
def list_dwelling_facilities() -> dict[str, object]:
    return dwelling_admin_service.list_facilities()


@router.get("/dwelling/facilities/{facility_id}")
def get_dwelling_facility(facility_id: str) -> dict[str, object]:
    try:
        return dwelling_admin_service.get_facility(facility_id)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.put("/dwelling/facilities/{facility_id}")
def update_dwelling_facility(
    facility_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    try:
        return dwelling_admin_service.update_facility(facility_id, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/dwelling/validate")
def validate_dwelling() -> dict[str, object]:
    result = dwelling_admin_service.validate_current_config()
    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/dwelling/reload")
def reload_dwelling() -> dict[str, object]:
    try:
        return dwelling_admin_service.reload_runtime_config()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/realms/validate")
def validate_realms() -> dict[str, object]:
    result = realm_admin_service.validate_current_config()
    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/realms/reload")
def reload_realms() -> dict[str, object]:
    try:
        return realm_admin_service.reload_runtime_config()
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/realms/reorder")
def reorder_realms(payload: dict[str, object]) -> dict[str, object]:
    try:
        keys = payload.get("keys")
        if not isinstance(keys, list):
            raise ValueError("realm reorder keys are required")
        return realm_admin_service.reorder_realms([str(key) for key in keys])
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.get("/realms/{realm_key}")
def get_realm(realm_key: str) -> dict[str, object]:
    try:
        return realm_admin_service.get_realm(realm_key)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/realms")
def create_realm(payload: dict[str, object]) -> dict[str, object]:
    try:
        return realm_admin_service.create_realm(payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.put("/realms/{realm_key}")
def update_realm(realm_key: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        return realm_admin_service.update_realm(realm_key, payload)
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.delete("/realms/{realm_key}")
def delete_realm(realm_key: str) -> dict[str, object]:
    try:
        realm_admin_service.delete_realm(realm_key)
        return {"deleted": True}
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise
