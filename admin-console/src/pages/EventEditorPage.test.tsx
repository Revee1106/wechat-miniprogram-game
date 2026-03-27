import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EventEditorPage } from "./EventEditorPage";

test("opens trigger rule editor inside a secondary panel", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        template: {},
        options: [],
      }),
    }))
  );

  render(
    <EventEditorPage
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  expect(await screen.findByText("编辑基础信息")).toBeInTheDocument();
  fireEvent.click(screen.getByText("编辑触发规则"));

  const dialog = await screen.findByRole("dialog", { name: "触发规则" });
  expect(within(dialog).getByLabelText("地域限定")).toBeInTheDocument();
});

test("supports selecting multiple trigger sources", async () => {
  let savedTemplate: Record<string, unknown> | null = null;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/events/evt_existing") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_existing",
              event_name: "Existing Event",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Existing Event",
              body_text: "Body",
              weight: 1,
              is_repeatable: true,
              option_ids: ["opt_existing"],
            },
            options: [
              {
                option_id: "opt_existing",
                event_id: "evt_existing",
                option_text: "Absorb",
                sort_order: 1,
                is_default: true,
              },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/events/evt_existing") && init?.method === "PUT") {
        savedTemplate = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedTemplate,
        };
      }
      if (url.endsWith("/admin/api/options/opt_existing") && init?.method === "PUT") {
        return {
          ok: true,
          json: async () => JSON.parse(String(init.body)),
        };
      }
      return {
        ok: true,
        json: async () => ({ items: [] }),
      };
    })
  );

  render(
    <EventEditorPage
      eventId="evt_existing"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  fireEvent.click(await screen.findByText("编辑触发规则"));
  const dialog = await screen.findByRole("dialog", { name: "触发规则" });
  fireEvent.click(within(dialog).getByRole("button", { name: "地域触发" }));
  fireEvent.click(within(dialog).getByRole("button", { name: "气运触发" }));
  fireEvent.click(within(dialog).getByText("完成编辑"));

  fireEvent.click(screen.getByText("保存事件"));

  await waitFor(() => {
    expect(savedTemplate).not.toBeNull();
  });

  expect(savedTemplate).toMatchObject({
    trigger_sources: ["global", "region_based", "luck_based"],
  });
});

test("adds a new option from the option panel", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        template: {},
        options: [],
      }),
    }))
  );

  render(
    <EventEditorPage
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  fireEvent.click(await screen.findByText("编辑选项编排"));
  const dialog = await screen.findByRole("dialog", { name: "选项编排" });

  expect(within(dialog).getAllByLabelText("选项文案")).toHaveLength(1);
  fireEvent.click(within(dialog).getByText("新增选项"));
  expect(within(dialog).getAllByLabelText("选项文案")).toHaveLength(2);
});

