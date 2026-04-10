# 战斗系统 V1 进度说明

**日期：** 2026-04-10

本次按《战斗系统 V1》实现计划推进，当前已完成后端运行态、事件战斗接入、战斗动作 API、以及管理台 battle 配置编辑链路。小程序前端战斗弹层与端到端演示事件仍未接入当前仓库。

## 本次已完成

### 1. 战斗运行态与序列化

- `RunState` 新增 `active_battle`
- 新增玩家 / 敌人战斗快照结构
- API schema 已支持返回战斗运行态
- 补充了战斗状态序列化测试

### 2. battle 配置读写与校验

- 事件 option 已支持 `resolution_mode = "combat"`
- 管理台 codec 与 API 类型已支持 battle 配置
- 后端事件配置校验已覆盖 battle 必填字段
- event registry 对空 `region` 做了归一化，避免运行态事件出现空 region

### 3. 玩家战斗属性映射

- 新增 `CombatStatService`
- 已按当前境界、阶段和修为进度映射玩家的
  - `hp_current`
  - `hp_max`
  - `attack`
  - `defense`
  - `speed`

### 4. 战斗回合结算服务

- 新增 `CombatService`
- 已支持
  - 攻击
  - 防御
  - 使用丹药
  - 逃跑
- 已覆盖速度先后手、逃跑成功率上下限、受防御减伤等规则

### 5. 事件链路接入战斗

- `combat` 事件 option 不再直接结算结果
- 选择战斗 option 后会进入 `active_battle`
- 战斗胜利 / 失败 / 逃跑成功后会统一回写事件结果
- 战斗结束后会同步剩余血量回角色状态

### 6. 战斗动作 API

- 新增战斗动作请求 schema
- 新增战斗动作接口
- `RunService` 已暴露 `perform_battle_action`
- 已覆盖无战斗中提交动作、非法动作等冲突场景

### 7. 管理台战斗配置编辑

- 管理台事件 option 编辑器已支持 `combat` 模式
- `combat` 模式下可编辑 battle 配置
- `direct` 模式下 battle 配置不会显示
- battle 配置变更可正确写回 payload

### 8. 本次顺带修复的回归问题

- 修复自定义小境界链下 `realm_max = qi_refining_peak` 等边界解析错误，避免默认事件被整体过滤
- 修复随机命中空 `region` 模板时，运行态事件结构不满足测试约束的问题

## 当前未完成

### 1. 小程序前端战斗 view model

- 尚未实现 battle modal view model
- 尚未在 run-store 中接入 `performBattleAction`
- 尚未补前端 battle flow 测试

### 2. 小程序战斗弹层 UI

- 尚未实现战斗弹层渲染
- 尚未接入主舞台优先显示 `active_battle`
- 尚未打通按钮交互到 adapter

### 3. 端到端示例战斗事件

- 当前仓库尚未补正式 combat 示例事件配置
- 尚未补小程序端到端战斗演示用例
- 尚未补管理台 `App` 级别的战斗链路回归

## 本次验证

已执行：

```bash
python -m pytest tests/backend/test_event_config_registry.py tests/backend/test_realm_runtime_config.py tests/backend/test_combat_state_serialization.py tests/backend/test_combat_stat_service.py tests/backend/test_combat_service.py tests/backend/test_event_config_validation.py tests/backend/test_event_resolution_payload.py tests/backend/test_run_lifecycle.py tests/backend/test_core_loop_api.py -q
npm test -- src/utils/eventFormCodec.test.ts src/components/EventOptionEditor.test.tsx src/pages/EventEditorPage.test.tsx
```

结果：

- 后端：`69 passed`
- admin-console：`18 passed`
