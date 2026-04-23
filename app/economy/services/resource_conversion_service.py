from __future__ import annotations

from app.core_loop.types import ConflictError, RunState
from app.economy.services.run_resource_service import RunResourceService


SPIRIT_STONE_TO_CULTIVATION_RATE = 3


class ResourceConversionService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)

    def convert_spirit_stone_to_cultivation(
        self,
        run: RunState,
        amount: int,
        *,
        cultivation_cap: int | None = None,
    ) -> None:
        if amount <= 0:
            raise ConflictError(
                "conversion amount must be a positive integer",
                code="core.resource_conversion.invalid_amount",
            )

        if int(run.resources.spirit_stone) < amount:
            raise ConflictError(
                "not enough spirit stone to convert",
                code="core.resource_conversion.not_enough_spirit_stone",
            )

        convertible_amount = amount
        if cultivation_cap is not None:
            remaining_gap = max(0, int(cultivation_cap) - int(run.character.cultivation_exp))
            if remaining_gap <= 0:
                return
            convertible_amount = min(
                amount,
                (remaining_gap + SPIRIT_STONE_TO_CULTIVATION_RATE - 1) // SPIRIT_STONE_TO_CULTIVATION_RATE,
            )

        self._resource_service.add(run, "spirit_stone", -convertible_amount)
        run.character.cultivation_exp = max(
            0,
            int(run.character.cultivation_exp) + convertible_amount * SPIRIT_STONE_TO_CULTIVATION_RATE,
        )
        if cultivation_cap is not None:
            run.character.cultivation_exp = min(
                run.character.cultivation_exp,
                int(cultivation_cap),
            )
