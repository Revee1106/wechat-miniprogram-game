from __future__ import annotations

from app.core_loop.types import ConflictError, PlayerProfile, RunState


class RebirthService:
    def claim(self, profile: PlayerProfile, run: RunState) -> PlayerProfile:
        if not run.character.is_dead:
            raise ConflictError("rebirth is only available after death")

        profile.total_rebirth_count += 1
        profile.permanent_luck_bonus += 1
        return profile

    def apply_permanent_bonus(self, profile: PlayerProfile, run: RunState) -> RunState:
        run.resources.spirit_stone += profile.total_rebirth_count
        run.resource_stacks = []
        return run
