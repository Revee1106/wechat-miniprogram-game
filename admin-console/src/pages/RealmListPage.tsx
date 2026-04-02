import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  createRealm,
  deleteRealm,
  fetchRealms,
  reloadRealms,
  reorderRealms,
  updateRealm,
  type RealmConfig,
  type RealmInput,
} from "../api/client";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { formatMajorRealm, majorRealmOptions, RealmForm } from "../components/RealmForm";

const DRAFT_REALM_KEY = "__draft_realm__";

type RealmListPageProps = {
  refreshToken?: number;
  onCreateRealm?: () => void;
  onEditRealm?: (realmKey: string) => void;
};

type RealmPanel = "identity" | "breakthrough";

export function RealmListPage({ refreshToken = 0 }: RealmListPageProps) {
  const [items, setItems] = useState<RealmConfig[]>([]);
  const [draftRealm, setDraftRealm] = useState<RealmInput | null>(null);
  const [selectedRealmKey, setSelectedRealmKey] = useState<string | null>(null);
  const [pendingMajorRealm, setPendingMajorRealm] = useState("qi_refining");
  const [drawerPanel, setDrawerPanel] = useState<RealmPanel | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const response = await fetchRealms();
        if (!isMounted) {
          return;
        }
        const nextItems = response.items ?? [];
        setItems(nextItems);
        setStatusMessage(null);
        setErrorMessage(null);
        setSelectedRealmKey((current) => {
          if (current === DRAFT_REALM_KEY && draftRealm) {
            return current;
          }
          if (current && nextItems.some((item) => item.key === current)) {
            return current;
          }
          return nextItems[0]?.key ?? null;
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

  const selectedRealm = useMemo(() => {
    if (selectedRealmKey === DRAFT_REALM_KEY) {
      return draftRealm;
    }
    return items.find((item) => item.key === selectedRealmKey) ?? null;
  }, [draftRealm, items, selectedRealmKey]);

  const selectedRealmIndex = selectedRealmKey
    ? items.findIndex((item) => item.key === selectedRealmKey)
    : -1;
  const isDraft = selectedRealmKey === DRAFT_REALM_KEY;

  function updateSelectedRealm(nextRealm: RealmInput) {
    if (selectedRealmKey === DRAFT_REALM_KEY) {
      setDraftRealm(nextRealm);
      return;
    }
    setItems((current) =>
      current.map((item) => (item.key === nextRealm.key ? normalizeRealm(nextRealm) : item))
    );
  }

  function handleRealmChange<K extends keyof RealmInput>(field: K, value: RealmInput[K]) {
    if (!selectedRealm) {
      return;
    }
    updateSelectedRealm({
      ...selectedRealm,
      [field]: value,
    });
  }

  function handleCreateDraft() {
    setDraftRealm(createEmptyRealm(pendingMajorRealm));
    setSelectedRealmKey(DRAFT_REALM_KEY);
    setDrawerPanel("identity");
    setStatusMessage(null);
    setErrorMessage(null);
  }

  function handleSelectedRealmChange(value: string) {
    if (!value) {
      return;
    }
    setSelectedRealmKey(value);
    setDrawerPanel(null);
    setStatusMessage(null);
    setErrorMessage(null);
  }

  async function reloadListAndRuntime(selectedKey?: string | null, message?: string) {
    const [response, reloadResult] = await Promise.all([fetchRealms(), reloadRealms()]);
    const nextItems = response.items ?? [];
    setItems(nextItems);
    setSelectedRealmKey(selectedKey ?? nextItems[0]?.key ?? null);
    setStatusMessage(
      message ?? `已同步并重载运行时，当前载入 ${reloadResult.realm_count} 条境界配置。`
    );
  }

  async function handleSave() {
    if (!selectedRealm) {
      return;
    }

    const payload = normalizeRealm(selectedRealm);
    if (!payload.key.trim() || !payload.display_name.trim()) {
      setErrorMessage("境界标识和中文名称不能为空。");
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const saved = isDraft ? await createRealm(payload) : await updateRealm(payload.key, payload);
      setDraftRealm(null);
      await reloadListAndRuntime(saved.key, "已保存并自动重载运行时。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!selectedRealm || isDraft) {
      return;
    }
    if (!window.confirm(`确定删除境界 ${selectedRealm.display_name} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteRealm(selectedRealm.key);
      await reloadListAndRuntime(null, "已删除并自动重载运行时。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleMove(direction: -1 | 1) {
    if (!selectedRealm || isDraft) {
      return;
    }

    const targetIndex = selectedRealmIndex + direction;
    if (selectedRealmIndex < 0 || targetIndex < 0 || targetIndex >= items.length) {
      return;
    }

    const reordered = [...items];
    const [moved] = reordered.splice(selectedRealmIndex, 1);
    reordered.splice(targetIndex, 0, moved);

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const reorderResult = await reorderRealms(reordered.map((item) => item.key));
      setItems(reorderResult.items ?? reordered);
      const reloadResult = await reloadRealms();
      setStatusMessage(`排序已更新，并自动重载运行时。当前载入 ${reloadResult.realm_count} 条境界。`);
      setSelectedRealmKey(selectedRealm.key);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载境界配置...</div>;
  }

  return (
    <>
      <ConfigWorkbench
        className="config-workbench--compact"
        title="境界配置"
        description="左侧切换境界与保存，右侧通过模块按钮进入抽屉编辑。"
        hideHero
        registryTitle="境界清单"
        registryContent={
          <div className="section-grid">
            <div className="event-compact-toolbar">
              <div className="event-compact-toolbar__grid">
                <label className="field field--full">
                  <span className="field__label">当前境界</span>
                  <select
                    aria-label="当前境界"
                    value={selectedRealmKey ?? ""}
                    onChange={(event) => handleSelectedRealmChange(event.target.value)}
                  >
                    <option value="">选择已有境界</option>
                    {draftRealm ? (
                      <option value={DRAFT_REALM_KEY}>
                        草稿：{draftRealm.display_name || "未命名新境界"}
                      </option>
                    ) : null}
                    {items.map((item) => (
                      <option key={item.key} value={item.key}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field field--full">
                  <span className="field__label">按大境界新建</span>
                  <select
                    aria-label="按大境界新建"
                    value={pendingMajorRealm}
                    onChange={(event) => setPendingMajorRealm(event.target.value)}
                  >
                    {majorRealmOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="event-compact-toolbar__actions event-compact-toolbar__actions--stack">
                <button className="button-secondary" type="button" onClick={handleCreateDraft}>
                  新增境界
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => void handleMove(-1)}
                  disabled={!selectedRealm || isDraft || selectedRealmIndex <= 0}
                >
                  上移
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => void handleMove(1)}
                  disabled={
                    !selectedRealm || isDraft || selectedRealmIndex < 0 || selectedRealmIndex >= items.length - 1
                  }
                >
                  下移
                </button>
                <button
                  className="button-danger"
                  type="button"
                  onClick={() => void handleDelete()}
                  disabled={!selectedRealm || isDraft}
                >
                  删除境界
                </button>
                <button
                  className="button-primary"
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={!selectedRealm}
                >
                  保存境界
                </button>
              </div>
            </div>

            {items.length === 0 && !draftRealm ? (
              <div className="empty-state">当前还没有境界配置，可先创建一个草稿。</div>
            ) : null}
          </div>
        }
        detailTitle={selectedRealm?.display_name || "境界详情"}
        detailContent={
          selectedRealm ? (
            <div className="section-grid">
              {errorMessage ? (
                <div className="status-card__banner status-card__banner--error" role="alert">
                  {errorMessage}
                </div>
              ) : null}
              {statusMessage ? <div className="status-card__banner">{statusMessage}</div> : null}

              <div className="event-detail-chips">
                <span className="event-detail-chip">
                  <small>所属大境界</small>
                  <strong>{formatMajorRealm(selectedRealm.major_realm)}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>层级</small>
                  <strong>{`第 ${selectedRealm.stage_index} 层`}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>排序</small>
                  <strong>{`序号 ${selectedRealm.order_index}`}</strong>
                </span>
                <span className="event-detail-chip">
                  <small>状态</small>
                  <strong>{selectedRealm.is_enabled ? "已启用" : "已停用"}</strong>
                </span>
              </div>

              <div className="event-module-tabs" role="tablist" aria-label="境界详情模块">
                <button
                  aria-pressed={drawerPanel === "identity"}
                  className={drawerPanel === "identity" ? "event-module-tab event-module-tab--active" : "event-module-tab"}
                  type="button"
                  onClick={() => setDrawerPanel("identity")}
                >
                  基础信息
                </button>
                <button
                  aria-pressed={drawerPanel === "breakthrough"}
                  className={
                    drawerPanel === "breakthrough" ? "event-module-tab event-module-tab--active" : "event-module-tab"
                  }
                  type="button"
                  onClick={() => setDrawerPanel("breakthrough")}
                >
                  突破配置
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state">左侧选择境界后，可在这里打开对应模块进行编辑。</div>
          )
        }
        actionBar={undefined}
      />

      {selectedRealm && drawerPanel ? (
        <ConfigEditorDrawer
          description={getRealmPanelDescription(drawerPanel)}
          title={getRealmPanelTitle(drawerPanel)}
          onClose={() => setDrawerPanel(null)}
        >
          <RealmForm
            isNew={isDraft}
            onChange={handleRealmChange}
            realm={selectedRealm}
            sections={[drawerPanel]}
          />
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

function getRealmPanelTitle(panel: RealmPanel): string {
  switch (panel) {
    case "identity":
      return "基础信息";
    case "breakthrough":
      return "突破配置";
  }
}

function getRealmPanelDescription(panel: RealmPanel): string {
  switch (panel) {
    case "identity":
      return "编辑名称、所属大境界、层级与启用状态。";
    case "breakthrough":
      return "编辑突破所需修为、灵石与基础成功率。";
  }
}

function createEmptyRealm(majorRealm: string): RealmInput {
  return {
    key: "",
    display_name: "",
    major_realm: majorRealm,
    stage_index: 1,
    order_index: 1,
    base_success_rate: 0.95,
    required_cultivation_exp: 100,
    required_spirit_stone: 20,
    lifespan_bonus: 6,
    is_enabled: true,
  };
}

function normalizeRealm(realm: RealmInput): RealmInput {
  return {
    ...createEmptyRealm(realm.major_realm || "qi_refining"),
    ...realm,
    key: String(realm.key ?? "").trim(),
    display_name: String(realm.display_name ?? "").trim(),
    major_realm: String(realm.major_realm ?? "qi_refining"),
    stage_index: Number(realm.stage_index ?? 1) || 1,
    order_index: Number(realm.order_index ?? 1) || 1,
    base_success_rate: Number(realm.base_success_rate ?? 0) || 0,
    required_cultivation_exp: Number(realm.required_cultivation_exp ?? 0) || 0,
    required_spirit_stone: Number(realm.required_spirit_stone ?? 0) || 0,
    lifespan_bonus: Number(realm.lifespan_bonus ?? 0) || 0,
    is_enabled: realm.is_enabled === true,
  };
}
