import type { EventOptionInput } from "../api/client";
import { ResultPayloadEditor } from "./ResultPayloadEditor";
import { SectionCard } from "./SectionCard";

type SingleOutcomeEditorProps = {
  option: EventOptionInput;
  onChange: <K extends keyof EventOptionInput>(
    field: K,
    value: EventOptionInput[K]
  ) => void;
};

export function SingleOutcomeEditor({
  option,
  onChange,
}: SingleOutcomeEditorProps) {
  return (
    <SectionCard
      title="单一结果"
      description="单一结果模式下，不再编排选项，只维护一条默认结算。"
    >
      <div className="field-grid">
        <label className="field">
          <span className="field__label">后续事件</span>
          <input
            aria-label="后续事件"
            placeholder="填写事件编号，留空表示结束"
            value={option.next_event_id ?? ""}
            onChange={(event) => onChange("next_event_id", event.target.value || null)}
          />
        </label>

        <label className="field">
          <span className="field__label">结果日志</span>
          <input
            aria-label="结果日志"
            placeholder="默认结果的结算文案"
            value={option.log_text_success ?? ""}
            onChange={(event) => onChange("log_text_success", event.target.value)}
          />
        </label>
      </div>

      <ResultPayloadEditor
        labelPrefix="结果"
        payload={option.result_on_success}
        onChange={(value) => onChange("result_on_success", value)}
      />
    </SectionCard>
  );
}
