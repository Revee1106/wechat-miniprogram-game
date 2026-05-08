from __future__ import annotations

from pathlib import Path

from app.admin.repositories.material_config_repository import MaterialConfigRepository
from app.economy.repositories.economy_config_repository import EconomyConfigRepository
from app.economy.types import ResourceDefinition


def load_resource_definitions(base_path: Path | str | None = None) -> list[ResourceDefinition]:
    payload = EconomyConfigRepository(base_path=base_path).load_resources()
    definitions = [
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

    by_key = {definition.key: definition for definition in definitions if definition.key}
    material_payload = MaterialConfigRepository(base_path=base_path).load()
    for item in material_payload.get("items", []):
        material_id = str(item.get("material_id", "")).strip()
        if not material_id:
            continue
        by_key[material_id] = ResourceDefinition(
            key=material_id,
            display_name=str(item.get("display_name", "")).strip(),
            category=str(item.get("category", "")).strip(),
            tier=int(item.get("tier", 0) or 0),
            rarity=str(item.get("rarity", "")).strip(),
            stackable=True,
            tags=[str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()],
        )
    return list(by_key.values())
