import { useEffect, useMemo, useState } from "react";

import {
  createBattleEnemy,
  deleteBattleEnemy,
  fetchBattleEnemies,
  fetchBattleEnemyDetail,
  reloadBattleEnemies,
  updateBattleEnemy,
  validateBattleEnemies,
  type EnemyTemplateInput,
  type ValidationResponse,
} from "../api/client";
import { BattleEnemyForm } from "../components/BattleEnemyForm";
import { ConfigWorkbench } from "../components/ConfigWorkbench";
import { ValidationPanel } from "../components/ValidationPanel";

const DRAFT_ENEMY_ID = "__draft_enemy__";

type BattleEnemyListPageProps = {
  refreshToken?: number;
};

export function BattleEnemyListPage({ refreshToken = 0 }: BattleEnemyListPageProps) {
  const [items, setItems] = useState<EnemyTemplateInput[]>([]);
  const [draftEnemy, setDraftEnemy] = useState<EnemyTemplateInput | null>(null);
  const [selectedEnemyId, setSelectedEnemyId] = useState<string | null>(null);
  const [pendingEnemyId, setPendingEnemyId] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const response = await fetchBattleEnemies();
        if (!isMounted) {
          return;
        }
        const nextItems = response.items ?? [];
        setItems(nextItems);
        setStatusMessage(null);
        setErrorMessage(null);
        setValidation(null);
        setSelectedEnemyId((current) => {
          if (current === DRAFT_ENEMY_ID) {
            return current;
          }
          if (current && nextItems.some((item) => item.enemy_id === current)) {
            return current;
          }
          return nextItems[0]?.enemy_id ?? null;
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
      if (!selectedEnemyId || selectedEnemyId === DRAFT_ENEMY_ID) {
        return;
      }

      try {
        const detail = await fetchBattleEnemyDetail(selectedEnemyId);
        if (!isMounted) {
          return;
        }
        setItems((current) =>
          current.map((item) =>
            item.enemy_id === selectedEnemyId ? normalizeEnemy(detail) : item
          )
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
  }, [selectedEnemyId]);

  const selectedEnemy = useMemo(() => {
    if (selectedEnemyId === DRAFT_ENEMY_ID) {
      return draftEnemy;
    }
    return items.find((item) => item.enemy_id === selectedEnemyId) ?? null;
  }, [draftEnemy, items, selectedEnemyId]);

  const isDraft = selectedEnemyId === DRAFT_ENEMY_ID;

  function updateSelectedEnemy(nextEnemy: EnemyTemplateInput) {
    if (selectedEnemyId === DRAFT_ENEMY_ID) {
      setDraftEnemy(nextEnemy);
      return;
    }
    setItems((current) =>
      current.map((item) =>
        item.enemy_id === nextEnemy.enemy_id ? normalizeEnemy(nextEnemy) : item
      )
    );
  }

  function handleEnemyChange<K extends keyof EnemyTemplateInput>(
    field: K,
    value: EnemyTemplateInput[K]
  ) {
    if (!selectedEnemy) {
      return;
    }
    updateSelectedEnemy({
      ...selectedEnemy,
      [field]: value,
    });
  }

  function handleSelectedEnemyChange(value: string) {
    if (!value) {
      return;
    }
    setSelectedEnemyId(value);
    setStatusMessage(null);
    setErrorMessage(null);
  }

  function handleCreateDraft() {
    const enemyId = pendingEnemyId.trim();
    if (enemyId && items.some((item) => item.enemy_id === enemyId)) {
      setErrorMessage(`敌人模板 ${enemyId} 已存在。`);
      return;
    }

    setDraftEnemy(createEmptyEnemy(enemyId));
    setSelectedEnemyId(DRAFT_ENEMY_ID);
    setPendingEnemyId("");
    setStatusMessage(null);
    setErrorMessage(null);
    setValidation(null);
  }

  async function reloadListAndRuntime(selectedId?: string | null, message?: string) {
    const [response, reloadResult] = await Promise.all([
      fetchBattleEnemies(),
      reloadBattleEnemies(),
    ]);
    const nextItems = response.items ?? [];
    setItems(nextItems);
    setSelectedEnemyId(selectedId ?? nextItems[0]?.enemy_id ?? null);
    setDraftEnemy(null);
    setStatusMessage(
      message ?? `已同步并重载运行时，当前载入 ${reloadResult.enemy_count} 个敌人模板。`
    );
  }

  async function handleSave() {
    if (!selectedEnemy) {
      return;
    }

    const payload = normalizeEnemy(selectedEnemy);
    if (!payload.enemy_id.trim() || !payload.enemy_name.trim()) {
      setErrorMessage("敌人 ID 和敌人名称不能为空。");
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      setValidation(null);
      const savedEnemy = isDraft
        ? await createBattleEnemy(payload)
        : await updateBattleEnemy(payload.enemy_id, payload);
      await reloadListAndRuntime(savedEnemy.enemy_id, "已保存敌人模板并自动重载运行时。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleDelete() {
    if (!selectedEnemy || isDraft) {
      return;
    }
    if (!window.confirm(`确定删除敌人模板 ${selectedEnemy.enemy_name} 吗？`)) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      setValidation(null);
      await deleteBattleEnemy(selectedEnemy.enemy_id);
      await reloadListAndRuntime(null, "已删除敌人模板并自动重载运行时。");
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleValidate() {
    try {
      setErrorMessage(null);
      setValidation(await validateBattleEnemies());
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  async function handleReload() {
    try {
      setErrorMessage(null);
      const result = await reloadBattleEnemies();
      setStatusMessage(`已重载运行时，当前载入 ${result.enemy_count} 个敌人模板。`);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载战斗配置...</div>;
  }

  return (
    <ConfigWorkbench
      className="config-workbench--compact"
      title="战斗配置"
      description="独立维护敌人模板，事件战斗选项只引用模板 ID。"
      hideHero
      registryTitle="敌人模板"
      registryContent={
        <div className="section-grid">
          <div className="event-compact-toolbar">
            <div className="event-compact-toolbar__grid">
              <label className="field field--full">
                <span className="field__label">当前敌人模板</span>
                <select
                  aria-label="当前敌人模板"
                  value={selectedEnemyId ?? ""}
                  onChange={(event) => handleSelectedEnemyChange(event.target.value)}
                >
                  <option value="">选择已有敌人模板</option>
                  {draftEnemy ? (
                    <option value={DRAFT_ENEMY_ID}>
                      草稿：{draftEnemy.enemy_name || draftEnemy.enemy_id || "未命名敌人"}
                    </option>
                  ) : null}
                  {items.map((item) => (
                    <option key={item.enemy_id} value={item.enemy_id}>
                      {item.enemy_name ? `${item.enemy_name} / ${item.enemy_id}` : item.enemy_id}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field field--full">
                <span className="field__label">新建敌人 ID</span>
                <input
                  aria-label="新建敌人 ID"
                  placeholder="例如 enemy_bandit_qi_early"
                  value={pendingEnemyId}
                  onChange={(event) => setPendingEnemyId(event.target.value)}
                />
              </label>
            </div>

            <div className="event-compact-toolbar__actions event-compact-toolbar__actions--stack">
              <button className="button-secondary" type="button" onClick={handleCreateDraft}>
                新建敌人模板
              </button>
              <button className="button-accent" type="button" onClick={() => void handleValidate()}>
                校验配置
              </button>
              <button className="button-secondary" type="button" onClick={() => void handleReload()}>
                重载运行时
              </button>
              <button
                className="button-danger"
                disabled={!selectedEnemy || isDraft}
                type="button"
                onClick={() => void handleDelete()}
              >
                删除敌人模板
              </button>
              <button
                className="button-primary"
                disabled={!selectedEnemy}
                type="button"
                onClick={() => void handleSave()}
              >
                保存敌人模板
              </button>
            </div>
          </div>

          {items.length === 0 && !draftEnemy ? (
            <div className="empty-state">当前还没有敌人模板，可先创建一个草稿。</div>
          ) : null}
        </div>
      }
      detailTitle={selectedEnemy?.enemy_name || "敌人详情"}
      detailContent={
        selectedEnemy ? (
          <div className="section-grid">
            <div className="event-detail-chips">
              <span className="event-detail-chip">
                <small>敌人 ID</small>
                <strong>{selectedEnemy.enemy_id || "未填写"}</strong>
              </span>
              <span className="event-detail-chip">
                <small>境界</small>
                <strong>{selectedEnemy.enemy_realm_label || "未填写"}</strong>
              </span>
              <span className="event-detail-chip">
                <small>战斗属性</small>
                <strong>
                  {`气血 ${selectedEnemy.enemy_hp} / 攻 ${selectedEnemy.enemy_attack} / 防 ${selectedEnemy.enemy_defense} / 速 ${selectedEnemy.enemy_speed}`}
                </strong>
              </span>
              <span className="event-detail-chip">
                <small>逃跑</small>
                <strong>{selectedEnemy.allow_flee ? "允许" : "禁止"}</strong>
              </span>
            </div>

            <BattleEnemyForm
              enemy={selectedEnemy}
              isNew={isDraft}
              onChange={handleEnemyChange}
            />
          </div>
        ) : (
          <div className="empty-state">左侧选择一个敌人模板后，即可在这里编辑战斗属性和奖励。</div>
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

function createEmptyEnemy(enemyId = ""): EnemyTemplateInput {
  return {
    enemy_id: enemyId,
    enemy_name: "",
    enemy_realm_label: "",
    enemy_hp: 1,
    enemy_attack: 0,
    enemy_defense: 0,
    enemy_speed: 0,
    allow_flee: true,
    rewards: {},
  };
}

function normalizeEnemy(enemy: EnemyTemplateInput): EnemyTemplateInput {
  return {
    ...createEmptyEnemy(enemy.enemy_id),
    ...enemy,
    enemy_id: String(enemy.enemy_id ?? "").trim(),
    enemy_name: String(enemy.enemy_name ?? "").trim(),
    enemy_realm_label: String(enemy.enemy_realm_label ?? "").trim(),
    enemy_hp: Math.max(1, Number(enemy.enemy_hp ?? 1) || 1),
    enemy_attack: Math.max(0, Number(enemy.enemy_attack ?? 0) || 0),
    enemy_defense: Math.max(0, Number(enemy.enemy_defense ?? 0) || 0),
    enemy_speed: Math.max(0, Number(enemy.enemy_speed ?? 0) || 0),
    allow_flee: enemy.allow_flee === true,
    rewards:
      enemy.rewards && typeof enemy.rewards === "object" && !Array.isArray(enemy.rewards)
        ? enemy.rewards
        : {},
  };
}
