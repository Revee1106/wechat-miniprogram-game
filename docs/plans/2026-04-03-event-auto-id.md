# Event Auto ID Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically generate non-editable event IDs for new events in the admin console and recompute them when the new event type changes.

**Architecture:** Keep event ID generation in the admin console pages where new events are created, so the UI always has a stable `event_id` before save and before generating option IDs. Leave backend APIs unchanged and make the event template form display `event_id` as a disabled field.

**Tech Stack:** React, TypeScript, Vitest, Testing Library

---

### Task 1: Add the first failing tests for new-event auto IDs

**Files:**
- Modify: `admin-console/src/pages/EventEditorPage.test.tsx`
- Modify: `admin-console/src/pages/EventListPage.test.tsx`
- Test: `admin-console/src/pages/EventEditorPage.test.tsx`
- Test: `admin-console/src/pages/EventListPage.test.tsx`

**Step 1: Write the failing test**

- Add a page test proving `EventEditorPage` creates `evt_cultivation_<n>` for a new event and disables the field
- Add a page test proving `EventListPage` draft creation generates an ID and recomputes it when the type changes

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: FAIL because new events still start with an empty editable `event_id`

**Step 3: Write minimal implementation**

Do not implement yet. Add the component-level disabled-field guard in Task 2 first.

**Step 4: Run test to verify it passes**

Run after implementation: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 2: Add the failing component test for non-editable event IDs

**Files:**
- Modify: `admin-console/src/components/EventTemplateForm.test.tsx`
- Modify: `admin-console/src/components/EventTemplateForm.tsx`
- Test: `admin-console/src/components/EventTemplateForm.test.tsx`

**Step 1: Write the failing test**

Add a test that renders the identity section and asserts the “事件编号” input is disabled.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --run src/components/EventTemplateForm.test.tsx`
Expected: FAIL because the field is editable in new-event mode

**Step 3: Write minimal implementation**

Update `EventTemplateForm.tsx` so the event ID field is always disabled and no longer writes `event_id` from direct user input.

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- --run src/components/EventTemplateForm.test.tsx`
Expected: PASS

### Task 3: Implement shared event-ID generation in both event entry paths

**Files:**
- Modify: `admin-console/src/pages/EventEditorPage.tsx`
- Modify: `admin-console/src/pages/EventListPage.tsx`
- Test: `admin-console/src/pages/EventEditorPage.test.tsx`
- Test: `admin-console/src/pages/EventListPage.test.tsx`

**Step 1: Write the failing test**

If needed, refine page tests so they cover:
- initial new-event ID generation
- type-change recomputation
- gap-filling sequence selection

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: FAIL because page logic still initializes with blank IDs

**Step 3: Write minimal implementation**

- Add a helper that finds the next free `evt_<type>_<n>` in the current event library
- Use it when creating empty templates for new events
- In new-event mode only, recompute `event_id` when `event_type` changes
- Keep existing-event IDs untouched

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 4: Run focused verification and build

**Files:**
- Verify only

**Step 1: Run focused tests**

Run: `npm.cmd test -- --run src/components/EventTemplateForm.test.tsx src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: PASS

**Step 2: Run full admin suite**

Run: `npm.cmd test -- --run`
Expected: PASS

**Step 3: Run admin console build**

Run: `npm.cmd run build`
Expected: build succeeds

**Step 4: Commit**

```bash
git add admin-console/src/components/EventTemplateForm.tsx admin-console/src/components/EventTemplateForm.test.tsx admin-console/src/pages/EventEditorPage.tsx admin-console/src/pages/EventEditorPage.test.tsx admin-console/src/pages/EventListPage.tsx admin-console/src/pages/EventListPage.test.tsx docs/plans/2026-04-03-event-auto-id-design.md docs/plans/2026-04-03-event-auto-id.md
git commit -m "feat: auto generate event ids"
```
