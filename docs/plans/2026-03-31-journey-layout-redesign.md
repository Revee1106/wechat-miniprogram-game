# Journey Layout Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构无待处理事件时的行程页布局，让底部成为独立标签导航，中部成为单一展示区，并移除命牌中的重复寿元信息。

**Architecture:** 保留待处理事件模式不动，只重构普通行程模式。`inspection-sheet` 被收缩成纯导航组件，具体标签内容回收到 `pages/event` 的主展示区中按 `activeSection` 渲染，底部固定 tab 样式由 event 页面整体布局控制。

**Tech Stack:** 微信小程序原生页面（WXML / WXSS / JS）、现有运行态 store、Node 源码断言测试。

---

### Task 1: 更新前端断言到新布局

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\tests\frontend\core_loop_pages.test.mjs`

**Step 1: Write the failing test**

- 为 event 页新增断言：
  - `journey-overview`
  - `journey-main-stage`
  - `journey-dock`
- 去掉对 `inspection-sheet` 中正文内容的旧断言。
- 断言 `inspection-sheet` 仍有四个 tab，但不再包含 `info-grid`、`info-card`、`player.lifespan_current`。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 只更新断言，不改生产代码。

**Step 4: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL，且失败原因与新布局结构缺失一致。

### Task 2: 收缩 inspection-sheet 为纯导航组件

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\components\inspection-sheet\index.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\components\inspection-sheet\index.wxss`

**Step 1: Write the failing test**

- 依赖 Task 1 的失败断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 只保留 tab 导航结构。
- 去掉 `inspection-body` 和内部信息卡。

**Step 4: Run test to verify it passes**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: PASS 或只剩 event 页主内容断言失败。

### Task 3: 重构 event 页无事件状态布局

**Files:**
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.wxml`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.wxss`
- Modify: `E:\game\wechat-miniprogram-game-front\pages\event\event.js`

**Step 1: Write the failing test**

- 依赖 Task 1 的失败断言。

**Step 2: Run test to verify it fails**

Run: `node tests/frontend/core_loop_pages.test.mjs`
Expected: FAIL

**Step 3: Write minimal implementation**

- 新增顶部概览条、中部主展示区、底部 dock。
- 将 `命牌 / 行囊 / 修炼 / 洞府` 的正文内容内联到 event 页主展示区。
- 命牌内容中不再渲染寿元。

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

Run: `git diff -- pages/event/event.js pages/event/event.wxml pages/event/event.wxss components/inspection-sheet/index.wxml components/inspection-sheet/index.wxss tests/frontend/core_loop_pages.test.mjs`
Expected: 仅包含本次布局重构和导航职责拆分相关改动。
