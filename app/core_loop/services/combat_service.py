from __future__ import annotations

import random
from copy import deepcopy
from collections.abc import Callable

from app.core_loop.types import ActiveBattleState, CombatActorState, ConflictError


class CombatService:
    def __init__(self, rng: Callable[[], float] | None = None) -> None:
        self._rng = rng or random.random

    def start_battle(
        self,
        *,
        source_event_id: str,
        source_option_id: str,
        player: CombatActorState,
        enemy: CombatActorState,
        allow_flee: bool,
        flee_base_rate: float,
        pill_heal_amount: int,
        pill_count: int = 0,
    ) -> ActiveBattleState:
        return ActiveBattleState(
            source_event_id=source_event_id,
            source_option_id=source_option_id,
            round_index=1,
            allow_flee=allow_flee,
            flee_base_rate=flee_base_rate,
            player=deepcopy(player),
            enemy=deepcopy(enemy),
            pill_heal_amount=max(0, int(pill_heal_amount)),
            pill_count=max(0, int(pill_count)),
            log_lines=[],
            is_finished=False,
            result=None,
        )

    def perform_action(self, battle: ActiveBattleState, action: str) -> ActiveBattleState:
        if battle.is_finished:
            raise ConflictError("battle has already finished", code="core.combat.finished")

        normalized_action = action.strip().lower()
        if normalized_action not in {"attack", "defend", "use_pill", "flee"}:
            raise ConflictError(
                f"unknown combat action '{action}'",
                code="core.combat.invalid_action",
            )

        player_first = battle.player.speed >= battle.enemy.speed
        if normalized_action == "defend":
            battle.log_lines.append("你摆出防御姿态。")
            if player_first:
                self._enemy_attack(battle, defended=True, before_player=False, prefix="")
            else:
                self._enemy_attack(battle, defended=True, before_player=True, prefix="")
            self._advance_round(battle)
            return battle

        if normalized_action == "flee":
            escaped = False
            if player_first:
                escaped = self._attempt_flee(battle)
                if escaped:
                    self._advance_round(battle)
                    return battle
                if not battle.is_finished and battle.enemy.hp_current > 0:
                    self._enemy_attack(battle, defended=False, before_player=False, prefix="")
            else:
                self._enemy_attack(battle, defended=False, before_player=True, prefix="先手")
                if not battle.is_finished:
                    escaped = self._attempt_flee(battle)
                    if escaped:
                        self._advance_round(battle)
                        return battle
            self._advance_round(battle)
            return battle

        if player_first:
            self._resolve_player_action(battle, normalized_action, player_first=True)
            if not battle.is_finished and battle.enemy.hp_current > 0:
                self._enemy_attack(battle, defended=False, before_player=False, prefix="")
        else:
            self._enemy_attack(battle, defended=False, before_player=True, prefix="先手")
            if not battle.is_finished and battle.player.hp_current > 0:
                self._resolve_player_action(battle, normalized_action, player_first=False)

        self._advance_round(battle)
        return battle

    def _resolve_player_action(
        self,
        battle: ActiveBattleState,
        action: str,
        *,
        player_first: bool,
    ) -> None:
        if action == "attack":
            damage = self._calculate_damage(battle.player.attack, battle.enemy.defense)
            battle.enemy.hp_current = max(0, battle.enemy.hp_current - damage)
            if player_first:
                battle.log_lines.append(f"你先手攻击{battle.enemy.name}，造成了{damage}点伤害。")
            else:
                battle.log_lines.append(f"你攻击{battle.enemy.name}，造成了{damage}点伤害。")
            if battle.enemy.hp_current <= 0:
                battle.is_finished = True
                battle.result = "victory"
            return

        if action == "use_pill":
            if battle.pill_count <= 0:
                raise ConflictError("no pill available", code="core.combat.no_pill")
            healed = min(
                battle.player.hp_max,
                battle.player.hp_current + battle.pill_heal_amount,
            )
            actual_heal = healed - battle.player.hp_current
            battle.player.hp_current = healed
            battle.pill_count -= 1
            battle.log_lines.append(f"你服下丹药，恢复了{actual_heal}点气血。")
            return

        raise ConflictError(f"unknown combat action '{action}'", code="core.combat.invalid_action")

    def _enemy_attack(
        self,
        battle: ActiveBattleState,
        *,
        defended: bool,
        before_player: bool,
        prefix: str,
    ) -> None:
        damage = self._calculate_damage(battle.enemy.attack, battle.player.defense)
        if defended:
            damage = max(1, int(damage * 0.6))
        battle.player.hp_current = max(0, battle.player.hp_current - damage)
        if before_player and prefix:
            battle.log_lines.append(f"{battle.enemy.name}{prefix}攻击你，造成了{damage}点伤害。")
        else:
            battle.log_lines.append(f"{battle.enemy.name}攻击你，造成了{damage}点伤害。")
        if battle.player.hp_current <= 0:
            battle.is_finished = True
            battle.result = "defeat"

    def _attempt_flee(self, battle: ActiveBattleState) -> bool:
        if not battle.allow_flee:
            raise ConflictError("flee is not allowed", code="core.combat.flee_not_allowed")

        success_rate = self._resolve_flee_success_rate(battle)
        if self._rng() <= success_rate:
            battle.is_finished = True
            battle.result = "flee_success"
            battle.log_lines.append("你尝试逃跑，成功脱身。")
            return True

        battle.result = "flee_failure"
        battle.log_lines.append(f"你尝试逃跑，但未能摆脱{battle.enemy.name}。")
        return False

    def _resolve_flee_success_rate(self, battle: ActiveBattleState) -> float:
        raw_rate = battle.flee_base_rate + (battle.player.speed - battle.enemy.speed) * 0.03
        return max(0.15, min(0.85, raw_rate))

    def _calculate_damage(self, attack: int, defense: int) -> int:
        random_multiplier = 0.9 + self._rng() * 0.2
        raw_damage = int(attack * random_multiplier) - defense
        return max(1, raw_damage)

    def _advance_round(self, battle: ActiveBattleState) -> None:
        battle.round_index += 1
