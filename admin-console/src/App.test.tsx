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
