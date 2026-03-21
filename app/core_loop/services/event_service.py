from __future__ import annotations

from app.core_loop.seeds import get_event_templates
from app.core_loop.types import ConflictError, CurrentEvent, EventChoice, RunState


class EventService:
    def __init__(self) -> None:
        self._templates = get_event_templates()

    def select_event_for_realm(self, realm_key: str, round_index: int) -> CurrentEvent:
        eligible = [
            template for template in self._templates if realm_key in template.realm_keys
        ]
        if not eligible:
            raise ConflictError(f"no event available for realm '{realm_key}'")

        template = eligible[(round_index - 1) % len(eligible)]
        return CurrentEvent(
            template_key=template.key,
            template_name=template.display_name,
            description=template.description,
            status="pending",
            choices=template.choices,
        )

    def resolve_choice(self, run: RunState, choice_key: str) -> RunState:
        if run.current_event is None:
            raise ConflictError("there is no pending event to resolve")

        choice = next(
            (
                event_choice
                for event_choice in run.current_event.choices
                if event_choice.key == choice_key
            ),
            None,
        )
        if choice is None:
            raise ConflictError(f"choice '{choice_key}' is not available")

        self._apply_choice(run, choice)
        run.current_event = None
        return run

    def _apply_choice(self, run: RunState, choice: EventChoice) -> None:
        run.resources.spirit_stone = max(
            0, run.resources.spirit_stone + choice.spirit_stone_delta
        )
        run.character.cultivation_exp = max(
            0, run.character.cultivation_exp + choice.cultivation_exp_delta
        )
        run.character.lifespan_current = min(
            run.character.lifespan_max,
            run.character.lifespan_current + choice.lifespan_delta,
        )

        if choice.death_chance >= 1.0:
            run.character.is_dead = True
            run.result_summary = "你在事件中陨落，本局结束。"
            return

        if run.character.lifespan_current <= 0:
            run.character.is_dead = True
            run.result_summary = "寿元耗尽，本局结束。"
        else:
            run.result_summary = f"已完成事件选择：{choice.display_name}"
