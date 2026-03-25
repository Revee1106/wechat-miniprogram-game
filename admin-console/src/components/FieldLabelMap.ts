export type OptionItem = {
  value: string;
  label: string;
};

export const eventTypeOptions: OptionItem[] = [
  { value: "cultivation", label: "修炼" },
  { value: "material", label: "采集" },
  { value: "technique", label: "功法" },
  { value: "equipment", label: "装备" },
  { value: "encounter", label: "奇遇" },
  { value: "survival", label: "生存" },
];

export const outcomeTypeOptions: OptionItem[] = [
  { value: "cultivation", label: "修炼收益" },
  { value: "material", label: "资源收益" },
  { value: "technique", label: "功法收益" },
  { value: "equipment", label: "装备收益" },
  { value: "lifespan", label: "寿元变动" },
  { value: "status", label: "状态变动" },
  { value: "breakthrough", label: "突破相关" },
  { value: "karma", label: "因果变动" },
  { value: "luck", label: "气运变动" },
  { value: "mixed", label: "混合结果" },
];

export const riskLevelOptions: OptionItem[] = [
  { value: "safe", label: "平稳" },
  { value: "normal", label: "寻常" },
  { value: "risky", label: "凶险" },
  { value: "fatal", label: "致命" },
];

export const triggerSourceOptions: OptionItem[] = [
  { value: "global", label: "全局触发" },
  { value: "realm_based", label: "境界触发" },
  { value: "region_based", label: "地域触发" },
  { value: "dwelling_based", label: "洞府触发" },
  { value: "technique_based", label: "功法触发" },
  { value: "equipment_based", label: "装备触发" },
  { value: "status_based", label: "状态触发" },
  { value: "karma_based", label: "因果触发" },
  { value: "luck_based", label: "气运触发" },
  { value: "rebirth_based", label: "转生触发" },
];

export const choicePatternOptions: OptionItem[] = [
  { value: "single_outcome", label: "单一结果" },
  { value: "binary_choice", label: "二择其一" },
  { value: "multi_choice", label: "多选分支" },
  { value: "resource_gated", label: "资源门槛" },
  { value: "stat_check", label: "属性判定" },
];

export function getOptionLabel(options: OptionItem[], value: string | null | undefined): string {
  if (!value) {
    return "未设定";
  }
  return options.find((item) => item.value === value)?.label ?? value;
}

export function formatRealmRange(
  realmMin: string | null | undefined,
  realmMax: string | null | undefined
): string {
  if (realmMin && realmMax) {
    return `${realmMin} 至 ${realmMax}`;
  }
  if (realmMin) {
    return `${realmMin} 及以上`;
  }
  if (realmMax) {
    return `${realmMax} 及以下`;
  }
  return "不限";
}

export function formatRepeatable(isRepeatable: boolean | undefined): string {
  return isRepeatable ? "可重复" : "唯一触发";
}

export function formatTriggerSources(triggerSources: string[] | undefined): string {
  if (!triggerSources || triggerSources.length === 0) {
    return "未设定";
  }
  return triggerSources.map((value) => getOptionLabel(triggerSourceOptions, value)).join(" / ");
}
