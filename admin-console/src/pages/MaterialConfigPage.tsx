import { useEffect, useMemo, useState } from "react";

import {
  createMaterial,
  deleteMaterial,
  fetchMaterialDetail,
  fetchMaterials,
  reloadMaterials,
  updateMaterial,
  type MaterialInput,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { StatusPanel } from "../components/StatusPanel";

const DRAFT_MATERIAL_ID = "__draft_material__";

const categoryOptions = [
  { value: "herb", label: "灵草" },
  { value: "ore", label: "矿材" },
  { value: "alchemy_auxiliary", label: "炼丹辅材" },
  { value: "craft_auxiliary", label: "炼器辅材" },
];

const rarityOptions = [
  { value: "common", label: "普通" },
  { value: "uncommon", label: "少见" },
  { value: "rare", label: "稀有" },
  { value: "epic", label: "珍品" },
];

const sourceOptions = [
  { value: "dwelling", label: "洞府产出" },
  { value: "event", label: "事件产出" },
  { value: "battle", label: "战斗产出" },
  { value: "shop", label: "商店产出" },
];

const tagOptions = [
  { value: "dwelling", label: "洞府相关" },
  { value: "alchemy", label: "炼丹材料" },
  { value: "basic", label: "基础材料" },
  { value: "auxiliary", label: "辅助材料" },
  { value: "crafting", label: "炼器材料" },
  { value: "breakthrough", label: "突破材料" },
  { value: "event", label: "事件材料" },
];

export function MaterialConfigPage() {
  const [items, setItems] = useState<MaterialInput[]>([]);
  const [draftItem, setDraftItem] = useState<MaterialInput | null>(null);
  const [selectedMaterialId, setSelectedMaterialId] = useState<string | null>(null);
  const [pendingMaterialId, setPendingMaterialId] = useState("");
  const [pendingTag, setPendingTag] = useState(tagOptions[0].value);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const response = await fetchMaterials();
        if (!isMounted) {
          return;
        }
        const nextItems = (response.items ?? []).map(normalizeMaterial);
        setItems(nextItems);
        setDraftItem(null);
        setErrorMessage(null);
        setStatusMessage(null);
        setSelectedMaterialId((current) => {
          if (current === DRAFT_MATERIAL_ID) {
            return current;
          }
          if (current && nextItems.some((item) => item.material_id === current)) {
            return current;
          }
          return nextItems[0]?.material_id ?? null;
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

  useEffect(() => {
    let isMounted = true;

    async function loadDetail() {
      if (!selectedMaterialId || selectedMaterialId === DRAFT_MATERIAL_ID) {
        return;
      }

      try {
        const detail = normalizeMaterial(await fetchMaterialDetail(selectedMaterialId));
        if (!isMounted) {
          return;
        }
        setItems((current) =>
          current.map((item) => (item.material_id === selectedMaterialId ? detail : item))
        );
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
  }, [selectedMaterialId]);

  const selectedMaterial = useMemo(() => {
    if (selectedMaterialId === DRAFT_MATERIAL_ID) {
      return draftItem;
    }
    return items.find((item) => item.material_id === selectedMaterialId) ?? null;
  }, [draftItem, items, selectedMaterialId]);

  const isDraft = selectedMaterialId === DRAFT_MATERIAL_ID;
  const availableTagOptions = tagOptions.filter(
    (option) => !selectedMaterial?.tags.includes(option.value)
  );
  const pendingTagValue = availableTagOptions.some((option) => option.value === pendingTag)
    ? pendingTag
    : availableTagOptions[0]?.value ?? "";

  function updateSelectedMaterial(nextItem: MaterialInput) {
    const normalized = normalizeMaterial(nextItem);
    if (selectedMaterialId === DRAFT_MATERIAL_ID) {
      setDraftItem(normalized);
      return;
    }
    setItems((current) =>
      current.map((item) => (item.material_id === normalized.material_id ? normalized : item))
    );
  }

  function handleFieldChange<K extends keyof MaterialInput>(
    field: K,
    value: MaterialInput[K]
  ) {
    if (!selectedMaterial) {
      return;
    }
    updateSelectedMaterial({
      ...selectedMaterial,
      [field]: value,
    });
  }

  function handleAddTag() {
    if (!selectedMaterial || !pendingTagValue || selectedMaterial.tags.includes(pendingTagValue)) {
      return;
    }
    updateSelectedMaterial({
      ...selectedMaterial,
      tags: [...selectedMaterial.tags, pendingTagValue],
    });
    const nextOption = tagOptions.find(
      (option) =>
        option.value !== pendingTagValue && !selectedMaterial.tags.includes(option.value)
    );
    if (nextOption) {
      setPendingTag(nextOption.value);
    }
  }

  function handleRemoveTag(tag: string) {
    if (!selectedMaterial) {
      return;
    }
    updateSelectedMaterial({
      ...selectedMaterial,
      tags: selectedMaterial.tags.filter((item) => item !== tag),
    });
  }

  function handleCreateDraft() {
    const materialId = pendingMaterialId.trim();
    if (materialId && items.some((item) => item.material_id === materialId)) {
      setErrorMessage(`材料 ${materialId} 已存在。`);
      return;
    }

    const nextDraft = createEmptyMaterial(materialId);
    setDraftItem(nextDraft);
    setSelectedMaterialId(DRAFT_MATERIAL_ID);
    setPendingMaterialId("");
    setStatusMessage(null);
    setErrorMessage(null);
  }

  async function reloadListAndRuntime(selectedId?: string | null, message?: string) {
    const [response, reloadResult] = await Promise.all([fetchMaterials(), reloadMaterials()]);
    const nextItems = (response.items ?? []).map(normalizeMaterial);
    setItems(nextItems);
    setDraftItem(null);
    setSelectedMaterialId(
      selectedId && nextItems.some((item) => item.material_id === selectedId)
        ? selectedId
        : nextItems[0]?.material_id ?? null
    );
    setStatusMessage(
      message ?? `已同步并立即生效，当前载入 ${reloadResult.material_count} 个材料。`
    );
  }

  async function handleSave() {
    if (!selectedMaterial) {
      return;
    }

    const payload = normalizeMaterial(selectedMaterial);
    if (!payload.material_id.trim() || !payload.display_name.trim()) {
      setErrorMessage("材料 ID 和材料名称不能为空。");
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const savedItem = isDraft
        ? await createMaterial(payload)
        : await updateMaterial(payload.material_id, payload);
      await reloadListAndRuntime(savedItem.material_id, "已保存材料并立即生效。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!selectedMaterial || isDraft) {
      return;
    }
    if (!window.confirm(`确定删除材料 ${selectedMaterial.display_name} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteMaterial(selectedMaterial.material_id);
      await reloadListAndRuntime(null, "已删除材料并立即生效。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载材料配置...</div>;
  }

  return (
    <ConfigWorkbench
      className="config-workbench--compact"
      title="材料配置"
      description="维护游戏内材料定义，洞府、炼丹与后续系统都以此处为准。"
      hideHero
      registryTitle="材料清单"
      registryContent={
        <div className="section-grid">
          <div className="event-compact-toolbar">
            <div className="event-compact-toolbar__grid">
              <label className="field field--full">
                <span className="field__label">当前材料</span>
                <select
                  aria-label="当前材料"
                  value={selectedMaterialId ?? ""}
                  onChange={(event) => {
                    setSelectedMaterialId(event.target.value || null);
                    setStatusMessage(null);
                    setErrorMessage(null);
                  }}
                >
                  <option value="">选择已有材料</option>
                  {draftItem ? (
                    <option value={DRAFT_MATERIAL_ID}>
                      草稿：{draftItem.display_name || draftItem.material_id || "未命名材料"}
                    </option>
                  ) : null}
                  {items.map((item) => (
                    <option key={item.material_id} value={item.material_id}>
                      {item.display_name
                        ? `${item.display_name} / ${item.material_id}`
                        : item.material_id}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field field--full">
                <span className="field__label">新建材料 ID</span>
                <input
                  aria-label="新建材料 ID"
                  placeholder="例如 moonlit_herb"
                  value={pendingMaterialId}
                  onChange={(event) => setPendingMaterialId(event.target.value)}
                />
              </label>
            </div>

            <div className="event-compact-toolbar__actions event-compact-toolbar__actions--stack">
              <button className="button-secondary" type="button" onClick={handleCreateDraft}>
                新建材料
              </button>
              <button
                className="button-danger"
                disabled={!selectedMaterial || isDraft}
                type="button"
                onClick={() => void handleDelete()}
              >
                删除材料
              </button>
              <button
                className="button-primary"
                disabled={!selectedMaterial}
                type="button"
                onClick={() => void handleSave()}
              >
                保存材料
              </button>
            </div>
          </div>

          {items.length === 0 && !draftItem ? (
            <div className="empty-state">当前还没有材料，可以先创建一个洞府产出的基础材料。</div>
          ) : null}
        </div>
      }
      detailTitle={selectedMaterial?.display_name || "材料详情"}
      detailDescription="材料 ID 会被炼丹配方、洞府产出和后续系统引用，创建后不支持改名。"
      detailMeta={
        selectedMaterial ? (
          <div className="event-detail-chips">
            <span className="event-detail-chip">
              <small>材料 ID</small>
              <strong>{selectedMaterial.material_id || "未填写"}</strong>
            </span>
            <span className="event-detail-chip">
              <small>来源</small>
              <strong>{sourceOptions.find((item) => item.value === selectedMaterial.source)?.label ?? selectedMaterial.source}</strong>
            </span>
            <span className="event-detail-chip">
              <small>品级</small>
              <strong>Tier {selectedMaterial.tier}</strong>
            </span>
          </div>
        ) : null
      }
      detailContent={
        selectedMaterial ? (
          <div className="section-grid">
            <section className="section-card">
              <div className="field-grid">
                <label className="field">
                  <span className="field__label">材料 ID</span>
                  <input
                    aria-label="材料 ID"
                    disabled={!isDraft}
                    value={selectedMaterial.material_id}
                    onChange={(event) => handleFieldChange("material_id", event.target.value)}
                  />
                </label>
                <label className="field">
                  <span className="field__label">材料名称</span>
                  <input
                    aria-label="材料名称"
                    value={selectedMaterial.display_name}
                    onChange={(event) => handleFieldChange("display_name", event.target.value)}
                  />
                </label>
                <label className="field">
                  <span className="field__label">材料类型</span>
                  <select
                    aria-label="材料类型"
                    value={selectedMaterial.category}
                    onChange={(event) => handleFieldChange("category", event.target.value)}
                  >
                    {categoryOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field__label">稀有度</span>
                  <select
                    aria-label="稀有度"
                    value={selectedMaterial.rarity}
                    onChange={(event) => handleFieldChange("rarity", event.target.value)}
                  >
                    {rarityOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field__label">来源</span>
                  <select
                    aria-label="来源"
                    value={selectedMaterial.source}
                    onChange={(event) => handleFieldChange("source", event.target.value)}
                  >
                    {sourceOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field__label">品级</span>
                  <input
                    aria-label="品级"
                    min={1}
                    type="number"
                    value={selectedMaterial.tier}
                    onChange={(event) =>
                      handleFieldChange("tier", Math.max(1, Number(event.target.value) || 1))
                    }
                  />
                </label>
                <div className="field field--full">
                  <span className="field__label">材料标签</span>
                  <div className="resource-row">
                    <label className="field">
                      <span className="field__hint">选择标签</span>
                      <select
                        aria-label="选择材料标签"
                        value={pendingTagValue}
                        onChange={(event) => setPendingTag(event.target.value)}
                      >
                        {availableTagOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      className="button-secondary resource-row__remove"
                      disabled={availableTagOptions.length === 0}
                      type="button"
                      onClick={handleAddTag}
                    >
                      添加标签
                    </button>
                  </div>
                  <div className="chip-row" aria-label="已选材料标签">
                    {selectedMaterial.tags.length > 0 ? (
                      selectedMaterial.tags.map((tag) => (
                        <button
                          key={tag}
                          className="event-detail-chip"
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                        >
                          <small>{tag}</small>
                          <strong>{formatTagLabel(tag)} ×</strong>
                        </button>
                      ))
                    ) : (
                      <span className="field__hint">尚未选择材料标签。</span>
                    )}
                  </div>
                </div>
                <label className="field field--full">
                  <span className="field__label">材料描述</span>
                  <textarea
                    aria-label="材料描述"
                    value={selectedMaterial.description}
                    onChange={(event) => handleFieldChange("description", event.target.value)}
                  />
                </label>
              </div>
            </section>
          </div>
        ) : (
          <div className="empty-state">左侧选择一个材料后，即可维护它在游戏中的基础定义。</div>
        )
      }
      statusPanel={<StatusPanel errorMessage={errorMessage} statusMessage={statusMessage} />}
    />
  );
}

function createEmptyMaterial(materialId = ""): MaterialInput {
  return {
    material_id: materialId,
    display_name: "",
    category: "herb",
    tier: 1,
    rarity: "common",
    source: "dwelling",
    description: "",
    tags: ["dwelling", "basic"],
  };
}

function normalizeMaterial(item: MaterialInput): MaterialInput {
  return {
    ...createEmptyMaterial(item.material_id),
    ...item,
    material_id: String(item.material_id ?? "").trim(),
    display_name: String(item.display_name ?? "").trim(),
    category: String(item.category ?? "herb").trim() || "herb",
    tier: Math.max(1, Number(item.tier ?? 1) || 1),
    rarity: String(item.rarity ?? "common").trim() || "common",
    source: String(item.source ?? "dwelling").trim() || "dwelling",
    description: String(item.description ?? "").trim(),
    tags: dedupeTags(Array.isArray(item.tags) ? item.tags.map(String) : []),
  };
}

function dedupeTags(tags: string[]): string[] {
  return Array.from(new Set(tags.map((item) => item.trim()).filter(Boolean)));
}

function formatTagLabel(tag: string): string {
  return tagOptions.find((option) => option.value === tag)?.label ?? tag;
}
