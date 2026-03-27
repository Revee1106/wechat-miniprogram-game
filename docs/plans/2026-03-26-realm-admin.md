# Realm Admin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为后台控制台新增“境界配置”能力，并把运行时境界与突破规则从写死 seed 抽到可校验、可重载的 JSON 配置。

**Architecture:** 在后端新增 `realms.json + repository + validation + runtime registry + admin API`，让 `ProgressionService` 和 `EventService` 都使用统一的 realm registry。前端控制台新增“境界配置”视图，支持列表、编辑、排序、删除校验和 reload，交互沿用现有二级编辑层模式。

**Tech Stack:** FastAPI, pytest, React, Vite, Vitest, JSON config files

---

### Task 1: 建立 realm 配置文件、repository 和基础校验

**Files:**
- Create: `app/admin/repositories/realm_config_repository.py`
- Create: `app/admin/services/realm_validation_service.py`
- Create: `config/realms/realms.json`
- Test: `tests/backend/test_realm_config_repository.py`
- Test: `tests/backend/test_realm_config_validation.py`

**Step 1: Write the failing tests**

```python
from app.admin.repositories.realm_config_repository import RealmConfigRepository


def test_realm_repository_loads_and_saves_realms(tmp_path) -> None:
    repository = RealmConfigRepository(base_path=tmp_path)
    payload = {
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

    repository.save(payload)

    assert repository.load() == payload
```

```python
from app.admin.services.realm_validation_service import validate_realm_config


def test_realm_validation_rejects_duplicate_keys() -> None:
    result = validate_realm_config(
        realms=[
            {"key": "qi_refining_early", "order_index": 1, "display_name": "炼气初期"},
            {"key": "qi_refining_early", "order_index": 2, "display_name": "炼气中期"},
        ]
    )

    assert result.is_valid is False
    assert "duplicate realm key: qi_refining_early" in result.errors
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/backend/test_realm_config_repository.py tests/backend/test_realm_config_validation.py -q`
Expected: FAIL with import error for missing repository/validation modules.

**Step 3: Write minimal implementation**

```python
class RealmConfigRepository:
    def __init__(self, base_path: Path | str | None = None) -> None:
        root = Path(base_path) if base_path is not None else Path(__file__).resolve().parents[3]
        self._config_dir = root / "config" / "realms"
        self._realms_path = self._config_dir / "realms.json"

    def load(self) -> dict[str, list[dict[str, Any]]]:
        if not self._realms_path.exists():
            self.save({"realms": []})
        return {"realms": self._read_json(self._realms_path)}

    def save(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self._realms_path, payload.get("realms", []))
```

```python
def validate_realm_config(*, realms: list[dict[str, object]]) -> ConfigValidationResult:
    errors: list[str] = []
    keys = [str(realm.get("key", "")) for realm in realms]
    order_indices = [str(realm.get("order_index", "")) for realm in realms]
    errors.extend(_find_duplicates(keys, "realm key"))
    errors.extend(_find_duplicates(order_indices, "realm order_index"))
    return ConfigValidationResult(is_valid=not errors, errors=errors, warnings=[])
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/backend/test_realm_config_repository.py tests/backend/test_realm_config_validation.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/admin/repositories/realm_config_repository.py app/admin/services/realm_validation_service.py config/realms/realms.json tests/backend/test_realm_config_repository.py tests/backend/test_realm_config_validation.py
git commit -m "feat: add realm config repository and validation"
```

### Task 2: 建立运行时 realm registry 并替换写死 seeds 入口

**Files:**
- Create: `app/core_loop/realm_config.py`
- Modify: `app/core_loop/seeds.py`
- Modify: `app/core_loop/types.py`
- Test: `tests/backend/test_core_loop_seeds.py`
- Test: `tests/backend/test_realm_runtime_config.py`

**Step 1: Write the failing tests**

```python
from app.core_loop.realm_config import load_realm_configs


def test_runtime_realm_configs_are_sorted_by_order_index(tmp_path) -> None:
    base_path = tmp_path
    config_dir = base_path / "config" / "realms"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "realms.json").write_text(
        '[{"key":"b","display_name":"乙","major_realm":"b","stage_index":1,"order_index":2,"base_success_rate":0.5,"required_cultivation_exp":20,"required_spirit_stone":10,"lifespan_bonus":12,"is_enabled":true},'
        '{"key":"a","display_name":"甲","major_realm":"a","stage_index":1,"order_index":1,"base_success_rate":0.6,"required_cultivation_exp":10,"required_spirit_stone":5,"lifespan_bonus":6,"is_enabled":true}]',
        encoding="utf-8",
    )

    realms = load_realm_configs(base_path=base_path)

    assert [realm.key for realm in realms] == ["a", "b"]
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/backend/test_core_loop_seeds.py tests/backend/test_realm_runtime_config.py -q`
Expected: FAIL because runtime realm loader does not exist yet.

**Step 3: Write minimal implementation**

