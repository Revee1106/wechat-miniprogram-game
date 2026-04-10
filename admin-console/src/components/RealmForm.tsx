import type { RealmFailurePenalty, RealmInput } from "../api/client";

export type RealmFormSection = "identity" | "breakthrough";

export const majorRealmOptions = [
  { value: "qi_refining", label: "炼气期" },
  { value: "foundation", label: "筑基期" },
  { value: "golden_core", label: "金丹期" },
  { value: "nascent_soul", label: "元婴期" },
];

type RealmFormProps = {
  realm: RealmInput;
  isNew: boolean;
  sections?: RealmFormSection[];
  onChange: <K extends keyof RealmInput>(field: K, value: RealmInput[K]) => void;
};

export function RealmForm({
  realm,
  isNew,
  sections = ["identity", "breakthrough"],
  onChange,
}: RealmFormProps) {
  const showIdentity = sections.includes("identity");
  const showBreakthrough = sections.includes("breakthrough");
  const isStartingRealm = realm.key === "qi_refining_early";
  const failurePenaltyMode = getFailurePenaltyMode(realm.failure_penalty);
  const failurePenaltyAmount = getFailurePenaltyAmount(realm.failure_penalty);

  function handleFailurePenaltyModeChange(mode: string) {
    if (mode === "cultivation_exp_loss") {
      onChange("failure_penalty", buildFailurePenalty(Math.max(failurePenaltyAmount, 10)));
      return;
    }
    onChange("failure_penalty", {});
  }

  function handleFailurePenaltyAmountChange(value: number) {
    onChange("failure_penalty", buildFailurePenalty(value));
  }

  return (
    <div className="realm-form">
      {showIdentity ? (
        <section className="section-card realm-form__section">
          <div className="section-card__header">
            <div>
              <h2>基础信息</h2>
              <p>配置境界名称、所属大境界、层级、排序和启用状态。</p>
            </div>
          </div>
          <div className="section-card__body">
            <div className="field-grid field-grid--three">
              <label className="field">
                <span className="field__label">内部标识</span>
                <input
                  aria-label="内部标识"
                  placeholder="例如 qi_refining_early"
                  readOnly={!isNew}
                  value={realm.key}
                  onChange={(event) => onChange("key", event.target.value)}
                />
              </label>
              <label className="field">
                <span className="field__label">展示名称</span>
                <input
                  aria-label="展示名称"
                  placeholder="例如 炼气初期"
                  value={realm.display_name}
                  onChange={(event) => onChange("display_name", event.target.value)}
                />
              </label>
              <label className="field">
                <span className="field__label">所属大境界</span>
                <select
                  aria-label="所属大境界"
                  value={realm.major_realm}
                  onChange={(event) => onChange("major_realm", event.target.value)}
                >
                  {majorRealmOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="field__label">小层级</span>
                <input
                  aria-label="小层级"
                  min={1}
                  step={1}
                  type="number"
                  value={realm.stage_index}
                  onChange={(event) => onChange("stage_index", Number(event.target.value) || 0)}
                />
              </label>
              <label className="field">
                <span className="field__label">排序</span>
                <input
                  aria-label="排序"
                  min={1}
                  step={1}
                  type="number"
                  value={realm.order_index}
                  onChange={(event) => onChange("order_index", Number(event.target.value) || 0)}
                />
              </label>
              <label className="field">
                <span className="field__label">每次推进基础修为增加</span>
                <input
                  aria-label="每次推进基础修为增加"
                  min={0}
                  step={1}
                  type="number"
                  value={realm.base_cultivation_gain_per_advance}
                  onChange={(event) =>
                    onChange(
                      "base_cultivation_gain_per_advance",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">每次推进灵石消耗</span>
                <input
                  aria-label="每次推进灵石消耗"
                  min={0}
                  step={1}
                  type="number"
                  value={realm.base_spirit_stone_cost_per_advance}
                  onChange={(event) =>
                    onChange(
                      "base_spirit_stone_cost_per_advance",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
              <label className="field field--full">
                <span className="field__label">启用状态</span>
                <input
                  aria-label="启用状态"
                  checked={realm.is_enabled}
                  type="checkbox"
                  onChange={(event) => onChange("is_enabled", event.target.checked)}
                />
              </label>
            </div>
          </div>
        </section>
      ) : null}

      {showBreakthrough ? (
        <section className="section-card realm-form__section">
          <div className="section-card__header">
            <div>
              <h2>突破配置</h2>
              <p>配置从上一层突破到当前境界时的消耗、成功率和失败惩罚。</p>
            </div>
          </div>
          <div className="section-card__body">
            {isStartingRealm ? (
              <div className="empty-state">
                <strong>当前为起始层，无需配置突破项。</strong>
                <p className="field__hint">角色开局即处于炼气初期，突破链从炼气中期开始配置。</p>
              </div>
            ) : (
              <div className="field-grid field-grid--three">
                <label className="field">
                  <span className="field__label">突破所需修为</span>
                  <input
                    aria-label="突破所需修为"
                    min={0}
                    step={1}
                    type="number"
                    value={realm.required_cultivation_exp}
                    onChange={(event) =>
                      onChange("required_cultivation_exp", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">突破所需灵石</span>
                  <input
                    aria-label="突破所需灵石"
                    min={0}
                    step={1}
                    type="number"
                    value={realm.required_spirit_stone}
                    onChange={(event) =>
                      onChange("required_spirit_stone", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">基础成功率</span>
                  <input
                    aria-label="基础成功率"
                    max={1}
                    min={0}
                    step={0.01}
                    type="number"
                    value={realm.base_success_rate}
                    onChange={(event) =>
                      onChange("base_success_rate", Number(event.target.value) || 0)
                    }
                  />
                </label>
                <label className="field">
                  <span className="field__label">寿元加成</span>
                  <input
                    aria-label="寿元加成"
                    min={0}
                    step={1}
                    type="number"
                    value={realm.lifespan_bonus}
                    onChange={(event) => onChange("lifespan_bonus", Number(event.target.value) || 0)}
                  />
                </label>
                <label className="field">
                  <span className="field__label">失败惩罚</span>
                  <select
                    aria-label="失败惩罚"
                    value={failurePenaltyMode}
                    onChange={(event) => handleFailurePenaltyModeChange(event.target.value)}
                  >
                    <option value="none">无惩罚</option>
                    <option value="cultivation_exp_loss">扣减修为</option>
                  </select>
                </label>
                {failurePenaltyMode === "cultivation_exp_loss" ? (
                  <label className="field">
                    <span className="field__label">失败扣减修为</span>
                    <input
                      aria-label="失败扣减修为"
                      min={1}
                      step={1}
                      type="number"
                      value={failurePenaltyAmount}
                      onChange={(event) =>
                        handleFailurePenaltyAmountChange(Number(event.target.value) || 0)
                      }
                    />
                  </label>
                ) : null}
              </div>
            )}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function getFailurePenaltyMode(penalty: RealmFailurePenalty | undefined): string {
  const amount = penalty?.character?.cultivation_exp ?? 0;
  return amount < 0 ? "cultivation_exp_loss" : "none";
}

function getFailurePenaltyAmount(penalty: RealmFailurePenalty | undefined): number {
  const amount = penalty?.character?.cultivation_exp ?? 0;
  return amount < 0 ? Math.abs(amount) : 10;
}

function buildFailurePenalty(amount: number): RealmFailurePenalty {
  const normalizedAmount = Math.max(0, Math.trunc(amount));
  if (normalizedAmount <= 0) {
    return {};
  }
  return {
    character: {
      cultivation_exp: -normalizedAmount,
    },
  };
}

export function formatMajorRealm(value: string | null | undefined): string {
  if (!value) {
    return "未设置";
  }
  return majorRealmOptions.find((option) => option.value === value)?.label ?? value;
}