test("single outcome events use a default result editor instead of option orchestration", async () => {
  let savedTemplate: Record<string, unknown> | null = null;
  let savedOption: Record<string, unknown> | null = null;
  let reloaded = false;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/events/evt_single") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_single",
              event_name: "Single Event",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "single_outcome",
              title_text: "Single Event",
              body_text: "Body",
              weight: 1,
              is_repeatable: true,
              option_ids: ["opt_single"],
            },
            options: [
              {
                option_id: "opt_single",
                event_id: "evt_single",
                option_text: "Old text",
                sort_order: 1,
                is_default: false,
                result_on_success: {},
              },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/events/evt_single") && init?.method === "PUT") {
        savedTemplate = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedTemplate,
        };
      }
      if (url.endsWith("/admin/api/options/opt_single") && init?.method === "PUT") {
        savedOption = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedOption,
        };
      }
      if (url.endsWith("/admin/api/events/reload") && init?.method === "POST") {
        reloaded = true;
        return {
          ok: true,
          json: async () => ({
            reloaded: true,
            template_count: 1,
            option_count: 1,
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
    <EventEditorPage
      eventId="evt_single"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  expect(await screen.findByText("编辑单一结果")).toBeInTheDocument();
  expect(screen.queryByText("编辑选项编排")).not.toBeInTheDocument();

  fireEvent.click(screen.getByText("编辑单一结果"));
  const dialog = await screen.findByRole("dialog", { name: "单一结果" });
  fireEvent.change(within(dialog).getByLabelText("结果日志"), {
    target: { value: "榛樿缁撶畻" },
  });
  fireEvent.click(within(dialog).getByRole("button", { name: "新增资源变化" }));
  fireEvent.change(within(dialog).getByLabelText("结果资源数值-1"), {
    target: { value: "5" },
  });
  fireEvent.click(screen.getByText("保存事件"));

  await waitFor(() => {
    expect(savedTemplate).not.toBeNull();
    expect(savedOption).not.toBeNull();
    expect(reloaded).toBe(true);
  });

  expect(savedTemplate).toMatchObject({
    choice_pattern: "single_outcome",
  });
  expect(savedOption).toMatchObject({
    option_id: "opt_single",
    option_text: "完成事件",
    sort_order: 1,
    is_default: true,
    log_text_success: "榛樿缁撶畻",
    result_on_success: {
      resources: { spirit_stone: 5 },
    },
  });
});

test("switching to single outcome clears hidden legacy rewards until they are explicitly reconfigured", async () => {
  let savedTemplate: Record<string, unknown> | null = null;
  let savedOption: Record<string, unknown> | null = null;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/events/evt_convert") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_convert",
              event_name: "Convert Event",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Convert Event",
              body_text: "Body",
              weight: 1,
              is_repeatable: true,
              option_ids: ["opt_convert"],
            },
            options: [
              {
                option_id: "opt_convert",
                event_id: "evt_convert",
                option_text: "Legacy option",
                sort_order: 1,
                is_default: true,
                result_on_success: {
                  resources: { spirit_stone: 1 },
                },
              },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/events/evt_convert") && init?.method === "PUT") {
        savedTemplate = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedTemplate,
        };
      }
      if (url.endsWith("/admin/api/options/opt_convert") && init?.method === "PUT") {
        savedOption = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedOption,
        };
      }
      if (url.endsWith("/admin/api/events/reload") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({
            reloaded: true,
            template_count: 1,
            option_count: 1,
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
    <EventEditorPage
      eventId="evt_convert"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  fireEvent.click(await screen.findByText("编辑触发规则"));
  let dialog = await screen.findByRole("dialog", { name: "触发规则" });
  fireEvent.change(within(dialog).getByLabelText("选项模式"), {
    target: { value: "single_outcome" },
  });
  fireEvent.click(within(dialog).getByText("完成编辑"));

  expect(await screen.findByText("编辑单一结果")).toBeInTheDocument();
  fireEvent.click(screen.getByText("编辑单一结果"));
  dialog = await screen.findByRole("dialog", { name: "单一结果" });
  fireEvent.change(within(dialog).getByLabelText("结果修为变化"), {
    target: { value: "5" },
  });

  fireEvent.click(screen.getByText("保存事件"));

  await waitFor(() => {
    expect(savedTemplate).not.toBeNull();
    expect(savedOption).not.toBeNull();
  });

  expect(savedTemplate).toMatchObject({
    choice_pattern: "single_outcome",
  });
  expect(savedOption).toMatchObject({
    option_id: "opt_convert",
    option_text: "完成事件",
    result_on_success: {
      character: { cultivation_exp: 5 },
    },
  });
  expect(savedOption?.result_on_success).not.toHaveProperty("resources");
});

test("saves advanced template and option fields through section panels", async () => {
  let savedTemplate: Record<string, unknown> | null = null;
  let savedOption: Record<string, unknown> | null = null;

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/admin/api/events/evt_existing") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_existing",
              event_name: "Existing Event",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Existing Event",
              body_text: "Body",
              weight: 1,
              is_repeatable: true,
              option_ids: ["opt_existing"],
            },
            options: [
              {
                option_id: "opt_existing",
                event_id: "evt_existing",
                option_text: "Absorb",
                sort_order: 1,
                is_default: true,
              },
            ],
          }),
        };
      }
      if (url.endsWith("/admin/api/events/evt_existing") && init?.method === "PUT") {
        savedTemplate = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedTemplate,
        };
      }
      if (url.endsWith("/admin/api/options/opt_existing") && init?.method === "PUT") {
        savedOption = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => savedOption,
        };
      }
      return {
        ok: true,
        json: async () => ({ items: [] }),
      };
    })
  );

  render(
    <EventEditorPage
      eventId="evt_existing"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  fireEvent.click(await screen.findByText("编辑触发规则"));
  let dialog = await screen.findByRole("dialog", { name: "触发规则" });
  fireEvent.change(within(dialog).getByLabelText("地域限定"), {
    target: { value: "starter-valley" },
  });
  fireEvent.change(within(dialog).getByLabelText("冷却回合"), {
    target: { value: "4" },
  });
  fireEvent.click(within(dialog).getByText("完成编辑"));

  fireEvent.click(screen.getByText("编辑前置条件"));
  dialog = await screen.findByRole("dialog", { name: "前置条件" });
  fireEvent.change(within(dialog).getByLabelText("所需资源"), {
    target: { value: "spirit_stone:3\nherb:2" },
  });
  fireEvent.change(within(dialog).getByLabelText("需要状态"), {
    target: { value: "blessed\nfocused" },
  });
  fireEvent.change(within(dialog).getByLabelText("最低因果"), {
    target: { value: "5" },
  });
  fireEvent.click(within(dialog).getByText("完成编辑"));

  fireEvent.click(screen.getByText("编辑选项编排"));
  dialog = await screen.findByRole("dialog", { name: "选项编排" });
  fireEvent.change(within(dialog).getByLabelText("选项需要状态"), {
    target: { value: "injured" },
  });
  fireEvent.change(within(dialog).getByLabelText("成功率公式"), {
    target: { value: "base_success_rate + 0.1" },
  });
  fireEvent.change(within(dialog).getByLabelText("后续事件"), {
    target: { value: "evt_follow_up" },
  });
  fireEvent.click(within(dialog).getAllByRole("button", { name: "新增资源变化" })[0]);
  fireEvent.change(within(dialog).getByLabelText("成功资源数值-1"), {
    target: { value: "2" },
  });
  fireEvent.change(within(dialog).getByLabelText("成功修为变化"), {
    target: { value: "6" },
  });
  fireEvent.change(within(dialog).getByLabelText("成功日志"), {
    target: { value: "Good result" },
  });
  fireEvent.click(within(dialog).getByText("完成编辑"));

  fireEvent.click(screen.getByText("保存事件"));

  await waitFor(() => {
    expect(savedTemplate).not.toBeNull();
    expect(savedOption).not.toBeNull();
  });

  expect(savedTemplate).toMatchObject({
    region: "starter-valley",
    cooldown_rounds: 4,
    required_resources: { spirit_stone: 3, herb: 2 },
    required_statuses: ["blessed", "focused"],
    required_karma_min: 5,
  });
  expect(savedOption).toMatchObject({
    requires_statuses: ["injured"],
    success_rate_formula: "base_success_rate + 0.1",
    next_event_id: "evt_follow_up",
    result_on_success: {
      resources: { spirit_stone: 2 },
      character: { cultivation_exp: 6 },
    },
    log_text_success: "Good result",
  });
});

