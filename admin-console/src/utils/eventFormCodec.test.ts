import { expect, test } from "vitest";

import {
  buildPayloadFromEditorState,
  buildPayloadWithBattleConfig,
  parsePayloadEditorState,
  parseBattleConfig,
} from "./eventFormCodec";

test("parses legacy payload strings into editor state", () => {
  const state = parsePayloadEditorState(
    "cultivation_exp:+3,spirit_stone:-1,herbs:+2,iron_essence:+4,lifespan:-5,death:true"
  );

  expect(state).toMatchObject({
    resources: {
      spirit_stone: -1,
      herb: 2,
      ore: 4,
    },
    cultivation_exp: 3,
    lifespan_delta: -5,
    death: true,
  });
});

test("builds compact structured payloads from editor state", () => {
  const payload = buildPayloadFromEditorState({
    resources: { spirit_stone: 2 },
    cultivation_exp: 6,
    lifespan_delta: 0,
    hp_delta: 0,
    breakthrough_bonus: 0,
    technique_exp: 0,
    luck_delta: 0,
    karma_delta: 0,
    rebirth_progress_delta: 0,
    statuses_add: ["blessed"],
    statuses_remove: [],
    techniques_add: [],
    equipment_add: [],
    equipment_remove: [],
    death: false,
  });

  expect(payload).toEqual({
    resources: { spirit_stone: 2 },
    character: { cultivation_exp: 6 },
    statuses_add: ["blessed"],
  });
});

test("normalizes structured resource payload aliases into canonical editor keys", () => {
  const state = parsePayloadEditorState({
    resources: {
      herbs: 2,
      iron_essence: 4,
      spirit_stone: 1,
    },
  });

  expect(state.resources).toEqual({
    spirit_stone: 1,
    herb: 2,
    ore: 4,
  });
});

test("parses battle config from structured payloads", () => {
  const battle = parseBattleConfig({
    resources: { spirit_stone: 2 },
    battle: {
      enemy_name: "山匪",
      enemy_realm_label: "炼气初期",
      enemy_hp: 36,
      enemy_attack: 8,
      enemy_defense: 4,
      enemy_speed: 6,
      allow_flee: true,
      flee_base_rate: 0.35,
      pill_heal_amount: 30,
    },
  });

  expect(battle).toEqual({
    enemy_name: "山匪",
    enemy_realm_label: "炼气初期",
    enemy_hp: 36,
    enemy_attack: 8,
    enemy_defense: 4,
    enemy_speed: 6,
    allow_flee: true,
    flee_base_rate: 0.35,
    pill_heal_amount: 30,
    victory_log: "",
    defeat_log: "",
    flee_success_log: "",
    flee_failure_log: "",
  });
});

test("merges battle config into structured payloads", () => {
  const payload = buildPayloadWithBattleConfig(
    {
      resources: { spirit_stone: 2 },
    },
    {
      enemy_name: "山匪",
      enemy_realm_label: "炼气初期",
      enemy_hp: 36,
      enemy_attack: 8,
      enemy_defense: 4,
      enemy_speed: 6,
      allow_flee: false,
      flee_base_rate: 0.2,
      pill_heal_amount: 24,
      victory_log: "你将山匪逼退。",
      defeat_log: "",
      flee_success_log: "",
      flee_failure_log: "",
    }
  );

  expect(payload).toEqual({
    resources: { spirit_stone: 2 },
    battle: {
      enemy_name: "山匪",
      enemy_realm_label: "炼气初期",
      enemy_hp: 36,
      enemy_attack: 8,
      enemy_defense: 4,
      enemy_speed: 6,
      allow_flee: false,
      flee_base_rate: 0.2,
      pill_heal_amount: 24,
      victory_log: "你将山匪逼退。",
    },
  });
});
