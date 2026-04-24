import { buildAdminErrorMessage, localizeValidationResponse } from "../utils/displayText";

export type EventListItem = {
  event_id: string;
  event_name: string;
  event_type: string;
  outcome_type?: string;
  risk_level: string;
  weight?: number;
  trigger_sources?: string[];
  region?: string;
  realm_min?: string | null;
  realm_max?: string | null;
  option_ids?: string[];
  is_repeatable?: boolean;
};

type EventListResponse = {
  items: EventListItem[];
};

export type EventTemplateInput = {
  event_id: string;
  event_name: string;
  event_type: string;
  outcome_type: string;
  risk_level: string;
  trigger_sources: string[];
  choice_pattern: string;
  title_text: string;
  body_text: string;
  realm_min?: string | null;
  realm_max?: string | null;
  region?: string;
  weight: number;
  is_repeatable: boolean;
  cooldown_rounds?: number;
  max_trigger_per_run?: number;
  required_statuses?: string[];
  excluded_statuses?: string[];
  required_techniques?: string[];
  required_equipment_tags?: string[];
  required_resources?: Record<string, number>;
  required_rebirth_count?: number;
  required_karma_min?: number | null;
  required_luck_min?: number;
  flags?: string[];
  option_ids: string[];
};

export type EventOptionInput = {
  option_id: string;
  event_id?: string;
  option_text: string;
  sort_order: number;
  is_default: boolean;
  time_cost_months?: number;
  resolution_mode?: string;
  enemy_template_id?: string | null;
  requires_resources?: Record<string, number>;
  requires_statuses?: string[];
  requires_techniques?: string[];
  requires_equipment_tags?: string[];
  success_rate_formula?: string;
  result_on_success?: Record<string, unknown> | string;
  result_on_failure?: Record<string, unknown> | string;
  next_event_id?: string | null;
  log_text_success?: string;
  log_text_failure?: string;
};

export type BattleConfigInput = {
  enemy_name: string;
  enemy_realm_label: string;
  enemy_hp: number;
  enemy_attack: number;
  enemy_defense: number;
  enemy_speed: number;
  allow_flee: boolean;
  flee_base_rate: number;
  pill_heal_amount: number;
  victory_log?: string;
  defeat_log?: string;
  flee_success_log?: string;
  flee_failure_log?: string;
};

export type EnemyTemplateInput = {
  enemy_id: string;
  enemy_name: string;
  enemy_realm_label: string;
  enemy_hp: number;
  enemy_attack: number;
  enemy_defense: number;
  enemy_speed: number;
  allow_flee: boolean;
  rewards: Record<string, unknown>;
};

export type EnemyTemplateListResponse = {
  items: EnemyTemplateInput[];
};

export type EnemyReloadResponse = {
  reloaded: boolean;
  enemy_count: number;
};

export type EventDetailResponse = {
  template: EventTemplateInput;
  options: EventOptionInput[];
};

export type ValidationResponse = {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
};

export type AdminSession = {
  authenticated: boolean;
  username: string;
};

export type RealmConfig = {
  key: string;
  display_name: string;
  major_realm: string;
  stage_index: number;
  order_index: number;
  base_cultivation_gain_per_advance: number;
  base_spirit_stone_cost_per_advance: number;
  base_success_rate: number;
  required_cultivation_exp: number;
  required_spirit_stone: number;
  lifespan_bonus: number;
  failure_penalty?: RealmFailurePenalty;
  is_enabled: boolean;
};

export type RealmInput = RealmConfig;

export type RealmFailurePenalty = {
  character?: {
    cultivation_exp?: number;
  };
};

export type RealmListResponse = {
  items: RealmConfig[];
};

export type RealmDetailResponse = RealmConfig;

export type RealmReloadResponse = {
  reloaded: boolean;
  realm_count: number;
};

export type RealmReorderResponse = {
  items: RealmConfig[];
};

export type DwellingLevelInput = {
  level: number;
  entry_cost: Record<string, number>;
  maintenance_cost: Record<string, number>;
  resource_yields: Record<string, number>;
  cultivation_exp_gain: number;
  special_effects: Record<string, number>;
};

export type DwellingFacilityInput = {
  facility_id: string;
  display_name: string;
  facility_type: string;
  summary: string;
  function_unlock_text: string;
  levels: DwellingLevelInput[];
};

export type DwellingFacilityListItem = {
  facility_id: string;
  display_name: string;
  facility_type: string;
  summary: string;
  max_level: number;
  level_count: number;
};

export type DwellingFacilityListResponse = {
  items: DwellingFacilityListItem[];
};

export type DwellingReloadResponse = {
  reloaded: boolean;
  facility_count: number;
};

export type AlchemyLevelInput = {
  level: number;
  display_name: string;
  required_mastery_exp: number;
};

