import { useEffect, useMemo, useState } from "react";

import {
  createEquipmentItem,
  deleteEquipmentItem,
  fetchEquipmentItemDetail,
  fetchEquipmentItems,
  reloadEquipment,
  updateEquipmentItem,
  type EquipmentItemInput,
  type EquipmentSlot,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { StatusPanel } from "../components/StatusPanel";

const DRAFT_EQUIPMENT_ID = "__draft_equipment__";

const slotOptions: Array<{ value: EquipmentSlot; label: string; hint: string }> = [
  { value: "weapon", label: "武器", hint: "只提升攻击力" },
  { value: "armor", label: "防具", hint: "提升防御力和气血" },
  { value: "accessory", label: "饰品", hint: "只提供特殊效果" },
  { value: "artifact", label: "法宝", hint: "特殊装备，只提供特殊效果" },
];

export function EquipmentConfigPage() {
  const [items, setItems] = useState<EquipmentItemInput[]>([]);
  const [draftItem, setDraftItem] = useState<EquipmentItemInput | null>(null);
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string | null>(null);
  const [pendingEquipmentId, setPendingEquipmentId] = useState("");
  const [specialEffectsText, setSpecialEffectsText] = useState("{}");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const response = await fetchEquipmentItems();
        if (!isMounted) {
          return;
        }
        const nextItems = (response.items ?? []).map(normalizeEquipment);
        setItems(nextItems);
        setDraftItem(null);
        setStatusMessage(null);
        setErrorMessage(null);
        setSelectedEquipmentId((current) => {
          if (current === DRAFT_EQUIPMENT_ID) {
            return current;
          }
          if (current && nextItems.some((item) => item.equipment_id === current)) {
            return current;
          }
          return nextItems[0]?.equipment_id ?? null;
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
      if (!selectedEquipmentId || selectedEquipmentId === DRAFT_EQUIPMENT_ID) {
        return;
      }

      try {
        const detail = normalizeEquipment(await fetchEquipmentItemDetail(selectedEquipmentId));
        if (!isMounted) {
          return;
        }
        setItems((current) =>
          current.map((item) =>
            item.equipment_id === selectedEquipmentId ? detail : item
          )
        );
        setSpecialEffectsText(JSON.stringify(detail.special_effects, null, 2));
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
  }, [selectedEquipmentId]);

  const selectedEquipment = useMemo(() => {
    if (selectedEquipmentId === DRAFT_EQUIPMENT_ID) {
      return draftItem;
    }
    return items.find((item) => item.equipment_id === selectedEquipmentId) ?? null;
  }, [draftItem, items, selectedEquipmentId]);

  const isDraft = selectedEquipmentId === DRAFT_EQUIPMENT_ID;
  const selectedSlot = slotOptions.find((option) => option.value === selectedEquipment?.slot);

  function updateSelectedEquipment(nextItem: EquipmentItemInput) {
    const normalized = normalizeEquipment(nextItem);
    if (selectedEquipmentId === DRAFT_EQUIPMENT_ID) {
      setDraftItem(normalized);
      return;
    }
    setItems((current) =>
      current.map((item) =>
        item.equipment_id === normalized.equipment_id ? normalized : item
      )
    );
  }

  function handleFieldChange<K extends keyof EquipmentItemInput>(
    field: K,
    value: EquipmentItemInput[K]
  ) {
    if (!selectedEquipment) {
      return;
    }
    updateSelectedEquipment({
      ...selectedEquipment,
      [field]: value,
    });
  }

  function handleSlotChange(slot: EquipmentSlot) {
    if (!selectedEquipment) {
      return;
    }
    const nextItem = normalizeEquipmentForSlot({
      ...selectedEquipment,
      slot,
    });
    updateSelectedEquipment(nextItem);
    setSpecialEffectsText(JSON.stringify(nextItem.special_effects, null, 2));
  }

  function handleCreateDraft() {
    const equipmentId = pendingEquipmentId.trim();
    if (equipmentId && items.some((item) => item.equipment_id === equipmentId)) {
      setErrorMessage(`装备 ${equipmentId} 已存在。`);
      return;
    }

    const nextDraft = createEmptyEquipment(equipmentId);
    setDraftItem(nextDraft);
    setSelectedEquipmentId(DRAFT_EQUIPMENT_ID);
    setPendingEquipmentId("");
    setSpecialEffectsText(JSON.stringify(nextDraft.special_effects, null, 2));
    setStatusMessage(null);
    setErrorMessage(null);
  }

  async function reloadListAndRuntime(selectedId?: string | null, message?: string) {
    const [response, reloadResult] = await Promise.all([
      fetchEquipmentItems(),
      reloadEquipment(),
    ]);
    const nextItems = (response.items ?? []).map(normalizeEquipment);
    setItems(nextItems);
    setDraftItem(null);
    setSelectedEquipmentId(
      selectedId && nextItems.some((item) => item.equipment_id === selectedId)
        ? selectedId
        : nextItems[0]?.equipment_id ?? null
    );
    setStatusMessage(
      message ?? `已同步并立即生效，当前载入 ${reloadResult.equipment_count} 件装备。`
    );
  }

  async function handleSave() {
    if (!selectedEquipment) {
      return;
    }

    let parsedEffects: Record<string, unknown>;
    try {
      parsedEffects = parseSpecialEffects(specialEffectsText);
    } catch (error) {
      setErrorMessage((error as Error).message);
      return;
    }

    const payload = normalizeEquipmentForSlot({
      ...selectedEquipment,
      special_effects: parsedEffects,
    });
    if (!payload.equipment_id.trim() || !payload.display_name.trim()) {
      setErrorMessage("装备 ID 和装备名称不能为空。");
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const savedItem = isDraft
        ? await createEquipmentItem(payload)
        : await updateEquipmentItem(payload.equipment_id, payload);
      await reloadListAndRuntime(savedItem.equipment_id, "已保存装备并立即生效。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!selectedEquipment || isDraft) {
      return;
    }
    if (!window.confirm(`确定删除装备 ${selectedEquipment.display_name} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteEquipmentItem(selectedEquipment.equipment_id);
      await reloadListAndRuntime(null, "已删除装备并立即生效。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载装备配置...</div>;
  }

  return (
    <ConfigWorkbench
      className="config-workbench--compact"
      title="装备配置"
      description="维护武器、防具、饰品和法宝的穿戴属性。"
      hideHero
      registryTitle="装备清单"
      registryContent={
        <div className="section-grid">
          <div className="event-compact-toolbar">
            <div className="event-compact-toolbar__grid">
              <label className="field field--full">
                <span className="field__label">当前装备</span>
                <select
                  aria-label="当前装备"
                  value={selectedEquipmentId ?? ""}
                  onChange={(event) => {
                    setSelectedEquipmentId(event.target.value || null);
                    setStatusMessage(null);
                    setErrorMessage(null);
                  }}
                >
                  <option value="">选择已有装备</option>
                  {draftItem ? (
                    <option value={DRAFT_EQUIPMENT_ID}>
                      草稿：{draftItem.display_name || draftItem.equipment_id || "未命名装备"}
                    </option>
                  ) : null}
                  {items.map((item) => (
                    <option key={item.equipment_id} value={item.equipment_id}>
                      {item.display_name
                        ? `${item.display_name} / ${item.equipment_id}`
                        : item.equipment_id}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field field--full">
                <span className="field__label">新建装备 ID</span>
                <input
                  aria-label="新建装备 ID"
                  placeholder="例如 iron_sword"
                  value={pendingEquipmentId}
                  onChange={(event) => setPendingEquipmentId(event.target.value)}
                />
              </label>
            </div>

            <div className="event-compact-toolbar__actions event-compact-toolbar__actions--stack">
              <button className="button-secondary" type="button" onClick={handleCreateDraft}>
                新建装备
              </button>
              <button
                className="button-danger"
                disabled={!selectedEquipment || isDraft}
                type="button"
                onClick={() => void handleDelete()}
              >
                删除装备
              </button>
              <button
                className="button-primary"
                disabled={!selectedEquipment}
                type="button"
                onClick={() => void handleSave()}
              >
                保存装备
              </button>
            </div>
          </div>

          {items.length === 0 && !draftItem ? (
            <div className="empty-state">当前还没有装备，可先创建一个草稿。</div>
          ) : null}
        </div>
      }
      detailTitle={selectedEquipment?.display_name || "装备详情"}
      detailDescription="武器只填攻击；防具只填防御和气血；饰品、法宝只填特殊效果。"
      detailMeta={
        selectedEquipment ? (
          <div className="event-detail-chips">
            <span className="event-detail-chip">
              <small>装备 ID</small>
              <strong>{selectedEquipment.equipment_id || "未填写"}</strong>
            </span>
            <span className="event-detail-chip">
              <small>装备类型</small>
              <strong>{selectedSlot?.label ?? "未填写"}</strong>
            </span>
            <span className="event-detail-chip">
              <small>规则</small>
              <strong>{selectedSlot?.hint ?? "按类型限制属性"}</strong>
            </span>
          </div>
        ) : null
      }
      detailContent={
        selectedEquipment ? (
          <div className="section-grid">
            <section className="section-card">
              <div className="field-grid">
                <label className="field">
                  <span className="field__label">装备 ID</span>
                  <input
                    aria-label="装备 ID"
                    disabled={!isDraft}
                    value={selectedEquipment.equipment_id}
                    onChange={(event) => handleFieldChange("equipment_id", event.target.value)}
                  />
                </label>
                <label className="field">
                  <span className="field__label">装备名称</span>
                  <input
                    aria-label="装备名称"
                    value={selectedEquipment.display_name}
                    onChange={(event) => handleFieldChange("display_name", event.target.value)}
                  />
                </label>
                <label className="field">
                  <span className="field__label">装备类型</span>
                  <select
                    aria-label="装备类型"
                    value={selectedEquipment.slot}
                    onChange={(event) => handleSlotChange(event.target.value as EquipmentSlot)}
                  >
                    {slotOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field__label">攻击</span>
                  <input
                    aria-label="攻击"
                    disabled={selectedEquipment.slot !== "weapon"}
                    min={0}
                    type="number"
                    value={selectedEquipment.attack}
                    onChange={(event) =>
                      handleFieldChange("attack", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">防御</span>
                  <input
                    aria-label="防御"
                    disabled={selectedEquipment.slot !== "armor"}
                    min={0}
                    type="number"
                    value={selectedEquipment.defense}
                    onChange={(event) =>
                      handleFieldChange("defense", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">气血</span>
                  <input
                    aria-label="气血"
                    disabled={selectedEquipment.slot !== "armor"}
                    min={0}
                    type="number"
                    value={selectedEquipment.hp_max}
                    onChange={(event) =>
                      handleFieldChange("hp_max", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field field--full">
                  <span className="field__label">装备描述</span>
                  <textarea
                    aria-label="装备描述"
                    value={selectedEquipment.description}
                    onChange={(event) => handleFieldChange("description", event.target.value)}
                  />
                </label>
                <label className="field field--full">
                  <span className="field__label">特殊效果 JSON</span>
                  <textarea
                    aria-label="特殊效果 JSON"
                    disabled={
                      selectedEquipment.slot !== "accessory" &&
                      selectedEquipment.slot !== "artifact"
                    }
                    value={specialEffectsText}
                    onChange={(event) => setSpecialEffectsText(event.target.value)}
                  />
                </label>
              </div>
            </section>
          </div>
        ) : (
          <div className="empty-state">左侧选择一件装备后，即可在这里编辑穿戴属性。</div>
        )
      }
      statusPanel={
        <StatusPanel
          errorMessage={errorMessage}
          statusMessage={statusMessage}
        />
      }
    />
  );
}

function createEmptyEquipment(equipmentId = ""): EquipmentItemInput {
  return {
    equipment_id: equipmentId,
    display_name: "",
    slot: "weapon",
    description: "",
    attack: 1,
    defense: 0,
    hp_max: 0,
    special_effects: {},
  };
}

function normalizeEquipment(item: EquipmentItemInput): EquipmentItemInput {
  return normalizeEquipmentForSlot({
    ...createEmptyEquipment(item.equipment_id),
    ...item,
    equipment_id: String(item.equipment_id ?? "").trim(),
    display_name: String(item.display_name ?? "").trim(),
    slot: normalizeSlot(item.slot),
    description: String(item.description ?? "").trim(),
    attack: Math.max(0, Number(item.attack ?? 0) || 0),
    defense: Math.max(0, Number(item.defense ?? 0) || 0),
    hp_max: Math.max(0, Number(item.hp_max ?? 0) || 0),
    special_effects:
      item.special_effects &&
      typeof item.special_effects === "object" &&
      !Array.isArray(item.special_effects)
        ? item.special_effects
        : {},
  });
}

function normalizeEquipmentForSlot(item: EquipmentItemInput): EquipmentItemInput {
  if (item.slot === "weapon") {
    return {
      ...item,
      attack: Math.max(1, Number(item.attack ?? 1) || 1),
      defense: 0,
      hp_max: 0,
      special_effects: {},
    };
  }
  if (item.slot === "armor") {
    return {
      ...item,
      attack: 0,
      defense: Math.max(0, Number(item.defense ?? 0) || 0),
      hp_max: Math.max(0, Number(item.hp_max ?? 0) || 0),
      special_effects: {},
    };
  }
  if (item.slot === "accessory") {
    return {
      ...item,
      attack: 0,
      defense: 0,
      hp_max: 0,
      special_effects:
        Object.keys(item.special_effects ?? {}).length > 0
          ? item.special_effects
          : { luck: 1 },
    };
  }
  return {
    ...item,
    attack: 0,
    defense: 0,
    hp_max: 0,
    special_effects:
      Object.keys(item.special_effects ?? {}).length > 0
        ? item.special_effects
        : { artifact_effect: 1 },
  };
}

function normalizeSlot(slot: string): EquipmentSlot {
  if (slot === "weapon" || slot === "armor" || slot === "accessory" || slot === "artifact") {
    return slot;
  }
  return "weapon";
}

function parseSpecialEffects(value: string): Record<string, unknown> {
  const parsed = JSON.parse(value || "{}") as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("特殊效果必须是 JSON 对象。");
  }
  return parsed as Record<string, unknown>;
}
