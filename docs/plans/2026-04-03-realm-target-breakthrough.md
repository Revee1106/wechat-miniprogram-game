# Realm Target Breakthrough Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把境界突破配置改成按目标境界生效，并新增突破失败扣减修为的配置与控制台编辑能力。

**Architecture:** 后端以 `RealmConfig` 承载目标境界突破参数与失败惩罚，`RunService` 和 `ProgressionService` 改为读取下一境界配置；控制台境界页保持现有抽屉式交互，只在“突破配置”模块中对第一条境界显示只读提示，对其他境界开放成功率、成本和失败惩罚编辑。

**Tech Stack:** Python dataclasses, FastAPI admin API, React + Vitest admin console

---

### Task 1: 写入失败测试

**Files:**
- Modify: `tests/backend/test_run_lifecycle.py`
- Modify: `tests/backend/test_breakthrough_economy_requirements.py`
- Modify: `tests/backend/test_realm_config_validation.py`
- Modify: `admin-console/src/pages/RealmEditorPage.test.tsx`

**Step 1: Write the failing tests**

- 运行时突破需求读取下一境界配置
- 失败惩罚会扣减修为
- 第一条境界打开突破配置只显示提示
- 后续境界保存时会提交 `failure_penalty`

**Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_breakthrough_economy_requirements.py tests/backend/test_realm_config_validation.py -q
npm test -- --run src/pages/RealmEditorPage.test.tsx
```

**Step 3: Commit**

```bash
git add tests/backend/test_run_lifecycle.py tests/backend/test_breakthrough_economy_requirements.py tests/backend/test_realm_config_validation.py admin-console/src/pages/RealmEditorPage.test.tsx
git commit -m "test: cover target breakthrough realm config"
```

### Task 2: 改造后端境界配置模型

**Files:**
- Modify: `app/core_loop/types.py`
- Modify: `app/core_loop/realm_config.py`
- Modify: `app/admin/services/realm_validation_service.py`
- Modify: `app/admin/services/realm_admin_service.py`
- Modify: `app/api/schemas.py`

**Step 1: Add failure_penalty support**

- 给 `RealmConfig` 增加失败惩罚字段
- 读取 JSON 时解析 `failure_penalty`
- 校验只允许 `character.cultivation_exp` 为整数且不为正数
- API 序列化保持直通

**Step 2: Run targeted tests**

```bash
python -m pytest tests/backend/test_realm_config_validation.py tests/backend/test_admin_realm_service.py tests/backend/test_admin_realm_api.py -q
```

### Task 3: 改造突破运行时

**Files:**
- Modify: `app/core_loop/services/progression_service.py`
- Modify: `app/core_loop/services/run_service.py`
- Modify: `tests/backend/test_run_lifecycle.py`
- Modify: `tests/backend/test_breakthrough_economy_requirements.py`
- Modify: `tests/backend/test_event_breakthrough_rebirth.py`

**Step 1: Implement target-realm breakthrough semantics**

- `breakthrough_requirements` 读取下一境界配置
- `try_breakthrough()` 使用下一境界的成功率和资源需求
- 失败时应用修为惩罚，成功时进入下一境界

**Step 2: Run targeted tests**

```bash
python -m pytest tests/backend/test_run_lifecycle.py tests/backend/test_breakthrough_economy_requirements.py tests/backend/test_event_breakthrough_rebirth.py -q
```

### Task 4: 迁移默认境界配置

**Files:**
- Modify: `config/realms/realms.json`
- Modify: `tests/backend/test_realm_runtime_config.py`

**Step 1: Shift default breakthrough config forward**

- 第一条境界清空突破参数
- 后续每条境界继承原上一条境界的突破需求

**Step 2: Run targeted tests**

```bash
python -m pytest tests/backend/test_realm_runtime_config.py -q
```

### Task 5: 改造控制台境界编辑器

**Files:**
- Modify: `admin-console/src/api/client.ts`
- Modify: `admin-console/src/components/RealmForm.tsx`
- Modify: `admin-console/src/pages/RealmListPage.tsx`
- Modify: `admin-console/src/pages/RealmEditorPage.tsx`
- Modify: `admin-console/src/pages/RealmEditorPage.test.tsx`
- Modify: `admin-console/src/pages/RealmListPage.test.tsx`

**Step 1: Add target-realm breakthrough UI**

- 第一条境界显示只读提示
- 其他境界显示成功率、修为、灵石、失败惩罚
- 失败惩罚用下拉框 + 数值输入

**Step 2: Run targeted tests**

```bash
npm test -- --run src/pages/RealmEditorPage.test.tsx src/pages/RealmListPage.test.tsx
```

### Task 6: 全量验证

**Files:**
- No code changes expected

**Step 1: Run backend tests**

```bash
python -m pytest tests/backend -q
```

**Step 2: Run frontend tests**

```bash
npm test -- --run
```

**Step 3: Build admin console**

```bash
npm run build
```
