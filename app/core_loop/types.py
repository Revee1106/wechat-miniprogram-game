from __future__ import annotations

from dataclasses import dataclass, field


class CoreLoopError(Exception):
    """Base domain error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "core.unknown",
        params: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.params = dict(params or {})


class NotFoundError(CoreLoopError):
    """Raised when an entity cannot be found."""


class ConflictError(CoreLoopError):
    """Raised when a requested action conflicts with run state."""


@dataclass(frozen=True)
class RealmConfig:
    key: str
    display_name: str
    major_realm: str
    stage_index: int
    order_index: int
    lifespan_bonus: int
    base_success_rate: float
    required_exp: int
    required_spirit_stone: int
    base_cultivation_gain_per_advance: int = 0
    base_spirit_stone_cost_per_advance: int = 0
    required_materials: dict[str, int] = field(default_factory=dict)
    failure_penalty: dict[str, dict[str, int]] = field(default_factory=dict)
    is_enabled: bool = True


@dataclass(frozen=True)
class BreakthroughRequirements:
    target_realm_key: str
    target_realm_display_name: str
    required_cultivation_exp: int
    required_spirit_stone: int


@dataclass(frozen=True)
class EventChoice:
    key: str
    display_name: str
    description: str
    spirit_stone_delta: int = 0
    herbs_delta: int = 0
    cultivation_exp_delta: int = 0
    lifespan_delta: int = 0
    death_chance: float = 0.0


@dataclass(frozen=True)
class EventTemplate:
    key: str
    display_name: str
    description: str
    realm_keys: list[str]
    weight: int
    region: str
    choices: list[EventChoice]


@dataclass(frozen=True)
class EventTemplateConfig:
    event_id: str
    event_name: str
    event_type: str
    option_ids: list[str]
    outcome_type: str = ""
    risk_level: str = ""
    trigger_sources: list[str] = field(default_factory=list)
    choice_pattern: str = ""
    title_text: str = ""
    body_text: str = ""
    realm_min: str | None = None
    realm_max: str | None = None
    region: str = ""
    weight: int = 1
    is_repeatable: bool = True
    cooldown_rounds: int = 0
    max_trigger_per_run: int = 999999
    required_statuses: list[str] = field(default_factory=list)
    excluded_statuses: list[str] = field(default_factory=list)
    required_techniques: list[str] = field(default_factory=list)
    required_equipment_tags: list[str] = field(default_factory=list)
    required_resources: dict[str, int] = field(default_factory=dict)
    required_rebirth_count: int = 0
    required_karma_min: int | None = None
    required_luck_min: int = 0
    flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EventOptionConfig:
    option_id: str
    event_id: str
    option_text: str
    sort_order: int = 1
    is_default: bool = False
    time_cost_months: int = 0
    resolution_mode: str = ""
    requires_resources: dict[str, int] = field(default_factory=dict)
    requires_statuses: list[str] = field(default_factory=list)
    requires_techniques: list[str] = field(default_factory=list)
    requires_equipment_tags: list[str] = field(default_factory=list)
    success_rate_formula: str = ""
    result_on_success: str | dict[str, object] | EventResultPayload = ""
    result_on_failure: str | dict[str, object] | EventResultPayload = ""
    next_event_id: str | None = None
    log_text_success: str = ""
    log_text_failure: str = ""


@dataclass(frozen=True)
class EventResultPayload:
    resources: dict[str, int] = field(default_factory=dict)
    character: dict[str, int] = field(default_factory=dict)
    statuses_add: list[str] = field(default_factory=list)
    statuses_remove: list[str] = field(default_factory=list)
    techniques_add: list[str] = field(default_factory=list)
    equipment_add: list[str] = field(default_factory=list)
    equipment_remove: list[str] = field(default_factory=list)
    battle: dict[str, object] | None = None
    death: bool = False
    rebirth_progress_delta: int = 0


@dataclass(frozen=True)
class CurrentEventOption:
    option_id: str
    option_text: str
    sort_order: int
    is_default: bool
    time_cost_months: int = 0
    requires_resources: dict[str, int] = field(default_factory=dict)
    requires_statuses: list[str] = field(default_factory=list)
    requires_techniques: list[str] = field(default_factory=list)
    requires_equipment_tags: list[str] = field(default_factory=list)
    is_available: bool = True
    disabled_reason: str | None = None


@dataclass
class CurrentEvent:
    event_id: str
    event_name: str
    event_type: str
    outcome_type: str
    risk_level: str
    trigger_sources: list[str]
    choice_pattern: str
    title_text: str
    body_text: str
    region: str
    status: str
    options: list[CurrentEventOption]


@dataclass
class EventResolutionLog:
    event_id: str
    option_id: str
    intended_resources: dict[str, int] = field(default_factory=dict)
    intended_character: dict[str, int] = field(default_factory=dict)
    actual_character: dict[str, int] = field(default_factory=dict)
    capped_character: dict[str, int] = field(default_factory=dict)
    time_cost_months: int = 0


@dataclass
class CombatActorState:
    name: str
    realm_label: str
    hp_current: int
    hp_max: int
    attack: int
    defense: int
    speed: int


@dataclass
class ActiveBattleState:
    source_event_id: str
    source_option_id: str
    round_index: int
    allow_flee: bool
    flee_base_rate: float
    player: CombatActorState
    enemy: CombatActorState
    pill_heal_amount: int = 0
    pill_count: int = 0
    log_lines: list[str] = field(default_factory=list)
    is_finished: bool = False
    result: str | None = None


@dataclass
class ResourceState:
    spirit_stone: int = 100
    herbs: int = 3
    iron_essence: int = 0
    ore: int = 0
    beast_material: int = 0
    pill: int = 0
    craft_material: int = 0


@dataclass
class RunResourceStack:
    resource_key: str
    amount: int


@dataclass
class DwellingFacilityState:
    facility_id: str
    display_name: str
    facility_type: str
    summary: str
    level: int = 0
    max_level: int = 3
    status: str = "unbuilt"
    build_cost: dict[str, int] = field(default_factory=dict)
    next_upgrade_cost: dict[str, int] = field(default_factory=dict)
    maintenance_cost: dict[str, int] = field(default_factory=dict)
    monthly_resource_yields: dict[str, int] = field(default_factory=dict)
    monthly_cultivation_exp_gain: int = 0
    function_unlock_text: str = ""
    is_function_unlocked: bool = False


@dataclass
class DwellingSettlementEntry:
    facility_id: str
    display_name: str
    status: str
    maintenance_paid: dict[str, int] = field(default_factory=dict)
    resource_gains: dict[str, int] = field(default_factory=dict)
    cultivation_exp_gain: int = 0
    summary: str = ""


@dataclass
class DwellingSettlement:
    round_index: int
    total_maintenance_paid: dict[str, int] = field(default_factory=dict)
    total_resource_gains: dict[str, int] = field(default_factory=dict)
    total_cultivation_exp_gain: int = 0
    entries: list[DwellingSettlementEntry] = field(default_factory=list)
    summary_lines: list[str] = field(default_factory=list)


@dataclass
class AlchemyRecipeState:
    recipe_id: str
    display_name: str
    category: str
    description: str
    required_alchemy_level: int
    required_alchemy_room_level: int
    duration_months: int
    base_success_rate: float
    ingredients: dict[str, int] = field(default_factory=dict)
    can_start: bool = False
    disabled_reason: str | None = None


@dataclass
class AlchemyInventoryItem:
    item_id: str
    display_name: str
    quality: str
    amount: int
    effect_summary: str


@dataclass
class AlchemyJob:
    recipe_id: str
    recipe_name: str
    total_months: int
    remaining_months: int
    use_spirit_spring: bool = False


@dataclass
class AlchemyResult:
    recipe_id: str
    recipe_name: str
    outcome: str
    quality: str
    outcome_rank: int
    amount: int
    mastery_exp_gained: int
    summary: str


@dataclass
class AlchemyState:
    mastery_exp: int = 0
    mastery_level: int = 0
    mastery_title: str = "丹道未入门"
    available_recipes: list[AlchemyRecipeState] = field(default_factory=list)
    inventory: list[AlchemyInventoryItem] = field(default_factory=list)
    active_job: AlchemyJob | None = None
    last_result: AlchemyResult | None = None


@dataclass
class CharacterState:
    name: str
    realm: str
    cultivation_exp: int
    lifespan_current: int
    lifespan_max: int
    realm_display_name: str = ""
    hp_current: int = 100
    hp_max: int = 100
    luck: int = 0
    karma: int = 0
    technique_exp: int = 0
    breakthrough_bonus: int = 0
    technique_bonus: float = 0.0
    pill_bonus: float = 0.0
    status_penalty: float = 0.0
    statuses: list[str] = field(default_factory=list)
    techniques: list[str] = field(default_factory=list)
    equipment_tags: list[str] = field(default_factory=list)
    rebirth_progress: int = 0
    is_dead: bool = False


@dataclass
class PlayerProfile:
    player_id: str
    total_rebirth_count: int = 0
    permanent_luck_bonus: int = 0
    rebirth_points: int = 0


@dataclass
class RunState:
    run_id: str
    player_id: str
    round_index: int
    character: CharacterState
    resources: ResourceState
    resource_stacks: list[RunResourceStack] = field(default_factory=list)
    alchemy_state: AlchemyState = field(default_factory=AlchemyState)
    breakthrough_requirements: BreakthroughRequirements | None = None
    current_event: CurrentEvent | None = None
    active_battle: ActiveBattleState | None = None
    dwelling_level: int = 1
    dwelling_facilities: list[DwellingFacilityState] = field(default_factory=list)
    dwelling_last_settlement: DwellingSettlement | None = None
    last_event_resolution: EventResolutionLog | None = None
    result_summary: str | None = None
    event_trigger_counts: dict[str, int] = field(default_factory=dict)
    event_cooldowns: dict[str, int] = field(default_factory=dict)


@dataclass
class BreakthroughResult:
    success: bool
    previous_realm: str
    new_realm: str
    success_rate: float
    message: str
    character: CharacterState
    resources: ResourceState
    breakthrough_requirements: BreakthroughRequirements | None = None


@dataclass
class RebirthResult:
    player_profile: PlayerProfile
    new_run: RunState


@dataclass
class RepositoryState:
    runs: dict[str, RunState] = field(default_factory=dict)
    profiles: dict[str, PlayerProfile] = field(default_factory=dict)


@dataclass(frozen=True)
class ConfigValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
