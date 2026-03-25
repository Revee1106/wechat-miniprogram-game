import type { EventTemplateInput } from "../api/client";
import {
  choicePatternOptions,
  eventTypeOptions,
  outcomeTypeOptions,
  riskLevelOptions,
  triggerSourceOptions,
} from "./FieldLabelMap";
import { SectionCard } from "./SectionCard";
import {
  formatKeyValueMap,
  formatLineList,
  parseKeyValueMap,
  parseLineList,
  parseNumberInput,
  parseOptionalNumber,
} from "../utils/eventFormCodec";

export type EventTemplateSection =
  | "identity"
  | "trigger"
  | "requirements"
  | "summary";

type EventTemplateFormProps = {
  template: EventTemplateInput;
  isNew: boolean;
  sections?: EventTemplateSection[];
  onChange: <K extends keyof EventTemplateInput>(
    field: K,
    value: EventTemplateInput[K]
  ) => void;
};

export function EventTemplateForm({
  template,
  isNew,
  sections,
  onChange,
}: EventTemplateFormProps) {
  const visibleSections = sections ?? ["identity", "trigger", "requirements", "summary"];

  function toggleTriggerSource(source: string) {
    const current = template.trigger_sources ?? [];
    const next = current.includes(source)
      ? current.filter((item) => item !== source)
      : [...current, source];
    onChange("trigger_sources", next.length > 0 ? next : ["global"]);
  }

  return (
    <div className="section-grid">
      {visibleSections.includes("identity") ? (
        <SectionCard
          title="事件名片"
          description="定义事件编号、名称和玩家看到的主文案。"
        >
          <div className="field-grid">
            <label className="field">
              <span className="field__label">事件编号</span>
              <input
                aria-label="事件编号"
                disabled={!isNew}
                placeholder="例如 evt_mountain_tide"
                value={template.event_id}
                onChange={(event) => onChange("event_id", event.target.value)}
              />
              <span className="field__hint">技术标识，创建后不建议再改。</span>
            </label>

            <label className="field">
              <span className="field__label">事件名称</span>
              <input
                aria-label="事件名称"
                placeholder="例如 山中灵潮"
                value={template.event_name}
                onChange={(event) => onChange("event_name", event.target.value)}
              />
            </label>

            <label className="field">
              <span className="field__label">事件类型</span>
              <select
                aria-label="事件类型"
                value={template.event_type}
                onChange={(event) => onChange("event_type", event.target.value)}
              >
                {eventTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span className="field__label">结果倾向</span>
              <select
                aria-label="结果倾向"
                value={template.outcome_type}
                onChange={(event) => onChange("outcome_type", event.target.value)}
              >
                {outcomeTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field field--full">
              <span className="field__label">标题文案</span>
              <input
                aria-label="标题文案"
                placeholder="留空时会自动使用事件名称"
                value={template.title_text}
                onChange={(event) => onChange("title_text", event.target.value)}
              />
            </label>

            <label className="field field--full">
              <span className="field__label">正文文案</span>
              <textarea
                aria-label="正文文案"
                placeholder="描述事件发生时的场景与提示"
                value={template.body_text}
                onChange={(event) => onChange("body_text", event.target.value)}
              />
            </label>
          </div>
        </SectionCard>
      ) : null}

      {visibleSections.includes("trigger") ? (
        <SectionCard
          title="触发规则"
          description="控制事件进入随机池时的来源、权重与触发边界。"
        >
          <div className="field-grid">
            <label className="field">
              <span className="field__label">风险等级</span>
              <select
                aria-label="风险等级"
                value={template.risk_level}
                onChange={(event) => onChange("risk_level", event.target.value)}
              >
                {riskLevelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span className="field__label">选项模式</span>
              <select
                aria-label="选项模式"
                value={template.choice_pattern}
                onChange={(event) => onChange("choice_pattern", event.target.value)}
              >
                {choicePatternOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="field field--full">
              <span className="field__label">触发来源</span>
              <div className="choice-cluster" aria-label="触发来源">
                {triggerSourceOptions.map((option) => {
                  const isSelected = (template.trigger_sources ?? []).includes(option.value);
                  return (
                    <button
                      key={option.value}
                      aria-pressed={isSelected}
                      className={isSelected ? "choice-chip choice-chip--selected" : "choice-chip"}
                      type="button"
                      onClick={() => toggleTriggerSource(option.value)}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
              <span className="field__hint">
                可多选。当前已选 {(template.trigger_sources ?? []).length} 项触发来源。
              </span>
            </div>

            <label className="field">
              <span className="field__label">触发权重</span>
              <input
                aria-label="触发权重"
                min={1}
                type="number"
                value={template.weight}
                onChange={(event) => onChange("weight", Number(event.target.value))}
              />
            </label>

            <label className="field">
              <span className="field__label">地域限定</span>
              <input
                aria-label="地域限定"
                placeholder="例如 starter-valley"
                value={template.region ?? ""}
                onChange={(event) => onChange("region", event.target.value)}
              />
            </label>

            <label className="field">
              <span className="field__label">最低境界</span>
              <input
                aria-label="最低境界"
                placeholder="例如 炼气期"
                value={template.realm_min ?? ""}
                onChange={(event) => onChange("realm_min", event.target.value || null)}
              />
            </label>

            <label className="field">
              <span className="field__label">最高境界</span>
              <input
                aria-label="最高境界"
                placeholder="例如 金丹期"
                value={template.realm_max ?? ""}
                onChange={(event) => onChange("realm_max", event.target.value || null)}
              />
            </label>

            <label className="field">
              <span className="field__label">冷却回合</span>
              <input
                aria-label="冷却回合"
                min={0}
                type="number"
                value={template.cooldown_rounds ?? 0}
                onChange={(event) =>
                  onChange("cooldown_rounds", parseNumberInput(event.target.value, 0))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">单局上限</span>
              <input
                aria-label="单局上限"
                min={1}
                type="number"
                value={template.max_trigger_per_run ?? 999999}
                onChange={(event) =>
                  onChange("max_trigger_per_run", parseNumberInput(event.target.value, 1))
                }
              />
            </label>

            <label className="switch-field field--full">
              <span>
                <strong>可重复触发</strong>
                <span className="field__hint">关闭后，事件在单局中通常只会出现一次。</span>
              </span>
              <input
                aria-label="可重复触发"
                checked={template.is_repeatable}
                type="checkbox"
                onChange={(event) => onChange("is_repeatable", event.target.checked)}
              />
            </label>
          </div>
        </SectionCard>
      ) : null}

      {visibleSections.includes("requirements") ? (
        <SectionCard
          title="前置条件"
          description="定义事件出现前需要满足的资源、状态、功法与养成条件。"
        >
          <div className="field-grid">
            <label className="field field--full">
              <span className="field__label">所需资源</span>
              <textarea
                aria-label="所需资源"
                placeholder="每行一个，格式为 名称:数量"
                value={formatKeyValueMap(template.required_resources)}
                onChange={(event) =>
                  onChange("required_resources", parseKeyValueMap(event.target.value))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">需要状态</span>
              <textarea
                aria-label="需要状态"
                placeholder="每行一个状态"
                value={formatLineList(template.required_statuses)}
                onChange={(event) =>
                  onChange("required_statuses", parseLineList(event.target.value))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">排斥状态</span>
              <textarea
                aria-label="排斥状态"
                placeholder="每行一个状态"
                value={formatLineList(template.excluded_statuses)}
                onChange={(event) =>
                  onChange("excluded_statuses", parseLineList(event.target.value))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">所需功法</span>
              <textarea
                aria-label="所需功法"
                placeholder="每行一个功法编号"
                value={formatLineList(template.required_techniques)}
                onChange={(event) =>
                  onChange("required_techniques", parseLineList(event.target.value))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">所需装备标签</span>
              <textarea
                aria-label="所需装备标签"
                placeholder="每行一个装备标签"
                value={formatLineList(template.required_equipment_tags)}
                onChange={(event) =>
                  onChange("required_equipment_tags", parseLineList(event.target.value))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">最低转生次数</span>
              <input
                aria-label="最低转生次数"
                min={0}
                type="number"
                value={template.required_rebirth_count ?? 0}
                onChange={(event) =>
                  onChange("required_rebirth_count", parseNumberInput(event.target.value, 0))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">最低因果</span>
              <input
                aria-label="最低因果"
                type="number"
                value={template.required_karma_min ?? ""}
                onChange={(event) =>
                  onChange("required_karma_min", parseOptionalNumber(event.target.value))
                }
              />
            </label>

            <label className="field">
              <span className="field__label">最低气运</span>
              <input
                aria-label="最低气运"
                min={0}
                type="number"
                value={template.required_luck_min ?? 0}
                onChange={(event) =>
                  onChange("required_luck_min", parseNumberInput(event.target.value, 0))
                }
              />
            </label>

            <label className="field field--full">
              <span className="field__label">附加标记</span>
              <textarea
                aria-label="附加标记"
                placeholder="每行一个标记，用于后续扩展"
                value={formatLineList(template.flags)}
                onChange={(event) => onChange("flags", parseLineList(event.target.value))}
              />
            </label>
          </div>
        </SectionCard>
      ) : null}

      {visibleSections.includes("summary") ? (
        <SectionCard
          title="策划摘要"
          description="这里会实时汇总事件的触发性格，方便快速复核配置方向。"
        >
          <div className="chip-row">
            <span className="chip">
              类型 {eventTypeOptions.find((item) => item.value === template.event_type)?.label}
            </span>
            <span className="chip">
              倾向 {outcomeTypeOptions.find((item) => item.value === template.outcome_type)?.label}
            </span>
            <span className="chip">
              风险 {riskLevelOptions.find((item) => item.value === template.risk_level)?.label}
            </span>
          </div>
          <p className="field__hint">
            事件正文决定玩家看到的叙事，触发规则决定它何时进入随机池，前置条件决定它是否可被抽到。
          </p>
          <p className="field__hint">
            若你主要在做内容维护，优先保证 `事件名称`、`标题文案`、`正文文案` 和
            `选项文案` 可读，再回头补条件与数值。
          </p>
        </SectionCard>
      ) : null}
    </div>
  );
}
