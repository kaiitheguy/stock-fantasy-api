-- Supabase SQL Schema aligned to the current JSON-backed model (demo data in data/*.json).
-- Tables mirror: agent_info, agent_events, user_info, user_events, weekly_pnl.

-- 1) Agent catalog (10 canonical agents generated at startup)
CREATE TABLE agent_info (
  agent_id SERIAL PRIMARY KEY,
  model_name VARCHAR(50) NOT NULL,
  model_provider VARCHAR(50),
  style_name VARCHAR(50) NOT NULL,
  style_description TEXT,
  system_prompt TEXT NOT NULL,
  cost_tier VARCHAR(20) DEFAULT 'medium', -- 'cheap', 'medium', 'expensive'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (model_name, style_name)
);

-- 2) Users
CREATE TABLE user_info (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3) User agent selections/drops (monthly roster changes)
CREATE TABLE user_events (
  event_id BIGSERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES user_info(user_id),
  action VARCHAR(10) NOT NULL CHECK (action IN ('select', 'drop')),
  agent_ids INT[] DEFAULT '{}',      -- used for "select" events (3-5 agents)
  agent_id INT,                      -- used for "drop" events (single agent)
  month_number INT,                  -- e.g., 202411
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_user_events_user ON user_events(user_id);
CREATE INDEX idx_user_events_month ON user_events(month_number);

-- 4) Agent trades (weekly)
CREATE TABLE agent_events (
  event_id BIGSERIAL PRIMARY KEY,
  agent_id INT NOT NULL REFERENCES agent_info(agent_id),
  user_id INT REFERENCES user_info(user_id),  -- optional: if trade tied to a user roster
  week_number INT NOT NULL,
  action VARCHAR(10) NOT NULL CHECK (action IN ('buy', 'sell')),
  stock_ticker VARCHAR(10) NOT NULL,
  quantity INT NOT NULL,
  price DECIMAL(12, 2) NOT NULL,
  pnl_delta DECIMAL(12, 2) DEFAULT 0.00,
  action_reason TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_agent_events_agent ON agent_events(agent_id);
CREATE INDEX idx_agent_events_week ON agent_events(week_number);

-- 5) Weekly P&L snapshots (optional, can be recomputed)
CREATE TABLE weekly_pnl (
  snapshot_id BIGSERIAL PRIMARY KEY,
  week_number INT NOT NULL,
  standings JSONB NOT NULL, -- array of agent standings with rank/total_pnl
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_weekly_pnl_week ON weekly_pnl(week_number);
