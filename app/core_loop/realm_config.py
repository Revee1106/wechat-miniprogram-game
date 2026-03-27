from __future__ import annotations

from pathlib import Path
from typing import Literal, Sequence

from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.core_loop.types import RealmConfig


def load_realm_configs(base_path: Path | str | None = None) -> list[RealmConfig]:
    payload = RealmConfigRepository(base_path=base_path).load()
    realms = sorted(
        payload.get("realms", []),
        key=lambda realm: _coerce_int(realm.get("order_index", 0)),
    )
    return [
        RealmConfig(
            key=str(realm.get("key", "")),
            display_name=str(realm.get("display_name", "")),
            major_realm=str(realm.get("major_realm", "")),
            stage_index=_coerce_int(realm.get("stage_index", 0)),
            order_index=_coerce_int(realm.get("order_index", 0)),
            lifespan_bonus=_coerce_int(realm.get("lifespan_bonus", 0)),
            base_success_rate=_coerce_float(realm.get("base_success_rate", 0)),
            required_exp=_coerce_int(realm.get("required_cultivation_exp", 0)),
            required_spirit_stone=_coerce_int(realm.get("required_spirit_stone", 0)),
            required_materials={
                str(key): _coerce_int(value)
                for key, value in dict(realm.get("required_materials", {})).items()
            },
            is_enabled=_coerce_bool(realm.get("is_enabled", True)),
        )
        for realm in realms
        if _coerce_bool(realm.get("is_enabled", True)) and str(realm.get("key", ""))
    ]


def resolve_realm_key(
    realm_key: str,
    realm_configs: Sequence[RealmConfig],
    *,
    boundary: Literal["current", "min", "max"] = "current",
) -> str:
    exact_match = next((config.key for config in realm_configs if config.key == realm_key), None)
    if exact_match is not None:
        return exact_match

    matching_keys = [
        config.key for config in realm_configs if config.major_realm == realm_key
    ]
    if not matching_keys:
        return realm_key

    if boundary == "max":
        return matching_keys[-1]
    return matching_keys[0]


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean value is not a valid integer")
    return int(value)


def _coerce_float(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean value is not a valid float")
    return float(value)


def _coerce_bool(value: object) -> bool:
    return value is True
