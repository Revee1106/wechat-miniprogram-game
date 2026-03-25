from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.admin.repositories.event_config_repository import EventConfigRepository


def test_repository_loads_templates_and_options_from_json() -> None:
    base_path = _make_test_base_path("load")
    repository = EventConfigRepository(base_path=base_path)
    repository.save(
        {
            "templates": [
                {
                    "event_id": "evt_one",
                    "event_name": "One",
                    "event_type": "cultivation",
                    "option_ids": ["opt_one"],
                }
            ],
            "options": [
                {
                    "option_id": "opt_one",
                    "event_id": "evt_one",
                    "option_text": "Option One",
                }
            ],
        }
    )

    loaded = repository.load()

    assert loaded["templates"][0]["event_id"] == "evt_one"
    assert loaded["options"][0]["option_id"] == "opt_one"
    rmtree(base_path)


def test_repository_creates_expected_json_files_on_save() -> None:
    base_path = _make_test_base_path("save")
    repository = EventConfigRepository(base_path=base_path)

    repository.save({"templates": [], "options": []})

    assert (base_path / "config" / "events" / "templates.json").exists()
    assert (base_path / "config" / "events" / "options.json").exists()
    rmtree(base_path)


def _make_test_base_path(label: str) -> Path:
    base_path = Path.cwd() / ".pytest_tmp" / f"{label}-{uuid4().hex}"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
