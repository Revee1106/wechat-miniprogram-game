# Event Option Auto ID Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically generate non-editable option IDs when adding event options in the admin console.

**Architecture:** Keep ID generation in the admin console page state where new options are created, so both event editor entry points can produce complete option records before save. Leave backend APIs unchanged and make the option editor render `option_id` as a disabled display field.

**Tech Stack:** React, TypeScript, Vitest, Testing Library

---

### Task 1: Add the first failing page test for auto-generated option IDs

**Files:**
- Modify: `admin-console/src/pages/EventEditorPage.test.tsx`
- Test: `admin-console/src/pages/EventEditorPage.test.tsx`

**Step 1: Write the failing test**

Add a test that opens the “选项编排” panel, clicks “新增选项”, and asserts the new option gets an auto-generated ID such as `event_option_2` or `evt_xxx_option_2`.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx`
Expected: FAIL because new options still start with an empty `option_id`.

**Step 3: Write minimal implementation**

Do not implement yet. Move to Task 2 first if a component-level guard is clearer.

**Step 4: Run test to verify it passes**

Run after implementation: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx`
Expected: PASS

### Task 2: Add the failing component test for non-editable option IDs

**Files:**
- Modify: `admin-console/src/components/EventOptionEditor.test.tsx`
- Test: `admin-console/src/components/EventOptionEditor.test.tsx`

**Step 1: Write the failing test**

Add a test that renders `EventOptionEditor` with a new option and asserts the “选项编号” input is disabled.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --run src/components/EventOptionEditor.test.tsx`
Expected: FAIL because new options are still editable.

**Step 3: Write minimal implementation**

Update `EventOptionEditor.tsx` so the option ID field is always disabled and no longer writes `option_id` through `onChange`.

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- --run src/components/EventOptionEditor.test.tsx`
Expected: PASS

### Task 3: Implement shared auto-ID generation in both event editor pages

**Files:**
- Modify: `admin-console/src/pages/EventEditorPage.tsx`
- Modify: `admin-console/src/pages/EventListPage.tsx`
- Test: `admin-console/src/pages/EventEditorPage.test.tsx`
- Test: `admin-console/src/pages/EventListPage.test.tsx`

**Step 1: Write the failing test**

If needed, add a second page test in `EventListPage.test.tsx` to cover the compact workbench entry path.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: FAIL because add-option logic still uses empty IDs.

**Step 3: Write minimal implementation**

- Add a helper that picks the next free `${prefix}_option_${n}` ID
- Use current `event_id` when present, otherwise `event`
- Call it from both `handleAddOption()` implementations
- Create new options with the generated ID and the correct `sort_order`

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- --run src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 4: Run focused verification and build

**Files:**
- Verify only

**Step 1: Run focused tests**

Run: `npm.cmd test -- --run src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx src/pages/EventListPage.test.tsx`
Expected: PASS

**Step 2: Run admin console build**

Run: `npm.cmd run build`
Expected: build succeeds

**Step 3: Commit**

```bash
git add admin-console/src/components/EventOptionEditor.tsx admin-console/src/components/EventOptionEditor.test.tsx admin-console/src/pages/EventEditorPage.tsx admin-console/src/pages/EventEditorPage.test.tsx admin-console/src/pages/EventListPage.tsx admin-console/src/pages/EventListPage.test.tsx docs/plans/2026-04-03-event-option-auto-id-design.md docs/plans/2026-04-03-event-option-auto-id.md
git commit -m "feat: auto generate event option ids"
```
