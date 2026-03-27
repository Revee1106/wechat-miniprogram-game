import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

test("shows redesigned login page when session is missing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: false,
      status: 401,
      json: async () => ({ detail: "admin login required" }),
    }))
  );

  render(<App />);

  expect(await screen.findByText("问道控制台")).toBeInTheDocument();
  expect(await screen.findByText("控制台登录")).toBeInTheDocument();
});

test("shows shell and sign out action when session is active", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.includes("/admin/api/auth/session")) {
        return {
          ok: true,
          json: async () => ({ authenticated: true, username: "admin" }),
        };
      }
      return {
        ok: true,
        json: async () => ({ items: [] }),
      };
    })
  );

  render(<App />);

  expect(await screen.findByText("事件库")).toBeInTheDocument();
  expect(screen.getByText("退出登录")).toBeInTheDocument();
});

test("shows realm entry and switches to realm library", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.includes("/admin/api/auth/session")) {
        return {
          ok: true,
          json: async () => ({ authenticated: true, username: "admin" }),
        };
      }
      if (url.includes("/admin/api/realms")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                key: "qi_refining_early",
                display_name: "炼气初期",
                major_realm: "qi_refining",
                stage_index: 1,
                order_index: 1,
                base_success_rate: 0.95,
                required_cultivation_exp: 100,
                required_spirit_stone: 20,
                lifespan_bonus: 6,
                is_enabled: true,
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

  render(<App />);

  expect(await screen.findByRole("button", { name: "境界配置" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "境界配置" }));

  expect(await screen.findByText("境界谱册")).toBeInTheDocument();
  expect(screen.getByText("炼气初期")).toBeInTheDocument();
});

test("shows backend login error detail", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/auth/session")) {
        return {
          ok: false,
          status: 401,
          json: async () => ({ detail: "admin login required" }),
        };
      }
      if (url.includes("/admin/api/auth/login") && init?.method === "POST") {
        return {
          ok: false,
          status: 401,
          json: async () => ({ detail: "invalid admin credentials" }),
        };
      }
      return {
        ok: true,
        json: async () => ({ items: [] }),
      };
    })
  );

  render(<App />);

  fireEvent.change(await screen.findByLabelText("管理密码"), {
    target: { value: "bad-password" },
  });
  fireEvent.click(screen.getAllByRole("button", { name: "进入控制台" })[0]);

  expect(await screen.findByRole("alert")).toHaveTextContent("invalid admin credentials");
});
