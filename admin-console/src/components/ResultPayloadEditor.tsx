import { useEffect, useMemo, useState } from "react";

import {
  buildPayloadFromEditorState,
  formatLineList,
  parseLineList,
  parseNumberInput,
  parsePayloadEditorState,
  type PayloadEditorState,
} from "../utils/eventFormCodec";
import {
  resourceOptions as defaultResourceOptions,
  sortResourceRecord,
  type ResourceOption,
} from "../utils/resourceCatalog";

type ResultPayloadEditorProps = {
  labelPrefix: string;
  payload: Record<string, unknown> | string | undefined;
  onChange: (value: Record<string, unknown>) => void;
  resourceOptions?: ResourceOption[];
  alchemyRecipeOptions?: ResourceOption[];
};

type ScalarFieldKey =
  | "cultivation_exp"
  | "lifespan_delta"
  | "hp_delta"
  | "breakthrough_bonus"
  | "technique_exp"
  | "luck_delta"
  | "karma_delta"
  | "alchemy_mastery_exp_delta"
  | "rebirth_progress_delta";

type ListFieldKey =
  | "statuses_add"
  | "statuses_remove"
  | "techniques_add"
  | "learned_alchemy_recipe_ids"
  | "unlocked_material_ids"
  | "equipment_add"
  | "equipment_remove";

type ChangeCatalogItem =
  | {
      id: string;
      label: string;
      type: "resource";
      resourceKey: string;
    }
  | {
      id: string;
      label: string;
      type: "scalar";
      stateKey: ScalarFieldKey;
    };

type ExtraFieldDefinition =
  | {
      key: ListFieldKey;
      type: "list";
      label: string;
      placeholder: string;
      emptyValue: string[];
    }
  | {
      key: "death";
      type: "boolean";
      label: string;
      hint: string;
      emptyValue: boolean;
    };

type ChangeEntry = {
  id: string;
  amount: number;
};

const scalarFieldDefinitions: Array<{ key: ScalarFieldKey; label: string }> = [
  { key: "cultivation_exp", label: "修为变化" },
  { key: "lifespan_delta", label: "寿元变化" },
  { key: "hp_delta", label: "气血变化" },
  { key: "breakthrough_bonus", label: "突破加成" },
  { key: "technique_exp", label: "功法经验" },
  { key: "luck_delta", label: "气运变化" },
  { key: "karma_delta", label: "因果变化" },
  { key: "alchemy_mastery_exp_delta", label: "炼丹熟练度" },
  { key: "rebirth_progress_delta", label: "转生进度" },
];

const extraFieldDefinitions: ExtraFieldDefinition[] = [
  {
    key: "statuses_add",
    type: "list",
    label: "增加状态",
    placeholder: "每行一个状态",
    emptyValue: [],
  },
  {
    key: "statuses_remove",
    type: "list",
    label: "移除状态",
    placeholder: "每行一个状态",
    emptyValue: [],
  },
  {
    key: "techniques_add",
    type: "list",
    label: "获得功法",
    placeholder: "每行一个功法",
    emptyValue: [],
  },
  {
    key: "learned_alchemy_recipe_ids",
    type: "list",
    label: "学会丹方",
    placeholder: "选择要学习的丹方",
    emptyValue: [],
  },
  {
    key: "unlocked_material_ids",
    type: "list",
    label: "解锁材料",
    placeholder: "选择要解锁的材料",
    emptyValue: [],
  },
  {
    key: "equipment_add",
    type: "list",
    label: "获得装备标签",
    placeholder: "每行一个装备标签",
    emptyValue: [],
  },
  {
    key: "equipment_remove",
    type: "list",
    label: "移除装备标签",
    placeholder: "每行一个装备标签",
    emptyValue: [],
  },
  {
    key: "death",
    type: "boolean",
    label: "导致死亡",
    hint: "只在需要直接终结角色时开启。",
    emptyValue: false,
  },
];

