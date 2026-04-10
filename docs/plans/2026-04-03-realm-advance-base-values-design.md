# Realm Advance Base Values Design

## Goal

在境界配置的“基础信息”中新增两个字段，用来控制角色每次执行“推进时间”时的基础修为增长与基础灵石消耗，并保证推进逻辑按当前所在境界配置生效。

## Chosen Approach

采用直接扩展 `RealmConfig` 的方案，在每条境界配置上新增两个平铺字段：

- `base_cultivation_gain_per_advance`
- `base_spirit_stone_cost_per_advance`

不新增额外规则对象，也不引入全局默认规则表。这样后台编辑、配置校验、运行时读取都围绕同一份境界配置展开，范围最小，语义最清晰。

## Runtime Semantics

- 每次调用 `advance_time` 时，读取角色“当前所在境界”的配置。
- 本次推进必须先校验灵石是否足够支付 `base_spirit_stone_cost_per_advance`。
- 若灵石不足，则直接阻止推进，返回 `ConflictError`，本次推进不产生任何副作用。
- 若灵石足够，则固定执行以下顺序：
  1. 扣除本次推进的基础灵石消耗
  2. 增加本次推进的基础修为
  3. 继续现有推进流程：寿元扣减、洞府月结、炼丹推进、事件冷却与事件抽取
- 推进后增加的修为仍受现有突破上限截断规则约束。

## Admin Console

“境界配置 -> 基础信息”新增两个数字输入框：

- `每次推进基础修为增加`
- `每次推进灵石消耗`

两者都是非负整数，纳入现有 `RealmInput` 的读取、回显、保存和新建默认值。

## Validation Rules

- 两个新字段都必须是整数
- 两个新字段都必须 `>= 0`
- 历史配置若未填写，运行时与后台归一化为 `0`

## Config Migration

`config/realms/realms.json` 中每条境界增加：

```json
{
  "base_cultivation_gain_per_advance": 0,
  "base_spirit_stone_cost_per_advance": 0
}
```

默认值先保持 `0`，保证老配置可平滑升级，再由后台逐条配置实际数值。

## Test Scope

后端新增或更新测试覆盖：

- 推进时间按当前境界配置增加修为并扣除灵石
- 灵石不足时阻止推进且不修改状态
- 推进增加的修为仍受突破上限截断
- API 序列化可返回新字段
- 管理台保存境界时会提交新字段

管理台测试覆盖：

- 基础信息抽屉正确回显新字段
- 编辑后保存请求带上新字段
