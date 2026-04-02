import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  fetchDwellingFacilities,
  fetchDwellingFacilityDetail,
  reloadDwelling,
  updateDwellingFacility,
  type DwellingFacilityInput,
  type DwellingFacilityListItem,
  type DwellingLevelInput,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { ResourceRecordEditor } from "../components/ResourceRecordEditor";

type DwellingListPageProps = {
  refreshToken?: number;
  onEditFacility?: (facilityId: string) => void;
};

type DwellingPanel = "overview" | "levels" | "effects";

type SpecialEffectOption = {
  value: string;
  label: string;
};

const facilityTypeOptions = [
  { value: "production", label: "生产设施" },
  { value: "function", label: "功能设施" },
  { value: "boost", label: "增益设施" },
];

const specialEffectMap: Record<string, SpecialEffectOption[]> = {
  spirit_gathering_array: [
    { value: "breakthrough_bonus_rate", label: "突破加成比例" },
    { value: "mine_spirit_stone_bonus_rate", label: "矿洞灵石加成比例" },
  ],
};

export function DwellingListPage({ refreshToken = 0 }: DwellingListPageProps) {
  const [items, setItems] = useState<DwellingFacilityListItem[]>([]);
  const [facility, setFacility] = useState<DwellingFacilityInput | null>(null);
  const [selectedFacilityId, setSelectedFacilityId] = useState<string | null>(null);
  const [drawerPanel, setDrawerPanel] = useState<DwellingPanel | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<number>(1);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const response = await fetchDwellingFacilities();
        if (!isMounted) {
          return;
        }
        const nextItems = response.items ?? [];
        setItems(nextItems);
        setStatusMessage(null);
        setErrorMessage(null);
        setSelectedFacilityId((current) => {
          if (current && nextItems.some((item) => item.facility_id === current)) {
            return current;
          }
          return nextItems[0]?.facility_id ?? null;
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

    void load();

    return () => {
      isMounted = false;
    };
  }, [refreshToken]);

  useEffect(() => {
    let isMounted = true;

    async function loadDetail() {
      if (!selectedFacilityId) {
        setFacility(null);
        return;
      }

      try {
        const detail = await fetchDwellingFacilityDetail(selectedFacilityId);
        if (!isMounted) {
          return;
        }
        setFacility(normalizeFacility(detail));
        setSelectedLevel(detail.levels[0]?.level ?? 1);
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
  }, [selectedFacilityId]);

  const currentLevel = useMemo(
    () => facility?.levels.find((level) => level.level === selectedLevel) ?? facility?.levels[0] ?? null,
    [facility, selectedLevel]
  );

  const nextLevel = facility ? Math.max(...facility.levels.map((level) => level.level)) + 1 : 1;
  const allowedSpecialEffects = useMemo(
    () => getSpecialEffectOptions(facility?.facility_id, currentLevel?.special_effects),
    [currentLevel?.special_effects, facility?.facility_id]
  );

  function updateFacility(nextFacility: DwellingFacilityInput) {
    const normalized = normalizeFacility(nextFacility);
    setFacility(normalized);
    setItems((current) =>
      current.map((item) =>
        item.facility_id === normalized.facility_id
          ? {
              ...item,
              display_name: normalized.display_name,
              facility_type: normalized.facility_type,
              summary: normalized.summary,
              max_level: Math.max(...normalized.levels.map((level) => level.level)),
              level_count: normalized.levels.length,
            }
          : item
      )
    );
  }

  function handleSelectedFacilityChange(value: string) {
    if (!value) {
      return;
    }
    setSelectedFacilityId(value);
  }

  function handleFacilityFieldChange(
    field: keyof Omit<DwellingFacilityInput, "levels" | "facility_id">,
    value: string
  ) {
    if (!facility) {
      return;
    }
    updateFacility({
      ...facility,
      [field]: value,
    });
  }

  function handleLevelFieldChange<K extends keyof DwellingLevelInput>(
    levelNumber: number,
    field: K,
    value: DwellingLevelInput[K]
  ) {
    if (!facility) {
      return;
    }
    updateFacility({
      ...facility,
      levels: facility.levels.map((level) =>
        level.level === levelNumber ? { ...level, [field]: value } : level
      ),
    });
  }

  function handleAddLevel() {
    if (!facility) {
      return;
    }
    updateFacility({
      ...facility,
      levels: [
        ...facility.levels,
        {
          level: nextLevel,
          entry_cost: {},
          maintenance_cost: {},
          resource_yields: {},
          cultivation_exp_gain: 0,
          special_effects: {},
        },
      ],
    });
    setSelectedLevel(nextLevel);
    setDrawerPanel("levels");
  }

  async function handleSave() {
    if (!facility) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const payload = normalizeFacility(facility);
      const savedFacility = await updateDwellingFacility(payload.facility_id, payload);
      updateFacility(savedFacility);
      const result = await reloadDwelling();
      setStatusMessage(`已保存并自动重载运行时，当前载入 ${result.facility_count} 项洞府设施。`);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载洞府配置...</div>;
  }

  return (
    <>
      <ConfigWorkbench
        className="config-workbench--compact"
        title="洞府配置"
        description="左侧切换设施与保存，右侧通过模块按钮进入抽屉编辑。"
        hideHero
        registryTitle="设施清单"
        registryContent={
          <div className="section-grid">
            <div className="event-compact-toolbar">
              <div className="event-compact-toolbar__grid">
                <label className="field field--full">
                  <span className="field__label">当前设施</span>
                  <select
                    aria-label="当前设施"
                    value={selectedFacilityId ?? ""}
                    onChange={(event) => handleSelectedFacilityChange(event.target.value)}
                  >
                    <option value="">选择已有设施</option>
                    {items.map((item) => (
                      <option key={item.facility_id} value={item.facility_id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field field--full">
                  <span className="field__label">新增等级</span>
                  <select aria-label="新增等级" value={String(nextLevel)} disabled={!facility}>
                    <option value={String(nextLevel)}>{`新增到 Lv${nextLevel}`}</option>
                  </select>
                </label>
              </div>

              <div className="event-compact-toolbar__actions">
                <button
                  className="button-secondary"
                  type="button"
                  onClick={handleAddLevel}
                  disabled={!facility}
                >
                  追加等级
                </button>
                <button
                  className="button-primary event-compact-toolbar__save"
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={!facility}
                >
                  保存设施
                </button>
              </div>
            </div>

            {items.length === 0 ? <div className="empty-state">当前没有可维护的洞府设施。</div> : null}
          </div>
        }
        detailTitle={facility?.display_name || "设施详情"}
        detailContent={
          facility ? (
            <div className="section-grid">
              {errorMessage ? (
                <div className="status-card__banner status-card__banner--error" role="alert">
                  {errorMessage}
                </div>
              ) : null}
              {statusMessage ? <div className="status-card__banner">{statusMessage}</div> : null}

              <div className="event-detail-chips">
                <span className="event-detail-chip">
                  <small>设施类别</small>
                  <strong>{formatFacilityType(facility.facility_type)}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>当前等级</small>
                  <strong>{`Lv${currentLevel?.level ?? 1}`}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>等级数</small>
                  <strong>{`${facility.levels.length} 个等级`}</strong>
                </span>
              </div>

              <div className="event-module-tabs" role="tablist" aria-label="设施详情模块">
                <button
                  aria-pressed={drawerPanel === "overview"}
                  className={drawerPanel === "overview" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("overview")}
                >
                  设施信息
                </button>
                <button
                  aria-pressed={drawerPanel === "levels"}
                  className={drawerPanel === "levels" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("levels")}
                >
                  等级配置
                </button>
                <button
                  aria-pressed={drawerPanel === "effects"}
                  className={drawerPanel === "effects" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("effects")}
                >
                  特殊效果
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state">左侧选择设施后，可在这里打开对应模块进行编辑。</div>
          )
        }
        actionBar={undefined}
      />

      {facility && drawerPanel ? (
        <ConfigEditorDrawer
          description={getDwellingPanelDescription(drawerPanel)}
          title={getDwellingPanelTitle(drawerPanel)}
          onClose={() => setDrawerPanel(null)}
        >
          {drawerPanel === "overview" ? (
            <div className="field-grid field-grid--three">
              <label className="field">
                <span className="field__label">设施名称</span>
                <input
                  aria-label="设施名称"
                  value={facility.display_name}
                  onChange={(event) => handleFacilityFieldChange("display_name", event.target.value)}
                />
              </label>
              <label className="field">
                <span className="field__label">设施类别</span>
                <select
                  aria-label="设施类别"
                  value={facility.facility_type}
                  onChange={(event) => handleFacilityFieldChange("facility_type", event.target.value)}
                >
                  {facilityTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="field__label">内部标识</span>
                <input aria-label="内部标识" readOnly value={facility.facility_id} />
              </label>
              <label className="field field--full">
                <span className="field__label">设施摘要</span>
                <textarea
                  aria-label="设施摘要"
                  value={facility.summary}
                  onChange={(event) => handleFacilityFieldChange("summary", event.target.value)}
                />
              </label>
              <label className="field field--full">
                <span className="field__label">功能说明</span>
                <textarea
                  aria-label="功能说明"
                  value={facility.function_unlock_text}
                  onChange={(event) =>
                    handleFacilityFieldChange("function_unlock_text", event.target.value)
                  }
                />
              </label>
            </div>
          ) : drawerPanel === "levels" && currentLevel ? (
            <div className="section-grid">
              <DwellingLevelToolbar
                currentLevel={selectedLevel}
                levels={facility.levels}
                nextLevel={nextLevel}
                onAddLevel={handleAddLevel}
                onLevelChange={setSelectedLevel}
              />

              <ResourceRecordEditor
                addLabel="新增成本"
                emptyMessage="当前等级还没有进入该等级的成本。"
                label="进入该等级成本"
                value={currentLevel.entry_cost}
                onChange={(value) => handleLevelFieldChange(currentLevel.level, "entry_cost", value)}
              />
              <ResourceRecordEditor
                addLabel="新增维护项"
                emptyMessage="当前等级还没有维护成本。"
                label="维护成本"
                value={currentLevel.maintenance_cost}
                onChange={(value) =>
                  handleLevelFieldChange(currentLevel.level, "maintenance_cost", value)
                }
              />
              <ResourceRecordEditor
                addLabel="新增产出项"
                emptyMessage="当前等级还没有资源产出。"
                label="资源产出"
                value={currentLevel.resource_yields}
                onChange={(value) =>
                  handleLevelFieldChange(currentLevel.level, "resource_yields", value)
                }
              />
              <label className="field">
                <span className="field__label">修为收益</span>
                <input
                  aria-label="修为收益"
                  min={0}
                  type="number"
                  value={currentLevel.cultivation_exp_gain}
                  onChange={(event) =>
                    handleLevelFieldChange(
                      currentLevel.level,
                      "cultivation_exp_gain",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
            </div>
          ) : drawerPanel === "effects" && currentLevel ? (
            <div className="section-grid">
              <DwellingLevelToolbar
                currentLevel={selectedLevel}
                levels={facility.levels}
                nextLevel={nextLevel}
                onAddLevel={handleAddLevel}
                onLevelChange={setSelectedLevel}
              />

              <SpecialEffectEditor
                effectOptions={allowedSpecialEffects}
                facilityId={facility.facility_id}
                level={currentLevel}
                onChange={(value) => handleLevelFieldChange(currentLevel.level, "special_effects", value)}
              />
            </div>
          ) : (
            <div className="empty-state">当前设施还没有可编辑的等级配置。</div>
          )}
        </ConfigEditorDrawer>
      ) : null}
    </>
  );
}

function ConfigEditorDrawer({
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

function DwellingLevelToolbar({
  currentLevel,
  levels,
  nextLevel,
  onAddLevel,
  onLevelChange,
}: {
  currentLevel: number;
  levels: DwellingLevelInput[];
  nextLevel: number;
  onAddLevel: () => void;
  onLevelChange: (level: number) => void;
}) {
  return (
    <div className="event-compact-toolbar">
      <div className="event-compact-toolbar__grid">
        <label className="field">
          <span className="field__label">当前等级</span>
          <select
            aria-label="当前等级"
            value={String(currentLevel)}
            onChange={(event) => onLevelChange(Number(event.target.value))}
          >
            {levels.map((level) => (
              <option key={level.level} value={String(level.level)}>
                {`Lv${level.level}`}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span className="field__label">新增等级</span>
          <select aria-label="新增等级" value={String(nextLevel)} disabled>
            <option value={String(nextLevel)}>{`新增到 Lv${nextLevel}`}</option>
          </select>
        </label>
      </div>

      <div className="event-compact-toolbar__actions">
        <button className="button-secondary" type="button" onClick={onAddLevel}>
          追加等级
        </button>
      </div>
    </div>
  );
}

function getDwellingPanelTitle(panel: DwellingPanel): string {
  switch (panel) {
    case "overview":
      return "设施信息";
    case "levels":
      return "等级配置";
    case "effects":
      return "特殊效果";
  }
}

function getDwellingPanelDescription(panel: DwellingPanel): string {
  switch (panel) {
    case "overview":
      return "编辑设施名称、类别和说明文本。";
    case "levels":
      return "编辑建造成本、维护成本、资源产出与修为收益。";
    case "effects":
      return "编辑当前等级开放的特殊效果项。";
  }
}

function normalizeFacility(facility: DwellingFacilityInput): DwellingFacilityInput {
  return {
    ...facility,
    display_name: String(facility.display_name ?? "").trim(),
    facility_type: String(facility.facility_type ?? "production").trim(),
    summary: String(facility.summary ?? "").trim(),
    function_unlock_text: String(facility.function_unlock_text ?? "").trim(),
    levels: [...(facility.levels ?? [])]
      .map((level, index) => ({
        level: Number(level.level ?? index + 1) || index + 1,
        entry_cost: level.entry_cost ?? {},
        maintenance_cost: level.maintenance_cost ?? {},
        resource_yields: level.resource_yields ?? {},
        cultivation_exp_gain: Number(level.cultivation_exp_gain ?? 0) || 0,
        special_effects: level.special_effects ?? {},
      }))
      .sort((left, right) => left.level - right.level),
  };
}

function formatFacilityType(value: string): string {
  return facilityTypeOptions.find((option) => option.value === value)?.label ?? value;
}

function getSpecialEffectOptions(
  facilityId: string | undefined,
  currentEffects: Record<string, number> | undefined
): SpecialEffectOption[] {
  const knownOptions = specialEffectMap[facilityId ?? ""] ?? [];
  const unknownOptions = Object.keys(currentEffects ?? {})
    .filter((key) => !knownOptions.some((option) => option.value === key))
    .map((key) => ({ value: key, label: key }));
  return [...knownOptions, ...unknownOptions];
}

function SpecialEffectEditor({
  facilityId,
  level,
  effectOptions,
  onChange,
}: {
  facilityId: string;
  level: DwellingLevelInput;
  effectOptions: SpecialEffectOption[];
  onChange: (value: Record<string, number>) => void;
}) {
  const entries = Object.entries(level.special_effects ?? {});
  const usedKeys = entries.map(([key]) => key);
  const canAdd = effectOptions.some((option) => !usedKeys.includes(option.value));

  function updateEntries(nextEntries: Array<[string, number]>) {
    onChange(
      Object.fromEntries(nextEntries.filter(([key, amount]) => key && Number.isFinite(amount)))
    );
  }

  function handleAdd() {
    const nextOption = effectOptions.find((option) => !usedKeys.includes(option.value));
    if (!nextOption) {
      return;
    }
    updateEntries([...entries, [nextOption.value, 0]]);
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
    <div className="section-grid">
      <div className="event-detail-chips">
        <span className="event-detail-chip">
          <small>当前设施</small>
          <strong>{facilityId}</strong>
        </span>
        <span className="event-detail-chip">
          <small>当前等级</small>
          <strong>{`Lv${level.level}`}</strong>
        </span>
      </div>

      <div className="field field--full">
        <div className="field__label">
          <span>特殊效果</span>
          <button
            className="button-secondary"
            disabled={!canAdd}
            type="button"
            onClick={handleAdd}
          >
            新增效果
          </button>
        </div>

        {entries.length > 0 ? (
          <div className="resource-editor__stack">
            {entries.map(([effectKey, amount], index) => (
              <div key={`${effectKey}-${index}`} className="resource-row">
                <label className="field">
                  <span className="field__hint">效果项</span>
                  <select
                    aria-label={`特殊效果项${index + 1}`}
                    value={effectKey}
                    onChange={(event) => handleKeyChange(index, event.target.value)}
                  >
                    {effectOptions.map((option) => {
                      const disabled = usedKeys.includes(option.value) && option.value !== effectKey;
                      return (
                        <option key={option.value} disabled={disabled} value={option.value}>
                          {option.label}
                        </option>
                      );
                    })}
                  </select>
                </label>

                <label className="field">
                  <span className="field__hint">效果值</span>
                  <input
                    aria-label={`特殊效果值${index + 1}`}
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
            ))}
          </div>
        ) : (
          <div className="resource-editor__empty">
            {effectOptions.length > 0 ? "当前等级还没有特殊效果项。" : "当前设施没有可配置的特殊效果。"}
          </div>
        )}
      </div>
    </div>
  );
}
