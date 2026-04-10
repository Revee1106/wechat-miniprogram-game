from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.realm_config_repository import RealmConfigRepository
from app.core_loop.realm_config import load_realm_configs, resolve_realm_key
from app.core_loop.seeds import get_realm_configs


def test_runtime_loader_sorts_realms_by_order_index() -> None:
    base_path = _make_test_base_path("realm-loader-sort")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "later",
                    "display_name": "后置",
                    "major_realm": "foundation",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 0.5,
                    "required_cultivation_exp": 20,
                    "required_spirit_stone": 10,
                    "lifespan_bonus": 12,
                    "is_enabled": True,
                },
                {
                    "key": "earlier",
                    "display_name": "前置",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.6,
                    "required_cultivation_exp": 10,
                    "required_spirit_stone": 5,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
            ]
        }
    )

    realms = load_realm_configs(base_path=base_path)

    assert [realm.key for realm in realms] == ["earlier", "later"]
    rmtree(base_path)


def test_runtime_loader_filters_disabled_realms() -> None:
    base_path = _make_test_base_path("realm-loader-filter")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "enabled",
                    "display_name": "启用",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.6,
                    "required_cultivation_exp": 10,
                    "required_spirit_stone": 5,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
                {
                    "key": "disabled",
                    "display_name": "禁用",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 0.5,
                    "required_cultivation_exp": 20,
                    "required_spirit_stone": 10,
                    "lifespan_bonus": 6,
                    "is_enabled": False,
                },
            ]
        }
    )

    realms = load_realm_configs(base_path=base_path)

    assert [realm.key for realm in realms] == ["enabled"]
    rmtree(base_path)


def test_runtime_loader_maps_config_fields_to_realm_config() -> None:
    base_path = _make_test_base_path("realm-loader-map")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_mid",
                    "display_name": "炼气中期",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 0.9,
                    "required_cultivation_exp": 200,
                    "required_spirit_stone": 30,
                    "lifespan_bonus": 6,
                    "failure_penalty": {"character": {"cultivation_exp": -30}},
                    "is_enabled": True,
                }
            ]
        }
    )

    realms = load_realm_configs(base_path=base_path)

    assert len(realms) == 1
    realm = realms[0]
    assert realm.key == "qi_refining_mid"
    assert realm.display_name == "炼气中期"
    assert realm.major_realm == "qi_refining"
    assert realm.stage_index == 2
    assert realm.order_index == 2
    assert realm.required_exp == 200
    assert realm.required_spirit_stone == 30
    assert realm.lifespan_bonus == 6
    assert realm.base_success_rate == 0.9
    assert realm.failure_penalty == {"character": {"cultivation_exp": -30}}
    assert realm.is_enabled is True
    rmtree(base_path)


def test_runtime_loader_treats_string_false_as_disabled() -> None:
    base_path = _make_test_base_path("realm-loader-bool")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "enabled",
                    "display_name": "启用",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.6,
                    "required_cultivation_exp": 10,
                    "required_spirit_stone": 5,
                    "lifespan_bonus": 6,
                    "is_enabled": "false",
                }
            ]
        }
    )

    realms = load_realm_configs(base_path=base_path)

    assert realms == []
    rmtree(base_path)


def test_seed_realms_starts_with_qi_refining_chain() -> None:
    realms = get_realm_configs()

    assert [realm.key for realm in realms[:4]] == [
        "qi_refining_early",
        "qi_refining_mid",
        "qi_refining_late",
        "qi_refining_peak",
    ]


def test_resolve_realm_key_boundary_falls_back_to_available_major_realm_stage() -> None:
    base_path = _make_test_base_path("realm-loader-boundary-fallback")
    RealmConfigRepository(base_path=base_path).save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.6,
                    "required_cultivation_exp": 10,
                    "required_spirit_stone": 5,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
                {
                    "key": "qi_refining_mid",
                    "display_name": "炼气中期",
                    "major_realm": "qi_refining",
                    "stage_index": 2,
                    "order_index": 2,
                    "base_success_rate": 0.5,
                    "required_cultivation_exp": 20,
                    "required_spirit_stone": 10,
                    "lifespan_bonus": 6,
                    "is_enabled": True,
                },
            ]
        }
    )

    realms = load_realm_configs(base_path=base_path)

    assert resolve_realm_key("qi_refining_peak", realms, boundary="max") == "qi_refining_mid"
    assert resolve_realm_key("qi_refining_peak", realms, boundary="min") == "qi_refining_early"
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
