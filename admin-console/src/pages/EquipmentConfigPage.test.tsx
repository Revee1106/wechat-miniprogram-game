import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EquipmentConfigPage } from "./EquipmentConfigPage";

test("renders equipment items and reloads runtime after save", async () => {
  let savedItem: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/admin/api/equipment/items/iron_sword") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            equipment_id: "iron_sword",
            display_name: "铁剑",
            slot: "weapon",
            description: "入门弟子常用的铁剑。",
            attack: 4,
            defense: 0,
            hp_max: 0,
            special_effects: {},
          }),
        };
      }
      if (
        url.endsWith("/admin/api/equipment/items/iron_sword") &&
        init?.method === "PUT"
      ) {
        savedItem = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedItem,
        };
      }
      if (url.endsWith("/admin/api/equipment/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({ reloaded: true, equipment_count: 1 }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              equipment_id: "iron_sword",
              display_name: "铁剑",
              slot: "weapon",
              description: "入门弟子常用的铁剑。",
              attack: 4,
              defense: 0,
              hp_max: 0,
              special_effects: {},
            },
          ],
        }),
      };
    })
  );

  render(<EquipmentConfigPage />);

  expect(await screen.findByLabelText("当前装备")).toBeInTheDocument();
  expect(await screen.findByDisplayValue("铁剑")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("攻击"), {
    target: { value: "6" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存装备" }));

  await waitFor(() => {
    expect(savedItem).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedItem).toMatchObject({
    equipment_id: "iron_sword",
    slot: "weapon",
    attack: 6,
    defense: 0,
    hp_max: 0,
    special_effects: {},
  });
});

test("changes slot rules when selecting accessory", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [],
      }),
    }))
  );

  render(<EquipmentConfigPage />);

  fireEvent.click(await screen.findByRole("button", { name: "新建装备" }));
  fireEvent.change(screen.getByLabelText("装备类型"), {
    target: { value: "accessory" },
  });

  expect(screen.getByLabelText("攻击")).toBeDisabled();
  expect(screen.getByLabelText("防御")).toBeDisabled();
  expect(screen.getByLabelText("气血")).toBeDisabled();
  expect(screen.getByLabelText("特殊效果 JSON")).not.toBeDisabled();
  expect(screen.getByLabelText("特殊效果 JSON")).toHaveValue('{\n  "luck": 1\n}');
});
