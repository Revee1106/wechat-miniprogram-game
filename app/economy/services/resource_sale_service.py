from __future__ import annotations

from dataclasses import dataclass

from app.core_loop.types import ConflictError, RunState
from app.economy.services.run_resource_service import RunResourceService


@dataclass(frozen=True)
class SaleRule:
    price: int
    uses_legacy_resource: bool = False


class ResourceSaleService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)
        self._rules = {
            "herb": SaleRule(price=2, uses_legacy_resource=True),
            "ore": SaleRule(price=2, uses_legacy_resource=True),
            "basic_herb": SaleRule(price=1),
            "basic_ore": SaleRule(price=2),
            "spirit_spring_water": SaleRule(price=3),
            "basic_breakthrough_material": SaleRule(price=4),
            "rare_material": SaleRule(price=10),
        }

    def sell(self, run: RunState, resource_key: str, amount: int) -> None:
        if amount <= 0:
            raise ConflictError(
                "sale amount must be a positive integer",
                code="core.resource_sale.invalid_amount",
            )

        rule = self._rules.get(resource_key)
        if rule is None:
            raise ConflictError(
                f"resource '{resource_key}' cannot be sold",
                code="core.resource_sale.resource_cannot_be_sold",
                params={"resource_key": resource_key},
            )

        if self._get_resource_amount(run, resource_key, rule) < amount:
            raise ConflictError(
                "not enough resources to sell",
                code="core.resource_sale.not_enough_resources",
            )

        self._consume_resource(run, resource_key, amount, rule)
        self._resource_service.add(run, "spirit_stone", rule.price * amount)

    def _get_resource_amount(self, run: RunState, resource_key: str, rule: SaleRule) -> int:
        if rule.uses_legacy_resource:
            if resource_key == "herb":
                return int(run.resources.herbs)
            if resource_key == "ore":
                return int(run.resources.ore)

        stack = next(
            (item for item in run.resource_stacks if item.resource_key == resource_key),
            None,
        )
        return int(stack.amount) if stack is not None else 0

    def _consume_resource(
        self,
        run: RunState,
        resource_key: str,
        amount: int,
        rule: SaleRule,
    ) -> None:
        if rule.uses_legacy_resource:
            self._resource_service.add(run, resource_key, -amount)
            return

        self._resource_service.add(run, resource_key, -amount)
