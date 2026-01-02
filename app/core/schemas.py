from typing import Optional

from pydantic import BaseModel


class LLMDecision(BaseModel):
    """LLM's trading decision in JSON form."""

    action: str  # 'buy', 'sell', 'hold'
    ticker: Optional[str] = None
    quantity: Optional[int] = None
    confidence: float  # 0-1
    reasoning: str
    raw_response: Optional[str] = None
