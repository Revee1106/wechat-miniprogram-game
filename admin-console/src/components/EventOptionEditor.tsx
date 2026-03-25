import type { EventOptionInput } from "../api/client";
import {
  formatKeyValueMap,
  formatLineList,
  parseKeyValueMap,
  parseLineList,
} from "../utils/eventFormCodec";
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
};

export function EventOptionEditor({
  options,
  existingOptionIds,
  onAddOption,
  onChangeOption,
  onRemoveOption,
}: EventOptionEditorProps) {
  return (
    <SectionCard
      title="选项编排"
      description="先写清楚玩家看到的选项文案，再补成功率、前置条件和结果结算。"
      actions={
        <button className="button-primary" type="button" onClick={onAddOption}>
          新增选项
        </button>
      }
    >
      <div className="option-stack">
        {options.map((option, index) => {
          const isExisting = existingOptionIds.includes(option.option_id);
          const summaryText = option.option_text.trim() || "尚未填写选项文案";
          const nextEvent = option.next_event_id?.trim() || "无后续事件";
          const successFormula = option.success_rate_formula?.trim() || "未填写";

          return (
            <details className="option-card" key={`${option.option_id || "new"}-${index}`} open>
              <summary>
                <div className="option-card__meta">
                  <h3>选项 {index + 1}</h3>
                  <div>{summaryText}</div>
                  <div className="chip-row">
                    <span className="chip chip--soft">后续事件 {nextEvent}</span>
                    <span className="chip chip--soft">成功率公式 {successFormula}</span>
                  </div>
                </div>
                <div className="toolbar">
                  <button
                    className="button-danger"
                    type="button"
                    onClick={(event) => {
                      event.preventDefault();
                      onRemoveOption(index);
                    }}
                  >
                    删除选项
                  </button>
                </div>
              </summary>

              <div className="option-card__body">
                <div className="field-grid">
                  <label className="field">
                    <span className="field__label">选项编号</span>
                    <input
                      aria-label="选项编号"
                      disabled={isExisting}
                      placeholder="例如 opt_absorb"
                      value={option.option_id}
                      onChange={(event) =>
                        onChangeOption(index, "option_id", event.target.value)
                      }
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
                      onChange={(event) =>
                        onChangeOption(index, "option_text", event.target.value)
                      }
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
                      onChange={(event) =>
                        onChangeOption(index, "is_default", event.target.checked)
                      }
                    />
                  </label>
                </div>

                <SectionCard
                  title="前置条件"
                  description="选项命中前需要满足的额外条件。"
                >
                  <div className="field-grid">
                    <label className="field field--full">
                      <span className="field__label">选项所需资源</span>
                      <textarea
                        aria-label="选项所需资源"
                        placeholder="每行一个，格式为 名称:数量"
                        value={formatKeyValueMap(option.requires_resources)}
                        onChange={(event) =>
                          onChangeOption(index, "requires_resources", parseKeyValueMap(event.target.value))
                        }
                      />
                    </label>

                    <label className="field">
                      <span className="field__label">选项需要状态</span>
                      <textarea
                        aria-label="选项需要状态"
                        placeholder="每行一个状态"
                        value={formatLineList(option.requires_statuses)}
                        onChange={(event) =>
                          onChangeOption(index, "requires_statuses", parseLineList(event.target.value))
                        }
                      />
                    </label>

                    <label className="field">
                      <span className="field__label">选项所需功法</span>
                      <textarea
                        aria-label="选项所需功法"
                        placeholder="每行一个功法"
                        value={formatLineList(option.requires_techniques)}
                        onChange={(event) =>
                          onChangeOption(index, "requires_techniques", parseLineList(event.target.value))
                        }
                      />
                    </label>

                    <label className="field">
                      <span className="field__label">选项所需装备标签</span>
                      <textarea
                        aria-label="选项所需装备标签"
                        placeholder="每行一个装备标签"
                        value={formatLineList(option.requires_equipment_tags)}
                        onChange={(event) =>
                          onChangeOption(index, "requires_equipment_tags", parseLineList(event.target.value))
                        }
                      />
                    </label>

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
                  </div>
                </SectionCard>

                <div className="section-grid section-grid--two">
                  <SectionCard
                    title="成功结果"
                    description="填写该选项成功后带来的资源、属性与状态变化。"
                  >
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
                      payload={option.result_on_success}
                      onChange={(value) => onChangeOption(index, "result_on_success", value)}
                    />
                  </SectionCard>

                  <SectionCard
                    title="失败结果"
                    description="填写该选项失败后的代价、损失或状态变化。"
                  >
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
                      payload={option.result_on_failure}
                      onChange={(value) => onChangeOption(index, "result_on_failure", value)}
                    />
                  </SectionCard>
                </div>
              </div>
            </details>
          );
        })}
      </div>
    </SectionCard>
  );
}
