import { normalizeResourceRecord } from "./resourceCatalog";

export function parseLineList(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function formatLineList(values?: string[]): string {
  return (values ?? []).join("\n");
}

export function parseNumberInput(value: string, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function parseOptionalNumber(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function parseKeyValueMap(value: string): Record<string, number> {
  const entries = value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const payload: Record<string, number> = {};
  for (const entry of entries) {
    const [key, rawValue] = entry.split(":");
    if (!key || rawValue === undefined) {
      continue;
    }
    const trimmedKey = key.trim();
    const trimmedValue = Number(rawValue.trim());
    if (!trimmedKey || !Number.isFinite(trimmedValue)) {
      continue;
    }
    payload[trimmedKey] = trimmedValue;
  }
  return payload;
}

export function formatKeyValueMap(values?: Record<string, number>): string {
  return Object.entries(values ?? {})
    .map(([key, value]) => `${key}:${value}`)
    .join("\n");
}

export function parseStructuredPayload(value: string): Record<string, unknown> | string {
  const normalized = value.trim();
  if (!normalized) {
    return "";
  }
  if (normalized.startsWith("{") || normalized.startsWith("[")) {
    return JSON.parse(normalized) as Record<string, unknown>;
  }
  return normalized;
}

export function formatStructuredPayload(value: Record<string, unknown> | string | undefined): string {
  if (!value) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

export type PayloadEditorState = {
  resources: Record<string, number>;
  cultivation_exp: number;
  lifespan_delta: number;
  hp_delta: number;
  breakthrough_bonus: number;
  technique_exp: number;
  luck_delta: number;
  karma_delta: number;
  rebirth_progress_delta: number;
  statuses_add: string[];
  statuses_remove: string[];
  techniques_add: string[];
  equipment_add: string[];
  equipment_remove: string[];
  death: boolean;
};

export function parsePayloadEditorState(
  value: Record<string, unknown> | string | undefined
): PayloadEditorState {
  const payload =
    typeof value === "string" ? parseLegacyPayload(value) : (value ?? {});
  const character =
    typeof payload.character === "object" && payload.character
      ? (payload.character as Record<string, number>)
      : {};

  return {
    resources:
      typeof payload.resources === "object" && payload.resources
        ? normalizeResourceRecord(payload.resources as Record<string, number>)
        : {},
    cultivation_exp: Number(character.cultivation_exp ?? 0),
    lifespan_delta: Number(character.lifespan_delta ?? 0),
    hp_delta: Number(character.hp_delta ?? 0),
    breakthrough_bonus: Number(character.breakthrough_bonus ?? 0),
    technique_exp: Number(character.technique_exp ?? 0),
    luck_delta: Number(character.luck_delta ?? 0),
    karma_delta: Number(character.karma_delta ?? 0),
    rebirth_progress_delta: Number(payload.rebirth_progress_delta ?? 0),
    statuses_add: Array.isArray(payload.statuses_add) ? payload.statuses_add as string[] : [],
    statuses_remove: Array.isArray(payload.statuses_remove) ? payload.statuses_remove as string[] : [],
    techniques_add: Array.isArray(payload.techniques_add) ? payload.techniques_add as string[] : [],
    equipment_add: Array.isArray(payload.equipment_add) ? payload.equipment_add as string[] : [],
    equipment_remove: Array.isArray(payload.equipment_remove) ? payload.equipment_remove as string[] : [],
    death: Boolean(payload.death),
  };
}

export function buildPayloadFromEditorState(
  state: PayloadEditorState
): Record<string, unknown> {
  const character: Record<string, number> = {};
  if (state.cultivation_exp !== 0) {
    character.cultivation_exp = state.cultivation_exp;
  }
  if (state.lifespan_delta !== 0) {
    character.lifespan_delta = state.lifespan_delta;
  }
  if (state.hp_delta !== 0) {
    character.hp_delta = state.hp_delta;
  }
  if (state.breakthrough_bonus !== 0) {
    character.breakthrough_bonus = state.breakthrough_bonus;
  }
  if (state.technique_exp !== 0) {
    character.technique_exp = state.technique_exp;
  }
  if (state.luck_delta !== 0) {
    character.luck_delta = state.luck_delta;
  }
  if (state.karma_delta !== 0) {
    character.karma_delta = state.karma_delta;
  }

  const payload: Record<string, unknown> = {};
  if (Object.keys(state.resources).length > 0) {
    const normalizedResources = normalizeResourceRecord(state.resources);
    if (Object.keys(normalizedResources).length > 0) {
      payload.resources = normalizedResources;
    }
  }
  if (Object.keys(character).length > 0) {
    payload.character = character;
  }
  if (state.statuses_add.length > 0) {
    payload.statuses_add = state.statuses_add;
  }
  if (state.statuses_remove.length > 0) {
    payload.statuses_remove = state.statuses_remove;
  }
  if (state.techniques_add.length > 0) {
    payload.techniques_add = state.techniques_add;
  }
  if (state.equipment_add.length > 0) {
    payload.equipment_add = state.equipment_add;
  }
  if (state.equipment_remove.length > 0) {
    payload.equipment_remove = state.equipment_remove;
  }
  if (state.rebirth_progress_delta !== 0) {
    payload.rebirth_progress_delta = state.rebirth_progress_delta;
  }
  if (state.death) {
    payload.death = true;
  }
  return payload;
}

function parseLegacyPayload(value: string): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    resources: {},
    character: {},
  };
  const resources = payload.resources as Record<string, number>;
  const character = payload.character as Record<string, number>;

  for (const token of value.split(",")) {
    const [rawKey, rawAmount] = token.split(":");
    if (!rawKey || rawAmount === undefined) {
      continue;
    }
    const key = rawKey.trim();
    const amount = rawAmount.trim();
    if (key === "death") {
      payload.death = amount.toLowerCase() === "true";
      continue;
    }
    const numericAmount = Number(amount);
    if (!Number.isFinite(numericAmount)) {
      continue;
    }
    if (key === "cultivation_exp") {
      character.cultivation_exp = (character.cultivation_exp ?? 0) + numericAmount;
      continue;
    }
    if (key === "lifespan") {
      character.lifespan_delta = (character.lifespan_delta ?? 0) + numericAmount;
      continue;
    }
    if (key === "herbs") {
      resources.herb = (resources.herb ?? 0) + numericAmount;
      continue;
    }
    if (key === "iron_essence") {
      resources.ore = (resources.ore ?? 0) + numericAmount;
      continue;
    }
    resources[key] = (resources[key] ?? 0) + numericAmount;
  }
  return payload;
}
