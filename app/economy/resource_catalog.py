from __future__ import annotations

from pathlib import Path

from app.economy.repositories.economy_config_repository import EconomyConfigRepository
from app.economy.types import ResourceDefinition


def load_resource_definitions(base_path: Path | str | None = None) -> list[ResourceDefinition]:
    payload = EconomyConfigRepository(base_path=base_path).load_resources()
    return [
        ResourceDefinition(
            key=str(item.get("key", "")),
            display_name=str(item.get("display_name", "")),
            category=str(item.get("category", "")),
            tier=int(item.get("tier", 0) or 0),
            rarity=str(item.get("rarity", "")),
            stackable=bool(item.get("stackable", True)),
            tags=[str(tag) for tag in item.get("tags", [])],
        )
        for item in payload.get("resources", [])
    ]
