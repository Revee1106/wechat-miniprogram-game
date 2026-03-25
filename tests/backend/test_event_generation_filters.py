from app.core_loop.event_config import EventRegistry
from app.core_loop.services.event_service import EventService
from app.core_loop.services.time_advance_service import TimeAdvanceService
from app.core_loop.types import ConflictError
from app.core_loop.types import (
    CharacterState,
    EventOptionConfig,
    EventTemplateConfig,
    ResourceState,
    RunState,
)


class _StubRng:
    def __init__(self, chosen_type: str, chosen_event_id: str) -> None:
        self.chosen_type = chosen_type
        self.chosen_event_id = chosen_event_id

    def choice(self, values):
        first_value = values[0]
        if isinstance(first_value, str):
            return self.chosen_type
        for value in values:
            if getattr(value, "event_id", None) == self.chosen_event_id:
                return value
        raise AssertionError("requested event_id not found in rng candidates")


class _WeightedStubRng:
    def __init__(self, chosen_type: str, chosen_event_id: str) -> None:
        self.chosen_type = chosen_type
        self.chosen_event_id = chosen_event_id
        self.recorded_type_weights: list[int] | None = None
        self.recorded_event_weights: list[int] | None = None

    def choice(self, values):
        first_value = values[0]
        if isinstance(first_value, str):
            return self.chosen_type
        raise AssertionError("expected weighted event selection via choices()")

    def choices(self, population, weights, k):
        assert k == 1
        first_value = population[0]
        if isinstance(first_value, str):
            self.recorded_type_weights = list(weights)
            return [self.chosen_type]

        self.recorded_event_weights = list(weights)
        for value in population:
            if getattr(value, "event_id", None) == self.chosen_event_id:
                return [value]
        raise AssertionError("requested weighted event_id not found in rng candidates")


def _build_run() -> RunState:
    return RunState(
        run_id="run-test",
        player_id="player-test",
        round_index=1,
        character=CharacterState(
            name="player-test-wanderer",
            realm="qi_refining",
            cultivation_exp=0,
            lifespan_current=240,
            lifespan_max=240,
            luck=0,
        ),
        resources=ResourceState(
            spirit_stone=20,
            herbs=3,
            iron_essence=0,
        ),
    )


def _build_registry(*templates: EventTemplateConfig) -> EventRegistry:
    options = {
        option.option_id: option
        for template in templates
        for option in [
            EventOptionConfig(
                option_id=template.option_ids[0],
                event_id=template.event_id,
                option_text=f"{template.event_id}-option",
                is_default=True,
            )
        ]
    }
    return EventRegistry(
        templates={template.event_id: template for template in templates},
        options=options,
    )


def test_event_selection_skips_realm_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_foundation_only",
                event_name="Foundation Only",
                event_type="cultivation",
                option_ids=["opt_foundation_only"],
                realm_min="foundation",
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="cultivation",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_resource_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_needs_herbs",
                event_name="Needs Herbs",
                event_type="material",
                option_ids=["opt_needs_herbs"],
                required_resources={"herbs": 5},
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="material",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_luck_and_rebirth_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_needs_meta_progress",
                event_name="Meta Progress",
                event_type="encounter",
                option_ids=["opt_needs_meta_progress"],
                required_rebirth_count=1,
                required_luck_min=3,
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="encounter",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_status_technique_equipment_and_karma_blocked_templates() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_needs_build",
                event_name="Needs Build",
                event_type="encounter",
                option_ids=["opt_needs_build"],
                required_statuses=["focused"],
                excluded_statuses=["injured"],
                required_techniques=["cloud_step"],
                required_equipment_tags=["jade_token"],
                required_karma_min=2,
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="encounter",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_templates_on_cooldown_or_trigger_cap() -> None:
    service = EventService(
        registry=_build_registry(
            EventTemplateConfig(
                event_id="evt_capped",
                event_name="Capped",
                event_type="cultivation",
                option_ids=["opt_capped"],
                is_repeatable=True,
                cooldown_rounds=2,
                max_trigger_per_run=1,
            ),
            EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="cultivation",
                option_ids=["opt_fallback"],
            ),
        )
    )
    run = _build_run()
    run.event_cooldowns["evt_capped"] = 1
    run.event_trigger_counts["evt_capped"] = 1

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_selection_skips_templates_with_no_available_options() -> None:
    registry = EventRegistry(
        templates={
            "evt_blocked": EventTemplateConfig(
                event_id="evt_blocked",
                event_name="Blocked",
                event_type="material",
                option_ids=["opt_blocked"],
            ),
            "evt_fallback": EventTemplateConfig(
                event_id="evt_fallback",
                event_name="Fallback",
                event_type="material",
                option_ids=["opt_fallback"],
            ),
        },
        options={
            "opt_blocked": EventOptionConfig(
                option_id="opt_blocked",
                event_id="evt_blocked",
                option_text="Blocked option",
                requires_resources={"herbs": 99},
                is_default=True,
            ),
            "opt_fallback": EventOptionConfig(
                option_id="opt_fallback",
                event_id="evt_fallback",
                option_text="Fallback option",
                is_default=True,
            ),
        },
    )
    run = _build_run()

    selected = EventService(registry=registry).select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_fallback"


