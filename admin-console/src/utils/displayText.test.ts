import { describe, expect, it } from "vitest";
import {
  buildAdminErrorMessage,
  formatRealmDisplayName,
  localizeValidationResponse,
} from "./displayText";

describe("displayText", () => {
  it("formats structured core-loop errors as Chinese text", () => {
    expect(
      buildAdminErrorMessage(
        {
          detail: {
            code: "core.time.not_enough_spirit_stones",
            message: "not enough spirit stones to advance time",
            params: {},
          },
        },
        "加载失败"
      )
    ).toBe("灵石不足，无法推进时间。");
  });

  it("formats fallback realm names in Chinese", () => {
    expect(formatRealmDisplayName("", "foundation_early")).toBe("筑基初期");
  });

  it("localizes validation issues into Chinese", () => {
    expect(
      localizeValidationResponse({
        is_valid: false,
        errors: [
          "realm 'qi_refining_early' has invalid required_spirit_stone",
          "facility 'spirit_field' level 2 has invalid resource_yields value for 'basic_herb'",
          "option 'choice_1' must have time_cost_months >= 0",
        ],
        warnings: ["duplicate realm key: qi_refining_early"],
      })
    ).toEqual({
      is_valid: false,
      errors: [
        "境界“qi_refining_early”的突破所需灵石填写无效",
        "设施“spirit_field”的 Lv.2 资源产出里，资源“basic_herb”的数值无效",
        "事件选项“choice_1”的事件耗时（月）不能小于 0",
      ],
      warnings: ["境界内部标识重复：qi_refining_early"],
    });
  });
});
