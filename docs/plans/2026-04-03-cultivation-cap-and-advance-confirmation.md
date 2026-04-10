# 修为上限与推进确认 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把突破修为门槛改成累计计算，并在修为已满但未突破时拦截时间推进、提供继续推进确认。

**Architecture:** 后端把境界配置中的 `required_cultivation_exp` 解释为“该层新增门槛”，运行时按当前目标境界累计求和，并在所有主循环写回前统一截断修为。小程序前端在推进时间前根据运行态计算是否已满修为，弹出带“不再提示”勾选的确认框；勾选状态只在当前 run 生命周期内生效。

**Tech Stack:** Python / FastAPI / pytest / WeChat Mini Program / Vitest

---

### Task 1: 累计突破门槛后端测试

**Files:**
- Modify: `tests/backend/test_run_lifecycle.py`
- Modify: `tests/backend/test_event_breakthrough_rebirth.py`
- Modify: `tests/backend/test_resource_sale_service.py`
- Modify: `tests/backend/test_core_loop_api.py`

**Step 1: Write the failing test**
- 让 `breakthrough_requirements.required_cultivation_exp` 断言为累计值。
- 新增“推进或事件收益不会把修为加到累计门槛之上”的断言。
- 新增“灵石转修为只转到上限，不额外浪费灵石”的断言。

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_event_breakthrough_rebirth.py tests/backend/test_resource_sale_service.py tests/backend/test_core_loop_api.py -q`
Expected: FAIL，显示仍按单层门槛计算，且修为未被截断。

**Step 3: Write minimal implementation**
- 在 `app/core_loop/services/run_service.py` 增加累计门槛计算 helper。
- 在运行态 hydrate 时输出累计修为门槛。
- 在状态写回链路里统一截断修为。
- 在 `app/economy/services/resource_conversion_service.py` 按剩余可增长空间消耗灵石。

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_event_breakthrough_rebirth.py tests/backend/test_resource_sale_service.py tests/backend/test_core_loop_api.py -q`
Expected: PASS

### Task 2: 满修为推进确认前端测试

**Files:**
- Modify: `wechat-miniprogram-game-front/tests/frontend/core_loop_pages.test.mjs`
- Modify: `wechat-miniprogram-game-front/utils/run-store.js`
- Modify: `wechat-miniprogram-game-front/pages/event/event.js`

**Step 1: Write the failing test**
- 断言 `event.js` 包含“修为已满”确认弹窗文案、继续/放弃按钮和“不再提示”状态。
- 断言 `run-store.js` 持有当前 run 生命周期内的静默标记并在开新局/转生时重置。

**Step 2: Run test to verify it fails**

Run: `npm test -- --run tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL，前端尚无该提示状态和文案。

**Step 3: Write minimal implementation**
- `run-store.js` 新增本次行程的满修为静默标记。
- `event.js` 在 `advanceTime` 前判断是否已满修为且可突破，弹出确认框。
- 勾选并继续推进时，本次 run 后续推进不再重复提示。

**Step 4: Run test to verify it passes**

Run: `npm test -- --run tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

### Task 3: 全量验证与文档更新

**Files:**
- Modify: `docs/2026-04-02-completed-features.md`

**Step 1: Run backend tests**

Run: `python -m pytest tests/backend -q`
Expected: PASS

**Step 2: Run frontend tests**

Run: `npm test -- --run`
Expected: PASS

**Step 3: Build frontend**

Run: `npm run build`
Expected: build success

**Step 4: Update docs**
- 补充累计突破门槛和满修为推进确认说明。