def test_event_runtime_option_availability_checks_all_gate_types() -> None:
    registry = EventRegistry(
        templates={
            "evt_option_gates": EventTemplateConfig(
                event_id="evt_option_gates",
                event_name="Option Gates",
                event_type="technique",
                option_ids=["opt_gated", "opt_fallback"],
            ),
        },
        options={
            "opt_gated": EventOptionConfig(
                option_id="opt_gated",
                event_id="evt_option_gates",
                option_text="Gated",
                requires_resources={"spirit_stone": 99},
                requires_statuses=["focused"],
                requires_techniques=["cloud_step"],
                requires_equipment_tags=["jade_token"],
                is_default=True,
            ),
            "opt_fallback": EventOptionConfig(
                option_id="opt_fallback",
                event_id="evt_option_gates",
                option_text="Fallback",
                is_default=False,
            ),
        },
    )
    run = _build_run()

    selected = EventService(registry=registry).select_event(run, rebirth_count=0)

    gated_option = next(option for option in selected.options if option.option_id == "opt_gated")
    assert gated_option.is_available is False
    assert gated_option.disabled_reason


def test_event_selection_randomizes_type_before_selecting_event() -> None:
    registry = EventRegistry(
        templates={
            "evt_cultivation": EventTemplateConfig(
                event_id="evt_cultivation",
                event_name="Cultivation",
                event_type="cultivation",
                option_ids=["opt_cultivation"],
            ),
            "evt_material_one": EventTemplateConfig(
                event_id="evt_material_one",
                event_name="Material One",
                event_type="material",
                option_ids=["opt_material_one"],
            ),
            "evt_material_two": EventTemplateConfig(
                event_id="evt_material_two",
                event_name="Material Two",
                event_type="material",
                option_ids=["opt_material_two"],
            ),
        },
        options={
            "opt_cultivation": EventOptionConfig(
                option_id="opt_cultivation",
                event_id="evt_cultivation",
                option_text="Cultivation Option",
                is_default=True,
            ),
            "opt_material_one": EventOptionConfig(
                option_id="opt_material_one",
                event_id="evt_material_one",
                option_text="Material One Option",
                is_default=True,
            ),
            "opt_material_two": EventOptionConfig(
                option_id="opt_material_two",
                event_id="evt_material_two",
                option_text="Material Two Option",
                is_default=True,
            ),
        },
    )
    run = _build_run()
    service = EventService(
        registry=registry,
        rng=_StubRng(chosen_type="material", chosen_event_id="evt_material_two"),
    )

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_type == "material"
    assert selected.event_id == "evt_material_two"


def test_event_selection_uses_weighted_choice_within_selected_type() -> None:
    registry = EventRegistry(
        templates={
            "evt_cultivation": EventTemplateConfig(
                event_id="evt_cultivation",
                event_name="Cultivation",
                event_type="cultivation",
                option_ids=["opt_cultivation"],
                weight=99,
            ),
            "evt_material_light": EventTemplateConfig(
                event_id="evt_material_light",
                event_name="Material Light",
                event_type="material",
                option_ids=["opt_material_light"],
                weight=1,
            ),
            "evt_material_heavy": EventTemplateConfig(
                event_id="evt_material_heavy",
                event_name="Material Heavy",
                event_type="material",
                option_ids=["opt_material_heavy"],
                weight=7,
            ),
        },
        options={
            "opt_cultivation": EventOptionConfig(
                option_id="opt_cultivation",
                event_id="evt_cultivation",
                option_text="Cultivation Option",
                is_default=True,
            ),
            "opt_material_light": EventOptionConfig(
                option_id="opt_material_light",
                event_id="evt_material_light",
                option_text="Material Light Option",
                is_default=True,
            ),
            "opt_material_heavy": EventOptionConfig(
                option_id="opt_material_heavy",
                event_id="evt_material_heavy",
                option_text="Material Heavy Option",
                is_default=True,
            ),
        },
    )
    run = _build_run()
    rng = _WeightedStubRng(
        chosen_type="material",
        chosen_event_id="evt_material_heavy",
    )
    service = EventService(registry=registry, rng=rng)

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_type == "material"
    assert selected.event_id == "evt_material_heavy"
    assert rng.recorded_event_weights == [1, 7]


