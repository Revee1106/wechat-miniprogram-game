# Event Option Time Cost Separation Design

**Date:** 2026-04-09

## Background

The admin console currently exposes option-level `time_cost_months` inside the `判定与后续` section and labels it as `耗时（月）`.

That presentation weakens the intended game meaning:

- option time cost is the lifespan cost required to execute the option
- result payload lifespan change is a separate outcome of success or failure

These are independent concepts and must remain independently editable.

## Problem

In the current UI, editors can easily misread `耗时（月）` as a generic narrative duration or confuse it with result payload `寿元变化`.

This causes a modeling problem:

- `time_cost_months` should represent the execution cost of taking the option
- `lifespan_delta` in the result payload should represent the consequence of the resolved result

An option may legitimately use both at the same time.

## Goals

- Make option execution cost visually independent from result payload changes.
- Rename the visible field to `事件耗时（月）`.
- Keep `结果` payload editing unchanged, including `寿元变化`.
- Preserve existing backend APIs and payload schemas.

## Non-Goals

- No backend schema change.
- No change to how `time_cost_months` is stored.
- No change to event resolution semantics.
- No change to result summary wording in backend responses.

## Chosen Direction

Split option editing into four peer sections:

1. `前置条件`
2. `判定与后续`
3. `事件耗时（月）`
4. `结果`

`事件耗时（月）` edits `time_cost_months` only.

`结果` continues to edit `result_on_success` and `result_on_failure`, including `寿元变化`.

## Rejected Alternatives

### Keep the field under `判定与后续`

This would be a smaller change, but the structure would still imply time cost is just a side property of resolution flow instead of a standalone option cost.

### Move time cost into the result payload editor

This would incorrectly merge execution cost and outcome effect, which contradicts the intended gameplay semantics.

## UI Design

### Option Editor

For both regular option editing and compact workbench mode:

- remove the numeric input from `判定与后续`
- add a new section card titled `事件耗时（月）`
- place one numeric input inside that section
- use the label and aria-label `事件耗时（月）`
- keep storing the value in `time_cost_months`

Suggested helper copy:

- `表示执行该选项额外消耗的时间，会单独扣减寿元，不等同于结果中的寿元变化。`

### Single Outcome Editor

For single-outcome events:

- keep `后续事件` and `结果日志`
- move `time_cost_months` into its own `事件耗时（月）` section
- keep the result payload editor unchanged below it

## Data Model

No data model changes:

- option execution cost remains `time_cost_months`
- result lifespan consequence remains `character.lifespan_delta`

Both may coexist on the same option.

## Testing Strategy

Frontend coverage should prove:

- the standalone `事件耗时（月）` section is rendered
- `判定与后续` no longer exposes the time cost input
- editing the new field still updates `time_cost_months`
- result payload editing still exposes `寿元变化`
- single-outcome editing also uses the new standalone section

Backend tests are unnecessary for this change because no backend behavior changes.
