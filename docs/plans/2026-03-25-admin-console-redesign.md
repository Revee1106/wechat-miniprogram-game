# Admin Console Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the admin console into a Chinese-labeled, card-based game planning workbench without changing backend APIs.

**Architecture:** Keep the existing React/Vite admin app and backend contracts, but reorganize the frontend into a themed shell, a card-based event library, and a sectional event workbench. Centralize field-label mapping and shared UI primitives so the redesigned console remains maintainable as more config domains are added.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, FastAPI, pytest

---

### Task 1: Add failing UI tests for the redesigned shell and Chinese labels

**Files:**
- Modify: `admin-console/src/App.test.tsx`
- Modify: `admin-console/src/pages/EventListPage.test.tsx`
- Modify: `admin-console/src/pages/EventEditorPage.test.tsx`

**Step 1: Write the failing test**

Add tests that expect:
- `问道控制台` in the shell
- `事件库` in the list page
- Chinese editor labels like `事件名称` and `成功结果`

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/App.test.tsx src/pages/EventListPage.test.tsx src/pages/EventEditorPage.test.tsx`
Expected: FAIL because the current UI still uses the old shell and English-first labels.

**Step 3: Write minimal implementation**

Update tests only. Do not change production code in this task.

**Step 4: Run test to verify it passes later**

Run the same command after implementation tasks.
Expected: PASS

### Task 2: Build a themed admin shell and redesign the login page

**Files:**
- Modify: `admin-console/src/App.tsx`
- Modify: `admin-console/src/pages/LoginPage.tsx`
- Create: `admin-console/src/styles/admin-theme.css`

**Step 1: Write the failing test**

Use the tests from Task 1 to drive the new shell.

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/App.test.tsx`
Expected: FAIL because the current shell does not render the new Chinese layout.

**Step 3: Write minimal implementation**

Implement:
- fixed shell header
- branded title
- signed-in summary
- Chinese buttons and loading states
- redesigned login page using the shared theme

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/App.test.tsx`
Expected: PASS

### Task 3: Replace the event table with a card-based event library

**Files:**
- Modify: `admin-console/src/pages/EventListPage.tsx`
- Modify: `admin-console/src/components/EventFilters.tsx`
- Modify: `admin-console/src/components/EventTable.tsx`
- Create: `admin-console/src/components/EventLibraryCard.tsx`
- Create: `admin-console/src/components/FieldLabelMap.ts`

**Step 1: Write the failing test**

Use the list-page tests to assert:
- `事件库` heading
- Chinese filter labels
- card summaries for type/risk/repeatability

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/pages/EventListPage.test.tsx`
Expected: FAIL because the page still renders the old list layout.

**Step 3: Write minimal implementation**

Implement:
- card-based list items
- Chinese filter UI
- summary chips and action buttons
- duplicated field-to-label mapping in one central file

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/pages/EventListPage.test.tsx`
Expected: PASS

### Task 4: Redesign the event workbench and section cards

**Files:**
- Modify: `admin-console/src/pages/EventEditorPage.tsx`
- Modify: `admin-console/src/components/EventTemplateForm.tsx`
- Modify: `admin-console/src/components/ValidationPanel.tsx`
- Create: `admin-console/src/components/SectionCard.tsx`
- Create: `admin-console/src/components/FormField.tsx`

**Step 1: Write the failing test**

Use the editor tests to assert:
- Chinese section titles
- Chinese labels for core fields
- status card text after save

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/pages/EventEditorPage.test.tsx`
Expected: FAIL because the editor still exposes the old structure.

**Step 3: Write minimal implementation**

Implement:
- event summary header
- card-based grouped sections
- Chinese labels and helper text
- unified action bar and status area

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/pages/EventEditorPage.test.tsx`
Expected: PASS

### Task 5: Turn option editing into collapsible planning cards

**Files:**
- Modify: `admin-console/src/components/EventOptionEditor.tsx`
- Modify: `admin-console/src/components/ResultPayloadEditor.tsx`

**Step 1: Write the failing test**

Extend the editor tests to assert:
- option cards show Chinese summary headers
- payload editor labels use Chinese names
- expanded option content can still be edited and saved

**Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/pages/EventEditorPage.test.tsx`
Expected: FAIL because options are still flat fieldsets with English labels.

**Step 3: Write minimal implementation**

Implement:
- collapsible option cards
- Chinese payload labels
- summary metadata shown before expanding

**Step 4: Run test to verify it passes**

Run: `npm.cmd test -- src/pages/EventEditorPage.test.tsx`
Expected: PASS

### Task 6: Run full verification

**Files:**
- Modify: `admin-console/src/test/setup.ts`
- Modify: `admin-console/src/utils/eventFormCodec.test.ts`

**Step 1: Run frontend verification**

Run: `npm.cmd test`
Expected: PASS

**Step 2: Run build verification**

Run: `npm.cmd run build`
Expected: PASS

**Step 3: Run backend regression**

Run: `python.exe -m pytest tests/backend -q`
Expected: PASS

