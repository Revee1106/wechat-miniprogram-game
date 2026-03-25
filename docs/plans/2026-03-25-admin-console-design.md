# Wendao Admin Console Design

**Date:** 2026-03-25

## Background

The current backend project only exposes gameplay APIs for the mini program. Event configuration is still maintained in Python source files, which is workable for engineering iteration but not suitable for long-term content operations or non-code maintenance.

The next stage needs a control console that can manage event templates and options through a UI, and later expand to other game configuration domains such as progression, drops, resources, and rebirth tuning.

## Goals

- Add a maintainable admin console for backend configuration management.
- Support event template and event option CRUD as the first managed domain.
- Keep gameplay runtime and config editing concerns separated.
- Create a structure that can later extend to other config domains without redesigning the system.

## Non-Goals

- No full RBAC or SSO in the first version.
- No multi-user locking, approval workflows, or audit pipelines.
- No generic low-code rule builder.
- No database migration in the first version.

## Recommended Architecture

Use a split admin frontend plus backend admin API, deployed through the same FastAPI service.

### Layers

1. Runtime gameplay layer
- Existing `/api/*` endpoints remain focused on run lifecycle and gameplay.

2. Admin API layer
- New `/admin/api/*` endpoints provide config-oriented CRUD, validation, and reload actions.

3. Shared config service layer
- A shared service translates persisted config files into runtime `EventTemplateConfig` and `EventOptionConfig` objects.
- Both gameplay runtime and admin API use this shared layer so there is only one source of truth.

4. Admin frontend layer
- A separate frontend app lives in the repository as `admin-console/`.
- Its built assets are served by FastAPI at `/admin`.

## Why This Structure

### Option A: Server-rendered HTML in FastAPI

Pros:
- Fastest initial delivery
- Minimal dependencies

Cons:
- Poor maintainability for nested event structures
- Harder to evolve into a broader configuration console

### Option B: Generic admin framework

Pros:
- Quick CRUD scaffolding for simple models

Cons:
- Current configuration is not a clean ORM-backed admin problem
- Nested event-template and event-option editing would still need custom work

### Option C: Separate admin frontend plus backend admin API

Pros:
- Best long-term structure
- Good fit for nested config editing
- Easy to extend into additional config domains
- Clear boundary between runtime and editing concerns

Cons:
- Slightly more initial setup than server-rendered pages

### Recommendation

Choose Option C.

It gives the best maintenance story without overcommitting to a database or a heavyweight admin platform too early.

## Data Storage Strategy

Move editable event configuration out of Python source and into JSON files.

### First-Version Storage

- `config/events/templates.json`
- `config/events/options.json`

### Why JSON First

- Safe and predictable for backend read/write.
- Easy for the admin frontend to reason about.
- Easier to validate than editing Python source.
- Straightforward migration path to database-backed storage later.

### Runtime Loading

Introduce an `EventConfigRepository` that:

- reads JSON files
- validates and normalizes them
- builds the runtime registry used by gameplay services

The gameplay runtime should no longer depend directly on `event_templates.py` and `event_options.py` once this migration is complete.

## Backend Admin API Design

Create a dedicated admin router mounted under `/admin/api`.

### Event Endpoints

- `GET /admin/api/events`
  Returns the event list with filters for `event_type`, `risk_level`, and keyword.

- `GET /admin/api/events/{event_id}`
  Returns one template plus its associated options.

- `POST /admin/api/events`
  Creates a new event template.

- `PUT /admin/api/events/{event_id}`
  Updates an existing event template.

- `DELETE /admin/api/events/{event_id}`
  Deletes the template and its options.

- `POST /admin/api/events/{event_id}/options`
  Creates an option under one event.

- `PUT /admin/api/options/{option_id}`
  Updates an option.

- `DELETE /admin/api/options/{option_id}`
  Deletes an option.

- `POST /admin/api/events/validate`
  Runs full config validation and returns errors or warnings.

- `POST /admin/api/events/reload`
  Reloads runtime config from persisted files.

## Validation Model

Validation runs in two phases.

### Form-Level Validation

Checks single-entity correctness:

- required fields
- enum values
- numeric ranges
- ID shape
- empty option lists

### Full Configuration Validation

Checks cross-entity correctness:

- unique `event_id`
- unique `option_id`
- `option.event_id` must exist
- `template.option_ids` must match actual options
- valid `next_event_id`
- only one default option where required
- no conflicting `equipment_add` and `equipment_remove`

## Runtime Safety Model

Saving config and activating config are separate actions.

### Save

- Admin UI writes JSON successfully.
- Config is persisted to disk.
- Validation results are returned immediately.

### Reload

- Runtime registry is reloaded explicitly.
- If reload validation fails, runtime keeps the last known good registry.

This prevents an invalid edit from breaking the live gameplay loop.

## Admin Frontend Design

The admin frontend should start with three views.

### 1. Event List Page

Features:

- filter by `event_type`
- filter by `risk_level`
- keyword search
- list summary columns:
  - event name
  - event type
  - risk level
  - option count
  - repeatability
- actions:
  - create event
  - validate config
  - reload config

### 2. Event Editor Page

Single-page structured editor for:

- template fields
- option list
- option ordering
- default option selection
- structured result payload editing

### 3. Validation / Preview Panel

Shows:

- normalized runtime shape preview
- validation errors and warnings
- save/reload status

## Frontend Technology Choice

Use a lightweight but maintainable frontend stack:

- React
- TypeScript
- Vite

### Why

- Better maintainability for nested form state
- Easier future expansion into multiple config domains
- Fast local iteration and clean build output

### Deployment Model

- Source: `admin-console/`
- Build output: `admin-console/dist/`
- FastAPI serves built files at `/admin`

## Repository Layout

Recommended additions:

```text
wechat-miniprogram-game/
  app/
    admin/
      api.py
      schemas.py
      services/
        event_admin_service.py
      repositories/
        event_config_repository.py
      runtime/
        event_runtime_registry.py
  config/
    events/
      templates.json
      options.json
  admin-console/
    package.json
    vite.config.ts
    src/
      main.tsx
      App.tsx
      api/
      pages/
      components/
  docs/
    plans/
```

## First-Version Scope

Build only the minimum viable admin console:

- event template CRUD
- event option CRUD
- config validation
- config reload
- event list filtering

Do not build in v1:

- auth
- audit history
- generic settings center
- workflow approvals
- visual rule builder

## Testing Strategy

### Backend

- repository load/save tests
- admin API CRUD tests
- validation tests
- reload tests
- integration test proving saved config becomes runtime config after reload

### Frontend

- smoke test for routing and core views
- API contract tests for list/detail/save flows
- editor state tests for option add/remove ordering

## Rollout Plan

1. Extract event configuration storage from Python seed files into JSON.
2. Introduce repository and validation service.
3. Add admin API endpoints.
4. Build admin frontend for event CRUD.
5. Add explicit reload and validation actions.
6. Retire direct runtime dependence on editable Python config files.

## Future Extension Path

Once the console works for events, the same structure can support:

- progression configs
- breakthrough tuning
- rebirth tuning
- resource generation configs
- loot and crafting configs

The key rule is to keep runtime services consuming validated shared models, not raw frontend payloads.
