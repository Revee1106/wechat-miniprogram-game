from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import BaseModel, model_validator

from app.core_loop.types import BreakthroughResult, RebirthResult, RunState


class CreateRunRequest(BaseModel):
    player_id: str


class RunIdRequest(BaseModel):
    run_id: str


class FacilityActionRequest(BaseModel):
    run_id: str
    facility_id: str


class ResourceSaleRequest(BaseModel):
    run_id: str
    resource_key: str
    amount: int


class StartAlchemyRequest(BaseModel):
    run_id: str
    recipe_id: str
    use_spirit_spring: bool = False


class ConsumeAlchemyItemRequest(BaseModel):
    run_id: str
    item_id: str
    quality: str | None = None


class ResolveEventRequest(BaseModel):
    run_id: str
    option_id: str | None = None
    choice_key: str | None = None

    @model_validator(mode="after")
    def validate_option_id(self) -> "ResolveEventRequest":
        if not self.option_id and not self.choice_key:
            raise ValueError("option_id is required")
        return self

    @property
    def resolved_option_id(self) -> str:
        return self.option_id or self.choice_key or ""


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def serialize_run_state(run: RunState) -> dict[str, Any]:
    return _serialize(run)


def serialize_breakthrough_result(result: BreakthroughResult) -> dict[str, Any]:
    return _serialize(result)


def serialize_rebirth_result(result: RebirthResult) -> dict[str, Any]:
    return _serialize(result)
