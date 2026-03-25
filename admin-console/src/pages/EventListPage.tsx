import { useEffect, useState } from "react";

import { fetchEvents, type EventListItem } from "../api/client";
import { EventFilters } from "../components/EventFilters";
import { EventTable } from "../components/EventTable";
import { buildEventTypeWeightMap } from "../utils/eventTypeWeight";

type EventListPageProps = {
  refreshToken?: number;
  onCreateEvent: () => void;
  onEditEvent: (eventId: string) => void;
};

export function EventListPage({
  refreshToken = 0,
  onCreateEvent,
  onEditEvent,
}: EventListPageProps) {
  const [items, setItems] = useState<EventListItem[]>([]);
  const [allItems, setAllItems] = useState<EventListItem[]>([]);
  const [eventType, setEventType] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [keyword, setKeyword] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function load() {
      const [response, fullResponse] = await Promise.all([
        fetchEvents({
          eventType,
          riskLevel,
          keyword,
        }),
        fetchEvents(),
      ]);

      if (isMounted) {
        setItems(response.items);
        setAllItems(fullResponse.items);
      }
    }

    void load();

    return () => {
      isMounted = false;
    };
  }, [eventType, riskLevel, keyword, refreshToken]);

  const typeWeightMap = buildEventTypeWeightMap(allItems);
  const typeWeightByEventId = Object.fromEntries(
    items.map((item) => [item.event_id, typeWeightMap[item.event_type] ?? 0])
  );

  return (
    <main className="section-grid">
      <section className="hero-panel">
        <div className="section-card__body">
          <div>
            <h1>事件库</h1>
            <p>按类型、风险和触发条件检索事件，快速进入编辑或继续补全配置。</p>
          </div>
          <div className="chip-row">
            <span className="chip">随机触发已启用</span>
            <span className="chip chip--soft">当前维护事件 {allItems.length || items.length} 条</span>
          </div>
        </div>
        <div className="section-card__body">
          <div className="toolbar">
            <button className="button-primary" type="button" onClick={onCreateEvent}>
              新建事件
            </button>
          </div>
          <p className="field__hint">
            事件卡片会显示类型、风险、地域、境界范围、是否可重复，以及当前所属类型的总权重，方便在不进入详情时先做快速判断。
          </p>
        </div>
      </section>
      <EventFilters
        eventType={eventType}
        riskLevel={riskLevel}
        keyword={keyword}
        onEventTypeChange={setEventType}
        onRiskLevelChange={setRiskLevel}
        onKeywordChange={setKeyword}
      />
      <EventTable items={items} typeWeightByEventId={typeWeightByEventId} onEdit={onEditEvent} />
    </main>
  );
}
