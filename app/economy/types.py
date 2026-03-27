from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResourceDefinition:
    key: str
    display_name: str
    category: str
    tier: int
    rarity: str
    stackable: bool = True
    tags: list[str] = field(default_factory=list)
