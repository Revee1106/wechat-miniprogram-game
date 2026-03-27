import { useEffect, useState } from "react";

import {
  createRealm,
  deleteRealm,
  fetchRealmDetail,
  reloadRealms,
  updateRealm,
  validateRealms,
  type RealmInput,
  type ValidationResponse,
} from "../api/client";
import { RealmForm, formatMajorRealm } from "../components/RealmForm";
import { ValidationPanel } from "../components/ValidationPanel";

type RealmEditorPageProps = {
  realmKey?: string;
  onBack: () => void;
  onSaved: (realmKey: string) => void;
};

type EditorPanel = "identity" | "breakthrough" | null;

const PANEL_TITLES: Record<Exclude<EditorPanel, null>, string> = {
  identity: "基础信息",
  breakthrough: "突破配置",
};

export function RealmEditorPage({
  realmKey,
  onBack,
  onSaved,
}: RealmEditorPageProps) {
  const [realm, setRealm] = useState<RealmInput>(createEmptyRealm());
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activePanel, setActivePanel] = useState<EditorPanel>(null);

  const isNew = !realmKey;

  useEffect(() => {
    let isMounted = true;

    async function load() {
      if (!realmKey) {
        if (!isMounted) {
          return;
        }
        setRealm(createEmptyRealm());
        setValidation(null);
        setStatusMessage(null);
        setErrorMessage(null);
        setActivePanel(null);
        return;
      }

      setIsLoading(true);
      try {
        const detail = await fetchRealmDetail(realmKey);
        if (!isMounted) {
          return;
        }
        setRealm(normalizeRealm(detail));
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
  }, [realmKey]);

  const realmSummary = `${formatMajorRealm(realm.major_realm)} · 第${realm.stage_index || 0}层 · 排序 ${
    realm.order_index || 0
  }`;

  async function handleSave() {
    setErrorMessage(null);
    setStatusMessage(null);

    const realmKeyValue = realmKey ? realmKey.trim() : realm.key.trim();
    const displayNameValue = realm.display_name.trim();

    if (!realmKeyValue || !displayNameValue) {
      setErrorMessage("内部标识和展示名称不能为空。");
      return;
    }

    const payload = normalizeRealm({
      ...realm,
      key: realmKeyValue,
      display_name: displayNameValue,
    });

    try {
      const savedRealm = realmKey
        ? await updateRealm(realmKey, payload)
        : await createRealm(payload);

      setRealm(normalizeRealm(savedRealm));
      try {
        const result = await reloadRealms();
        setStatusMessage(
          `境界已保存，并已重载运行时。当前共载入 ${result.realm_count} 条境界。`
        );
      } catch (reloadError) {
        setStatusMessage("境界已保存，但运行时重载失败，请手动点击“重载运行时”。");
        setErrorMessage((reloadError as Error).message);
      }
      onSaved(savedRealm.key || realmKeyValue);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleValidate() {
    try {
      setErrorMessage(null);
      setValidation(await validateRealms());
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleReload() {
    try {
      setErrorMessage(null);
      const result = await reloadRealms();
      setStatusMessage(`境界配置已重载，共载入 ${result.realm_count} 条境界。`);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!realmKey) {
      return;
    }
    if (!window.confirm(`确定删除境界 ${realmKey} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteRealm(realmKey);
      onBack();
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  function handleChange<K extends keyof RealmInput>(field: K, value: RealmInput[K]) {
    setRealm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  if (isLoading) {
    return <div className="page-loading">正在加载境界内容...</div>;
  }

  return (
    <main className="section-grid workbench-page">
      <section className="hero-panel">
        <div className="section-card__body">
          <div>
            <h1>{realmKey ? "境界工坊" : "新建境界"}</h1>
            <p>
              {realmKey
                ? "按模块进入二级编辑层，减少长页滚动。修改完成后直接重载即可生效。"
                : "先填写基础信息，再补充突破配置，保存后即可加入当前境界谱册。"}
            </p>
          </div>
          <div className="chip-row">
            <span className="chip">展示名称 {realm.display_name || "未命名境界"}</span>
            <span className="chip chip--soft">内部标识 {realm.key || "待填写"}</span>
            <span className="chip chip--soft">{realmSummary}</span>
            <span className="chip chip--soft">{realm.is_enabled ? "开放中" : "关闭"}</span>
          </div>
        </div>

        <div className="section-card__body">
          <div className="toolbar">
            <button className="button-primary" type="button" onClick={() => setActivePanel("identity")}>
              编辑基础信息
            </button>
            <button
              className="button-secondary"
              type="button"
              onClick={() => setActivePanel("breakthrough")}
            >
              编辑突破配置
            </button>
          </div>
          <p className="field__hint">
            内部标识创建后锁定，后续只需要维护中文名称、排序和突破参数。若被事件引用，删除或关闭会被后端拦截。
          </p>
        </div>
      </section>

      <section className="workbench-grid">
        <WorkbenchCard
          buttonText="编辑基础信息"
          description="境界中文名、所属大境界、小层级、排序和开放状态。"
          summary={`${realm.display_name || "未命名境界"} · ${formatMajorRealm(realm.major_realm)}`}
          title="基础信息"
          onClick={() => setActivePanel("identity")}
        />
        <WorkbenchCard
          buttonText="编辑突破配置"
          description="突破所需修为、灵石、基础成功率与寿元加成。"
          summary={`修为 ${realm.required_cultivation_exp || 0} · 灵石 ${realm.required_spirit_stone || 0}`}
          title="突破配置"
          onClick={() => setActivePanel("breakthrough")}
        />
      </section>

      <ValidationPanel
        errorMessage={errorMessage}
        statusMessage={statusMessage}
        validation={validation}
      />

      <footer className="editor-footer">
        <div className="editor-footer__meta">
          <strong>{realm.display_name || "未命名境界"}</strong>
          <span>{realmKey ? "编辑中" : "新建中"} · {realm.key || "等待填写内部标识"}</span>
        </div>
        <div className="toolbar">
          <button className="button-secondary" type="button" onClick={onBack}>
            返回境界谱册
          </button>
          <button className="button-accent" type="button" onClick={() => void handleValidate()}>
            校验配置
          </button>
          <button className="button-secondary" type="button" onClick={() => void handleReload()}>
            重载运行时
          </button>
          <button className="button-primary" type="button" onClick={() => void handleSave()}>
            保存境界
          </button>
          {realmKey ? (
            <button className="button-danger" type="button" onClick={() => void handleDelete()}>
              删除境界
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
                <p>完成当前模块后返回工作台即可，修改内容会保留在本地状态中。</p>
              </div>
              <button className="button-secondary" type="button" onClick={() => setActivePanel(null)}>
                完成编辑
              </button>
            </header>
            <div className="editor-dialog__body">
              {activePanel === "identity" ? (
                <RealmForm
                  isNew={isNew}
                  onChange={handleChange}
                  realm={realm}
                  sections={["identity"]}
                />
              ) : null}
              {activePanel === "breakthrough" ? (
                <RealmForm
                  isNew={isNew}
                  onChange={handleChange}
                  realm={realm}
                  sections={["breakthrough"]}
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

function createEmptyRealm(): RealmInput {
  return {
    key: "",
    display_name: "",
    major_realm: "qi_refining",
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
    ...createEmptyRealm(),
    ...realm,
    key: String(realm.key ?? "").trim(),
    display_name: String(realm.display_name ?? "").trim(),
    major_realm: String(realm.major_realm ?? "qi_refining"),
    stage_index: Number(realm.stage_index ?? 0) || 0,
    order_index: Number(realm.order_index ?? 0) || 0,
    base_success_rate: Number(realm.base_success_rate ?? 0) || 0,
    required_cultivation_exp: Number(realm.required_cultivation_exp ?? 0) || 0,
    required_spirit_stone: Number(realm.required_spirit_stone ?? 0) || 0,
    lifespan_bonus: Number(realm.lifespan_bonus ?? 0) || 0,
    is_enabled: realm.is_enabled === true,
  };
}