def test_event_selection_uses_weighted_choice_for_event_types() -> None:
    registry = EventRegistry(
        templates={
            "evt_cultivation": EventTemplateConfig(
                event_id="evt_cultivation",
                event_name="Cultivation",
                event_type="cultivation",
                option_ids=["opt_cultivation"],
                weight=2,
            ),
            "evt_material_light": EventTemplateConfig(
                event_id="evt_material_light",
                event_name="Material Light",
                event_type="material",
                option_ids=["opt_material_light"],
                weight=1,
            ),
            "evt_material_heavy": EventTemplateConfig(
                event_id="evt_material_heavy",
                event_name="Material Heavy",
                event_type="material",
                option_ids=["opt_material_heavy"],
                weight=7,
            ),
        },
        options={
            "opt_cultivation": EventOptionConfig(
                option_id="opt_cultivation",
                event_id="evt_cultivation",
                option_text="Cultivation Option",
                is_default=True,
            ),
            "opt_material_light": EventOptionConfig(
                option_id="opt_material_light",
                event_id="evt_material_light",
                option_text="Material Light Option",
                is_default=True,
            ),
            "opt_material_heavy": EventOptionConfig(
                option_id="opt_material_heavy",
                event_id="evt_material_heavy",
                option_text="Material Heavy Option",
                is_default=True,
            ),
        },
    )
    run = _build_run()
    rng = _WeightedStubRng(
        chosen_type="material",
        chosen_event_id="evt_material_heavy",
    )
    service = EventService(registry=registry, rng=rng)

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_type == "material"
    assert selected.event_id == "evt_material_heavy"
    assert rng.recorded_type_weights == [2, 8]


def test_event_selection_excludes_evil_cultist_from_random_pool() -> None:
    registry = EventRegistry(
        templates={
            "evt_evil_cultist_012": EventTemplateConfig(
                event_id="evt_evil_cultist_012",
                event_name="Evil Cultist",
                event_type="survival",
                option_ids=["opt_evil_cultist"],
            ),
            "evt_safe_fallback": EventTemplateConfig(
                event_id="evt_safe_fallback",
                event_name="Safe Fallback",
                event_type="cultivation",
                option_ids=["opt_safe_fallback"],
            ),
        },
        options={
            "opt_evil_cultist": EventOptionConfig(
                option_id="opt_evil_cultist",
                event_id="evt_evil_cultist_012",
                option_text="Risk",
                is_default=True,
            ),
            "opt_safe_fallback": EventOptionConfig(
                option_id="opt_safe_fallback",
                event_id="evt_safe_fallback",
                option_text="Safe",
                is_default=True,
            ),
        },
    )
    run = _build_run()
    service = EventService(
        registry=registry,
        rng=_StubRng(chosen_type="cultivation", chosen_event_id="evt_safe_fallback"),
    )

    selected = service.select_event(run, rebirth_count=0)

    assert selected.event_id == "evt_safe_fallback"


def test_time_advance_does_not_mutate_run_when_no_event_is_eligible() -> None:
    registry = EventRegistry(
        templates={
            "evt_blocked": EventTemplateConfig(
                event_id="evt_blocked",
                event_name="Blocked",
                event_type="material",
                option_ids=["opt_blocked"],
                required_resources={"herbs": 99},
            ),
        },
        options={
            "opt_blocked": EventOptionConfig(
                option_id="opt_blocked",
                event_id="evt_blocked",
                option_text="Blocked option",
                requires_resources={"herbs": 99},
                is_default=True,
            ),
        },
    )
    run = _build_run()
    before_round = run.round_index
    before_lifespan = run.character.lifespan_current

    try:
        TimeAdvanceService(EventService(registry=registry)).advance(run, rebirth_count=0)
    except ConflictError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("expected advance to fail when no config event is eligible")

    assert run.round_index == before_round
    assert run.character.lifespan_current == before_lifespan
    assert run.current_event is None
