# Architecture & Implementation

Complete technical documentation for the AI Trading Fantasy system.

## 📐 System Architecture

### High-Level Flow

```
Market Data → LLM Decisions → Trade Validation → P&L Calculation → Standings
(Yahoo)       (OpenAI/etc)    (Position limits)  (Realized+Unreal)  (Rankings)
```

### Core Components

```
app/
├── market_data_service.py      # Yahoo Finance integration
├── llm_service.py              # LLM orchestration (3 providers)
├── trading_engine.py           # Paper trading simulation
├── scoring_service.py          # P&L & standings calculation
├── agent_service.py            # Agent generation (25+ combinations)
├── trading_styles.py           # 5 trading style prompts
├── trading_api.py              # 16 REST API endpoints
└── schemas.py                  # Pydantic data models
```

---

## 🔄 Trading Cycle (Every 3-5 Minutes)

1. **Market Data Fetch** (Yahoo Finance)
   - Get current prices for S&P 500 stocks
   - Calculate technical indicators (RSI, EMA, MACD)
   - Cache results (60-second TTL)

2. **LLM Decisions** (Parallel)
   - Send market data to all agents simultaneously
   - Each agent gets their trading style prompt
   - LLM returns: action, ticker, quantity, reasoning

3. **Trade Validation**
   - Check position limits (max 5 stocks, max 30% per stock)
   - Check available cash
   - Validate action is buy/sell/hold

4. **Trade Execution** (Simulated)
   - Update positions (buy increases, sell decreases)
   - Update cash balance
   - Log trade with reasoning

5. **P&L Update**
   - Calculate unrealized P&L from open positions
   - Calculate realized P&L from closed positions
   - Update league standings

6. **Data Persistence**
   - Store trades to database
   - Update agent performance stats
   - Generate reports

---

## 📊 Data Models

### Agent
```python
{
    "id": 1,
    "model_name": "gpt-4-mini",           # LLM model
    "style_name": "conservative",         # Trading style
    "system_prompt": "...",               # Full system prompt
    "cost_tier": "cheap"                  # cheap/medium/expensive
}
```

### Trade
```python
{
    "id": 1,
    "agent_id": 1,
    "league_id": 1,
    "decision_timestamp": "2024-11-06T10:15:00",
    "action": "buy",                      # buy/sell/hold
    "ticker": "AAPL",
    "quantity": 10,
    "entry_price": 150.25,
    "llm_reasoning": "RSI exceeded 70...",
    "executed": True
}
```

### Market Data
```python
{
    "ticker": "AAPL",
    "price": 150.25,
    "three_month_change_pct": 12.5,
    "rsi": 65.2,                          # 0-100
    "ema_50": 148.0,
    "ema_200": 145.0,
    "macd_line": 2.5,
    "macd_signal": 1.8,
    "macd_histogram": 0.7,
    "volume": 50000000,
    "timestamp": "2024-11-06T10:00:00"
}
```

### League Agent (Performance)
```python
{
    "league_id": 1,
    "agent_id": 1,
    "starting_capital": 10000.0,
    "current_cash": 8500.0,
    "positions": {"AAPL": 10, "MSFT": 5},
    "realized_pnl": 150.0,                # Closed trade profits
    "unrealized_pnl": 500.0,              # Open position gains
    "total_pnl": 650.0,                   # Total return
    "pnl_pct": 6.5                        # Percentage return
}
```

---

## 🎯 Trading Styles (5 Types)

Each style = unique system prompt that guides LLM decisions.

### Conservative
```
Position Size: Max 15% portfolio
Stop Loss: -3%
Profit Target: +8-12%
Hold: 4+ weeks
Entry: 3+ aligned signals
```

### Aggressive
```
Position Size: Max 30% portfolio
Stop Loss: -5%
Profit Target: +15-25%
Hold: 1-3 weeks
Entry: 2+ aligned signals
```

### Momentum
```
Buy When: Price > 50-day EMA + RSI > 60
Sell When: Momentum breaks or -10% stop
Hold: 1-4 weeks
Focus: Trend confirmation
```

### Mean Reversion
```
Buy When: RSI < 35 (oversold)
Sell When: RSI > 70 (overbought)
Hold: 2-6 weeks
Avoid: Clear downtrends
```

### Balanced
```
Position Size: 15-20% per stock
Positions: 5-6 stocks
Profit Target: +10%
Stop Loss: -4%
Hold: 3-8 weeks
```

---

## 🤖 LLM Providers

