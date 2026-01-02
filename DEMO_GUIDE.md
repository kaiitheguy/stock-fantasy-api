# Stock Fantasy MVP Demo Guide

This walkthrough shows how to stand up the FastAPI backend, run the TestFlight-style demo, and drive the new notebook playground.

## 1. Environment setup

```bash
cd stock-fantasy-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp app/.env.example app/.env  # fill in API keys + INTERNAL_API_KEY
```

Optional quick checks before the demo:

- `source app/.env && python notebooks/test_llm_connections.py --providers openai deepseek`
- `ls data/*.json` to confirm the four JSON files exist (they are created automatically if missing)

## 2. Run the API locally

```bash
source .venv/bin/activate
set -a && source app/.env && set +a
uvicorn server:app --host 0.0.0.0 --port 3000 --reload
```

Key points:

- Endpoints live under `http://localhost:3000/api`
- The CLI/notebook sends `X-Internal-Key` automatically if `INTERNAL_API_KEY` is set
- All state is written to `data/*.json`, so you can wipe the folder between demos

## 3. Playground notebook workflow

1. Launch Jupyter or VS Code notebooks and open `notebooks/mvp_demo_playground.ipynb`.
2. Ensure the FastAPI server is running (step 2) before executing any cells.
3. Run the notebook top to bottom:
   - Registers two demo users (Alice/Bob)
   - Fetches the 10 canonical agents (5 styles × ChatGPT/DeepSeek)
   - Records their monthly selections (3–5 agents each)
   - Simulates two weekly cycles by posting trades via `/agents/{id}/trades`
   - Pulls `/standings`, `/users/{id}/pnl`, and saves a `/standings/snapshot`
4. Inspect `data/agent_events.json` and `data/user_events.json` to show internal state if needed.

You can tweak the trade templates in the notebook to showcase alternative outcomes or reset by truncating the JSON files.

## 4. Running without the notebook

If you prefer curl/httpx scripts:

1. Register: `POST /api/users/register`
2. Select agents: `POST /api/users/{id}/select-agents`
3. Record trades: `POST /api/agents/{agent_id}/trades`
4. View standings: `GET /api/standings`
5. User portfolio: `GET /api/users/{id}/pnl`

All payloads mirror the README examples and the notebook source, so you can copy/paste from there for manual testing.

---

Need a clean slate? Stop the server and delete the JSON files in `data/` (they will be recreated on the next run), then rerun the notebook. That gives you a deterministic two-week simulation every time.***
