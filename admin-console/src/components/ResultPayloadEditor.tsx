import {
  buildPayloadFromEditorState,
  formatLineList,
  parseLineList,
  parseNumberInput,
  parsePayloadEditorState,
  type PayloadEditorState,
} from "../utils/eventFormCodec";
import { resourceOptions, sortResourceRecord } from "../utils/resourceCatalog";

type ResultPayloadEditorProps = {
  labelPrefix: string;
  payload: Record<string, unknown> | string | undefined;
  onChange: (value: Record<string, unknown>) => void;
};

export function ResultPayloadEditor({
  labelPrefix,
  payload,
  onChange,
}: ResultPayloadEditorProps) {
  const state = parsePayloadEditorState(payload);
  const resourceEntries = Object.entries(sortResourceRecord(state.resources));
  const usedResourceKeys = resourceEntries.map(([key]) => key);
  const canAddResource = usedResourceKeys.length < resourceOptions.length;

  function update(partial: Partial<PayloadEditorState>) {
    onChange(
      buildPayloadFromEditorState({
        ...state,
        ...partial,
      })
    );
  }

  function updateResources(entries: Array<[string, number]>) {
    const resources = Object.fromEntries(
      entries.filter(([key, amount]) => key && Number.isFinite(amount) && amount !== 0)
    );
    update({ resources });
  }

  function handleAddResource() {
    const nextResource = resourceOptions.find(
      (option) => !usedResourceKeys.includes(option.value)
    );
    if (!nextResource) {
      return;
    }
    updateResources([...resourceEntries, [nextResource.value, 1]]);
  }

  function handleResourceKeyChange(index: number, nextKey: string) {
    const nextEntries = resourceEntries.map(([key, amount], entryIndex) =>
      entryIndex === index ? [nextKey, amount] : [key, amount]
    ) as Array<[string, number]>;
    updateResources(nextEntries);
  }

  function handleResourceAmountChange(index: number, nextAmount: string) {
    const nextEntries = resourceEntries.map(([key, amount], entryIndex) =>
      entryIndex === index ? [key, parseNumberInput(nextAmount, 0)] : [key, amount]
    ) as Array<[string, number]>;
    updateResources(nextEntries);
  }

  function handleRemoveResource(index: number) {
    updateResources(resourceEntries.filter((_, entryIndex) => entryIndex !== index));
  }

  return (
    <div className="field-grid">
      <div className="field field--full resource-editor">
        <div className="field__label">
          <span>{labelPrefix}资源变化</span>
          <button
            className="button-secondary"
            disabled={!canAddResource}
            type="button"
            onClick={handleAddResource}
          >
            新增资源变化
          </button>
        </div>
        <div className="resource-editor__stack">
          {resourceEntries.length > 0 ? (
            resourceEntries.map(([resourceKey, amount], index) => (
              <div key={resourceKey} className="resource-row">
                <label className="field">
                  <span className="field__hint">资源名称</span>
                  <select
                    aria-label={`${labelPrefix}资源类型-${index + 1}`}
                    value={resourceKey}
                    onChange={(event) => handleResourceKeyChange(index, event.target.value)}
                  >
                    {resourceOptions.map((option) => {
                      const isTakenByAnother =
                        usedResourceKeys.includes(option.value) && option.value !== resourceKey;
                      return (
                        <option
                          key={option.value}
                          disabled={isTakenByAnother}
                          value={option.value}
                        >
                          {option.label}
                        </option>
                      );
                    })}
                  </select>
                </label>

                <label className="field">
                  <span className="field__hint">增减数值</span>
                  <input
                    aria-label={`${labelPrefix}资源数值-${index + 1}`}
                    type="number"
                    value={amount}
                    onChange={(event) => handleResourceAmountChange(index, event.target.value)}
                  />
                </label>

                <button
                  className="button-secondary resource-row__remove"
                  type="button"
                  onClick={() => handleRemoveResource(index)}
                >
                  删除
                </button>
              </div>
            ))
          ) : (
            <div className="resource-editor__empty">
              暂未配置资源变化，可通过“新增资源变化”补充收益或消耗。
            </div>
          )}
        </div>
        <span className="field__hint">
          只支持系统内已定义的资源类型。正数表示获得，负数表示消耗。
        </span>
      </div>

      <label className="field">
        <span className="field__label">{labelPrefix}修为变化</span>
        <input
          aria-label={`${labelPrefix}修为变化`}
          type="number"
          value={state.cultivation_exp}
          onChange={(event) =>
            update({ cultivation_exp: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}寿元变化</span>
        <input
          aria-label={`${labelPrefix}寿元变化`}
          type="number"
          value={state.lifespan_delta}
          onChange={(event) =>
            update({ lifespan_delta: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}气血变化</span>
        <input
          aria-label={`${labelPrefix}气血变化`}
          type="number"
          value={state.hp_delta}
          onChange={(event) => update({ hp_delta: parseNumberInput(event.target.value, 0) })}
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}突破加成</span>
        <input
          aria-label={`${labelPrefix}突破加成`}
          type="number"
          value={state.breakthrough_bonus}
          onChange={(event) =>
            update({ breakthrough_bonus: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}功法经验</span>
        <input
          aria-label={`${labelPrefix}功法经验`}
          type="number"
          value={state.technique_exp}
          onChange={(event) =>
            update({ technique_exp: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}气运变化</span>
        <input
          aria-label={`${labelPrefix}气运变化`}
          type="number"
          value={state.luck_delta}
          onChange={(event) =>
            update({ luck_delta: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}因果变化</span>
        <input
          aria-label={`${labelPrefix}因果变化`}
          type="number"
          value={state.karma_delta}
          onChange={(event) =>
            update({ karma_delta: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}转生进度</span>
        <input
          aria-label={`${labelPrefix}转生进度`}
          type="number"
          value={state.rebirth_progress_delta}
          onChange={(event) =>
            update({ rebirth_progress_delta: parseNumberInput(event.target.value, 0) })
          }
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}增加状态</span>
        <textarea
          aria-label={`${labelPrefix}增加状态`}
          placeholder="每行一个状态"
          value={formatLineList(state.statuses_add)}
          onChange={(event) => update({ statuses_add: parseLineList(event.target.value) })}
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}移除状态</span>
        <textarea
          aria-label={`${labelPrefix}移除状态`}
          placeholder="每行一个状态"
          value={formatLineList(state.statuses_remove)}
          onChange={(event) => update({ statuses_remove: parseLineList(event.target.value) })}
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}获得功法</span>
        <textarea
          aria-label={`${labelPrefix}获得功法`}
          placeholder="每行一个功法"
          value={formatLineList(state.techniques_add)}
          onChange={(event) => update({ techniques_add: parseLineList(event.target.value) })}
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}获得装备标签</span>
        <textarea
          aria-label={`${labelPrefix}获得装备标签`}
          placeholder="每行一个装备标签"
          value={formatLineList(state.equipment_add)}
          onChange={(event) => update({ equipment_add: parseLineList(event.target.value) })}
        />
      </label>

      <label className="field">
        <span className="field__label">{labelPrefix}移除装备标签</span>
        <textarea
          aria-label={`${labelPrefix}移除装备标签`}
          placeholder="每行一个装备标签"
          value={formatLineList(state.equipment_remove)}
          onChange={(event) => update({ equipment_remove: parseLineList(event.target.value) })}
        />
      </label>

      <label className="switch-field field--full">
        <span>
          <strong>{labelPrefix}导致死亡</strong>
          <span className="field__hint">只在需要直接终结角色时开启。</span>
        </span>
        <input
          aria-label={`${labelPrefix}导致死亡`}
          checked={state.death}
          type="checkbox"
          onChange={(event) => update({ death: event.target.checked })}
        />
      </label>
    </div>
  );
}
