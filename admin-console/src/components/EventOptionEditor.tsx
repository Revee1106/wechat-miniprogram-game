import type { EventOptionInput } from "../api/client";
import { formatLineList, parseLineList } from "../utils/eventFormCodec";
import { RequirementFieldGroup } from "./RequirementFieldGroup";
import { ResourceRecordEditor } from "./ResourceRecordEditor";
import { ResultPayloadEditor } from "./ResultPayloadEditor";
import { SectionCard } from "./SectionCard";

type EventOptionEditorProps = {
  options: EventOptionInput[];
  existingOptionIds: string[];
  onAddOption: () => void;
  onChangeOption: (
    index: number,
    field: keyof EventOptionInput,
    value: EventOptionInput[keyof EventOptionInput]
  ) => void;
  onRemoveOption: (index: number) => void;
  compact?: boolean;
  activeIndex?: number;
  onSelectOption?: (index: number) => void;
  eventOptions?: Array<{ value: string; label: string }>;
};

export function EventOptionEditor({
  options,
  existingOptionIds,
  onAddOption,
  onChangeOption,
  onRemoveOption,
  compact = false,
  activeIndex = 0,
  onSelectOption,
  eventOptions = [],
}: EventOptionEditorProps) {
  if (!compact) {
    return (
      <SectionCard
        title="选项编排"
        description="先写玩家看到的选项文案，再补充成功率、前置条件和结果结算。"
        actions={
          <button className="button-primary" type="button" onClick={onAddOption}>
            新增选项
          </button>
        }
      >
        <div className="option-stack">
          {options.map((option, index) => (
            <OptionDetailCard
              key={`${option.option_id || "new"}-${index}`}
              eventOptions={eventOptions}
              existingOptionIds={existingOptionIds}
              index={index}
              onChangeOption={onChangeOption}
              onRemoveOption={onRemoveOption}
              option={option}
            />
          ))}
        </div>
      </SectionCard>
    );
  }

  const currentOption = options[activeIndex] ?? options[0];

  return (
    <div className="option-workbench">
      <div className="option-workbench__toolbar">
        <div className="option-workbench__chips">
          <button className="button-primary" type="button" onClick={onAddOption}>
            新增选项
          </button>
          {options.map((option, index) => {
            const isActive = index === activeIndex;
            const summaryText = option.option_text.trim() || `选项 ${index + 1}`;
            return (
              <button
                key={`${option.option_id || "new"}-${index}`}
                aria-pressed={isActive}
                className={
                  isActive
                    ? "option-workbench__chip option-workbench__chip--active"
                    : "option-workbench__chip"
                }
                type="button"
                onClick={() => onSelectOption?.(index)}
              >
                <span>{summaryText}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="option-workbench__panel">
        {currentOption ? (
          <OptionDetailCard
            compact
            eventOptions={eventOptions}
            existingOptionIds={existingOptionIds}
            index={activeIndex}
            onChangeOption={onChangeOption}
            onRemoveOption={onRemoveOption}
            option={currentOption}
          />
        ) : (
          <div className="empty-state">当前没有选项，可先新增一条。</div>
        )}
      </div>
    </div>
  );
}

function OptionDetailCard({
  option,
  index,
  existingOptionIds,
  onChangeOption,
  onRemoveOption,
  compact = false,
  eventOptions,
}: {
  option: EventOptionInput;
  index: number;
  existingOptionIds: string[];
  onChangeOption: (
    index: number,
    field: keyof EventOptionInput,
    value: EventOptionInput[keyof EventOptionInput]
  ) => void;
  onRemoveOption: (index: number) => void;
  compact?: boolean;
  eventOptions: Array<{ value: string; label: string }>;
}) {
  const isExisting = existingOptionIds.includes(option.option_id);
  const shellClassName = compact ? "section-grid" : "option-card__body";
  const optionTitle = option.option_text.trim() || `选项 ${index + 1}`;

  const requirementFields = [
    {
      key: "requires_resources",
      label: "选项所需资源",
      isActive: Object.keys(option.requires_resources ?? {}).length > 0,
      onActivate: () => onChangeOption(index, "requires_resources", {}),
      onReset: () => onChangeOption(index, "requires_resources", {}),
      render: () => (
        <ResourceRecordEditor
          addLabel="新增资源"
          emptyMessage="当前还没有资源门槛。"
          hideLabel
          label="选项所需资源"
          onChange={(value) => onChangeOption(index, "requires_resources", value)}
          value={option.requires_resources}
        />
      ),
    },
    {
      key: "requires_statuses",
      label: "选项需要状态",
      isActive: (option.requires_statuses ?? []).length > 0,
      onActivate: () => onChangeOption(index, "requires_statuses", []),
      onReset: () => onChangeOption(index, "requires_statuses", []),
      render: () => (
        <textarea
          aria-label="选项需要状态"
          className="requirement-field__input"
          placeholder="每行一个状态"
          value={formatLineList(option.requires_statuses)}
          onChange={(event) =>
            onChangeOption(index, "requires_statuses", parseLineList(event.target.value))
          }
        />
      ),
    },
    {
      key: "requires_techniques",
      label: "选项所需功法",
      isActive: (option.requires_techniques ?? []).length > 0,
      onActivate: () => onChangeOption(index, "requires_techniques", []),
      onReset: () => onChangeOption(index, "requires_techniques", []),
      render: () => (
        <textarea
          aria-label="选项所需功法"
          className="requirement-field__input"
          placeholder="每行一个功法"
          value={formatLineList(option.requires_techniques)}
          onChange={(event) =>
            onChangeOption(index, "requires_techniques", parseLineList(event.target.value))
          }
        />
      ),
    },
    {
      key: "requires_equipment_tags",
      label: "选项所需装备标签",
      isActive: (option.requires_equipment_tags ?? []).length > 0,
      onActivate: () => onChangeOption(index, "requires_equipment_tags", []),
      onReset: () => onChangeOption(index, "requires_equipment_tags", []),
      render: () => (
        <textarea
          aria-label="选项所需装备标签"
          className="requirement-field__input"
          placeholder="每行一个装备标签"
          value={formatLineList(option.requires_equipment_tags)}
          onChange={(event) =>
            onChangeOption(index, "requires_equipment_tags", parseLineList(event.target.value))
          }
        />
      ),
    },
  ];

  return (
    <SectionCard
      title={optionTitle}
      description={compact ? undefined : "当前只编辑一个选项，其他选项通过左侧清单切换。"}
      actions={
        <button className="button-danger" type="button" onClick={() => onRemoveOption(index)}>
          删除选项
        </button>
      }
    >
      <div className={shellClassName}>
        <div className="field-grid">
          <label className="field">
            <span className="field__label">选项编号</span>
            <input
              aria-label="选项编号"
              disabled={isExisting}
              placeholder="例如 opt_absorb"
              value={option.option_id}
              onChange={(event) => onChangeOption(index, "option_id", event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">排序</span>
            <input
              aria-label="排序"
              min={1}
              type="number"
              value={option.sort_order}
              onChange={(event) =>
                onChangeOption(index, "sort_order", Number(event.target.value))
              }
            />
          </label>

          <label className="field field--full">
            <span className="field__label">选项文案</span>
            <input
              aria-label="选项文案"
              placeholder="玩家在事件中看到的选择"
              value={option.option_text}
              onChange={(event) => onChangeOption(index, "option_text", event.target.value)}
            />
          </label>

          <label className="switch-field field--full">
            <span>
              <strong>默认选项</strong>
              <span className="field__hint">若事件需要默认分支，可在这里设定。</span>
            </span>
            <input
              aria-label="默认选项"
              checked={option.is_default}
              type="checkbox"
              onChange={(event) => onChangeOption(index, "is_default", event.target.checked)}
            />
          </label>
        </div>

        <SectionCard title="前置条件" description="选项命中前需要满足的额外条件。">
          <RequirementFieldGroup fields={requirementFields} />
        </SectionCard>

        <SectionCard title="判定与后续" description="编辑成功率判定和后续事件跳转。">
          <div className="field-grid">
            <label className="field">
              <span className="field__label">成功率公式</span>
              <input
                aria-label="成功率公式"
                placeholder="例如 base_success_rate + 0.1"
                value={option.success_rate_formula ?? ""}
                onChange={(event) =>
                  onChangeOption(index, "success_rate_formula", event.target.value)
                }
              />
            </label>

            {eventOptions.length > 0 ? (
              <label className="field">
                <span className="field__label">后续事件</span>
                <select
                  aria-label="后续事件"
                  value={option.next_event_id ?? ""}
                  onChange={(event) =>
                    onChangeOption(index, "next_event_id", event.target.value || null)
                  }
                >
                  <option value="">无后续事件</option>
                  {eventOptions.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <label className="field">
                <span className="field__label">后续事件</span>
                <input
                  aria-label="后续事件"
                  placeholder="填写事件编号，留空表示结束"
                  value={option.next_event_id ?? ""}
                  onChange={(event) =>
                    onChangeOption(index, "next_event_id", event.target.value || null)
                  }
                />
              </label>
            )}
          </div>
        </SectionCard>

        <div className="section-grid section-grid--two">
          <SectionCard title="成功结果" description="填写该选项成功后带来的资源、属性与状态变化。">
            <div className="field-grid">
              <label className="field field--full">
                <span className="field__label">成功日志</span>
                <textarea
                  aria-label="成功日志"
                  placeholder="成功分支的战报文案"
                  value={option.log_text_success ?? ""}
                  onChange={(event) =>
                    onChangeOption(index, "log_text_success", event.target.value)
                  }
                />
              </label>
            </div>
            <ResultPayloadEditor
              labelPrefix="成功"
              onChange={(value) => onChangeOption(index, "result_on_success", value)}
              payload={option.result_on_success}
            />
          </SectionCard>

          <SectionCard title="失败结果" description="填写该选项失败后的代价、损失或状态变化。">
            <div className="field-grid">
              <label className="field field--full">
                <span className="field__label">失败日志</span>
                <textarea
                  aria-label="失败日志"
                  placeholder="失败分支的战报文案"
                  value={option.log_text_failure ?? ""}
                  onChange={(event) =>
                    onChangeOption(index, "log_text_failure", event.target.value)
                  }
                />
              </label>
            </div>
            <ResultPayloadEditor
              labelPrefix="失败"
              onChange={(value) => onChangeOption(index, "result_on_failure", value)}
              payload={option.result_on_failure}
            />
          </SectionCard>
        </div>
      </div>
    </SectionCard>
  );
}