### OpenAI
- **Models**: GPT-4-turbo, GPT-4, GPT-4-mini
- **Cost**: $0.01-0.00015 per 1K tokens
- **Speed**: Fast (~1 second)
- **Quality**: Excellent
- **Status**: ✅ Configured (you have API key)

### Anthropic
- **Models**: Claude-3.5-Sonnet, Claude-3-Haiku
- **Cost**: $0.003-0.0008 per 1K tokens
- **Speed**: Fast (~1-2 seconds)
- **Quality**: Excellent (great reasoning)
- **Status**: ⚠️ Optional (add key to .env)

### DeepSeek
- **Models**: DeepSeek-Chat
- **Cost**: ~$0.0002 per 1K tokens ⭐ **Cheapest**
- **Speed**: Fast (~2 seconds)
- **Quality**: Good
- **Status**: ⚠️ Optional (requires phone verification)

---

## 💾 Market Data Service

### Usage

```python
from app.market_data_service import MarketDataService

service = MarketDataService()

# Get single stock with all indicators
data = await service.get_ticker_data("AAPL")
# Returns: {price, rsi, ema_50, ema_200, macd, volume, ...}

# Get multiple stocks in parallel
data = await service.get_multiple_tickers(["AAPL", "MSFT", "GOOGL"])

# Just the price
price = await service.get_current_price("AAPL")

# Format for LLM input
market_str = service.format_market_data_for_llm(data)
```

### Technical Indicators

| Indicator | Formula | Use |
|-----------|---------|-----|
| **RSI** | Relative Strength Index | Momentum (0-100) |
| **EMA-50** | 50-period exponential moving average | Short-term trend |
| **EMA-200** | 200-period exponential moving average | Long-term trend |
| **MACD** | Moving Average Convergence Divergence | Trend + momentum |
| **Volume** | Trading volume | Activity strength |
| **Change %** | 3-month price change | Recent trend |

### Caching

- Default: 60-second TTL
- Prevents duplicate API calls
- Improves performance
- Configurable: `MarketDataService(cache_ttl_seconds=120)`

---

## 🔀 LLM Orchestration

### Single LLM Decision

```python
from app.llm_service import OpenAIProvider

provider = OpenAIProvider()
decision = await provider.get_trading_decision(
    system_prompt="...",
    market_data="AAPL: $150, RSI: 65...",
    account_state='{"cash": 8500, "positions": {"AAPL": 10}}',
    model="gpt-4-mini"
)

# Returns LLMDecision:
# {
#     action: "buy",           # buy/sell/hold
#     ticker: "MSFT",
#     quantity: 5,
#     confidence: 0.85,
#     reasoning: "Strong momentum signal..."
# }
```

### Parallel Decisions

```python
from app.llm_service import LLMOrchestrator

orchestrator = LLMOrchestrator()

# Call 25+ agents simultaneously
decisions = await orchestrator.get_decisions_parallel([
    {"agent_id": 1, "model_name": "gpt-4-mini", ...},
    {"agent_id": 2, "model_name": "claude-3-haiku", ...},
    {"agent_id": 3, "model_name": "deepseek-chat", ...},
    # ... more agents
])

# Results: Dict[agent_id, LLMDecision]
for agent_id, decision in decisions.items():
    print(f"Agent {agent_id}: {decision.action} {decision.ticker}")
```

---

## 📋 Paper Trading Engine

### Position Limits

- **Max positions**: 5 stocks per agent
- **Max position size**: 30% of portfolio
- **Min position size**: $100
- **No shorting**: Only long positions
- **No leverage**: 1x only

### Trade Execution

1. **Validation**
   - Check position limits
   - Check cash available
   - Check action is valid

2. **Execution**
   - Update positions
   - Update cash balance
   - Log trade

3. **P&L Calculation**
   - Unrealized: (current_price - entry_price) × quantity
   - Realized: Sum of closed position gains
   - Total: Realized + Unrealized

### Example

```python
from app.trading_engine import TradingEngine

engine = TradingEngine()

# Execute a decision
success, trade, error = await engine.execute_decision(
    decision=LLMDecision(...),
    agent_id=1,
    league_id=1,
    current_price=150.25,
    account_state={
        "cash": 8500,
        "positions": {"AAPL": 10},
        "starting_capital": 10000
    }
)

if success:
    print(f"Trade executed: {trade.action} {trade.ticker}")
else:
    print(f"Trade failed: {error}")
```

---

## 📊 Scoring System

### Weekly Scoring

