from __future__ import annotations

from dataclasses import dataclass

from app.core_loop.event_options import EVENT_OPTION_CONFIGS
from app.core_loop.event_templates import EVENT_TEMPLATE_CONFIGS
from app.core_loop.types import EventOptionConfig, EventTemplateConfig


@dataclass(frozen=True)
class EventRegistry:
    templates: dict[str, EventTemplateConfig]
    options: dict[str, EventOptionConfig]


def load_event_registry() -> EventRegistry:
    templates: dict[str, EventTemplateConfig] = {}
    for template in EVENT_TEMPLATE_CONFIGS:
        if template.event_id in templates:
            raise ValueError(f"duplicate event_id: {template.event_id}")
        templates[template.event_id] = template

    options: dict[str, EventOptionConfig] = {}
    for option in EVENT_OPTION_CONFIGS:
        if option.option_id in options:
            raise ValueError(f"duplicate option_id: {option.option_id}")
        options[option.option_id] = option

    for template in EVENT_TEMPLATE_CONFIGS:
        for option_id in template.option_ids:
            option = options.get(option_id)
            if option is None:
                raise ValueError(
                    f"template '{template.event_id}' references missing option_id '{option_id}'"
                )
            if option.event_id != template.event_id:
                raise ValueError(
                    f"option_id '{option_id}' event_id mismatch: expected '{template.event_id}', got '{option.event_id}'"
                )

    return EventRegistry(templates=templates, options=options)
