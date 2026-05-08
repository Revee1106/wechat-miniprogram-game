from __future__ import annotations

import hashlib
from pathlib import Path

from app.admin.repositories.equipment_config_repository import EquipmentConfigRepository
from app.core_loop.types import ConflictError, EquipmentItemState, RunState


EQUIPMENT_SLOTS = {
    "weapon": "武器",
    "armor": "防具",
    "accessory": "饰品",
    "artifact": "法宝",
}


class EquipmentService:
    def __init__(self, base_path: str | None = None) -> None:
        self._base_path = base_path
        self._specs = self._load_specs(base_path=base_path)

    def reload_config(self, base_path: str | None = None) -> None:
        if base_path is not None:
            self._base_path = base_path
        self._specs = self._load_specs(base_path=self._base_path)

    def hydrate_run(self, run: RunState) -> None:
        self._cleanup_equipped_items(run)
        run.equipment_inventory = [
            self.build_item(run, item_id)
            for item_id in run.character.equipment_tags
        ]

    def equip(self, run: RunState, item_id: str) -> None:
        normalized_item_id = item_id.strip()
        if normalized_item_id not in set(run.character.equipment_tags):
            raise ConflictError(
                f"equipment '{item_id}' is not available",
                code="core.equipment.not_available",
            )

        item = self.build_item(run, normalized_item_id)
        run.character.equipped_items[item.slot] = normalized_item_id
        self.hydrate_run(run)

    def unequip(self, run: RunState, item_id: str) -> None:
        normalized_item_id = item_id.strip()
        equipped_slot = next(
            (
                slot
                for slot, equipped_item_id in run.character.equipped_items.items()
                if equipped_item_id == normalized_item_id
            ),
            None,
        )
        if equipped_slot is None:
            raise ConflictError(
                f"equipment '{item_id}' is not equipped",
                code="core.equipment.not_equipped",
            )

        run.character.equipped_items.pop(equipped_slot, None)
        self.hydrate_run(run)

    def build_item(self, run: RunState, item_id: str) -> EquipmentItemState:
        spec = self._specs.get(item_id)
        if spec is not None:
            slot = str(spec.get("slot", "artifact"))
            return EquipmentItemState(
                item_id=item_id,
                display_name=str(spec.get("display_name", "")).strip() or self.format_display_name(item_id),
                slot=slot,
                slot_label=EQUIPMENT_SLOTS.get(slot, "装备"),
                attack=max(0, int(spec.get("attack", 0) or 0)),
                defense=max(0, int(spec.get("defense", 0) or 0)),
                speed=0,
                hp_max=max(0, int(spec.get("hp_max", 0) or 0)),
                description=str(spec.get("description", "")).strip()
                or self._build_description(
                    slot,
                    max(0, int(spec.get("attack", 0) or 0)),
                    max(0, int(spec.get("defense", 0) or 0)),
                    0,
                    max(0, int(spec.get("hp_max", 0) or 0)),
                    spec.get("special_effects", {}),
                ),
                special_effects=dict(spec.get("special_effects", {}) or {}),
                is_equipped=item_id in set(run.character.equipped_items.values()),
            )

        slot = self.resolve_slot(item_id)
        stat_seed = self._build_stat_seed(item_id)
        attack = 0
        defense = 0
        speed = 0
        hp_max = 0

        if slot == "weapon":
            attack = 2 + stat_seed % 4
            speed = stat_seed % 2
        elif slot == "armor":
            defense = 2 + stat_seed % 4
            hp_max = 8 + (stat_seed % 3) * 4
        elif slot == "accessory":
            speed = 1 + stat_seed % 3
            hp_max = 4 + (stat_seed % 2) * 4
        else:
            attack = 1 + stat_seed % 3
            defense = 1 + (stat_seed // 2) % 3

        return EquipmentItemState(
            item_id=item_id,
            display_name=self.format_display_name(item_id),
            slot=slot,
            slot_label=EQUIPMENT_SLOTS[slot],
            attack=attack,
            defense=defense,
            speed=speed,
            hp_max=hp_max,
            description=self._build_description(slot, attack, defense, speed, hp_max),
            special_effects={},
            is_equipped=item_id in set(run.character.equipped_items.values()),
        )

    def get_equipped_stat_bonus(self, run: RunState) -> dict[str, int]:
        self._cleanup_equipped_items(run)
        bonus = {
            "attack": 0,
            "defense": 0,
            "speed": 0,
            "hp_max": 0,
        }
        for item_id in run.character.equipped_items.values():
            if item_id not in set(run.character.equipment_tags):
                continue
            item = self.build_item(run, item_id)
            bonus["attack"] += item.attack
            bonus["defense"] += item.defense
            bonus["speed"] += item.speed
            bonus["hp_max"] += item.hp_max
        return bonus

    def resolve_slot(self, item_id: str) -> str:
        normalized = item_id.lower()
        if any(token in normalized for token in ("weapon", "sword", "blade", "knife", "spear", "bow", "jian", "dao")):
            return "weapon"
        if any(token in normalized for token in ("armor", "robe", "shield", "mail", "jia", "pao")):
            return "armor"
        if any(token in normalized for token in ("artifact", "ding", "bell", "seal", "tower", "fan", "mirror")):
            return "artifact"
        if any(token in normalized for token in ("ring", "amulet", "token", "jade", "bead", "pendant")):
            return "accessory"
        return "artifact"

    def format_display_name(self, item_id: str) -> str:
        name = item_id.strip().replace("_", " ").replace("-", " ")
        if not name:
            return "未知装备"
        return " ".join(part.capitalize() for part in name.split())

    def _cleanup_equipped_items(self, run: RunState) -> None:
        owned = set(run.character.equipment_tags)
        cleaned: dict[str, str] = {}
        for slot, item_id in run.character.equipped_items.items():
            if slot in EQUIPMENT_SLOTS and item_id in owned:
                cleaned[slot] = item_id
        run.character.equipped_items = cleaned

    def _build_stat_seed(self, item_id: str) -> int:
        digest = hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:8]
        return int(digest, 16)

    def _load_specs(self, *, base_path: str | None) -> dict[str, dict[str, object]]:
        try:
            payload = EquipmentConfigRepository(base_path=Path(base_path) if base_path else None).load()
        except (FileNotFoundError, ValueError):
            return {}

        specs: dict[str, dict[str, object]] = {}
        for item in payload.get("items", []):
            item_id = str(item.get("equipment_id", "")).strip()
            slot = str(item.get("slot", "")).strip()
            if not item_id or slot not in EQUIPMENT_SLOTS:
                continue
            specs[item_id] = dict(item)
        return specs

    def _build_description(
        self,
        slot: str,
        attack: int,
        defense: int,
        speed: int,
        hp_max: int,
        special_effects: object | None = None,
    ) -> str:
        parts = [EQUIPMENT_SLOTS.get(slot, "装备")]
        if attack:
            parts.append(f"攻击 +{attack}")
        if defense:
            parts.append(f"防御 +{defense}")
        if speed:
            parts.append(f"速度 +{speed}")
        if hp_max:
            parts.append(f"气血上限 +{hp_max}")
        if isinstance(special_effects, dict) and special_effects:
            parts.append("特殊效果")
        return "，".join(parts)
