from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class RationaleRequest(BaseModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    changePct: Optional[float] = None


# ==================== AI Trading Fantasy Models ====================

class TradingStyle(BaseModel):
    """Trading style configuration"""
    name: str
    description: str
    system_prompt: str


class Agent(BaseModel):
    """LLM Agent (Model x Style combination)"""
    id: int
    model_name: str
    style_name: str
    system_prompt: str
    cost_tier: str  # 'cheap', 'medium', 'expensive'


class AgentCreate(BaseModel):
    """Create new agent"""
    model_name: str
    style_name: str
    system_prompt: str
    cost_tier: str = "medium"


class Trade(BaseModel):
    """Trade executed by an agent"""
    id: int
    agent_id: int
    league_id: int
    decision_timestamp: datetime
    action: str  # 'buy', 'sell', 'hold'
    ticker: Optional[str] = None
    quantity: Optional[int] = None
    entry_price: Optional[float] = None
    llm_reasoning: str
    executed: bool = True


class TradeCreate(BaseModel):
    """Create new trade"""
    agent_id: int
    league_id: int
    action: str
    ticker: Optional[str] = None
    quantity: Optional[int] = None
    entry_price: Optional[float] = None
    llm_reasoning: str


class LeagueAgent(BaseModel):
    """Agent state within a league"""
    league_id: int
    agent_id: int
    agent_model: str
    agent_style: str
    starting_capital: float
    current_cash: float
    positions: Dict[str, int]  # {ticker: quantity}
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float  # realized + unrealized


class League(BaseModel):
    """Weekly league"""
    id: int
    week_number: int
    start_date: str
    end_date: str
    status: str
    created_at: datetime


class LeagueCreate(BaseModel):
    """Create new league"""
    week_number: int
    start_date: str
    end_date: str


class LeagueStandings(BaseModel):
    """League standings with agent rankings"""
    league_id: int
    week_number: int
    agents: List[LeagueAgent]


class MarketData(BaseModel):
    """Market data point"""
    ticker: str
    timestamp: datetime
    price: float
    volume: int


class LLMDecision(BaseModel):
    """LLM's trading decision"""
    action: str  # 'buy', 'sell', 'hold'
    ticker: Optional[str] = None
    quantity: Optional[int] = None
    confidence: float  # 0-1
    reasoning: str
    raw_response: Optional[str] = None
