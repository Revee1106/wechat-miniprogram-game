from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


_REWARD_CHARACTER_INT_FIELDS = {
    "cultivation_exp",
    "lifespan_delta",
    "hp_delta",
    "breakthrough_bonus",
    "technique_exp",
    "luck_delta",
    "karma_delta",
}
_REWARD_LIST_FIELDS = {
    "statuses_add",
    "statuses_remove",
    "techniques_add",
    "equipment_add",
    "equipment_remove",
}


def validate_enemy_config(*, enemies: list[dict[str, object]]) -> ConfigValidationResult:
    errors: list[str] = []

    enemy_ids = [str(enemy.get("enemy_id", "")).strip() for enemy in enemies]
    errors.extend(_find_duplicates(enemy_ids, "enemy_id"))

    for enemy in enemies:
        enemy_id = str(enemy.get("enemy_id", "")).strip()
        enemy_name = str(enemy.get("enemy_name", "")).strip()
        enemy_realm_label = str(enemy.get("enemy_realm_label", "")).strip()

        if not enemy_id:
            errors.append("enemy missing enemy_id")
            continue
        if not enemy_name:
            errors.append(f"enemy '{enemy_id}' has empty enemy_name")
        if not enemy_realm_label:
            errors.append(f"enemy '{enemy_id}' has empty enemy_realm_label")

        hp = _coerce_int(enemy.get("enemy_hp"))
        if hp < 1:
            errors.append(f"enemy '{enemy_id}' has invalid enemy_hp")
        for field_name in ("enemy_attack", "enemy_defense", "enemy_speed"):
            value = _coerce_int(enemy.get(field_name))
            if value < 0:
                errors.append(f"enemy '{enemy_id}' has invalid {field_name}")

        allow_flee = enemy.get("allow_flee")
        if not isinstance(allow_flee, bool):
            errors.append(f"enemy '{enemy_id}' has invalid allow_flee")

        rewards = enemy.get("rewards", {})
        errors.extend(_validate_rewards(enemy_id=enemy_id, rewards=rewards))

    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])


def _validate_rewards(*, enemy_id: str, rewards: object) -> list[str]:
    errors: list[str] = []

    if not isinstance(rewards, dict):
        return [f"enemy '{enemy_id}' has invalid rewards"]

    if "battle" in rewards:
        errors.append(f"enemy '{enemy_id}' rewards may not define nested battle payload")

    resource_payload = rewards.get("resources", {})
    if not isinstance(resource_payload, dict):
        errors.append(f"enemy '{enemy_id}' rewards has invalid resources")
    else:
        errors.extend(
            _validate_numeric_map(
                enemy_id=enemy_id,
                field_name="resources",
                value=resource_payload,
            )
        )

    character_payload = rewards.get("character", {})
    if not isinstance(character_payload, dict):
        errors.append(f"enemy '{enemy_id}' rewards has invalid character")
    else:
        for field_name, value in character_payload.items():
            if field_name not in _REWARD_CHARACTER_INT_FIELDS:
                errors.append(f"enemy '{enemy_id}' rewards has unsupported character field '{field_name}'")
                continue
            if isinstance(value, bool) or not _is_int_like(value):
                errors.append(f"enemy '{enemy_id}' rewards has invalid character field '{field_name}'")

    for field_name in _REWARD_LIST_FIELDS:
        list_value = rewards.get(field_name, [])
        if not isinstance(list_value, list):
            errors.append(f"enemy '{enemy_id}' rewards has invalid {field_name}")
            continue
        for item in list_value:
            if not str(item).strip():
                errors.append(f"enemy '{enemy_id}' rewards has invalid {field_name}")
                break

    rebirth_progress_delta = rewards.get("rebirth_progress_delta", 0)
    if isinstance(rebirth_progress_delta, bool) or not _is_int_like(rebirth_progress_delta):
        errors.append(f"enemy '{enemy_id}' rewards has invalid rebirth_progress_delta")

    death = rewards.get("death", False)
    if not isinstance(death, bool):
        errors.append(f"enemy '{enemy_id}' rewards has invalid death")

    return errors


def _validate_numeric_map(
    *,
    enemy_id: str,
    field_name: str,
    value: dict[object, object],
) -> list[str]:
    errors: list[str] = []
    for resource_key, resource_value in value.items():
        if not str(resource_key).strip():
            errors.append(f"enemy '{enemy_id}' rewards has empty {field_name} key")
            continue
        if isinstance(resource_value, bool) or not _is_int_like(resource_value):
            errors.append(
                f"enemy '{enemy_id}' rewards has invalid {field_name} value for '{resource_key}'"
            )
    return errors


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return -1
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _is_int_like(value: object) -> bool:
    try:
        int(value)
    except (TypeError, ValueError):
        return False
    return True


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
