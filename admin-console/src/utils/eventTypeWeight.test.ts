import { expect, test } from "vitest";

import { buildEventDrawChanceEstimate, formatChance } from "./eventTypeWeight";

test("estimates event draw chance from type and event weights", () => {
  const estimate = buildEventDrawChanceEstimate(
    [
      {
        event_id: "evt_cultivation",
        event_name: "Cultivation",
        event_type: "cultivation",
        outcome_type: "cultivation",
        risk_level: "normal",
        trigger_sources: ["global"],
        region: "",
        realm_min: null,
        realm_max: null,
        option_ids: [],
        is_repeatable: true,
        weight: 2,
      },
      {
        event_id: "evt_material_light",
        event_name: "Material Light",
        event_type: "material",
        outcome_type: "material",
        risk_level: "normal",
        trigger_sources: ["global"],
        region: "",
        realm_min: null,
        realm_max: null,
        option_ids: [],
        is_repeatable: true,
        weight: 1,
      },
      {
        event_id: "evt_material_heavy",
        event_name: "Material Heavy",
        event_type: "material",
        outcome_type: "material",
        risk_level: "normal",
        trigger_sources: ["global"],
        region: "",
        realm_min: null,
        realm_max: null,
        option_ids: [],
        is_repeatable: true,
        weight: 7,
      },
    ],
    {
      event_id: "evt_material_heavy",
      event_type: "material",
      weight: 7,
    }
  );

  expect(estimate.currentWeight).toBe(7);
  expect(estimate.typeTotalWeight).toBe(8);
  expect(estimate.allTotalWeight).toBe(10);
  expect(estimate.typeChance).toBeCloseTo(0.8);
  expect(estimate.withinTypeChance).toBeCloseTo(0.875);
  expect(estimate.finalChance).toBeCloseTo(0.7);
  expect(formatChance(estimate.finalChance)).toBe("70%");
});
