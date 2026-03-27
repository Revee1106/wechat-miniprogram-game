import { useEffect, useState } from "react";

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
  validateEvents,
  type EventListItem,
  type EventOptionInput,
  type EventTemplateInput,
  type ValidationResponse,
} from "../api/client";
import { EventOptionEditor } from "../components/EventOptionEditor";
import { EventTemplateForm } from "../components/EventTemplateForm";
import {
  eventTypeOptions,
  formatTriggerSources,
  getOptionLabel,
  outcomeTypeOptions,
  riskLevelOptions,
} from "../components/FieldLabelMap";
import { SingleOutcomeEditor } from "../components/SingleOutcomeEditor";
import { ValidationPanel } from "../components/ValidationPanel";
import { getEventTypeTotalWeight } from "../utils/eventTypeWeight";

type EventEditorPageProps = {
  eventId?: string;
  onBack: () => void;
  onSaved: (eventId: string) => void;
};

type EditorPanel = "identity" | "trigger" | "requirements" | "options" | "singleOutcome" | null;

const PANEL_TITLES: Record<Exclude<EditorPanel, null>, string> = {
  identity: "基础信息",
  trigger: "触发规则",
  requirements: "前置条件",
  options: "选项编排",
  singleOutcome: "单一结果",
};

const SINGLE_OUTCOME_TEXT = "完成事件";

