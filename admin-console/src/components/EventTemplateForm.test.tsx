import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EventTemplateForm } from "./EventTemplateForm";

test("requirements section starts with only add button when event has no preconditions", () => {
  const onChange = vi.fn();

  render(
    <EventTemplateForm
      isNew
      onChange={onChange}
      sections={["requirements"]}
      template={{
        event_id: "evt_empty",
        event_name: "Empty Event",
        event_type: "cultivation",
        outcome_type: "cultivation",
        risk_level: "normal",
        trigger_sources: ["global"],
        choice_pattern: "binary_choice",
        title_text: "",
        body_text: "",
        weight: 1,
        is_repeatable: true,
        option_ids: [],
        required_resources: {},
        required_statuses: [],
        excluded_statuses: [],
        required_techniques: [],
        required_equipment_tags: [],
        required_rebirth_count: 0,
        required_karma_min: null,
        required_luck_min: 0,
        flags: [],
      }}
    />
  );

  expect(screen.queryByRole("heading", { name: "前置条件" })).toBeNull();
  expect(screen.getByRole("button", { name: "新增前置条件" })).toBeInTheDocument();
  expect(screen.queryByLabelText("所需资源")).toBeNull();
  expect(screen.queryByLabelText("需要状态")).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: "新增前置条件" }));
  fireEvent.change(screen.getByLabelText("前置条件类型"), {
    target: { value: "required_resources" },
  });
  fireEvent.click(screen.getByRole("button", { name: "确认新增" }));

  expect(screen.getByText("当前还没有资源前置。")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "新增资源" })).toBeInTheDocument();
});
