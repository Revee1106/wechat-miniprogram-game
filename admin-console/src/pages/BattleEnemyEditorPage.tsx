import { useEffect, useState } from "react";

import {
  createBattleEnemy,
  fetchBattleEnemyDetail,
  reloadBattleEnemies,
  updateBattleEnemy,
  type EnemyTemplateInput,
} from "../api/client";
import { BattleEnemyForm } from "../components/BattleEnemyForm";

type BattleEnemyEditorPageProps = {
  enemyId?: string;
  onBack: () => void;
  onSaved: (enemyId: string) => void;
};

export function BattleEnemyEditorPage({
  enemyId,
  onBack,
  onSaved,
}: BattleEnemyEditorPageProps) {
  const [enemy, setEnemy] = useState<EnemyTemplateInput>(createEmptyEnemy(enemyId ?? ""));
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      if (!enemyId) {
        setEnemy(createEmptyEnemy());
        return;
      }

      setIsLoading(true);
      try {
        const detail = await fetchBattleEnemyDetail(enemyId);
        if (!isMounted) {
          return;
        }
        setEnemy(normalizeEnemy(detail));
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
  }, [enemyId]);

  function handleChange<K extends keyof EnemyTemplateInput>(
    field: K,
    value: EnemyTemplateInput[K]
  ) {
    setEnemy((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSave() {
    const payload = normalizeEnemy(enemy);
    if (!payload.enemy_id.trim() || !payload.enemy_name.trim()) {
      setErrorMessage("敌人 ID 和敌人名称不能为空。");
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const savedEnemy = enemyId
        ? await updateBattleEnemy(enemyId, payload)
        : await createBattleEnemy(payload);
      setEnemy(normalizeEnemy(savedEnemy));
      const reloadResult = await reloadBattleEnemies();
      setStatusMessage(`敌人模板已保存，当前载入 ${reloadResult.enemy_count} 个敌人模板。`);
      onSaved(savedEnemy.enemy_id);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading) {
    return <div className="page-loading">正在加载战斗配置...</div>;
  }

  return (
    <main className="section-grid workbench-page">
      <section className="hero-panel">
        <div className="section-card__body">
          <div>
            <h1>战斗工坊</h1>
            <p>维护敌人模板的数值、逃跑开关和默认战利品。</p>
          </div>
          <div className="chip-row">
            <span className="chip">敌人 {enemy.enemy_name || "未命名敌人"}</span>
            <span className="chip chip--soft">模板 ID {enemy.enemy_id || "待填写"}</span>
          </div>
        </div>

        <div className="section-card__body">
          {statusMessage ? <div className="status-card__banner">{statusMessage}</div> : null}
          {errorMessage ? (
            <div className="status-card__banner status-card__banner--error" role="alert">
              {errorMessage}
            </div>
          ) : null}
          <div className="toolbar">
            <button className="button-secondary" type="button" onClick={onBack}>
              返回战斗配置
            </button>
            <button className="button-primary" type="button" onClick={() => void handleSave()}>
              保存敌人模板
            </button>
          </div>
        </div>
      </section>

      <BattleEnemyForm enemy={enemy} isNew={!enemyId} onChange={handleChange} />
    </main>
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
