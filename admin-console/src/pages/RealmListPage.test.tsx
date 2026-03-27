import { within } from "@testing-library/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { RealmListPage } from "./RealmListPage";

test("renders realm spectrum cards with key fields", async () => {
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

  render(<RealmListPage onCreateRealm={() => {}} onEditRealm={() => {}} />);

  expect(await screen.findByRole("heading", { name: "境界谱册" })).toBeInTheDocument();
  expect(screen.getByText("Qi Refining Early")).toBeInTheDocument();
  expect(within(screen.getAllByRole("article")[0]).getByText(/qi_refining_early/)).toBeInTheDocument();
  expect(screen.getByText(/100/)).toBeInTheDocument();
  expect(screen.getByText(/80/)).toBeInTheDocument();
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

  render(<RealmListPage onCreateRealm={() => {}} onEditRealm={() => {}} />);

  expect(await screen.findByText("Qi Refining Early")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "move-up qi_refining_mid" }));

  await waitFor(() => {
    expect(reloadCalls).toBe(1);
    expect(within(screen.getAllByRole("article")[0]).getByText("Qi Refining Mid")).toBeInTheDocument();
  });
});
