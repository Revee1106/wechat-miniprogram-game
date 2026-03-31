# Dwelling Entry Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将事件页 `dwelling` 上半屏改成轻量入口区，并为独立洞府页、炼丹页补显式返回行程按钮。

**Architecture:** 保留事件页作为主流程容器，只在 `dwelling` 页签展示总览和入口卡，完整营建与炼丹交互继续分别留在独立页面。通过页面跳转解耦主流程页和重功能页，避免洞府模块继续侵占事件页上半屏。

**Tech Stack:** 微信小程序原生页面（WXML / WXSS / JS）、现有 `run-store` 状态管理、Node 源码断言测试。

---

### Task 1: 更新前端断言到新交互

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\tests\frontend\core_loop_pages.test.mjs`

**Step 1: Write the failing test**

- 断言事件页存在 `openDwellingPage`、`openCraftingPage`、`bindtap="openDwellingPage"`、`bindtap="openCraftingPage"`。
- 去掉事件页上半屏对 `bindtap="buildDwellingFacility"` 和 `bindtap="upgradeDwellingFacility"` 的断言。
- 断言洞府页和炼丹页存在 `bindtap="returnToJourney"` 与对应方法。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL，提示事件页缺少新入口或返回按钮。

**Step 3: Write minimal implementation**

- 仅修改断言，不改生产代码。

**Step 4: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL，且失败原因与新交互断言一致。

### Task 2: 实现事件页洞府入口化

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.js`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.wxss`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.json`

**Step 1: Write the failing test**

- 依赖 Task 1 的失败断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在事件页新增 `openDwellingPage` 和 `openCraftingPage`。
- `dwelling` 分支改成轻量总览和入口按钮，不再直接渲染完整设施列表。
- 如不再需要，移除事件页对 `dwelling-bonus-panel` 组件和直接建造逻辑的依赖。

**Step 4: Run test to verify it passes**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

### Task 3: 为洞府页增加返回行程按钮

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\pages\dwelling\dwelling.js`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\dwelling\dwelling.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\dwelling\dwelling.wxss`

**Step 1: Write the failing test**

- 依赖 Task 1 中的返回按钮断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 新增 `returnToJourney`。
- 页头增加 `返回行程` 按钮。
- 先走 `wx.navigateBack`，失败时回退到事件页。

**Step 4: Run test to verify it passes**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS 或只剩炼丹页相关失败。

### Task 4: 为炼丹页增加返回行程按钮

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\pages\crafting\crafting.js`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\crafting\crafting.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\crafting\crafting.wxss`

**Step 1: Write the failing test**

- 依赖 Task 1 中的返回按钮断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 新增 `returnToJourney`。
- 页头增加 `返回行程` 按钮。
- 返回逻辑与洞府页保持一致。

**Step 4: Run test to verify it passes**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

### Task 5: 全量前端验证

**Files:**
- Test: `E:\game\wechat-miniprogram-game-front\tests\frontend\core_loop_pages.test.mjs`
- Test: `E:\game\wechat-miniprogram-game-front\tests\frontend\app_manifest.test.mjs`

**Step 1: Run targeted verification**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

**Step 2: Run manifest verification**

Run: `node tests/frontend/app_manifest.test.mjs`
Expected: PASS

**Step 3: Review diff**

Run: `git diff -- pages/event/event.js pages/event/event.wxml pages/event/event.wxss pages/event/event.json pages/dwelling/dwelling.js pages/dwelling/dwelling.wxml pages/dwelling/dwelling.wxss pages/crafting/crafting.js pages/crafting/crafting.wxml pages/crafting/crafting.wxss tests/frontend/core_loop_pages.test.mjs`
Expected: 仅包含本次入口化与返回按钮相关修改。
