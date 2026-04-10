const ERROR_CODE_MESSAGES: Record<string, string> = {
  "core.time.not_enough_spirit_stones": "灵石不足，无法推进时间。",
  "core.run.not_found": "当前没有进行中的修仙历程，请先启程。",
  "core.breakthrough.not_enough_cultivation_exp": "修为不足，尚不能突破。",
  "core.breakthrough.not_enough_spirit_stones": "灵石不足，尚不能突破。",
  "core.dwelling.facility_already_at_max_level": "该设施已达当前最高等级。",
  "core.dwelling.not_enough_resources": "资源不足，无法执行洞府操作。",
  "core.resource_sale.not_enough_resources": "资源不足，无法出售。",
  "core.resource_conversion.not_enough_spirit_stone": "灵石不足，无法转化。",
};

const LEGACY_ERROR_PATTERNS: Array<[RegExp, string]> = [
  [/Failed to load events/i, "加载事件列表失败"],
  [/Failed to load event detail/i, "加载事件详情失败"],
  [/Failed to load realms/i, "加载境界列表失败"],
  [/Failed to load realm detail/i, "加载境界详情失败"],
  [/Failed to load dwelling facilities/i, "加载洞府设施列表失败"],
  [/Failed to load dwelling facility detail/i, "加载洞府设施详情失败"],
  [/Failed to load admin session/i, "加载管理会话失败"],
  [/not enough spirit stones to advance time/i, "灵石不足，无法推进时间。"],
  [/run .* not found/i, "当前没有进行中的修仙历程，请先启程。"],
];

const REALM_LABELS: Record<string, string> = {
  qi_refining_early: "炼气初期",
  qi_refining_mid: "炼气中期",
  qi_refining_late: "炼气后期",
  qi_refining_peak: "炼气大圆满",
  foundation_early: "筑基初期",
  foundation_mid: "筑基中期",
  foundation_late: "筑基后期",
  foundation_peak: "筑基大圆满",
};

type ValidationPattern = {
  pattern: RegExp;
  format: (...groups: string[]) => string;
};

const VALIDATION_FIELD_LABELS: Record<string, string> = {
  display_name: "展示名称",
  major_realm: "所属大境界",
  stage_index: "阶段序号",
  base_success_rate: "基础成功率",
  required_cultivation_exp: "突破所需修为",
  required_spirit_stone: "突破所需灵石",
  base_cultivation_gain_per_advance: "每次推进基础修为",
  base_spirit_stone_cost_per_advance: "每次推进基础灵石消耗",
  lifespan_bonus: "寿元加成",
  failure_penalty: "失败惩罚",
  facility_type: "设施类型",
  summary: "设施说明",
  entry_cost: "建造消耗",
  maintenance_cost: "维护消耗",
  resource_yields: "资源产出",
  cultivation_exp_gain: "修为产出",
  special_effects: "特殊效果",
  event_type: "事件类型",
  outcome_type: "结果类型",
  risk_level: "风险等级",
  choice_pattern: "选项模式",
  trigger_sources: "触发来源",
  resolution_mode: "结算模式",
  sort_order: "排序",
  time_cost_months: "事件耗时（月）",
};

const VALIDATION_SCOPE_LABELS: Record<string, string> = {
  realm: "境界",
  facility: "设施",
  template: "事件模板",
  option: "事件选项",
};