export function ResultPayloadEditor({
  labelPrefix,
  payload,
  onChange,
  resourceOptions = defaultResourceOptions,
  alchemyRecipeOptions = [],
}: ResultPayloadEditorProps) {
  const state = parsePayloadEditorState(payload);
  const changeCatalog = useMemo(() => buildChangeCatalog(resourceOptions), [resourceOptions]);
  const scalarCatalog = changeCatalog.filter((item) => item.type === "scalar");
  const resourceCatalog = changeCatalog.filter((item) => item.type === "resource");
  const changeCatalogById = Object.fromEntries(
    changeCatalog.map((item) => [item.id, item])
  ) as Record<string, ChangeCatalogItem>;
  const changeEntries = buildChangeEntries(state);
  const usedChangeIds = changeEntries.map((entry) => entry.id);
  const indexedChangeEntries = changeEntries.map((entry, index) => ({ entry, index }));
  const scalarEntries = indexedChangeEntries.filter(
    ({ entry }) => changeCatalogById[entry.id]?.type === "scalar"
  );
  const resourceEntries = indexedChangeEntries.filter(
    ({ entry }) => changeCatalogById[entry.id]?.type === "resource"
  );
  const usedChangeIdSet = new Set(usedChangeIds);
  const [activeExtraKeys, setActiveExtraKeys] = useState<string[]>([]);
  const activeExtraFields = extraFieldDefinitions.filter((field) =>
    isExtraFieldVisible(state, field, activeExtraKeys)
  );
  const addableExtraFields = extraFieldDefinitions.filter(
    (field) => !isExtraFieldVisible(state, field, activeExtraKeys)
  );
  const [draftAmounts, setDraftAmounts] = useState<Record<string, string>>({});
  const changeEntriesSignature = changeEntries
    .map((entry) => `${entry.id}:${entry.amount}`)
    .join("|");

  useEffect(() => {
    setDraftAmounts(
      Object.fromEntries(
        changeEntries.map((entry, index) => [buildEntryKey(entry, index), String(entry.amount)])
      )
    );
  }, [payload, changeEntries.length, changeEntriesSignature]);

  function update(partial: Partial<PayloadEditorState>) {
    onChange(
      buildPayloadFromEditorState({
        ...state,
        ...partial,
      })
    );
  }

  function updateChangeEntries(entries: ChangeEntry[]) {
    const nextResources: Record<string, number> = {};
    const nextScalarState = Object.fromEntries(
      scalarFieldDefinitions.map((field) => [field.key, 0])
    ) as Pick<PayloadEditorState, ScalarFieldKey>;

    for (const entry of entries) {
      const catalogItem = changeCatalogById[entry.id];
      if (!catalogItem || !Number.isFinite(entry.amount) || entry.amount === 0) {
        continue;
      }
      if (catalogItem.type === "resource") {
        nextResources[catalogItem.resourceKey] = entry.amount;
        continue;
      }
      nextScalarState[catalogItem.stateKey] = entry.amount;
    }

    update({
      resources: sortResourceRecord(nextResources),
      ...nextScalarState,
    });
  }

  function handleAddChange(changeId: string) {
    if (!changeId || usedChangeIds.includes(changeId)) {
      return;
    }
    updateChangeEntries([...changeEntries, { id: changeId, amount: 1 }]);
  }

  function handleChangeType(index: number, nextId: string) {
    updateChangeEntries(
      changeEntries.map((entry, entryIndex) =>
        entryIndex === index ? { ...entry, id: nextId } : entry
      )
    );
  }

  function handleChangeAmount(index: number, nextAmount: string) {
    const entry = changeEntries[index];
    if (!entry) {
      return;
    }
    const entryKey = buildEntryKey(entry, index);
    setDraftAmounts((current) => ({
      ...current,
      [entryKey]: nextAmount,
    }));

    if (!/^-?\d+$/.test(nextAmount.trim())) {
      return;
    }

    updateChangeEntries(
      changeEntries.map((currentEntry, entryIndex) =>
        entryIndex === index
          ? { ...currentEntry, amount: parseNumberInput(nextAmount, 0) }
          : currentEntry
      )
    );
  }

  function handleAmountBlur(index: number) {
    const entry = changeEntries[index];
    if (!entry) {
      return;
    }
    const entryKey = buildEntryKey(entry, index);
    setDraftAmounts((current) => ({
      ...current,
      [entryKey]: String(entry.amount),
    }));
  }

  function handleRemoveChange(index: number) {
    updateChangeEntries(changeEntries.filter((_, entryIndex) => entryIndex !== index));
  }

  function handleActivateExtra(fieldKey: string) {
    const definition = extraFieldDefinitions.find((field) => field.key === fieldKey);
    if (!definition) {
      return;
    }
    setActiveExtraKeys((current) =>
      current.includes(definition.key) ? current : [...current, definition.key]
    );
    if (definition.type === "boolean") {
      update({ death: true });
      return;
    }
    update({ [definition.key]: [] } as Partial<PayloadEditorState>);
  }

  function handleResetExtra(field: ExtraFieldDefinition) {
    setActiveExtraKeys((current) => current.filter((key) => key !== field.key));
    update({ [field.key]: field.emptyValue } as Partial<PayloadEditorState>);
  }

  return (
    <div className="result-payload-editor">
      <section className="result-payload-editor__resource-panel">
        <div className="result-payload-editor__resource-header">
          <div className="result-payload-editor__resource-title">
            <h3>{labelPrefix}变化</h3>
            <p>数值、物品和附加变化分开维护。正数表示获得，负数表示消耗。</p>
          </div>
          <div className="result-payload-editor__actions">
            <label className="field result-payload-editor__resource-action">
              <span className="sr-only">新增数值变化</span>
              <select
                aria-label={`${labelPrefix}新增数值变化`}
                defaultValue=""
                onChange={(event) => {
                  handleAddChange(event.target.value);
                  event.target.value = "";
                }}
              >
                <option value="">新增数值变化</option>
                {scalarCatalog.map((item) => (
                  <option key={item.id} disabled={usedChangeIdSet.has(item.id)} value={item.id}>
                    {usedChangeIdSet.has(item.id) ? `${item.label}（已添加）` : item.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field result-payload-editor__resource-action">
              <span className="sr-only">新增物品变化</span>
              <select
                aria-label={`${labelPrefix}新增物品变化`}
                defaultValue=""
                onChange={(event) => {
                  handleAddChange(event.target.value);
                  event.target.value = "";
                }}
              >
                <option value="">新增物品变化</option>
                {resourceCatalog.map((item) => (
                  <option key={item.id} disabled={usedChangeIdSet.has(item.id)} value={item.id}>
                    {usedChangeIdSet.has(item.id) ? `${item.label}（已添加）` : item.label}
                  </option>
                ))}
              </select>
            </label>

            {addableExtraFields.length > 0 ? (
              <label className="field result-payload-editor__resource-action">
                <span className="sr-only">新增附加变化</span>
                <select
                  aria-label={`${labelPrefix}新增附加变化`}
                  defaultValue=""
                  onChange={(event) => {
                    handleActivateExtra(event.target.value);
                    event.target.value = "";
                  }}
                >
                  <option value="">新增附加变化</option>
                  {addableExtraFields.map((field) => (
                    <option key={field.key} value={field.key}>
                      {field.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </div>
        </div>

        <ChangeEntryGroup
          catalog={scalarCatalog}
          changeCatalogById={changeCatalogById}
          draftAmounts={draftAmounts}
          entries={scalarEntries}
          labelPrefix={labelPrefix}
          title="数值变化"
          usedChangeIds={usedChangeIds}
          onAmountBlur={handleAmountBlur}
          onAmountChange={handleChangeAmount}
          onChangeType={handleChangeType}
          onRemove={handleRemoveChange}
        />

        <ChangeEntryGroup
          catalog={resourceCatalog}
          changeCatalogById={changeCatalogById}
          draftAmounts={draftAmounts}
          entries={resourceEntries}
          labelPrefix={labelPrefix}
          title="物品变化"
          usedChangeIds={usedChangeIds}
          onAmountBlur={handleAmountBlur}
          onAmountChange={handleChangeAmount}
          onChangeType={handleChangeType}
          onRemove={handleRemoveChange}
        />

        {changeEntries.length === 0 ? (
          <div className="resource-editor__empty">
            暂未配置变化项，可通过上方入口补充数值、物品或附加变化。
          </div>
        ) : null}
      </section>

      {activeExtraFields.length > 0 ? (
        <section className="result-payload-editor__extras">
          <div className="result-payload-editor__resource-title">
            <h3>{labelPrefix}附加变化</h3>
            <p>只有实际启用的状态、功法、丹方、装备和死亡标记才会显示。</p>
          </div>

          <div className="requirement-group">
            {activeExtraFields.map((field) => {
              if (field.type === "boolean") {
                return (
                  <div key={field.key} className="requirement-field">
                    <div className="requirement-field__toolbar">
                      <span className="requirement-field__label">
                        {labelPrefix}
                        {field.label}
                      </span>
                      <button
                        className="button-secondary"
                        type="button"
                        onClick={() => handleResetExtra(field)}
                      >
                        移除
                      </button>
                    </div>
                    <label className="switch-field field--full">
                      <span>
                        <strong>
                          {labelPrefix}
                          {field.label}
                        </strong>
                        <span className="field__hint">{field.hint}</span>
                      </span>
                      <input
                        aria-label={`${labelPrefix}${field.label}`}
                        checked={state.death}
                        type="checkbox"
                        onChange={(event) => update({ death: event.target.checked })}
                      />
                    </label>
                  </div>
                );
              }

              return (
                <div key={field.key} className="requirement-field">
                  <div className="requirement-field__toolbar">
                    <span className="requirement-field__label">
                      {labelPrefix}
                      {field.label}
                    </span>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => handleResetExtra(field)}
                    >
                      移除
                    </button>
                  </div>
                  {field.key === "learned_alchemy_recipe_ids" ? (
                    <SelectionListEditor
                      addLabel="新增丹方"
                      ariaLabel={`${labelPrefix}${field.label}`}
                      emptyMessage="当前还没有选择丹方。"
                      options={alchemyRecipeOptions}
                      value={state.learned_alchemy_recipe_ids}
                      onChange={(value) => update({ learned_alchemy_recipe_ids: value })}
                    />
                  ) : field.key === "unlocked_material_ids" ? (
                    <SelectionListEditor
                      addLabel="新增材料"
                      ariaLabel={`${labelPrefix}${field.label}`}
                      emptyMessage="当前还没有选择要解锁的材料。"
                      options={resourceOptions}
                      value={state.unlocked_material_ids}
                      onChange={(value) => update({ unlocked_material_ids: value })}
                    />
                  ) : (
                    <textarea
                      aria-label={`${labelPrefix}${field.label}`}
                      className="requirement-field__input"
                      placeholder={field.placeholder}
                      value={formatLineList(state[field.key])}
                      onChange={(event) =>
                        update({
                          [field.key]: parseLineList(event.target.value),
                        } as Partial<PayloadEditorState>)
                      }
                    />
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function buildChangeEntries(state: PayloadEditorState): ChangeEntry[] {
  const resourceEntries = Object.entries(sortResourceRecord(state.resources)).map(
    ([resourceKey, amount]) => ({
      id: `resource:${resourceKey}`,
      amount,
    })
  );

  const scalarEntries = scalarFieldDefinitions
    .map((field) => ({
      id: `stat:${field.key}`,
      amount: state[field.key],
    }))
    .filter((entry) => entry.amount !== 0);

  return [...resourceEntries, ...scalarEntries];
}

function ChangeEntryGroup({
  catalog,
  changeCatalogById,
  draftAmounts,
  entries,
  labelPrefix,
  title,
  usedChangeIds,
  onAmountBlur,
  onAmountChange,
  onChangeType,
  onRemove,
}: {
  catalog: ChangeCatalogItem[];
  changeCatalogById: Record<string, ChangeCatalogItem>;
  draftAmounts: Record<string, string>;
  entries: Array<{ entry: ChangeEntry; index: number }>;
  labelPrefix: string;
  title: string;
  usedChangeIds: string[];
  onAmountBlur: (index: number) => void;
  onAmountChange: (index: number, nextAmount: string) => void;
  onChangeType: (index: number, nextId: string) => void;
  onRemove: (index: number) => void;
}) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="result-payload-editor__change-group">
      <h4>{title}</h4>
      <div className="resource-editor__stack">
        {entries.map(({ entry, index }, groupIndex) => {
          const currentItem = changeCatalogById[entry.id];
          const entryKey = buildEntryKey(entry, index);
          return (
            <div key={entryKey} className="result-payload-editor__resource-row">
              <label className="field">
                <span className="field__hint">变化类型</span>
                <select
                  aria-label={`${labelPrefix}${title}类型-${groupIndex + 1}`}
                  value={entry.id}
                  onChange={(event) => onChangeType(index, event.target.value)}
                >
                  {catalog.map((item) => {
                    const isTakenByAnother =
                      usedChangeIds.includes(item.id) && item.id !== currentItem?.id;
                    return (
                      <option key={item.id} disabled={isTakenByAnother} value={item.id}>
                        {item.label}
                      </option>
                    );
                  })}
                </select>
              </label>

              <label className="field">
                <span className="field__hint">变动数值</span>
                <input
                  aria-label={`${labelPrefix}${title}数值-${groupIndex + 1}`}
                  inputMode="numeric"
                  type="text"
                  value={draftAmounts[entryKey] ?? String(entry.amount)}
                  onBlur={() => onAmountBlur(index)}
                  onChange={(event) => onAmountChange(index, event.target.value)}
                />
              </label>

              <button
                className="button-secondary result-payload-editor__resource-remove"
                type="button"
                onClick={() => onRemove(index)}
              >
                删除
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function SelectionListEditor({
  addLabel,
  ariaLabel,
  emptyMessage,
  options,
  value,
  onChange,
}: {
  addLabel: string;
  ariaLabel: string;
  emptyMessage: string;
  options: ResourceOption[];
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const selected = value.filter(Boolean);
  const used = new Set(selected);
  const mergedOptions = mergeSelectionOptions(options, selected);
  const canAdd = mergedOptions.some((option) => !used.has(option.value));

  function handleAdd() {
    const nextOption = mergedOptions.find((option) => !used.has(option.value));
    if (!nextOption) {
      return;
    }
    onChange([...selected, nextOption.value]);
  }

  function handleChange(index: number, nextValue: string) {
    onChange(selected.map((item, itemIndex) => (itemIndex === index ? nextValue : item)));
  }

  function handleRemove(index: number) {
    onChange(selected.filter((_, itemIndex) => itemIndex !== index));
  }

  return (
    <div className="selection-list-editor">
      <div className="field__label field__label--end">
        <button
          className="button-secondary"
          disabled={!canAdd}
          type="button"
          onClick={handleAdd}
        >
          {addLabel}
        </button>
      </div>
      <div className="resource-editor__stack">
        {selected.length > 0 ? (
          selected.map((item, index) => (
            <div key={`${item}-${index}`} className="result-payload-editor__select-row">
              <label className="field">
                <span className="field__hint">选择项</span>
                <select
                  aria-label={`${ariaLabel}-${index + 1}`}
                  value={item}
                  onChange={(event) => handleChange(index, event.target.value)}
                >
                  {mergedOptions.map((option) => {
                    const disabled = used.has(option.value) && option.value !== item;
                    return (
                      <option key={option.value} disabled={disabled} value={option.value}>
                        {option.label}
                      </option>
                    );
                  })}
                </select>
              </label>
              <button
                className="button-secondary result-payload-editor__resource-remove"
                type="button"
                onClick={() => handleRemove(index)}
              >
                删除
              </button>
            </div>
          ))
        ) : (
          <div className="resource-editor__empty">{emptyMessage}</div>
        )}
      </div>
    </div>
  );
}

function mergeSelectionOptions(options: ResourceOption[], value: string[]): ResourceOption[] {
  const known = new Set(options.map((option) => option.value));
  const missingOptions = value
    .filter((item) => item && !known.has(item))
    .map((item) => ({ value: item, label: item }));
  return [...options, ...missingOptions];
}

function isExtraFieldVisible(
  state: PayloadEditorState,
  field: ExtraFieldDefinition,
  activeExtraKeys: string[]
): boolean {
  if (activeExtraKeys.includes(field.key)) {
    return true;
  }
  if (field.type === "boolean") {
    return state.death;
  }
  return state[field.key].length > 0;
}

function buildEntryKey(entry: ChangeEntry, index: number): string {
  return `${entry.id}-${index}`;
}

function buildChangeCatalog(resourceOptions: ResourceOption[]): ChangeCatalogItem[] {
  return [
    ...resourceOptions.map((option) => ({
      id: `resource:${option.value}`,
      label: option.label,
      type: "resource" as const,
      resourceKey: option.value,
    })),
    ...scalarFieldDefinitions.map((field) => ({
      id: `stat:${field.key}`,
      label: field.label,
      type: "scalar" as const,
      stateKey: field.key,
    })),
  ];
}
