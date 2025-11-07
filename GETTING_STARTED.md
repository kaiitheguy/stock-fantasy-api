# Getting Started: AI Trading Fantasy

Quick setup guide to get the system running in 10 minutes.

## ⚡ Quick Setup (5 minutes)

### 1. Choose LLM Providers (Pick at least 1)

| Provider | Cost | Setup Time | Notes |
|----------|------|-----------|-------|
| **OpenAI** | Medium | 1 min | Most reliable, already configured |
| **Anthropic** | Medium | 2 min | Great reasoning for trading |
| **DeepSeek** ⭐ | Cheapest | 5 min | Requires phone verification |

### 2. Get API Keys

**OpenAI (Already in .env):**
- You already have: `sk-proj-...`
- No action needed ✅

**Anthropic (Optional):**
1. Go to https://console.anthropic.com/
2. Click "API Keys" → "Create new key"
3. Copy key (starts with `sk-ant-`)
4. Edit `app/.env`: `ANTHROPIC_API_KEY=sk-ant-your-key`

**DeepSeek (Cheapest, but requires setup):**
1. Go to https://platform.deepseek.com/
2. Sign up + complete phone verification
3. Add payment method ($5-10 minimum)
4. API Keys → Create new
5. Copy key (starts with `sk-`)
6. Edit `app/.env`: `DEEPSEEK_API_KEY=sk-your-key`

### 3. Verify Configuration

Edit `app/.env` to add any optional keys:
```env
# Required (already set)
OPENAI_API_KEY=sk-proj-...

# Optional (add if you have them)
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...

# Server port
PORT=3000
```

### 4. Test Everything

Run the playground notebook:
```bash
jupyter notebook app/playground.ipynb
```

This will test:
- ✅ Real market data (Yahoo Finance)
- ✅ All configured LLM providers
- ✅ Parallel decision making
- ✅ Full integration

---

## 📊 What Each Test Does

### Test 1: Yahoo Finance Market Data
Fetches real stock data:
- Current price
- 3-month change %
- RSI (momentum indicator)
- EMA-50 / EMA-200 (trends)
- MACD (trend confirmation)
- Volume

### Test 2: LLM Providers
Tests each configured provider:
- OpenAI (GPT-4-mini)
- Anthropic (Claude-Haiku)
- DeepSeek (DeepSeek-Chat)

Gets trading decisions from each.

### Test 3: Parallel Orchestration
Gets decisions from multiple agents simultaneously.

### Test 4: Agent Generation
Lists all 25+ agent combinations:
- 5 models × 5 styles = 25+ agents
- Each agent = LLM model + trading style

### Test 5: Full Integration
End-to-end test combining everything:
- Real market data
- Real LLM decisions
- Real trading styles
- Real parallel orchestration

---

## 💾 Using Market Data

```python
from app.market_data_service import MarketDataService

service = MarketDataService()

# Single stock
aapl = await service.get_ticker_data("AAPL")
print(f"Price: ${aapl['price']}")
print(f"RSI: {aapl['rsi']}")

# Multiple stocks (parallel)
data = await service.get_multiple_tickers(["AAPL", "MSFT", "GOOGL"])
for ticker, info in data.items():
    print(f"{ticker}: ${info['price']}")

# Just the price
price = await service.get_current_price("AAPL")

# Format for LLM
market_str = service.format_market_data_for_llm(aapl)
# → Ready to pass to trading system
```

---

## 🤖 Using LLM Services

```python
from app.llm_service import OpenAIProvider, LLMOrchestrator
from app.trading_styles import TRADING_STYLES

# Single provider
provider = OpenAIProvider()
decision = await provider.get_trading_decision(
    system_prompt=TRADING_STYLES["conservative"]["system_prompt"],
    market_data="AAPL: $150, RSI: 65...",
    account_state='{"cash": 8500, "positions": {"AAPL": 10}}',
    model="gpt-4-mini"
)
print(f"Action: {decision.action}")  # buy/sell/hold
print(f"Ticker: {decision.ticker}")
print(f"Confidence: {decision.confidence}")

# Parallel decisions
orchestrator = LLMOrchestrator()
decisions = await orchestrator.get_decisions_parallel([
    {"agent_id": 1, "model_name": "gpt-4-mini", ...},
    {"agent_id": 2, "model_name": "claude-3-haiku", ...},
])
```

---

## 🎯 Trading Styles

System includes 5 trading styles. Each can be combined with any LLM model:

### 1. Conservative
- Small positions (max 15% portfolio)
- Tight stops (-3%)
- Focus on capital preservation
- Requires 3+ aligned signals

### 2. Aggressive
- Large positions (max 30% portfolio)
- Quick exits
- Focus on growth
- Acts on 2+ signals

### 3. Momentum
- Follow trends
- Buy when price > 50-day EMA
- Exit on momentum break
- Hold 1-4 weeks

### 4. Mean Reversion
- Buy oversold (RSI < 35)
- Sell overbought (RSI > 70)
- Bet against extremes
- Hold 2-6 weeks

### 5. Balanced
- 5-6 diversified positions
- +10% profit target, -4% stop loss
- Moderate everything
- Hold 3-8 weeks

---

## 💰 Cost Estimate

Weekly costs for 25 agents (5 per style):

| Model | Cost/Week | Note |
|-------|-----------|------|
| DeepSeek | $0.07 | ⭐ Cheapest |
| GPT-4-mini | $0.05 | Already configured |
| Claude-Haiku | $0.28 | |
| Claude-Sonnet | $1.05 | Better quality |
| GPT-4-turbo | $3.50 | Best quality |
| **TOTAL** | **~$5.00** | Per-user: $0.05/week |

**Recommended mix:**
- 5 DeepSeek agents (cheap)
- 5 GPT-4-mini agents (reliable)
- 5 Claude-Haiku agents (alternative)
- 5 Claude-Sonnet agents (quality)
- 5 GPT-4-turbo agents (best)

---

## ⚙️ Configuration

### Environment Variables

File: `app/.env`

```env
# LLM API Keys
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
DEEPSEEK_API_KEY=sk-your-key

# Server
PORT=3000

# Database (Phase 2)
# SUPABASE_URL=https://...
# SUPABASE_KEY=eyJ...
```

### Market Data Service

```python
# Default: cache for 60 seconds
service = MarketDataService()

# Custom TTL
service = MarketDataService(cache_ttl_seconds=30)

# Clear cache
service.cache.clear()
```

---

## 🐛 Troubleshooting

### "API key missing" error
- Check `app/.env` has your key
- Verify key isn't empty

### "Invalid API key" error
- Copy key again from provider dashboard
- Check for extra spaces
- Try creating a new key

### "Rate limit exceeded"
- Wait 1 minute
- Check provider dashboard for usage
- Consider upgrading plan

### "No module named 'app'"
- Run notebook from project root
- Ensure Python path is correct

### DeepSeek not available
- May not work in your country
- Check https://platform.deepseek.com/
- Try different region/VPN

### Tests failing
1. Check all required keys are set
2. Verify internet connection
3. Check API key usage limits
4. See ARCHITECTURE.md for details

---

## 📖 Learn More

- **ARCHITECTURE.md** - Technical deep dive
- **README.md** - Project overview
- **app/playground.ipynb** - Working examples

---

## ✅ Next Steps

1. ✅ Add API keys to `app/.env`
2. ✅ Run `app/playground.ipynb`
3. ✅ Verify all tests pass
4. ✅ Ready to build Phase 2!

**Status: Ready to use!** 🚀
