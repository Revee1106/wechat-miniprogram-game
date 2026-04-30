from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


_EFFECT_TYPE_WHITELIST = {
    "cultivation_exp",
    "hp_restore",
    "lifespan_restore",
    "status_penalty_reduce",
    "breakthrough_bonus",
}

_QUALITY_KEYS = {"low", "mid", "high", "supreme"}


def validate_alchemy_config(
    *,
    levels: list[dict[str, object]],
    recipes: list[dict[str, object]],
) -> ConfigValidationResult:
    errors: list[str] = []

    if not levels:
        errors.append("alchemy config must define at least one mastery level")

    level_values = [str(level.get("level", "")) for level in levels]
    errors.extend(_find_duplicates(level_values, "alchemy_level"))

    sorted_levels = sorted(levels, key=lambda item: _coerce_int(item.get("level")))
    expected_levels = list(range(len(sorted_levels)))
    actual_levels = [_coerce_int(level.get("level")) for level in sorted_levels]
    if actual_levels != expected_levels:
        errors.append("alchemy levels must start at 0 and be contiguous")

    previous_required_exp: int | None = None
    for level in sorted_levels:
        level_number = _coerce_int(level.get("level"))
        display_name = str(level.get("display_name", "")).strip()
        required_mastery_exp = _coerce_int(level.get("required_mastery_exp"))

        if not display_name:
            errors.append(f"alchemy level '{level_number}' has empty display_name")
        if required_mastery_exp < 0:
            errors.append(f"alchemy level '{level_number}' has invalid required_mastery_exp")
        if level_number == 0 and required_mastery_exp != 0:
            errors.append("alchemy level '0' must start at required_mastery_exp 0")
        if previous_required_exp is not None and required_mastery_exp <= previous_required_exp:
            errors.append(
                f"alchemy level '{level_number}' must have increasing required_mastery_exp"
            )
        previous_required_exp = required_mastery_exp

    valid_level_numbers = {
        _coerce_int(level.get("level"))
        for level in sorted_levels
        if _coerce_int(level.get("level")) >= 0
    }

    recipe_ids = [str(recipe.get("recipe_id", "")).strip() for recipe in recipes]
    errors.extend(_find_duplicates(recipe_ids, "alchemy_recipe_id"))

    base_recipe_count = 0
    for recipe in recipes:
        recipe_id = str(recipe.get("recipe_id", "")).strip()
        display_name = str(recipe.get("display_name", "")).strip()
        category = str(recipe.get("category", "")).strip()
        description = str(recipe.get("description", "")).strip()
        effect_summary = str(recipe.get("effect_summary", "")).strip()
        effect_type = str(recipe.get("effect_type", "")).strip()
        required_alchemy_level = _coerce_int(recipe.get("required_alchemy_level"))
        duration_months = _coerce_int(recipe.get("duration_months"))
        success_mastery_exp_gain = _coerce_int(
            recipe.get("success_mastery_exp_gain", 10)
        )
        effect_value = _coerce_float(recipe.get("effect_value"))
        base_success_rate = _coerce_float(recipe.get("base_success_rate"))
        per_level_success_rate = _coerce_float(
            recipe.get("per_level_success_rate", 0.04)
        )
        ingredients = recipe.get("ingredients")
        quality_profiles = recipe.get("quality_profiles", {})
        is_base_recipe = recipe.get("is_base_recipe") is True

        if not recipe_id:
            errors.append("alchemy recipe missing recipe_id")
            continue
        if not display_name:
            errors.append(f"alchemy recipe '{recipe_id}' has empty display_name")
        if not category:
            errors.append(f"alchemy recipe '{recipe_id}' has empty category")
        if not description:
            errors.append(f"alchemy recipe '{recipe_id}' has empty description")
        if required_alchemy_level not in valid_level_numbers:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid required_alchemy_level")
        if duration_months < 1:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid duration_months")
        if success_mastery_exp_gain < 0:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid success_mastery_exp_gain")
        if not 0 <= base_success_rate <= 1:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid base_success_rate")
        if not -1 <= per_level_success_rate <= 1:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid per_level_success_rate")
        if not effect_summary:
            errors.append(f"alchemy recipe '{recipe_id}' has empty effect_summary")
        if effect_type not in _EFFECT_TYPE_WHITELIST:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid effect_type")
        if effect_value <= 0:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid effect_value")
        if not isinstance(ingredients, dict) or not ingredients:
            errors.append(f"alchemy recipe '{recipe_id}' has invalid ingredients")
        else:
            for resource_key, amount in ingredients.items():
                if not str(resource_key).strip():
                    errors.append(
                        f"alchemy recipe '{recipe_id}' has empty ingredients key"
                    )
                    continue
                if _coerce_int(amount) <= 0:
                    errors.append(
                        f"alchemy recipe '{recipe_id}' has invalid ingredients value for '{resource_key}'"
                    )
        errors.extend(_validate_quality_profiles(recipe_id, quality_profiles))
        if is_base_recipe:
            base_recipe_count += 1

    if recipes and base_recipe_count == 0:
        errors.append("alchemy config must define at least one base recipe")

    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])


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


def _validate_quality_profiles(recipe_id: str, raw_profiles: object) -> list[str]:
    if raw_profiles in (None, {}):
        return []
    if not isinstance(raw_profiles, dict):
        return [f"alchemy recipe '{recipe_id}' has invalid quality_profiles"]

    errors: list[str] = []
    for quality, profile in raw_profiles.items():
        normalized_quality = str(quality).strip()
        if normalized_quality not in _QUALITY_KEYS:
            errors.append(
                f"alchemy recipe '{recipe_id}' has unknown quality profile '{normalized_quality}'"
            )
            continue
        if not isinstance(profile, dict):
            errors.append(
                f"alchemy recipe '{recipe_id}' has invalid quality profile '{normalized_quality}'"
            )
            continue
        if not str(profile.get("display_name", "")).strip():
            errors.append(
                f"alchemy recipe '{recipe_id}' quality '{normalized_quality}' has empty display_name"
            )
        if _coerce_float(profile.get("base_weight")) < 0:
            errors.append(
                f"alchemy recipe '{recipe_id}' quality '{normalized_quality}' has invalid base_weight"
            )
        if _coerce_float(profile.get("effect_multiplier")) <= 0:
            errors.append(
                f"alchemy recipe '{recipe_id}' quality '{normalized_quality}' has invalid effect_multiplier"
            )
        if not str(profile.get("color", "")).strip():
            errors.append(
                f"alchemy recipe '{recipe_id}' quality '{normalized_quality}' has empty color"
            )
    return errors


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return -1
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _coerce_float(value: object) -> float:
    if isinstance(value, bool):
        return -1.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1.0
