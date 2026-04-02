import { useMemo, useState, type ReactNode } from "react";

export type RequirementFieldDefinition = {
  key: string;
  label: string;
  isActive: boolean;
  onActivate: () => void;
  onReset: () => void;
  render: () => ReactNode;
};

type RequirementFieldGroupProps = {
  fields: RequirementFieldDefinition[];
  addButtonLabel?: string;
  emptyLabel?: string;
};

export function RequirementFieldGroup({
  fields,
  addButtonLabel = "新增前置条件",
  emptyLabel = "前置条件类型",
}: RequirementFieldGroupProps) {
  const [openedKeys, setOpenedKeys] = useState<string[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const visibleFields = useMemo(
    () => fields.filter((field) => field.isActive || openedKeys.includes(field.key)),
    [fields, openedKeys]
  );
  const availableFields = useMemo(
    () => fields.filter((field) => !visibleFields.some((item) => item.key === field.key)),
    [fields, visibleFields]
  );
  const [pendingKey, setPendingKey] = useState("");

  function handleOpenAdd() {
    if (availableFields.length === 0) {
      return;
    }
    setPendingKey(availableFields[0].key);
    setIsAdding(true);
  }

  function handleConfirmAdd() {
    const target = availableFields.find((field) => field.key === pendingKey);
    if (!target) {
      return;
    }
    target.onActivate();
    setOpenedKeys((current) => (current.includes(target.key) ? current : [...current, target.key]));
    setPendingKey("");
    setIsAdding(false);
  }

  function handleRemove(field: RequirementFieldDefinition) {
    field.onReset();
    setOpenedKeys((current) => current.filter((item) => item !== field.key));
  }

  return (
    <div className="requirement-group">
      {visibleFields.map((field) => (
        <div key={field.key} className="requirement-field">
          <div className="requirement-field__toolbar">
            <span className="requirement-field__label">{field.label}</span>
            <button className="button-ghost" type="button" onClick={() => handleRemove(field)}>
              移除
            </button>
          </div>
          {field.render()}
        </div>
      ))}

      {isAdding ? (
        <div className="requirement-add-bar">
          <label className="field field--full">
            <span className="field__label">{emptyLabel}</span>
            <select
              aria-label={emptyLabel}
              value={pendingKey}
              onChange={(event) => setPendingKey(event.target.value)}
            >
              {availableFields.map((field) => (
                <option key={field.key} value={field.key}>
                  {field.label}
                </option>
              ))}
            </select>
          </label>
          <div className="toolbar">
            <button className="button-primary" type="button" onClick={handleConfirmAdd}>
              确认新增
            </button>
            <button
              className="button-secondary"
              type="button"
              onClick={() => {
                setIsAdding(false);
                setPendingKey("");
              }}
            >
              取消
            </button>
          </div>
        </div>
      ) : availableFields.length > 0 ? (
        <button className="button-secondary" type="button" onClick={handleOpenAdd}>
          {addButtonLabel}
        </button>
      ) : null}
    </div>
  );
}
