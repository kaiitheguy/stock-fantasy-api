# Stock Fantasy API (Python)

Simple FastAPI service that wraps Yahoo Finance data and an OpenAI rationale generator.

## Endpoints
- `GET /api/health` – Health check with API key status.
- `GET /api/yahoo?symbol=TSLA` – Aggregated quote, change %, sparkline, and company description from Yahoo.
- `POST /api/rationale` – Generates buy/sell rationale JSON for a symbol using OpenAI.

## Requirements
- Python 3.10+
- OpenAI API key (for rationale endpoint)

Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENAI_API_KEY=your-key
PORT=3000  # optional
```

## Local Development
Run the server:
```bash
uvicorn server:app --host 0.0.0.0 --port 3000 --reload
```

## Deployment
- Render/railway/fly: use build command `pip install -r requirements.txt`.
- Start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`.
- Set environment variables inside the provider dashboard (never commit secrets).
