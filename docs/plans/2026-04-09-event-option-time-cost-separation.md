# Event Option Time Cost Separation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make option-level `time_cost_months` a standalone `事件耗时（月）` section in the admin console while keeping result payload `寿元变化` unchanged.

**Architecture:** Keep backend contracts unchanged and refactor only the admin-console component structure. Treat execution cost and result lifespan change as separate UI concepts backed by separate existing fields.

**Tech Stack:** React 18, TypeScript, Vitest, Testing Library, Vite

---

### Task 1: Lock the new UI semantics with tests

**Files:**
- Modify: `E:/game/wechat-miniprogram-game/admin-console/src/components/EventOptionEditor.test.tsx`
- Modify: `E:/game/wechat-miniprogram-game/admin-console/src/pages/EventEditorPage.test.tsx`

**Step 1: Write the failing test**

Add assertions that:

- `事件耗时（月）` appears as its own section/input
- `判定与后续` no longer uses `耗时（月）`
- `结果` editing still exposes `寿元变化`
- single-outcome mode also renders `事件耗时（月）`

**Step 2: Run test to verify it fails**

Run: `npm test -- src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Expected: FAIL because the current UI still renders `耗时（月）` inside the resolution section.

**Step 3: Write minimal implementation**

Update the option editor components so the tests target the new structure without changing the underlying value shape.

**Step 4: Run test to verify it passes**

Run: `npm test -- src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/components/EventOptionEditor.test.tsx admin-console/src/pages/EventEditorPage.test.tsx admin-console/src/components/EventOptionEditor.tsx admin-console/src/components/SingleOutcomeEditor.tsx
git commit -m "feat: separate event time cost from result payload editing"
```

### Task 2: Refactor the option editor layout

**Files:**
- Modify: `E:/game/wechat-miniprogram-game/admin-console/src/components/EventOptionEditor.tsx`
- Modify: `E:/game/wechat-miniprogram-game/admin-console/src/components/SingleOutcomeEditor.tsx`

**Step 1: Write the failing test**

Reuse the tests from Task 1 as the active failing spec.

**Step 2: Run test to verify it fails**

Run: `npm test -- src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Expected: FAIL before the component refactor is complete.

**Step 3: Write minimal implementation**

Implement:

- a new `SectionCard` titled `事件耗时（月）`
- a numeric input labeled `事件耗时（月）`
- helper copy clarifying it is separate from result payload lifespan changes
- removal of the old `耗时（月）` input from `判定与后续`

**Step 4: Run test to verify it passes**

Run: `npm test -- src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add admin-console/src/components/EventOptionEditor.tsx admin-console/src/components/SingleOutcomeEditor.tsx admin-console/src/components/EventOptionEditor.test.tsx admin-console/src/pages/EventEditorPage.test.tsx
git commit -m "feat: add standalone event time cost section"
```

### Task 3: Verify no targeted regressions remain

**Files:**
- Test: `E:/game/wechat-miniprogram-game/admin-console/src/components/EventOptionEditor.test.tsx`
- Test: `E:/game/wechat-miniprogram-game/admin-console/src/pages/EventEditorPage.test.tsx`

**Step 1: Run the targeted suite**

Run: `npm test -- src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx`

Expected: PASS

**Step 2: Run a broader related frontend check**

Run: `npm test -- src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx src/App.test.tsx`

Expected: PASS

**Step 3: Inspect diff**

Run: `git diff -- admin-console/src/components/EventOptionEditor.tsx admin-console/src/components/SingleOutcomeEditor.tsx admin-console/src/components/EventOptionEditor.test.tsx admin-console/src/pages/EventEditorPage.test.tsx`

Expected: only layout, label, and test changes related to standalone event time cost editing.

**Step 4: Commit**

```bash
git add admin-console/src/components/EventOptionEditor.tsx admin-console/src/components/SingleOutcomeEditor.tsx admin-console/src/components/EventOptionEditor.test.tsx admin-console/src/pages/EventEditorPage.test.tsx docs/plans/2026-04-09-event-option-time-cost-separation-design.md docs/plans/2026-04-09-event-option-time-cost-separation.md
git commit -m "feat: clarify option event time cost editing"
```