test("shows current event type total weight in the workbench header", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/admin/api/events/evt_existing") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            template: {
              event_id: "evt_existing",
              event_name: "Existing Event",
              event_type: "cultivation",
              outcome_type: "cultivation",
              risk_level: "normal",
              trigger_sources: ["global"],
              choice_pattern: "binary_choice",
              title_text: "Existing Event",
              body_text: "Body",
              weight: 5,
              is_repeatable: true,
              option_ids: ["opt_existing"],
            },
            options: [
              {
                option_id: "opt_existing",
                event_id: "evt_existing",
                option_text: "Absorb",
                sort_order: 1,
                is_default: true,
              },
            ],
          }),
        };
      }
      if (url.includes("/admin/api/events") && !init?.method) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                event_id: "evt_existing",
                event_name: "Existing Event",
                event_type: "cultivation",
                risk_level: "normal",
                weight: 5,
                option_ids: ["opt_existing"],
                is_repeatable: true,
              },
              {
                event_id: "evt_other_cultivation",
                event_name: "Other Event",
                event_type: "cultivation",
                risk_level: "safe",
                weight: 3,
                option_ids: ["opt_other_cultivation"],
                is_repeatable: true,
              },
              {
                event_id: "evt_material",
                event_name: "Material Event",
                event_type: "material",
                risk_level: "normal",
                weight: 9,
                option_ids: ["opt_material"],
                is_repeatable: true,
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

  render(
    <EventEditorPage
      eventId="evt_existing"
      onBack={() => {}}
      onSaved={() => {}}
    />
  );

  expect(await screen.findByText("同类总权重 8")).toBeInTheDocument();
});


