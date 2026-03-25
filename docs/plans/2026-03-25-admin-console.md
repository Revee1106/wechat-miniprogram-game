# Admin Console Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a maintainable admin console for the backend project so event template and option configuration can be managed through UI-driven CRUD instead of direct code edits.

**Architecture:** Migrate editable event configuration into JSON files, add a shared backend repository and validation service, expose admin-only CRUD and reload APIs under `/admin/api`, and add a separate React/Vite admin frontend served by FastAPI at `/admin`. Keep gameplay runtime and admin editing concerns separated while sharing the same normalized event model.

**Tech Stack:** FastAPI, Python dataclasses, pytest, React, TypeScript, Vite

---

### Task 1: Create JSON-backed event config storage and repository

**Files:**
- Create: `config/events/templates.json`
- Create: `config/events/options.json`
- Create: `app/admin/repositories/event_config_repository.py`
- Modify: `app/core_loop/event_config.py`
- Test: `tests/backend/test_event_config_repository.py`

**Step 1: Write the failing test**

```python
from app.admin.repositories.event_config_repository import EventConfigRepository


def test_repository_loads_templates_and_options_from_json(tmp_path) -> None:
    repo = EventConfigRepository(base_path=tmp_path)
    repo.save({"templates": [{"event_id": "evt_one", "event_name": "One"}], "options": []})

    loaded = repo.load()

    assert loaded["templates"][0]["event_id"] == "evt_one"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_event_config_repository.py -q`
Expected: FAIL because the repository does not exist yet.

**Step 3: Write minimal implementation**

Create a repository that:
- reads `templates.json` and `options.json`
- writes full-file replacements
- returns plain dictionaries for admin editing
- exposes a conversion path used later by runtime loading

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_event_config_repository.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add config/events/templates.json config/events/options.json app/admin/repositories/event_config_repository.py app/core_loop/event_config.py tests/backend/test_event_config_repository.py
git commit -m "feat: add json-backed event config repository"
```

### Task 2: Add full event-config validation service

**Files:**
- Create: `app/admin/services/event_validation_service.py`
- Modify: `app/core_loop/types.py`
- Test: `tests/backend/test_event_config_validation.py`

**Step 1: Write the failing test**

```python
from app.admin.services.event_validation_service import validate_event_config


def test_validation_rejects_missing_option_reference() -> None:
    result = validate_event_config(
        templates=[{"event_id": "evt_one", "option_ids": ["opt_missing"]}],
        options=[],
    )

    assert result.is_valid is False
    assert "opt_missing" in result.errors[0]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_event_config_validation.py -q`
Expected: FAIL because the validator does not exist yet.

**Step 3: Write minimal implementation**

Implement validation for:
- unique IDs
- enum vocabulary
- positive weights
- valid `sort_order`
- template-option linkage
- valid `next_event_id`
- conflicting equipment mutations

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_event_config_validation.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/admin/services/event_validation_service.py app/core_loop/types.py tests/backend/test_event_config_validation.py
git commit -m "feat: add event config validation service"
```

### Task 3: Switch runtime loading to repository-backed config

**Files:**
- Modify: `app/core_loop/event_config.py`
- Modify: `app/core_loop/services/event_service.py`
- Test: `tests/backend/test_event_config_registry.py`
- Test: `tests/backend/test_event_generation_filters.py`

**Step 1: Write the failing test**

```python
from app.core_loop.event_config import load_event_registry


def test_runtime_registry_loads_from_repository_files(tmp_path) -> None:
    registry = load_event_registry(base_path=tmp_path)
    assert registry.templates
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_event_config_registry.py tests/backend/test_event_generation_filters.py -q`
Expected: FAIL because runtime still depends on Python seed constants.

**Step 3: Write minimal implementation**

Make runtime loading:
- read from repository-backed JSON
- normalize into runtime dataclasses
- preserve existing runtime behavior

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_event_config_registry.py tests/backend/test_event_generation_filters.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/core_loop/event_config.py app/core_loop/services/event_service.py tests/backend/test_event_config_registry.py tests/backend/test_event_generation_filters.py
git commit -m "feat: load runtime event registry from repository"
```

### Task 4: Add admin schemas and event admin service

**Files:**
- Create: `app/admin/schemas.py`
- Create: `app/admin/services/event_admin_service.py`
- Test: `tests/backend/test_admin_event_service.py`

**Step 1: Write the failing test**

```python
from app.admin.services.event_admin_service import EventAdminService


def test_service_returns_event_detail_with_options(tmp_path) -> None:
    service = EventAdminService(base_path=tmp_path)

    detail = service.get_event("evt_sample")

    assert detail["template"]["event_id"] == "evt_sample"
    assert isinstance(detail["options"], list)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_admin_event_service.py -q`
Expected: FAIL because the service layer does not exist yet.

**Step 3: Write minimal implementation**

Create a service that supports:
- list events
- get one event with options
- create/update/delete template
- create/update/delete option
- validate current config
- reload runtime config

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_admin_event_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/admin/schemas.py app/admin/services/event_admin_service.py tests/backend/test_admin_event_service.py
git commit -m "feat: add admin event service layer"
```

### Task 5: Add admin API router

