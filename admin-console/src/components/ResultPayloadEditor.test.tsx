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

  expect(screen.getByLabelText("成功变化项类型-1")).toHaveValue("resource:spirit_stone");
  expect(screen.getByLabelText("成功变化项类型-2")).toHaveValue("resource:herb");
  expect(screen.getByLabelText("成功变化项类型-3")).toHaveValue("resource:ore");
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

  fireEvent.change(screen.getByLabelText("结果新增变化项"), {
    target: { value: "resource:herb" },
  });
  fireEvent.change(screen.getByLabelText("结果变化数值-2"), {
    target: { value: "5" },
  });

  expect(screen.getByTestId("payload").textContent).toContain("\"spirit_stone\":2");
  expect(screen.getByTestId("payload").textContent).toContain("\"herb\":5");
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

  fireEvent.change(screen.getByLabelText("结果新增变化项"), {
    target: { value: "resource:spirit_stone" },
  });

  const amountInput = screen.getByLabelText("结果变化数值-1");
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
  expect(screen.getByLabelText("结果变化项类型-1")).toHaveValue("stat:cultivation_exp");
  expect(screen.getByLabelText("结果变化数值-1")).toHaveValue("20");
  expect(screen.queryByLabelText("结果修为变化")).toBeNull();
});
