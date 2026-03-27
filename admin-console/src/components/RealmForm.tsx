import type { RealmInput } from "../api/client";

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

  return (
    <div className="realm-form">
      {showIdentity ? (
        <section className="section-card realm-form__section">
          <div className="section-card__header">
            <div>
              <h2>基础信息</h2>
              <p>控制境界的中文展示、所属大境界、层级和开放状态。内部标识创建后锁定不可改。</p>
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
              <label className="field field--full">
                <span className="field__label">是否开放</span>
                <input
                  aria-label="是否开放"
                  checked={realm.is_enabled}
                  type="checkbox"
                  onChange={(event) => onChange("is_enabled", event.target.checked)}
                />
              </label>
            </div>
            <p className="field__hint">
              新建境界时先填内部标识和中文名称，再设定所属大境界与排序，保存后即可参与突破链和事件筛选。
            </p>
          </div>
        </section>
      ) : null}

      {showBreakthrough ? (
        <section className="section-card realm-form__section">
          <div className="section-card__header">
            <div>
              <h2>突破配置</h2>
              <p>控制从当前境界迈向下一层时需要消耗的修为、灵石和基础成功率。</p>
            </div>
          </div>
          <div className="section-card__body">
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
              <div className="field field--full">
                <span className="field__label">说明</span>
                <p className="field__hint">
                  突破链会按照排序中的下一条境界继续前进。若当前境界被事件引用，删除或关闭会被后端拦截。
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}

export function formatMajorRealm(value: string | null | undefined): string {
  if (!value) {
    return "未设置";
  }
  return majorRealmOptions.find((option) => option.value === value)?.label ?? value;
}
