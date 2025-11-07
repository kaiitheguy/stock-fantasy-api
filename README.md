# Stock Fantasy API: AI Trading Fantasy League 🚀

A backend system for an AI-powered trading fantasy league where users pick different AI trading agents and compete in weekly paper trading competitions.

## Overview

Instead of manually picking stocks, users pick **AI trading agents** (combinations of LLM models × trading styles) and watch them autonomously trade S&P 500 stocks. Each agent makes trading decisions based on real market data and technical analysis.

**Key Stats:**
- 25+ unique AI agents (5 models × 5 styles)
- Real market data from Yahoo Finance
- 3 LLM providers: OpenAI, Anthropic, DeepSeek
- Paper trading with $10,000 starting capital per agent
- Weekly P&L scoring and rankings
- $5/week cost for full system

## ⚡ Quick Start (5 minutes)

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Add API keys to app/.env (you already have OpenAI)
# OPTIONAL: Add Anthropic or DeepSeek keys

# 3. Test everything
jupyter notebook app/playground.ipynb

# 4. Run server
uvicorn server:app --host 0.0.0.0 --port 3000 --reload
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Setup, quick start, API configuration, troubleshooting |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical details, data models, implementation |

## 🎯 What It Does

### Market Data (Yahoo Finance)
- Real-time stock prices
- Technical indicators: RSI, EMA, MACD, Volume
- Parallel data fetching for speed
- Smart caching (60-second TTL)

### Trading Agents (25+ Combinations)
- 5 LLM models: GPT-4, GPT-4-mini, Claude-Sonnet, Claude-Haiku, DeepSeek
- 5 trading styles: Conservative, Aggressive, Momentum, Mean Reversion, Balanced
- Each agent autonomously makes buy/sell/hold decisions
- Parallel decision making (all agents decide simultaneously)

### Paper Trading
- Simulated trading (no real money)
- Position limits: max 5 stocks, max 30% per stock
- Trade validation before execution
- Full trade logging with reasoning

### Scoring & Standings
- Weekly P&L calculation
- Simple metric: Total return percentage
- Agent rankings by performance
- Trade transparency (all reasoning logged)

## 🏗️ Architecture

```
Market Data (Yahoo)
    ↓
Parallel LLM Calls (OpenAI/Anthropic/DeepSeek)
    ↓
Trade Validation (Position limits, cash available)
    ↓
Paper Trading Execution
    ↓
P&L Calculation (Realized + Unrealized)
    ↓
League Standings Update
    ↓
Database Storage
```

## 💻 Core Services

| Service | Purpose |
|---------|---------|
| `market_data_service.py` | Yahoo Finance data + technical indicators |
| `llm_service.py` | LLM orchestration (OpenAI, Anthropic, DeepSeek) |
| `trading_engine.py` | Paper trading simulation |
| `scoring_service.py` | P&L calculation + standings |
| `agent_service.py` | Agent generation (25+ combinations) |
| `trading_api.py` | 16 REST API endpoints |

## 🤖 Trading Styles

| Style | Focus | Risk | Hold |
|-------|-------|------|------|
| **Conservative** | Capital preservation | Low | 4+ weeks |
| **Aggressive** | Growth | High | 1-3 weeks |
| **Momentum** | Trend following | Medium | 1-4 weeks |
| **Mean Reversion** | Buy dips, sell rallies | Low | 2-6 weeks |
| **Balanced** | Moderate everything | Medium | 3-8 weeks |

Each style = unique system prompt that guides LLM decisions.

## 💰 Cost Breakdown

Weekly costs for 25 agents (MVP):

| Model | Cost/Week | Agents | Note |
|-------|-----------|--------|------|
| DeepSeek | $0.07 | 5 | ⭐ Cheapest |
| GPT-4-mini | $0.05 | 5 | Already configured |
| Claude-Haiku | $0.28 | 5 | |
| Claude-Sonnet | $1.05 | 5 | Better reasoning |
| GPT-4-turbo | $3.50 | 5 | Best quality |
| **TOTAL** | **~$5.00** | **25** | Per-user: $0.05/week |

## 📦 Requirements

- Python 3.10+
- FastAPI
- Pydantic
- OpenAI API key (required)
- Anthropic API key (optional)
- DeepSeek API key (optional)
- YFinance

Install all dependencies:
```bash
pip install -r requirements.txt
```

## 🔧 Configuration

### Environment Variables (app/.env)

```env
# Required (you already have this)
OPENAI_API_KEY=sk-proj-...

# Optional but recommended
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...

# Server
PORT=3000

# Database (Phase 2)
# SUPABASE_URL=https://...
# SUPABASE_KEY=eyJ...
```

## 🚀 Running

**Development:**
```bash
uvicorn server:app --host 0.0.0.0 --port 3000 --reload
```

**Testing:**
```bash
jupyter notebook app/playground.ipynb
```

**Production:**
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

## 📊 API Endpoints

### Agents
- `GET /api/trading/agents` - List all agents
- `GET /api/trading/agents/{model}/{style}` - Get specific agent

### Leagues
- `POST /api/trading/leagues` - Create new league
- `GET /api/trading/leagues/{id}` - Get league details

### Standings
- `GET /api/trading/leagues/{id}/standings` - Rankings by P&L
- `GET /api/trading/leagues/{id}/scores` - Detailed scores

### Trading
- `GET /api/trading/leagues/{id}/trades` - All trades with reasoning
- `POST /api/trading/decisions/get` - Get single LLM decision
- `POST /api/trading/decisions/batch` - Get parallel decisions

## 🔄 Workflow

1. User creates weekly league
2. User drafts 5-10 agents
3. System fetches real market data
4. System calls LLMs in parallel
5. System executes validated trades
6. System calculates P&L
7. System updates standings
8. User sees results

All in ~5 minutes per cycle!

## 📈 Next Phase (Phase 2)

- [ ] Supabase database integration
- [ ] Background scheduler for decision cycles
- [ ] Automated trade execution
- [ ] Real-time P&L updates
- [ ] Frontend dashboard

## 📚 Learn More

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup and quick start
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical details
- **app/playground.ipynb** - Working examples and tests

## ⚠️ Disclaimer

This is a **paper trading system** - no real money involved. For educational and entertainment purposes only. Do not use for actual trading decisions.

## 📄 License

MIT License - See LICENSE file
