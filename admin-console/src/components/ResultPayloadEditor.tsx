import {
  buildPayloadFromEditorState,
  formatKeyValueMap,
  formatLineList,
  parseKeyValueMap,
  parseLineList,
  parseNumberInput,
  parsePayloadEditorState,
  type PayloadEditorState,
} from "../utils/eventFormCodec";

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

  function update(partial: Partial<PayloadEditorState>) {
    onChange(
      buildPayloadFromEditorState({
        ...state,
        ...partial,
      })
    );
  }

  return (
    <div className="field-grid">
      <label className="field field--full">
        <span className="field__label">{labelPrefix}资源变化</span>
        <textarea
          aria-label={`${labelPrefix}资源变化`}
          placeholder="每行一个，格式为 名称:数量"
          value={formatKeyValueMap(state.resources)}
          onChange={(event) => update({ resources: parseKeyValueMap(event.target.value) })}
        />
      </label>

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
