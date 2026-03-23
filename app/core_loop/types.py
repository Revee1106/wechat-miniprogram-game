from __future__ import annotations

from dataclasses import dataclass, field


class CoreLoopError(Exception):
    """Base domain error."""


class NotFoundError(CoreLoopError):
    """Raised when an entity cannot be found."""


class ConflictError(CoreLoopError):
    """Raised when a requested action conflicts with run state."""


@dataclass(frozen=True)
class RealmConfig:
    key: str
    display_name: str
    lifespan_bonus: int
    base_success_rate: float
    required_exp: int


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
    required_resources: dict[str, int] = field(default_factory=dict)
    required_rebirth_count: int = 0
    required_luck_min: int = 0
    flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EventOptionConfig:
    option_id: str
    event_id: str
    option_text: str
    sort_order: int = 0
    is_default: bool = False
    requires_resources: dict[str, int] = field(default_factory=dict)
    success_rate_formula: str = ""
    result_on_success: str = ""
    result_on_failure: str = ""
    log_text_success: str = ""
    log_text_failure: str = ""


@dataclass
class CurrentEvent:
    template_key: str
    template_name: str
    description: str
    status: str
    choices: list[EventChoice]


@dataclass
class ResourceState:
    spirit_stone: int = 20
    herbs: int = 3
    iron_essence: int = 0


@dataclass
class CharacterState:
    name: str
    realm: str
    cultivation_exp: int
    lifespan_current: int
    lifespan_max: int
    luck: int = 0
    technique_bonus: float = 0.0
    pill_bonus: float = 0.0
    status_penalty: float = 0.0
    is_dead: bool = False


@dataclass
class PlayerProfile:
    player_id: str
    total_rebirth_count: int = 0
    permanent_luck_bonus: int = 0


@dataclass
class RunState:
    run_id: str
    player_id: str
    round_index: int
    character: CharacterState
    resources: ResourceState
    current_event: CurrentEvent | None = None
    dwelling_level: int = 1
    result_summary: str | None = None


@dataclass
class BreakthroughResult:
    success: bool
    previous_realm: str
    new_realm: str
    success_rate: float
    message: str
    character: CharacterState
    resources: ResourceState


@dataclass
class RebirthResult:
    player_profile: PlayerProfile
    new_run: RunState


@dataclass
class RepositoryState:
    runs: dict[str, RunState] = field(default_factory=dict)
    profiles: dict[str, PlayerProfile] = field(default_factory=dict)
