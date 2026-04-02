import { resourceOptions, sortResourceRecord } from "../utils/resourceCatalog";

type ResourceRecordEditorProps = {
  label: string;
  value?: Record<string, number>;
  onChange: (value: Record<string, number>) => void;
  addLabel?: string;
  emptyMessage?: string;
  hint?: string;
  hideLabel?: boolean;
};

export function ResourceRecordEditor({
  label,
  value,
  onChange,
  addLabel = "新增资源",
  emptyMessage = "当前还没有资源项。",
  hint,
  hideLabel = false,
}: ResourceRecordEditorProps) {
  const entries = Object.entries(sortResourceRecord(value ?? {}));
  const usedKeys = entries.map(([key]) => key);
  const canAddResource = usedKeys.length < resourceOptions.length;

  function updateEntries(nextEntries: Array<[string, number]>) {
    onChange(
      Object.fromEntries(
        nextEntries.filter(([key, amount]) => key && Number.isFinite(amount) && amount !== 0)
      )
    );
  }

  function handleAdd() {
    const nextResource = resourceOptions.find((option) => !usedKeys.includes(option.value));
    if (!nextResource) {
      return;
    }
    updateEntries([...entries, [nextResource.value, 1]]);
  }

  function handleKeyChange(index: number, nextKey: string) {
    updateEntries(
      entries.map(([key, amount], entryIndex) =>
        entryIndex === index ? [nextKey, amount] : [key, amount]
      ) as Array<[string, number]>
    );
  }

  function handleAmountChange(index: number, nextAmount: string) {
    updateEntries(
      entries.map(([key, amount], entryIndex) =>
        entryIndex === index ? [key, Number(nextAmount) || 0] : [key, amount]
      ) as Array<[string, number]>
    );
  }

  function handleRemove(index: number) {
    updateEntries(entries.filter((_, entryIndex) => entryIndex !== index));
  }

  return (
    <div className="field field--full resource-editor">
      <div className={hideLabel ? "field__label field__label--end" : "field__label"}>
        {!hideLabel ? <span>{label}</span> : null}
        <button
          className="button-secondary"
          disabled={!canAddResource}
          type="button"
          onClick={handleAdd}
        >
          {addLabel}
        </button>
      </div>

      <div className="resource-editor__stack">
        {entries.length > 0 ? (
          entries.map(([resourceKey, amount], index) => (
            <div key={`${resourceKey}-${index}`} className="resource-row">
              <label className="field">
                <span className="field__hint">资源类型</span>
                <select
                  aria-label={`${label}-资源类型-${index + 1}`}
                  value={resourceKey}
                  onChange={(event) => handleKeyChange(index, event.target.value)}
                >
                  {resourceOptions.map((option) => {
                    const disabled =
                      usedKeys.includes(option.value) && option.value !== resourceKey;
                    return (
                      <option key={option.value} disabled={disabled} value={option.value}>
                        {option.label}
                      </option>
                    );
                  })}
                </select>
              </label>

              <label className="field">
                <span className="field__hint">数量</span>
                <input
                  aria-label={`${label}-数量-${index + 1}`}
                  type="number"
                  value={amount}
                  onChange={(event) => handleAmountChange(index, event.target.value)}
                />
              </label>

              <button
                className="button-secondary resource-row__remove"
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

      {hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  );
}
