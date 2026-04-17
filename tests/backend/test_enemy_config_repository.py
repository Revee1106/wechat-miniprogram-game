from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.enemy_config_repository import EnemyConfigRepository


def test_enemy_config_repository_creates_and_loads_default_file() -> None:
    base_path = _make_test_base_path("enemy-config-repository-default")

    payload = EnemyConfigRepository(base_path=base_path).load()

    assert payload == {"items": []}
    assert (base_path / "config" / "battle" / "enemies.json").exists()
    rmtree(base_path)


def test_enemy_config_repository_persists_enemy_templates() -> None:
    base_path = _make_test_base_path("enemy-config-repository-save")
    repository = EnemyConfigRepository(base_path=base_path)
    repository.save(
        {
            "items": [
                {
                    "enemy_id": "enemy_bandit_qi_early",
                    "enemy_name": "山匪",
                    "enemy_realm_label": "炼气初期",
                    "enemy_hp": 36,
                    "enemy_attack": 8,
                    "enemy_defense": 4,
                    "enemy_speed": 6,
                    "allow_flee": True,
                    "rewards": {
                        "resources": {"spirit_stone": 7},
                        "character": {"cultivation_exp": 5},
                    },
                }
            ]
        }
    )

    reloaded = repository.load()

    assert reloaded["items"][0]["enemy_id"] == "enemy_bandit_qi_early"
    assert reloaded["items"][0]["enemy_hp"] == 36
    assert reloaded["items"][0]["rewards"] == {
        "resources": {"spirit_stone": 7},
        "character": {"cultivation_exp": 5},
    }
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
