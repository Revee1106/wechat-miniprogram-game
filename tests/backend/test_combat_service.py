from app.core_loop.services.combat_service import CombatService
from app.core_loop.types import CombatActorState, ConflictError


def _make_actor(
    name: str,
    hp_current: int,
    hp_max: int,
    attack: int,
    defense: int,
    speed: int,
) -> CombatActorState:
    return CombatActorState(
        name=name,
        realm_label="测试境界",
        hp_current=hp_current,
        hp_max=hp_max,
        attack=attack,
        defense=defense,
        speed=speed,
    )


def _make_service(*values: float) -> CombatService:
    iterator = iter(values)
    return CombatService(rng=lambda: next(iterator))


def test_start_battle_initializes_battle_state() -> None:
    service = CombatService()

    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 40, 40, 12, 5, 8),
        enemy=_make_actor("山匪", 30, 30, 8, 3, 6),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=2,
    )

    assert battle.source_event_id == "evt_bandit"
    assert battle.source_option_id == "opt_bandit"
    assert battle.round_index == 1
    assert battle.allow_flee is True
    assert battle.flee_base_rate == 0.35
    assert battle.pill_heal_amount == 18
    assert battle.pill_count == 2
    assert battle.is_finished is False
    assert battle.result is None


def test_attack_action_resolves_in_speed_order_and_finishes_when_enemy_dies() -> None:
    service = _make_service(0.5)
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 30, 30, 12, 4, 10),
        enemy=_make_actor("山匪", 10, 10, 8, 2, 5),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=1,
    )

    updated = service.perform_action(battle, "attack")

    assert updated.enemy.hp_current == 0
    assert updated.player.hp_current == 30
    assert updated.is_finished is True
    assert updated.result == "victory"
    assert updated.log_lines[0] == "你先手攻击山匪，造成了10点伤害。"


def test_attack_action_lets_faster_enemy_act_first() -> None:
    service = _make_service(0.5, 0.5)
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 30, 30, 12, 4, 5),
        enemy=_make_actor("山匪", 20, 20, 8, 3, 10),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=1,
    )

    updated = service.perform_action(battle, "attack")

    assert updated.player.hp_current == 26
    assert updated.enemy.hp_current == 11
    assert updated.is_finished is False
    assert updated.result is None
    assert updated.log_lines[0] == "山匪先手攻击你，造成了4点伤害。"
    assert updated.log_lines[1] == "你攻击山匪，造成了9点伤害。"


def test_defend_reduces_enemy_damage_even_when_enemy_starts_first() -> None:
    service = _make_service(0.5)
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 30, 30, 12, 2, 4),
        enemy=_make_actor("山匪", 20, 20, 10, 1, 9),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=1,
    )

    updated = service.perform_action(battle, "defend")

    assert updated.player.hp_current == 26
    assert updated.enemy.hp_current == 20
    assert updated.log_lines[0] == "你摆出防御姿态。"
    assert updated.log_lines[1] == "山匪攻击你，造成了4点伤害。"


def test_use_pill_heals_and_consumes_pill() -> None:
    service = _make_service(0.5)
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 10, 40, 12, 4, 10),
        enemy=_make_actor("山匪", 20, 20, 6, 5, 3),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=12,
        pill_count=1,
    )

    updated = service.perform_action(battle, "use_pill")

    assert updated.player.hp_current == 20
    assert updated.pill_count == 0
    assert updated.log_lines[0] == "你服下丹药，恢复了12点气血。"
    assert updated.log_lines[1] == "山匪攻击你，造成了2点伤害。"


def test_flee_success_rate_clamps_to_lower_bound() -> None:
    service = _make_service(0.5, 0.14)
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 30, 30, 12, 4, 1),
        enemy=_make_actor("山匪", 20, 20, 8, 3, 20),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=1,
    )

    updated = service.perform_action(battle, "flee")

    assert updated.is_finished is True
    assert updated.result == "flee_success"
    assert updated.log_lines[0] == "山匪先手攻击你，造成了4点伤害。"
    assert updated.log_lines[1] == "你尝试逃跑，成功脱身。"


def test_flee_success_rate_clamps_to_upper_bound() -> None:
    service = _make_service(0.86, 0.5)
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 30, 30, 12, 4, 30),
        enemy=_make_actor("山匪", 20, 20, 8, 3, 1),
        allow_flee=True,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=1,
    )

    updated = service.perform_action(battle, "flee")

    assert updated.is_finished is False
    assert updated.result == "flee_failure"
    assert updated.log_lines[0] == "你尝试逃跑，但未能摆脱山匪。"


def test_flee_rejected_when_not_allowed() -> None:
    service = CombatService()
    battle = service.start_battle(
        source_event_id="evt_bandit",
        source_option_id="opt_bandit",
        player=_make_actor("修士甲", 30, 30, 12, 4, 10),
        enemy=_make_actor("山匪", 20, 20, 8, 3, 5),
        allow_flee=False,
        flee_base_rate=0.35,
        pill_heal_amount=18,
        pill_count=1,
    )

    try:
        service.perform_action(battle, "flee")
    except ConflictError as error:
        assert "flee" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected flee to be rejected")
