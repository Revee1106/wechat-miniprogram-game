# Enemy Template Config Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a standalone enemy template config module to the admin console and runtime so combat events reference `enemy_template_id` instead of embedding enemy stats directly in each event option.

**Architecture:** Introduce a file-backed enemy template repository under `config/battle/enemies.json`, validate and expose it through admin APIs, and load it into `RunService` for combat resolution. Keep backward compatibility by continuing to accept legacy inline `battle` payloads when `enemy_template_id` is absent, while moving admin-console editing to the new template reference flow.

**Tech Stack:** FastAPI, Python dataclasses and services, JSON config repositories, React + TypeScript admin-console, pytest, Vitest

---

### Task 1: Add failing backend tests for enemy config repository and validation

**Files:**
- Create: `tests/backend/test_enemy_config_repository.py`
- Create: `tests/backend/test_enemy_validation_service.py`
- Create: `config/battle/enemies.json`

**Step 1: Write the failing test**

Add repository tests that expect:

```python
def test_repository_creates_default_enemy_config_file(tmp_path: Path) -> None:
    repository = EnemyConfigRepository(base_path=tmp_path)
    payload = repository.load()
    assert payload == {"items": []}
    assert (tmp_path / "config" / "battle" / "enemies.json").exists()
```

```python
def test_validate_enemy_config_accepts_valid_enemy_template() -> None:
    result = validate_enemy_config(
        enemies=[
            {
                "enemy_id": "enemy_bandit_qi_early",
                "enemy_name": "山匪",
                "enemy_realm_label": "炼气初期",
                "enemy_hp": 36,
                "enemy_attack": 8,
                "enemy_defense": 4,
                "enemy_speed": 6,
                "allow_flee": True,
                "rewards": {"resources": {"spirit_stone": 7}},
            }
        ]
    )
    assert result.is_valid is True
```

Also add failing validation coverage for duplicate `enemy_id`, invalid numeric bounds, and forbidden nested `battle` in `rewards`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_enemy_config_repository.py tests/backend/test_enemy_validation_service.py -q`

Expected: FAIL because enemy repository and validation service do not exist.

**Step 3: Write minimal implementation**

Create:

- `app/admin/repositories/enemy_config_repository.py`
- `app/admin/services/enemy_validation_service.py`

Implement only:

- default `{"items": []}` file creation
- repository `load()` and `save()`
- validation for required fields, uniqueness, numeric bounds, boolean `allow_flee`, and legal reward payload shape

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_enemy_config_repository.py tests/backend/test_enemy_validation_service.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_enemy_config_repository.py tests/backend/test_enemy_validation_service.py config/battle/enemies.json app/admin/repositories/enemy_config_repository.py app/admin/services/enemy_validation_service.py
git commit -m "test: add enemy config repository coverage"
```

### Task 2: Add failing backend tests for enemy admin service and API

**Files:**
- Create: `tests/backend/test_admin_enemy_api.py`
- Modify: `app/admin/api.py`
- Modify: `app/admin/schemas.py`

**Step 1: Write the failing test**

Add API tests that expect:

```python
def test_list_enemy_templates_returns_configured_items(client) -> None:
    response = client.get("/admin/api/battle/enemies")
    assert response.status_code == 200
    assert "items" in response.json()
```

```python
def test_create_enemy_template_persists_payload(client) -> None:
    response = client.post(
        "/admin/api/battle/enemies",
        json={
            "enemy_id": "enemy_bandit_qi_early",
            "enemy_name": "山匪",
            "enemy_realm_label": "炼气初期",
            "enemy_hp": 36,
            "enemy_attack": 8,
            "enemy_defense": 4,
            "enemy_speed": 6,
            "allow_flee": True,
            "rewards": {"resources": {"spirit_stone": 7}},
        },
    )
    assert response.status_code == 200
```

Also cover:

- detail endpoint
- update endpoint
- delete endpoint
- validate endpoint
- reload endpoint calling `run_service.reload_enemy_config(...)`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_admin_enemy_api.py -q`

Expected: FAIL because enemy admin routes and service do not exist.

**Step 3: Write minimal implementation**

Create `app/admin/services/enemy_admin_service.py` and wire routes in `app/admin/api.py`:

- `GET /admin/api/battle/enemies`
- `GET /admin/api/battle/enemies/{enemy_id}`
- `POST /admin/api/battle/enemies`
- `PUT /admin/api/battle/enemies/{enemy_id}`
- `DELETE /admin/api/battle/enemies/{enemy_id}`
- `POST /admin/api/battle/validate`
- `POST /admin/api/battle/reload`

Keep payloads dictionary-based like existing admin modules.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_admin_enemy_api.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_admin_enemy_api.py app/admin/api.py app/admin/schemas.py app/admin/services/enemy_admin_service.py
git commit -m "feat: add enemy admin api"
```

