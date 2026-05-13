export type ResourceOption = {
  value: string;
  label: string;
};

export const resourceOptions: ResourceOption[] = [
  { value: "spirit_stone", label: "灵石" },
  { value: "herb", label: "药草" },
  { value: "ore", label: "玄铁精华" },
  { value: "beast_material", label: "妖兽材料" },
  { value: "pill", label: "丹药" },
  { value: "craft_material", label: "炼器材料" },
];

const resourceAliasMap: Record<string, string> = {
  spirit_stone: "spirit_stone",
  herbs: "herb",
  herb: "herb",
  basic_herb: "basic_herb",
  iron_essence: "ore",
  ore: "ore",
  basic_ore: "basic_ore",
  beast_material: "beast_material",
  pill: "pill",
  craft_material: "craft_material",
  spirit_spring_water: "spirit_spring_water",
};

const resourceOrder = resourceOptions.reduce<Record<string, number>>((map, option, index) => {
  map[option.value] = index;
  return map;
}, {});

export function buildConfiguredResourceOptions(
  materials: Array<{ material_id: string; display_name?: string }>
): ResourceOption[] {
  const seen = new Set<string>();
  return materials
    .map((item) => ({
      value: String(item.material_id ?? "").trim(),
      label: String(item.display_name || item.material_id || "").trim(),
    }))
    .filter((item) => {
      if (!item.value || seen.has(item.value)) {
        return false;
      }
      seen.add(item.value);
      return true;
    })
    .map((item) => ({
      value: item.value,
      label: item.label || item.value,
    }));
}

export function normalizeResourceKey(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  return resourceAliasMap[trimmed] ?? trimmed;
}

export function normalizeResourceRecord(
  values?: Record<string, number>
): Record<string, number> {
  const normalized: Record<string, number> = {};
  for (const [rawKey, rawAmount] of Object.entries(values ?? {})) {
    const key = normalizeResourceKey(rawKey);
    const amount = Number(rawAmount);
    if (!key || !Number.isFinite(amount)) {
      continue;
    }
    normalized[key] = (normalized[key] ?? 0) + amount;
  }
  return sortResourceRecord(normalized);
}

export function sortResourceRecord(values: Record<string, number>): Record<string, number> {
  return Object.fromEntries(
    Object.entries(values).sort(([left], [right]) => {
      const leftOrder = resourceOrder[left] ?? Number.MAX_SAFE_INTEGER;
      const rightOrder = resourceOrder[right] ?? Number.MAX_SAFE_INTEGER;
      return leftOrder - rightOrder || left.localeCompare(right);
    })
  );
}
