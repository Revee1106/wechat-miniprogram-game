import { useEffect, useState, type ReactNode } from "react";

import {
  createEvent,
  createOption,
  deleteEvent,
  deleteOption,
  fetchEventDetail,
  fetchEvents,
  reloadEvents,
  updateEvent,
  updateOption,
  type EventListItem,
  type EventOptionInput,
  type EventTemplateInput,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { EventOptionEditor } from "../components/EventOptionEditor";
import {
  choicePatternOptions,
  eventTypeOptions,
  formatTriggerSources,
  getOptionLabel,
  riskLevelOptions,
} from "../components/FieldLabelMap";
import { EventTemplateForm } from "../components/EventTemplateForm";
import { SingleOutcomeEditor } from "../components/SingleOutcomeEditor";
import { getEventTypeTotalWeight } from "../utils/eventTypeWeight";

const DRAFT_EVENT_ID = "__draft_event__";
const SINGLE_OUTCOME_TEXT = "完成事件";

type EventListPageProps = {
  refreshToken?: number;
};

type EventPanel = "identity" | "trigger" | "requirements" | "outcome";

export function EventListPage({ refreshToken = 0 }: EventListPageProps) {
  const [items, setItems] = useState<EventListItem[]>([]);
  const [allItems, setAllItems] = useState<EventListItem[]>([]);
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [riskLevelFilter, setRiskLevelFilter] = useState("");
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [draftEventType, setDraftEventType] = useState("");
  const [template, setTemplate] = useState<EventTemplateInput | null>(null);
  const [options, setOptions] = useState<EventOptionInput[]>([]);
  const [existingOptionIds, setExistingOptionIds] = useState<string[]>([]);
  const [removedOptionIds, setRemovedOptionIds] = useState<string[]>([]);
  const [drawerPanel, setDrawerPanel] = useState<EventPanel | null>(null);
  const [activeOptionIndex, setActiveOptionIndex] = useState(0);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const isDraft = selectedEventId === DRAFT_EVENT_ID;
  const isSingleOutcome = template?.choice_pattern === "single_outcome";
  const singleOutcomeOption = isSingleOutcome
    ? normalizeSingleOutcomeOption(options[0], template?.event_id || "event")
    : null;
  const currentTypeTotalWeight = template ? getEventTypeTotalWeight(allItems, template) : 0;
  const linkedEventOptions = allItems
    .filter((item) => item.event_id !== template?.event_id)
    .map((item) => ({ value: item.event_id, label: item.event_name }));
  const defaultOptionCount = options.filter((option) => option.is_default).length;

  useEffect(() => {
    let isMounted = true;

    async function loadLibrary() {
      setIsLoading(true);
      try {
        const [filteredResponse, fullResponse] = await Promise.all([
          fetchEvents({
            eventType: eventTypeFilter,
            riskLevel: riskLevelFilter,
          }),
          fetchEvents(),
        ]);
        if (!isMounted) {
          return;
        }
        const nextItems = filteredResponse.items ?? [];
        const nextAllItems = fullResponse.items ?? [];
        setItems(nextItems);
        setAllItems(nextAllItems);
        setSelectedEventId((current) => {
          if (current === DRAFT_EVENT_ID && template) {
            return current;
          }
          if (current && nextAllItems.some((item) => item.event_id === current)) {
            return current;
          }
          return nextItems[0]?.event_id ?? nextAllItems[0]?.event_id ?? null;
        });
      } catch (error) {
        if (isMounted) {
          setErrorMessage((error as Error).message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadLibrary();

    return () => {
      isMounted = false;
    };
  }, [eventTypeFilter, refreshToken, riskLevelFilter]);

  useEffect(() => {
    let isMounted = true;

    async function loadDetail() {
      if (!selectedEventId || selectedEventId === DRAFT_EVENT_ID) {
        return;
      }
      try {
        const detail = await fetchEventDetail(selectedEventId);
        if (!isMounted) {
          return;
        }
        setTemplate(normalizeTemplate(detail.template));
        setOptions(
          detail.options.length > 0 ? detail.options.map(normalizeOption) : [createEmptyOption(1)]
        );
        setExistingOptionIds(detail.options.map((option) => option.option_id));
        setRemovedOptionIds([]);
        setActiveOptionIndex(0);
        setDrawerPanel(null);
        setStatusMessage(null);
        setErrorMessage(null);
      } catch (error) {
        if (isMounted) {
          setErrorMessage((error as Error).message);
        }
      }
    }

    void loadDetail();

    return () => {
      isMounted = false;
    };
  }, [selectedEventId]);

  function handleCreateDraft(eventType = "cultivation") {
    setSelectedEventId(DRAFT_EVENT_ID);
    setTemplate(createEmptyTemplate(eventType));
    setOptions([createEmptyOption(1)]);
    setExistingOptionIds([]);
    setRemovedOptionIds([]);
    setDrawerPanel("identity");
    setActiveOptionIndex(0);
    setStatusMessage(null);
    setErrorMessage(null);
  }

  function handleDraftTypeChange(value: string) {
    if (!value) {
      return;
    }
    setDraftEventType("");
    handleCreateDraft(value);
  }

  function handleSelectedEventChange(value: string) {
    if (!value) {
      return;
    }
    setSelectedEventId(value);
    setDrawerPanel(null);
    setStatusMessage(null);
    setErrorMessage(null);
  }

  function handleTemplateChange<K extends keyof EventTemplateInput>(
    field: K,
    value: EventTemplateInput[K]
  ) {
    setTemplate((current) => {
      const nextTemplate = {
        ...(current ?? createEmptyTemplate()),
        [field]: value,
      };
      if (field === "choice_pattern" && String(value) === "single_outcome") {
        setOptions((currentOptions) => [
          createCleanSingleOutcomeOption(
            currentOptions[0],
            nextTemplate.event_id || "event",
            nextTemplate.event_name
          ),
        ]);
        setActiveOptionIndex(0);
      }
      return nextTemplate;
    });
  }

  function handleOptionChange(
    index: number,
    field: keyof EventOptionInput,
    value: EventOptionInput[keyof EventOptionInput]
  ) {
    setOptions((current) =>
      current.map((option, optionIndex) =>
        optionIndex === index ? { ...option, [field]: value } : option
      )
    );
  }

  function handleSingleOutcomeChange<K extends keyof EventOptionInput>(
    field: K,
    value: EventOptionInput[K]
  ) {
    setOptions((current) => {
      const base = normalizeSingleOutcomeOption(current[0], template?.event_id || "event");
      return [{ ...base, [field]: value }];
    });
  }

  function handleAddOption() {
    setOptions((current) => {
      const next = [...current, createEmptyOption(current.length + 1)];
      setActiveOptionIndex(next.length - 1);
      return next;
    });
  }

  function handleRemoveOption(index: number) {
    setOptions((current) => {
      const target = current[index];
      if (target?.option_id && existingOptionIds.includes(target.option_id)) {
        setRemovedOptionIds((removed) =>
          removed.includes(target.option_id) ? removed : [...removed, target.option_id]
        );
      }
      const next = current.filter((_, optionIndex) => optionIndex !== index);
      setActiveOptionIndex(Math.max(0, Math.min(index, next.length - 1)));
      return next.length > 0 ? next : [createEmptyOption(1)];
    });
  }

  async function reloadLibraryAndRuntime(savedEventId?: string) {
    const [filteredResponse, fullResponse, reloadResult] = await Promise.all([
      fetchEvents({
        eventType: eventTypeFilter,
        riskLevel: riskLevelFilter,
      }),
      fetchEvents(),
      reloadEvents(),
    ]);

    const nextItems = filteredResponse.items ?? [];
    const nextAllItems = fullResponse.items ?? [];

    setItems(nextItems);
    setAllItems(nextAllItems);
    setSelectedEventId(
      savedEventId ?? nextItems[0]?.event_id ?? nextAllItems[0]?.event_id ?? null
    );
    setStatusMessage(
      `已保存并自动重载运行时，当前载入 ${reloadResult.template_count} 条事件和 ${reloadResult.option_count} 个选项。`
    );
  }

  async function handleSave() {
    if (!template) {
      return;
    }

    const eventIdValue = template.event_id.trim();
    const eventNameValue = template.event_name.trim();

    if (!eventIdValue || !eventNameValue) {
      setErrorMessage("事件编号和事件名称不能为空。");
      return;
    }

    const normalizedOptions = buildPreparedOptions({
      eventIdValue,
      eventNameValue,
      isSingleOutcome: template.choice_pattern === "single_outcome",
      options,
    });
    const optionIdsToDelete = collectOptionIdsToDelete({
      existingOptionIds,
      removedOptionIds,
      normalizedOptions,
      isSingleOutcome: template.choice_pattern === "single_outcome",
    });

    if (normalizedOptions.length === 0) {
      setErrorMessage("至少需要保留一条结果配置。");
      return;
    }

    const templatePayload: EventTemplateInput = {
      ...normalizeTemplate(template),
      event_id: eventIdValue,
      event_name: eventNameValue,
      title_text: template.title_text.trim() || eventNameValue,
      option_ids: normalizedOptions.map((option) => option.option_id),
    };

    try {
      setErrorMessage(null);
      setStatusMessage(null);

      if (isDraft) {
        await createEvent(templatePayload);
      } else {
        await updateEvent(eventIdValue, templatePayload);
      }

      for (const optionId of optionIdsToDelete) {
        await deleteOption(optionId);
      }

      for (const option of normalizedOptions) {
        if (existingOptionIds.includes(option.option_id)) {
          await updateOption(option.option_id, option);
        } else {
          await createOption(eventIdValue, option);
        }
      }

      setTemplate(templatePayload);
      setOptions(normalizedOptions);
      setExistingOptionIds(normalizedOptions.map((option) => option.option_id));
      setRemovedOptionIds([]);
      await reloadLibraryAndRuntime(eventIdValue);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!template || isDraft) {
      return;
    }
    if (!window.confirm(`确定删除事件 ${template.event_name} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteEvent(template.event_id);
      setTemplate(null);
      setOptions([]);
      setExistingOptionIds([]);
      setRemovedOptionIds([]);
      setDrawerPanel(null);
      await reloadLibraryAndRuntime();
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载事件配置...</div>;
  }

  return (
    <>
      <ConfigWorkbench
        className="config-workbench--event"
        title="事件配置"
        description="左侧只负责筛选、切换和保存，右侧只编辑当前选中的事件。"
        hideHero
        registryTitle="事件清单"
        registryContent={
          <div className="section-grid">
            <div className="event-compact-toolbar">
              <div className="event-compact-toolbar__grid">
                <label className="field">
                  <span className="field__label">事件类型</span>
                  <select
                    aria-label="事件类型筛选"
                    value={eventTypeFilter}
                    onChange={(event) => setEventTypeFilter(event.target.value)}
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
                    value={riskLevelFilter}
                    onChange={(event) => setRiskLevelFilter(event.target.value)}
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
                  <span className="field__label">当前事件</span>
                  <select
                    aria-label="当前事件"
                    value={selectedEventId ?? ""}
                    onChange={(event) => handleSelectedEventChange(event.target.value)}
                  >
                    <option value="">选择已有事件</option>
                    {isDraft && template ? (
                      <option value={DRAFT_EVENT_ID}>
                        草稿：{template.event_name || "未命名新事件"}
                      </option>
                    ) : null}
                    {items.map((item) => (
                      <option key={item.event_id} value={item.event_id}>
                        {item.event_name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field field--full">
                  <span className="field__label">按类型新建</span>
                  <select
                    aria-label="按类型新建"
                    value={draftEventType}
                    onChange={(event) => handleDraftTypeChange(event.target.value)}
                  >
                    <option value="">选择类型后立即创建草稿</option>
                    {eventTypeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="event-compact-toolbar__actions">
                <button
                  className="button-primary event-compact-toolbar__save"
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={!template}
                >
                  保存事件
                </button>
                <button
                  className="button-danger event-compact-toolbar__delete"
                  type="button"
                  onClick={() => void handleDelete()}
                  disabled={!template || isDraft}
                >
                  删除事件
                </button>
              </div>
            </div>

            {items.length === 0 && !isDraft ? (
              <div className="empty-state">当前筛选下没有事件，可通过上方下拉框直接创建草稿。</div>
            ) : null}
          </div>
        }
        detailTitle={template?.event_name || "事件详情"}
        detailContent={
          template ? (
            <div className="section-grid">
              {errorMessage ? (
                <div className="status-card__banner status-card__banner--error" role="alert">
                  {errorMessage}
                </div>
              ) : null}
              {statusMessage ? <div className="status-card__banner">{statusMessage}</div> : null}

              <div className="event-detail-chips">
                <span className="event-detail-chip">
                  <small>触发来源</small>
                  <strong>{formatTriggerSources(template.trigger_sources)}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>触发权重</small>
                  <strong>{`权重 ${template.weight}`}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>选项模式</small>
                  <strong>{getOptionLabel(choicePatternOptions, template.choice_pattern)}</strong>
                </span>
              </div>

              <div className="event-module-tabs" role="tablist" aria-label="事件详情模块">
                <button
                  aria-pressed={drawerPanel === "identity"}
                  className={drawerPanel === "identity" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("identity")}
                >
                  基础信息
                </button>
                <button
                  aria-pressed={drawerPanel === "trigger"}
                  className={drawerPanel === "trigger" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("trigger")}
                >
                  触发规则
                </button>
                <button
                  aria-pressed={drawerPanel === "requirements"}
                  className={
                    drawerPanel === "requirements" ? "event-module-tab event-module-tab--active" : "event-module-tab"
                  }
                  type="button"
                  onClick={() => setDrawerPanel("requirements")}
                >
                  前置条件
                </button>
                <button
                  aria-pressed={drawerPanel === "outcome"}
                  className={drawerPanel === "outcome" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("outcome")}
                >
                  选项与结果
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state">左侧选择一个事件后，即可在这里查看摘要并通过抽屉编辑。</div>
          )
        }
        actionBar={undefined}
      />

      {template && drawerPanel ? (
        <EventEditorDrawer
          description={getPanelDescription(drawerPanel)}
          title={getPanelTitle(drawerPanel)}
          onClose={() => setDrawerPanel(null)}
        >
          {drawerPanel === "identity" ? (
            <EventTemplateForm
              isNew={isDraft}
              onChange={handleTemplateChange}
              sections={["identity"]}
              template={template}
            />
          ) : drawerPanel === "trigger" ? (
            <EventTemplateForm
              isNew={isDraft}
              onChange={handleTemplateChange}
              sections={["trigger"]}
              template={template}
            />
          ) : drawerPanel === "requirements" ? (
            <EventTemplateForm
              isNew={isDraft}
              onChange={handleTemplateChange}
              sections={["requirements"]}
              template={template}
            />
          ) : isSingleOutcome && singleOutcomeOption ? (
            <SingleOutcomeEditor onChange={handleSingleOutcomeChange} option={singleOutcomeOption} />
          ) : (
            <EventOptionEditor
              activeIndex={activeOptionIndex}
              compact
              eventOptions={linkedEventOptions}
              existingOptionIds={existingOptionIds}
              onAddOption={handleAddOption}
              onChangeOption={handleOptionChange}
              onRemoveOption={handleRemoveOption}
              onSelectOption={setActiveOptionIndex}
              options={options}
            />
          )}
        </EventEditorDrawer>
      ) : null}
    </>
  );
}
function EventSummaryCard({
  title,
  description,
  actionLabel,
  onEdit,
  children,
}: {
  title: string;
  description: string;
  actionLabel: string;
  onEdit: () => void;
  children: ReactNode;
}) {
  return (
    <section className="event-summary-card">
      <header className="event-summary-card__header">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <button className="button-secondary" type="button" onClick={onEdit}>
          {actionLabel}
        </button>
      </header>
      <div className="event-summary-card__list">{children}</div>
    </section>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="event-summary-item">
      <strong>{label}</strong>
      <span>{value}</span>
    </div>
  );
}

function EventEditorDrawer({
  title,
  description,
  onClose,
  children,
}: {
  title: string;
  description: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="editor-dialog-backdrop" role="presentation" onClick={onClose}>
      <section
        aria-label={title}
        aria-modal="true"
        className="editor-dialog editor-dialog--drawer"
        role="dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="editor-dialog__header">
          <div>
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
          <button className="button-ghost" type="button" onClick={onClose}>
            关闭
          </button>
        </header>
        <div className="editor-dialog__body event-drawer__body">{children}</div>
      </section>
    </div>
  );
}

function getPanelTitle(panel: EventPanel): string {
  switch (panel) {
    case "identity":
      return "基础信息";
    case "trigger":
      return "触发规则";
    case "requirements":
      return "前置条件";
    case "outcome":
      return "选项与结果";
  }
}

function getPanelDescription(panel: EventPanel): string {
  switch (panel) {
    case "identity":
      return "编辑名称、编号、标题和主文案。";
    case "trigger":
      return "编辑风险等级、触发来源、权重和边界。";
    case "requirements":
      return "编辑资源、状态、功法与成长门槛。";
    case "outcome":
      return "编辑选项、默认结果与后续事件。";
  }
}

function summarizeText(value: string | null | undefined): string {
  const normalized = (value ?? "").replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "未填写";
  }
  if (normalized.length <= 30) {
    return normalized;
  }
  return `${normalized.slice(0, 30)}…`;
}

function countRecordKeys(value: Record<string, unknown> | null | undefined): number {
  return Object.keys(value ?? {}).length;
}

function buildOptionPreview(options: EventOptionInput[], isSingleOutcome: boolean): string {
  if (isSingleOutcome) {
    return "默认结果";
  }

  const labels = options
    .map((option, index) => option.option_text.trim() || `选项 ${index + 1}`)
    .filter(Boolean);

  if (labels.length === 0) {
    return "未设置";
  }
  if (labels.length <= 2) {
    return labels.join("、");
  }
  return `${labels.slice(0, 2).join("、")}，另 ${labels.length - 2} 项`;
}

function buildNextEventPreview(options: EventOptionInput[], isSingleOutcome: boolean): string {
  const nextEventCount = options.filter((option) => option.next_event_id?.trim()).length;
  if (nextEventCount === 0) {
    return isSingleOutcome ? "无后续事件" : "当前没有后续事件";
  }
  return `${nextEventCount} 个结果会跳转后续事件`;
}
function buildPreparedOptions({
  eventIdValue,
  eventNameValue,
  isSingleOutcome,
  options,
}: {
  eventIdValue: string;
  eventNameValue: string;
  isSingleOutcome: boolean;
  options: EventOptionInput[];
}): EventOptionInput[] {
  if (isSingleOutcome) {
    const base = normalizeSingleOutcomeOption(options[0], eventIdValue);
    return [
      {
        ...base,
        event_id: eventIdValue,
        option_id: base.option_id.trim() || `${eventIdValue}_default`,
        option_text: SINGLE_OUTCOME_TEXT,
        sort_order: 1,
        is_default: true,
        success_rate_formula: "",
        requires_resources: {},
        requires_statuses: [],
        requires_techniques: [],
        requires_equipment_tags: [],
        result_on_failure: {},
        log_text_failure: "",
        next_event_id: base.next_event_id ?? null,
        log_text_success: base.log_text_success ?? eventNameValue,
      },
    ];
  }

  return options
    .filter((option) => option.option_id.trim() || option.option_text.trim())
    .map((option, index) => ({
      ...option,
      event_id: eventIdValue,
      option_id: option.option_id.trim(),
      option_text: option.option_text.trim(),
      sort_order: index + 1,
    }));
}

function normalizeSingleOutcomeOption(
  option: EventOptionInput | undefined,
  eventIdSeed: string
): EventOptionInput {
  const normalized = normalizeOption(option ?? createEmptyOption(1));
  return {
    ...normalized,
    option_id: normalized.option_id || `${eventIdSeed}_default`,
    option_text: SINGLE_OUTCOME_TEXT,
    sort_order: 1,
    is_default: true,
    success_rate_formula: "",
    requires_resources: {},
    requires_statuses: [],
    requires_techniques: [],
    requires_equipment_tags: [],
    result_on_failure: {},
    log_text_failure: "",
  };
}

function createCleanSingleOutcomeOption(
  option: EventOptionInput | undefined,
  eventIdSeed: string,
  eventNameSeed: string
): EventOptionInput {
  const normalized = normalizeOption(option ?? createEmptyOption(1));
  return {
    ...createEmptyOption(1),
    ...normalized,
    option_id: normalized.option_id || `${eventIdSeed}_default`,
    option_text: SINGLE_OUTCOME_TEXT,
    sort_order: 1,
    is_default: true,
    success_rate_formula: "",
    requires_resources: {},
    requires_statuses: [],
    requires_techniques: [],
    requires_equipment_tags: [],
    result_on_success: {},
    result_on_failure: {},
    next_event_id: normalized.next_event_id ?? null,
    log_text_success: normalized.log_text_success || eventNameSeed || "",
    log_text_failure: "",
  };
}

function collectOptionIdsToDelete({
  existingOptionIds,
  removedOptionIds,
  normalizedOptions,
  isSingleOutcome,
}: {
  existingOptionIds: string[];
  removedOptionIds: string[];
  normalizedOptions: EventOptionInput[];
  isSingleOutcome: boolean;
}): string[] {
  const ids = new Set(removedOptionIds);
  if (!isSingleOutcome) {
    return [...ids];
  }

  const keepId = normalizedOptions[0]?.option_id;
  for (const existingOptionId of existingOptionIds) {
    if (existingOptionId !== keepId) {
      ids.add(existingOptionId);
    }
  }
  return [...ids];
}

function createEmptyTemplate(eventType = "cultivation"): EventTemplateInput {
  return {
    event_id: "",
    event_name: "",
    event_type: eventType,
    outcome_type: eventType,
    risk_level: "normal",
    trigger_sources: ["global"],
    choice_pattern: "binary_choice",
    title_text: "",
    body_text: "",
    realm_min: null,
    realm_max: null,
    region: "",
    weight: 1,
    is_repeatable: true,
    cooldown_rounds: 0,
    max_trigger_per_run: 999999,
    required_statuses: [],
    excluded_statuses: [],
    required_techniques: [],
    required_equipment_tags: [],
    required_resources: {},
    required_rebirth_count: 0,
    required_karma_min: null,
    required_luck_min: 0,
    flags: [],
    option_ids: [],
  };
}

function createEmptyOption(sortOrder: number): EventOptionInput {
  return {
    option_id: "",
    option_text: "",
    sort_order: sortOrder,
    is_default: sortOrder === 1,
    requires_resources: {},
    requires_statuses: [],
    requires_techniques: [],
    requires_equipment_tags: [],
    success_rate_formula: "",
    result_on_success: {},
    result_on_failure: {},
    next_event_id: null,
    log_text_success: "",
    log_text_failure: "",
  };
}

function normalizeTemplate(template: EventTemplateInput): EventTemplateInput {
  return {
    ...createEmptyTemplate(template.event_type || "cultivation"),
    ...template,
    trigger_sources: template.trigger_sources ?? [],
    required_statuses: template.required_statuses ?? [],
    excluded_statuses: template.excluded_statuses ?? [],
    required_techniques: template.required_techniques ?? [],
    required_equipment_tags: template.required_equipment_tags ?? [],
    required_resources: template.required_resources ?? {},
    flags: template.flags ?? [],
  };
}

function normalizeOption(option: EventOptionInput): EventOptionInput {
  return {
    ...createEmptyOption(option.sort_order || 1),
    ...option,
    requires_resources: option.requires_resources ?? {},
    requires_statuses: option.requires_statuses ?? [],
    requires_techniques: option.requires_techniques ?? [],
    requires_equipment_tags: option.requires_equipment_tags ?? [],
    success_rate_formula: option.success_rate_formula ?? "",
    next_event_id: option.next_event_id ?? null,
    log_text_success: option.log_text_success ?? "",
    log_text_failure: option.log_text_failure ?? "",
    result_on_success: option.result_on_success ?? {},
    result_on_failure: option.result_on_failure ?? {},
  };
}





