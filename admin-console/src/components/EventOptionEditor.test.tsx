import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EventOptionEditor } from "./EventOptionEditor";

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

test("compact mode renders option chips inline and edits only the selected option below", () => {
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
  expect(screen.queryByText("当前只编辑一个选项，其他选项通过左侧清单切换。")).toBeNull();
  expect(screen.getByDisplayValue("收敛心神")).toBeInTheDocument();
  expect(screen.queryByDisplayValue("顺势吐纳")).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "顺势吐纳" }));
  expect(onSelectOption).toHaveBeenCalledWith(0);
});
