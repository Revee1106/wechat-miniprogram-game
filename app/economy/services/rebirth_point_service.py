from __future__ import annotations

from app.core_loop.realm_config import load_realm_configs, resolve_realm_key
from app.core_loop.types import RunState
from app.economy.repositories.economy_config_repository import EconomyConfigRepository
from app.economy.resource_catalog import load_resource_definitions


class RebirthPointService:
    def __init__(self, base_path: str | None = None) -> None:
        self._base_path = base_path
        self._weights = EconomyConfigRepository(base_path=base_path).load_settlement().get(
            "weights",
            {},
        )
        self._resource_definitions = {
            definition.key: definition
            for definition in load_resource_definitions(base_path=base_path)
        }
        realm_configs = load_realm_configs(base_path=base_path)
        if not realm_configs:
            realm_configs = load_realm_configs()
        self._realm_configs = realm_configs
        self._realm_order_indices = {
            config.key: config.order_index for config in realm_configs
        }

    def calculate(self, run: RunState, special_event_count: int = 0) -> int:
        realm_score = self._get_realm_order_index(run) * self._get_weight("realm")
        survival_score = max(0, run.round_index) * self._get_weight("survival_rounds")
        rare_resource_score = self._get_rare_resource_amount(run) * self._get_weight(
            "rare_resources"
        )
        special_event_score = max(0, special_event_count) * self._get_weight("special_events")
        return max(0, realm_score + survival_score + rare_resource_score + special_event_score)

    def _get_weight(self, key: str) -> int:
        value = self._weights.get(key, 0)
        return int(value) if not isinstance(value, bool) else 0

    def _get_realm_order_index(self, run: RunState) -> int:
        if not self._realm_order_indices:
            return 0
        realm_key = resolve_realm_key(run.character.realm, self._realm_configs)
        return self._realm_order_indices.get(realm_key, 0)

    def _get_rare_resource_amount(self, run: RunState) -> int:
        total = 0
        for stack in run.resource_stacks:
            definition = self._resource_definitions.get(stack.resource_key)
            if definition is None:
                continue
            if definition.rarity.lower() == "common":
                continue
            total += max(0, stack.amount)
        return total
