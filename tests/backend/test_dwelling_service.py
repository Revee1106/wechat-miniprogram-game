from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.services.progression_service import ProgressionService
from app.core_loop.services.run_service import RunService
from app.core_loop.types import RealmConfig


def test_build_and_upgrade_dwelling_facility_updates_state_and_costs() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 400

    built = service.build_dwelling_facility(run.run_id, "spirit_field")
    facility = next(
        item for item in built.dwelling_facilities if item.facility_id == "spirit_field"
    )

    assert built.resources.spirit_stone == 350
    assert facility.level == 1
    assert facility.status == "active"
    assert facility.maintenance_cost == {"spirit_stone": 2}

    upgraded = service.upgrade_dwelling_facility(run.run_id, "spirit_field")
    facility = next(
        item for item in upgraded.dwelling_facilities if item.facility_id == "spirit_field"
    )

    assert upgraded.resources.spirit_stone == 310
    assert facility.level == 2
    assert facility.monthly_resource_yields == {"herb": 3}


def test_advance_time_settles_dwelling_outputs_before_event_selection() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 400

    service.build_dwelling_facility(run.run_id, "spirit_field")
    service.build_dwelling_facility(run.run_id, "mine_cave")
    service.build_dwelling_facility(run.run_id, "spirit_gathering_array")
    before_herbs = run.resources.herbs
    before_ore = run.resources.ore
    before_exp = run.character.cultivation_exp
    before_spirit_stone = run.resources.spirit_stone

    advanced = service.advance_time(run.run_id)

    assert advanced.current_event is not None
    assert advanced.dwelling_last_settlement is not None
    assert advanced.dwelling_last_settlement.total_maintenance_paid == {"spirit_stone": 9}
    assert advanced.dwelling_last_settlement.total_resource_gains == {"herb": 2, "ore": 1}
    assert advanced.dwelling_last_settlement.total_cultivation_exp_gain == 6
    assert advanced.resources.herbs == before_herbs + 2
    assert advanced.resources.ore == before_ore + 1
    assert advanced.character.cultivation_exp == before_exp + 6
    assert advanced.resources.spirit_stone == before_spirit_stone - 9


def test_dwelling_facility_stalls_when_maintenance_cannot_be_paid() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 60

    service.build_dwelling_facility(run.run_id, "spirit_field")
    run.resources.spirit_stone = 0
    before_herbs = run.resources.herbs

    advanced = service.advance_time(run.run_id)
    facility = next(
        item for item in advanced.dwelling_facilities if item.facility_id == "spirit_field"
    )

    assert facility.status == "stalled"
    assert advanced.resources.herbs == before_herbs
    assert advanced.dwelling_last_settlement is not None
    assert advanced.dwelling_last_settlement.entries[0].status == "stalled"


def test_spirit_gathering_array_increases_breakthrough_success_rate() -> None:
    service = RunService()
    current_realm = RealmConfig(
        key="qi_refining_early",
        display_name="Qi Refining Early",
        major_realm="qi_refining",
        stage_index=1,
        order_index=1,
        lifespan_bonus=6,
        base_success_rate=0.40,
        required_exp=100,
        required_spirit_stone=20,
    )
    next_realm = RealmConfig(
        key="qi_refining_mid",
        display_name="Qi Refining Mid",
        major_realm="qi_refining",
        stage_index=2,
        order_index=2,
        lifespan_bonus=6,
        base_success_rate=0.45,
        required_exp=200,
        required_spirit_stone=30,
    )
    progression_service = ProgressionService(
        DwellingService(),
        realm_configs=[current_realm, next_realm],
    )

    base_run = service.create_run(player_id="base")
    base_run.character.cultivation_exp = 100
    base_run.resources.spirit_stone = 300
    base_result = progression_service.try_breakthrough(base_run)

    array_run = service.create_run(player_id="array")
    array_run.resources.spirit_stone = 400
    service.build_dwelling_facility(array_run.run_id, "spirit_gathering_array")
    service.upgrade_dwelling_facility(array_run.run_id, "spirit_gathering_array")
    array_run.character.cultivation_exp = 100
    array_run.resources.spirit_stone = 300
    array_result = progression_service.try_breakthrough(array_run)

    assert array_result.success_rate > base_result.success_rate
