# Event Drawer Editor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the event page's inline detail form with a compact summary dashboard and right-side drawer editing flow.

**Architecture:** Keep the current event loading and save pipeline in `EventListPage`, but split the UI into a summary surface and a module drawer. The main page shows metadata and summary cards, while the drawer reuses existing form components for module editing.

**Tech Stack:** React, TypeScript, existing admin-console CSS, Vitest

---

### Task 1: Lock the new interaction with tests

**Files:**
- Modify: `admin-console/src/pages/EventListPage.test.tsx`

**Step 1: Write the failing test**

Add assertions that:
- the left column no longer renders the event chip cloud
- the right side shows module edit entry points
- clicking a module opens a right-side dialog

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/pages/EventListPage.test.tsx`
Expected: FAIL because the page still renders event chips and inline forms.

**Step 3: Write minimal implementation**

Adjust tests only after confirming they fail for the intended reason.

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 2: Refactor the event page into summary mode

**Files:**
- Modify: `admin-console/src/pages/EventListPage.tsx`

**Step 1: Write the failing test**

Use the new test expectations from Task 1.

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/pages/EventListPage.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

Refactor the page so that:
- the left column only keeps selectors and save
- the right column shows summary chips and summary cards
- inline form rendering is removed from the main panel
- clicking a summary card opens a drawer

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 3: Add drawer layout and styling

**Files:**
- Modify: `admin-console/src/styles/admin-theme.css`

**Step 1: Write the failing test**

Rely on the dialog test from Task 1 to ensure the drawer container exists.

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/pages/EventListPage.test.tsx`
Expected: FAIL if the drawer is not rendered.

**Step 3: Write minimal implementation**

Add styles for:
- summary cards
- summary rows
- right-side drawer shell
- drawer header/body actions

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 4: Run full verification and build

**Files:**
- Modify if needed: `admin-console/src/App.test.tsx`

**Step 1: Run full tests**

Run: `npm test -- --run`
Expected: PASS

**Step 2: Build the served frontend bundle**

Run: `npm run build`
Expected: build succeeds and updates `admin-console/dist`