export type AlchemyRecipeInput = {
  recipe_id: string;
  display_name: string;
  category: string;
  description: string;
  required_alchemy_level: number;
  duration_months: number;
  base_success_rate: number;
  ingredients: Record<string, number>;
  effect_type: string;
  effect_value: number;
  effect_summary: string;
  is_base_recipe: boolean;
};

export type AlchemyLevelListResponse = {
  items: AlchemyLevelInput[];
};

export type AlchemyRecipeListResponse = {
  items: AlchemyRecipeInput[];
};

export type AlchemyReloadResponse = {
  reloaded: boolean;
  level_count: number;
  recipe_count: number;
};

export async function fetchEvents(filters?: {
  eventType?: string;
  riskLevel?: string;
  keyword?: string;
}): Promise<EventListResponse> {
  const params = new URLSearchParams();
  if (filters?.eventType) {
    params.set("event_type", filters.eventType);
  }
  if (filters?.riskLevel) {
    params.set("risk_level", filters.riskLevel);
  }
  if (filters?.keyword) {
    params.set("keyword", filters.keyword);
  }

  const query = params.toString();
  const response = await fetch(`/admin/api/events${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载事件列表失败"));
  }
  return response.json();
}

export async function fetchEventDetail(eventId: string): Promise<EventDetailResponse> {
  const response = await fetch(`/admin/api/events/${eventId}`);
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载事件详情失败"));
  }
  return response.json();
}

export async function fetchRealms(): Promise<RealmListResponse> {
  const response = await fetch("/admin/api/realms");
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载境界列表失败"));
  }
  return response.json();
}

export async function fetchRealmDetail(realmKey: string): Promise<RealmDetailResponse> {
  const response = await fetch(`/admin/api/realms/${realmKey}`);
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载境界详情失败"));
  }
  return response.json();
}

export async function fetchDwellingFacilities(): Promise<DwellingFacilityListResponse> {
  const response = await fetch("/admin/api/dwelling/facilities");
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载洞府设施列表失败"));
  }
  return response.json();
}

export async function fetchDwellingFacilityDetail(
  facilityId: string
): Promise<DwellingFacilityInput> {
  const response = await fetch(`/admin/api/dwelling/facilities/${facilityId}`);
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载洞府设施详情失败"));
  }
  return response.json();
}

export async function fetchBattleEnemies(): Promise<EnemyTemplateListResponse> {
  const response = await fetch("/admin/api/battle/enemies");
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载敌人模板列表失败"));
  }
  return response.json();
}

export async function fetchBattleEnemyDetail(enemyId: string): Promise<EnemyTemplateInput> {
  const response = await fetch(`/admin/api/battle/enemies/${enemyId}`);
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载敌人模板详情失败"));
  }
  return response.json();
}

export async function fetchAlchemyLevels(): Promise<AlchemyLevelListResponse> {
  const response = await fetch("/admin/api/alchemy/levels");
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载丹道等级失败"));
  }
  return response.json();
}

export async function updateAlchemyLevels(
  levels: AlchemyLevelInput[]
): Promise<AlchemyLevelListResponse> {
  return sendJson("/admin/api/alchemy/levels", {
    method: "PUT",
    body: JSON.stringify({ items: levels }),
  });
}

export async function fetchAlchemyRecipes(): Promise<AlchemyRecipeListResponse> {
  const response = await fetch("/admin/api/alchemy/recipes");
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载丹方列表失败"));
  }
  return response.json();
}

export async function fetchAlchemyRecipeDetail(
  recipeId: string
): Promise<AlchemyRecipeInput> {
  const response = await fetch(`/admin/api/alchemy/recipes/${recipeId}`);
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载丹方详情失败"));
  }
  return response.json();
}

export async function createEvent(payload: EventTemplateInput): Promise<EventTemplateInput> {
  return sendJson("/admin/api/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteEvent(eventId: string): Promise<void> {
  await sendJson(`/admin/api/events/${eventId}`, {
    method: "DELETE",
  });
}

export async function createRealm(payload: RealmInput): Promise<RealmDetailResponse> {
  return sendJson("/admin/api/realms", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateRealm(
  realmKey: string,
  payload: RealmInput
): Promise<RealmDetailResponse> {
  return sendJson(`/admin/api/realms/${realmKey}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteRealm(realmKey: string): Promise<void> {
  await sendJson(`/admin/api/realms/${realmKey}`, {
    method: "DELETE",
  });
}

export async function updateDwellingFacility(
  facilityId: string,
  payload: DwellingFacilityInput
): Promise<DwellingFacilityInput> {
  return sendJson(`/admin/api/dwelling/facilities/${facilityId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function createBattleEnemy(
  payload: EnemyTemplateInput
): Promise<EnemyTemplateInput> {
  return sendJson("/admin/api/battle/enemies", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateBattleEnemy(
  enemyId: string,
  payload: EnemyTemplateInput
): Promise<EnemyTemplateInput> {
  return sendJson(`/admin/api/battle/enemies/${enemyId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteBattleEnemy(enemyId: string): Promise<void> {
  await sendJson(`/admin/api/battle/enemies/${enemyId}`, {
    method: "DELETE",
  });
}

export async function createAlchemyRecipe(
  payload: AlchemyRecipeInput
): Promise<AlchemyRecipeInput> {
  return sendJson("/admin/api/alchemy/recipes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAlchemyRecipe(
  recipeId: string,
  payload: AlchemyRecipeInput
): Promise<AlchemyRecipeInput> {
  return sendJson(`/admin/api/alchemy/recipes/${recipeId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteAlchemyRecipe(recipeId: string): Promise<void> {
  await sendJson(`/admin/api/alchemy/recipes/${recipeId}`, {
    method: "DELETE",
  });
}

export async function updateEvent(
  eventId: string,
  payload: EventTemplateInput
): Promise<EventTemplateInput> {
  return sendJson(`/admin/api/events/${eventId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function createOption(
  eventId: string,
  payload: EventOptionInput
): Promise<EventOptionInput> {
  return sendJson(`/admin/api/events/${eventId}/options`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateOption(
  optionId: string,
  payload: EventOptionInput
): Promise<EventOptionInput> {
  return sendJson(`/admin/api/options/${optionId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteOption(optionId: string): Promise<void> {
  await sendJson(`/admin/api/options/${optionId}`, {
    method: "DELETE",
  });
}

export async function validateEvents(): Promise<ValidationResponse> {
  const response = await sendJson<ValidationResponse>("/admin/api/events/validate", {
    method: "POST",
  });
  return localizeValidationResponse(response);
}

export async function validateRealms(): Promise<ValidationResponse> {
  const response = await sendJson<ValidationResponse>("/admin/api/realms/validate", {
    method: "POST",
  });
  return localizeValidationResponse(response);
}

export async function validateDwelling(): Promise<ValidationResponse> {
  const response = await sendJson<ValidationResponse>("/admin/api/dwelling/validate", {
    method: "POST",
  });
  return localizeValidationResponse(response);
}

export async function validateBattleEnemies(): Promise<ValidationResponse> {
  const response = await sendJson<ValidationResponse>("/admin/api/battle/validate", {
    method: "POST",
  });
  return localizeValidationResponse(response);
}

export async function validateAlchemy(): Promise<ValidationResponse> {
  const response = await sendJson<ValidationResponse>("/admin/api/alchemy/validate", {
    method: "POST",
  });
  return localizeValidationResponse(response);
}

export async function reloadEvents(): Promise<{
  reloaded: boolean;
  template_count: number;
  option_count: number;
}> {
  return sendJson("/admin/api/events/reload", {
    method: "POST",
  });
}

export async function reloadRealms(): Promise<RealmReloadResponse> {
  return sendJson("/admin/api/realms/reload", {
    method: "POST",
  });
}

export async function reloadDwelling(): Promise<DwellingReloadResponse> {
  return sendJson("/admin/api/dwelling/reload", {
    method: "POST",
  });
}

export async function reloadBattleEnemies(): Promise<EnemyReloadResponse> {
  return sendJson("/admin/api/battle/reload", {
    method: "POST",
  });
}

export async function reloadAlchemy(): Promise<AlchemyReloadResponse> {
  return sendJson("/admin/api/alchemy/reload", {
    method: "POST",
  });
}

export async function reorderRealms(keys: string[]): Promise<RealmReorderResponse> {
  return sendJson("/admin/api/realms/reorder", {
    method: "POST",
    body: JSON.stringify({ keys }),
  });
}

export async function fetchAdminSession(): Promise<AdminSession | null> {
  const response = await fetch("/admin/api/auth/session");
  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "加载管理会话失败"));
  }
  return response.json();
}

export async function loginAdmin(
  username: string,
  password: string
): Promise<AdminSession> {
  return sendJson("/admin/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function logoutAdmin(): Promise<void> {
  await sendJson("/admin/api/auth/logout", {
    method: "POST",
  });
}

async function sendJson<T>(input: string, init: RequestInit): Promise<T> {
  const response = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await buildErrorMessage(response, "请求失败"));
  }
  return response.json();
}

async function buildErrorMessage(response: Response, fallbackMessage: string): Promise<string> {
  try {
    const payload = await response.json();
    return buildAdminErrorMessage(payload, fallbackMessage);
  } catch {
    return fallbackMessage;
  }
}
