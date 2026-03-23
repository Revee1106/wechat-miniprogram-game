from __future__ import annotations

from app.core_loop.event_config import EventRegistry, load_event_registry
from app.core_loop.seeds import get_realm_configs
from app.core_loop.types import (
    ConflictError,
    CoreLoopError,
    CurrentEventOption,
    EventOptionConfig,
    EventResultPayload,
    RealmConfig,
    RunState,
)


class EventResolutionService:
    def __init__(
        self,
        registry: EventRegistry | None = None,
        realm_configs: list[RealmConfig] | None = None,
    ) -> None:
        self._registry = registry or load_event_registry()
        self._realm_configs = {
            config.key: config for config in (realm_configs or get_realm_configs())
        }

    def resolve(self, run: RunState, option_id: str) -> RunState:
        if run.current_event is None:
            raise ConflictError("there is no pending event to resolve")

        runtime_option = next(
            (
                option
                for option in run.current_event.options
                if option.option_id == option_id
            ),
            None,
        )
        if runtime_option is None:
            raise ConflictError(f"option '{option_id}' is not available")
        if not self._is_option_available(run, runtime_option):
            raise ConflictError(runtime_option.disabled_reason or "option is unavailable")

        option_config = self._registry.options.get(option_id)
        if option_config is None or option_config.event_id != run.current_event.event_id:
            raise ConflictError(f"option '{option_id}' is not valid for this event")

        success = self._determine_success(run, option_config)
        payload = self._parse_payload(
            option_config.result_on_success
            if success
            else option_config.result_on_failure
        )
        log_text = (
            option_config.log_text_success
            if success
            else option_config.log_text_failure
        )

        self._apply_payload(run, payload)
        if run.character.lifespan_current <= 0:
            run.character.lifespan_current = 0
            run.character.is_dead = True

        run.result_summary = log_text or self._build_fallback_summary(
            run.current_event.event_name,
            option_config.option_text,
        )
        run.current_event = None
        return run

    def _is_option_available(
        self,
        run: RunState,
        runtime_option: CurrentEventOption,
    ) -> bool:
        return all(
            getattr(run.resources, resource_name, 0) >= amount
            for resource_name, amount in runtime_option.requires_resources.items()
        )

    def _determine_success(self, run: RunState, option_config: EventOptionConfig) -> bool:
        success_rate = self._evaluate_success_rate(run, option_config.success_rate_formula)
        return success_rate >= 0.5

    def _evaluate_success_rate(self, run: RunState, formula: str) -> float:
        realm_config = self._realm_configs.get(run.character.realm)
        if realm_config is None:
            raise CoreLoopError(f"unknown realm '{run.character.realm}'")

        expression = formula or "base_success_rate"
        try:
            value = eval(  # noqa: S307 - config expressions are repository-owned input
                expression,
                {"__builtins__": {}},
                {
                    "base_success_rate": realm_config.base_success_rate,
                    "luck": run.character.luck,
                    "technique_bonus": run.character.technique_bonus,
                    "pill_bonus": run.character.pill_bonus,
                    "status_penalty": run.character.status_penalty,
                },
            )
        except Exception as error:  # pragma: no cover - defensive
            raise CoreLoopError(f"invalid success rate formula: {expression}") from error

        return max(0.0, min(1.0, float(value)))

    def _parse_payload(
        self,
        payload_config: str | dict[str, object] | EventResultPayload,
    ) -> EventResultPayload:
        if isinstance(payload_config, EventResultPayload):
            return payload_config

        if isinstance(payload_config, dict):
            return EventResultPayload(
                resource_deltas={
                    key: int(value)
                    for key, value in payload_config.get("resource_deltas", {}).items()
                },
                cultivation_exp_delta=int(payload_config.get("cultivation_exp_delta", 0)),
                lifespan_delta=int(payload_config.get("lifespan_delta", 0)),
                death=bool(payload_config.get("death", False)),
            )

        resource_deltas: dict[str, int] = {}
        cultivation_exp_delta = 0
        lifespan_delta = 0
        death = False
        for token in filter(None, (item.strip() for item in payload_config.split(","))):
            key, _, raw_value = token.partition(":")
            if not _:
                raise CoreLoopError(f"invalid event payload token: {token}")

            normalized_key = key.strip()
            normalized_value = raw_value.strip()
            if normalized_key == "cultivation_exp":
                cultivation_exp_delta += int(normalized_value)
                continue
            if normalized_key == "lifespan":
                lifespan_delta += int(normalized_value)
                continue
            if normalized_key == "death":
                death = normalized_value.lower() == "true"
                continue
            resource_deltas[normalized_key] = resource_deltas.get(normalized_key, 0) + int(
                normalized_value
            )

        return EventResultPayload(
            resource_deltas=resource_deltas,
            cultivation_exp_delta=cultivation_exp_delta,
            lifespan_delta=lifespan_delta,
            death=death,
        )

    def _apply_payload(self, run: RunState, payload: EventResultPayload) -> None:
        updated_resources: dict[str, int] = {}
        for resource_name, delta in payload.resource_deltas.items():
            if not hasattr(run.resources, resource_name):
                raise CoreLoopError(f"unknown resource '{resource_name}'")
            updated_resources[resource_name] = max(
                0,
                getattr(run.resources, resource_name) + delta,
            )

        updated_cultivation_exp = max(
            0,
            run.character.cultivation_exp + payload.cultivation_exp_delta,
        )
        updated_lifespan = min(
            run.character.lifespan_max,
            max(0, run.character.lifespan_current + payload.lifespan_delta),
        )

        for resource_name, updated_value in updated_resources.items():
            setattr(run.resources, resource_name, updated_value)
        run.character.cultivation_exp = updated_cultivation_exp
        run.character.lifespan_current = updated_lifespan

        if payload.death:
            run.character.is_dead = True
            run.character.lifespan_current = 0

    def _build_fallback_summary(self, event_name: str, option_text: str) -> str:
        return f"{event_name}: {option_text}"
