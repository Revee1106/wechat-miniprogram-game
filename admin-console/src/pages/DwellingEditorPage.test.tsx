import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { DwellingEditorPage } from "./DwellingEditorPage";

test("loads dwelling facility detail and appends a new level", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.includes("/admin/api/dwelling/facilities/spirit_field")) {
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
      return {
        ok: true,
        json: async () => ({ items: [] }),
      };
    })
  );

  render(
    <DwellingEditorPage
      facilityId="spirit_field"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  expect(await screen.findByText("洞府工坊")).toBeInTheDocument();
  expect(screen.getAllByText(/等级 1/)).not.toHaveLength(0);
  fireEvent.click(screen.getByRole("button", { name: "新增等级" }));
  expect(screen.getByTestId("dwelling-level-2")).toBeInTheDocument();
});

test("saves dwelling facility changes through admin api", async () => {
  let savedFacility: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/dwelling/facilities/spirit_field") && !init?.method) {
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
      if (url.endsWith("/admin/api/dwelling/facilities/spirit_field") && init?.method === "PUT") {
        savedFacility = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedFacility,
        };
      }
      if (url.endsWith("/admin/api/dwelling/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({ reloaded: true, facility_count: 5 }),
        };
      }
      return {
        ok: true,
        json: async () => ({ items: [] }),
      };
    })
  );

  render(
    <DwellingEditorPage
      facilityId="spirit_field"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  expect(await screen.findByText("洞府工坊")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("设施名称"), {
    target: { value: "高阶灵田" },
  });
  const levelCard = screen.getByTestId("dwelling-level-1");
  fireEvent.change(within(levelCard).getByLabelText("进入该等级成本"), {
    target: { value: "spirit_stone:66" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存洞府配置" }));

  await waitFor(() => {
    expect(savedFacility).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedFacility).toMatchObject({
    display_name: "高阶灵田",
    levels: [
      {
        level: 1,
        entry_cost: { spirit_stone: 66 },
      },
    ],
  });
});
