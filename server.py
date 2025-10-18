import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from pydantic import BaseModel
import yfinance as yf


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("[REQ] %s %s", request.method, request.url.path)
    return await call_next(request)


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {"ok": True, "env": bool(os.environ.get("OPENAI_API_KEY"))}


def _fallback_percent_from_change(change: Optional[float], price: Optional[float]) -> Optional[float]:
    if change is None or price is None:
        return None
    prev_close = price - change
    if prev_close in (None, 0):
        return None
    return (change / prev_close) * 100


def _normalize_probabilities(a: Any, b: Any) -> Dict[str, float]:
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 0.0
    try:
        b_val = float(b)
    except (TypeError, ValueError):
        b_val = 0.0

    if a_val < 0:
        a_val = 0.0
    if b_val < 0:
        b_val = 0.0

    total = a_val + b_val
    if total == 0:
        a_val = b_val = 50.0
    elif total != 100:
        a_val = (a_val / total) * 100
        b_val = 100 - a_val

    return {
        "buyProbability": round(a_val, 1),
        "sellProbability": round(b_val, 1),
    }


def _extract_yahoo_description(info: Dict[str, Any]) -> Optional[str]:
    for key in ("longBusinessSummary", "longBusinessDescription", "businessSummary"):
        if key in info and info[key]:
            return info[key]
    profile = info.get("summaryProfile") or {}
    if isinstance(profile, dict):
        desc = profile.get("longBusinessSummary")
        if desc:
            return desc
    return None


def fetch_yahoo_data(symbol: str) -> Dict[str, Any]:
    ticker = yf.Ticker(symbol)

    info: Dict[str, Any] = {}
    try:
        info = ticker.get_info() or {}
    except Exception as err:
        logger.warning("yfinance get_info failed for %s: %s", symbol, err)

    fast_info: Dict[str, Any] = {}
    try:
        fast_info = ticker.fast_info or {}
    except Exception as err:
        logger.warning("yfinance fast_info failed for %s: %s", symbol, err)

    price = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or fast_info.get("last_price")
    )

    change_pct = (
        info.get("regularMarketChangePercent")
        or fast_info.get("regular_market_percent_change")
    )
    if isinstance(change_pct, (int, float)) and abs(change_pct) < 1:
        # fast_info returns a ratio; convert to percentage.
        change_pct *= 100
    if change_pct is None:
        change_pct = _fallback_percent_from_change(
            info.get("regularMarketChange") or fast_info.get("regular_market_change"),
            price,
        )

    spark = []
    try:
        history = ticker.history(period="7d", interval="1d")
        if not history.empty:
            spark = [
                float(close)
                for close in history["Close"].dropna().tolist()
                if close is not None
            ]
    except Exception as err:
        logger.warning("yfinance history failed for %s: %s", symbol, err)

    yahoo_desc = _extract_yahoo_description(info)

    return {
        "price": price,
        "changePct": change_pct,
        "spark": spark,
        "yahooDesc": yahoo_desc,
    }


@app.get("/api/yahoo")
async def yahoo(symbol: str, response: Response):
    trimmed = symbol.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail={"error": "Missing symbol"})

    try:
        data = await asyncio.to_thread(fetch_yahoo_data, trimmed)
    except Exception as err:
        logger.exception("Failed to fetch stock data for %s", trimmed)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch stock data", "detail": str(err)},
        ) from err

    response.headers["Cache-Control"] = "no-store"
    return data


class RationaleRequest(BaseModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    changePct: Optional[float] = None


@app.post("/api/rationale")
async def rationale(payload: RationaleRequest) -> JSONResponse:
    if not os.environ.get("OPENAI_API_KEY"):
        return JSONResponse(
            status_code=500,
            content={"error": "OPENAI_API_KEY missing on server"},
        )

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    parts = [
        f"Ticker: {payload.symbol}" if payload.symbol else None,
        f"Company: {payload.name}" if payload.name else None,
        f"Spot price: {payload.price}"
        if isinstance(payload.price, (int, float))
        else None,
        f"Change %: {payload.changePct}"
        if isinstance(payload.changePct, (int, float))
        else None,
        "Return STRICT JSON with keys: companyDescription, buy, buyProbability, sell, sellProbability.",
        "buyProbability + sellProbability MUST equal 100.",
        "Each text ≤ 80 words. No markdown. No extra text around the JSON.",
    ]
    user_prompt = "\n".join(filter(None, parts))

    try:
        chat = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an equity analyst. Be neutral, concise, and factual.",
                },
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as err:
        logger.exception("OpenAI chat completion failed")
        return JSONResponse(
            status_code=500,
            content={"error": "AI error", "detail": str(err)},
        )

    raw = chat.choices[0].message.content if chat.choices else "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    probs = _normalize_probabilities(
        data.get("buyProbability"),
        data.get("sellProbability"),
    )

    return JSONResponse(
        {
            "companyDescription": data.get("companyDescription", ""),
            "buy": data.get("buy", ""),
            "buyProbability": probs["buyProbability"],
            "sell": data.get("sell", ""),
            "sellProbability": probs["sellProbability"],
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "3000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