**Files:**
- Create: `app/admin/api.py`
- Modify: `app/api/router.py`
- Test: `tests/backend/test_admin_event_api.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_admin_event_list_endpoint_returns_events() -> None:
    response = client.get("/admin/api/events")

    assert response.status_code == 200
    assert "items" in response.json()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_admin_event_api.py -q`
Expected: FAIL because the admin router is not mounted.

**Step 3: Write minimal implementation**

Expose:
- `GET /admin/api/events`
- `GET /admin/api/events/{event_id}`
- `POST /admin/api/events`
- `PUT /admin/api/events/{event_id}`
- `DELETE /admin/api/events/{event_id}`
- `POST /admin/api/events/{event_id}/options`
- `PUT /admin/api/options/{option_id}`
- `DELETE /admin/api/options/{option_id}`
- `POST /admin/api/events/validate`
- `POST /admin/api/events/reload`

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_admin_event_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/admin/api.py app/api/router.py tests/backend/test_admin_event_api.py
git commit -m "feat: expose admin event crud api"
```

### Task 6: Scaffold admin frontend application

**Files:**
- Create: `admin-console/package.json`
- Create: `admin-console/tsconfig.json`
- Create: `admin-console/vite.config.ts`
- Create: `admin-console/index.html`
- Create: `admin-console/src/main.tsx`
- Create: `admin-console/src/App.tsx`
- Create: `admin-console/src/api/client.ts`
- Test: `admin-console/src/App.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import App from "./App";

test("shows event console shell", () => {
  render(<App />);
  expect(screen.getByText("Event Console")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand`
Expected: FAIL because the admin frontend app does not exist.

**Step 3: Write minimal implementation**

Scaffold a React/Vite app with:
- app shell
- API client
- placeholder event list layout

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/package.json admin-console/tsconfig.json admin-console/vite.config.ts admin-console/index.html admin-console/src/main.tsx admin-console/src/App.tsx admin-console/src/api/client.ts admin-console/src/App.test.tsx
git commit -m "feat: scaffold admin console frontend"
```

### Task 7: Build event list and filtering UI

**Files:**
- Create: `admin-console/src/pages/EventListPage.tsx`
- Create: `admin-console/src/components/EventFilters.tsx`
- Create: `admin-console/src/components/EventTable.tsx`
- Modify: `admin-console/src/App.tsx`
- Test: `admin-console/src/pages/EventListPage.test.tsx`

**Step 1: Write the failing test**

```tsx
test("filters events by type", async () => {
  render(<EventListPage />);
  expect(await screen.findByText("cultivation")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand`
Expected: FAIL because the page and filters are not implemented.

**Step 3: Write minimal implementation**

Implement:
- list fetch
- event type filter
- risk level filter
- keyword search
- create-event button

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/pages/EventListPage.tsx admin-console/src/components/EventFilters.tsx admin-console/src/components/EventTable.tsx admin-console/src/App.tsx admin-console/src/pages/EventListPage.test.tsx
git commit -m "feat: add admin event list and filters"
```

### Task 8: Build event editor and option editor

**Files:**
- Create: `admin-console/src/pages/EventEditorPage.tsx`
- Create: `admin-console/src/components/EventTemplateForm.tsx`
- Create: `admin-console/src/components/EventOptionEditor.tsx`
- Create: `admin-console/src/components/ValidationPanel.tsx`
- Test: `admin-console/src/pages/EventEditorPage.test.tsx`

**Step 1: Write the failing test**

```tsx
test("adds a new option row", async () => {
  render(<EventEditorPage />);
  expect(await screen.findByText("Add Option")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand`
Expected: FAIL because the editor UI does not exist.

**Step 3: Write minimal implementation**

Build structured forms for:
- template fields
- option CRUD
- option ordering
- default-option selection
- validation result display

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/pages/EventEditorPage.tsx admin-console/src/components/EventTemplateForm.tsx admin-console/src/components/EventOptionEditor.tsx admin-console/src/components/ValidationPanel.tsx admin-console/src/pages/EventEditorPage.test.tsx
git commit -m "feat: add admin event editor"
```

### Task 9: Serve built admin frontend from FastAPI

**Files:**
- Modify: `app/main.py`
- Create: `app/admin/static.py`
- Test: `tests/backend/test_admin_frontend_mount.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_admin_frontend_is_served() -> None:
    response = client.get("/admin")
    assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_admin_frontend_mount.py -q`
Expected: FAIL because no admin frontend mount exists.

**Step 3: Write minimal implementation**

Mount built frontend assets under `/admin` while preserving `/admin/api/*` routes.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_admin_frontend_mount.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add app/main.py app/admin/static.py tests/backend/test_admin_frontend_mount.py
git commit -m "feat: mount admin console frontend"
```

### Task 10: Run full verification

**Files:**
- Modify: `tests/backend/test_admin_event_api.py`
- Modify: `tests/backend/test_event_config_registry.py`
- Modify: `tests/backend/test_core_loop_api.py`

**Step 1: Run backend verification**

Run: `python -m pytest tests/backend -q`
Expected: PASS

**Step 2: Run frontend verification**

Run: `npm test -- --runInBand`
Expected: PASS

**Step 3: Run admin frontend build**

Run: `npm run build`
Expected: PASS

**Step 4: Commit**

```bash
git add tests/backend/test_admin_event_api.py tests/backend/test_event_config_registry.py tests/backend/test_core_loop_api.py
git commit -m "test: verify admin console and runtime config integration"
```
