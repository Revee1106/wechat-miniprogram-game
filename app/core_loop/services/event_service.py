from __future__ import annotations

import random

from app.core_loop.realm_config import resolve_realm_key
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


EXCLUDED_RANDOM_EVENT_IDS = {"evt_evil_cultist_012"}


class EventService:
    def __init__(
        self,
        registry: EventRegistry | None = None,
        realm_configs: list[RealmConfig] | None = None,
        rng: random.Random | object | None = None,
    ) -> None:
        self._registry = registry or load_event_registry()
        self._realm_configs = realm_configs or get_realm_configs()
        self._realm_indices = {
            config.key: index for index, config in enumerate(self._realm_configs)
        }
        self._rng = rng or random.Random()

    def select_event(self, run: RunState, rebirth_count: int = 0) -> CurrentEvent:
        eligible = [
            template
            for template in self._registry.templates.values()
            if template.event_id not in EXCLUDED_RANDOM_EVENT_IDS
            and self._is_template_eligible(template, run, rebirth_count)
            and self._has_available_option(template, run)
        ]
        if not eligible:
            raise ConflictError(
                f"no config event available for realm '{run.character.realm}'"
            )

        eligible_by_type: dict[str, list[EventTemplateConfig]] = {}
        for template in eligible:
            eligible_by_type.setdefault(template.event_type, []).append(template)

        selected_type = self._choose_weighted_type(eligible_by_type)
        template = self._choose_weighted_template(eligible_by_type[selected_type])
        return self._build_current_event(template, run)

    def refresh_pending_event(self, run: RunState) -> CurrentEvent | None:
        if run.current_event is None:
            return None

        template = self._registry.templates.get(run.current_event.event_id)
        if template is None:
            return None

        refreshed_event = self._build_current_event(template, run)
        return CurrentEvent(
            event_id=refreshed_event.event_id,
            event_name=refreshed_event.event_name,
            event_type=refreshed_event.event_type,
            outcome_type=refreshed_event.outcome_type,
            risk_level=refreshed_event.risk_level,
            trigger_sources=refreshed_event.trigger_sources,
            choice_pattern=refreshed_event.choice_pattern,
            title_text=refreshed_event.title_text,
            body_text=refreshed_event.body_text,
            region=refreshed_event.region,
            status=run.current_event.status,
            options=refreshed_event.options,
        )

    def _choose_weighted_type(
        self,
        eligible_by_type: dict[str, list[EventTemplateConfig]],
    ) -> str:
        event_types = list(eligible_by_type)
        weights = [
            sum(max(template.weight, 1) for template in eligible_by_type[event_type])
            for event_type in event_types
        ]
        return self._choose_weighted_value(event_types, weights)

    def _choose_weighted_template(
        self,
        templates: list[EventTemplateConfig],
    ) -> EventTemplateConfig:
        weights = [max(template.weight, 1) for template in templates]
        return self._choose_weighted_value(templates, weights)

    def _choose_weighted_value(
        self,
        values: list,
        weights: list[int],
    ):
        if hasattr(self._rng, "choices"):
            return self._rng.choices(values, weights=weights, k=1)[0]

        weighted_pool = [
            value
            for value, weight in zip(values, weights)
            for _ in range(weight)
        ]
        return self._rng.choice(weighted_pool)

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
        disabled_reason = self._get_option_unavailable_reason(run, option)
        is_available = disabled_reason is None
        return CurrentEventOption(
            option_id=option.option_id,
            option_text=option.option_text,
            sort_order=option.sort_order,
            is_default=option.is_default,
            time_cost_months=option.time_cost_months,
            requires_resources=dict(option.requires_resources),
            requires_statuses=list(option.requires_statuses),
            requires_techniques=list(option.requires_techniques),
            requires_equipment_tags=list(option.requires_equipment_tags),
            is_available=is_available,
            disabled_reason=disabled_reason,
        )

    def _is_template_eligible(
        self,
        template: EventTemplateConfig,
        run: RunState,
        rebirth_count: int,
    ) -> bool:
        return (
            self._is_realm_eligible(template, run.character.realm)
            and self._meets_required_statuses(run, template.required_statuses)
            and self._excludes_blocked_statuses(run, template.excluded_statuses)
            and self._meets_required_techniques(run, template.required_techniques)
            and self._meets_required_equipment_tags(run, template.required_equipment_tags)
            and self._meets_required_resources(run, template.required_resources)
            and rebirth_count >= template.required_rebirth_count
            and self._meets_required_karma(run, template.required_karma_min)
            and run.character.luck >= template.required_luck_min
            and self._is_template_repeatable(template, run)
            and self._is_template_off_cooldown(template, run)
        )

    def _has_available_option(
        self,
        template: EventTemplateConfig,
        run: RunState,
    ) -> bool:
        return any(
            self._get_option_unavailable_reason(run, option) is None
            for option in self._registry.get_options_for_event(template.event_id)
        )

    def _is_realm_eligible(self, template: EventTemplateConfig, realm_key: str) -> bool:
        current_index = self._realm_indices.get(
            resolve_realm_key(realm_key, self._realm_configs)
        )
        if current_index is None:
            return False

        if template.realm_min is not None:
            minimum_index = self._realm_indices.get(
                resolve_realm_key(template.realm_min, self._realm_configs, boundary="min")
            )
            if minimum_index is None or current_index < minimum_index:
                return False

        if template.realm_max is not None:
            maximum_index = self._realm_indices.get(
                resolve_realm_key(template.realm_max, self._realm_configs, boundary="max")
            )
            if maximum_index is None or current_index > maximum_index:
                return False

        return True

    def _meets_required_resources(
        self,
        run: RunState,
        required_resources: dict[str, int],
    ) -> bool:
        return all(
            self._get_resource_amount(run, resource_name) >= amount
            for resource_name, amount in required_resources.items()
        )

    def _meets_required_statuses(self, run: RunState, required_statuses: list[str]) -> bool:
        current_statuses = set(run.character.statuses)
        return all(status in current_statuses for status in required_statuses)

    def _excludes_blocked_statuses(self, run: RunState, excluded_statuses: list[str]) -> bool:
        current_statuses = set(run.character.statuses)
        return all(status not in current_statuses for status in excluded_statuses)

    def _meets_required_techniques(self, run: RunState, required_techniques: list[str]) -> bool:
        current_techniques = set(run.character.techniques)
        return all(technique in current_techniques for technique in required_techniques)

    def _meets_required_equipment_tags(
        self,
        run: RunState,
        required_equipment_tags: list[str],
    ) -> bool:
        current_equipment_tags = set(run.character.equipment_tags)
        return all(tag in current_equipment_tags for tag in required_equipment_tags)

    def _meets_required_karma(self, run: RunState, required_karma_min: int | None) -> bool:
        return required_karma_min is None or run.character.karma >= required_karma_min

    def _is_template_repeatable(
        self,
        template: EventTemplateConfig,
        run: RunState,
    ) -> bool:
        trigger_count = run.event_trigger_counts.get(template.event_id, 0)
        if not template.is_repeatable and trigger_count > 0:
            return False
        return trigger_count < template.max_trigger_per_run

    def _is_template_off_cooldown(
        self,
        template: EventTemplateConfig,
        run: RunState,
    ) -> bool:
        return run.event_cooldowns.get(template.event_id, 0) <= 0

    def _get_option_unavailable_reason(self, run: RunState, option) -> str | None:
        if not self._meets_required_resources(run, option.requires_resources):
            return self._build_resource_reason(option.requires_resources)
        if not self._meets_required_statuses(run, option.requires_statuses):
            return self._build_list_reason("statuses", option.requires_statuses)
        if not self._meets_required_techniques(run, option.requires_techniques):
            return self._build_list_reason("techniques", option.requires_techniques)
        if not self._meets_required_equipment_tags(run, option.requires_equipment_tags):
            return self._build_list_reason("equipment_tags", option.requires_equipment_tags)
        return None

    def _build_resource_reason(self, required_resources: dict[str, int]) -> str:
        details = ", ".join(
            f"{resource_name}:{amount}"
            for resource_name, amount in sorted(required_resources.items())
        )
        return f"requires resources {details}"

    def _build_list_reason(self, label: str, values: list[str]) -> str:
        return f"requires {label} {', '.join(values)}"

    def _get_resource_amount(self, run: RunState, resource_name: str) -> int:
        aliases = {
            "herb": "herbs",
            "ore": "ore",
        }
        resolved_name = aliases.get(resource_name, resource_name)
        if resolved_name == "ore":
            return max(getattr(run.resources, "ore", 0), getattr(run.resources, "iron_essence", 0))
        return getattr(run.resources, resolved_name, 0)
