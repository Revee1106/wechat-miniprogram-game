import { expect, test } from "vitest";

import {
  buildPayloadFromEditorState,
  parsePayloadEditorState,
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