### Task 3: Add failing backend tests for combat runtime enemy template resolution

**Files:**
- Modify: `tests/backend/test_run_lifecycle.py`
- Modify: `app/core_loop/types.py`
- Modify: `app/core_loop/services/run_service.py`
- Modify: `app/core_loop/services/event_resolution_service.py`

**Step 1: Write the failing test**

Add tests that expect:

```python
def test_combat_option_resolves_enemy_from_enemy_template_id() -> None:
    service = RunService(event_config_base_path=str(base_path))
    run = service.create_run(player_id="p1")
    # attach event option with enemy_template_id
    resolved = service.resolve_event(run.run_id, "opt_fight")
    assert resolved.active_battle is not None
    assert resolved.active_battle.enemy.name == "山匪"
```

```python
def test_combat_victory_uses_enemy_template_rewards() -> None:
    finished = service.perform_battle_action(run.run_id, "attack")
    assert finished.resources.spirit_stone == 12
    assert finished.character.cultivation_exp == 5
```

Also add a compatibility test proving a legacy inline `battle` payload still works when `enemy_template_id` is missing.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_run_lifecycle.py -q`

Expected: FAIL because event options do not support `enemy_template_id` and runtime cannot resolve enemy templates.

**Step 3: Write minimal implementation**

Modify:

- `EventOptionConfig` to include `enemy_template_id: str | None = None`
- `RunService` to load enemy config and rebuild runtime services with it
- `EventResolutionService` to:
  - resolve combat templates by `enemy_template_id`
  - build `ActiveBattleState.enemy` from template data
  - use template `rewards` as success payload on victory
  - fall back to legacy inline `battle` when template id is absent

Add `reload_enemy_config(...)` to `RunService`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_run_lifecycle.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_run_lifecycle.py app/core_loop/types.py app/core_loop/services/run_service.py app/core_loop/services/event_resolution_service.py
git commit -m "feat: load combat enemy templates in runtime"
```

### Task 4: Add failing backend tests for event validation with enemy template references

**Files:**
- Modify: `tests/backend/test_event_config_validation.py`
- Modify: `app/admin/services/event_validation_service.py`
- Modify: `app/admin/services/event_admin_service.py`

**Step 1: Write the failing test**

Add tests that expect:

```python
def test_combat_option_requires_existing_enemy_template_id() -> None:
    result = validate_event_config(
        templates=[...],
        options=[
            {
                "option_id": "opt_fight",
                "event_id": "evt_bandit",
                "resolution_mode": "combat",
                "enemy_template_id": "missing_enemy",
            }
        ],
        enemy_ids={"enemy_bandit_qi_early"},
    )
    assert result.is_valid is False
```

Also add coverage for:

- valid `enemy_template_id`
- legacy inline `battle` still accepted when `enemy_template_id` absent
- `enemy_template_id` preferred over inline `battle` when both exist

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_event_config_validation.py -q`

Expected: FAIL because event validation does not know enemy template ids.

**Step 3: Write minimal implementation**

Update `validate_event_config(...)` to accept enemy template identifiers from repository-backed config and validate combat options accordingly. Update `EventAdminService.validate_current_config()` and `reload_runtime_config()` to pass enemy ids into validation.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_event_config_validation.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_event_config_validation.py app/admin/services/event_validation_service.py app/admin/services/event_admin_service.py
git commit -m "feat: validate combat enemy template references"
```

### Task 5: Add failing admin-console tests for battle config pages

**Files:**
- Create: `admin-console/src/pages/BattleEnemyListPage.test.tsx`
- Create: `admin-console/src/pages/BattleEnemyEditorPage.test.tsx`
- Modify: `admin-console/src/api/client.ts`
- Modify: `admin-console/src/App.tsx`

**Step 1: Write the failing test**

Add Vitest coverage that expects:

```tsx
test("renders enemy templates in the battle list page", async () => {
  render(<BattleEnemyListPage />);
  expect(await screen.findByText("山匪")).toBeInTheDocument();
});
```

