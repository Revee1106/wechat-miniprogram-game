import type { EnemyTemplateInput } from "../api/client";
import { ResultPayloadEditor } from "./ResultPayloadEditor";
import { SectionCard } from "./SectionCard";

type BattleEnemyFormProps = {
  enemy: EnemyTemplateInput;
  isNew?: boolean;
  onChange: <K extends keyof EnemyTemplateInput>(
    field: K,
    value: EnemyTemplateInput[K]
  ) => void;
};

export function BattleEnemyForm({
  enemy,
  isNew = false,
  onChange,
}: BattleEnemyFormProps) {
  return (
    <div className="section-grid">
      <SectionCard
        title="敌人信息"
        description="维护敌人模板的基础标识、境界文案和战斗属性。"
      >
        <div className="field-grid field-grid--three">
          <label className="field">
            <span className="field__label">敌人 ID</span>
            <input
              aria-label="敌人 ID"
              placeholder="例如 enemy_bandit_qi_early"
              readOnly={!isNew}
              value={enemy.enemy_id}
              onChange={(event) => onChange("enemy_id", event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">敌人名称</span>
            <input
              aria-label="敌人名称"
              placeholder="例如 山匪"
              value={enemy.enemy_name}
              onChange={(event) => onChange("enemy_name", event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">境界文案</span>
            <input
              aria-label="境界文案"
              placeholder="例如 炼气初期"
              value={enemy.enemy_realm_label}
              onChange={(event) => onChange("enemy_realm_label", event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">气血</span>
            <input
              aria-label="气血"
              min={1}
              type="number"
              value={enemy.enemy_hp}
              onChange={(event) => onChange("enemy_hp", Math.max(1, Number(event.target.value) || 1))}
            />
          </label>

          <label className="field">
            <span className="field__label">攻击</span>
            <input
              aria-label="攻击"
              min={0}
              type="number"
              value={enemy.enemy_attack}
              onChange={(event) =>
                onChange("enemy_attack", Math.max(0, Number(event.target.value) || 0))
              }
            />
          </label>

          <label className="field">
            <span className="field__label">防御</span>
            <input
              aria-label="防御"
              min={0}
              type="number"
              value={enemy.enemy_defense}
              onChange={(event) =>
                onChange("enemy_defense", Math.max(0, Number(event.target.value) || 0))
              }
            />
          </label>

          <label className="field">
            <span className="field__label">速度</span>
            <input
              aria-label="速度"
              min={0}
              type="number"
              value={enemy.enemy_speed}
              onChange={(event) =>
                onChange("enemy_speed", Math.max(0, Number(event.target.value) || 0))
              }
            />
          </label>

          <label className="switch-field field--full">
            <span>
              <strong>允许逃跑</strong>
              <span className="field__hint">关闭后，战斗内不会提供逃跑分支。</span>
            </span>
            <input
              aria-label="允许逃跑"
              checked={enemy.allow_flee}
              type="checkbox"
              onChange={(event) => onChange("allow_flee", event.target.checked)}
            />
          </label>
        </div>
      </SectionCard>

      <SectionCard
        title="奖励配置"
        description="击败该敌人后默认发放的奖励，会在事件战斗胜利时直接结算。"
      >
        <ResultPayloadEditor
          labelPrefix="奖励"
          onChange={(value) => onChange("rewards", value)}
          payload={enemy.rewards}
        />
      </SectionCard>
    </div>
  );
}
