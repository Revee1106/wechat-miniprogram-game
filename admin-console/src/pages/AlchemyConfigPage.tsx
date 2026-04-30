import { useEffect, useMemo, useState } from "react";

import {
  createAlchemyRecipe,
  deleteAlchemyRecipe,
  fetchAlchemyLevels,
  fetchAlchemyRecipes,
  reloadAlchemy,
  updateAlchemyLevels,
  updateAlchemyRecipe,
  type AlchemyLevelInput,
  type AlchemyRecipeInput,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { ResourceRecordEditor } from "../components/ResourceRecordEditor";

const DRAFT_RECIPE_ID = "__draft_alchemy_recipe__";

type DetailTab = "recipe" | "levels";

const effectTypeOptions = [
  { value: "cultivation_exp", label: "修为增长" },
  { value: "hp_restore", label: "气血恢复" },
  { value: "lifespan_restore", label: "寿元恢复" },
  { value: "status_penalty_reduce", label: "状态惩罚减免" },
  { value: "breakthrough_bonus", label: "突破辅助加成" },
];

const qualityProfileOptions = [
  { key: "low", label: "下品", color: "white" },
  { key: "mid", label: "中品", color: "green" },
  { key: "high", label: "上品", color: "blue" },
  { key: "supreme", label: "极品", color: "purple" },
] as const;

export function AlchemyConfigPage() {
  const [levels, setLevels] = useState<AlchemyLevelInput[]>([]);
  const [recipes, setRecipes] = useState<AlchemyRecipeInput[]>([]);
  const [draftRecipe, setDraftRecipe] = useState<AlchemyRecipeInput | null>(null);
  const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
  const [selectedLevelIndex, setSelectedLevelIndex] = useState(0);
  const [pendingRecipeId, setPendingRecipeId] = useState("");
  const [activeTab, setActiveTab] = useState<DetailTab>("recipe");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const [levelsResponse, recipesResponse] = await Promise.all([
          fetchAlchemyLevels(),
          fetchAlchemyRecipes(),
        ]);
        if (!isMounted) {
          return;
        }
        const nextLevels = normalizeLevels(levelsResponse.items ?? []);
        const nextRecipes = (recipesResponse.items ?? []).map(normalizeRecipe);
        setLevels(nextLevels);
        setRecipes(nextRecipes);
        setDraftRecipe(null);
        setStatusMessage(null);
        setErrorMessage(null);
        setSelectedRecipeId((current) => {
          if (current === DRAFT_RECIPE_ID) {
            return current;
          }
          if (current && nextRecipes.some((item) => item.recipe_id === current)) {
            return current;
          }
          return nextRecipes[0]?.recipe_id ?? null;
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
  }, []);

  const selectedRecipe = useMemo(() => {
    if (selectedRecipeId === DRAFT_RECIPE_ID) {
      return draftRecipe;
    }
    return recipes.find((item) => item.recipe_id === selectedRecipeId) ?? null;
  }, [draftRecipe, recipes, selectedRecipeId]);

  const isDraft = selectedRecipeId === DRAFT_RECIPE_ID;
  const normalizedSelectedLevelIndex =
    levels.length > 0 ? Math.min(selectedLevelIndex, levels.length - 1) : 0;
  const selectedLevel = levels[normalizedSelectedLevelIndex] ?? null;

  function updateSelectedRecipe(nextRecipe: AlchemyRecipeInput) {
    if (isDraft) {
      setDraftRecipe(nextRecipe);
      return;
    }
    setRecipes((current) =>
      current.map((item) =>
        item.recipe_id === nextRecipe.recipe_id ? normalizeRecipe(nextRecipe) : item
      )
    );
  }

  function handleRecipeFieldChange<K extends keyof AlchemyRecipeInput>(
    field: K,
    value: AlchemyRecipeInput[K]
  ) {
    if (!selectedRecipe) {
      return;
    }
    updateSelectedRecipe({
      ...selectedRecipe,
      [field]: value,
    });
  }

  function handleQualityProfileChange(
    qualityKey: string,
    field: "display_name" | "color" | "base_weight" | "per_level_weight" | "effect_multiplier",
    value: string | number
  ) {
    if (!selectedRecipe) {
      return;
    }
    const currentProfiles = normalizeQualityProfiles(selectedRecipe.quality_profiles);
    updateSelectedRecipe({
      ...selectedRecipe,
      quality_profiles: {
        ...currentProfiles,
        [qualityKey]: {
          ...currentProfiles[qualityKey],
          [field]: value,
        },
      },
    });
  }

  function handleLevelFieldChange<K extends keyof AlchemyLevelInput>(
    index: number,
    field: K,
    value: AlchemyLevelInput[K]
  ) {
    setLevels((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: value,
            }
          : item
      )
    );
  }

  function handleCreateDraft() {
    const recipeId = pendingRecipeId.trim();
    if (recipeId && recipes.some((item) => item.recipe_id === recipeId)) {
      setErrorMessage(`丹方 ${recipeId} 已存在。`);
      return;
    }

    setDraftRecipe(createEmptyRecipe(recipeId, levels));
    setSelectedRecipeId(DRAFT_RECIPE_ID);
    setPendingRecipeId("");
    setActiveTab("recipe");
    setStatusMessage(null);
    setErrorMessage(null);
  }

  function handleAddLevel() {
    const nextLevelIndex = levels.length;
    setLevels((current) => [
      ...current,
      {
        level: current.length,
        display_name: "",
        required_mastery_exp:
          current.length > 0
            ? Number(current[current.length - 1].required_mastery_exp || 0) + 1
            : 0,
      },
    ]);
    setSelectedLevelIndex(nextLevelIndex);
    setActiveTab("levels");
  }

  function handleRemoveLevel(index: number) {
    setLevels((current) =>
      current
        .filter((_, itemIndex) => itemIndex !== index)
        .map((item, itemIndex) => ({
          ...item,
          level: itemIndex,
        }))
    );
    setSelectedLevelIndex((current) =>
      Math.max(0, Math.min(current, Math.max(0, levels.length - 2)))
    );
  }

  async function reloadAllAndRuntime(selectedId?: string | null, message?: string) {
    const [levelsResponse, recipesResponse, reloadResult] = await Promise.all([
      fetchAlchemyLevels(),
      fetchAlchemyRecipes(),
      reloadAlchemy(),
    ]);
    const nextLevels = normalizeLevels(levelsResponse.items ?? []);
    const nextRecipes = (recipesResponse.items ?? []).map(normalizeRecipe);
    setLevels(nextLevels);
    setRecipes(nextRecipes);
    setDraftRecipe(null);
    setSelectedRecipeId(
      selectedId && nextRecipes.some((item) => item.recipe_id === selectedId)
        ? selectedId
        : nextRecipes[0]?.recipe_id ?? null
    );
    setStatusMessage(
      message ??
        `已重载运行时，当前载入 ${reloadResult.level_count} 个丹道等级、${reloadResult.recipe_count} 个丹方。`
    );
  }

  async function handleSaveRecipe() {
    if (!selectedRecipe) {
      return;
    }

    const payload = normalizeRecipe(selectedRecipe);
    if (!payload.recipe_id.trim() || !payload.display_name.trim()) {
      setErrorMessage("丹方 ID 和丹方名称不能为空。");
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const savedRecipe = isDraft
        ? await createAlchemyRecipe(payload)
        : await updateAlchemyRecipe(payload.recipe_id, payload);
      await reloadAllAndRuntime(savedRecipe.recipe_id, "已保存丹方并自动重载运行时。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDeleteRecipe() {
    if (!selectedRecipe || isDraft) {
      return;
    }
    if (!window.confirm(`确定删除丹方 ${selectedRecipe.display_name} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteAlchemyRecipe(selectedRecipe.recipe_id);
      await reloadAllAndRuntime(null, "已删除丹方并自动重载运行时。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleSaveLevels() {
    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await updateAlchemyLevels(normalizeLevels(levels));
      await reloadAllAndRuntime(
        !isDraft ? selectedRecipeId : null,
        "已保存丹道等级并自动重载运行时。"
      );
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleReload() {
    try {
      setErrorMessage(null);
      const result = await reloadAlchemy();
      setStatusMessage(
        `已重载运行时，当前载入 ${result.level_count} 个丹道等级、${result.recipe_count} 个丹方。`
      );
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载丹道配置...</div>;
  }

  return (
    <ConfigWorkbench
      className="config-workbench--compact config-workbench--alchemy"
      title="丹道配置"
      description="集中维护丹道等级、丹方材料和成丹效果。"
      hideHero
      registryTitle={activeTab === "levels" ? "丹道等级" : "丹方清单"}
      registryDescription="先选择编辑对象，再维护具体配置。"
      registryContent={
        <div className="section-grid">
          <nav className="tab-strip" aria-label="丹道配置对象">
            <button
              aria-pressed={activeTab === "recipe"}
              className={
                activeTab === "recipe"
                  ? "tab-strip__button tab-strip__button--active"
                  : "tab-strip__button"
              }
              type="button"
              onClick={() => setActiveTab("recipe")}
            >
              <span>丹方</span>
              <small>{recipes.length + (draftRecipe ? 1 : 0)}</small>
            </button>
            <button
              aria-pressed={activeTab === "levels"}
              className={
                activeTab === "levels"
                  ? "tab-strip__button tab-strip__button--active"
                  : "tab-strip__button"
              }
              type="button"
              onClick={() => setActiveTab("levels")}
            >
              <span>丹道等级</span>
              <small>{levels.length}</small>
            </button>
          </nav>

          {activeTab === "recipe" ? (
            <div className="event-compact-toolbar">
              <div className="event-compact-toolbar__grid">
                <label className="field field--full">
                  <span className="field__label">当前丹方</span>
                  <select
                    aria-label="当前丹方"
                    value={selectedRecipeId ?? ""}
                    onChange={(event) => {
                      setSelectedRecipeId(event.target.value || null);
                      setStatusMessage(null);
                      setErrorMessage(null);
                    }}
                  >
                    <option value="">选择已有丹方</option>
                    {draftRecipe ? (
                      <option value={DRAFT_RECIPE_ID}>
                        草稿：{draftRecipe.display_name || draftRecipe.recipe_id || "未命名丹方"}
                      </option>
                    ) : null}
                    {recipes.map((item) => (
                      <option key={item.recipe_id} value={item.recipe_id}>
                        {item.display_name
                          ? `${item.display_name} / ${item.recipe_id}`
                          : item.recipe_id}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field field--full">
                  <span className="field__label">新建丹方 ID</span>
                  <input
                    aria-label="新建丹方 ID"
                    placeholder="例如 ning_shen_dan"
                    value={pendingRecipeId}
                    onChange={(event) => setPendingRecipeId(event.target.value)}
                  />
                </label>
              </div>

              <div className="event-compact-toolbar__actions event-compact-toolbar__actions--stack">
                <button className="button-secondary" type="button" onClick={handleCreateDraft}>
                  新建丹方
                </button>
                <button className="button-secondary" type="button" onClick={() => void handleReload()}>
                  重载运行时
                </button>
              </div>
            </div>
          ) : (
            <div className="event-compact-toolbar">
              <div className="event-compact-toolbar__grid">
                <label className="field field--full">
                  <span className="field__label">当前等级</span>
                  <select
                    aria-label="当前丹道等级"
                    value={normalizedSelectedLevelIndex}
                    onChange={(event) => setSelectedLevelIndex(Number(event.target.value) || 0)}
                  >
                    {levels.map((level, index) => (
                      <option key={level.level} value={index}>
                        {`Lv.${level.level} ${level.display_name || "未命名等级"}`}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="event-compact-toolbar__actions event-compact-toolbar__actions--stack">
                <button className="button-secondary" type="button" onClick={handleAddLevel}>
                  新增等级
                </button>
                <button className="button-secondary" type="button" onClick={() => void handleReload()}>
                  重载运行时
                </button>
              </div>
            </div>
          )}

          {activeTab === "recipe" && recipes.length === 0 && !draftRecipe ? (
            <div className="empty-state">当前还没有丹方，可先创建一个草稿。</div>
          ) : null}
        </div>
      }
      detailTitle={
        activeTab === "levels"
          ? selectedLevel
            ? `丹道等级 ${selectedLevel.level}`
            : "丹道等级"
          : selectedRecipe?.display_name || "丹方详情"
      }
      detailDescription={
        activeTab === "levels"
          ? "维护每级丹道名称与解锁所需熟练度。"
          : "维护丹方描述、材料、成丹效果与是否属于基础丹方。"
      }
      detailMeta={
        <div className="event-detail-chips">
          <span className="event-detail-chip">
            <small>丹道等级</small>
            <strong>{levels.length}</strong>
          </span>
          <span className="event-detail-chip">
            <small>丹方总数</small>
            <strong>{recipes.length + (draftRecipe ? 1 : 0)}</strong>
          </span>
          {activeTab === "recipe" && selectedRecipe ? (
            <span className="event-detail-chip">
              <small>当前丹方</small>
              <strong>{selectedRecipe.recipe_id || "未填写"}</strong>
            </span>
          ) : null}
          {activeTab === "levels" && selectedLevel ? (
            <span className="event-detail-chip">
              <small>当前等级</small>
              <strong>{`Lv.${selectedLevel.level} ${selectedLevel.display_name || "未命名"}`}</strong>
            </span>
          ) : null}
        </div>
      }
      detailContent={
        activeTab === "levels" && selectedLevel ? (
          <div className="section-grid">
            <section className="section-card">
              <div className="section-card__header">
                <div>
                  <h3>等级 {selectedLevel.level}</h3>
                  <p>只编辑当前选中的等级，切换左侧等级标签可维护其它等级。</p>
                </div>
                <button
                  className="button-secondary"
                  disabled={levels.length <= 1}
                  type="button"
                  onClick={() => handleRemoveLevel(normalizedSelectedLevelIndex)}
                >
                  删除等级
                </button>
              </div>
              <div className="field-grid">
                <label className="field">
                  <span className="field__label">等级序号</span>
                  <input aria-label={`等级序号-${selectedLevel.level}`} disabled value={selectedLevel.level} />
                </label>
                <label className="field">
                  <span className="field__label">等级名称</span>
                  <input
                    aria-label={`等级名称-${selectedLevel.level}`}
                    value={selectedLevel.display_name}
                    onChange={(event) =>
                      handleLevelFieldChange(
                        normalizedSelectedLevelIndex,
                        "display_name",
                        event.target.value
                      )
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">所需熟练度</span>
                  <input
                    aria-label={`所需熟练度-${selectedLevel.level}`}
                    type="number"
                    value={selectedLevel.required_mastery_exp}
                    onChange={(event) =>
                      handleLevelFieldChange(
                        normalizedSelectedLevelIndex,
                        "required_mastery_exp",
                        Number(event.target.value) || 0
                      )
                    }
                  />
                </label>
              </div>
            </section>
          </div>
        ) : activeTab === "levels" ? (
          <div className="empty-state">当前还没有丹道等级，可先新增一个等级。</div>
        ) : selectedRecipe ? (
          <div className="section-grid">
            <div className="field-grid">
              <label className="field">
                <span className="field__label">丹方 ID</span>
                <input
                  aria-label="丹方 ID"
                  disabled={!isDraft}
                  value={selectedRecipe.recipe_id}
                  onChange={(event) =>
                    handleRecipeFieldChange("recipe_id", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">丹方名称</span>
                <input
                  aria-label="丹方名称"
                  value={selectedRecipe.display_name}
                  onChange={(event) =>
                    handleRecipeFieldChange("display_name", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">分类</span>
                <input
                  aria-label="分类"
                  value={selectedRecipe.category}
                  onChange={(event) => handleRecipeFieldChange("category", event.target.value)}
                />
              </label>
              <label className="field">
                <span className="field__label">所需丹道等级</span>
                <select
                  aria-label="所需丹道等级"
                  value={selectedRecipe.required_alchemy_level}
                  onChange={(event) =>
                    handleRecipeFieldChange(
                      "required_alchemy_level",
                      Number(event.target.value) || 0
                    )
                  }
                >
                  {levels.map((level) => (
                    <option key={level.level} value={level.level}>
                      {`Lv.${level.level} ${level.display_name || "未命名等级"}`}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="field__label">炼制时长（月）</span>
                <input
                  aria-label="炼制时长（月）"
                  type="number"
                  value={selectedRecipe.duration_months}
                  onChange={(event) =>
                    handleRecipeFieldChange("duration_months", Number(event.target.value) || 0)
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">基础成丹率</span>
                <input
                  aria-label="基础成丹率"
                  max={1}
                  min={0}
                  step="0.01"
                  type="number"
                  value={selectedRecipe.base_success_rate}
                  onChange={(event) =>
                    handleRecipeFieldChange(
                      "base_success_rate",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">每级成丹率变化</span>
                <input
                  aria-label="每级成丹率变化"
                  max={1}
                  min={-1}
                  step="0.01"
                  type="number"
                  value={selectedRecipe.per_level_success_rate}
                  onChange={(event) =>
                    handleRecipeFieldChange(
                      "per_level_success_rate",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">成功熟练度</span>
                <input
                  aria-label="成功熟练度"
                  min={0}
                  type="number"
                  value={selectedRecipe.success_mastery_exp_gain}
                  onChange={(event) =>
                    handleRecipeFieldChange(
                      "success_mastery_exp_gain",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
              <label className="field field--full">
                <span className="field__label">丹方描述</span>
                <textarea
                  aria-label="丹方描述"
                  value={selectedRecipe.description}
                  onChange={(event) =>
                    handleRecipeFieldChange("description", event.target.value)
                  }
                />
              </label>
            </div>

            <ResourceRecordEditor
              label="丹方材料"
              value={selectedRecipe.ingredients}
              onChange={(value) => handleRecipeFieldChange("ingredients", value)}
              addLabel="新增材料"
              emptyMessage="当前还没有配置材料。"
              hint="成丹前会按这里配置的材料扣除库存。"
            />

            <section className="section-card">
              <div className="section-card__header">
                <div>
                  <h3>成丹效果</h3>
                  <p>配置成丹后可服用的效果类型、数值与展示说明。</p>
                </div>
              </div>
              <div className="field-grid">
                <label className="field">
                  <span className="field__label">效果类型</span>
                  <select
                    aria-label="效果类型"
                    value={selectedRecipe.effect_type}
                    onChange={(event) =>
                      handleRecipeFieldChange("effect_type", event.target.value)
                    }
                  >
                    {effectTypeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field__label">效果数值</span>
                  <input
                    aria-label="效果数值"
                    step="0.01"
                    type="number"
                    value={selectedRecipe.effect_value}
                    onChange={(event) =>
                      handleRecipeFieldChange("effect_value", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field field--full">
                  <span className="field__label">效果说明</span>
                  <textarea
                    aria-label="效果说明"
                    value={selectedRecipe.effect_summary}
                    onChange={(event) =>
                      handleRecipeFieldChange("effect_summary", event.target.value)
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">基础丹方</span>
                  <select
                    aria-label="基础丹方"
                    value={selectedRecipe.is_base_recipe ? "true" : "false"}
                    onChange={(event) =>
                      handleRecipeFieldChange("is_base_recipe", event.target.value === "true")
                    }
                  >
                    <option value="true">是</option>
                    <option value="false">否</option>
                  </select>
                </label>
              </div>
            </section>

            <section className="section-card">
              <div className="section-card__header">
                <div>
                  <h3>品级概率与效果</h3>
                  <p>基础权重 + 丹道等级 * 每级权重变化，决定成丹后的品级概率；效果倍率决定服用收益。</p>
                </div>
              </div>
              <div className="alchemy-quality-grid">
                {qualityProfileOptions.map((quality) => {
                  const profile = normalizeQualityProfiles(selectedRecipe.quality_profiles)[quality.key];
                  return (
                    <div key={quality.key} className={`alchemy-quality-card alchemy-quality-card--${quality.key}`}>
                      <div className="alchemy-quality-card__title">
                        <strong>{profile.display_name || quality.label}</strong>
                        <small>{quality.key}</small>
                      </div>
                      <div className="field-grid">
                        <label className="field">
                          <span className="field__label">品级名称</span>
                          <input
                            aria-label={`${quality.label}名称`}
                            value={profile.display_name}
                            onChange={(event) =>
                              handleQualityProfileChange(
                                quality.key,
                                "display_name",
                                event.target.value
                              )
                            }
                          />
                        </label>
                        <label className="field">
                          <span className="field__label">颜色标识</span>
                          <input
                            aria-label={`${quality.label}颜色标识`}
                            value={profile.color}
                            onChange={(event) =>
                              handleQualityProfileChange(
                                quality.key,
                                "color",
                                event.target.value
                              )
                            }
                          />
                        </label>
                        <label className="field">
                          <span className="field__label">基础权重</span>
                          <input
                            aria-label={`${quality.label}基础权重`}
                            min={0}
                            type="number"
                            value={profile.base_weight}
                            onChange={(event) =>
                              handleQualityProfileChange(
                                quality.key,
                                "base_weight",
                                Number(event.target.value) || 0
                              )
                            }
                          />
                        </label>
                        <label className="field">
                          <span className="field__label">每级权重变化</span>
                          <input
                            aria-label={`${quality.label}每级权重变化`}
                            type="number"
                            value={profile.per_level_weight}
                            onChange={(event) =>
                              handleQualityProfileChange(
                                quality.key,
                                "per_level_weight",
                                Number(event.target.value) || 0
                              )
                            }
                          />
                        </label>
                        <label className="field field--full">
                          <span className="field__label">效果倍率</span>
                          <input
                            aria-label={`${quality.label}效果倍率`}
                            min={0.01}
                            step="0.01"
                            type="number"
                            value={profile.effect_multiplier}
                            onChange={(event) =>
                              handleQualityProfileChange(
                                quality.key,
                                "effect_multiplier",
                                Number(event.target.value) || 0
                              )
                            }
                          />
                        </label>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        ) : (
          <div className="empty-state">左侧选择一个丹方后，即可在这里编辑材料与成丹效果。</div>
        )
      }
      actionBar={
        activeTab === "levels" ? (
          <div className="toolbar">
            <button className="button-primary" type="button" onClick={() => void handleSaveLevels()}>
              保存丹道等级
            </button>
          </div>
        ) : (
          <div className="toolbar">
            <button
              className="button-danger"
              disabled={!selectedRecipe || isDraft}
              type="button"
              onClick={() => void handleDeleteRecipe()}
            >
              删除丹方
            </button>
            <button
              className="button-primary"
              disabled={!selectedRecipe}
              type="button"
              onClick={() => void handleSaveRecipe()}
            >
              保存丹方
            </button>
          </div>
        )
      }
      statusPanel={
        <AlchemyStatusPanel errorMessage={errorMessage} statusMessage={statusMessage} />
      }
    />
  );
}

function AlchemyStatusPanel({
  errorMessage,
  statusMessage,
}: {
  errorMessage: string | null;
  statusMessage: string | null;
}) {
  if (!errorMessage && !statusMessage) {
    return null;
  }

  return (
    <section className="status-card">
      {statusMessage ? (
        <div className="status-card__banner">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="status-card__banner status-card__banner--error" role="alert">
          {errorMessage}
        </div>
      ) : null}
    </section>
  );
}

function createEmptyRecipe(
  recipeId: string,
  levels: AlchemyLevelInput[]
): AlchemyRecipeInput {
  return {
    recipe_id: recipeId,
    display_name: "",
    category: "",
    description: "",
    required_alchemy_level: levels[0]?.level ?? 0,
    duration_months: 1,
    base_success_rate: 0.5,
    per_level_success_rate: 0.04,
    success_mastery_exp_gain: 10,
    ingredients: {},
    effect_type: "cultivation_exp",
    effect_value: 1,
    effect_summary: "",
    quality_profiles: createDefaultQualityProfiles(),
    is_base_recipe: false,
  };
}

function normalizeLevels(levels: AlchemyLevelInput[]): AlchemyLevelInput[] {
  return [...levels]
    .map((level, index) => ({
      level: index,
      display_name: String(level.display_name ?? "").trim(),
      required_mastery_exp: Math.max(0, Number(level.required_mastery_exp ?? 0) || 0),
    }))
    .sort((left, right) => left.level - right.level);
}

function normalizeRecipe(recipe: AlchemyRecipeInput): AlchemyRecipeInput {
  return {
    recipe_id: String(recipe.recipe_id ?? "").trim(),
    display_name: String(recipe.display_name ?? "").trim(),
    category: String(recipe.category ?? "").trim(),
    description: String(recipe.description ?? "").trim(),
    required_alchemy_level: Math.max(0, Number(recipe.required_alchemy_level ?? 0) || 0),
    duration_months: Math.max(1, Number(recipe.duration_months ?? 1) || 1),
    base_success_rate: Number(recipe.base_success_rate ?? 0) || 0,
    per_level_success_rate: Number(recipe.per_level_success_rate ?? 0.04) || 0,
    success_mastery_exp_gain: Math.max(
      0,
      Number(recipe.success_mastery_exp_gain ?? 10) || 0
    ),
    ingredients:
      recipe.ingredients && typeof recipe.ingredients === "object" && !Array.isArray(recipe.ingredients)
        ? recipe.ingredients
        : {},
    effect_type: String(recipe.effect_type ?? "").trim(),
    effect_value: Number(recipe.effect_value ?? 0) || 0,
    effect_summary: String(recipe.effect_summary ?? "").trim(),
    quality_profiles: normalizeQualityProfiles(recipe.quality_profiles),
    is_base_recipe: recipe.is_base_recipe === true,
  };
}

function createDefaultQualityProfiles(): AlchemyRecipeInput["quality_profiles"] {
  return {
    low: {
      display_name: "下品",
      color: "white",
      base_weight: 70,
      per_level_weight: -10,
      effect_multiplier: 1,
    },
    mid: {
      display_name: "中品",
      color: "green",
      base_weight: 25,
      per_level_weight: 4,
      effect_multiplier: 1.25,
    },
    high: {
      display_name: "上品",
      color: "blue",
      base_weight: 5,
      per_level_weight: 4,
      effect_multiplier: 1.5,
    },
    supreme: {
      display_name: "极品",
      color: "purple",
      base_weight: 0,
      per_level_weight: 2,
      effect_multiplier: 2,
    },
  };
}

function normalizeQualityProfiles(
  profiles: AlchemyRecipeInput["quality_profiles"] | undefined
): AlchemyRecipeInput["quality_profiles"] {
  const defaults = createDefaultQualityProfiles();
  const source =
    profiles && typeof profiles === "object" && !Array.isArray(profiles)
      ? profiles
      : {};

  return Object.fromEntries(
    qualityProfileOptions.map((quality) => {
      const profile = source[quality.key] ?? defaults[quality.key];
      return [
        quality.key,
        {
          display_name: String(profile.display_name ?? defaults[quality.key].display_name).trim(),
          color: String(profile.color ?? defaults[quality.key].color).trim(),
          base_weight: Math.max(0, Number(profile.base_weight ?? defaults[quality.key].base_weight) || 0),
          per_level_weight: Number(profile.per_level_weight ?? defaults[quality.key].per_level_weight) || 0,
          effect_multiplier: Math.max(
            0.01,
            Number(profile.effect_multiplier ?? defaults[quality.key].effect_multiplier) || 0
          ),
        },
      ];
    })
  ) as AlchemyRecipeInput["quality_profiles"];
}
