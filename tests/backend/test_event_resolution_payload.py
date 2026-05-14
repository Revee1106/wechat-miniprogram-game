from app.core_loop.event_config import EventRegistry
from app.core_loop.services.event_resolution_service import EventResolutionService
from app.core_loop.services.event_service import EventService
from app.core_loop.types import (
    CharacterState,
    AlchemyInventoryItem,
    EventOptionConfig,
    EventResultPayload,
    EventTemplateConfig,
    ResourceState,
    RunState,
)


def _build_run() -> RunState:
    return RunState(
        run_id="run-test",
        player_id="player-test",
        round_index=1,
        character=CharacterState(
            name="player-test-wanderer",
            realm="qi_refining",
            cultivation_exp=0,
            lifespan_current=120,
            lifespan_max=240,
            luck=0,
        ),
        resources=ResourceState(
            spirit_stone=20,
            herbs=3,
            iron_essence=0,
        ),
    )


def test_resolve_event_applies_success_payload_and_summary() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="cultivation",
                option_ids=["opt_payload_gain"],
            )
        },
        options={
            "opt_payload_gain": EventOptionConfig(
                option_id="opt_payload_gain",
                event_id="evt_payload",
                option_text="Take the gain",
                is_default=True,
                success_rate_formula="1.0",
                result_on_success=EventResultPayload(
                    resources={"spirit_stone": 2, "herb": 1},
                    character={
                        "cultivation_exp": 4,
                        "lifespan_delta": 3,
                        "karma_delta": 2,
                        "luck_delta": 1,
                        "technique_exp": 5,
                    },
                    statuses_add=["focused"],
                    techniques_add=["cloud_step"],
                    learned_alchemy_recipe_ids=["ning_qi_dan"],
                    unlocked_material_ids=["herb_julingzhi"],
                    alchemy_mastery_exp_delta=12,
                    equipment_add=["jade_token"],
                    rebirth_progress_delta=2,
                ),
                result_on_failure=EventResultPayload(),
                log_text_success="success log",
                log_text_failure="failure log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_payload_gain")

    assert resolved.current_event is None
    assert resolved.character.cultivation_exp == 4
    assert resolved.resources.spirit_stone == 22
    assert resolved.resources.herbs == 4
    assert resolved.character.lifespan_current == 123
    assert resolved.character.karma == 2
    assert resolved.character.luck == 1
    assert resolved.character.technique_exp == 5
    assert resolved.character.rebirth_progress == 2
    assert resolved.character.statuses == ["focused"]
    assert resolved.character.techniques == ["cloud_step"]
    assert resolved.alchemy_state.learned_recipe_ids == ["ning_qi_dan"]
    assert resolved.unlocked_material_ids == ["herb_julingzhi"]
    assert resolved.alchemy_state.mastery_exp == 12
    assert resolved.character.equipment_tags == ["jade_token"]
    assert resolved.result_summary == "success log 你学会了凝气丹丹方。 你解锁了聚灵芝材料。"


def test_resolve_event_applies_progress_counter_deltas() -> None:
    registry = EventRegistry(
        templates={
            "evt_progress": EventTemplateConfig(
                event_id="evt_progress",
                event_name="Progress Event",
                event_type="alchemy",
                option_ids=["opt_progress"],
            )
        },
        options={
            "opt_progress": EventOptionConfig(
                option_id="opt_progress",
                event_id="evt_progress",
                option_text="Record progress",
                is_default=True,
                resolution_mode="direct",
                result_on_success=EventResultPayload(
                    progress_counter_deltas={
                        "alchemy.ning_qi_dan_clue": 1,
                        "alchemy.npc_lingyao_approval": 20,
                    }
                ),
                log_text_success="progress log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_progress")

    assert resolved.progress_counters["alchemy.ning_qi_dan_clue"] == 1
    assert resolved.progress_counters["alchemy.npc_lingyao_approval"] == 20


def test_resolve_event_clamps_progress_counter_deltas_at_zero() -> None:
    registry = EventRegistry(
        templates={
            "evt_progress": EventTemplateConfig(
                event_id="evt_progress",
                event_name="Progress Event",
                event_type="alchemy",
                option_ids=["opt_progress"],
            )
        },
        options={
            "opt_progress": EventOptionConfig(
                option_id="opt_progress",
                event_id="evt_progress",
                option_text="Spend progress",
                is_default=True,
                resolution_mode="direct",
                result_on_success=EventResultPayload(
                    progress_counter_deltas={"alchemy.ning_qi_dan_clue": -5}
                ),
                log_text_success="progress log",
            )
        },
    )
    run = _build_run()
    run.progress_counters = {"alchemy.ning_qi_dan_clue": 1}
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_progress")

    assert resolved.progress_counters["alchemy.ning_qi_dan_clue"] == 0


def test_direct_resolution_mode_always_uses_single_result_without_formula() -> None:
    registry = EventRegistry(
        templates={
            "evt_direct": EventTemplateConfig(
                event_id="evt_direct",
                event_name="Direct Event",
                event_type="cultivation",
                option_ids=["opt_direct"],
            )
        },
        options={
            "opt_direct": EventOptionConfig(
                option_id="opt_direct",
                event_id="evt_direct",
                option_text="Take the direct path",
                is_default=True,
                resolution_mode="direct",
                success_rate_formula="0.0",
                result_on_success=EventResultPayload(character={"cultivation_exp": 6}),
                result_on_failure=EventResultPayload(character={"lifespan_delta": -999}, death=True),
                log_text_success="direct log",
                log_text_failure="failure log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_direct")

    assert resolved.character.cultivation_exp == 6
    assert resolved.character.is_dead is False
    assert resolved.result_summary == "direct log"


def test_resolve_event_unlocks_configured_next_event() -> None:
    registry = EventRegistry(
        templates={
            "evt_source": EventTemplateConfig(
                event_id="evt_source",
                event_name="Source Event",
                event_type="encounter",
                option_ids=["opt_unlock_next"],
            ),
            "evt_next": EventTemplateConfig(
                event_id="evt_next",
                event_name="Next Event",
                event_type="encounter",
                option_ids=["opt_next"],
            ),
        },
        options={
            "opt_unlock_next": EventOptionConfig(
                option_id="opt_unlock_next",
                event_id="evt_source",
                option_text="Unlock next",
                is_default=True,
                resolution_mode="direct",
                next_event_id="evt_next",
                log_text_success="unlocked",
            ),
            "opt_next": EventOptionConfig(
                option_id="opt_next",
                event_id="evt_next",
                option_text="Next option",
                is_default=True,
            ),
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_unlock_next")

    assert resolved.unlocked_event_ids == ["evt_next"]


def test_resolve_event_applies_failure_death_payload() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="survival",
                option_ids=["opt_payload_death"],
            )
        },
        options={
            "opt_payload_death": EventOptionConfig(
                option_id="opt_payload_death",
                event_id="evt_payload",
                option_text="Take the risk",
                is_default=True,
                success_rate_formula="0.0",
                result_on_success=EventResultPayload(
                    character={"cultivation_exp": 1},
                ),
                result_on_failure=EventResultPayload(
                    character={"lifespan_delta": -999},
                    death=True,
                ),
                log_text_success="success log",
                log_text_failure="death log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_payload_death")

    assert resolved.current_event is None
    assert resolved.character.is_dead is True
    assert resolved.result_summary == "death log"


def test_resolve_event_does_not_partially_mutate_run_on_invalid_payload() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="material",
                option_ids=["opt_payload_invalid"],
            )
        },
        options={
            "opt_payload_invalid": EventOptionConfig(
                option_id="opt_payload_invalid",
                event_id="evt_payload",
                option_text="Break the payload",
                is_default=True,
                success_rate_formula="1.0",
                result_on_success=EventResultPayload(
                    resources={"spirit_stone": 2, "unknown_resource": 1}
                ),
                log_text_success="success log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)
    before_spirit_stone = run.resources.spirit_stone
    before_cultivation = run.character.cultivation_exp

    try:
        EventResolutionService(registry=registry).resolve(run, "opt_payload_invalid")
    except Exception as error:
        assert "unknown resource" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected invalid payload to fail")

    assert run.resources.spirit_stone == before_spirit_stone
    assert run.character.cultivation_exp == before_cultivation


def test_resolve_event_applies_failure_payload_status_cleanup_and_cooldown_tracking() -> None:
    registry = EventRegistry(
        templates={
            "evt_payload": EventTemplateConfig(
                event_id="evt_payload",
                event_name="Payload Event",
                event_type="survival",
                option_ids=["opt_payload_fail"],
                cooldown_rounds=3,
                max_trigger_per_run=2,
            )
        },
        options={
            "opt_payload_fail": EventOptionConfig(
                option_id="opt_payload_fail",
                event_id="evt_payload",
                option_text="Fail forward",
                is_default=True,
                success_rate_formula="0.0",
                result_on_success=EventResultPayload(),
                result_on_failure=EventResultPayload(
                    character={"hp_delta": -5, "lifespan_delta": -2},
                    statuses_remove=["injured"],
                    equipment_remove=["jade_token"],
                ),
                log_text_failure="failure log",
            )
        },
    )
    run = _build_run()
    run.character.statuses = ["injured", "focused"]
    run.character.equipment_tags = ["jade_token", "wood_amulet"]
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_payload_fail")

    assert resolved.character.lifespan_current == 118
    assert resolved.character.statuses == ["focused"]
    assert resolved.character.equipment_tags == ["wood_amulet"]
    assert resolved.event_trigger_counts["evt_payload"] == 1
    assert resolved.event_cooldowns["evt_payload"] == 3


def test_resolve_event_applies_time_cost_months_as_extra_lifespan_loss_only() -> None:
    registry = EventRegistry(
        templates={
            "evt_time_cost": EventTemplateConfig(
                event_id="evt_time_cost",
                event_name="Time Cost Event",
                event_type="cultivation",
                option_ids=["opt_time_cost"],
            )
        },
        options={
            "opt_time_cost": EventOptionConfig(
                option_id="opt_time_cost",
                event_id="evt_time_cost",
                option_text="Spend extra time",
                is_default=True,
                resolution_mode="direct",
                time_cost_months=3,
                result_on_success=EventResultPayload(character={"cultivation_exp": 2}),
                log_text_success="time cost log",
            )
        },
    )
    run = _build_run()
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)
    before_round_index = run.round_index

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_time_cost")

    assert resolved.character.cultivation_exp == 2
    assert resolved.character.lifespan_current == 117
    assert resolved.round_index == before_round_index
    assert resolved.result_summary == "time cost log（额外耗时3个月）"


def test_resolve_combat_event_enters_active_battle_without_applying_payload() -> None:
    registry = EventRegistry(
        templates={
            "evt_combat": EventTemplateConfig(
                event_id="evt_combat",
                event_name="Combat Event",
                event_type="encounter",
                option_ids=["opt_combat"],
            )
        },
        options={
            "opt_combat": EventOptionConfig(
                option_id="opt_combat",
                event_id="evt_combat",
                option_text="Fight",
                is_default=True,
                resolution_mode="combat",
                time_cost_months=2,
                result_on_success=EventResultPayload(
                    resources={"spirit_stone": 7},
                    character={"cultivation_exp": 5},
                    battle={
                        "enemy_name": "山匪",
                        "enemy_realm_label": "炼气初期",
                        "enemy_hp": 1,
                        "enemy_attack": 1,
                        "enemy_defense": 0,
                        "enemy_speed": 1,
                        "allow_flee": True,
                        "flee_base_rate": 0.35,
                        "pill_heal_amount": 12,
                    },
                ),
                result_on_failure=EventResultPayload(),
                log_text_success="victory log",
                log_text_failure="defeat log",
            )
        },
    )
    run = _build_run()
    run.resources.spirit_stone = 17
    run.resources.pill = 1
    run.alchemy_state.inventory = [
        AlchemyInventoryItem(
            item_id="yang_yuan_dan",
            display_name="养元丹",
            quality="low",
            amount=1,
            effect_summary="恢复气血",
            effect_type="hp_restore",
            effect_value=25,
            usable_in_battle=True,
        )
    ]
    run.current_event = EventService(registry=registry).select_event(run, rebirth_count=0)

    resolved = EventResolutionService(registry=registry).resolve(run, "opt_combat")

    assert resolved.current_event is not None
    assert resolved.active_battle is not None
    assert resolved.active_battle.source_event_id == "evt_combat"
    assert resolved.active_battle.source_option_id == "opt_combat"
    assert resolved.active_battle.is_finished is False
    assert resolved.active_battle.result is None
    assert resolved.active_battle.pill_count == 1
    assert resolved.character.cultivation_exp == 0
    assert resolved.resources.spirit_stone == 17
    assert resolved.resources.pill == 1
