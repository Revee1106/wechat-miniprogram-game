import type { EventListItem, EventTemplateInput } from "../api/client";

export type EventDrawChanceEstimate = {
  currentWeight: number;
  typeTotalWeight: number;
  allTotalWeight: number;
  typeChance: number;
  withinTypeChance: number;
  finalChance: number;
};

function normalizeWeight(value: number | undefined): number {
  const parsed = Number(value ?? 0);
  return parsed > 0 ? parsed : 1;
}

export function buildEventTypeWeightMap(items: EventListItem[] | undefined): Record<string, number> {
  return (items ?? []).reduce<Record<string, number>>((totals, item) => {
    const eventType = item.event_type || "";
    if (!eventType) {
      return totals;
    }
    totals[eventType] = (totals[eventType] ?? 0) + normalizeWeight(item.weight);
    return totals;
  }, {});
}

export function getEventTypeTotalWeight(
  items: EventListItem[] | undefined,
  template: Pick<EventTemplateInput, "event_id" | "event_type" | "weight">
): number {
  return buildEventDrawChanceEstimate(items, template).typeTotalWeight;
}

export function buildEventDrawChanceEstimate(
  items: EventListItem[] | undefined,
  template: Pick<EventTemplateInput, "event_id" | "event_type" | "weight">
): EventDrawChanceEstimate {
  const safeItems = items ?? [];
  const totals = buildEventTypeWeightMap(safeItems);
  const currentWeight = normalizeWeight(template.weight);
  const currentType = template.event_type || "";
  const existing = safeItems.find((item) => item.event_id === template.event_id);

  if (existing) {
    const existingType = existing.event_type || "";
    if (existingType) {
      totals[existingType] = Math.max(
        0,
        (totals[existingType] ?? 0) - normalizeWeight(existing.weight)
      );
    }
  }

  if (currentType) {
    totals[currentType] = (totals[currentType] ?? 0) + currentWeight;
  }

  const typeTotalWeight = currentType ? totals[currentType] ?? currentWeight : currentWeight;
  const allTotalWeight = Object.values(totals).reduce((sum, weight) => sum + weight, 0);
  const typeChance = allTotalWeight > 0 ? typeTotalWeight / allTotalWeight : 0;
  const withinTypeChance = typeTotalWeight > 0 ? currentWeight / typeTotalWeight : 0;

  return {
    currentWeight,
    typeTotalWeight,
    allTotalWeight,
    typeChance,
    withinTypeChance,
    finalChance: typeChance * withinTypeChance,
  };
}

export function formatChance(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return "0%";
  }
  const percentage = value * 100;
  if (percentage < 0.01) {
    return "<0.01%";
  }
  if (percentage < 1) {
    return `${percentage.toFixed(2)}%`;
  }
  if (percentage < 10) {
    return `${percentage.toFixed(1)}%`;
  }
  return `${Math.round(percentage)}%`;
}
