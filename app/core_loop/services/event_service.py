from __future__ import annotations

from app.core_loop.event_config import EventRegistry, load_event_registry
from app.core_loop.seeds import get_realm_configs
from app.core_loop.types import (
    ConflictError,
    CurrentEvent,
    CurrentEventOption,
    EventTemplateConfig,
    RealmConfig,
    RunState,
)


class EventService:
    def __init__(
        self,
        registry: EventRegistry | None = None,
        realm_configs: list[RealmConfig] | None = None,
    ) -> None:
        self._registry = registry or load_event_registry()
        self._realm_configs = realm_configs or get_realm_configs()
        self._realm_indices = {
            config.key: index for index, config in enumerate(self._realm_configs)
        }

    def select_event(self, run: RunState, rebirth_count: int = 0) -> CurrentEvent:
        eligible = [
            template
            for template in self._registry.templates.values()
            if self._is_template_eligible(template, run, rebirth_count)
            and self._has_available_option(template, run)
        ]
        if not eligible:
            raise ConflictError(
                f"no config event available for realm '{run.character.realm}'"
            )

        template = eligible[(run.round_index - 1) % len(eligible)]
        return self._build_current_event(template, run)

    def _build_current_event(
        self,
        template: EventTemplateConfig,
        run: RunState,
    ) -> CurrentEvent:
        options = [
            self._build_current_option(run, option)
            for option in self._registry.get_options_for_event(template.event_id)
        ]
        return CurrentEvent(
            event_id=template.event_id,
            event_name=template.event_name,
            event_type=template.event_type,
            outcome_type=template.outcome_type,
            risk_level=template.risk_level,
            trigger_sources=list(template.trigger_sources),
            choice_pattern=template.choice_pattern,
            title_text=template.title_text or template.event_name,
            body_text=template.body_text,
            region=template.region,
            status="pending",
            options=options,
        )

    def _build_current_option(
        self,
        run: RunState,
        option,
    ) -> CurrentEventOption:
        is_available = self._meets_required_resources(run, option.requires_resources)
        return CurrentEventOption(
            option_id=option.option_id,
            option_text=option.option_text,
            sort_order=option.sort_order,
            is_default=option.is_default,
            requires_resources=dict(option.requires_resources),
            is_available=is_available,
            disabled_reason=(
                None
                if is_available
                else self._build_disabled_reason(option.requires_resources)
            ),
        )

    def _is_template_eligible(
        self,
        template: EventTemplateConfig,
        run: RunState,
        rebirth_count: int,
    ) -> bool:
        return (
            self._is_realm_eligible(template, run.character.realm)
            and self._meets_required_resources(run, template.required_resources)
            and rebirth_count >= template.required_rebirth_count
            and run.character.luck >= template.required_luck_min
        )

    def _has_available_option(
        self,
        template: EventTemplateConfig,
        run: RunState,
    ) -> bool:
        return any(
            self._meets_required_resources(run, option.requires_resources)
            for option in self._registry.get_options_for_event(template.event_id)
        )

    def _is_realm_eligible(self, template: EventTemplateConfig, realm_key: str) -> bool:
        current_index = self._realm_indices.get(realm_key)
        if current_index is None:
            return False

        if template.realm_min is not None:
            minimum_index = self._realm_indices.get(template.realm_min)
            if minimum_index is None or current_index < minimum_index:
                return False

        if template.realm_max is not None:
            maximum_index = self._realm_indices.get(template.realm_max)
            if maximum_index is None or current_index > maximum_index:
                return False

        return True

    def _meets_required_resources(
        self,
        run: RunState,
        required_resources: dict[str, int],
    ) -> bool:
        return all(
            getattr(run.resources, resource_name, 0) >= amount
            for resource_name, amount in required_resources.items()
        )

    def _build_disabled_reason(self, required_resources: dict[str, int]) -> str:
        details = ", ".join(
            f"{resource_name}:{amount}"
            for resource_name, amount in sorted(required_resources.items())
        )
        return f"requires {details}"
