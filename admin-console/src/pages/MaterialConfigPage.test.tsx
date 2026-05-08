import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { MaterialConfigPage } from "./MaterialConfigPage";

test("renders materials and reloads runtime after save", async () => {
  let savedItem: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/admin/api/materials/basic_herb") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            material_id: "basic_herb",
            display_name: "基础灵草",
            category: "herb",
            tier: 1,
            rarity: "common",
            source: "dwelling",
            description: "洞府灵田产出",
            tags: ["alchemy", "dwelling"],
          }),
        };
      }
      if (url.endsWith("/admin/api/materials/basic_herb") && init?.method === "PUT") {
        savedItem = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedItem,
        };
      }
      if (url.endsWith("/admin/api/materials/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({ reloaded: true, material_count: 1 }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              material_id: "basic_herb",
              display_name: "基础灵草",
              category: "herb",
              tier: 1,
              rarity: "common",
              source: "dwelling",
              description: "洞府灵田产出",
              tags: ["alchemy", "dwelling"],
            },
          ],
        }),
      };
    })
  );

  render(<MaterialConfigPage />);

  expect(await screen.findByLabelText("当前材料")).toBeInTheDocument();
  expect(await screen.findByDisplayValue("基础灵草")).toBeInTheDocument();
  expect(screen.getByText("炼丹材料 ×")).toBeInTheDocument();
  expect(screen.getByText("洞府相关 ×")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("选择材料标签"), {
    target: { value: "basic" },
  });
  fireEvent.click(screen.getByRole("button", { name: "添加标签" }));

  fireEvent.change(screen.getByLabelText("材料名称"), {
    target: { value: "基础灵草·改" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存材料" }));

  await waitFor(() => {
    expect(savedItem).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedItem).toMatchObject({
    material_id: "basic_herb",
    display_name: "基础灵草·改",
    tags: ["alchemy", "dwelling", "basic"],
  });
});

test("creates a new material draft with dwelling defaults", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [],
      }),
    }))
  );

  render(<MaterialConfigPage />);

  fireEvent.change(await screen.findByLabelText("新建材料 ID"), {
    target: { value: "moonlit_herb" },
  });
  fireEvent.click(screen.getByRole("button", { name: "新建材料" }));

  expect(screen.getByLabelText("材料 ID")).toHaveValue("moonlit_herb");
  expect(screen.getByLabelText("来源")).toHaveValue("dwelling");
  expect(screen.getByText("洞府相关 ×")).toBeInTheDocument();
  expect(screen.getByText("基础材料 ×")).toBeInTheDocument();
});
