# Enemy Template Config Design
日期：2026-04-13

## 目标

在现有管理控制台中新增“战斗配置”模块，单独维护敌人模板；事件配置中的战斗选项不再内嵌敌人数值，而是直接选择一个敌人模板。运行时在进入战斗时解析敌人模板，并把模板中的奖励配置作为战斗胜利后的默认奖励来源。

## 范围

本次支持的敌人模板字段：

- `enemy_id`
- `enemy_name`
- `enemy_realm_label`
- `enemy_hp`
- `enemy_attack`
- `enemy_defense`
- `enemy_speed`
- `allow_flee`
- `rewards`

其中 `rewards` 复用当前事件结果载荷结构，首版至少支持：

- `resources`
- `character`
- `statuses_add`
- `statuses_remove`
- `techniques_add`
- `equipment_add`
- `equipment_remove`
- `death`
- `rebirth_progress_delta`

本次支持：

- 新增敌人模板配置仓储与校验
- 新增后台管理 API
- 新增控制台“战斗配置”列表页与编辑页
- 事件战斗选项改为选择敌人模板
- 战斗胜利奖励改为读取敌人模板 `rewards`
- 运行时支持新老配置并行读取

本次不支持：

- 事件层对敌人模板做局部覆盖
- 敌人行为 AI 参数扩展
- 掉落预览、标签、启用状态等策划扩展字段
- 批量迁移全部旧事件配置

## 配置模型

新增配置文件：`config/battle/enemies.json`

建议保存结构：

```json
{
  "items": [
    {
      "enemy_id": "enemy_bandit_qi_early",
      "enemy_name": "山匪",
      "enemy_realm_label": "炼气初期",
      "enemy_hp": 36,
      "enemy_attack": 8,
      "enemy_defense": 4,
      "enemy_speed": 6,
      "allow_flee": true,
      "rewards": {
        "resources": {
          "spirit_stone": 7
        },
        "character": {
          "cultivation_exp": 5
        }
      }
    }
  ]
}
```

事件选项配置改造：

- `resolution_mode = "combat"` 时，新增 `enemy_template_id`
- 旧的 `result_on_success.battle` 继续兼容读取，但不再作为控制台保存目标
- `result_on_failure` 保留在事件侧，用来描述战斗失败代价
- `log_text_success`、`log_text_failure`、`next_event_id` 继续保留在事件侧

## 后端设计

新增模块：

- `app/admin/repositories/enemy_config_repository.py`
- `app/admin/services/enemy_validation_service.py`
- `app/admin/services/enemy_admin_service.py`

新增后台接口：

- `GET /admin/api/battle/enemies`
- `GET /admin/api/battle/enemies/{enemy_id}`
- `POST /admin/api/battle/enemies`
- `PUT /admin/api/battle/enemies/{enemy_id}`
- `DELETE /admin/api/battle/enemies/{enemy_id}`
- `POST /admin/api/battle/validate`
- `POST /admin/api/battle/reload`

运行时改造：

- `RunService` 新增敌人模板运行时装载与 `reload_enemy_config(...)`
- `EventResolutionService` 在战斗开始时优先按 `enemy_template_id` 查找模板并构建敌人状态
- 战斗胜利时，成功奖励优先读取敌人模板 `rewards`
- 战斗失败时继续使用事件配置中的 `result_on_failure`
- 逃跑逻辑继续沿用当前实现

为了减少首版改动，不新增新的结果类型；敌人奖励直接复用现有 `EventResultPayload` 结构。

## 控制台设计

控制台顶层新增并列页签：

- `事件配置`
- `境界配置`
- `洞府配置`
- `战斗配置`

新增页面：

- `BattleEnemyListPage`
- `BattleEnemyEditorPage`

列表页职责：

- 展示敌人 ID、名称、境界文案、气血、攻击、防御、速度、是否允许逃跑
- 支持进入编辑
- 支持校验配置
- 支持重载运行时

编辑页职责：

- 编辑基础信息与战斗属性
- 编辑奖励配置
- 保存、删除、返回列表

事件配置页改造：

- `resolution_mode = "combat"` 时显示“敌人模板”下拉框
- 下拉数据来自 `/admin/api/battle/enemies`
- 去掉当前内嵌敌人数值编辑能力
- 成功结果面板不再承担敌人奖励维护
- 失败结果面板继续保留

## 兼容策略

首版采用渐进兼容：

- 新配置优先：若 combat 选项存在 `enemy_template_id`，运行时读取敌人模板
- 旧配置兜底：若没有 `enemy_template_id`，仍回退读取旧的 `battle` 内嵌字段
- 控制台重新保存 combat 选项后，应统一写入 `enemy_template_id`

这样可以避免一次性迁移全部历史事件，并保证现有运行中的老配置仍可用。

## 校验规则

敌人模板校验：

- `enemy_id` 必填且唯一
- `enemy_name` 必填
- `enemy_realm_label` 必填
- `enemy_hp >= 1`
- `enemy_attack >= 0`
- `enemy_defense >= 0`
- `enemy_speed >= 0`
- `allow_flee` 必须是布尔值
- `rewards` 必须是合法结果载荷
- `rewards` 中不允许再次嵌套 `battle`

事件配置校验：

- 当 `resolution_mode = "combat"` 时，必须满足以下任一条件：
  - `enemy_template_id` 指向一个存在的敌人模板
  - 旧配置里仍有合法的 `battle` 内嵌字段
- 若同时存在两者，运行时以 `enemy_template_id` 为准

## 测试策略

后端：

- 敌人配置仓储读写
- 敌人配置校验
- 管理 API 列表、详情、创建、更新、删除、校验、重载
- 运行时按 `enemy_template_id` 开启战斗
- 战斗胜利奖励来自敌人模板
- 老的内嵌 `battle` 配置仍可运行

前端：

- 战斗配置列表页渲染
- 战斗配置编辑页加载、保存、删除
- 事件编辑页 combat 选项显示模板选择器
- 事件保存时写入 `enemy_template_id`

## 实施建议

先完成后端配置与运行时读取，再接入控制台新页签，最后收口事件编辑页。这样可以先把新模型与兼容逻辑稳住，避免前端先行后反复调整接口。
