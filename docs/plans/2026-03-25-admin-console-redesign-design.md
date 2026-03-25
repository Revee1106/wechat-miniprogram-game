# Wendao Admin Console Redesign Design

**Date:** 2026-03-25

## Background

The current admin console is functionally usable, but it still behaves like an exposed data form:

- too many fields are flattened on one page
- the visual hierarchy is weak
- most labels expose backend field names directly
- option editing is hard to scan and easy to misread

This redesign focuses on usability first, while giving the console a stronger game-planning identity that better matches the Wendao setting.

## Goals

- Redesign the admin console as a card-based planning workbench instead of a raw form page.
- Replace visible English field labels with Chinese names and short helper copy.
- Improve list scanning, event editing flow, and option editing ergonomics.
- Keep all current backend APIs and data contracts unchanged.

## Non-Goals

- No backend API redesign.
- No drag-and-drop event graph editor.
- No schema migration.
- No visual editor for arbitrary formulas.

## Product Direction

Adopt a "game planner workbench" interface, not a generic SaaS admin screen.

### Chosen Direction

Use a card-based workbench:

- fixed top console bar
- event library shown as Chinese summary cards
- event editing split into themed sections
- options edited as collapsible cards with summary headers
- validation and runtime actions grouped into one feedback area

### Rejected Alternatives

#### Skin-Only Refresh

Changing colors and spacing without changing structure would leave the main usability problems in place.

#### Dual-Pane Graph Editor

This would be visually interesting but premature for the current event model and would slow down basic CRUD work.

## Visual Language

### Tone

- planning desk
- scroll-and-ledger feel
- restrained fantasy flavor

### Palette

- warm rice-paper background
- dark ink green as the primary UI tone
- muted bronze as the accent tone
- cinnabar red for destructive states

### Typography

- display heading with a literary serif tone
- body text with a readable Chinese sans stack
- no generic SaaS headline treatment

### Surfaces

- cards with subtle borders and layered shadows
- soft gradients and faint paper texture
- dense information balanced with strong grouping

## Information Architecture

### Admin Shell

The shell should include:

- brand/title area
- signed-in state
- primary actions
- page subtitle or current event context

### Event Library

Replace the current table-first page with event cards.

Each card shows:

- event name
- event id
- type
- outcome tendency
- risk level
- trigger source
- region
- realm range
- repeatability
- option count

Actions per card:

- edit
- duplicate
- delete

### Event Workbench

Split event editing into cards:

1. Event identity
2. Trigger rules
3. Preconditions
4. Event narrative
5. Option orchestration
6. Validation and runtime feedback

## Chinese Field Mapping

Visible labels should switch to Chinese. Internal values remain unchanged.

### Template Fields

- `event_id` -> `事件编号`
- `event_name` -> `事件名称`
- `event_type` -> `事件类型`
- `outcome_type` -> `结果倾向`
- `risk_level` -> `风险等级`
- `choice_pattern` -> `选项模式`
- `trigger_sources` -> `触发来源`
- `weight` -> `触发权重`
- `region` -> `地域限定`
- `realm_min` -> `最低境界`
- `realm_max` -> `最高境界`
- `cooldown_rounds` -> `冷却回合`
- `max_trigger_per_run` -> `单局上限`
- `required_resources` -> `所需资源`
- `required_statuses` -> `需要状态`
- `excluded_statuses` -> `排斥状态`
- `required_techniques` -> `所需功法`
- `required_equipment_tags` -> `所需装备标签`
- `required_rebirth_count` -> `最低转生次数`
- `required_karma_min` -> `最低因果`
- `required_luck_min` -> `最低气运`
- `flags` -> `附加标记`
- `title_text` -> `标题文案`
- `body_text` -> `正文文案`
- `is_repeatable` -> `可重复触发`

### Option Fields

- `option_id` -> `选项编号`
- `option_text` -> `选项文案`
- `sort_order` -> `排序`
- `is_default` -> `默认选项`
- `requires_resources` -> `选项所需资源`
- `requires_statuses` -> `选项需要状态`
- `requires_techniques` -> `选项所需功法`
- `requires_equipment_tags` -> `选项所需装备标签`
- `success_rate_formula` -> `成功率公式`
- `next_event_id` -> `后续事件`
- `log_text_success` -> `成功日志`
- `log_text_failure` -> `失败日志`

### Result Payload Fields

- `resources` -> `资源变化`
- `cultivation_exp` -> `修为变化`
- `lifespan_delta` -> `寿元变化`
- `hp_delta` -> `气血变化`
- `breakthrough_bonus` -> `突破加成`
- `technique_exp` -> `功法经验`
- `luck_delta` -> `气运变化`
- `karma_delta` -> `因果变化`
- `rebirth_progress_delta` -> `转生进度`
- `statuses_add` -> `增加状态`
- `statuses_remove` -> `移除状态`
- `techniques_add` -> `获得功法`
- `equipment_add` -> `获得装备标签`
- `equipment_remove` -> `移除装备标签`
- `death` -> `导致死亡`

## Interaction Design

### Event Library

- filters remain at the top, but use Chinese labels
- cards show dense summaries without requiring entry into edit mode
- primary action is `新建事件`
- destructive actions should be visually separated

### Event Workbench

- use a sticky action bar
- show one summary card for event identity at the top
- organize detailed form controls into section cards
- keep long text and line-list inputs, but add helper text and examples
- use collapsible option cards so large events remain manageable

### Validation Feedback

- show save success, reload success, and validation results in one unified status card
- error copy should remain direct and readable

## Implementation Boundaries

The redesign should only affect the admin frontend:

- React components
- page structure
- styling
- visible labels and helper text
- frontend tests that assert the new UI

Backend routes and payload schemas remain unchanged.

## Testing Strategy

Frontend verification should cover:

- Chinese page headings and shell rendering
- event library filtering and action rendering
- editor save flow with Chinese labels
- option card expansion and payload editor interaction

Backend regression still runs to ensure no accidental contract breakage.
