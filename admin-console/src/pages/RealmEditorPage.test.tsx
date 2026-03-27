import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { RealmEditorPage } from "./RealmEditorPage";

test("loads and saves a realm through the secondary editor panels", async () => {
  let savedRealm: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/realms/qi_refining_early") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
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
          }),
        };
      }
      if (url.endsWith("/admin/api/realms/qi_refining_early") && init?.method === "PUT") {
        savedRealm = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedRealm,
        };
      }
      if (url.endsWith("/admin/api/realms/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({
            reloaded: true,
            realm_count: 1,
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
    <RealmEditorPage
      realmKey="qi_refining_early"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  expect((await screen.findAllByText("编辑基础信息")).length).toBeGreaterThan(0);
  fireEvent.click((await screen.findAllByText("编辑基础信息"))[0]);

  let dialog = await screen.findByRole("dialog", { name: "基础信息" });
  fireEvent.change(within(dialog).getByLabelText("展示名称"), {
    target: { value: "炼气初期（修订）" },
  });
  fireEvent.click(within(dialog).getByText("完成编辑"));

  fireEvent.click((await screen.findAllByRole("button", { name: "编辑突破配置" }))[0]);
  dialog = await screen.findByRole("dialog", { name: "突破配置" });
  fireEvent.change(within(dialog).getByLabelText("突破所需修为"), {
    target: { value: "120" },
  });
  fireEvent.change(within(dialog).getByLabelText("突破所需灵石"), {
    target: { value: "30" },
  });
  fireEvent.click(within(dialog).getByText("完成编辑"));

  fireEvent.click(screen.getByText("保存境界"));

  await waitFor(() => {
    expect(savedRealm).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedRealm).toMatchObject({
    key: "qi_refining_early",
    display_name: "炼气初期（修订）",
    required_cultivation_exp: 120,
    required_spirit_stone: 30,
  });
});