```python
def load_realm_configs(base_path: Path | str | None = None) -> list[RealmConfig]:
    payload = RealmConfigRepository(base_path=base_path).load()
    rows = sorted(payload["realms"], key=lambda item: int(item.get("order_index", 0)))
    return [
        RealmConfig(
            key=str(row["key"]),
            display_name=str(row["display_name"]),
            lifespan_bonus=int(row["lifespan_bonus"]),
            base_success_rate=float(row["base_success_rate"]),
            required_exp=int(row["required_cultivation_exp"]),
        )
        for row in rows
        if bool(row.get("is_enabled", True))
    ]
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/backend/test_core_loop_seeds.py tests/backend/test_realm_runtime_config.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/core_loop/realm_config.py app/core_loop/seeds.py app/core_loop/types.py tests/backend/test_core_loop_seeds.py tests/backend/test_realm_runtime_config.py
git commit -m "feat: load runtime realm configs from json"
```

### Task 3: 改造突破与事件筛选，使用新的境界排序和突破条件

**Files:**
- Modify: `app/core_loop/services/progression_service.py`
- Modify: `app/core_loop/services/event_service.py`
- Modify: `app/core_loop/services/run_service.py`
- Test: `tests/backend/test_event_breakthrough_rebirth.py`
- Test: `tests/backend/test_event_generation_filters.py`

**Step 1: Write the failing tests**

```python
from app.core_loop.services.progression_service import ProgressionService
from app.core_loop.services.dwelling_service import DwellingService
from app.core_loop.types import CharacterState, ResourceState, RunState


def test_breakthrough_uses_current_realm_required_spirit_stone() -> None:
    service = ProgressionService(DwellingService())
    run = RunState(
        run_id="run-1",
        player_id="p1",
        round_index=0,
        character=CharacterState(
            name="道者",
            realm="qi_refining_early",
            cultivation_exp=100,
            lifespan_current=100,
            lifespan_max=100,
        ),
        resources=ResourceState(spirit_stone=49),
    )

    try:
        service.try_breakthrough(run)
    except Exception as error:
        assert str(error) == "not enough spirit stones to breakthrough"
    else:
        raise AssertionError("expected breakthrough to fail")
```

```python
def test_event_selection_uses_runtime_realm_order() -> None:
    ...
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/backend/test_event_breakthrough_rebirth.py tests/backend/test_event_generation_filters.py -q`
Expected: FAIL because breakthrough still uses hard-coded spirit stone cost and old realm ordering.

**Step 3: Write minimal implementation**

```python
if run.character.cultivation_exp < current_realm.required_exp:
    raise ConflictError("not enough cultivation exp to breakthrough")
if run.resources.spirit_stone < current_realm.required_spirit_stone:
    raise ConflictError("not enough spirit stones to breakthrough")

run.resources.spirit_stone -= current_realm.required_spirit_stone
```

```python
self._realm_indices = {
    config.key: index for index, config in enumerate(load_realm_configs())
}
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/backend/test_event_breakthrough_rebirth.py tests/backend/test_event_generation_filters.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/core_loop/services/progression_service.py app/core_loop/services/event_service.py app/core_loop/services/run_service.py tests/backend/test_event_breakthrough_rebirth.py tests/backend/test_event_generation_filters.py
git commit -m "feat: use realm config for breakthrough and event ordering"
```

### Task 4: 增加 realm admin service 和 API

**Files:**
- Create: `app/admin/services/realm_admin_service.py`
- Modify: `app/admin/api.py`
- Test: `tests/backend/test_admin_realm_api.py`
- Test: `tests/backend/test_admin_realm_service.py`

**Step 1: Write the failing tests**

```python
def test_admin_realm_list_endpoint_returns_items(monkeypatch) -> None:
    client = _create_authorized_client()

    response = client.get("/admin/api/realms")

    assert response.status_code == 200
    assert "items" in response.json()
```

```python
def test_admin_realm_delete_is_blocked_when_event_references_realm(monkeypatch) -> None:
    ...
    response = client.delete("/admin/api/realms/qi_refining_early")
    assert response.status_code == 400
    assert "referenced by events" in response.json()["detail"]
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/backend/test_admin_realm_api.py tests/backend/test_admin_realm_service.py -q`
Expected: FAIL with 404 or missing realm admin service.

**Step 3: Write minimal implementation**

```python
@router.get("/realms")
def list_realms() -> dict[str, object]:
    return realm_admin_service.list_realms()


@router.post("/realms/reload")
def reload_realms() -> dict[str, object]:
    return realm_admin_service.reload_runtime_config()
```

```python
def delete_realm(self, realm_key: str) -> None:
    references = self._find_event_references(realm_key)
    if references:
        raise ValueError(f"realm '{realm_key}' is referenced by events: {', '.join(references)}")
    ...
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/backend/test_admin_realm_api.py tests/backend/test_admin_realm_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/admin/services/realm_admin_service.py app/admin/api.py tests/backend/test_admin_realm_api.py tests/backend/test_admin_realm_service.py
git commit -m "feat: add admin api for realm configuration"
```

