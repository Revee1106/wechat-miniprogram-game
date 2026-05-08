from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


EQUIPMENT_SLOTS = {"weapon", "armor", "accessory", "artifact"}


def validate_equipment_config(*, items: list[dict[str, object]]) -> ConfigValidationResult:
    errors: list[str] = []

    item_ids = [str(item.get("equipment_id", "")).strip() for item in items]
    errors.extend(_find_duplicates(item_ids, "equipment_id"))

    for item in items:
        equipment_id = str(item.get("equipment_id", "")).strip()
        display_name = str(item.get("display_name", "")).strip()
        slot = str(item.get("slot", "")).strip()

        if not equipment_id:
            errors.append("equipment missing equipment_id")
            continue
        if not display_name:
            errors.append(f"equipment '{equipment_id}' has empty display_name")
        if slot not in EQUIPMENT_SLOTS:
            errors.append(f"equipment '{equipment_id}' has invalid slot")
            continue

        attack = _coerce_non_negative_int(item.get("attack"))
        defense = _coerce_non_negative_int(item.get("defense"))
        hp_max = _coerce_non_negative_int(item.get("hp_max"))
        if attack is None:
            errors.append(f"equipment '{equipment_id}' has invalid attack")
            attack = 0
        if defense is None:
            errors.append(f"equipment '{equipment_id}' has invalid defense")
            defense = 0
        if hp_max is None:
            errors.append(f"equipment '{equipment_id}' has invalid hp_max")
            hp_max = 0

        special_effects = item.get("special_effects", {})
        if not isinstance(special_effects, dict):
            errors.append(f"equipment '{equipment_id}' has invalid special_effects")
            special_effects = {}
        elif any(not str(key).strip() for key in special_effects):
            errors.append(f"equipment '{equipment_id}' has empty special_effects key")

        if slot == "weapon":
            if attack <= 0:
                errors.append(f"weapon '{equipment_id}' must provide attack")
            if defense != 0 or hp_max != 0 or special_effects:
                errors.append(f"weapon '{equipment_id}' may only provide attack")
        elif slot == "armor":
            if defense <= 0 and hp_max <= 0:
                errors.append(f"armor '{equipment_id}' must provide defense or hp_max")
            if attack != 0 or special_effects:
                errors.append(f"armor '{equipment_id}' may only provide defense and hp_max")
        elif slot == "accessory":
            if attack != 0 or defense != 0 or hp_max != 0:
                errors.append(f"accessory '{equipment_id}' may only provide special_effects")
            if not special_effects:
                errors.append(f"accessory '{equipment_id}' must provide special_effects")
        elif slot == "artifact":
            if attack != 0 or defense != 0 or hp_max != 0:
                errors.append(f"artifact '{equipment_id}' may only provide special_effects")
            if not special_effects:
                errors.append(f"artifact '{equipment_id}' must provide special_effects")

    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])


def _coerce_non_negative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        numeric_value = int(value or 0)
    except (TypeError, ValueError):
        return None
    if numeric_value < 0:
        return None
    return numeric_value


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
