import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { EventListPage } from "./EventListPage";

test("filters events by type in the redesigned library", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const url = String(input);
      if (url.includes("event_type=material")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                event_id: "evt_material",
                event_name: "采集灵草",
                event_type: "material",
                risk_level: "normal",
                weight: 3,
                option_ids: ["opt_material"],
                is_repeatable: true,
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
              event_id: "evt_cultivation",
              event_name: "山中灵潮",
              event_type: "cultivation",
              risk_level: "normal",
              weight: 2,
              option_ids: ["opt_cultivation"],
              is_repeatable: true,
            },
            {
              event_id: "evt_material",
              event_name: "采集灵草",
              event_type: "material",
              risk_level: "normal",
              weight: 3,
              option_ids: ["opt_material"],
              is_repeatable: true,
            },
          ],
        }),
      };
    })
  );

  render(
    <EventListPage
      onCreateEvent={() => {}}
      onEditEvent={() => {}}
    />
  );

  expect(await screen.findByText("事件库")).toBeInTheDocument();
  expect(screen.getByText("山中灵潮")).toBeInTheDocument();
  expect(screen.getByText("事件类型")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("事件类型筛选"), {
    target: { value: "material" },
  });

  await waitFor(() => {
    expect(screen.getByText("采集灵草")).toBeInTheDocument();
    expect(screen.queryByText("山中灵潮")).not.toBeInTheDocument();
  });
});

test("shows total type weight for each event card", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [
          {
            event_id: "evt_cultivation_one",
            event_name: "山中灵潮",
            event_type: "cultivation",
            risk_level: "normal",
            weight: 2,
            option_ids: ["opt_cultivation_one"],
            is_repeatable: true,
          },
          {
            event_id: "evt_cultivation_two",
            event_name: "云海吐纳",
            event_type: "cultivation",
            risk_level: "safe",
            weight: 5,
            option_ids: ["opt_cultivation_two"],
            is_repeatable: true,
          },
          {
            event_id: "evt_material",
            event_name: "采集灵草",
            event_type: "material",
            risk_level: "normal",
            weight: 3,
            option_ids: ["opt_material"],
            is_repeatable: true,
          },
        ],
      }),
    }))
  );

  render(
    <EventListPage
      onCreateEvent={() => {}}
      onEditEvent={() => {}}
    />
  );

  expect(await screen.findByText("山中灵潮")).toBeInTheDocument();
  expect(screen.getAllByText("同类总权重 7")).toHaveLength(2);
  expect(screen.getByText("同类总权重 3")).toBeInTheDocument();
});
