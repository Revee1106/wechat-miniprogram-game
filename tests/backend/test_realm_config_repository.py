from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.realm_config_repository import RealmConfigRepository


def test_repository_loads_and_saves_realms_from_json() -> None:
    base_path = _make_test_base_path("realm-load")
    repository = RealmConfigRepository(base_path=base_path)
    repository.save(
        {
            "realms": [
                {
                    "key": "qi_refining_early",
                    "display_name": "炼气初期",
                    "major_realm": "qi_refining",
                    "stage_index": 1,
                    "order_index": 1,
                    "base_success_rate": 0.85,
                    "required_cultivation_exp": 100,
                    "required_spirit_stone": 50,
                    "lifespan_bonus": 12,
                    "is_enabled": True,
                }
            ]
        }
    )

    loaded = repository.load()

    assert loaded["realms"][0]["key"] == "qi_refining_early"
    assert loaded["realms"][0]["display_name"] == "炼气初期"
    rmtree(base_path)


def test_repository_creates_expected_json_file_on_save() -> None:
    base_path = _make_test_base_path("realm-save")
    repository = RealmConfigRepository(base_path=base_path)

    repository.save({"realms": []})

    assert (base_path / "config" / "realms" / "realms.json").exists()
    rmtree(base_path)


def test_default_realms_json_covers_four_major_realms_with_four_stages() -> None:
    repository = RealmConfigRepository()

    loaded = repository.load()
    realms = loaded["realms"]

    assert len(realms) >= 16
    assert {
        realm["major_realm"]
        for realm in realms
        if realm["major_realm"] in {
            "qi_refining",
            "foundation",
            "golden_core",
            "nascent_soul",
        }
    } == {"qi_refining", "foundation", "golden_core", "nascent_soul"}
    for major_realm in ("qi_refining", "foundation", "golden_core", "nascent_soul"):
        stage_indices = sorted(
            realm["stage_index"]
            for realm in realms
            if realm["major_realm"] == major_realm
        )
        assert stage_indices == [1, 2, 3, 4]


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
