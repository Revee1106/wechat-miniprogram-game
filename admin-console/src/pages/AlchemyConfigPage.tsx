import { useEffect, useMemo, useState } from "react";

import {
  createAlchemyRecipe,
  deleteAlchemyRecipe,
  fetchAlchemyLevels,
  fetchAlchemyRecipes,
  reloadAlchemy,
  updateAlchemyLevels,
  updateAlchemyRecipe,
  validateAlchemy,
  type AlchemyLevelInput,
  type AlchemyRecipeInput,
  type ValidationResponse,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { ResourceRecordEditor } from "../components/ResourceRecordEditor";
import { ValidationPanel } from "../components/ValidationPanel";

const DRAFT_RECIPE_ID = "__draft_alchemy_recipe__";

type DetailTab = "recipe" | "levels";

const effectTypeOptions = [
  { value: "cultivation_exp", label: "修为增长" },
  { value: "hp_restore", label: "气血恢复" },
  { value: "lifespan_restore", label: "寿元恢复" },
  { value: "status_penalty_reduce", label: "状态惩罚减免" },
  { value: "breakthrough_bonus", label: "突破辅助加成" },
];

export function AlchemyConfigPage() {
  const [levels, setLevels] = useState<AlchemyLevelInput[]>([]);
  const [recipes, setRecipes] = useState<AlchemyRecipeInput[]>([]);
  const [draftRecipe, setDraftRecipe] = useState<AlchemyRecipeInput | null>(null);
  const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
  const [pendingRecipeId, setPendingRecipeId] = useState("");
  const [activeTab, setActiveTab] = useState<DetailTab>("recipe");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
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
        setValidation(null);
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
    setValidation(null);
  }

  function handleAddLevel() {
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
      setValidation(null);
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
      setValidation(null);
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
      setValidation(null);
      await updateAlchemyLevels(normalizeLevels(levels));
      await reloadAllAndRuntime(
        !isDraft ? selectedRecipeId : null,
        "已保存丹道等级并自动重载运行时。"
      );
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleValidate() {
    try {
      setErrorMessage(null);
      setValidation(await validateAlchemy());
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
      className="config-workbench--compact"
      title="丹道配置"
      description="集中维护丹道等级、丹方材料和成丹效果。"
      hideHero
      registryTitle="丹方清单"
      registryContent={
        <div className="section-grid">
          <div className="event-compact-toolbar">
            <div className="event-compact-toolbar__grid">
              <label className="field field--full">
                <span className="field__label">当前丹方</span>
                <select
                  aria-label="当前丹方"
                  value={selectedRecipeId ?? ""}
                  onChange={(event) => {
                    setSelectedRecipeId(event.target.value || null);
                    setActiveTab("recipe");
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
              <button className="button-accent" type="button" onClick={() => void handleValidate()}>
                校验配置
              </button>
              <button className="button-secondary" type="button" onClick={() => void handleReload()}>
                重载运行时
              </button>
            </div>
          </div>

          {recipes.length === 0 && !draftRecipe ? (
            <div className="empty-state">当前还没有丹方，可先创建一个草稿。</div>
          ) : null}
        </div>
      }
      detailTitle={activeTab === "levels" ? "丹道等级" : selectedRecipe?.display_name || "丹方详情"}
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
        </div>
      }
      detailTabs={[
        { id: "recipe", label: "丹方详情" },
        { id: "levels", label: "丹道等级", badge: levels.length },
      ]}
      activeTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as DetailTab)}
      detailContent={
        activeTab === "levels" ? (
          <div className="section-grid">
            <div className="toolbar">
              <button className="button-secondary" type="button" onClick={handleAddLevel}>
                新增等级
              </button>
            </div>

            <div className="library-grid">
              {levels.map((level, index) => (
                <section key={level.level} className="section-card">
                  <div className="section-card__header">
                    <div>
                      <h3>等级 {level.level}</h3>
                      <p>设置该等级的名称与所需熟练度门槛。</p>
                    </div>
                    <button
                      className="button-secondary"
                      disabled={levels.length <= 1}
                      type="button"
                      onClick={() => handleRemoveLevel(index)}
                    >
                      删除等级
                    </button>
                  </div>
                  <div className="field-grid">
                    <label className="field">
                      <span className="field__label">等级序号</span>
                      <input aria-label={`等级序号-${level.level}`} disabled value={level.level} />
                    </label>
                    <label className="field">
                      <span className="field__label">等级名称</span>
                      <input
                        aria-label={`等级名称-${level.level}`}
                        value={level.display_name}
                        onChange={(event) =>
                          handleLevelFieldChange(index, "display_name", event.target.value)
                        }
                      />
                    </label>
                    <label className="field">
                      <span className="field__label">所需熟练度</span>
                      <input
                        aria-label={`所需熟练度-${level.level}`}
                        type="number"
                        value={level.required_mastery_exp}
                        onChange={(event) =>
                          handleLevelFieldChange(
                            index,
                            "required_mastery_exp",
                            Number(event.target.value) || 0
                          )
                        }
                      />
                    </label>
                  </div>
                </section>
              ))}
            </div>
          </div>
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
        <ValidationPanel
          errorMessage={errorMessage}
          statusMessage={statusMessage}
          validation={validation}
        />
      }
    />
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
    ingredients: {},
    effect_type: "cultivation_exp",
    effect_value: 1,
    effect_summary: "",
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
    ingredients:
      recipe.ingredients && typeof recipe.ingredients === "object" && !Array.isArray(recipe.ingredients)
        ? recipe.ingredients
        : {},
    effect_type: String(recipe.effect_type ?? "").trim(),
    effect_value: Number(recipe.effect_value ?? 0) || 0,
    effect_summary: String(recipe.effect_summary ?? "").trim(),
    is_base_recipe: recipe.is_base_recipe === true,
  };
}
