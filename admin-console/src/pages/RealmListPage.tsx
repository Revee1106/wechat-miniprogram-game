import { useEffect, useState } from "react";

import {
  deleteRealm,
  fetchRealms,
  reloadRealms,
  reorderRealms,
  validateRealms,
  type RealmConfig,
  type ValidationResponse,
} from "../api/client";
import { formatMajorRealm } from "../components/RealmForm";
import { ValidationPanel } from "../components/ValidationPanel";

type RealmListPageProps = {
  refreshToken?: number;
  onCreateRealm: () => void;
  onEditRealm: (realmKey: string) => void;
};

export function RealmListPage({
  refreshToken = 0,
  onCreateRealm,
  onEditRealm,
}: RealmListPageProps) {
  const [items, setItems] = useState<RealmConfig[]>([]);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
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
        setItems(response.items ?? []);
        setValidation(null);
        setStatusMessage(null);
        setErrorMessage(null);
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

  const enabledCount = items.filter((item) => item.is_enabled).length;
  const majorRealmCount = new Set(items.map((item) => item.major_realm)).size;

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
      setStatusMessage(`境界配置已重载，当前共载入 ${result.realm_count} 条境界。`);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete(realmKey: string) {
    if (!window.confirm(`确定删除境界 ${realmKey} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      await deleteRealm(realmKey);
      const [response, reloadResult] = await Promise.all([fetchRealms(), reloadRealms()]);
      setItems(response.items ?? []);
      setStatusMessage(`已删除境界 ${realmKey}，并已重载运行时。当前共载入 ${reloadResult.realm_count} 条境界。`);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleMove(realmKey: string, direction: -1 | 1) {
    const index = items.findIndex((item) => item.key === realmKey);
    const targetIndex = index + direction;
    if (index < 0 || targetIndex < 0 || targetIndex >= items.length) {
      return;
    }

    const reordered = [...items];
    const [moved] = reordered.splice(index, 1);
    reordered.splice(targetIndex, 0, moved);

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const reorderResult = await reorderRealms(reordered.map((item) => item.key));
      setItems(reorderResult.items ?? reordered);

      try {
        const reloadResult = await reloadRealms();
        setStatusMessage(
          `排序已更新，并已重载运行时。当前共载入 ${reloadResult.realm_count} 条境界。`
        );
      } catch (reloadError) {
        setStatusMessage("排序已更新，但运行时重载失败，请手动点击“重载运行时”。");
        setErrorMessage((reloadError as Error).message);
      }
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载境界谱册...</div>;
  }

  return (
    <main className="section-grid">
      <section className="hero-panel">
        <div className="section-card__body">
          <div>
            <h1>境界谱册</h1>
            <p>维护当前开放的境界链路、突破门槛和排序。排序结果会直接决定逐级突破的顺序。</p>
          </div>
          <div className="chip-row">
            <span className="chip">当前开放 {enabledCount}/{items.length || 0}</span>
            <span className="chip chip--soft">大境界 {majorRealmCount || 0} 组</span>
            <span className="chip chip--soft">按排序决定突破顺序</span>
          </div>
        </div>
        <div className="section-card__body">
          <div className="toolbar">
            <button className="button-primary" type="button" onClick={onCreateRealm}>
              新建境界
            </button>
            <button className="button-accent" type="button" onClick={() => void handleValidate()}>
              校验配置
            </button>
            <button className="button-secondary" type="button" onClick={() => void handleReload()}>
              重载运行时
            </button>
          </div>
          <p className="field__hint">
            删除或停用被事件引用的境界会被后端拦截。你可以先在这里调整顺序，再用按钮把新顺序实时推入运行时。
          </p>
        </div>
      </section>

      <ValidationPanel
        errorMessage={errorMessage}
        statusMessage={statusMessage}
        validation={validation}
      />

      {items.length === 0 ? (
        <div className="empty-state">当前还没有境界配置，先创建第一条可开放的境界节点。</div>
      ) : (
        <div className="library-grid">
          {items.map((item, index) => (
            <article key={item.key} className="library-card">
              <header className="library-card__header">
                <h3>{item.display_name}</h3>
                <div className="library-card__id">内部标识 {item.key}</div>
              </header>

              <div className="chip-row">
                <span className="chip">所属大境界 {formatMajorRealm(item.major_realm)}</span>
                <span className="chip">小层级 {item.stage_index}</span>
                <span className="chip">排序 {item.order_index}</span>
              </div>

              <dl className="kv-grid">
                <div className="kv-item">
                  <dt>突破所需修为</dt>
                  <dd>{item.required_cultivation_exp}</dd>
                </div>
                <div className="kv-item">
                  <dt>突破所需灵石</dt>
                  <dd>{item.required_spirit_stone}</dd>
                </div>
                <div className="kv-item">
                  <dt>基础成功率</dt>
                  <dd>{Math.round(item.base_success_rate * 100)}%</dd>
                </div>
                <div className="kv-item">
                  <dt>寿元加成</dt>
                  <dd>{item.lifespan_bonus}</dd>
                </div>
                <div className="kv-item">
                  <dt>是否开放</dt>
                  <dd>{item.is_enabled ? "是" : "否"}</dd>
                </div>
              </dl>

              <div className="chip-row">
                <span className="chip chip--soft">{item.is_enabled ? "开放中" : "已关闭"}</span>
              </div>

              <div className="toolbar">
                <button
                  aria-label={`move-up ${item.key}`}
                  className="button-secondary"
                  disabled={index === 0}
                  type="button"
                  onClick={() => void handleMove(item.key, -1)}
                >
                  上移
                </button>
                <button
                  aria-label={`move-down ${item.key}`}
                  className="button-secondary"
                  disabled={index === items.length - 1}
                  type="button"
                  onClick={() => void handleMove(item.key, 1)}
                >
                  下移
                </button>
                <button
                  className="button-primary"
                  type="button"
                  onClick={() => onEditRealm(item.key)}
                >
                  编辑境界
                </button>
                <button
                  className="button-danger"
                  type="button"
                  onClick={() => void handleDelete(item.key)}
                >
                  删除境界
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
