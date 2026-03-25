from __future__ import annotations

from app.core_loop.types import ConfigValidationResult


ALLOWED_EVENT_TYPES = {
    "cultivation",
    "material",
    "technique",
    "equipment",
    "encounter",
    "survival",
}
ALLOWED_OUTCOME_TYPES = {
    "cultivation",
    "material",
    "technique",
    "equipment",
    "lifespan",
    "status",
    "breakthrough",
    "karma",
    "luck",
    "mixed",
}
ALLOWED_RISK_LEVELS = {"safe", "normal", "risky", "fatal"}
ALLOWED_CHOICE_PATTERNS = {
    "single_outcome",
    "binary_choice",
    "multi_choice",
    "resource_gated",
    "stat_check",
}
ALLOWED_TRIGGER_SOURCES = {
    "realm_based",
    "region_based",
    "dwelling_based",
    "technique_based",
    "equipment_based",
    "status_based",
    "karma_based",
    "luck_based",
    "rebirth_based",
    "global",
}


def validate_event_config(
    *,
    templates: list[dict[str, object]],
    options: list[dict[str, object]],
) -> ConfigValidationResult:
    errors: list[str] = []

    template_ids = [str(template.get("event_id", "")) for template in templates]
    option_ids = [str(option.get("option_id", "")) for option in options]

    errors.extend(_find_duplicates(template_ids, "event_id"))
    errors.extend(_find_duplicates(option_ids, "option_id"))

    template_map = {str(template.get("event_id", "")): template for template in templates}
    option_map = {str(option.get("option_id", "")): option for option in options}

    for template in templates:
        event_id = str(template.get("event_id", ""))
        if not event_id:
            errors.append("template missing event_id")
            continue
        if str(template.get("event_type", "")) not in ALLOWED_EVENT_TYPES:
            errors.append(f"template '{event_id}' has invalid event_type")
        if str(template.get("outcome_type", "")) not in ALLOWED_OUTCOME_TYPES:
            errors.append(f"template '{event_id}' has invalid outcome_type")
        if str(template.get("risk_level", "")) not in ALLOWED_RISK_LEVELS:
            errors.append(f"template '{event_id}' has invalid risk_level")
        if str(template.get("choice_pattern", "")) not in ALLOWED_CHOICE_PATTERNS:
            errors.append(f"template '{event_id}' has invalid choice_pattern")
        trigger_sources = template.get("trigger_sources", [])
        if not isinstance(trigger_sources, list) or not set(trigger_sources).issubset(
            ALLOWED_TRIGGER_SOURCES
        ):
            errors.append(f"template '{event_id}' has invalid trigger_sources")
        if int(template.get("weight", 0) or 0) <= 0:
            errors.append(f"template '{event_id}' must have positive weight")
        option_refs = template.get("option_ids", [])
        if not isinstance(option_refs, list) or not option_refs:
            errors.append(f"template '{event_id}' must include option_ids")
        else:
            for option_id in option_refs:
                if str(option_id) not in option_map:
                    errors.append(
                        f"template '{event_id}' references missing option_id '{option_id}'"
                    )

    for option in options:
        option_id = str(option.get("option_id", ""))
        event_id = str(option.get("event_id", ""))
        if not option_id:
            errors.append("option missing option_id")
            continue
        if event_id not in template_map:
            errors.append(f"option '{option_id}' references missing event_id '{event_id}'")
        if int(option.get("sort_order", 1) or 0) < 1:
            errors.append(f"option '{option_id}' must have sort_order >= 1")
        next_event_id = option.get("next_event_id")
        if next_event_id is not None and str(next_event_id) not in template_map:
            errors.append(
                f"option '{option_id}' references missing next_event_id '{next_event_id}'"
            )
        for payload_name in ("result_on_success", "result_on_failure"):
            payload = option.get(payload_name) or {}
            if not isinstance(payload, dict):
                continue
            equipment_add = set(payload.get("equipment_add", []) or [])
            equipment_remove = set(payload.get("equipment_remove", []) or [])
            if equipment_add & equipment_remove:
                errors.append(
                    f"option '{option_id}' has conflicting equipment mutations in {payload_name}"
                )

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
