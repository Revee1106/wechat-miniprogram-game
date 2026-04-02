from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


_SPECIAL_EFFECT_WHITELIST = {
    "spirit_gathering_array": {
        "breakthrough_bonus_rate",
        "mine_spirit_stone_bonus_rate",
    }
}


def validate_dwelling_config(*, facilities: list[dict[str, object]]) -> ConfigValidationResult:
    errors: list[str] = []

    facility_ids = [str(facility.get("facility_id", "")).strip() for facility in facilities]
    errors.extend(_find_duplicates(facility_ids, "facility_id"))

    for facility in facilities:
        facility_id = str(facility.get("facility_id", "")).strip()
        display_name = str(facility.get("display_name", "")).strip()
        facility_type = str(facility.get("facility_type", "")).strip()
        summary = str(facility.get("summary", "")).strip()
        levels = facility.get("levels")

        if not facility_id:
            errors.append("facility missing facility_id")
            continue
        if not display_name:
            errors.append(f"facility '{facility_id}' has empty display_name")
        if not facility_type:
            errors.append(f"facility '{facility_id}' has empty facility_type")
        if not summary:
            errors.append(f"facility '{facility_id}' has empty summary")
        if not isinstance(levels, list) or not levels:
            errors.append(f"facility '{facility_id}' must define at least one level")
            continue

        level_numbers = [_coerce_int(level.get("level")) for level in levels if isinstance(level, dict)]
        if level_numbers != list(range(1, len(level_numbers) + 1)):
            errors.append(f"facility '{facility_id}' levels must start at 1 and be contiguous")

        for level in levels:
            if not isinstance(level, dict):
                errors.append(f"facility '{facility_id}' has invalid level payload")
                continue

            level_number = _coerce_int(level.get("level"))
            if level_number < 1:
                errors.append(f"facility '{facility_id}' has invalid level")

            errors.extend(
                _validate_non_negative_int_map(
                    facility_id=facility_id,
                    level=level_number,
                    field_name="entry_cost",
                    value=level.get("entry_cost"),
                )
            )
            errors.extend(
                _validate_non_negative_int_map(
                    facility_id=facility_id,
                    level=level_number,
                    field_name="maintenance_cost",
                    value=level.get("maintenance_cost"),
                )
            )
            errors.extend(
                _validate_non_negative_int_map(
                    facility_id=facility_id,
                    level=level_number,
                    field_name="resource_yields",
                    value=level.get("resource_yields"),
                )
            )

            cultivation_exp_gain = _coerce_int(level.get("cultivation_exp_gain"))
            if cultivation_exp_gain < 0:
                errors.append(
                    f"facility '{facility_id}' level {level_number} has invalid cultivation_exp_gain"
                )

            special_effects = level.get("special_effects") or {}
            if not isinstance(special_effects, dict):
                errors.append(
                    f"facility '{facility_id}' level {level_number} has invalid special_effects"
                )
                continue

            allowed_keys = _SPECIAL_EFFECT_WHITELIST.get(facility_id, set())
            for effect_key, effect_value in special_effects.items():
                if effect_key not in allowed_keys:
                    errors.append(
                        f"facility '{facility_id}' level {level_number} has unknown special effect '{effect_key}'"
                    )
                    continue
                if isinstance(effect_value, bool):
                    errors.append(
                        f"facility '{facility_id}' level {level_number} has invalid special effect '{effect_key}'"
                    )
                    continue
                try:
                    float(effect_value)
                except (TypeError, ValueError):
                    errors.append(
                        f"facility '{facility_id}' level {level_number} has invalid special effect '{effect_key}'"
                    )

    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])


def _validate_non_negative_int_map(
    *,
    facility_id: str,
    level: int,
    field_name: str,
    value: object,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"facility '{facility_id}' level {level} has invalid {field_name}"]

    for resource_key, resource_value in value.items():
        if not str(resource_key).strip():
            errors.append(f"facility '{facility_id}' level {level} has empty {field_name} key")
            continue
        if isinstance(resource_value, bool):
            errors.append(
                f"facility '{facility_id}' level {level} has invalid {field_name} value for '{resource_key}'"
            )
            continue
        try:
            coerced = int(resource_value)
        except (TypeError, ValueError):
            errors.append(
                f"facility '{facility_id}' level {level} has invalid {field_name} value for '{resource_key}'"
            )
            continue
        if coerced < 0:
            errors.append(
                f"facility '{facility_id}' level {level} has invalid {field_name} value for '{resource_key}'"
            )
    return errors


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return -1
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


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

