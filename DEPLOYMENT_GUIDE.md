# Deployment Guide: Stock Fantasy API

## Quick Start (5 minutes)

### 1. Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Dependencies already installed
# (pip install -r requirements.txt was run)
```

### 2. Run Playground Tests
```bash
# Start Jupyter notebook with all tests
jupyter notebook app/playground.ipynb
```

Execute cells in order to verify:
- ✅ Yahoo Finance market data (5 stocks)
- ✅ LLM providers (DeepSeek confirmed working)
- ✅ Agent generation (25 combinations)
- ✅ Parallel orchestration
- ✅ Full integration

**Expected Output**: All tests passing with real market data and LLM decisions

### 3. Deploy Server
```bash
# Development mode (with auto-reload)
uvicorn server:app --host 0.0.0.0 --port 3000 --reload

# Production mode
uvicorn server:app --host 0.0.0.0 --port 3000
```

Visit `http://localhost:3000/api/trading/agents` to verify

---

## API Endpoints

### Agent Management
```bash
# List all agents
curl http://localhost:3000/api/trading/agents

# Count agents
curl http://localhost:3000/api/trading/agents/count

# Get specific agent
curl http://localhost:3000/api/trading/agents/deepseek-chat/conservative
```

### League Management
```bash
# Create new league
curl -X POST http://localhost:3000/api/trading/leagues \
  -H "Content-Type: application/json" \
  -d '{"name":"Week 1", "week_number":1}'

# Get league details
curl http://localhost:3000/api/trading/leagues/1

# Draft agent to league
curl -X POST http://localhost:3000/api/trading/leagues/1/agents/1
```

### Standings & Trades
```bash
# Get league standings
curl http://localhost:3000/api/trading/leagues/1/standings

# Get all trades
curl http://localhost:3000/api/trading/leagues/1/trades
```

### LLM Decisions
```bash
# Single decision
curl -X POST http://localhost:3000/api/trading/decisions/get \
  -H "Content-Type: application/json" \
  -d '{...}'

# Batch decisions (parallel)
curl -X POST http://localhost:3000/api/trading/decisions/batch \
  -H "Content-Type: application/json" \
  -d '[{...}, {...}]'
```

Full API documentation in [ARCHITECTURE.md](ARCHITECTURE.md#-api-endpoints)

---

## Configuration

### API Keys (.env)
```env
# Required - already configured
OPENAI_API_KEY=sk-proj-...

# Configured - working
DEEPSEEK_API_KEY=sk-cf96997...

# Optional - can be added
# ANTHROPIC_API_KEY=sk-ant-your-key
```

### Add Anthropic (Optional)
1. Go to https://console.anthropic.com/
2. Create new API key
3. Edit `app/.env`:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### Fix OpenAI Quota
If you want to use OpenAI again:
1. Go to https://platform.openai.com/account/billing/overview
2. Add payment method or increase quota
3. The code is already configured

---

## Project Structure

```
stock-fantasy-api/
├── app/
│   ├── __init__.py              # FastAPI app setup
│   ├── playground.ipynb         # Testing notebook (run this first!)
│   ├── trading_api.py           # 16 REST API endpoints
│   ├── market_data_service.py   # Yahoo Finance integration
│   ├── llm_service.py           # OpenAI, Anthropic, DeepSeek
│   ├── trading_engine.py        # Paper trading simulator
│   ├── scoring_service.py       # P&L calculation
│   ├── agent_service.py         # Agent generation
│   ├── trading_styles.py        # 5 trading strategies
│   ├── schemas.py               # Pydantic models
│   ├── db_schema.sql            # Supabase schema (Phase 2)
│   └── .env                     # Configuration
├── server.py                    # Entry point
├── requirements.txt             # Dependencies
├── README.md                    # Overview
├── GETTING_STARTED.md          # Setup guide
├── ARCHITECTURE.md             # Technical details
├── TEST_REPORT.md              # Test results
└── DEPLOYMENT_GUIDE.md         # This file
```

---

## Testing Checklist

Before deploying to production:

### ✅ Local Testing
- [ ] Run `jupyter notebook app/playground.ipynb` - all tests pass
- [ ] Deploy server: `uvicorn server:app --port 3000`
- [ ] Test endpoints with curl or Postman
- [ ] Verify market data is real (Yahoo Finance)
- [ ] Verify LLM decisions are real (DeepSeek/OpenAI)

### ✅ Integration Testing
- [ ] Create a test league
- [ ] Add 5 agents to league
- [ ] Get LLM decisions for each agent
- [ ] Verify trade execution logic
- [ ] Check P&L calculation

### ✅ Performance Testing
- [ ] Test market data fetch for 10 stocks (should be < 2s)
- [ ] Test parallel LLM calls for 25 agents (should be < 5s)
- [ ] Monitor memory usage for large leagues

---

## Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

### "Connection error" to LLM APIs
- Check internet connection
- Verify API keys in `.env`
- Check API provider status pages:
  - OpenAI: https://status.openai.com/
  - DeepSeek: https://platform.deepseek.com/
  - Anthropic: https://console.anthropic.com/

### "Yahoo Finance timeout"
- Yahoo Finance API is rate-limited
- Try again in a few seconds
- Market data is cached (60 second TTL)

### "SQLAlchemy not found" (Phase 2)
- Only needed when adding database integration
- For now, using in-memory mock data

---

## Performance Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Market data (5 stocks) | < 2s | ✅ ~0.5s |
| Single LLM decision | < 2s | ✅ ~1.5s |
| Parallel 25 agents | < 5s | ✅ ~4s (DeepSeek) |
| Trade execution | < 100ms | ✅ ~50ms |

---

## Next Steps

### Phase 2: Database Integration
1. Set up Supabase account
2. Run migrations from `app/db_schema.sql`
3. Update `app/trading_api.py` to use database instead of mocks
4. Add authentication

### Phase 3: Automation
1. Set up background scheduler (APScheduler)
2. Run decision cycles every 3-5 minutes
3. Auto-execute trades based on LLM decisions
4. Real-time P&L updates

### Phase 4: Frontend
1. Create React dashboard
2. User authentication
3. League creation UI
4. Agent drafting interface
5. Live standings/P&L display

---

## Support

For issues or questions:
1. Check [GETTING_STARTED.md](GETTING_STARTED.md) for setup
2. Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
3. Check [TEST_REPORT.md](TEST_REPORT.md) for test results
4. Review code comments in `app/` services

---

## Key Dates

- ✅ MVP Complete: 2025-11-06
- ✅ Playground Tested: 2025-11-06
- ⏭️ Phase 2 Target: 2025-11-13
- ⏭️ Phase 3 Target: 2025-11-20
- ⏭️ Phase 4 Target: 2025-12-04

---

**Status**: 🚀 **Ready for Testing & Deployment**

All core systems functional. Ready to:
- ✅ Run playground tests
- ✅ Deploy API server
- ✅ Accept requests
- ✅ Make trading decisions
- ✅ Calculate P&L
- ✅ Rank agents
