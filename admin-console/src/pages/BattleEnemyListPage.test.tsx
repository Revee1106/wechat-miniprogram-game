import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { BattleEnemyListPage } from "./BattleEnemyListPage";

test("renders enemy templates and reloads runtime after save", async () => {
  let savedEnemy: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/admin/api/battle/enemies/enemy_bandit_qi_early") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            enemy_id: "enemy_bandit_qi_early",
            enemy_name: "山匪",
            enemy_realm_label: "炼气初期",
            enemy_hp: 36,
            enemy_attack: 8,
            enemy_defense: 4,
            enemy_speed: 6,
            allow_flee: true,
            rewards: {
              resources: { spirit_stone: 7 },
              character: { cultivation_exp: 5 },
            },
          }),
        };
      }
      if (
        url.endsWith("/admin/api/battle/enemies/enemy_bandit_qi_early") &&
        init?.method === "PUT"
      ) {
        savedEnemy = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedEnemy,
        };
      }
      if (url.endsWith("/admin/api/battle/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({ reloaded: true, enemy_count: 1 }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              enemy_id: "enemy_bandit_qi_early",
              enemy_name: "山匪",
              enemy_realm_label: "炼气初期",
              enemy_hp: 36,
              enemy_attack: 8,
              enemy_defense: 4,
              enemy_speed: 6,
              allow_flee: true,
              rewards: {
                resources: { spirit_stone: 7 },
                character: { cultivation_exp: 5 },
              },
            },
          ],
        }),
      };
    })
  );

  render(<BattleEnemyListPage />);

  expect(await screen.findByLabelText("当前敌人模板")).toBeInTheDocument();
  expect(await screen.findByDisplayValue("山匪")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("敌人名称"), {
    target: { value: "山匪头目" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存敌人模板" }));

  await waitFor(() => {
    expect(savedEnemy).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedEnemy).toMatchObject({
    enemy_id: "enemy_bandit_qi_early",
    enemy_name: "山匪头目",
  });
});

test("creates a draft enemy immediately when clicking new enemy template", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [],
      }),
    }))
  );

  render(<BattleEnemyListPage />);

  fireEvent.click(await screen.findByRole("button", { name: "新建敌人模板" }));

  expect(await screen.findByLabelText("敌人 ID")).toBeInTheDocument();
  expect(screen.getByLabelText("敌人 ID")).toHaveValue("");
  expect(screen.getByRole("button", { name: "保存敌人模板" })).toBeEnabled();
});
