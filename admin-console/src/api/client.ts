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
  base_success_rate: number;
  required_cultivation_exp: number;
  required_spirit_stone: number;
  lifespan_bonus: number;
  is_enabled: boolean;
};

export type RealmInput = RealmConfig;

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
    throw new Error("Failed to load events");
  }
  return response.json();
}

export async function fetchEventDetail(eventId: string): Promise<EventDetailResponse> {
  const response = await fetch(`/admin/api/events/${eventId}`);
  if (!response.ok) {
    throw new Error("Failed to load event detail");
  }
  return response.json();
}

export async function fetchRealms(): Promise<RealmListResponse> {
  const response = await fetch("/admin/api/realms");
  if (!response.ok) {
    throw new Error("Failed to load realms");
  }
  return response.json();
}

export async function fetchRealmDetail(realmKey: string): Promise<RealmDetailResponse> {
  const response = await fetch(`/admin/api/realms/${realmKey}`);
  if (!response.ok) {
    throw new Error("Failed to load realm detail");
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
  return sendJson("/admin/api/events/validate", {
    method: "POST",
  });
}

export async function validateRealms(): Promise<ValidationResponse> {
  return sendJson("/admin/api/realms/validate", {
    method: "POST",
  });
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
    throw new Error("Failed to load admin session");
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
    throw new Error(await buildErrorMessage(response));
  }
  return response.json();
}

async function buildErrorMessage(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string" && payload.detail) {
      return payload.detail;
    }
  } catch {
    return "Request failed";
  }
  return "Request failed";
}