const VALIDATION_MESSAGE_PATTERNS: ValidationPattern[] = [
  {
    pattern: /^duplicate (realm key|order_index|facility_id|event_id|option_id): (.+)$/i,
    format: (field, value) => `${formatDuplicateFieldLabel(field)}重复：${value}`,
  },
  {
    pattern: /^(realm|facility|template|option) missing ([a-z_]+)$/i,
    format: (scope, field) => `${VALIDATION_SCOPE_LABELS[scope] ?? scope}缺少${formatValidationFieldLabel(field)}`,
  },
  {
    pattern: /^(realm|facility|template|option) '(.+)' has empty ([a-z_]+)$/i,
    format: (scope, key, field) =>
      `${VALIDATION_SCOPE_LABELS[scope] ?? scope}“${key}”缺少${formatValidationFieldLabel(field)}`,
  },
  {
    pattern: /^realm '(.+)' has invalid ([a-z_]+)$/i,
    format: (key, field) => `境界“${key}”的${formatValidationFieldLabel(field)}填写无效`,
  },
  {
    pattern: /^facility '(.+)' must define at least one level$/i,
    format: (facilityId) => `设施“${facilityId}”至少需要配置一个等级`,
  },
  {
    pattern: /^facility '(.+)' levels must start at 1 and be contiguous$/i,
    format: (facilityId) => `设施“${facilityId}”的等级必须从 1 开始连续配置`,
  },
  {
    pattern: /^facility '(.+)' has invalid level payload$/i,
    format: (facilityId) => `设施“${facilityId}”存在无效的等级配置`,
  },
  {
    pattern: /^facility '(.+)' has invalid level$/i,
    format: (facilityId) => `设施“${facilityId}”存在无效的等级值`,
  },
  {
    pattern: /^facility '(.+)' level (\d+) has invalid ([a-z_]+)$/i,
    format: (facilityId, level, field) =>
      `设施“${facilityId}”的 Lv.${level} ${formatValidationFieldLabel(field)}填写无效`,
  },
  {
    pattern: /^facility '(.+)' level (\d+) has empty ([a-z_]+) key$/i,
    format: (facilityId, level, field) =>
      `设施“${facilityId}”的 Lv.${level} ${formatValidationFieldLabel(field)}存在空白资源键`,
  },
  {
    pattern: /^facility '(.+)' level (\d+) has invalid ([a-z_]+) value for '(.+)'$/i,
    format: (facilityId, level, field, resourceKey) =>
      `设施“${facilityId}”的 Lv.${level} ${formatValidationFieldLabel(field)}里，资源“${resourceKey}”的数值无效`,
  },
  {
    pattern: /^facility '(.+)' level (\d+) has unknown special effect '(.+)'$/i,
    format: (facilityId, level, effectKey) =>
      `设施“${facilityId}”的 Lv.${level} 存在未识别的特殊效果“${effectKey}”`,
  },
  {
    pattern: /^facility '(.+)' level (\d+) has invalid special effect '(.+)'$/i,
    format: (facilityId, level, effectKey) =>
      `设施“${facilityId}”的 Lv.${level} 特殊效果“${effectKey}”数值无效`,
  },
  {
    pattern: /^template '(.+)' has invalid ([a-z_]+)$/i,
    format: (eventId, field) => `事件模板“${eventId}”的${formatValidationFieldLabel(field)}填写无效`,
  },
  {
    pattern: /^template '(.+)' must have positive weight$/i,
    format: (eventId) => `事件模板“${eventId}”的权重必须大于 0`,
  },
  {
    pattern: /^template '(.+)' must include option_ids$/i,
    format: (eventId) => `事件模板“${eventId}”至少需要关联一个选项`,
  },
  {
    pattern: /^template '(.+)' references missing option_id '(.+)'$/i,
    format: (eventId, optionId) => `事件模板“${eventId}”引用了不存在的选项“${optionId}”`,
  },
  {
    pattern: /^option '(.+)' references missing event_id '(.+)'$/i,
    format: (optionId, eventId) => `事件选项“${optionId}”引用了不存在的事件“${eventId}”`,
  },
  {
    pattern: /^option '(.+)' must have sort_order >= 1$/i,
    format: (optionId) => `事件选项“${optionId}”的排序必须大于等于 1`,
  },
  {
    pattern: /^option '(.+)' must have time_cost_months >= 0$/i,
    format: (optionId) => `事件选项“${optionId}”的事件耗时（月）不能小于 0`,
  },
  {
    pattern: /^option '(.+)' has invalid ([a-z_]+)$/i,
    format: (optionId, field) => `事件选项“${optionId}”的${formatValidationFieldLabel(field)}填写无效`,
  },
  {
    pattern: /^option '(.+)' references missing next_event_id '(.+)'$/i,
    format: (optionId, eventId) => `事件选项“${optionId}”引用了不存在的后续事件“${eventId}”`,
  },
  {
    pattern: /^option '(.+)' has conflicting equipment mutations in ([a-z_]+)$/i,
    format: (optionId, payloadName) =>
      `事件选项“${optionId}”在${formatPayloadLabel(payloadName)}里同时添加并移除了同一装备`,
  },
];

export function formatRealmDisplayName(displayName: string | null | undefined, key: string): string {
  const normalized = String(displayName ?? "").trim();
  if (normalized) {
    return normalized;
  }
  return REALM_LABELS[key] ?? key;
}

export function localizeAdminErrorMessage(
  message: string,
  code?: string | null,
  params?: Record<string, unknown>
): string {
  if (code && ERROR_CODE_MESSAGES[code]) {
    return ERROR_CODE_MESSAGES[code];
  }

  const rawMessage = String(message || "").trim();
  const validationMessage = localizeValidationMessage(rawMessage);
  if (validationMessage) {
    return validationMessage;
  }

  for (const [pattern, localizedMessage] of LEGACY_ERROR_PATTERNS) {
    if (pattern.test(rawMessage)) {
      return localizedMessage;
    }
  }

  if (params?.realm && typeof params.realm === "string" && REALM_LABELS[params.realm]) {
    return rawMessage.replace(params.realm, REALM_LABELS[params.realm]);
  }

  return rawMessage || "请求失败";
}

export function localizeValidationResponse<T extends { errors: string[]; warnings: string[] }>(
  validation: T
): T {
  return {
    ...validation,
    errors: validation.errors.map((message) => localizeAdminErrorMessage(message)),
    warnings: validation.warnings.map((message) => localizeAdminErrorMessage(message)),
  };
}

export function buildAdminErrorMessage(
  payload: unknown,
  fallbackMessage: string
): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (detail && typeof detail === "object" && !Array.isArray(detail)) {
      const errorDetail = detail as {
        code?: string;
        message?: string;
        params?: Record<string, unknown>;
      };
      return localizeAdminErrorMessage(
        String(errorDetail.message || fallbackMessage),
        errorDetail.code,
        errorDetail.params
      );
    }
    if (typeof detail === "string" && detail) {
      return localizeAdminErrorMessage(detail);
    }
  }

  return localizeAdminErrorMessage(fallbackMessage);
}

function localizeValidationMessage(message: string): string | null {
  for (const { pattern, format } of VALIDATION_MESSAGE_PATTERNS) {
    const matched = message.match(pattern);
    if (matched) {
      return format(...matched.slice(1));
    }
  }
  return null;
}

function formatValidationFieldLabel(field: string): string {
  return VALIDATION_FIELD_LABELS[field] ?? field;
}

function formatDuplicateFieldLabel(field: string): string {
  if (field === "realm key") {
    return "境界内部标识";
  }
  return formatValidationFieldLabel(field);
}

function formatPayloadLabel(payloadName: string): string {
  if (payloadName === "result_on_success") {
    return "成功结果";
  }
  if (payloadName === "result_on_failure") {
    return "失败结果";
  }
  return payloadName;
}
