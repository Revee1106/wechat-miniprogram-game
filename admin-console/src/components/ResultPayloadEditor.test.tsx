import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { expect, test } from "vitest";

import { ResultPayloadEditor } from "./ResultPayloadEditor";

test("renders canonical resource rows from legacy resource keys", () => {
  render(
    <ResultPayloadEditor
      labelPrefix="成功"
      onChange={() => {}}
      payload={{
        resources: {
          spirit_stone: 2,
          herbs: 3,
          iron_essence: 4,
        },
      }}
    />
  );

  expect(screen.getByLabelText("成功物品变化类型-1")).toHaveValue("resource:spirit_stone");
  expect(screen.getByLabelText("成功物品变化类型-2")).toHaveValue("resource:herb");
  expect(screen.getByLabelText("成功物品变化类型-3")).toHaveValue("resource:ore");
});

test("edits resource deltas through predefined selector rows", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({
      resources: { spirit_stone: 2 },
    });

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="结果"
          onChange={setPayload}
          payload={payload}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("结果新增物品变化"), {
    target: { value: "resource:herb" },
  });
  fireEvent.change(screen.getByLabelText("结果物品变化数值-2"), {
    target: { value: "5" },
  });

  expect(screen.getByTestId("payload").textContent).toContain("\"spirit_stone\":2");
  expect(screen.getByTestId("payload").textContent).toContain("\"herb\":5");
});

test("uses configured material options instead of unconfigured legacy materials", () => {
  render(
    <ResultPayloadEditor
      labelPrefix="结果"
      onChange={() => {}}
      payload={{}}
      resourceOptions={[
        { value: "basic_herb", label: "基础灵草" },
        { value: "herb_ninglucao", label: "凝露草" },
      ]}
    />
  );

  const options = screen
    .getByLabelText("结果新增物品变化")
    .querySelectorAll("option");
  const labels = Array.from(options).map((option) => option.textContent);

  expect(labels).toContain("基础灵草");
  expect(labels).toContain("凝露草");
  expect(labels).not.toContain("灵石");
  expect(labels).not.toContain("药草");
  expect(labels).not.toContain("玄铁精华");
});

test("allows typing a negative resource delta without resetting the input mid-edit", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({});

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="结果"
          onChange={setPayload}
          payload={payload}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("结果新增物品变化"), {
    target: { value: "resource:spirit_stone" },
  });

  const amountInput = screen.getByLabelText("结果物品变化数值-1");
  fireEvent.change(amountInput, { target: { value: "-" } });
  expect(amountInput).toHaveValue("-");

  fireEvent.change(amountInput, { target: { value: "-3" } });
  expect(screen.getByTestId("payload").textContent).toContain("\"spirit_stone\":-3");
});

test("uses dedicated compact layout shells for narrow drawer panels", () => {
  const { container } = render(
    <ResultPayloadEditor
      labelPrefix="成功"
      onChange={() => {}}
      payload={{ resources: { spirit_stone: 2 } }}
    />
  );

  expect(container.querySelector(".result-payload-editor")).not.toBeNull();
  expect(container.querySelector(".result-payload-editor__resource-panel")).not.toBeNull();
  expect(container.querySelector(".result-payload-editor__extras")).toBeNull();
});

test("merges scalar deltas into the unified change list and hides the empty stats grid", () => {
  render(
    <ResultPayloadEditor
      labelPrefix="结果"
      onChange={() => {}}
      payload={{
        character: {
          cultivation_exp: 20,
        },
      }}
    />
  );

  expect(screen.getByText("结果变化")).toBeInTheDocument();
  expect(screen.getByLabelText("结果数值变化类型-1")).toHaveValue("stat:cultivation_exp");
  expect(screen.getByLabelText("结果数值变化数值-1")).toHaveValue("20");
  expect(screen.queryByLabelText("结果修为变化")).toBeNull();
});

test("edits alchemy mastery exp through the change list", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({});

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="结果"
          onChange={setPayload}
          payload={payload}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("结果新增数值变化"), {
    target: { value: "stat:alchemy_mastery_exp_delta" },
  });
  fireEvent.change(screen.getByLabelText("结果数值变化数值-1"), {
    target: { value: "12" },
  });

  expect(screen.getByTestId("payload").textContent).toContain(
    "\"alchemy_mastery_exp_delta\":12"
  );
});

test("keeps selected scalar options visible as disabled entries", () => {
  render(
    <ResultPayloadEditor
      labelPrefix="结果"
      onChange={() => {}}
      payload={{ alchemy_mastery_exp_delta: 10 }}
    />
  );

  const selectedOption = screen.getByRole("option", {
    name: "炼丹熟练度（已添加）",
  });
  expect(selectedOption).toBeDisabled();
});

