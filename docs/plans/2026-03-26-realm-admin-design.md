# 境界配置后台设计

最后更新：2026-03-26

## 目标

在现有事件控制台基础上，新增“境界配置”能力，使运营或策划可以在后台完成以下操作：

- 配置当前游戏开放的境界节点
- 维护每个境界节点的中文展示名称
- 维护境界节点排序
- 配置突破所需修为
- 配置突破消耗灵石
- 配置基础突破成功率
- 配置突破成功后的寿元加成
- 通过按钮实时重载并生效

本轮只支持“灵石”作为额外突破条件，不引入材料、丹药、装备等其他突破消耗字段。

## 背景约束

当前项目中的境界配置仍写死在 `app/core_loop/seeds.py`，存在几个问题：

- 控制台无法维护
- 无法和事件配置一样做显式校验
- 无法支持完整增删改查和排序
- 改动后只能靠重启服务重新加载

同时，当前突破逻辑仅支持“大境界”顺序突破，而产品要求已经明确为“小层级逐级突破”，例如：

- 炼气初期
- 炼气中期
- 炼气后期
- 炼气大圆满
- 筑基初期

因此，这次不仅是“后台加页面”，还需要把运行时境界配置从写死逻辑抽到可加载配置。

## 设计选择

### 方案 1：继续使用 Python seed，后台直接写源码

优点：

- 改动最少

缺点：

- 可维护性差
- 不适合做排序和引用校验
- 风险高
- 后续扩展性差

不采用。

### 方案 2：独立 `JSON` 境界配置 + 后台管理 + 运行时 reload

优点：

- 和现有事件配置后台架构一致
- 易于做 CRUD、排序、校验和引用检查
- 易于后续迁移到 MySQL
- 可以通过按钮实时生效

缺点：

- 需要补一套 realm repository、validation、admin API 和前端页面

采用本方案。

### 方案 3：直接上通用配置中心

优点：

- 长期结构完整

缺点：

- 当前属于过度工程
- 交付慢

本轮不采用。

## 核心建模

### 境界节点粒度

突破链路以“小层级节点”为单位，而不是仅以大境界为单位。

例如：

- `qi_refining_early`
- `qi_refining_mid`
- `qi_refining_late`
- `qi_refining_peak`
- `foundation_early`
- `foundation_mid`

每一个节点都是一个独立可配置的突破目标。

### RealmConfig 字段

每个境界节点至少包含：

- `key`
  - 内部唯一标识
  - 创建后不可修改
- `display_name`
  - 中文展示名称，例如“炼气初期”
- `major_realm`
  - 所属大境界，例如 `qi_refining`
- `stage_index`
  - 小层级序号，例如 `1~4`
- `order_index`
  - 全局排序序号，运行时以此排序
- `base_success_rate`
  - 基础突破成功率
- `required_cultivation_exp`
  - 突破到下一境界所需修为
- `required_spirit_stone`
  - 突破消耗灵石
- `lifespan_bonus`
  - 突破成功后新增寿元
- `is_enabled`
  - 是否开放

## 存储方案

首版继续沿用文件化配置，不迁移到 MySQL。

新增：

- `config/realms/realms.json`

后端新增 `RealmConfigRepository`，负责：

- 读取 `realms.json`
- 保存 `realms.json`
- 提供统一数据入口

后续若要迁移 MySQL，只新增新的 repository 实现，不改控制台页面和大部分业务层。

## 运行时加载

新增 realm registry / loader，用于替代 `seeds.py` 中写死的 `get_realm_configs()`。

运行时统一从 `realms.json` 加载，并在内存中构建：

- 按 `order_index` 排序后的 realm 列表
- `key -> realm config` 映射
- `key -> index` 映射

这些结构将被以下模块复用：

- `ProgressionService`
- `EventService`
- 其他后续需要境界排序和境界区间判断的模块

## 突破规则

### 当前规则调整

当前突破逻辑需要从“大境界升级”改为“按排序后的下一个节点升级”。

即：

- 当前角色在某个境界节点
- 突破时找到排序后的下一个启用节点
- 根据当前节点配置校验突破条件
- 成功后将角色境界切换到下一个节点

