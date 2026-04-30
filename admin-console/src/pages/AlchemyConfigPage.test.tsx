import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { AlchemyConfigPage } from "./AlchemyConfigPage";

test("renders alchemy config page and reloads runtime after saving recipe", async () => {
  let savedRecipe: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal("confirm", vi.fn(() => true));
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/admin/api/alchemy/levels")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              { level: 0, display_name: "初识丹道", required_mastery_exp: 0 },
              { level: 1, display_name: "初窥门径", required_mastery_exp: 20 },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/alchemy/recipes/yang_qi_dan") && init?.method === "PUT") {
        savedRecipe = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedRecipe,
        };
      }
      if (url.endsWith("/admin/api/alchemy/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({ reloaded: true, level_count: 2, recipe_count: 1 }),
        };
      }
      if (url.endsWith("/admin/api/alchemy/recipes")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                recipe_id: "yang_qi_dan",
                display_name: "养气丹",
                category: "cultivation",
                description: "增加修为",
                required_alchemy_level: 0,
                duration_months: 1,
                base_success_rate: 0.86,
                per_level_success_rate: 0.04,
                success_mastery_exp_gain: 19,
                ingredients: { basic_herb: 2 },
                effect_type: "cultivation_exp",
                effect_value: 12,
                effect_summary: "直接增加修为",
                is_base_recipe: true,
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

  render(<AlchemyConfigPage />);

  expect(await screen.findByLabelText("当前丹方")).toBeInTheDocument();
  expect(await screen.findByDisplayValue("养气丹")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("丹方名称"), {
    target: { value: "养气丹·改" },
  });
  fireEvent.change(screen.getByLabelText("成功熟练度"), {
    target: { value: "21" },
  });
  fireEvent.change(screen.getByLabelText("每级成丹率变化"), {
    target: { value: "0.06" },
  });
  fireEvent.change(screen.getByLabelText("极品效果倍率"), {
    target: { value: "2.5" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存丹方" }));

  await waitFor(() => {
    expect(savedRecipe).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedRecipe).toMatchObject({
    recipe_id: "yang_qi_dan",
    display_name: "养气丹·改",
    per_level_success_rate: 0.06,
    success_mastery_exp_gain: 21,
    quality_profiles: expect.objectContaining({
      supreme: expect.objectContaining({ effect_multiplier: 2.5 }),
    }),
  });
});

test("separates recipe and level editing with a single active level panel", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.endsWith("/admin/api/alchemy/levels")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              { level: 0, display_name: "初识丹道", required_mastery_exp: 0 },
              { level: 1, display_name: "初窥门径", required_mastery_exp: 20 },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/alchemy/recipes")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                recipe_id: "yang_qi_dan",
                display_name: "养气丹",
                category: "cultivation",
                description: "增加修为",
                required_alchemy_level: 0,
                duration_months: 1,
                base_success_rate: 0.86,
                per_level_success_rate: 0.04,
                success_mastery_exp_gain: 19,
                ingredients: { basic_herb: 2 },
                effect_type: "cultivation_exp",
                effect_value: 12,
                effect_summary: "直接增加修为",
                is_base_recipe: true,
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

  const { container } = render(<AlchemyConfigPage />);

  await screen.findByLabelText("当前丹方");
  fireEvent.click(screen.getByRole("button", { name: "丹道等级 2" }));

  expect(await screen.findByLabelText("当前丹道等级")).toBeInTheDocument();
  expect(screen.getByDisplayValue("初识丹道")).toBeInTheDocument();
  expect(container.querySelectorAll(".config-workbench__detail-body .section-card")).toHaveLength(1);
  expect(screen.queryByText("校验回执")).not.toBeInTheDocument();
  expect(container.querySelector(".event-chip-cloud")).toBeNull();

  fireEvent.change(screen.getByLabelText("当前丹道等级"), {
    target: { value: "1" },
  });

  expect(screen.getByDisplayValue("初窥门径")).toBeInTheDocument();
  expect(container.querySelectorAll(".config-workbench__detail-body .section-card")).toHaveLength(1);
});
