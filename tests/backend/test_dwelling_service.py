from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.dwelling_config_repository import DwellingConfigRepository
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
    assert facility.monthly_resource_yields == {"basic_herb": 3}


def test_advance_time_settles_dwelling_outputs_before_event_selection() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 500

    service.build_dwelling_facility(run.run_id, "spirit_field")
    service.build_dwelling_facility(run.run_id, "spirit_spring")
    service.build_dwelling_facility(run.run_id, "mine_cave")
    service.build_dwelling_facility(run.run_id, "spirit_gathering_array")
    before_exp = run.character.cultivation_exp
    before_spirit_stone = run.resources.spirit_stone

    advanced = service.advance_time(run.run_id)

    assert advanced.current_event is not None
    assert advanced.dwelling_last_settlement is not None
    assert advanced.dwelling_last_settlement.total_maintenance_paid == {"spirit_stone": 12}
    assert advanced.dwelling_last_settlement.total_resource_gains == {
        "basic_herb": 2,
        "spirit_spring_water": 1,
        "spirit_stone": 4,
        "basic_ore": 1,
    }
    assert advanced.dwelling_last_settlement.total_cultivation_exp_gain == 6
    assert advanced.resources.herbs == run.resources.herbs
    assert advanced.resources.ore == run.resources.ore
    assert advanced.character.cultivation_exp == before_exp + 12
    assert advanced.resources.spirit_stone == before_spirit_stone - 10
    assert any(
        stack.resource_key == "basic_herb" and stack.amount == 2
        for stack in advanced.resource_stacks
    )
    assert any(
        stack.resource_key == "basic_ore" and stack.amount == 1
        for stack in advanced.resource_stacks
    )
    assert any(
        stack.resource_key == "spirit_spring_water" and stack.amount == 1
        for stack in advanced.resource_stacks
    )


