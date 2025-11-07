-- Supabase SQL Schema for AI Trading Fantasy

-- Agents table (Model x Style combinations)
CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(50) NOT NULL,
  style_name VARCHAR(50) NOT NULL,
  system_prompt TEXT NOT NULL,
  cost_tier VARCHAR(20) NOT NULL DEFAULT 'medium', -- 'cheap', 'medium', 'expensive'
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(model_name, style_name)
);

-- Weekly Leagues
CREATE TABLE leagues (
  id SERIAL PRIMARY KEY,
  week_number INT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'closed', 'archived'
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(week_number)
);

-- League agents (many-to-many)
CREATE TABLE league_agents (
  id SERIAL PRIMARY KEY,
  league_id INT NOT NULL REFERENCES leagues(id),
  agent_id INT NOT NULL REFERENCES agents(id),
  starting_capital DECIMAL(12, 2) DEFAULT 10000.00,
  current_cash DECIMAL(12, 2) DEFAULT 10000.00,
  positions JSONB DEFAULT '{}', -- {ticker: quantity, ...}
  realized_pnl DECIMAL(12, 2) DEFAULT 0.00,
  unrealized_pnl DECIMAL(12, 2) DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(league_id, agent_id)
);

-- Trades executed by agents
CREATE TABLE trades (
  id SERIAL PRIMARY KEY,
  agent_id INT NOT NULL REFERENCES agents(id),
  league_id INT NOT NULL REFERENCES leagues(id),
  decision_timestamp TIMESTAMP NOT NULL,
  action VARCHAR(20) NOT NULL, -- 'buy', 'sell', 'hold'
  ticker VARCHAR(10),
  quantity INT,
  entry_price DECIMAL(12, 2),
  llm_reasoning TEXT,
  executed BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Market data cache (for backfill testing)
CREATE TABLE market_data (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(10) NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  price DECIMAL(12, 2),
  volume BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(ticker, timestamp)
);

CREATE INDEX idx_agents_model_style ON agents(model_name, style_name);
CREATE INDEX idx_trades_agent_league ON trades(agent_id, league_id);
CREATE INDEX idx_trades_timestamp ON trades(decision_timestamp);
CREATE INDEX idx_league_agents_league ON league_agents(league_id);
CREATE INDEX idx_market_data_ticker_time ON market_data(ticker, timestamp);
