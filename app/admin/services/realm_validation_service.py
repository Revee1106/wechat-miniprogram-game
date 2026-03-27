from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


def validate_realm_config(*, realms: list[dict[str, object]]) -> ConfigValidationResult:
    errors: list[str] = []

    keys = [str(realm.get("key", "")) for realm in realms]
    order_indices = [str(realm.get("order_index", "")) for realm in realms]
    errors.extend(_find_duplicates(keys, "realm key"))
    errors.extend(_find_duplicates(order_indices, "order_index"))

    for realm in realms:
        key = str(realm.get("key", ""))
        if not key:
            errors.append("realm missing key")
            continue

        display_name = str(realm.get("display_name", ""))
        major_realm = str(realm.get("major_realm", ""))
        stage_index, stage_index_valid = _coerce_int(realm.get("stage_index"))
        base_success_rate, base_success_rate_valid = _coerce_float(
            realm.get("base_success_rate")
        )
        required_cultivation_exp, cultivation_exp_valid = _coerce_int(
            realm.get("required_cultivation_exp")
        )
        required_spirit_stone, spirit_stone_valid = _coerce_int(
            realm.get("required_spirit_stone")
        )
        lifespan_bonus, lifespan_bonus_valid = _coerce_int(realm.get("lifespan_bonus"))

        if not display_name.strip():
            errors.append(f"realm '{key}' has empty display_name")
        if not major_realm.strip():
            errors.append(f"realm '{key}' has empty major_realm")
        if not stage_index_valid or stage_index < 1:
            errors.append(f"realm '{key}' has invalid stage_index")
        if not base_success_rate_valid or not 0 <= base_success_rate <= 1:
            errors.append(f"realm '{key}' has invalid base_success_rate")
        if not cultivation_exp_valid or required_cultivation_exp < 0:
            errors.append(f"realm '{key}' has invalid required_cultivation_exp")
        if not spirit_stone_valid or required_spirit_stone < 0:
            errors.append(f"realm '{key}' has invalid required_spirit_stone")
        if not lifespan_bonus_valid or lifespan_bonus < 0:
            errors.append(f"realm '{key}' has invalid lifespan_bonus")

    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])


def _coerce_int(value: object) -> tuple[int, bool]:
    if isinstance(value, bool):
        return 0, False
    try:
        return int(value), True
    except (TypeError, ValueError):
        return 0, False


def _coerce_float(value: object) -> tuple[float, bool]:
    if isinstance(value, bool):
        return 0.0, False
    try:
        return float(value), True
    except (TypeError, ValueError):
        return 0.0, False


def _find_duplicates(values: list[str], label: str) -> list[str]:
    duplicates: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            duplicates.append(f"duplicate {label}: {value}")
            continue
        seen.add(value)
    return duplicates
