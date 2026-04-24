from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import BaseModel, model_validator

from app.core_loop.services.combat_stat_service import CombatStatService
from app.core_loop.types import BreakthroughResult, RebirthResult, RunState


class CreateRunRequest(BaseModel):
    player_id: str


class RunIdRequest(BaseModel):
    run_id: str


class AdvanceTimeRequest(BaseModel):
    run_id: str
    allow_cultivation_penalty: bool = False


class FacilityActionRequest(BaseModel):
    run_id: str
    facility_id: str


class ResourceSaleRequest(BaseModel):
    run_id: str
    resource_key: str
    amount: int


class ResourceConversionRequest(BaseModel):
    run_id: str
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


class BattleActionRequest(BaseModel):
    run_id: str
    action: str


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _apply_character_combat_stats(serialized_run: dict[str, Any], run: RunState) -> None:
    player_combat_state = CombatStatService().build_player_state(run)
    serialized_run["character"]["attack"] = player_combat_state.attack
    serialized_run["character"]["defense"] = player_combat_state.defense
    serialized_run["character"]["speed"] = player_combat_state.speed


def serialize_run_state(run: RunState) -> dict[str, Any]:
    serialized = _serialize(run)
    _apply_character_combat_stats(serialized, run)
    return serialized


def serialize_breakthrough_result(result: BreakthroughResult) -> dict[str, Any]:
    serialized = _serialize(result)
    run = RunState(
        run_id="",
        player_id="",
        round_index=0,
        character=result.character,
        resources=result.resources,
        breakthrough_requirements=result.breakthrough_requirements,
    )
    _apply_character_combat_stats({"character": serialized["character"]}, run)
    return serialized


def serialize_rebirth_result(result: RebirthResult) -> dict[str, Any]:
    return {
        "player_profile": _serialize(result.player_profile),
        "new_run": serialize_run_state(result.new_run),
    }
