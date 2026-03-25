import type { EventListItem } from "../api/client";
import {
  eventTypeOptions,
  formatRealmRange,
  formatRepeatable,
  formatTriggerSources,
  getOptionLabel,
  outcomeTypeOptions,
  riskLevelOptions,
} from "./FieldLabelMap";

type EventTableProps = {
  items: EventListItem[];
  typeWeightByEventId: Record<string, number>;
  onEdit: (eventId: string) => void;
};

export function EventTable({ items, typeWeightByEventId, onEdit }: EventTableProps) {
  if (items.length === 0) {
    return <div className="empty-state">当前筛选下没有事件，试试调整条件或新建一条事件。</div>;
  }

  return (
    <div className="library-grid">
      {items.map((item) => (
        <article key={item.event_id} className="library-card">
          <header className="library-card__header">
            <h3>{item.event_name}</h3>
            <div className="library-card__id">事件编号 {item.event_id}</div>
          </header>
          <div className="chip-row">
            <span className="chip">事件类型 {getOptionLabel(eventTypeOptions, item.event_type)}</span>
            <span className="chip">结果倾向 {getOptionLabel(outcomeTypeOptions, item.outcome_type)}</span>
            <span className="chip">风险等级 {getOptionLabel(riskLevelOptions, item.risk_level)}</span>
          </div>
          <dl className="kv-grid">
            <div className="kv-item">
              <dt>触发方式</dt>
              <dd>{formatTriggerSources(item.trigger_sources)}</dd>
            </div>
            <div className="kv-item">
              <dt>地域</dt>
              <dd>{item.region || "不限"}</dd>
            </div>
            <div className="kv-item">
              <dt>境界范围</dt>
              <dd>{formatRealmRange(item.realm_min, item.realm_max)}</dd>
            </div>
            <div className="kv-item">
              <dt>选项数</dt>
              <dd>{item.option_ids?.length ?? 0}</dd>
            </div>
          </dl>
          <div className="chip-row">
            <span className="chip chip--soft">{formatRepeatable(item.is_repeatable)}</span>
            <span className="chip chip--soft">同类总权重 {typeWeightByEventId[item.event_id] ?? 0}</span>
          </div>
          <div className="toolbar">
            <button className="button-primary" type="button" onClick={() => onEdit(item.event_id)}>
              编辑事件
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}