def test_dwelling_facility_stalls_when_maintenance_cannot_be_paid() -> None:
    service = RunService()
    run = service.create_run(player_id="p1")
    run.resources.spirit_stone = 60

    service.build_dwelling_facility(run.run_id, "spirit_field")
    run.resources.spirit_stone = 2
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
        base_success_rate=0,
        required_exp=0,
        required_spirit_stone=0,
    )
    next_realm = RealmConfig(
        key="qi_refining_mid",
        display_name="Qi Refining Mid",
        major_realm="qi_refining",
        stage_index=2,
        order_index=2,
        lifespan_bonus=6,
        base_success_rate=0.45,
        required_exp=100,
        required_spirit_stone=20,
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


def test_spirit_gathering_array_increases_mine_spirit_stone_output() -> None:
    service = RunService()

    base_run = service.create_run(player_id="mine-base")
    base_run.resources.spirit_stone = 200
    service.build_dwelling_facility(base_run.run_id, "mine_cave")
    base_before = base_run.resources.spirit_stone
    base_advanced = service.advance_time(base_run.run_id)

    boosted_run = service.create_run(player_id="mine-boosted")
    boosted_run.resources.spirit_stone = 400
    service.build_dwelling_facility(boosted_run.run_id, "mine_cave")
    service.build_dwelling_facility(boosted_run.run_id, "spirit_gathering_array")
    service.upgrade_dwelling_facility(boosted_run.run_id, "spirit_gathering_array")
    service.upgrade_dwelling_facility(boosted_run.run_id, "spirit_gathering_array")
    boosted_advanced = service.advance_time(boosted_run.run_id)

    base_gain = base_advanced.dwelling_last_settlement.total_resource_gains["spirit_stone"]
    boosted_gain = boosted_advanced.dwelling_last_settlement.total_resource_gains["spirit_stone"]

    assert boosted_gain > base_gain


def test_advance_time_without_built_dwelling_does_not_create_dwelling_inventory() -> None:
    service = RunService()
    run = service.create_run(player_id="no-dwelling")

    advanced = service.advance_time(run.run_id)

    assert advanced.resource_stacks == []


def test_dwelling_service_reads_costs_and_yields_from_json_config() -> None:
    base_path = _make_test_base_path("dwelling-runtime-config")
    DwellingConfigRepository(base_path=base_path).save(
        {
            "facilities": [
                _facility_config(
                    facility_id="spirit_field",
                    display_name="灵田",
                    facility_type="production",
                    levels=[
                        _facility_level(
                            level=1,
                            entry_cost={"spirit_stone": 66},
                            maintenance_cost={"spirit_stone": 5},
                            resource_yields={"basic_herb": 9},
                        ),
                    ],
                ),
                _facility_config("spirit_spring", "灵泉", "production", [_facility_level(1)]),
                _facility_config("mine_cave", "矿洞", "production", [_facility_level(1)]),
                _facility_config("alchemy_room", "炼丹房", "function", [_facility_level(1)]),
                _facility_config(
                    "spirit_gathering_array",
                    "聚灵阵",
                    "boost",
                    [_facility_level(1, cultivation_exp_gain=6)],
                ),
            ]
        }
    )

    service = RunService(dwelling_config_base_path=str(base_path))
    run = service.create_run(player_id="config-read")
    run.resources.spirit_stone = 200

    built = service.build_dwelling_facility(run.run_id, "spirit_field")
    facility = next(
        item for item in built.dwelling_facilities if item.facility_id == "spirit_field"
    )
    advanced = service.advance_time(run.run_id)

    assert built.resources.spirit_stone == 134
    assert facility.maintenance_cost == {"spirit_stone": 5}
    assert advanced.dwelling_last_settlement is not None
    assert advanced.dwelling_last_settlement.total_resource_gains["basic_herb"] == 9
    rmtree(base_path)


def test_dwelling_service_can_upgrade_to_newly_added_level_four() -> None:
    base_path = _make_test_base_path("dwelling-runtime-level-four")
    DwellingConfigRepository(base_path=base_path).save(
        {
            "facilities": [
                _facility_config(
                    facility_id="spirit_field",
                    display_name="灵田",
                    facility_type="production",
                    levels=[
                        _facility_level(1, entry_cost={"spirit_stone": 50}),
                        _facility_level(2, entry_cost={"spirit_stone": 40}),
                        _facility_level(3, entry_cost={"spirit_stone": 55}),
                        _facility_level(
                            4,
                            entry_cost={"spirit_stone": 80},
                            maintenance_cost={"spirit_stone": 6},
                            resource_yields={"basic_herb": 8},
                        ),
                    ],
                ),
                _facility_config("spirit_spring", "灵泉", "production", [_facility_level(1)]),
                _facility_config("mine_cave", "矿洞", "production", [_facility_level(1)]),
                _facility_config("alchemy_room", "炼丹房", "function", [_facility_level(1)]),
                _facility_config(
                    "spirit_gathering_array",
                    "聚灵阵",
                    "boost",
                    [_facility_level(1, cultivation_exp_gain=6)],
                ),
            ]
        }
    )

    service = RunService(dwelling_config_base_path=str(base_path))
    run = service.create_run(player_id="level-four")
    run.resources.spirit_stone = 400

    service.build_dwelling_facility(run.run_id, "spirit_field")
    service.upgrade_dwelling_facility(run.run_id, "spirit_field")
    service.upgrade_dwelling_facility(run.run_id, "spirit_field")
    upgraded = service.upgrade_dwelling_facility(run.run_id, "spirit_field")
    facility = next(
        item for item in upgraded.dwelling_facilities if item.facility_id == "spirit_field"
    )

    assert facility.level == 4
    assert facility.max_level == 4
    assert facility.monthly_resource_yields == {"basic_herb": 8}
    rmtree(base_path)


def test_spirit_gathering_array_special_effects_are_loaded_from_config() -> None:
    base_path = _make_test_base_path("dwelling-runtime-special-effects")
    DwellingConfigRepository(base_path=base_path).save(
        {
            "facilities": [
                _facility_config("spirit_field", "灵田", "production", [_facility_level(1)]),
                _facility_config("spirit_spring", "灵泉", "production", [_facility_level(1)]),
                _facility_config(
                    "mine_cave",
                    "矿洞",
                    "production",
                    [
                        _facility_level(
                            1,
                            entry_cost={"spirit_stone": 60},
                            maintenance_cost={"spirit_stone": 3},
                            resource_yields={"spirit_stone": 4, "basic_ore": 1},
                        )
                    ],
                ),
                _facility_config("alchemy_room", "炼丹房", "function", [_facility_level(1)]),
                _facility_config(
                    "spirit_gathering_array",
                    "聚灵阵",
                    "boost",
                    [
                        _facility_level(
                            1,
                            entry_cost={"spirit_stone": 100},
                            maintenance_cost={"spirit_stone": 4},
                            cultivation_exp_gain=6,
                            special_effects={
                                "breakthrough_bonus_rate": 0.05,
                                "mine_spirit_stone_bonus_rate": 0.5,
                            },
                        )
                    ],
                ),
            ]
        }
    )

    service = RunService(dwelling_config_base_path=str(base_path))

    base_run = service.create_run(player_id="config-mine-base")
    base_run.resources.spirit_stone = 200
    service.build_dwelling_facility(base_run.run_id, "mine_cave")
    base_advanced = service.advance_time(base_run.run_id)

    boosted_run = service.create_run(player_id="config-mine-boosted")
    boosted_run.resources.spirit_stone = 400
    service.build_dwelling_facility(boosted_run.run_id, "mine_cave")
    service.build_dwelling_facility(boosted_run.run_id, "spirit_gathering_array")
    boosted_advanced = service.advance_time(boosted_run.run_id)

    base_gain = base_advanced.dwelling_last_settlement.total_resource_gains["spirit_stone"]
    boosted_gain = boosted_advanced.dwelling_last_settlement.total_resource_gains["spirit_stone"]

    assert boosted_gain == 6
    assert boosted_gain > base_gain
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def _facility_config(
    facility_id: str,
    display_name: str,
    facility_type: str,
    levels: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "facility_id": facility_id,
        "display_name": display_name,
        "facility_type": facility_type,
        "summary": f"{display_name}摘要",
        "function_unlock_text": "",
        "levels": levels,
    }


def _facility_level(
    level: int,
    *,
    entry_cost: dict[str, int] | None = None,
    maintenance_cost: dict[str, int] | None = None,
    resource_yields: dict[str, int] | None = None,
    cultivation_exp_gain: int = 0,
    special_effects: dict[str, float] | None = None,
) -> dict[str, object]:
    return {
        "level": level,
        "entry_cost": entry_cost if entry_cost is not None else {"spirit_stone": 50},
        "maintenance_cost": (
            maintenance_cost if maintenance_cost is not None else {"spirit_stone": 2}
        ),
        "resource_yields": resource_yields if resource_yields is not None else {},
        "cultivation_exp_gain": cultivation_exp_gain,
        "special_effects": special_effects if special_effects is not None else {},
    }
