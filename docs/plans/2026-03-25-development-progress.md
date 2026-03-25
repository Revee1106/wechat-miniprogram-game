# 2026-03-25 开发进度

## 今日概览

今天完成了事件系统、后台控制台、小程序事件页三个方向的迭代，覆盖后端、控制台前端和小程序前端两个仓库。

## 后端进度

- 按 `docs/wendao_event_config_spec.md` 完成事件配置模型对齐，补齐模板、选项、结果 payload、冷却与触发次数等能力。
- 事件触发逻辑从顺序轮转改为随机触发，并临时将邪修事件 `evt_evil_cultist_012` 排除在随机池外。
- 在随机触发基础上继续补齐权重逻辑：
  - 先按事件类型总权重抽取类型。
  - 再在该类型下按事件 `weight` 抽取具体事件。
- 将原本依赖随机事件池的回归测试改为确定性配置，避免测试受随机结果影响。

## 控制台进度

- 新增后台管理模块与 `/admin` 控制台。
- 完成后台登录保护：
  - `ADMIN_PASSWORD`
  - `ADMIN_SESSION_SECRET`
  - HttpOnly Cookie 会话
- 完成事件模板与选项的 CRUD、校验、运行时重载。
- 控制台页面改成卡片式策划工作台，整体中文化。
- 编辑页改成“工作台 + 二级编辑层”结构，适配笔记本等小屏幕。
- `single_outcome` 事件不再暴露多选项编排，改为默认单一结果编辑。
- “触发来源”从单选下拉改成标签式多选。
- 控制台补充展示“同类总权重”：
  - 列表卡片显示当前事件所属类型总权重。
  - 编辑页页头显示当前类型总权重，并会随未保存的权重修改实时变化。

## 小程序前端进度

- 修复事件页 `wx:key` 重复问题。
- 历史记录项改为使用稳定唯一 key，避免开发者工具重复 key 告警。

## 验证结果

- 后端：`python -m pytest tests/backend -q`
- 控制台前端：`npm test`
- 控制台前端：`npm run build`
- 小程序前端：
  - `node tests/frontend/core_loop_pages.test.mjs`
  - `node tests/frontend/app_manifest.test.mjs`
  - `node tests/frontend/dev_config.test.mjs`

## 推送说明

- 后端仓库：提交后台控制台、事件权重随机、今日进度文档等改动。
- 前端仓库：提交事件页 key 修复与对应测试更新。
