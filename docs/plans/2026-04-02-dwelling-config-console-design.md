# 洞府配置控制台设计

日期：2026-04-02

## 目标

在现有后台控制台中新增“洞府配置”模块，支持维护洞府设施的按等级配置，并让游戏启动与运行时都读取这份配置，而不是继续依赖 `DwellingService` 内部硬编码。

## 范围

本次只覆盖当前已有的 5 个洞府设施：

- `spirit_field`
- `spirit_spring`
- `mine_cave`
- `alchemy_room`
- `spirit_gathering_array`

本次支持：

- 编辑设施基础信息
- 按等级编辑“建造/升级成本、维护成本、产出/效果”
- 追加新等级，例如从 3 级扩展到 4 级
- 校验配置合法性
- 控制台保存后重载运行时
- 游戏启动时默认读取控制台配置文件

本次不支持：

- 新建设施 ID
- 删除设施
- 通用脚本化效果系统

## 配置模型

新增配置文件：`config/dwelling/facilities.json`

配置按设施保存，每个设施包含基础信息和连续等级列表。

设施级字段：

- `facility_id`
- `display_name`
- `facility_type`
- `summary`
- `function_unlock_text`
- `levels`

等级级字段：

- `level`
- `entry_cost`
- `maintenance_cost`
- `resource_yields`
- `cultivation_exp_gain`
- `special_effects`

约定：

- `level = 1` 的 `entry_cost` 表示建造成本
- `level >= 2` 的 `entry_cost` 表示从上一级升到当前级的升级成本
- 等级必须从 `1` 开始连续递增

## 特殊效果范围

本次仅开放当前已有特殊效果，不做通用扩展框架。

允许的特殊效果：

- `spirit_gathering_array.breakthrough_bonus_rate`
- `spirit_gathering_array.mine_spirit_stone_bonus_rate`

其他设施的 `special_effects` 必须为空对象。

## 后端设计

新增模块：

- `app/admin/repositories/dwelling_config_repository.py`
- `app/admin/services/dwelling_validation_service.py`
- `app/admin/services/dwelling_admin_service.py`

新增后台接口：

- `GET /admin/api/dwelling/facilities`
- `GET /admin/api/dwelling/facilities/{facility_id}`
- `PUT /admin/api/dwelling/facilities/{facility_id}`
- `POST /admin/api/dwelling/validate`
- `POST /admin/api/dwelling/reload`

运行时改造：

- `DwellingService` 改为从 `DwellingConfigRepository` 读取配置
- `DwellingService` 保留 `hydrate_run()` 机制，继续把运行态和配置态结合
- `RunService` 新增 `reload_dwelling_config(...)`
- 后台重载时刷新当前运行时使用的洞府配置

## 前端控制台设计

新增控制台模式：

- 洞府配置列表页 `DwellingListPage`
- 洞府配置编辑页 `DwellingEditorPage`

列表页职责：

- 展示所有设施卡片
- 展示设施类型、当前最高等级、等级数量
- 提供“编辑”“校验配置”“重载运行时”操作

编辑页职责：

- 编辑设施基础信息
- 展示等级卡片列表
- 每个等级编辑：
  - 进入该等级成本
  - 维护成本
  - 资源产出
  - 修为收益
  - 特殊效果
- 支持新增等级

交互约束：

- `facility_id` 只读
- 不允许删除中间等级
- 不支持删除全部等级

## 兼容策略

- 旧存档继续使用 `run.dwelling_facilities`
- `hydrate_run()` 按最新配置回填动态字段
- 新增 4 级后，旧存档设施可继续升级到 4 级
- 修改已有等级配置后，后续展示、升级和月结按新配置执行

## 校验规则

- 设施 ID 不为空且不可变
- 名称、类型非空
- 等级列表从 1 开始连续
- 金额、维护、产出、修为收益必须为非负整数
- 仅允许白名单特殊效果字段
- `spirit_gathering_array` 之外不能出现特殊效果

## 测试策略

后端：

- 配置仓储读写
- 配置校验
- 管理 API 列表、详情、更新、重载
- `DwellingService` 从 JSON 读取配置
- 追加 4 级后可升级到 4 级
- 特殊效果变更影响月结/突破逻辑

前端：

- 列表页展示设施信息
- 编辑页加载详情并保存
- 新增等级交互

