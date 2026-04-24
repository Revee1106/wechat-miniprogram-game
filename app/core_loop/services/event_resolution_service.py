from __future__ import annotations

from app.core_loop.realm_config import resolve_realm_key
from app.core_loop.event_config import EventRegistry, load_event_registry
from app.core_loop.seeds import get_realm_configs
from app.core_loop.types import (
    ActiveBattleState,
    CombatActorState,
    ConflictError,
    CoreLoopError,
    CurrentEventOption,
    EventOptionConfig,
    EventResolutionLog,
    EventResultPayload,
    RealmConfig,
    RunState,
)
from app.core_loop.services.combat_service import CombatService
from app.core_loop.services.combat_stat_service import CombatStatService
from app.economy.services.run_resource_service import RunResourceService


DO_NOTHING_OPTION_ID = "__do_nothing__"


class EventResolutionService:
    _DEFAULT_FLEE_BASE_RATE = 0.35
    _DEFAULT_PILL_HEAL_AMOUNT = 30

    def __init__(
        self,
        registry: EventRegistry | None = None,
        realm_configs: list[RealmConfig] | None = None,
        economy_base_path: str | None = None,
        enemy_templates: dict[str, dict[str, object]] | None = None,
    ) -> None:
        self._registry = registry or load_event_registry()
        self._realm_configs = {
            config.key: config for config in (realm_configs or get_realm_configs())
        }
        self._enemy_templates = {
            enemy_id: dict(template)
            for enemy_id, template in (enemy_templates or {}).items()
        }
        self._combat_service = CombatService()
        self._combat_stat_service = CombatStatService(
            realm_configs=list(self._realm_configs.values())
        )
        self._run_resource_service = RunResourceService(base_path=economy_base_path)

    def resolve(
        self,
        run: RunState,
        option_id: str,
        *,
        combat_service: CombatService | None = None,
        combat_stat_service: CombatStatService | None = None,
    ) -> RunState:
        if run.current_event is None:
            raise ConflictError("there is no pending event to resolve")
        if run.active_battle is not None:
            raise ConflictError("battle is already in progress")

        runtime_option = next(
            (
                option
                for option in run.current_event.options
                if option.option_id == option_id
            ),
            None,
        )
        if runtime_option is None:
            raise ConflictError(f"option '{option_id}' is not available")
        if not self._is_option_available(run, runtime_option):
            raise ConflictError(runtime_option.disabled_reason or "option is unavailable")

        if option_id == DO_NOTHING_OPTION_ID:
            template = self._registry.templates.get(run.current_event.event_id)
            if template is not None:
                run.event_trigger_counts[template.event_id] = (
                    run.event_trigger_counts.get(template.event_id, 0) + 1
                )
                if template.cooldown_rounds > 0:
                    run.event_cooldowns[template.event_id] = template.cooldown_rounds
            run.result_summary = "你没有采取行动，事情就此过去。"
            run.last_event_resolution = EventResolutionLog(
                event_id=run.current_event.event_id,
                option_id=DO_NOTHING_OPTION_ID,
            )
            run.current_event = None
            return run

        option_config = self._registry.options.get(option_id)
        if option_config is None or option_config.event_id != run.current_event.event_id:
            raise ConflictError(f"option '{option_id}' is not valid for this event")
        template = self._registry.templates.get(option_config.event_id)
        if template is None:
            raise ConflictError(f"event '{option_config.event_id}' is not registered")

        if option_config.resolution_mode == "combat" and self._should_start_battle(option_config):
            self._start_combat_event(
                run,
                option_config=option_config,
                template=template,
                combat_service=combat_service or self._combat_service,
                combat_stat_service=combat_stat_service or self._combat_stat_service,
            )
            run.result_summary = None
            run.last_event_resolution = None
            return run

        success = self._determine_success(run, option_config)
        payload = self._parse_payload(
            option_config.result_on_success
            if success
            else option_config.result_on_failure
        )
        log_text = (
            option_config.log_text_success
            if success
            else option_config.log_text_failure
        )

        self._apply_payload(run, payload)
        self._apply_time_cost(run, option_config.time_cost_months)
        run.event_trigger_counts[template.event_id] = (
            run.event_trigger_counts.get(template.event_id, 0) + 1
        )
        if template.cooldown_rounds > 0:
            run.event_cooldowns[template.event_id] = template.cooldown_rounds
        if run.character.lifespan_current <= 0:
            run.character.lifespan_current = 0
            run.character.is_dead = True
        if run.character.hp_current <= 0:
            run.character.hp_current = 0
            run.character.is_dead = True

        base_summary = log_text or self._build_fallback_summary(
            run.current_event.event_name,
            option_config.option_text,
        )
        run.result_summary = self._build_result_summary(
            base_summary,
            option_config.time_cost_months,
        )
        run.last_event_resolution = EventResolutionLog(
            event_id=template.event_id,
            option_id=option_config.option_id,
            intended_resources=dict(payload.resources),
            intended_character=dict(payload.character),
            time_cost_months=option_config.time_cost_months,
        )
        run.current_event = None
        return run

    def _should_start_battle(self, option_config: EventOptionConfig) -> bool:
        if self._resolve_enemy_template(option_config) is not None:
            return True

        for payload_source in (
            option_config.result_on_success,
            option_config.result_on_failure,
        ):
            payload = self._parse_payload(payload_source)
            if payload.battle:
                return True

        return False

    def perform_battle_action(
        self,
        run: RunState,
        action: str,
        *,
        combat_service: CombatService | None = None,
        combat_stat_service: CombatStatService | None = None,
    ) -> RunState:
        if run.active_battle is None:
            raise ConflictError("there is no active battle")

        service = combat_service or self._combat_service
        before_pill_count = int(run.active_battle.pill_count)
        battle = service.perform_action(run.active_battle, action)
        if self._did_use_pill(action, before_pill_count, battle.pill_count):
            self._consume_battle_pill(run, before_pill_count - battle.pill_count)
            self._run_resource_service.add(run, "pill", -1)
            # Keep the aggregated pill counter aligned with inventory.
            run.resources.pill = sum(item.amount for item in run.alchemy_state.inventory)

        if not battle.is_finished:
            return run

        return self._finalize_battle(
            run,
            battle,
            combat_stat_service=combat_stat_service or self._combat_stat_service,
        )

    def _is_option_available(
        self,
        run: RunState,
        runtime_option: CurrentEventOption,
    ) -> bool:
        return (
            all(
                self._get_resource_amount(run, resource_name) >= amount
                for resource_name, amount in runtime_option.requires_resources.items()
            )
            and all(status in set(run.character.statuses) for status in runtime_option.requires_statuses)
            and all(
                technique in set(run.character.techniques)
                for technique in runtime_option.requires_techniques
            )
            and all(
                tag in set(run.character.equipment_tags)
                for tag in runtime_option.requires_equipment_tags
            )
        )

    def _determine_success(self, run: RunState, option_config: EventOptionConfig) -> bool:
        if option_config.resolution_mode == "direct":
            return True
        success_rate = self._evaluate_success_rate(run, option_config.success_rate_formula)
        return success_rate >= 0.5

    def _evaluate_success_rate(self, run: RunState, formula: str) -> float:
        realm_config = self._realm_configs.get(
            resolve_realm_key(run.character.realm, list(self._realm_configs.values()))
        )
        if realm_config is None:
            raise CoreLoopError(f"unknown realm '{run.character.realm}'")

        expression = formula or "base_success_rate"
        try:
            value = eval(  # noqa: S307 - config expressions are repository-owned input
                expression,
                {"__builtins__": {}},
                {
                    "base_success_rate": realm_config.base_success_rate,
                    "luck": run.character.luck,
                    "technique_bonus": run.character.technique_bonus,
                    "pill_bonus": run.character.pill_bonus,
                    "status_penalty": run.character.status_penalty,
                },
            )
        except Exception as error:  # pragma: no cover - defensive
            raise CoreLoopError(f"invalid success rate formula: {expression}") from error

        return max(0.0, min(1.0, float(value)))

    def _parse_payload(
        self,
        payload_config: str | dict[str, object] | EventResultPayload,
    ) -> EventResultPayload:
        if isinstance(payload_config, EventResultPayload):
            return payload_config

        if isinstance(payload_config, dict):
            if "resource_deltas" in payload_config:
                character: dict[str, int] = {}
                if "cultivation_exp_delta" in payload_config:
                    character["cultivation_exp"] = int(
                        payload_config.get("cultivation_exp_delta", 0)
                    )
                if "lifespan_delta" in payload_config:
                    character["lifespan_delta"] = int(payload_config.get("lifespan_delta", 0))
                return EventResultPayload(
                    resources={
                        self._normalize_resource_key(key): int(value)
                        for key, value in payload_config.get("resource_deltas", {}).items()
                    },
                    character=character,
                    death=bool(payload_config.get("death", False)),
                )
            return EventResultPayload(
                resources={
                    self._normalize_resource_key(key): int(value)
                    for key, value in payload_config.get("resources", {}).items()
                },
                character={
                    key: int(value)
                    for key, value in payload_config.get("character", {}).items()
                },
                statuses_add=list(payload_config.get("statuses_add", [])),
                statuses_remove=list(payload_config.get("statuses_remove", [])),
                techniques_add=list(payload_config.get("techniques_add", [])),
                learned_alchemy_recipe_ids=list(
                    payload_config.get("learned_alchemy_recipe_ids", [])
                ),
                equipment_add=list(payload_config.get("equipment_add", [])),
                equipment_remove=list(payload_config.get("equipment_remove", [])),
                battle=payload_config.get("battle"),
                death=bool(payload_config.get("death", False)),
                rebirth_progress_delta=int(payload_config.get("rebirth_progress_delta", 0)),
            )

        resources: dict[str, int] = {}
        character: dict[str, int] = {}
        death = False
        for token in filter(None, (item.strip() for item in payload_config.split(","))):
            key, _, raw_value = token.partition(":")
            if not _:
                raise CoreLoopError(f"invalid event payload token: {token}")

            normalized_key = key.strip()
            normalized_value = raw_value.strip()
            if normalized_key == "cultivation_exp":
                character["cultivation_exp"] = character.get("cultivation_exp", 0) + int(
                    normalized_value
                )
                continue
            if normalized_key == "lifespan":
                character["lifespan_delta"] = character.get("lifespan_delta", 0) + int(
                    normalized_value
                )
                continue
            if normalized_key == "death":
                death = normalized_value.lower() == "true"
                continue
            resources[self._normalize_resource_key(normalized_key)] = resources.get(
                self._normalize_resource_key(normalized_key),
                0,
            ) + int(
                normalized_value
            )

        return EventResultPayload(
            resources=resources,
            character=character,
            death=death,
        )

    def _apply_payload(self, run: RunState, payload: EventResultPayload) -> None:
        for resource_name, delta in payload.resources.items():
            if not self._run_resource_service.supports(resource_name):
                raise CoreLoopError(f"unknown resource '{resource_name}'")

        for resource_name, delta in payload.resources.items():
            self._run_resource_service.add(run, resource_name, delta)

        run.character.cultivation_exp = max(
            0,
            run.character.cultivation_exp + payload.character.get("cultivation_exp", 0),
        )
        run.character.lifespan_current = min(
            run.character.lifespan_max,
            max(0, run.character.lifespan_current + payload.character.get("lifespan_delta", 0)),
        )
        run.character.hp_current = min(
            run.character.hp_max,
            max(0, run.character.hp_current + payload.character.get("hp_delta", 0)),
        )
        run.character.breakthrough_bonus = max(
            0,
            run.character.breakthrough_bonus + payload.character.get("breakthrough_bonus", 0),
        )
        run.character.technique_exp = max(
            0,
            run.character.technique_exp + payload.character.get("technique_exp", 0),
        )
        run.character.luck = max(
            0,
            run.character.luck + payload.character.get("luck_delta", 0),
        )
        run.character.karma += payload.character.get("karma_delta", 0)
        run.character.rebirth_progress = max(
            0,
            run.character.rebirth_progress + payload.rebirth_progress_delta,
        )
        run.character.statuses = self._merge_tags(
            run.character.statuses,
            payload.statuses_add,
            payload.statuses_remove,
        )
        run.character.techniques = self._merge_tags(
            run.character.techniques,
            payload.techniques_add,
            [],
        )
        run.alchemy_state.learned_recipe_ids = self._merge_tags(
            run.alchemy_state.learned_recipe_ids,
            payload.learned_alchemy_recipe_ids,
            [],
        )
        run.character.equipment_tags = self._merge_tags(
            run.character.equipment_tags,
            payload.equipment_add,
            payload.equipment_remove,
        )

        if payload.death:
            run.character.is_dead = True
            run.character.lifespan_current = 0

    def _apply_time_cost(self, run: RunState, time_cost_months: int) -> None:
        if time_cost_months <= 0:
            return
        run.character.lifespan_current = max(
            0,
            run.character.lifespan_current - int(time_cost_months),
        )

    def _start_combat_event(
        self,
        run: RunState,
        *,
        option_config: EventOptionConfig,
        template: RealmConfig | object,
        combat_service: CombatService,
        combat_stat_service: CombatStatService,
    ) -> None:
        success_payload = self._parse_payload(option_config.result_on_success)
        failure_payload = self._parse_payload(option_config.result_on_failure)
        enemy_template = self._resolve_enemy_template(option_config)
        battle_payload = success_payload.battle or failure_payload.battle
        if enemy_template is None and not battle_payload:
            raise ConflictError("combat option is missing battle configuration")

        player_state = combat_stat_service.build_player_state(run)
        enemy_state = self._build_combat_enemy_state(enemy_template or battle_payload or {})
        allow_flee = (
            bool(enemy_template.get("allow_flee"))
            if enemy_template is not None
            else bool((battle_payload or {}).get("allow_flee", True))
        )
        flee_base_rate = (
            self._DEFAULT_FLEE_BASE_RATE
            if enemy_template is not None
            else float((battle_payload or {}).get("flee_base_rate", self._DEFAULT_FLEE_BASE_RATE))
        )
        pill_heal_amount = (
            self._DEFAULT_PILL_HEAL_AMOUNT
            if enemy_template is not None
            else int((battle_payload or {}).get("pill_heal_amount", self._DEFAULT_PILL_HEAL_AMOUNT))
        )
        run.active_battle = combat_service.start_battle(
            source_event_id=option_config.event_id,
            source_option_id=option_config.option_id,
            player=player_state,
            enemy=enemy_state,
            allow_flee=allow_flee,
            flee_base_rate=flee_base_rate,
            pill_heal_amount=pill_heal_amount,
            pill_count=max(0, int(getattr(run.resources, "pill", 0))),
        )

    def _finalize_battle(
        self,
        run: RunState,
        battle: ActiveBattleState,
        *,
        combat_stat_service: CombatStatService,
    ) -> RunState:
        if not battle.is_finished:
            return run

        option_config = self._registry.options.get(battle.source_option_id)
        if option_config is None:
            raise ConflictError(f"option '{battle.source_option_id}' is not registered")
        template = self._registry.templates.get(option_config.event_id)
        if template is None:
            raise ConflictError(f"event '{option_config.event_id}' is not registered")

        outcome = battle.result
        if outcome == "victory":
            payload = self._resolve_combat_victory_payload(option_config)
            base_summary = self._resolve_combat_summary(
                template.event_name,
                option_config,
                payload,
                "victory",
            )
        elif outcome == "defeat":
            payload = self._parse_payload(option_config.result_on_failure)
            base_summary = self._resolve_combat_summary(
                template.event_name,
                option_config,
                payload,
                "defeat",
            )
        elif outcome == "flee_success":
            battle_payload = self._get_combat_battle_payload(option_config)
            payload = EventResultPayload(battle=battle_payload)
            base_summary = self._resolve_combat_summary(
                template.event_name,
                option_config,
                payload,
                "flee_success",
            )
        else:
            raise ConflictError("battle is not finished")

        run.character.hp_current = min(
            run.character.hp_max,
            max(0, int(battle.player.hp_current)),
        )
        self._apply_payload(run, payload)
        self._apply_time_cost(run, option_config.time_cost_months)
        run.event_trigger_counts[template.event_id] = (
            run.event_trigger_counts.get(template.event_id, 0) + 1
        )
        if template.cooldown_rounds > 0:
            run.event_cooldowns[template.event_id] = template.cooldown_rounds
        if run.character.lifespan_current <= 0:
            run.character.lifespan_current = 0
            run.character.is_dead = True
        if run.character.hp_current <= 0:
            run.character.hp_current = 0
            run.character.is_dead = True

        run.result_summary = (
            base_summary
            if outcome == "flee_success"
            else self._build_result_summary(base_summary, option_config.time_cost_months)
        )
        run.last_event_resolution = EventResolutionLog(
            event_id=template.event_id,
            option_id=option_config.option_id,
            intended_resources=dict(payload.resources),
            intended_character=dict(payload.character),
            time_cost_months=option_config.time_cost_months,
        )
        run.current_event = None
        run.active_battle = None
        return run

    def _build_combat_enemy_state(self, battle_payload: dict[str, object]) -> CombatActorState:
        return CombatActorState(
            name=str(battle_payload.get("enemy_name", "enemy")),
            realm_label=str(battle_payload.get("enemy_realm_label", "enemy")),
            hp_current=max(1, int(battle_payload.get("enemy_hp", 1))),
            hp_max=max(1, int(battle_payload.get("enemy_hp", 1))),
            attack=max(0, int(battle_payload.get("enemy_attack", 0))),
            defense=max(0, int(battle_payload.get("enemy_defense", 0))),
            speed=max(0, int(battle_payload.get("enemy_speed", 0))),
        )

    def _resolve_combat_victory_payload(self, option_config: EventOptionConfig) -> EventResultPayload:
        enemy_template = self._resolve_enemy_template(option_config)
        if enemy_template is not None:
            return self._parse_payload(enemy_template.get("rewards", {}))
        return self._parse_payload(option_config.result_on_success)

    def _resolve_enemy_template(
        self,
        option_config: EventOptionConfig,
    ) -> dict[str, object] | None:
        enemy_template_id = (option_config.enemy_template_id or "").strip()
        if not enemy_template_id:
            return None
        enemy_template = self._enemy_templates.get(enemy_template_id)
        if enemy_template is None:
            raise ConflictError(f"enemy template '{enemy_template_id}' is not registered")
        return enemy_template

    def _get_combat_battle_payload(
        self,
        option_config: EventOptionConfig,
    ) -> dict[str, object]:
        enemy_template = self._resolve_enemy_template(option_config)
        if enemy_template is not None:
            return {
                "enemy_name": enemy_template.get("enemy_name", ""),
                "enemy_realm_label": enemy_template.get("enemy_realm_label", ""),
                "enemy_hp": enemy_template.get("enemy_hp", 1),
                "enemy_attack": enemy_template.get("enemy_attack", 0),
                "enemy_defense": enemy_template.get("enemy_defense", 0),
                "enemy_speed": enemy_template.get("enemy_speed", 0),
                "allow_flee": enemy_template.get("allow_flee", True),
            }
        for payload_source in (
            option_config.result_on_success,
            option_config.result_on_failure,
        ):
            payload = self._parse_payload(payload_source)
            if payload.battle:
                return dict(payload.battle)
        return {}

    def _resolve_combat_summary(
        self,
        event_name: str,
        option_config: EventOptionConfig,
        payload: EventResultPayload,
        outcome: str,
    ) -> str:
        battle_payload = payload.battle or {}
        if outcome == "victory":
            candidates = [
                str(battle_payload.get("victory_log", "")).strip(),
                option_config.log_text_success.strip(),
                option_config.log_text_failure.strip(),
            ]
        elif outcome == "defeat":
            candidates = [
                str(battle_payload.get("defeat_log", "")).strip(),
                option_config.log_text_failure.strip(),
                option_config.log_text_success.strip(),
            ]
        else:
            candidates = [
                str(battle_payload.get("flee_success_log", "")).strip(),
                option_config.log_text_success.strip(),
                option_config.log_text_failure.strip(),
            ]

        for candidate in candidates:
            if candidate:
                return candidate
        return self._build_fallback_summary(event_name, option_config.option_text)

    def _did_use_pill(
        self,
        action: str,
        before_pill_count: int,
        after_pill_count: int,
    ) -> bool:
        return (
            action.strip().lower() == "use_pill"
            and before_pill_count > after_pill_count
        )

    def _consume_battle_pill(self, run: RunState, amount: int) -> None:
        if amount <= 0:
            return

        remaining = amount
        for item in list(run.alchemy_state.inventory):
            if remaining <= 0:
                break
            if item.amount <= 0:
                continue
            consumed = min(item.amount, remaining)
            item.amount -= consumed
            remaining -= consumed

        run.alchemy_state.inventory = [
            item for item in run.alchemy_state.inventory if item.amount > 0
        ]

    def _build_result_summary(self, base_summary: str, time_cost_months: int) -> str:
        if time_cost_months <= 0:
            return base_summary
        return f"{base_summary}（额外耗时{time_cost_months}个月）"

    def _merge_tags(
        self,
        current_values: list[str],
        values_to_add: list[str],
        values_to_remove: list[str],
    ) -> list[str]:
        merged = [value for value in current_values if value not in set(values_to_remove)]
        for value in values_to_add:
            if value not in merged:
                merged.append(value)
        return merged

    def _normalize_resource_key(self, resource_name: str) -> str:
        aliases = {
            "herbs": "herb",
            "iron_essence": "ore",
        }
        return aliases.get(resource_name, resource_name)

    def _resolve_resource_name(self, resource_name: str) -> str | None:
        normalized_name = self._normalize_resource_key(resource_name)
        if normalized_name == "herb":
            return "herbs"
        if normalized_name == "ore":
            return "ore"
        allowed_names = {
            "spirit_stone",
            "beast_material",
            "pill",
            "craft_material",
        }
        return normalized_name if normalized_name in allowed_names else None

    def _get_resource_amount(self, run: RunState, resource_name: str) -> int:
        normalized_name = self._normalize_resource_key(resource_name)
        if normalized_name == "herb":
            return getattr(run.resources, "herbs", 0)
        if normalized_name == "ore":
            return max(getattr(run.resources, "ore", 0), getattr(run.resources, "iron_essence", 0))
        return getattr(run.resources, normalized_name, 0)

    def _set_resource_amount(self, run: RunState, resource_name: str, amount: int) -> None:
        normalized_name = self._normalize_resource_key(resource_name)
        if normalized_name == "herb":
            run.resources.herbs = amount
            return
        if normalized_name == "ore":
            run.resources.ore = amount
            run.resources.iron_essence = amount
            return
        setattr(run.resources, normalized_name, amount)

    def _build_fallback_summary(self, event_name: str, option_text: str) -> str:
        return f"{event_name}: {option_text}"
