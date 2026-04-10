# Realm Advance Base Values Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 给境界配置增加“每次推进基础修为增加”和“每次推进灵石消耗”字段，并让推进时间逻辑按当前境界配置执行固定修为增长和灵石扣费。

**Architecture:** 后端将两个新字段直接纳入 `RealmConfig`，配置读取、校验、后台保存、API 序列化统一透传；`TimeAdvanceService` 在月推进主流程前先执行当前境界的基础扣费与修为增长。管理台在“基础信息”抽屉中新增两个数值输入框，继续使用现有 `RealmInput` 保存。

**Tech Stack:** Python / FastAPI / pytest / React / Vitest

---

### Task 1: 写后端失败测试

**Files:**
- Modify: `tests/backend/test_run_lifecycle.py`
- Modify: `tests/backend/test_core_loop_api.py`
- Modify: `tests/backend/test_admin_realm_service.py`
- Modify: `tests/backend/test_admin_realm_api.py`

**Step 1: Write the failing test**

- 新增“推进时间按当前境界配置增加修为并扣灵石”的断言
- 新增“灵石不足时推进失败且状态不变”的断言
- 新增 API 返回新字段的断言
- 新增后台保存与读取新字段的断言

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_core_loop_api.py tests/backend/test_admin_realm_service.py tests/backend/test_admin_realm_api.py -q`
Expected: FAIL，提示新字段不存在或推进逻辑未按配置扣费增益。

**Step 3: Write minimal implementation**

- 暂不执行，本任务只写失败测试

**Step 4: Run test to verify it fails for the expected reason**

Run: `python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_core_loop_api.py tests/backend/test_admin_realm_service.py tests/backend/test_admin_realm_api.py -q`
Expected: FAIL，失败集中在新字段与推进规则缺失。

### Task 2: 扩展后端境界配置模型

**Files:**
- Modify: `app/core_loop/types.py`
- Modify: `app/core_loop/realm_config.py`
- Modify: `app/admin/services/realm_validation_service.py`
- Modify: `app/admin/services/realm_admin_service.py`
- Modify: `app/api/schemas.py`
- Modify: `config/realms/realms.json`

**Step 1: Write minimal implementation**

- 给 `RealmConfig` 增加两个整数字段
- 配置加载时读取并默认归一化为 `0`
- 后台校验两个字段为非负整数
- API schema 与后台服务读写透传
- 默认配置文件补全两个字段

**Step 2: Run targeted tests**

Run: `python -m pytest tests/backend/test_admin_realm_service.py tests/backend/test_admin_realm_api.py tests/backend/test_realm_config_validation.py tests/backend/test_realm_runtime_config.py -q`
Expected: PASS

### Task 3: 实现推进时间基础结算

**Files:**
- Modify: `app/core_loop/services/time_advance_service.py`
- Modify: `app/core_loop/services/run_service.py`
- Modify: `tests/backend/test_run_lifecycle.py`
- Modify: `tests/backend/test_core_loop_api.py`

**Step 1: Write minimal implementation**

- `TimeAdvanceService.advance()` 读取当前境界配置
- 推进前校验灵石是否足够，不足则抛 `ConflictError`
- 足够时先扣灵石、加修为，再继续原有推进链路
- 推进后的修为仍走现有上限截断

**Step 2: Run targeted tests**

Run: `python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_core_loop_api.py -q`
Expected: PASS

### Task 4: 写管理台失败测试

**Files:**
- Modify: `admin-console/src/pages/RealmEditorPage.test.tsx`

**Step 1: Write the failing test**

- 断言基础信息抽屉显示两个新输入框
- 断言保存时提交两个新字段

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/pages/RealmEditorPage.test.tsx`
Expected: FAIL，提示字段不存在或保存未提交。

### Task 5: 实现管理台基础信息表单

**Files:**
- Modify: `admin-console/src/api/client.ts`
- Modify: `admin-console/src/components/RealmForm.tsx`
- Modify: `admin-console/src/pages/RealmEditorPage.tsx`
- Modify: `admin-console/src/pages/RealmEditorPage.test.tsx`

**Step 1: Write minimal implementation**

- `RealmInput` 增加两个新字段
- 基础信息抽屉新增两个数字输入框
- 新建默认值、详情回显、保存归一化一起更新

**Step 2: Run targeted tests**

Run: `npm test -- --run src/pages/RealmEditorPage.test.tsx`
Expected: PASS

### Task 6: 全量验证

**Files:**
- No code changes expected

**Step 1: Run backend tests**

Run: `python -m pytest tests/backend -q`
Expected: PASS

**Step 2: Run admin console tests**

Run: `npm test -- --run`
Expected: PASS

**Step 3: Build admin console**

Run: `npm run build`
Expected: build success
