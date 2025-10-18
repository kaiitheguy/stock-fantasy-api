import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yfinance as yf
from openai import OpenAI

from .schemas import RationaleRequest


logger = logging.getLogger(__name__)


@dataclass
class EnvironmentMissing(Exception):
    detail: Dict[str, Any]


@dataclass
class OpenAIError(Exception):
    detail: Dict[str, Any]


async def fetch_yahoo_data(symbol: str) -> Dict[str, Any]:
    return await asyncio.to_thread(_fetch_yahoo_data_sync, symbol)


async def generate_rationale(payload: RationaleRequest) -> Dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentMissing({"error": "OPENAI_API_KEY missing on server"})

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    segments = [
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
    user_prompt = "\n".join(filter(None, segments))

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
        raise OpenAIError({"error": "AI error", "detail": str(err)}) from err

    raw = chat.choices[0].message.content if chat.choices else "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    probs = _normalize_probabilities(
        data.get("buyProbability"),
        data.get("sellProbability"),
    )

    return {
        "companyDescription": data.get("companyDescription", ""),
        "buy": data.get("buy", ""),
        "buyProbability": probs["buyProbability"],
        "sell": data.get("sell", ""),
        "sellProbability": probs["sellProbability"],
    }


def _fetch_yahoo_data_sync(symbol: str) -> Dict[str, Any]:
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


def _fallback_percent_from_change(
    change: Optional[float], price: Optional[float]
) -> Optional[float]:
    if change is None or price is None:
        return None
    prev_close = price - change
    if not prev_close:
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
        value = info.get(key)
        if value:
            return value
    profile = info.get("summaryProfile") or {}
    if isinstance(profile, dict):
        desc = profile.get("longBusinessSummary")
        if desc:
            return desc
    return None
