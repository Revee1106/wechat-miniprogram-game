# Admin Console Compact Workbench Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a shared compact workbench UI for event, realm, and dwelling admin pages so users edit items from a dense registry list instead of navigating long scrolling pages.

**Architecture:** Keep the current admin APIs and persistence logic intact, but replace the current page flow with a shared two-column shell. Each page owns its data loading and save behavior, while the new reusable workbench components handle registry layout, detail tabs, and sticky actions.

**Tech Stack:** React, TypeScript, Vitest, existing admin-console CSS

---

### Task 1: Write the shared layout plan into reusable components

**Files:**
- Create: `admin-console/src/components/ConfigWorkbench.tsx`
- Modify: `admin-console/src/styles/admin-theme.css`
- Test: `admin-console/src/App.test.tsx`

**Step 1: Write the failing test**

Add assertions that the authenticated app shell still renders and can switch to the three config modules after the page layout changes.

**Step 2: Run test to verify it fails**

Run: `npm test -- App.test.tsx`
Expected: FAIL once the new shell structure is referenced but not yet implemented.

**Step 3: Write minimal implementation**

Create a reusable workbench shell with:
- left registry area
- right detail area
- sticky action bar slot

**Step 4: Run test to verify it passes**

Run: `npm test -- App.test.tsx`
Expected: PASS

### Task 2: Rebuild the event page around the compact workbench

**Files:**
- Modify: `admin-console/src/pages/EventListPage.tsx`
- Modify: `admin-console/src/pages/EventEditorPage.tsx`
- Modify: `admin-console/src/components/EventFilters.tsx`
- Modify: `admin-console/src/components/EventTable.tsx`
- Modify: `admin-console/src/components/EventOptionEditor.tsx`
- Modify: `admin-console/src/components/EventTemplateForm.tsx`
- Test: `admin-console/src/App.test.tsx`

**Step 1: Write the failing test**

Add assertions for dense event registry content and visible event editing modules after selecting an event.

**Step 2: Run test to verify it fails**

Run: `npm test -- App.test.tsx`
Expected: FAIL because the old event flow still renders separate large panels.

**Step 3: Write minimal implementation**

Refactor the event page to:
- show filters and compact registry together
- select or create an event without leaving the page
- split editor content into compact tabs
- use list-based option selection instead of fully expanded option stacks by default

**Step 4: Run test to verify it passes**

Run: `npm test -- App.test.tsx`
Expected: PASS

### Task 3: Rebuild the realm page around the compact workbench

**Files:**
- Modify: `admin-console/src/pages/RealmListPage.tsx`
- Modify: `admin-console/src/pages/RealmEditorPage.tsx`
- Modify: `admin-console/src/components/RealmForm.tsx`
- Test: `admin-console/src/App.test.tsx`

**Step 1: Write the failing test**

Add assertions for grouped realm registry and compact realm detail panels.

**Step 2: Run test to verify it fails**

Run: `npm test -- App.test.tsx`
Expected: FAIL because the current realm page still uses full-page cards and editor route transitions.

**Step 3: Write minimal implementation**

Refactor the realm page so:
- the left side shows grouped realm rows
- creation uses a major-realm dropdown
- the right side edits the selected realm in compact tabs

**Step 4: Run test to verify it passes**

Run: `npm test -- App.test.tsx`
Expected: PASS

### Task 4: Rebuild the dwelling page around the compact workbench

**Files:**
- Modify: `admin-console/src/pages/DwellingListPage.tsx`
- Modify: `admin-console/src/pages/DwellingEditorPage.tsx`
- Test: `admin-console/src/pages/DwellingEditorPage.test.tsx`
- Test: `admin-console/src/pages/DwellingListPage.test.tsx`

**Step 1: Write the failing test**

Add assertions for compact facility rows, level-tab switching, and dropdown-based level creation.

**Step 2: Run test to verify it fails**

Run: `npm test -- Dwelling`
Expected: FAIL because the current dwelling page still expands every level vertically.

**Step 3: Write minimal implementation**

Refactor the dwelling page so:
- the registry stays compact
- facility editing happens in-place
- levels are switched through tabs
- adding a level uses a dropdown for the next level

**Step 4: Run test to verify it passes**

Run: `npm test -- Dwelling`
Expected: PASS

### Task 5: Finish styling and verify build output

**Files:**
- Modify: `admin-console/src/styles/admin-theme.css`
- Modify: `admin-console/src/App.tsx`
- Test: `admin-console/src/App.test.tsx`

**Step 1: Write the failing test**

Add final assertions for the compact workbench labels and action visibility if needed.

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: Any remaining layout-related test failures.

**Step 3: Write minimal implementation**

Polish compact spacing, tab treatment, list density, and sticky actions while keeping the established visual language.

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS

**Step 5: Verify production bundle**

Run: `npm run build`
Expected: build succeeds and updates `admin-console/dist`
