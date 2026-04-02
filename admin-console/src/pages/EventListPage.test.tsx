import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EventListPage } from "./EventListPage";

test("filters events by type in the compact workbench registry", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.includes("/admin/api/events/evt_material")) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_material",
              event_name: "Material Event",
              event_type: "material",
              outcome_type: "material",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Material Event",
              body_text: "Body",
              weight: 3,
              is_repeatable: true,
              option_ids: ["opt_material"],
            },
            options: [
              {
                option_id: "opt_material",
                event_id: "evt_material",
                option_text: "Collect",
                sort_order: 1,
                is_default: true,
              },
            ],
          }),
        };
      }
      if (url.includes("event_type=material")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                event_id: "evt_material",
                event_name: "Material Event",
                event_type: "material",
                risk_level: "normal",
                weight: 3,
                option_ids: ["opt_material"],
                is_repeatable: true,
              },
            ],
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              event_id: "evt_cultivation",
              event_name: "Cultivation Event",
              event_type: "cultivation",
              risk_level: "normal",
              weight: 2,
              option_ids: ["opt_cultivation"],
              is_repeatable: true,
            },
            {
              event_id: "evt_material",
              event_name: "Material Event",
              event_type: "material",
              risk_level: "normal",
              weight: 3,
              option_ids: ["opt_material"],
              is_repeatable: true,
            },
          ],
        }),
      };
    })
  );

  render(<EventListPage />);

  expect(await screen.findByLabelText("当前事件")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("事件类型筛选"), {
    target: { value: "material" },
  });

  await waitFor(() => {
    expect(screen.getByRole("option", { name: "Material Event" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Cultivation Event" })).not.toBeInTheDocument();
  });
});

test("uses four direct editor tabs and a right drawer instead of summary cards", async () => {
  const confirmSpy = vi.fn(() => false);
  vi.stubGlobal("confirm", confirmSpy);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.includes("/admin/api/events/evt_cultivation_one")) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_cultivation_one",
              event_name: "Cultivation One",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global", "realm_based"],
              choice_pattern: "binary_choice",
              title_text: "Cultivation One",
              body_text: "Body",
              weight: 2,
              is_repeatable: true,
              option_ids: ["opt_cultivation_one", "opt_cultivation_two"],
            },
            options: [
              {
                option_id: "opt_cultivation_one",
                event_id: "evt_cultivation_one",
                option_text: "Absorb",
                sort_order: 1,
                is_default: true,
              },
              {
                option_id: "opt_cultivation_two",
                event_id: "evt_cultivation_one",
                option_text: "Observe",
                sort_order: 2,
                is_default: false,
              },
            ],
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              event_id: "evt_cultivation_one",
              event_name: "Cultivation One",
              event_type: "cultivation",
              risk_level: "normal",
              weight: 2,
              option_ids: ["opt_cultivation_one", "opt_cultivation_two"],
              is_repeatable: true,
            },
            {
              event_id: "evt_cultivation_two",
              event_name: "Cultivation Two",
              event_type: "cultivation",
              risk_level: "safe",
              weight: 5,
              option_ids: ["opt_cultivation_three"],
              is_repeatable: true,
            },
          ],
        }),
      };
    })
  );

  render(<EventListPage />);

  expect(await screen.findByRole("button", { name: "基础信息" })).toBeInTheDocument();
  expect(document.querySelector(".event-chip-cloud")).toBeNull();
  expect(document.querySelector(".event-summary-grid")).toBeNull();
  expect(screen.getByRole("button", { name: "触发规则" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "前置条件" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "选项与结果" })).toBeInTheDocument();
  expect(screen.queryByText("保存后自动重载运行时")).toBeNull();
  expect(screen.getByText("全局触发 / 境界触发")).toBeInTheDocument();
  expect(screen.getByText("权重 2")).toBeInTheDocument();
  expect(screen.getByText("二择其一")).toBeInTheDocument();

  const toolbar = document.querySelector(".event-compact-toolbar");
  expect(toolbar).not.toBeNull();
  const scoped = within(toolbar as HTMLElement);
  const deleteButton = scoped.getByRole("button", { name: "删除事件" });
  expect(deleteButton).toBeEnabled();
  fireEvent.click(deleteButton);
  expect(confirmSpy).toHaveBeenCalledWith("确定删除事件 Cultivation One 吗？");

  fireEvent.click(screen.getByRole("button", { name: "基础信息" }));

  const dialog = await screen.findByRole("dialog", { name: "基础信息" });
  expect(within(dialog).getByLabelText("事件名称")).toHaveValue("Cultivation One");
  expect(within(dialog).getByLabelText("标题文案")).toHaveValue("Cultivation One");
});
