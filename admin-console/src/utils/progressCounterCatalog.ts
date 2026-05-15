import type { EventOptionInput, EventTemplateInput } from "../api/client";
import { parsePayloadEditorState } from "./eventFormCodec";
import type { ResourceOption } from "./resourceCatalog";

export function buildProgressCounterOptions(
  template: EventTemplateInput | null | undefined,
  options: EventOptionInput[] = []
): ResourceOption[] {
  const keys = new Set<string>();

  Object.keys(template?.required_progress_counters ?? {}).forEach((key) => addKey(keys, key));

  for (const option of options) {
    collectPayloadProgressKeys(keys, option.result_on_success);
    collectPayloadProgressKeys(keys, option.result_on_failure);
  }

  return Array.from(keys)
    .sort((left, right) => left.localeCompare(right))
    .map((key) => ({ value: key, label: key }));
}

export function mergeProgressCounterOptions(
  globalOptions: ResourceOption[],
  localOptions: ResourceOption[]
): ResourceOption[] {
  const merged = new Map<string, ResourceOption>();
  for (const option of [...globalOptions, ...localOptions]) {
    const value = String(option?.value ?? "").trim();
    if (!value || merged.has(value)) {
      continue;
    }
    merged.set(value, { value, label: option?.label || value });
  }
  return Array.from(merged.values()).sort((left, right) =>
    left.value.localeCompare(right.value)
  );
}

function collectPayloadProgressKeys(
  keys: Set<string>,
  payload: EventOptionInput["result_on_success"]
) {
  const state = parsePayloadEditorState(payload);
  Object.keys(state.progress_counter_deltas).forEach((key) => addKey(keys, key));
}

function addKey(keys: Set<string>, key: string) {
  const normalized = key.trim();
  if (normalized) {
    keys.add(normalized);
  }
}
