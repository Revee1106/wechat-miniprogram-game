from __future__ import annotations

from dataclasses import dataclass

from app.core_loop.event_options import EVENT_OPTION_CONFIGS
from app.core_loop.event_templates import EVENT_TEMPLATE_CONFIGS
from app.core_loop.types import EventOptionConfig, EventTemplateConfig


@dataclass(frozen=True)
class EventRegistry:
    templates: dict[str, EventTemplateConfig]
    options: dict[str, EventOptionConfig]

    def get_options_for_event(self, event_id: str) -> list[EventOptionConfig]:
        if event_id not in self.templates:
            raise ValueError(f"unknown event_id: {event_id}")
        return sorted(
            (
                option
                for option in self.options.values()
                if option.event_id == event_id
            ),
            key=lambda option: (option.sort_order, option.option_id),
        )


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

    option_reference_counts: dict[str, int] = {}
    for template in EVENT_TEMPLATE_CONFIGS:
        for option_id in template.option_ids:
            option = options.get(option_id)
            if option is None:
                raise ValueError(
                    f"template '{template.event_id}' references missing option_id '{option_id}'"
                )
            option_reference_counts[option_id] = option_reference_counts.get(option_id, 0) + 1

    for option_id, option in options.items():
        reference_count = option_reference_counts.get(option_id, 0)
        if reference_count == 0:
            raise ValueError(f"orphan option_id: {option_id}")
        if reference_count > 1:
            raise ValueError(f"duplicate option reference: {option_id}")

    for template in EVENT_TEMPLATE_CONFIGS:
        for option_id in template.option_ids:
            option = options[option_id]
            if option.event_id != template.event_id:
                raise ValueError(
                    f"option_id '{option_id}' event_id mismatch: expected '{template.event_id}', got '{option.event_id}'"
                )

    return EventRegistry(templates=templates, options=options)
