import { eventTypeOptions, riskLevelOptions } from "./FieldLabelMap";

type EventFiltersProps = {
  eventType: string;
  riskLevel: string;
  keyword: string;
  onEventTypeChange: (value: string) => void;
  onRiskLevelChange: (value: string) => void;
  onKeywordChange: (value: string) => void;
};

export function EventFilters(props: EventFiltersProps) {
  return (
    <div className="field-grid">
      <label className="field">
        <span className="field__label">事件类型</span>
        <select
          aria-label="事件类型筛选"
          value={props.eventType}
          onChange={(event) => props.onEventTypeChange(event.target.value)}
        >
          <option value="">全部类型</option>
          {eventTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span className="field__label">风险等级</span>
        <select
          aria-label="风险等级筛选"
          value={props.riskLevel}
          onChange={(event) => props.onRiskLevelChange(event.target.value)}
        >
          <option value="">全部风险</option>
          {riskLevelOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field field--full">
        <span className="field__label">关键词</span>
        <input
          aria-label="关键词搜索"
          placeholder="搜索事件编号、名称或文案"
          value={props.keyword}
          onChange={(event) => props.onKeywordChange(event.target.value)}
        />
      </label>
    </div>
  );
}
