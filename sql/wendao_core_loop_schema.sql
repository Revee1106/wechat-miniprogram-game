CREATE TABLE run_character (
  run_id VARCHAR(64) PRIMARY KEY,
  player_id VARCHAR(64) NOT NULL,
  realm VARCHAR(32) NOT NULL,
  cultivation_exp BIGINT NOT NULL DEFAULT 0,
  lifespan_current INT NOT NULL,
  lifespan_max INT NOT NULL,
  luck INT NOT NULL DEFAULT 0,
  is_dead TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE event_template (
  event_key VARCHAR(64) PRIMARY KEY,
  display_name VARCHAR(128) NOT NULL,
  description TEXT NOT NULL,
  region VARCHAR(64) NOT NULL,
  weight INT NOT NULL DEFAULT 1
);

CREATE TABLE rebirth_progress (
  player_id VARCHAR(64) PRIMARY KEY,
  total_rebirth_count INT NOT NULL DEFAULT 0,
  permanent_luck_bonus INT NOT NULL DEFAULT 0
);
