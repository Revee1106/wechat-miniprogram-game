from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


def validate_material_config(*, items: list[dict[str, object]]) -> ConfigValidationResult:
    errors: list[str] = []

    material_ids = [str(item.get("material_id", "")).strip() for item in items]
    errors.extend(_find_duplicates(material_ids, "material_id"))

    for item in items:
        material_id = str(item.get("material_id", "")).strip()
        if not material_id:
            errors.append("material missing material_id")
            continue

        if not str(item.get("display_name", "")).strip():
            errors.append(f"material '{material_id}' has empty display_name")
        if not str(item.get("category", "")).strip():
            errors.append(f"material '{material_id}' has empty category")
        if not str(item.get("rarity", "")).strip():
            errors.append(f"material '{material_id}' has empty rarity")
        if not str(item.get("source", "")).strip():
            errors.append(f"material '{material_id}' has empty source")

        tier = _coerce_positive_int(item.get("tier"))
        if tier is None:
            errors.append(f"material '{material_id}' has invalid tier")

        tags = item.get("tags", [])
        if not isinstance(tags, list):
            errors.append(f"material '{material_id}' has invalid tags")
        elif any(not str(tag).strip() for tag in tags):
            errors.append(f"material '{material_id}' has empty tag")

        description = item.get("description", "")
        if description is not None and not isinstance(description, str):
            errors.append(f"material '{material_id}' has invalid description")

    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])


def _coerce_positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        numeric_value = int(value or 0)
    except (TypeError, ValueError):
        return None
    if numeric_value <= 0:
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
