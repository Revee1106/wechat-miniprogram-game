import { fireEvent, render, screen, within } from "@testing-library/react";
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

  expect(await screen.findByText("WENDAO CONTROL")).toBeInTheDocument();
  expect(screen.getByDisplayValue("admin")).toBeInTheDocument();
  expect(screen.getByRole("button")).toBeInTheDocument();
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
      if (url.includes("/admin/api/events/event_one")) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "event_one",
              event_name: "Event One",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Event One",
              body_text: "Body",
              weight: 1,
              is_repeatable: true,
              option_ids: ["option_one"],
            },
            options: [
              {
                option_id: "option_one",
                event_id: "event_one",
                option_text: "Absorb",
                sort_order: 1,
                is_default: true,
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
              event_id: "event_one",
              event_name: "Event One",
              event_type: "cultivation",
              risk_level: "normal",
              weight: 1,
              option_ids: ["option_one"],
              is_repeatable: true,
            },
          ],
        }),
      };
    })
  );

  render(<App />);

  expect(await screen.findByDisplayValue("Event One")).toBeInTheDocument();
  expect(screen.getByRole("navigation")).toBeInTheDocument();
  expect(screen.getByText("退出登录")).toBeInTheDocument();
});

test("switches between event, realm, and dwelling workbenches", async () => {
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
      if (url.includes("/admin/api/events/event_one")) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "event_one",
              event_name: "Event One",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Event One",
              body_text: "Body",
              weight: 1,
              is_repeatable: true,
              option_ids: ["option_one"],
            },
            options: [
              {
                option_id: "option_one",
                event_id: "event_one",
                option_text: "Absorb",
                sort_order: 1,
                is_default: true,
              },
            ],
          }),
        };
      }
      if (url.includes("/admin/api/realms")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                key: "realm_one",
                display_name: "Realm One",
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
      if (url.includes("/admin/api/dwelling/facilities/spirit_field")) {
        return {
          ok: true,
          json: async () => ({
            facility_id: "spirit_field",
            display_name: "Spirit Field",
            facility_type: "production",
            summary: "Provides herbs",
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
      if (url.includes("/admin/api/dwelling/facilities")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                facility_id: "spirit_field",
                display_name: "Spirit Field",
                facility_type: "production",
                summary: "Provides herbs",
                max_level: 3,
                level_count: 3,
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
              event_id: "event_one",
              event_name: "Event One",
              event_type: "cultivation",
              risk_level: "normal",
              weight: 1,
              option_ids: ["option_one"],
              is_repeatable: true,
            },
          ],
        }),
      };
    })
  );

  render(<App />);

  expect(await screen.findByDisplayValue("Event One")).toBeInTheDocument();

  const navButtons = within(screen.getByRole("navigation", { name: "主导航" })).getAllByRole(
    "button"
  );

  fireEvent.click(navButtons[1]);
  expect(await screen.findByDisplayValue("Realm One")).toBeInTheDocument();

  fireEvent.click(navButtons[2]);
  expect(await screen.findByDisplayValue("Spirit Field")).toBeInTheDocument();
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

  const { container } = render(<App />);

  fireEvent.change(await screen.findByDisplayValue("admin"), {
    target: { value: "admin" },
  });

  const passwordInput = container.querySelector('input[type="password"]');
  if (!passwordInput) {
    throw new Error("Password input not found");
  }
  fireEvent.change(passwordInput, {
    target: { value: "bad-password" },
  });

  fireEvent.click(screen.getByRole("button"));

  expect(await screen.findByRole("alert")).toHaveTextContent("invalid admin credentials");
});