test("edits learned alchemy recipe ids as an extra payload field", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({});

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="成功"
          onChange={setPayload}
          alchemyRecipeOptions={[
            { value: "ning_qi_dan", label: "凝气丹" },
            { value: "huo_mai_dan", label: "火脉丹" },
          ]}
          payload={payload}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("成功新增附加变化"), {
    target: { value: "learned_alchemy_recipe_ids" },
  });
  fireEvent.click(screen.getByRole("button", { name: "新增丹方" }));
  fireEvent.click(screen.getByRole("button", { name: "新增丹方" }));

  expect(screen.getByTestId("payload").textContent).toContain(
    "\"learned_alchemy_recipe_ids\":[\"ning_qi_dan\",\"huo_mai_dan\"]"
  );
});

test("edits unlocked material ids as an extra payload field", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({});

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="成功"
          onChange={setPayload}
          payload={payload}
          resourceOptions={[
            { value: "basic_herb", label: "基础灵草" },
            { value: "herb_julingzhi", label: "聚灵芝" },
          ]}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("成功新增附加变化"), {
    target: { value: "unlocked_material_ids" },
  });
  fireEvent.click(screen.getByRole("button", { name: "新增材料" }));
  fireEvent.change(screen.getByLabelText("成功解锁材料-1"), {
    target: { value: "herb_julingzhi" },
  });

  expect(screen.getByTestId("payload").textContent).toContain(
    "\"unlocked_material_ids\":[\"herb_julingzhi\"]"
  );
});

test("edits progress counter deltas as an extra payload field", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({});

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="成功"
          onChange={setPayload}
          payload={payload}
          progressCounterOptions={[
            { value: "alchemy.ning_qi_dan_clue", label: "alchemy.ning_qi_dan_clue" },
            { value: "alchemy.npc_lingyao_approval", label: "alchemy.npc_lingyao_approval" },
          ]}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("成功新增附加变化"), {
    target: { value: "progress_counter_deltas" },
  });
  fireEvent.click(screen.getByRole("button", { name: "新增进度" }));
  expect(screen.getByLabelText("成功进度变化进度项-1")).toHaveValue(
    "alchemy.ning_qi_dan_clue"
  );
  fireEvent.change(screen.getByLabelText("成功进度变化数值-1"), {
    target: { value: "3" },
  });

  expect(screen.getByTestId("payload").textContent).toContain(
    "\"progress_counter_deltas\":{\"alchemy.ning_qi_dan_clue\":3}"
  );
});

test("edits per-change chance for numeric and item deltas", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({
      resources: { spirit_stone: 2 },
    });

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="结果"
          onChange={setPayload}
          payload={payload}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("结果物品变化概率-1"), {
    target: { value: "0.25" },
  });

  expect(screen.getByTestId("payload").textContent).toContain(
    "\"change_chances\":{\"resources.spirit_stone\":0.25}"
  );
});

test("allows adding a new progress counter key when it is not in suggestions", () => {
  function Harness() {
    const [payload, setPayload] = useState<Record<string, unknown>>({});

    return (
      <>
        <ResultPayloadEditor
          labelPrefix="成功"
          onChange={setPayload}
          payload={payload}
          progressCounterOptions={[]}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.change(screen.getByLabelText("成功新增附加变化"), {
    target: { value: "progress_counter_deltas" },
  });
  fireEvent.click(screen.getByRole("button", { name: "新增进度" }));
  const progressKeyInput = screen.getByLabelText("成功进度变化进度项-1");
  fireEvent.change(progressKeyInput, {
    target: { value: "a" },
  });
  expect(progressKeyInput).toHaveValue("a");
  fireEvent.change(progressKeyInput, {
    target: { value: "alchemy.custom_progress" },
  });
  fireEvent.change(screen.getByLabelText("成功进度变化数值-1"), {
    target: { value: "2" },
  });

  expect(screen.getByTestId("payload").textContent).toContain(
    "\"progress_counter_deltas\":{\"alchemy.custom_progress\":2}"
  );
});

test("shows all configured progress counters in the row dropdown", () => {
  render(
    <ResultPayloadEditor
      labelPrefix="成功"
      onChange={() => {}}
      payload={{ progress_counter_deltas: { zhu_ji_dan_xiansuo: 1 } }}
      progressCounterOptions={[
        { value: "zhu_ji_dan_xiansuo", label: "zhu_ji_dan_xiansuo" },
        { value: "zhu_ji_dan_npc", label: "zhu_ji_dan_npc" },
      ]}
    />
  );

  const progressSelect = screen.getByLabelText("成功进度变化进度项-1");

  expect(progressSelect).toHaveValue("zhu_ji_dan_xiansuo");
  expect(screen.getByRole("option", { name: "zhu_ji_dan_xiansuo" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "zhu_ji_dan_npc" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "新增自定义进度项..." })).toBeInTheDocument();
});
