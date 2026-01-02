"""
Quick CLI to verify OpenAI / DeepSeek credentials.

Usage:
    uv run python notebooks/test_llm_connections.py --providers openai deepseek

Requires OPENAI_API_KEY / DEEPSEEK_API_KEY to be set (e.g., via app/.env).
"""

import argparse
import asyncio
from typing import List

from app.core.llm_service import OpenAIProvider, DeepSeekProvider

TEST_SYSTEM_PROMPT = (
    "You are a compliance-safe trading bot. "
    "Always respond with compact JSON."
)
TEST_MARKET_DATA = "SPY 520.15 (+0.4%), AAPL 212.40 (+0.9%), NVDA 125.88 (-0.8%)"
TEST_ACCOUNT_STATE = "Cash: $10,000, Positions: {}"


async def _run_single(provider_name: str) -> None:
    """Call the provider once and print a short status line."""
    if provider_name == "openai":
        provider = OpenAIProvider()
        model_name = "gpt-4o-mini"  # cheaper than full GPT-4
    elif provider_name == "deepseek":
        provider = DeepSeekProvider()
        model_name = "deepseek-chat"
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")

    print(f"→ Testing {provider_name} ({model_name}) … ", end="", flush=True)
    try:
        decision = await provider.get_trading_decision(
            system_prompt=TEST_SYSTEM_PROMPT,
            market_data=TEST_MARKET_DATA,
            account_state=TEST_ACCOUNT_STATE,
            model=model_name,
        )
    except Exception as exc:  # pragma: no cover - manual CLI
        print("FAILED")
        print(f"   Reason: {exc}")
        return

    action = decision.action.upper()
    ticker = decision.ticker or "-"
    confidence = f"{decision.confidence:.2f}"
    print("OK")
    print(f"   Decision: action={action}, ticker={ticker}, confidence={confidence}")


async def main(providers: List[str]) -> None:
    for provider in providers:
        await _run_single(provider)


if __name__ == "__main__":  # pragma: no cover - manual CLI
    parser = argparse.ArgumentParser(description="Test LLM provider connectivity")
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["openai", "deepseek"],
        default=["openai", "deepseek"],
        help="Which providers to hit",
    )
    args = parser.parse_args()
    asyncio.run(main(args.providers))
