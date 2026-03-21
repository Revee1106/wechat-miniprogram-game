from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import BaseModel

from app.core_loop.types import BreakthroughResult, RebirthResult, RunState


class CreateRunRequest(BaseModel):
    player_id: str


class RunIdRequest(BaseModel):
    run_id: str


class ResolveEventRequest(BaseModel):
    run_id: str
    choice_key: str


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
