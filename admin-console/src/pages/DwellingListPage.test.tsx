import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { DwellingListPage } from "./DwellingListPage";

test("renders dwelling toolbar and opens drawer editing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.endsWith("/admin/api/dwelling/facilities/spirit_field")) {
        return {
          ok: true,
          json: async () => ({
            facility_id: "spirit_field",
            display_name: "灵田",
            facility_type: "production",
            summary: "提供灵植",
            function_unlock_text: "",
            levels: [
              {
                level: 1,
                entry_cost: { spirit_stone: 50 },
                maintenance_cost: { spirit_stone: 2 },
                resource_yields: { basic_herb: 2 },
                cultivation_exp_gain: 0,
                special_effects: {},
              },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/dwelling/facilities/spirit_gathering_array")) {
        return {
          ok: true,
          json: async () => ({
            facility_id: "spirit_gathering_array",
            display_name: "聚灵阵",
            facility_type: "boost",
            summary: "提供增益",
            function_unlock_text: "",
            levels: [
              {
                level: 1,
                entry_cost: { spirit_stone: 100 },
                maintenance_cost: { spirit_stone: 4 },
                resource_yields: {},
                cultivation_exp_gain: 6,
                special_effects: { breakthrough_bonus_rate: 0.02 },
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
              facility_id: "spirit_field",
              display_name: "灵田",
              facility_type: "production",
              summary: "提供灵植",
              max_level: 4,
              level_count: 4,
            },
            {
              facility_id: "spirit_gathering_array",
              display_name: "聚灵阵",
              facility_type: "boost",
              summary: "提供增益",
              max_level: 3,
              level_count: 3,
            },
          ],
        }),
      };
    })
  );

  render(<DwellingListPage />);

  expect(await screen.findByLabelText("当前设施")).toBeInTheDocument();
  expect(document.querySelector(".registry-list")).toBeNull();
  expect(await screen.findByRole("button", { name: "设施信息" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "等级配置" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "特殊效果" })).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("当前设施"), {
    target: { value: "spirit_gathering_array" },
  });
  expect(await screen.findByText("增益设施")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "设施信息" }));
  expect(await screen.findByRole("dialog", { name: "设施信息" })).toBeInTheDocument();
  expect(await screen.findByDisplayValue("spirit_gathering_array")).toBeInTheDocument();
});