### Task 5: 在控制台增加“境界配置”导航、列表和编辑页

**Files:**
- Modify: `admin-console/src/App.tsx`
- Modify: `admin-console/src/api/client.ts`
- Create: `admin-console/src/pages/RealmListPage.tsx`
- Create: `admin-console/src/pages/RealmEditorPage.tsx`
- Create: `admin-console/src/components/RealmForm.tsx`
- Modify: `admin-console/src/styles/admin-theme.css`
- Test: `admin-console/src/pages/RealmListPage.test.tsx`
- Test: `admin-console/src/pages/RealmEditorPage.test.tsx`
- Test: `admin-console/src/App.test.tsx`

**Step 1: Write the failing tests**

```tsx
import { render, screen } from "@testing-library/react";
import App from "../App";


test("shows realm config entry in admin shell", async () => {
  render(<App />);

  expect(await screen.findByText("境界配置")).toBeInTheDocument();
});
```

```tsx
test("renders realm rows with breakthrough fields", async () => {
  ...
  expect(await screen.findByText("突破所需修为")).toBeInTheDocument();
  expect(await screen.findByText("突破所需灵石")).toBeInTheDocument();
});
```

**Step 2: Run tests to verify they fail**

Run: `npm.cmd test -- src/App.test.tsx src/pages/RealmListPage.test.tsx src/pages/RealmEditorPage.test.tsx`
Expected: FAIL because realm pages do not exist yet.

**Step 3: Write minimal implementation**

```tsx
type ViewState =
  | { mode: "event-list" }
  | { mode: "event-editor"; eventId?: string }
  | { mode: "realm-list" }
  | { mode: "realm-editor"; realmKey?: string };
```

```tsx
<button className="button-secondary" type="button" onClick={() => setView({ mode: "realm-list" })}>
  境界配置
</button>
```

**Step 4: Run tests to verify they pass**

Run: `npm.cmd test -- src/App.test.tsx src/pages/RealmListPage.test.tsx src/pages/RealmEditorPage.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/App.tsx admin-console/src/api/client.ts admin-console/src/pages/RealmListPage.tsx admin-console/src/pages/RealmEditorPage.tsx admin-console/src/components/RealmForm.tsx admin-console/src/styles/admin-theme.css admin-console/src/pages/RealmListPage.test.tsx admin-console/src/pages/RealmEditorPage.test.tsx admin-console/src/App.test.tsx
git commit -m "feat: add realm configuration screens to admin console"
```

### Task 6: 增加 realm 排序、自动 reload 和前后端回归验证

**Files:**
- Modify: `app/admin/services/realm_admin_service.py`
- Modify: `admin-console/src/pages/RealmListPage.tsx`
- Modify: `admin-console/src/pages/RealmEditorPage.tsx`
- Test: `tests/backend/test_admin_realm_api.py`
- Test: `admin-console/src/pages/RealmListPage.test.tsx`
- Test: `admin-console/src/pages/RealmEditorPage.test.tsx`
- Doc: `docs/plans/2026-03-26-realm-admin-progress.md`

**Step 1: Write the failing tests**

```python
def test_realm_reorder_endpoint_updates_order(monkeypatch) -> None:
    ...
    response = client.post(
        "/admin/api/realms/reorder",
        json={"keys": ["qi_refining_mid", "qi_refining_early"]},
    )
    assert response.status_code == 200
```

```tsx
test("saving realm shows reload success message", async () => {
  ...
  expect(await screen.findByText(/已保存，并已重载运行时/)).toBeInTheDocument();
});
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/backend/test_admin_realm_api.py -q`
Expected: FAIL because reorder endpoint and reload success flow are missing.

Run: `npm.cmd test -- src/pages/RealmListPage.test.tsx src/pages/RealmEditorPage.test.tsx`
Expected: FAIL because UI does not expose reorder / reload feedback yet.

**Step 3: Write minimal implementation**

```python
@router.post("/realms/reorder")
def reorder_realms(payload: dict[str, list[str]]) -> dict[str, object]:
    return realm_admin_service.reorder_realms(payload.get("keys", []))
```

```tsx
setStatusMessage(`境界已保存，并已重载运行时。当前共载入 ${result.realm_count} 个境界节点。`);
```

**Step 4: Run all verification**

Run: `python -m pytest tests/backend -q`
Expected: PASS

Run: `npm.cmd test`
Expected: PASS

Run: `npm.cmd run build`
Expected: PASS

**Step 5: Commit**

```bash
git add app/admin/services/realm_admin_service.py admin-console/src/pages/RealmListPage.tsx admin-console/src/pages/RealmEditorPage.tsx tests/backend/test_admin_realm_api.py admin-console/src/pages/RealmListPage.test.tsx admin-console/src/pages/RealmEditorPage.test.tsx docs/plans/2026-03-26-realm-admin-progress.md
git commit -m "feat: ship realm configuration admin flow"
```
