import {
  buildPayloadFromEditorState,
  formatLineList,
  parseLineList,
  parseNumberInput,
  parsePayloadEditorState,
  type PayloadEditorState,
} from "../utils/eventFormCodec";
import { resourceOptions, sortResourceRecord } from "../utils/resourceCatalog";

type ResultPayloadEditorProps = {
  labelPrefix: string;
  payload: Record<string, unknown> | string | undefined;
  onChange: (value: Record<string, unknown>) => void;
};

type ScalarFieldKey =
  | "cultivation_exp"
  | "lifespan_delta"
  | "hp_delta"
  | "breakthrough_bonus"
  | "technique_exp"
  | "luck_delta"
  | "karma_delta"
  | "rebirth_progress_delta";

type ListFieldKey =
  | "statuses_add"
  | "statuses_remove"
  | "techniques_add"
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

const changeCatalog: ChangeCatalogItem[] = [
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

const changeCatalogById = Object.fromEntries(
  changeCatalog.map((item) => [item.id, item])
) as Record<string, ChangeCatalogItem>;

export function ResultPayloadEditor({
  labelPrefix,
  payload,
  onChange,
}: ResultPayloadEditorProps) {
  const state = parsePayloadEditorState(payload);
  const changeEntries = buildChangeEntries(state);
  const usedChangeIds = changeEntries.map((entry) => entry.id);
  const addableChangeOptions = changeCatalog.filter((item) => !usedChangeIds.includes(item.id));
  const activeExtraFields = extraFieldDefinitions.filter((field) => isExtraFieldActive(state, field));
  const addableExtraFields = extraFieldDefinitions.filter((field) => !isExtraFieldActive(state, field));

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
    const nextEntries = changeEntries.map((entry, entryIndex) =>
      entryIndex === index ? { ...entry, id: nextId } : entry
    );
    updateChangeEntries(nextEntries);
  }

  function handleChangeAmount(index: number, nextAmount: string) {
    const nextEntries = changeEntries.map((entry, entryIndex) =>
      entryIndex === index ? { ...entry, amount: parseNumberInput(nextAmount, 0) } : entry
    );
    updateChangeEntries(nextEntries);
  }

  function handleRemoveChange(index: number) {
    updateChangeEntries(changeEntries.filter((_, entryIndex) => entryIndex !== index));
  }

  function handleActivateExtra(fieldKey: string) {
    const definition = extraFieldDefinitions.find((field) => field.key === fieldKey);
    if (!definition) {
      return;
    }
    if (definition.type === "boolean") {
      update({ death: true });
      return;
    }
    update({ [definition.key]: [] } as Partial<PayloadEditorState>);
  }

  function handleResetExtra(field: ExtraFieldDefinition) {
    update({ [field.key]: field.emptyValue } as Partial<PayloadEditorState>);
  }

  return (
    <div className="result-payload-editor">
      <section className="result-payload-editor__resource-panel">
        <div className="result-payload-editor__resource-header">
          <div className="result-payload-editor__resource-title">
            <h3>{labelPrefix}变化</h3>
            <p>资源和数值变化统一在这里维护。正数表示获得，负数表示消耗。</p>
          </div>
          <div className="result-payload-editor__actions">
            <label className="field result-payload-editor__resource-action">
              <span className="sr-only">新增变化项</span>
              <select
                aria-label={`${labelPrefix}新增变化项`}
                defaultValue=""
                onChange={(event) => {
                  handleAddChange(event.target.value);
                  event.target.value = "";
                }}
              >
                <option value="">新增变化项</option>
                {addableChangeOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
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

        <div className="resource-editor__stack">
          {changeEntries.length > 0 ? (
            changeEntries.map((entry, index) => {
              const currentItem = changeCatalogById[entry.id];
              return (
                <div key={`${entry.id}-${index}`} className="result-payload-editor__resource-row">
                  <label className="field">
                    <span className="field__hint">变化类型</span>
                    <select
                      aria-label={`${labelPrefix}变化项类型-${index + 1}`}
                      value={entry.id}
                      onChange={(event) => handleChangeType(index, event.target.value)}
                    >
                      {changeCatalog.map((item) => {
                        const isTakenByAnother =
                          usedChangeIds.includes(item.id) && item.id !== currentItem?.id;
                        return (
                          <option
                            key={item.id}
                            disabled={isTakenByAnother}
                            value={item.id}
                          >
                            {item.label}
                          </option>
                        );
                      })}
                    </select>
                  </label>

                  <label className="field">
                    <span className="field__hint">变动数值</span>
                    <input
                      aria-label={`${labelPrefix}变化数值-${index + 1}`}
                      type="number"
                      value={entry.amount}
                      onChange={(event) => handleChangeAmount(index, event.target.value)}
                    />
                  </label>

                  <button
                    className="button-secondary result-payload-editor__resource-remove"
                    type="button"
                    onClick={() => handleRemoveChange(index)}
                  >
                    删除
                  </button>
                </div>
              );
            })
          ) : (
            <div className="resource-editor__empty">
              暂未配置变化项，可通过“新增变化项”补充收益、消耗或属性变动。
            </div>
          )}
        </div>
      </section>

      {activeExtraFields.length > 0 ? (
        <section className="result-payload-editor__extras">
          <div className="result-payload-editor__resource-title">
            <h3>{labelPrefix}附加变化</h3>
            <p>只有实际启用的状态、功法、装备和死亡标记才会显示。</p>
          </div>

          <div className="requirement-group">
            {activeExtraFields.map((field) => {
              if (field.type === "boolean") {
                return (
                  <div key={field.key} className="requirement-field">
                    <div className="requirement-field__toolbar">
                      <span className="requirement-field__label">{labelPrefix}{field.label}</span>
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
                        <strong>{labelPrefix}{field.label}</strong>
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
                    <span className="requirement-field__label">{labelPrefix}{field.label}</span>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => handleResetExtra(field)}
                    >
                      移除
                    </button>
                  </div>
                  <textarea
                    aria-label={`${labelPrefix}${field.label}`}
                    className="requirement-field__input"
                    placeholder={field.placeholder}
                    value={formatLineList(state[field.key])}
                    onChange={(event) =>
                      update({ [field.key]: parseLineList(event.target.value) } as Partial<PayloadEditorState>)
                    }
                  />
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

function isExtraFieldActive(state: PayloadEditorState, field: ExtraFieldDefinition): boolean {
  if (field.type === "boolean") {
    return state.death;
  }
  return state[field.key].length > 0;
}
