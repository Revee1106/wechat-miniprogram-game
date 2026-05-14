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

test("requirements section can add dwelling facility minimum level", () => {
  const onChange = vi.fn();

  render(
    <EventTemplateForm
      isNew
      dwellingFacilityOptions={[
        { value: "spirit_field", label: "灵田 / spirit_field" },
        { value: "alchemy_room", label: "炼丹房 / alchemy_room" },
      ]}
      onChange={onChange}
      sections={["requirements"]}
      template={{
        event_id: "evt_facility_gate",
        event_name: "Facility Gate",
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
        required_completed_event_ids: [],
        required_dwelling_facility_levels: {},
        required_karma_min: null,
        required_luck_min: 0,
        flags: [],
      }}
    />
  );

  fireEvent.click(screen.getByRole("button", { name: "新增前置条件" }));
  expect(screen.getByRole("option", { name: "洞府设施最低等级" })).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("前置条件类型"), {
    target: { value: "required_dwelling_facility_levels" },
  });
  fireEvent.click(screen.getByRole("button", { name: "确认新增" }));

  expect(onChange).toHaveBeenCalledWith("required_dwelling_facility_levels", {});
  expect(screen.getByText("当前还没有洞府设施等级前置。")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "新增设施等级" }));

  expect(onChange).toHaveBeenLastCalledWith("required_dwelling_facility_levels", {
    spirit_field: 1,
  });
});

test("requirements section can add progress counter thresholds", () => {
  const onChange = vi.fn();

  render(
    <EventTemplateForm
      isNew
      onChange={onChange}
      sections={["requirements"]}
      template={{
        event_id: "evt_progress_gate",
        event_name: "Progress Gate",
        event_type: "alchemy",
        outcome_type: "alchemy",
        risk_level: "normal",
        trigger_sources: ["alchemy_based"],
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
        required_completed_event_ids: [],
        required_dwelling_facility_levels: {},
        required_progress_counters: {},
        required_karma_min: null,
        required_luck_min: 0,
        flags: [],
      }}
    />
  );

  fireEvent.click(screen.getByRole("button", { name: "新增前置条件" }));
  fireEvent.change(screen.getByLabelText("前置条件类型"), {
    target: { value: "required_progress_counters" },
  });
  fireEvent.click(screen.getByRole("button", { name: "确认新增" }));

  expect(onChange).toHaveBeenCalledWith("required_progress_counters", {});

  fireEvent.change(screen.getByLabelText("所需进度"), {
    target: { value: "alchemy.ning_qi_dan_clue:3" },
  });

  expect(onChange).toHaveBeenLastCalledWith("required_progress_counters", {
    "alchemy.ning_qi_dan_clue": 3,
  });
});

test("trigger section uses realm dropdowns for min and max realm", () => {
  render(
    <EventTemplateForm
      isNew
      onChange={vi.fn()}
      realmOptions={[
        { value: "qi_refining_early", label: "炼气初期" },
        { value: "qi_refining_mid", label: "炼气中期" },
      ]}
      sections={["trigger"]}
      template={{
        event_id: "evt_trigger",
        event_name: "Trigger Event",
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
        realm_min: "qi_refining_early",
        realm_max: "qi_refining_mid",
      }}
    />
  );

  expect(screen.getByLabelText("最低境界")).toHaveDisplayValue("炼气初期");
  expect(screen.getByLabelText("最高境界")).toHaveDisplayValue("炼气中期");
  expect(screen.getAllByRole("option", { name: "无限制" })).toHaveLength(2);
});

test("trigger section shows estimated draw chance when provided", () => {
  render(
    <EventTemplateForm
      isNew
      onChange={vi.fn()}
      drawChanceEstimate={{
        currentWeight: 7,
        typeTotalWeight: 8,
        allTotalWeight: 10,
        typeChance: 0.8,
        withinTypeChance: 0.875,
        finalChance: 0.7,
      }}
      sections={["trigger"]}
      template={{
        event_id: "evt_material_heavy",
        event_name: "Material Heavy",
        event_type: "material",
        outcome_type: "material",
        risk_level: "normal",
        trigger_sources: ["global"],
        choice_pattern: "binary_choice",
        title_text: "",
        body_text: "",
        weight: 7,
        is_repeatable: true,
        option_ids: [],
      }}
    />
  );

  expect(screen.getByLabelText("预估抽取概率")).toBeInTheDocument();
  expect(screen.getByText("当前事件")).toBeInTheDocument();
  expect(screen.getByText("70%")).toBeInTheDocument();
  expect(screen.getByText("7 / 10")).toBeInTheDocument();
});

test("identity section shows a disabled event id field", () => {
  render(
    <EventTemplateForm
      isNew
      onChange={vi.fn()}
      sections={["identity"]}
      template={{
        event_id: "evt_cultivation_2",
        event_name: "Auto Event",
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
      }}
    />
  );

  expect(screen.getByLabelText("事件编号")).toBeDisabled();
  expect(screen.getByDisplayValue("evt_cultivation_2")).toBeDisabled();
});