### 突破条件

首版只支持：

- 修为达到要求
- 灵石达到要求

暂不引入：

- 材料
- 丹药
- 装备
- 功法前置

### 事件境界过滤

事件系统中的 `realm_min` / `realm_max` 判断，继续保留现有字段，但比较顺序改为以新 realm registry 为准。

## 删除与校验规则

### `key` 不可修改

创建后只能修改：

- 中文名称
- 排序
- 成功率
- 突破需求
- 寿元奖励
- 是否开放

不能修改：

- `key`

### 删除校验

删除境界前，必须检查：

- 事件配置中是否有 `realm_min` 引用
- 事件配置中是否有 `realm_max` 引用

如果存在引用：

- 禁止删除
- 返回引用的事件列表

本轮不做“自动清空引用”。

### 基础校验

realm validation 至少检查：

- `key` 唯一
- `display_name` 不为空
- `order_index` 唯一
- `base_success_rate` 在合法范围内
- `required_cultivation_exp >= 0`
- `required_spirit_stone >= 0`
- `lifespan_bonus >= 0`
- `major_realm` 不为空
- `stage_index >= 1`

## 管理 API

在现有 `/admin/api` 下新增 realm 管理接口：

- `GET /admin/api/realms`
  - 返回境界列表
- `GET /admin/api/realms/{realm_key}`
  - 返回单个境界详情
- `POST /admin/api/realms`
  - 新建境界节点
- `PUT /admin/api/realms/{realm_key}`
  - 更新境界节点
- `DELETE /admin/api/realms/{realm_key}`
  - 删除境界节点
- `POST /admin/api/realms/reorder`
  - 保存排序结果
- `POST /admin/api/realms/validate`
  - 执行全量校验
- `POST /admin/api/realms/reload`
  - 重载运行时境界配置

## 控制台页面设计

### 导航结构

控制台首页从单一“事件库”扩展为两个入口：

- 事件配置
- 境界配置

### 境界列表页

列表页展示所有境界节点，每条显示：

- 中文名称
- 内部标识
- 所属大境界
- 小层级
- 当前排序
- 突破所需修为
- 突破所需灵石
- 基础成功率
- 寿元加成
- 是否开放

操作包括：

- 新建
- 编辑
- 删除
- 上移
- 下移
- 校验配置
- 重载运行时

### 境界编辑页

沿用现有“总览工作台 + 二级编辑层”模式，避免长页滚动。

编辑字段分为两个模块：

- 基础信息
  - `key`
  - 中文名称
  - 所属大境界
  - 小层级
  - 排序
  - 是否开放
- 突破配置
  - 所需修为
  - 所需灵石
  - 基础成功率
  - 寿元加成

小屏下编辑层直接全屏覆盖，保证按钮始终可见。

## 实时生效

用户修改后可通过按钮执行 `reload`：

- 后端重新加载 `realms.json`
- `RunService` / `ProgressionService` / `EventService` 读取最新 realm registry
- 不需要重启服务

建议与事件后台保持一致：

- 保存 realm 后可自动尝试 reload
- 若 reload 成功，提示“已保存，并已重载运行时”
- 若 reload 失败，提示“已保存，但运行时重载失败，请手动重载”

## 测试范围

### 后端

- repository 读写测试
- validation 测试
- admin realm API CRUD 测试
- 删除引用拦截测试
- reload 后突破条件生效测试
- reload 后事件境界过滤顺序生效测试

### 前端

- 控制台导航切换测试
- 境界列表渲染测试
- 境界编辑保存测试
- 上移/下移排序测试
- 删除拦截错误提示测试
- reload 成功提示测试

## 结论

本次采用：

- `JSON` 文件存储
- 独立 realm repository
- 后台 realm CRUD
- 小层级逐级突破
- 引用保护删除
- 手动或保存后自动 reload

这样可以在不引入数据库的前提下，把“开放境界配置”和“突破门槛配置”都纳入控制台，并且为后续继续扩展更多配置模块保留清晰结构。
