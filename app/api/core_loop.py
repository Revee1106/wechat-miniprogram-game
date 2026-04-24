from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    AdvanceTimeRequest,
    BattleActionRequest,
    ResourceConversionRequest,
    ConsumeAlchemyItemRequest,
    CreateRunRequest,
    FacilityActionRequest,
    ResourceSaleRequest,
    ResolveEventRequest,
    RunIdRequest,
    StartAlchemyRequest,
    serialize_breakthrough_result,
    serialize_rebirth_result,
    serialize_run_state,
)
from app.core_loop.services.run_service import RunService
from app.core_loop.types import ConflictError, CoreLoopError, NotFoundError


router = APIRouter(tags=["core-loop"])
run_service = RunService()


def _build_error_detail(error: CoreLoopError) -> dict[str, object]:
    return {
        "code": error.code,
        "message": error.message,
        "params": error.params,
    }


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, NotFoundError):
        raise HTTPException(status_code=404, detail=_build_error_detail(error)) from error
    if isinstance(error, ConflictError):
        raise HTTPException(status_code=409, detail=_build_error_detail(error)) from error
    if isinstance(error, CoreLoopError):
        raise HTTPException(status_code=400, detail=_build_error_detail(error)) from error
    raise error


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/run/create")
def create_run(payload: CreateRunRequest) -> dict[str, object]:
    run = run_service.create_run(player_id=payload.player_id)
    return serialize_run_state(run)


@router.post("/run/state")
def get_run(payload: RunIdRequest) -> dict[str, object]:
    try:
        return serialize_run_state(run_service.get_run(payload.run_id))
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/advance")
def advance_time(payload: AdvanceTimeRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.advance_time(
                payload.run_id,
                allow_cultivation_penalty=payload.allow_cultivation_penalty,
            )
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/resolve")
def resolve_event(payload: ResolveEventRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.resolve_event(payload.run_id, payload.resolved_option_id)
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/battle/action")
def perform_battle_action(payload: BattleActionRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.perform_battle_action(payload.run_id, payload.action)
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/breakthrough")
def breakthrough(payload: RunIdRequest) -> dict[str, object]:
    try:
        return serialize_breakthrough_result(run_service.breakthrough(payload.run_id))
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/dwelling/build")
def build_dwelling_facility(payload: FacilityActionRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.build_dwelling_facility(payload.run_id, payload.facility_id)
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/dwelling/upgrade")
def upgrade_dwelling_facility(payload: FacilityActionRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.upgrade_dwelling_facility(payload.run_id, payload.facility_id)
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/resource/sell")
def sell_resource(payload: ResourceSaleRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.sell_resource(
                payload.run_id,
                payload.resource_key,
                payload.amount,
            )
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/resource/convert-cultivation")
def convert_spirit_stone_to_cultivation(
    payload: ResourceConversionRequest,
) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.convert_spirit_stone_to_cultivation(
                payload.run_id,
                payload.amount,
            )
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/alchemy/start")
def start_alchemy(payload: StartAlchemyRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.start_alchemy(
                payload.run_id,
                payload.recipe_id,
                use_spirit_spring=payload.use_spirit_spring,
            )
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/alchemy/consume")
def consume_alchemy_item(payload: ConsumeAlchemyItemRequest) -> dict[str, object]:
    try:
        return serialize_run_state(
            run_service.consume_alchemy_item(
                payload.run_id,
                payload.item_id,
                quality=payload.quality,
            )
        )
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise


@router.post("/run/rebirth")
def rebirth(payload: RunIdRequest) -> dict[str, object]:
    try:
        return serialize_rebirth_result(run_service.rebirth(payload.run_id))
    except Exception as error:  # pragma: no cover - centralized mapping
        _raise_http_error(error)
        raise
