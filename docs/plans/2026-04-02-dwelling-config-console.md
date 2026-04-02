# Dwelling Config Console Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dwelling configuration console so admins can edit per-level dwelling costs, upkeep, yields, and current special effects, with runtime reload and startup reading from config files.

**Architecture:** Move dwelling facility definitions out of `DwellingService` hardcoded builders into a JSON config repository, validate and expose them through admin APIs, then add matching admin-console list/editor pages. Keep runtime save format file-based to match existing event/realm config modules, and preserve run-state compatibility by continuing to hydrate facility state from config on each run load.

**Tech Stack:** FastAPI, Python dataclass services, JSON config repositories, React + TypeScript admin-console, Vitest, pytest

---

### Task 1: Add failing backend tests for dwelling config repository and validation

**Files:**
- Create: `tests/backend/test_dwelling_config_repository.py`
- Create: `tests/backend/test_dwelling_validation_service.py`

**Step 1: Write the failing tests**

Add tests that expect:
- repository creates and loads `config/dwelling/facilities.json`
- valid per-level config passes validation
- invalid non-contiguous levels fail validation
- invalid special effect keys fail validation

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_dwelling_config_repository.py tests/backend/test_dwelling_validation_service.py -q`
Expected: FAIL because repository and validation service do not exist

**Step 3: Write minimal implementation**

Create repository and validation service modules with only the behaviors needed by the tests.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_dwelling_config_repository.py tests/backend/test_dwelling_validation_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_dwelling_config_repository.py tests/backend/test_dwelling_validation_service.py app/admin/repositories/dwelling_config_repository.py app/admin/services/dwelling_validation_service.py config/dwelling/facilities.json
git commit -m "test: add dwelling config repository coverage"
```

### Task 2: Add failing backend tests for admin dwelling APIs

**Files:**
- Create: `tests/backend/test_admin_dwelling_api.py`
- Modify: `app/admin/api.py`

**Step 1: Write the failing tests**

Add tests that expect:
- facility list endpoint returns configured facilities
- detail endpoint returns one facility
- update endpoint persists edited levels and special effects
- reload endpoint calls run-service reload hook

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_admin_dwelling_api.py -q`
Expected: FAIL because endpoints and service do not exist

**Step 3: Write minimal implementation**

Add admin service and API routes to satisfy the tests.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_admin_dwelling_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_admin_dwelling_api.py app/admin/api.py app/admin/services/dwelling_admin_service.py
git commit -m "feat: add dwelling admin api"
```

### Task 3: Add failing backend tests for DwellingService runtime config loading

**Files:**
- Modify: `tests/backend/test_dwelling_service.py`
- Modify: `app/core_loop/services/dwelling_service.py`
- Modify: `app/core_loop/services/run_service.py`

**Step 1: Write the failing tests**

Add tests that expect:
- custom JSON config changes facility costs/yields
- adding level 4 in config allows upgrading to level 4
- spirit gathering array special effect config changes breakthrough or mine yield bonus

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_dwelling_service.py -q`
Expected: FAIL because service still reads hardcoded config

**Step 3: Write minimal implementation**

Replace hardcoded config source with repository loading and add reload support through `RunService`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_dwelling_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/backend/test_dwelling_service.py app/core_loop/services/dwelling_service.py app/core_loop/services/run_service.py
git commit -m "feat: load dwelling runtime config from json"
```

### Task 4: Add failing admin-console tests for dwelling pages

**Files:**
- Create: `admin-console/src/pages/DwellingListPage.test.tsx`
- Create: `admin-console/src/pages/DwellingEditorPage.test.tsx`
- Modify: `admin-console/src/api/client.ts`
- Modify: `admin-console/src/App.tsx`

**Step 1: Write the failing tests**

Add tests that expect:
- dwelling list page renders facility cards from API
- dwelling editor loads a facility and saves updates
- editor can append a new level row
- app navigation exposes the dwelling config section

**Step 2: Run test to verify it fails**

Run: `npm test -- --run DwellingListPage.test.tsx DwellingEditorPage.test.tsx`
Expected: FAIL because pages and APIs do not exist

**Step 3: Write minimal implementation**

Add typed client methods, list/editor pages, and navigation wiring.

**Step 4: Run test to verify it passes**

Run: `npm test -- --run DwellingListPage.test.tsx DwellingEditorPage.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/pages/DwellingListPage.test.tsx admin-console/src/pages/DwellingEditorPage.test.tsx admin-console/src/pages/DwellingListPage.tsx admin-console/src/pages/DwellingEditorPage.tsx admin-console/src/api/client.ts admin-console/src/App.tsx
git commit -m "feat: add dwelling config console pages"
```

### Task 5: Verify end-to-end backend and frontend coverage

**Files:**
- Modify: `docs/2026-04-02-completed-features.md`

**Step 1: Write the failing test**

No new test file; verification task only.

**Step 2: Run test to verify current full suite status**

Run: `python -m pytest tests/backend -q`
Expected: PASS

Run: `npm test -- --run`
Expected: PASS for admin-console tests

**Step 3: Write minimal implementation**

Update docs to mention dwelling config console once verification passes.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend -q`
Expected: PASS

Run: `npm test -- --run`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/2026-04-02-completed-features.md
git commit -m "docs: document dwelling config console"
```
