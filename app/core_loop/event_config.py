from __future__ import annotations

from dataclasses import dataclass, replace

from app.admin.repositories.event_config_repository import EventConfigRepository
from app.core_loop.event_options import EVENT_OPTION_CONFIGS
from app.core_loop.event_templates import EVENT_TEMPLATE_CONFIGS
from app.core_loop.types import EventOptionConfig, EventResultPayload, EventTemplateConfig


@dataclass(frozen=True)
class EventRegistry:
    templates: dict[str, EventTemplateConfig]
    options: dict[str, EventOptionConfig]

    def get_options_for_event(self, event_id: str) -> list[EventOptionConfig]:
        template = self.templates.get(event_id)
        if template is None:
            raise ValueError(f"unknown event_id: {event_id}")
        return [
            self.options[option_id]
            for option_id in template.option_ids
            if option_id in self.options
        ]


def load_event_registry(base_path: str | None = None) -> EventRegistry:
    payload = EventConfigRepository(base_path=base_path).load()
    has_runtime_config = bool(payload.get("templates")) or bool(payload.get("options"))
    if has_runtime_config:
        templates_source, options_source = _coerce_registry_sources(payload)
    else:
        templates_source = list(EVENT_TEMPLATE_CONFIGS)
        options_source = list(EVENT_OPTION_CONFIGS)

    options: dict[str, EventOptionConfig] = {}
    for option in options_source:
        if option.option_id in options:
            raise ValueError(f"duplicate option_id: {option.option_id}")
        if option.sort_order < 1:
            raise ValueError(f"option '{option.option_id}' must have sort_order >= 1")
        normalized_option = replace(
            option,
            resolution_mode=_normalize_resolution_mode(option),
            result_on_success=_coerce_payload(option.result_on_success),
            result_on_failure=_coerce_payload(option.result_on_failure),
        )
        options[option.option_id] = normalized_option

    templates: dict[str, EventTemplateConfig] = {}
    normalized_templates: list[EventTemplateConfig] = []
    ignored_option_ids: set[str] = set()
    for template in templates_source:
        if template.event_id in templates:
            raise ValueError(f"duplicate event_id: {template.event_id}")
        if template.weight <= 0:
            raise ValueError(f"template '{template.event_id}' must have positive weight")
        if not template.option_ids:
            raise ValueError(f"template '{template.event_id}' must include option_ids")
        normalized_template, ignored_option_ids_for_template = _normalize_template_options(
            template,
            options,
        )
        normalized_templates.append(normalized_template)
        ignored_option_ids.update(ignored_option_ids_for_template)
        templates[template.event_id] = normalized_template

    option_reference_counts: dict[str, int] = {}
    for template in normalized_templates:
        for option_id in template.option_ids:
            option = options.get(option_id)
            if option is None:
                raise ValueError(
                    f"template '{template.event_id}' references missing option_id '{option_id}'"
                )
            option_reference_counts[option_id] = option_reference_counts.get(option_id, 0) + 1

    for option_id, option in options.items():
        reference_count = option_reference_counts.get(option_id, 0)
        if option_id in ignored_option_ids:
            continue
        if reference_count == 0:
            raise ValueError(f"orphan option_id: {option_id}")
        if reference_count > 1:
            raise ValueError(f"duplicate option reference: {option_id}")

    for template in normalized_templates:
        for option_id in template.option_ids:
            option = options[option_id]
            if option.event_id != template.event_id:
                raise ValueError(
                    f"option_id '{option_id}' event_id mismatch: expected '{template.event_id}', got '{option.event_id}'"
                )
            if option.next_event_id is not None and option.next_event_id not in templates:
                raise ValueError(
                    f"option_id '{option_id}' references unknown next_event_id '{option.next_event_id}'"
                )
            if set(option.result_on_success.equipment_add) & set(
                option.result_on_success.equipment_remove
            ):
                raise ValueError(
                    f"option_id '{option_id}' mutates the same equipment in add/remove"
                )
            if set(option.result_on_failure.equipment_add) & set(
                option.result_on_failure.equipment_remove
            ):
                raise ValueError(
                    f"option_id '{option_id}' mutates the same equipment in add/remove"
                )

    return EventRegistry(templates=templates, options=options)


def _coerce_registry_sources(
    payload: dict[str, list[dict[str, object]]],
) -> tuple[list[EventTemplateConfig], list[EventOptionConfig]]:
    templates_source = [
        EventTemplateConfig(**template_payload)
        for template_payload in payload.get("templates", [])
    ]
    options_source = [
        EventOptionConfig(**option_payload)
        for option_payload in payload.get("options", [])
    ]
    return templates_source, options_source