1. **Fetch all trades for agent**
2. **Calculate realized P&L**
   - From closed positions
   - Using FIFO cost basis

3. **Calculate unrealized P&L**
   - From open positions
   - Using current prices

4. **Calculate metrics**
   - Total P&L = Realized + Unrealized
   - P&L % = (Total P&L / Starting Capital) × 100
   - Win rate = Winning trades / Total trades

5. **Rank agents**
   - Sort by total P&L (descending)
   - Generate standings

### Example Response

```python
standings = await scoring_service.get_league_standings(league_id=1)
# [
#     LeagueAgent(
#         rank=1,
#         agent_id=1,
#         total_pnl=856.50,
#         pnl_pct=8.57,
#         win_rate=75.0
#     ),
#     ...
# ]
```

---

## 🌐 API Endpoints

### Agent Management
- `GET /api/trading/agents` - List all agents
- `GET /api/trading/agents/count` - Total agent count
- `GET /api/trading/agents/{model}/{style}` - Get specific agent

### League Management
- `POST /api/trading/leagues` - Create league
- `GET /api/trading/leagues/{id}` - Get league details
- `POST /api/trading/leagues/{id}/agents/{agent_id}` - Draft agent

### Standings
- `GET /api/trading/leagues/{id}/standings` - Ranked agents
- `GET /api/trading/leagues/{id}/scores` - Detailed scores

### Trades
- `GET /api/trading/leagues/{id}/trades` - All trades with reasoning

### Decisions
- `POST /api/trading/decisions/get` - Single LLM decision
- `POST /api/trading/decisions/batch` - Parallel decisions

---

## 🗄️ Database Schema (Supabase)

### agents
```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50),
    style_name VARCHAR(50),
    system_prompt TEXT,
    cost_tier VARCHAR(20),
    created_at TIMESTAMP
)
```

### leagues
```sql
CREATE TABLE leagues (
    id SERIAL PRIMARY KEY,
    week_number INT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP
)
```

### league_agents
```sql
CREATE TABLE league_agents (
    id SERIAL PRIMARY KEY,
    league_id INT,
    agent_id INT,
    starting_capital DECIMAL,
    current_cash DECIMAL,
    positions JSONB,
    realized_pnl DECIMAL,
    unrealized_pnl DECIMAL
)
```

### trades
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    agent_id INT,
    league_id INT,
    decision_timestamp TIMESTAMP,
    action VARCHAR(20),
    ticker VARCHAR(10),
    quantity INT,
    entry_price DECIMAL,
    llm_reasoning TEXT
)
```

---

## 🔐 Security

### API Keys
- Store in `app/.env`
- Never commit to git
- Rotate regularly
- Monitor usage

### Database
- Use Supabase (managed)
- Encrypted connections
- Row-level security (future)
- Regular backups

### Trading
- Position limits enforced
- No real money (paper trading)
- Reversible (can reset anytime)
- Full audit trail (all trades logged)

---

## 📈 Extensibility

### Add New LLM Provider
1. Create class extending `LLMProvider`
2. Implement `get_trading_decision()`
3. Register in `LLMOrchestrator`

### Add New Trading Style
1. Create new entry in `TRADING_STYLES` dict
2. Write system prompt
3. Automatically creates 5+ agents (1 per model)

### Add New Market Indicator
1. Add calculation method to `MarketDataService`
2. Include in returned data
3. Format for LLM input

---

## 🚀 Performance

### Speed Targets
- Market data fetch: < 2 seconds (for 5 stocks)
- Single LLM decision: < 2 seconds
- Parallel decisions (25 agents): < 4 seconds
- Trade execution: < 100ms

### Optimization Strategies
- Parallel API calls (asyncio)
- Market data caching (60s TTL)
- Batch database operations
- Index database queries

---

## 📦 Dependencies

```
fastapi              # Web framework
pydantic             # Data validation
openai               # OpenAI API
anthropic            # Anthropic API
yfinance             # Yahoo Finance
python-dotenv        # Environment variables
```

---

## 🔄 Workflow (From Code to Results)

1. User creates league
2. User drafts 5-10 agents
3. System fetches market data
4. System calls LLM APIs (parallel)
5. System executes trades (validated)
6. System calculates P&L
7. System updates standings
8. User sees rankings

All in ~5 minutes per cycle!

---

## 📖 See Also

- **GETTING_STARTED.md** - Setup & quick start
- **README.md** - Project overview
- **app/playground.ipynb** - Working examples
