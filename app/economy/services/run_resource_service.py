from __future__ import annotations

from app.core_loop.types import RunResourceStack, RunState
from app.economy.resource_catalog import load_resource_definitions


class RunResourceService:
    def __init__(self, base_path: str | None = None) -> None:
        self._catalog_keys = {
            definition.key for definition in load_resource_definitions(base_path=base_path)
        }

    def supports(self, resource_key: str) -> bool:
        return self._resolve_legacy_field(resource_key) is not None or resource_key in self._catalog_keys

    def add(self, run: RunState, resource_key: str, amount: int) -> None:
        legacy_field = self._resolve_legacy_field(resource_key)
        if legacy_field is not None:
            current_amount = getattr(run.resources, legacy_field, 0)
            updated_amount = max(0, current_amount + amount)
            setattr(run.resources, legacy_field, updated_amount)
            if legacy_field == "ore":
                run.resources.iron_essence = updated_amount
            return

        self._update_stack(run, resource_key, amount)

    def _resolve_legacy_field(self, resource_key: str) -> str | None:
        legacy_fields = {
            "spirit_stone": "spirit_stone",
            "herb": "herbs",
            "ore": "ore",
            "beast_material": "beast_material",
            "pill": "pill",
            "craft_material": "craft_material",
        }
        return legacy_fields.get(resource_key)

    def _update_stack(self, run: RunState, resource_key: str, amount: int) -> None:
        existing_stack = next(
            (stack for stack in run.resource_stacks if stack.resource_key == resource_key),
            None,
        )
        if existing_stack is None:
            if amount <= 0:
                return
            run.resource_stacks.append(
                RunResourceStack(resource_key=resource_key, amount=amount)
            )
            return

        existing_stack.amount = max(0, existing_stack.amount + amount)
        if existing_stack.amount == 0:
            run.resource_stacks = [
                stack for stack in run.resource_stacks if stack.resource_key != resource_key
            ]
