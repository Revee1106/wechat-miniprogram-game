import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { RealmListPage } from "./RealmListPage";

test("renders compact realm toolbar and opens drawer editing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [
          {
            key: "qi_refining_early",
            display_name: "Qi Refining Early",
            major_realm: "qi_refining",
            stage_index: 1,
            order_index: 1,
            base_success_rate: 0.95,
            required_cultivation_exp: 100,
            required_spirit_stone: 20,
            lifespan_bonus: 6,
            is_enabled: true,
          },
          {
            key: "foundation_early",
            display_name: "Foundation Early",
            major_realm: "foundation",
            stage_index: 1,
            order_index: 5,
            base_success_rate: 0.78,
            required_cultivation_exp: 700,
            required_spirit_stone: 80,
            lifespan_bonus: 12,
            is_enabled: false,
          },
        ],
      }),
    }))
  );

  render(<RealmListPage />);

  expect(await screen.findByLabelText("当前境界")).toBeInTheDocument();
  expect(document.querySelector(".registry-group")).toBeNull();
  expect(screen.getByRole("button", { name: "基础信息" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "突破配置" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "基础信息" }));
  expect(await screen.findByRole("dialog", { name: "基础信息" })).toBeInTheDocument();
});

test("moves a realm upward and reloads runtime immediately", async () => {
  let currentItems = [
    {
      key: "qi_refining_early",
      display_name: "Qi Refining Early",
      major_realm: "qi_refining",
      stage_index: 1,
      order_index: 1,
      base_success_rate: 0.95,
      required_cultivation_exp: 100,
      required_spirit_stone: 20,
      lifespan_bonus: 6,
      is_enabled: true,
    },
    {
      key: "qi_refining_mid",
      display_name: "Qi Refining Mid",
      major_realm: "qi_refining",
      stage_index: 2,
      order_index: 2,
      base_success_rate: 0.9,
      required_cultivation_exp: 180,
      required_spirit_stone: 30,
      lifespan_bonus: 6,
      is_enabled: true,
    },
  ];
  let reloadCalls = 0;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/admin/api/realms") && !init?.method) {
        return {
          ok: true,
          json: async () => ({ items: currentItems }),
        };
      }
      if (url.endsWith("/admin/api/realms/reorder") && init?.method === "POST") {
        const payload = JSON.parse(String(init.body)) as { keys: string[] };
        currentItems = payload.keys.map((key, index) => ({
          ...currentItems.find((item) => item.key === key)!,
          order_index: index + 1,
        }));
        return {
          ok: true,
          json: async () => ({ items: currentItems }),
        };
      }
      if (url.endsWith("/admin/api/realms/reload") && init?.method === "POST") {
        reloadCalls += 1;
        return {
          ok: true,
          json: async () => ({ reloaded: true, realm_count: currentItems.length }),
        };
      }
      return {
        ok: true,
        json: async () => ({ items: currentItems }),
      };
    })
  );

  render(<RealmListPage />);

  expect(await screen.findByLabelText("当前境界")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("当前境界"), {
    target: { value: "qi_refining_mid" },
  });
  fireEvent.click(screen.getByRole("button", { name: "上移" }));

  await waitFor(() => {
    expect(reloadCalls).toBe(1);
  });

  const selector = screen.getByLabelText("当前境界") as HTMLSelectElement;
  const optionLabels = Array.from(selector.options)
    .slice(1)
    .map((option) => option.textContent?.trim());
  expect(optionLabels.slice(0, 2)).toEqual(["Qi Refining Mid", "Qi Refining Early"]);
});
