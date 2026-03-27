# Result Resource Editor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace free-text result resource editing with a structured, Chinese-labeled resource selector for admin users.

**Architecture:** Add a shared resource catalog for canonical keys, labels, and legacy aliases, then rebuild the result payload resource editor around selector rows. Keep the backend payload shape unchanged and normalize legacy resource aliases on load/save.

**Tech Stack:** React, TypeScript, Vitest, existing admin-console payload codec utilities

---

### Task 1: Define canonical resource metadata

**Files:**
- Create: `admin-console/src/utils/resourceCatalog.ts`
- Test: `admin-console/src/components/ResultPayloadEditor.test.tsx`

**Step 1: Write the failing test**

- Add a test that renders a result payload with legacy keys like `herbs` and `iron_essence` and expects the editor to expose canonical selectable rows.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/components/ResultPayloadEditor.test.tsx`
Expected: FAIL because the editor still renders a textarea and has no canonical resource catalog.

**Step 3: Write minimal implementation**

- Add canonical resource options and labels.
- Add helper functions to normalize legacy aliases into canonical keys.

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/components/ResultPayloadEditor.test.tsx`
Expected: PASS

### Task 2: Replace result resource textarea with selector rows

**Files:**
- Modify: `admin-console/src/components/ResultPayloadEditor.tsx`
- Modify: `admin-console/src/styles/admin-theme.css`
- Test: `admin-console/src/components/ResultPayloadEditor.test.tsx`

**Step 1: Write the failing test**

- Add a test that adds a second resource row, selects a predefined resource, edits the amount, and expects `onChange` to receive a structured `resources` payload without duplicate keys.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/components/ResultPayloadEditor.test.tsx`
Expected: FAIL because the component still uses a plain textarea.

**Step 3: Write minimal implementation**

- Replace the textarea with selector rows.
- Add add/remove row actions.
- Prevent duplicate resource selection.
- Keep other payload fields unchanged.

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/components/ResultPayloadEditor.test.tsx`
Expected: PASS

### Task 3: Normalize resource payloads in codec layer

**Files:**
- Modify: `admin-console/src/utils/eventFormCodec.ts`
- Test: `admin-console/src/utils/eventFormCodec.test.ts`

**Step 1: Write the failing test**

- Add a codec test ensuring payloads with `herbs` / `iron_essence` normalize to canonical editor keys while preserving values.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/utils/eventFormCodec.test.ts`
Expected: FAIL because current parsing preserves raw keys.

**Step 3: Write minimal implementation**

- Normalize `payload.resources` through the shared resource catalog.
- Ensure build helpers omit zero-value rows and emit canonical keys.

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/utils/eventFormCodec.test.ts`
Expected: PASS

### Task 4: Update integration coverage and verify the full admin console

**Files:**
- Modify: `admin-console/src/pages/EventEditorPage.test.tsx`

**Step 1: Write the failing test**

- Update the event editor test to configure resource gains through the new selector UI and expect the saved option payload to contain canonical resources.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/pages/EventEditorPage.test.tsx`
Expected: FAIL until the new UI is wired through the page.

**Step 3: Write minimal implementation**

- Adjust any labels or helper wiring needed so the page test can drive the structured editor.

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/pages/EventEditorPage.test.tsx`
Expected: PASS

### Task 5: Full verification

**Files:**
- Verify only

**Step 1: Run admin console tests**

Run: `npm.cmd test`
Expected: PASS

**Step 2: Run admin console build**

Run: `npm.cmd run build`
Expected: PASS

**Step 3: Run backend regression tests**

Run: `python.exe -m pytest tests/backend -q`
Expected: PASS
