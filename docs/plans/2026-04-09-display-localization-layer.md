# Display Localization Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a structured localization layer so internal English identifiers and error codes never leak directly into player-facing or operator-facing UI.

**Architecture:** Introduce structured core-loop error codes in the backend API, then localize those errors in the player frontend and admin console through centralized mapping utilities. Keep existing `display_name` fields as the first-choice source for Chinese display text, and add fallback key-to-label formatters for resources, facilities, realms, and statuses.

**Tech Stack:** Python FastAPI backend, TypeScript React admin console, JavaScript WeChat miniprogram frontend, Node.js and pytest tests.

---

### Task 1: Add structured core-loop error metadata

**Files:**
- Modify: `wechat-miniprogram-game/app/core_loop/types.py`
- Modify: `wechat-miniprogram-game/app/api/core_loop.py`
- Modify: `wechat-miniprogram-game/app/core_loop/services/time_advance_service.py`
- Modify: `wechat-miniprogram-game/app/core_loop/services/progression_service.py`
- Modify: `wechat-miniprogram-game/app/core_loop/services/dwelling_service.py`
- Modify: `wechat-miniprogram-game/app/economy/services/resource_sale_service.py`
- Modify: `wechat-miniprogram-game/app/economy/services/resource_conversion_service.py`
- Modify: `wechat-miniprogram-game/app/core_loop/services/event_resolution_service.py`
- Modify: `wechat-miniprogram-game/app/core_loop/services/alchemy_service.py`
- Test: `wechat-miniprogram-game/tests/backend/test_core_loop_api.py`

**Step 1: Write the failing test**

Add a backend API test asserting conflict responses return structured `detail` with:
- `code`
- `message`
- `params`

Use the “not enough spirit stones to advance time” path as the first case.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_core_loop_api.py -q -k advance`
Expected: FAIL because `detail` is still a raw English string.

**Step 3: Write minimal implementation**

Introduce structured error fields on core-loop errors and make API serialization return an object in `detail`. Update the most common player-facing service errors to use stable codes.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_core_loop_api.py -q -k advance`
Expected: PASS

### Task 2: Localize player frontend API errors

**Files:**
- Create: `wechat-miniprogram-game-front/utils/display-text.js`
- Modify: `wechat-miniprogram-game-front/utils/api.js`
- Test: `wechat-miniprogram-game-front/tests/frontend/user_facing_errors.test.mjs`

**Step 1: Write the failing test**

Add assertions that:
- the frontend API layer recognizes structured `detail.code`
- the English advance-time error is mapped to Chinese
- legacy English strings still map to Chinese fallbacks

**Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/user_facing_errors.test.mjs`
Expected: FAIL because no structured localization helper exists yet.

**Step 3: Write minimal implementation**

Create a single player-frontend display text helper that:
- maps core-loop error codes to Chinese
- localizes legacy English strings for backward compatibility
- formats API failures into `Error` objects with Chinese `message`

**Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/user_facing_errors.test.mjs`
Expected: PASS

### Task 3: Replace direct key fallbacks in player-facing view models and pages

**Files:**
- Modify: `wechat-miniprogram-game-front/src/game/view-models/main-stage.js`
- Modify: `wechat-miniprogram-game-front/src/game/view-models/summary-modal.js`
- Modify: `wechat-miniprogram-game-front/src/game/view-models/cultivation-drawer.js`
- Modify: `wechat-miniprogram-game-front/src/game/view-models/dwelling-drawer.js`
- Modify: `wechat-miniprogram-game-front/src/game/view-models/alchemy-drawer.js`
- Modify: `wechat-miniprogram-game-front/pages/event/event.js`
- Modify: `wechat-miniprogram-game-front/pages/dwelling/dwelling.js`
- Modify: `wechat-miniprogram-game-front/pages/crafting/crafting.js`
- Test: `wechat-miniprogram-game-front/tests/frontend/minigame_drawers_view_model.test.mjs`
- Test: `wechat-miniprogram-game-front/tests/frontend/core_loop_pages.test.mjs`

**Step 1: Write the failing test**

Add assertions that player-facing UI no longer falls back to raw internal keys such as:
- `realm.key`
- `facility_id`
- `resource_key`

**Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/minigame_drawers_view_model.test.mjs tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL because raw key fallbacks still exist.

**Step 3: Write minimal implementation**

Use the shared player display text helper to localize fallback labels across minigame view models and old pages.

**Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/minigame_drawers_view_model.test.mjs tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

### Task 4: Localize admin console errors and fallback labels

**Files:**
- Create: `wechat-miniprogram-game/admin-console/src/utils/displayText.ts`
- Modify: `wechat-miniprogram-game/admin-console/src/api/client.ts`
- Modify: `wechat-miniprogram-game/admin-console/src/components/RealmForm.tsx`
- Modify: `wechat-miniprogram-game/admin-console/src/pages/EventListPage.tsx`
- Modify: `wechat-miniprogram-game/admin-console/src/pages/RealmListPage.tsx`
- Test: `wechat-miniprogram-game/admin-console/src/App.test.tsx`
- Test: `wechat-miniprogram-game/admin-console/src/pages/RealmListPage.test.tsx`

**Step 1: Write the failing test**

Add tests for:
- structured API errors being shown as Chinese
- fallback realm/facility labels using localized text instead of raw keys when display names are absent

**Step 2: Run test to verify it fails**

Run: `npm test -- src/App.test.tsx src/pages/RealmListPage.test.tsx`
Expected: FAIL because admin console still uses English fallback messages and raw keys.

**Step 3: Write minimal implementation**

Add an admin-console display text utility and route API errors plus fallback labels through it.

**Step 4: Run test to verify it passes**

Run: `npm test -- src/App.test.tsx src/pages/RealmListPage.test.tsx`
Expected: PASS

### Task 5: Run integrated verification

**Files:**
- Verify only

**Step 1: Run backend verification**

Run: `python -m pytest tests/backend/test_core_loop_api.py tests/backend/test_run_lifecycle.py -q`
Expected: PASS

**Step 2: Run player frontend verification**

Run: `node --test tests/frontend/user_facing_errors.test.mjs tests/frontend/minigame_drawers_view_model.test.mjs tests/frontend/minigame_screen_modules.test.mjs tests/frontend/minigame_screen_interactions.test.mjs tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

**Step 3: Run admin console verification**

Run: `npm test -- src/App.test.tsx src/pages/RealmListPage.test.tsx`
Expected: PASS
