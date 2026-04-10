import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EventOptionEditor } from "./EventOptionEditor";

function createCombatOption() {
  return {
    option_id: "opt_battle",
    option_text: "遭遇山匪",
    sort_order: 1,
    is_default: true,
    resolution_mode: "combat",
    requires_resources: {},
    requires_statuses: [],
    requires_techniques: [],
    requires_equipment_tags: [],
    success_rate_formula: "base_success_rate + 0.1",
    result_on_success: {
      resources: { spirit_stone: 2 },
    },
    result_on_failure: {},
    next_event_id: null,
    log_text_success: "",
    log_text_failure: "",
  };
}

test("option requirement section starts collapsed until a precondition is added", () => {
  const onChangeOption = vi.fn();

  render(
    <EventOptionEditor
      existingOptionIds={[]}
      onAddOption={() => {}}
      onChangeOption={onChangeOption}
      onRemoveOption={() => {}}
      options={[
        {
          option_id: "opt_empty",
          option_text: "Empty Option",
          sort_order: 1,
          is_default: true,
          requires_resources: {},
          requires_statuses: [],
          requires_techniques: [],
          requires_equipment_tags: [],
          success_rate_formula: "",
          result_on_success: {},
          result_on_failure: {},
          next_event_id: null,
          log_text_success: "",
          log_text_failure: "",
        },
      ]}
    />
  );

  expect(screen.getByRole("button", { name: "新增前置条件" })).toBeInTheDocument();
  expect(screen.queryByLabelText("选项需要状态")).toBeNull();
  expect(screen.queryByLabelText("选项所需功法")).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "新增前置条件" }));
  fireEvent.change(screen.getByLabelText("前置条件类型"), {
    target: { value: "requires_statuses" },
  });
  fireEvent.click(screen.getByRole("button", { name: "确认新增" }));

  expect(screen.getByLabelText("选项需要状态")).toBeInTheDocument();
  expect(screen.getAllByText("选项需要状态")).toHaveLength(1);
});

test("option editor exposes standalone event time cost and keeps lifespan change in results", () => {
  const onChangeOption = vi.fn();

  render(
    <EventOptionEditor
      existingOptionIds={[]}
      onAddOption={() => {}}
      onChangeOption={onChangeOption}
      onRemoveOption={() => {}}
      options={[
        {
          option_id: "evt_time_option_1",
          option_text: "问道耗时",
          sort_order: 1,
          is_default: true,
          resolution_mode: "direct",
          time_cost_months: 0,
          requires_resources: {},
          requires_statuses: [],
          requires_techniques: [],
          requires_equipment_tags: [],
          success_rate_formula: "",
          result_on_success: {},
          result_on_failure: {},
          next_event_id: null,
          log_text_success: "",
          log_text_failure: "",
        },
      ]}
    />
  );

  expect(screen.getByRole("heading", { name: "事件耗时（月）" })).toBeInTheDocument();
  expect(screen.queryByLabelText("耗时（月）")).toBeNull();
  expect(screen.getByRole("option", { name: "寿元变化" })).toBeInTheDocument();

  const input = screen.getByLabelText("事件耗时（月）");
  expect(input).toHaveValue(0);

  fireEvent.change(input, {
    target: { value: "3" },
  });

  expect(onChangeOption).toHaveBeenCalledWith(0, "time_cost_months", 3);
});

test("compact mode renders numbered option chips inline and edits only the selected option below", () => {
  const onSelectOption = vi.fn();

  const { container } = render(
    <EventOptionEditor
      activeIndex={1}
      compact
      eventOptions={[{ value: "evt_next", label: "后续事件 / evt_next" }]}
      existingOptionIds={["opt_absorb", "opt_withdraw"]}
      onAddOption={() => {}}
      onChangeOption={() => {}}
      onRemoveOption={() => {}}
      onSelectOption={onSelectOption}
      options={[
        {
          option_id: "opt_absorb",
          option_text: "顺势吐纳",
          sort_order: 10,
          is_default: true,
          requires_resources: {},
          requires_statuses: [],
          requires_techniques: [],
          requires_equipment_tags: [],
          success_rate_formula: "",
          result_on_success: {},
          result_on_failure: {},
          next_event_id: null,
          log_text_success: "",
          log_text_failure: "",
        },
        {
          option_id: "opt_withdraw",
          option_text: "收敛心神",
          sort_order: 20,
          is_default: false,
          requires_resources: {},
          requires_statuses: [],
          requires_techniques: [],
          requires_equipment_tags: [],
          success_rate_formula: "",
          result_on_success: {},
          result_on_failure: {},
          next_event_id: null,
          log_text_success: "",
          log_text_failure: "",
        },
      ]}
    />
  );

  expect(container.querySelector(".option-workbench")).not.toBeNull();
  expect(container.querySelector(".option-workbench__toolbar")).not.toBeNull();
  expect(container.querySelector(".option-workbench__chips")).not.toBeNull();
  expect(screen.queryByText("当前只编辑一个选项，其它选项通过左侧清单切换。")).toBeNull();
  expect(screen.getByDisplayValue("收敛心神")).toBeInTheDocument();
  expect(screen.queryByDisplayValue("顺势吐纳")).toBeNull();
  expect(screen.getByRole("button", { name: "选项 1" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "选项 2" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "选项 1" }));
  expect(onSelectOption).toHaveBeenCalledWith(0);
});

test("default option editing uses a single direct result until combat mode is selected", () => {
  render(
    <EventOptionEditor
      compact
      existingOptionIds={[]}
      onAddOption={() => {}}
      onChangeOption={() => {}}
      onRemoveOption={() => {}}
      options={[
        {
          option_id: "opt_direct",
          option_text: "直接结算",
          sort_order: 1,
          is_default: true,
          resolution_mode: "direct",
          requires_resources: {},
          requires_statuses: [],
          requires_techniques: [],
          requires_equipment_tags: [],
          success_rate_formula: "",
          result_on_success: {},
          result_on_failure: {},
          next_event_id: null,
          log_text_success: "",
          log_text_failure: "",
        },
      ]}
    />
  );

  expect(screen.getByLabelText("结算模式")).toHaveValue("direct");
  expect(screen.queryByLabelText("成功率公式")).toBeNull();
  expect(screen.queryByText("失败结果")).toBeNull();
  expect(screen.getByText("结果")).toBeInTheDocument();
});

test("option id field stays disabled for generated ids", () => {
  render(
    <EventOptionEditor
      existingOptionIds={[]}
      onAddOption={() => {}}
      onChangeOption={() => {}}
      onRemoveOption={() => {}}
      options={[
        {
          option_id: "evt_breakthrough_option_2",
          option_text: "继续吸纳灵气",
          sort_order: 2,
          is_default: false,
          resolution_mode: "direct",
          requires_resources: {},
          requires_statuses: [],
          requires_techniques: [],
          requires_equipment_tags: [],
          success_rate_formula: "",
          result_on_success: {},
          result_on_failure: {},
          next_event_id: null,
          log_text_success: "",
          log_text_failure: "",
        },
      ]}
    />
  );

  expect(screen.getByLabelText("选项编号")).toBeDisabled();
  expect(screen.getByDisplayValue("evt_breakthrough_option_2")).toBeDisabled();
});