```tsx
test("saves edited enemy template from editor page", async () => {
  render(<BattleEnemyEditorPage enemyId="enemy_bandit_qi_early" />);
  await userEvent.clear(screen.getByLabelText("敌人名称"));
  await userEvent.type(screen.getByLabelText("敌人名称"), "山匪头目");
  await userEvent.click(screen.getByRole("button", { name: "保存敌人模板" }));
});
```

Also add assertions for:

- top-level `战斗配置` navigation button
- validation and reload actions
- create and delete flows

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/pages/BattleEnemyListPage.test.tsx src/pages/BattleEnemyEditorPage.test.tsx`

Workdir: `E:\game\wechat-miniprogram-game\admin-console`

Expected: FAIL because battle config pages and client methods do not exist.

**Step 3: Write minimal implementation**

Add:

- battle enemy client types and CRUD methods in `src/api/client.ts`
- `BattleEnemyListPage.tsx`
- `BattleEnemyEditorPage.tsx`
- `App.tsx` navigation wiring for `view === "battle"`

Reuse the existing console layout and validation panel patterns.

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/pages/BattleEnemyListPage.test.tsx src/pages/BattleEnemyEditorPage.test.tsx`

Workdir: `E:\game\wechat-miniprogram-game\admin-console`

Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/pages/BattleEnemyListPage.test.tsx admin-console/src/pages/BattleEnemyEditorPage.test.tsx admin-console/src/pages/BattleEnemyListPage.tsx admin-console/src/pages/BattleEnemyEditorPage.tsx admin-console/src/api/client.ts admin-console/src/App.tsx
git commit -m "feat: add battle config console pages"
```

### Task 6: Add failing admin-console tests for event option enemy template selection

**Files:**
- Modify: `admin-console/src/components/EventOptionEditor.test.tsx`
- Modify: `admin-console/src/components/EventOptionEditor.tsx`
- Modify: `admin-console/src/pages/EventEditorPage.tsx`
- Modify: `admin-console/src/api/client.ts`

**Step 1: Write the failing test**

Add tests that expect:

```tsx
test("combat option shows enemy template select instead of inline enemy stat fields", async () => {
  render(<EventOptionEditor ... />);
  expect(screen.getByLabelText("敌人模板")).toBeInTheDocument();
  expect(screen.queryByLabelText("敌人名称")).not.toBeInTheDocument();
});
```

```tsx
test("saving combat option persists enemy_template_id", async () => {
  // choose template and save event
  expect(updateOption).toHaveBeenCalledWith(
    "opt_fight",
    expect.objectContaining({ enemy_template_id: "enemy_bandit_qi_early" })
  );
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Workdir: `E:\game\wechat-miniprogram-game\admin-console`

Expected: FAIL because event editor still uses inline combat payload editing.

**Step 3: Write minimal implementation**

Update client and form types to include `enemy_template_id`. In `EventOptionEditor.tsx`:

- load enemy template options passed from parent
- show template selector for combat mode
- remove inline enemy stat editing
- keep failure payload and event-level logs

Update `EventEditorPage.tsx` to fetch enemy templates for combat option editing and persist `enemy_template_id`.

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Workdir: `E:\game\wechat-miniprogram-game\admin-console`

Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/components/EventOptionEditor.test.tsx admin-console/src/components/EventOptionEditor.tsx admin-console/src/pages/EventEditorPage.tsx admin-console/src/api/client.ts
git commit -m "feat: reference enemy templates in event combat options"
```

### Task 7: Verify full backend and admin-console coverage

**Files:**
- Modify: `docs/plans/2026-04-10-combat-system-v1-progress.md`

**Step 1: Write the failing test**

No new test file. This is a verification and documentation task.

**Step 2: Run test to verify current full suite status**

Run: `python -m pytest tests/backend -q`

Workdir: `E:\game\wechat-miniprogram-game`

Expected: PASS

Run: `npm test -- --run`

Workdir: `E:\game\wechat-miniprogram-game\admin-console`

Expected: PASS

**Step 3: Write minimal implementation**

Update the combat progress doc with:

- enemy template config shipped
- runtime compatibility status
- admin-console pages shipped

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend -q`

Workdir: `E:\game\wechat-miniprogram-game`

Expected: PASS

Run: `npm test -- --run`

Workdir: `E:\game\wechat-miniprogram-game\admin-console`

Expected: PASS

**Step 5: Commit**

```bash
git add docs/plans/2026-04-10-combat-system-v1-progress.md
git commit -m "docs: record enemy template config progress"
```
