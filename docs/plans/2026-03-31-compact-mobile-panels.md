# Compact Mobile Panels Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把洞府页和炼丹页重构成更适合手机单屏操作的摘要加横向切换布局，减少纵向滚动。

**Architecture:** 两个页面统一采用固定视口容器、顶部摘要、页签切换和 `swiper` 面板联动。设施、丹方、库存等多项内容通过横向卡片带展示，避免整页纵向堆叠。保留现有业务逻辑和 API，只调整展示结构与本地交互状态。

**Tech Stack:** 微信小程序原生页面（WXML / WXSS / JS）、现有 `run-store`、Node 源码断言测试。

---

### Task 1: 更新前端断言到页签加滑动布局

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\tests\frontend\core_loop_pages.test.mjs`

**Step 1: Write the failing test**

- 为洞府页新增断言：
  - `swiper`
  - `bindchange="handlePanelSwipe"`
  - `bindtap="switchPanel"`
  - `scroll-x="{{true}}"`
  - `activePanel`
  - `currentPanelIndex`
- 为炼丹页新增同类断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL，提示页面尚未实现新页签结构。

**Step 3: Write minimal implementation**

- 只改断言，不改生产代码。

**Step 4: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL，且失败原因与新布局缺失一致。

### Task 2: 重构洞府页为单屏面板布局

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\pages\dwelling\dwelling.js`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\dwelling\dwelling.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\dwelling\dwelling.wxss`

**Step 1: Write the failing test**

- 依赖 Task 1 的失败断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 新增 `activePanel`、`currentPanelIndex`、`switchPanel`、`handlePanelSwipe`。
- 把洞府页改成顶部摘要、页签、`swiper` 面板。
- 设施区改成横向卡片带，卡片内保留建造和升级按钮。

**Step 4: Run test to verify it passes**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS 或仅剩炼丹页相关失败。

### Task 3: 重构炼丹页为单屏面板布局

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\pages\crafting\crafting.js`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\crafting\crafting.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\crafting\crafting.wxss`

**Step 1: Write the failing test**

- 依赖 Task 1 的失败断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 新增 `activePanel`、`currentPanelIndex`、`switchPanel`、`handlePanelSwipe`。
- 让丹方、炉次、库存分别落在不同面板中。
- 丹方和库存改成横向卡片带。

**Step 4: Run test to verify it passes**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

### Task 4: 验证与回归检查

**Files:**
- Test: `E:\game\wechat-miniprogram-game-front\tests\frontend\core_loop_pages.test.mjs`
- Test: `E:\game\wechat-miniprogram-game-front\tests\frontend\app_manifest.test.mjs`

**Step 1: Run source assertions**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS

**Step 2: Run manifest assertions**

Run: `node tests/frontend/app_manifest.test.mjs`
Expected: PASS

**Step 3: Review diff**

Run: `git diff -- pages/dwelling/dwelling.js pages/dwelling/dwelling.wxml pages/dwelling/dwelling.wxss pages/crafting/crafting.js pages/crafting/crafting.wxml pages/crafting/crafting.wxss tests/frontend/core_loop_pages.test.mjs`
Expected: 仅包含本次布局与交互相关改动。
