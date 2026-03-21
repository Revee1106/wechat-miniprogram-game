import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const schema = readFileSync("sql/wendao_core_loop_schema.sql", "utf8");

assert.match(schema, /CREATE TABLE run_character\b/i);
assert.match(schema, /CREATE TABLE event_template\b/i);
assert.match(schema, /CREATE TABLE rebirth_progress\b/i);