export function EventEditorPage({
  eventId,
  onBack,
  onSaved,
}: EventEditorPageProps) {
  const [template, setTemplate] = useState<EventTemplateInput>(createEmptyTemplate());
  const [options, setOptions] = useState<EventOptionInput[]>([createEmptyOption(1)]);
  const [existingOptionIds, setExistingOptionIds] = useState<string[]>([]);
  const [removedOptionIds, setRemovedOptionIds] = useState<string[]>([]);
  const [eventLibrary, setEventLibrary] = useState<EventListItem[]>([]);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activePanel, setActivePanel] = useState<EditorPanel>(null);

  const isSingleOutcome = template.choice_pattern === "single_outcome";
  const singleOutcomeOption = normalizeSingleOutcomeOption(options[0], template.event_id || "event");
  const currentTypeTotalWeight = getEventTypeTotalWeight(eventLibrary, template);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      if (!eventId) {
        const library = await fetchEvents();
        if (!isMounted) {
          return;
        }
        setTemplate(createEmptyTemplate());
        setOptions([createEmptyOption(1)]);
        setExistingOptionIds([]);
        setRemovedOptionIds([]);
        setEventLibrary(library.items ?? []);
        setValidation(null);
        setStatusMessage(null);
        setErrorMessage(null);
        setActivePanel(null);
        return;
      }

      setIsLoading(true);
      try {
        const [detail, library] = await Promise.all([
          fetchEventDetail(eventId),
          fetchEvents(),
        ]);
        if (!isMounted) {
          return;
        }
        setTemplate(normalizeTemplate(detail.template));
        setOptions(
          detail.options.length > 0
            ? detail.options.map(normalizeOption)
            : [createEmptyOption(1)]
        );
        setExistingOptionIds(detail.options.map((option) => option.option_id));
        setRemovedOptionIds([]);
        setEventLibrary(library.items ?? []);
        setValidation(null);
        setStatusMessage(null);
        setErrorMessage(null);
        setActivePanel(null);
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

    void load();

    return () => {
      isMounted = false;
    };
  }, [eventId]);

  async function handleSave() {
    setErrorMessage(null);
    setStatusMessage(null);

    const eventIdValue = template.event_id.trim();
    const eventNameValue = template.event_name.trim();

    if (!eventIdValue || !eventNameValue) {
      setErrorMessage("事件编号和事件名称不能为空。");
      return;
    }

    const normalizedOptions = buildPreparedOptions({
      eventIdValue,
      eventNameValue,
      isSingleOutcome,
      options,
    });
    const optionIdsToDelete = collectOptionIdsToDelete({
      existingOptionIds,
      removedOptionIds,
      normalizedOptions,
      isSingleOutcome,
    });

    if (normalizedOptions.length === 0) {
      setErrorMessage("至少需要保留一个结果配置。");
      return;
    }
    if (normalizedOptions.some((option) => !option.option_id || !option.option_text)) {
      setErrorMessage("每个结果配置都需要编号和文案。");
      return;
    }

    const templatePayload: EventTemplateInput = {
      ...normalizeTemplate(template),
      event_id: eventIdValue,
      event_name: eventNameValue,
      title_text: template.title_text.trim() || eventNameValue,
      body_text: template.body_text,
      option_ids: normalizedOptions.map((option) => option.option_id),
    };

    try {
      if (eventId) {
        await updateEvent(eventId, templatePayload);
      } else {
        await createEvent(templatePayload);
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
      setEventLibrary((current) => {
        const nextItem = {
          event_id: templatePayload.event_id,
          event_name: templatePayload.event_name,
          event_type: templatePayload.event_type,
          outcome_type: templatePayload.outcome_type,
          risk_level: templatePayload.risk_level,
          trigger_sources: templatePayload.trigger_sources,
          region: templatePayload.region,
          realm_min: templatePayload.realm_min,
          realm_max: templatePayload.realm_max,
          option_ids: templatePayload.option_ids,
          is_repeatable: templatePayload.is_repeatable,
          weight: templatePayload.weight,
        };
        const withoutCurrent = current.filter((item) => item.event_id !== templatePayload.event_id);
        return [...withoutCurrent, nextItem];
      });
      try {
        const result = await reloadEvents();
        setStatusMessage(
          `事件已保存，并已重载运行时。当前共载入 ${result.template_count} 条事件和 ${result.option_count} 个选项。`
        );
      } catch (reloadError) {
        setStatusMessage("事件已保存，但运行时重载失败，请手动点击“重载运行时”。");
        setErrorMessage((reloadError as Error).message);
      }
      onSaved(eventIdValue);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleValidate() {
    try {
      setErrorMessage(null);
      setValidation(await validateEvents());
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleReload() {
    try {
      setErrorMessage(null);
      const result = await reloadEvents();
      setStatusMessage(
        `运行时配置已重载，共载入 ${result.template_count} 条事件和 ${result.option_count} 个选项。`
      );
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!eventId) {
      return;
    }
    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteEvent(eventId);
      onBack();
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  function handleTemplateChange<K extends keyof EventTemplateInput>(
    field: K,
    value: EventTemplateInput[K]
  ) {
    setTemplate((current) => {
      if (field === "choice_pattern") {
        const nextPattern = String(value);
        if (nextPattern === "single_outcome" && current.choice_pattern !== "single_outcome") {
          setOptions((currentOptions) => [
            createCleanSingleOutcomeOption(
              currentOptions[0],
              current.event_id || "event",
              current.event_name
            ),
          ]);
        }
      }

      return {
        ...current,
        [field]: value,
      };
    });
  }

  function handleOptionChange(
    index: number,
    field: keyof EventOptionInput,
    value: EventOptionInput[keyof EventOptionInput]
  ) {
    setOptions((current) =>
      current.map((option, optionIndex) =>
        optionIndex === index
          ? { ...option, [field]: value }
          : option
      )
    );
  }

  function handleSingleOutcomeChange<K extends keyof EventOptionInput>(
    field: K,
    value: EventOptionInput[K]
  ) {
    setOptions((current) => {
      const base = normalizeSingleOutcomeOption(current[0], template.event_id || "event");
      const nextFirst = {
        ...base,
        [field]: value,
      };
      return [nextFirst];
    });
  }

  function handleAddOption() {
    setOptions((current) => [...current, createEmptyOption(current.length + 1)]);
  }

  function handleRemoveOption(index: number) {
    setOptions((current) => {
      const target = current[index];
      if (target?.option_id && existingOptionIds.includes(target.option_id)) {
        setRemovedOptionIds((removed) =>
          removed.includes(target.option_id)
            ? removed
            : [...removed, target.option_id]
        );
      }
      const next = current.filter((_, optionIndex) => optionIndex !== index);
      return next.length > 0 ? next : [createEmptyOption(1)];
    });
  }

  if (isLoading) {
    return <div className="page-loading">正在装载事件内容...</div>;
  }

  return (
    <main className="section-grid workbench-page">
      <section className="hero-panel">
        <div className="section-card__body">
          <div>
            <h1>{eventId ? "事件工坊" : "新建事件"}</h1>
            <p>{eventId ? "按模块进入二级编辑层，减少长页滚动。" : "先写基础信息，再依次补全规则与结果。"}</p>
          </div>
          <div className="chip-row">
            <span className="chip">事件类型 {getOptionLabel(eventTypeOptions, template.event_type)}</span>
            <span className="chip">结果倾向 {getOptionLabel(outcomeTypeOptions, template.outcome_type)}</span>
            <span className="chip">风险 {getOptionLabel(riskLevelOptions, template.risk_level)}</span>
            <span className="chip chip--soft">触发 {formatTriggerSources(template.trigger_sources)}</span>
            <span className="chip chip--soft">同类总权重 {currentTypeTotalWeight}</span>
          </div>
        </div>

        <div className="section-card__body">
          <div className="meta-list">
            <span className="chip chip--soft">事件编号 {template.event_id || "未填写"}</span>
            <span className="chip chip--soft">事件名称 {template.event_name || "未填写"}</span>
            <span className="chip chip--soft">
              当前模式 {isSingleOutcome ? "单一结果" : "选项编排"}
            </span>
          </div>
          <p className="field__hint">
            你只需要进入正在修改的模块，完成后返回工作台。底部操作条会一直保留在视口内。
          </p>
        </div>
      </section>

      <section className="workbench-grid">
        <WorkbenchCard
          title="基础信息"
          description="事件编号、名称、标题和正文文案。"
          summary={`${template.event_name || "未命名事件"} · ${template.title_text || "未写标题"}`}
          buttonText="编辑基础信息"
          onClick={() => setActivePanel("identity")}
        />
        <WorkbenchCard
          title="触发规则"
          description="风险、模式、触发来源、境界与冷却。"
          summary={`${getOptionLabel(riskLevelOptions, template.risk_level)} · ${template.region || "不限地域"}`}
          buttonText="编辑触发规则"
          onClick={() => setActivePanel("trigger")}
        />
        <WorkbenchCard
          title="前置条件"
          description="资源、状态、功法、因果与气运门槛。"
          summary={`${Object.keys(template.required_resources ?? {}).length} 项资源条件 · ${(template.required_statuses ?? []).length} 项状态条件`}
          buttonText="编辑前置条件"
          onClick={() => setActivePanel("requirements")}
        />
        {isSingleOutcome ? (
          <WorkbenchCard
            title="单一结果"
            description="单一结果模式下只维护一条默认结算。"
            summary={`${singleOutcomeOption.log_text_success || "未写结果日志"} · 后续 ${singleOutcomeOption.next_event_id || "无"}`}
            buttonText="编辑单一结果"
            onClick={() => setActivePanel("singleOutcome")}
          />
        ) : (
          <WorkbenchCard
            title="选项编排"
            description="维护多个选项及其成功率、后续事件和结果。"
            summary={`共 ${options.length} 个选项 · 默认 ${options.find((option) => option.is_default)?.option_text || "未设定"}`}
            buttonText="编辑选项编排"
            onClick={() => setActivePanel("options")}
          />
        )}
      </section>

      <ValidationPanel
        errorMessage={errorMessage}
        statusMessage={statusMessage}
        validation={validation}
      />

      <footer className="editor-footer">
        <div className="editor-footer__meta">
          <strong>{template.event_name || "未命名事件"}</strong>
          <span>{eventId ? "编辑中" : "新建中"} · {template.event_id || "等待填写编号"}</span>
        </div>
        <div className="toolbar">
          <button className="button-secondary" type="button" onClick={onBack}>
            返回事件库
          </button>
          <button className="button-accent" type="button" onClick={handleValidate}>
            校验配置
          </button>
          <button className="button-secondary" type="button" onClick={handleReload}>
            重载运行时
          </button>
          <button className="button-primary" type="button" onClick={handleSave}>
            保存事件
          </button>
          {eventId ? (
            <button className="button-danger" type="button" onClick={handleDelete}>
              删除事件
            </button>
          ) : null}
        </div>
      </footer>

      {activePanel ? (
        <div className="editor-dialog-backdrop" onClick={() => setActivePanel(null)}>
          <section
            aria-label={PANEL_TITLES[activePanel]}
            aria-modal="true"
            className="editor-dialog"
            role="dialog"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="editor-dialog__header">
              <div>
                <h2>{PANEL_TITLES[activePanel]}</h2>
                <p>完成当前模块后返回工作台即可，改动会先保留在本地状态中。</p>
              </div>
              <button className="button-secondary" type="button" onClick={() => setActivePanel(null)}>
                完成编辑
              </button>
            </header>
            <div className="editor-dialog__body">
              {activePanel === "identity" ? (
                <EventTemplateForm
                  isNew={!eventId}
                  onChange={handleTemplateChange}
                  sections={["identity"]}
                  template={template}
                />
              ) : null}
              {activePanel === "trigger" ? (
                <EventTemplateForm
                  isNew={!eventId}
                  onChange={handleTemplateChange}
                  sections={["trigger"]}
                  template={template}
                />
              ) : null}
              {activePanel === "requirements" ? (
                <EventTemplateForm
                  isNew={!eventId}
                  onChange={handleTemplateChange}
                  sections={["requirements"]}
                  template={template}
                />
              ) : null}
              {activePanel === "options" ? (
                <EventOptionEditor
                  existingOptionIds={existingOptionIds}
                  onAddOption={handleAddOption}
                  onChangeOption={handleOptionChange}
                  onRemoveOption={handleRemoveOption}
                  options={options}
                />
              ) : null}
              {activePanel === "singleOutcome" ? (
                <SingleOutcomeEditor
                  onChange={handleSingleOutcomeChange}
                  option={singleOutcomeOption}
                />
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}

type WorkbenchCardProps = {
  title: string;
  description: string;
  summary: string;
  buttonText: string;
  onClick: () => void;
};

function WorkbenchCard({
  title,
  description,
  summary,
  buttonText,
  onClick,
}: WorkbenchCardProps) {
  return (
    <article className="workbench-card">
      <div className="workbench-card__content">
        <h2>{title}</h2>
        <p>{description}</p>
        <div className="chip-row">
          <span className="chip chip--soft">{summary}</span>
        </div>
      </div>
      <button className="button-primary" type="button" onClick={onClick}>
        {buttonText}
      </button>
    </article>
  );
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

function createEmptyTemplate(): EventTemplateInput {
  return {
    event_id: "",
    event_name: "",
    event_type: "cultivation",
    outcome_type: "cultivation",
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
    ...createEmptyTemplate(),
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
