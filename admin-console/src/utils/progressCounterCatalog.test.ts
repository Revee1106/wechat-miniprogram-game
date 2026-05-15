import { expect, test } from "vitest";

import {
  buildProgressCounterOptions,
  mergeProgressCounterOptions,
} from "./progressCounterCatalog";

test("builds progress counter options from template requirements and result deltas", () => {
  const options = buildProgressCounterOptions(
    {
      event_id: "evt_b",
      event_name: "B",
      event_type: "alchemy",
      outcome_type: "alchemy",
      risk_level: "normal",
      trigger_sources: ["global"],
      choice_pattern: "binary_choice",
      title_text: "",
      body_text: "",
      weight: 1,
      is_repeatable: true,
      option_ids: ["opt_b"],
      required_progress_counters: { "alchemy.old_clue": 1 },
    },
    [
      {
        option_id: "opt_b",
        option_text: "B",
        sort_order: 1,
        is_default: true,
        result_on_success: {
          progress_counter_deltas: { zhu_ji_dan_xiansuo: 1 },
        },
      },
    ]
  );

  expect(options).toEqual([
    { value: "alchemy.old_clue", label: "alchemy.old_clue" },
    { value: "zhu_ji_dan_xiansuo", label: "zhu_ji_dan_xiansuo" },
  ]);
});

test("merges global and local progress counter options without duplicates", () => {
  expect(
    mergeProgressCounterOptions(
      [
        { value: "zhu_ji_dan_xiansuo", label: "zhu_ji_dan_xiansuo" },
        { value: "alchemy.old_clue", label: "alchemy.old_clue" },
      ],
      [
        { value: "zhu_ji_dan_xiansuo", label: "zhu_ji_dan_xiansuo" },
        { value: "alchemy.local_clue", label: "alchemy.local_clue" },
      ]
    )
  ).toEqual([
    { value: "alchemy.local_clue", label: "alchemy.local_clue" },
    { value: "alchemy.old_clue", label: "alchemy.old_clue" },
    { value: "zhu_ji_dan_xiansuo", label: "zhu_ji_dan_xiansuo" },
  ]);
});
