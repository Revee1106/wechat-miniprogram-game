from __future__ import annotations

from app.core_loop.types import ConflictError, RunState
from app.economy.services.run_resource_service import RunResourceService


class ResourceConversionService:
    def __init__(self, base_path: str | None = None) -> None:
        self._resource_service = RunResourceService(base_path=base_path)

    def convert_spirit_stone_to_cultivation(self, run: RunState, amount: int) -> None:
        if amount <= 0:
            raise ConflictError("conversion amount must be a positive integer")

        if int(run.resources.spirit_stone) < amount:
            raise ConflictError("not enough spirit stone to convert")

        self._resource_service.add(run, "spirit_stone", -amount)
        run.character.cultivation_exp = max(0, int(run.character.cultivation_exp) + amount * 5)
