import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { expect, test } from "vitest";

import { ResultPayloadEditor } from "./ResultPayloadEditor";

test("renders canonical resource rows from legacy resource keys", () => {
  render(
    <ResultPayloadEditor
      labelPrefix="成功"
      payload={{
        resources: {
          spirit_stone: 2,
          herbs: 3,
          iron_essence: 4,
        },
      }}
      onChange={() => {}}
    />
  );

  expect(screen.getByLabelText("成功资源类型-1")).toHaveValue("spirit_stone");
  expect(screen.getByLabelText("成功资源类型-2")).toHaveValue("herb");
  expect(screen.getByLabelText("成功资源类型-3")).toHaveValue("ore");
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
          payload={payload}
          onChange={setPayload}
        />
        <pre data-testid="payload">{JSON.stringify(payload)}</pre>
      </>
    );
  }

  render(<Harness />);

  fireEvent.click(screen.getByRole("button", { name: "新增资源变化" }));
  fireEvent.change(screen.getByLabelText("结果资源类型-2"), {
    target: { value: "herb" },
  });
  fireEvent.change(screen.getByLabelText("结果资源数值-2"), {
    target: { value: "5" },
  });

  expect(screen.getByTestId("payload").textContent).toContain("\"spirit_stone\":2");
  expect(screen.getByTestId("payload").textContent).toContain("\"herb\":5");
});