def _normalize_template_options(
    template: EventTemplateConfig,
    options: dict[str, EventOptionConfig],
) -> tuple[EventTemplateConfig, set[str]]:
    if template.choice_pattern != "single_outcome" or len(template.option_ids) <= 1:
        return template, set()

    referenced_options = [
        options[option_id]
        for option_id in template.option_ids
        if option_id in options
    ]
    if not referenced_options:
        return template, set()

    selected_option = next(
        (option for option in referenced_options if option.is_default),
        sorted(referenced_options, key=lambda option: (option.sort_order, option.option_id))[0],
    )
    ignored_option_ids = {
        option.option_id
        for option in referenced_options
        if option.option_id != selected_option.option_id
    }
    return replace(template, option_ids=[selected_option.option_id]), ignored_option_ids


def _coerce_payload(
    payload: str | dict[str, object] | EventResultPayload,
) -> EventResultPayload:
    if isinstance(payload, EventResultPayload):
        return payload

    if isinstance(payload, dict):
        if "resource_deltas" in payload:
            resources = {
                _normalize_resource_key(key): int(value)
                for key, value in payload.get("resource_deltas", {}).items()
            }
            character: dict[str, int] = {}
            if "cultivation_exp_delta" in payload:
                character["cultivation_exp"] = int(payload["cultivation_exp_delta"])
            if "lifespan_delta" in payload:
                character["lifespan_delta"] = int(payload["lifespan_delta"])
            return EventResultPayload(
                resources=resources,
                character=character,
                death=bool(payload.get("death", False)),
            )
        return EventResultPayload(
            resources={
                _normalize_resource_key(key): int(value)
                for key, value in payload.get("resources", {}).items()
            },
            character={
                key: int(value) for key, value in payload.get("character", {}).items()
            },
            statuses_add=list(payload.get("statuses_add", [])),
            statuses_remove=list(payload.get("statuses_remove", [])),
            techniques_add=list(payload.get("techniques_add", [])),
            equipment_add=list(payload.get("equipment_add", [])),
            equipment_remove=list(payload.get("equipment_remove", [])),
            battle=payload.get("battle"),
            death=bool(payload.get("death", False)),
            rebirth_progress_delta=int(payload.get("rebirth_progress_delta", 0)),
        )

    if not payload:
        return EventResultPayload()

    resources: dict[str, int] = {}
    character: dict[str, int] = {}
    death = False
    for token in filter(None, (item.strip() for item in payload.split(","))):
        key, _, raw_value = token.partition(":")
        if not _:
            raise ValueError(f"invalid event payload token: {token}")
        normalized_key = key.strip()
        normalized_value = raw_value.strip()
        if normalized_key == "cultivation_exp":
            character["cultivation_exp"] = character.get("cultivation_exp", 0) + int(
                normalized_value
            )
            continue
        if normalized_key == "lifespan":
            character["lifespan_delta"] = character.get("lifespan_delta", 0) + int(
                normalized_value
            )
            continue
        if normalized_key == "death":
            death = normalized_value.lower() == "true"
            continue
        resources[_normalize_resource_key(normalized_key)] = resources.get(
            _normalize_resource_key(normalized_key),
            0,
        ) + int(normalized_value)

    return EventResultPayload(resources=resources, character=character, death=death)


def _normalize_resolution_mode(option: EventOptionConfig) -> str:
    if option.resolution_mode in {"direct", "combat"}:
        return option.resolution_mode

    if (
        (option.success_rate_formula or "").strip()
        or bool(option.log_text_failure.strip())
        or _has_meaningful_payload(option.result_on_failure)
    ):
        return "combat"
    return "direct"


def _has_meaningful_payload(
    payload: str | dict[str, object] | EventResultPayload,
) -> bool:
    if isinstance(payload, EventResultPayload):
        return any(
            (
                payload.resources,
                payload.character,
                payload.statuses_add,
                payload.statuses_remove,
                payload.techniques_add,
                payload.equipment_add,
                payload.equipment_remove,
                payload.battle,
                payload.death,
                payload.rebirth_progress_delta,
            )
        )

    if isinstance(payload, dict):
        return any(payload.values())

    return bool(payload.strip())


def _normalize_resource_key(resource_name: str) -> str:
    aliases = {
        "herbs": "herb",
        "iron_essence": "ore",
    }
    return aliases.get(resource_name, resource_name)
