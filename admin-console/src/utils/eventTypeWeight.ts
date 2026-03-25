import type { EventListItem, EventTemplateInput } from "../api/client";

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

  return currentType ? totals[currentType] ?? currentWeight : currentWeight;
}
