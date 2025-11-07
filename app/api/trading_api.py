"""
API routes for AI Trading Fantasy features.
Endpoints for agents, leagues, trades, and standings.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from ..core.schemas import (
    Agent,
    AgentCreate,
    League,
    LeagueCreate,
    LeagueStandings,
    LeagueAgent,
    Trade,
)
from ..services.agent_service import AgentService
from ..core.llm_service import LLMOrchestrator
from ..core.trading_engine import TradingEngine
from ..services.scoring_service import ScoringService


router = APIRouter(prefix="/api/trading", tags=["trading"])

# Initialize services (ideally from DI container)
agent_service = AgentService(db_client=None)
llm_orchestrator = LLMOrchestrator()
trading_engine = TradingEngine(db_client=None)
scoring_service = ScoringService(db_client=None)


# ==================== AGENT ENDPOINTS ====================

@router.get("/agents", response_model=List[Agent])
async def list_all_agents(limit: int = Query(100, ge=1, le=500)):
    """
    List all available agents (Model x Style combinations).

    Returns list of all agents that can be drafted into leagues.
    """
    try:
        agents_data = agent_service.generate_all_agents()
        return JSONResponse(
            status_code=200,
            content=[
                {
                    "model_name": a["model_name"],
                    "style_name": a["style_name"],
                    "cost_tier": a["cost_tier"],
                    "description": a.get("description", ""),
                }
                for a in agents_data[:limit]
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/count")
async def count_agents():
    """Get total number of available agents"""
    try:
        agents = agent_service.generate_all_agents()
        return {"total_agents": len(agents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{model}/{style}")
async def get_agent_by_model_style(model: str, style: str):
    """Get specific agent by model and style"""
    try:
        if not agent_service.validate_agent_config(model, style):
            raise HTTPException(status_code=404, detail=f"Agent {model}#{style} not found")

        model_config = agent_service.get_model_config(model)
        style_prompt = agent_service.get_style_prompt(style)

        return {
            "model": model,
            "style": style,
            "cost_tier": model_config["cost_tier"],
            "system_prompt": style_prompt,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LEAGUE ENDPOINTS ====================

@router.post("/leagues", response_model=League)
async def create_league(payload: LeagueCreate):
    """
    Create a new weekly league.

    Returns the created league.
    """
    try:
        # Validate dates
        start = datetime.strptime(payload.start_date, "%Y-%m-%d")
        end = datetime.strptime(payload.end_date, "%Y-%m-%d")

        if end <= start:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        # In MVP, just return mock response
        return JSONResponse(
            status_code=201,
            content={
                "id": 1,
                "week_number": payload.week_number,
                "start_date": payload.start_date,
                "end_date": payload.end_date,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues/{league_id}")
async def get_league(league_id: int):
    """Get league details"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "id": league_id,
                "week_number": 1,
                "status": "active",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leagues/{league_id}/agents/{agent_id}")
async def add_agent_to_league(league_id: int, agent_id: int):
    """Add an agent to a league (draft)"""
    try:
        # Validate agent exists
        agents = agent_service.generate_all_agents()
        if agent_id > len(agents):
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # In MVP, just return success
        return JSONResponse(
            status_code=201,
            content={
                "league_id": league_id,
                "agent_id": agent_id,
                "starting_capital": 10000.0,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STANDINGS ENDPOINTS ====================

@router.get("/leagues/{league_id}/standings", response_model=LeagueStandings)
async def get_league_standings(league_id: int):
    """
    Get current league standings.

    Returns agents sorted by total P&L (descending).
    """
    try:
        # Mock response for MVP
        return JSONResponse(
            status_code=200,
            content={
                "league_id": league_id,
                "week_number": 1,
                "agents": [
                    {
                        "league_id": league_id,
                        "agent_id": 1,
                        "agent_model": "gpt-4-mini",
                        "agent_style": "conservative",
                        "starting_capital": 10000.0,
                        "current_cash": 9500.0,
                        "positions": {"AAPL": 10},
                        "realized_pnl": 100.0,
                        "unrealized_pnl": 500.0,
                        "total_pnl": 600.0,
                    },
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues/{league_id}/scores")
async def get_league_scores(league_id: int):
    """Get detailed scores for all agents in league"""
    try:
        # Mock response for MVP
        return JSONResponse(
            status_code=200,
            content={
                "league_id": league_id,
                "scores": [
                    {
                        "rank": 1,
                        "agent_id": 1,
                        "model": "gpt-4-mini",
                        "style": "conservative",
                        "total_pnl": 600.0,
                        "pnl_pct": 6.0,
                        "realized_pnl": 100.0,
                        "unrealized_pnl": 500.0,
                        "num_trades": 5,
                        "buy_trades": 3,
                        "sell_trades": 2,
                        "win_rate": 80.0,
                    },
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TRADE ENDPOINTS ====================

@router.get("/leagues/{league_id}/trades")
async def get_league_trades(league_id: int, agent_id: int = Query(None)):
    """
    Get all trades in a league, optionally filtered by agent.

    Returns trades with reasoning.
    """
    try:
        # Mock response for MVP
        return JSONResponse(
            status_code=200,
            content={
                "league_id": league_id,
                "trades": [
                    {
                        "id": 1,
                        "agent_id": 1,
                        "league_id": league_id,
                        "decision_timestamp": "2024-01-01T10:00:00",
                        "action": "buy",
                        "ticker": "AAPL",
                        "quantity": 10,
                        "entry_price": 150.0,
                        "llm_reasoning": "Strong momentum signal detected",
                        "executed": True,
                    },
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DECISION/EXECUTION ENDPOINTS ====================

@router.post("/decisions/get")
async def get_trading_decision(
    model: str = Body(...),
    style: str = Body(...),
    market_data: str = Body(...),
    account_state: Dict[str, Any] = Body(...),
):
    """
    Get a trading decision from an LLM agent.

    For testing/demo purposes.
    """
    try:
        if not agent_service.validate_agent_config(model, style):
            raise HTTPException(status_code=404, detail=f"Agent {model}#{style} not found")

        system_prompt = agent_service.get_style_prompt(style)

        decision = await llm_orchestrator.get_decision(
            model_name=model,
            system_prompt=system_prompt,
            market_data=market_data,
            account_state=json.dumps(account_state),
        )

        return JSONResponse(
            status_code=200,
            content={
                "action": decision.action,
                "ticker": decision.ticker,
                "quantity": decision.quantity,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/batch")
async def get_batch_decisions(
    decisions_config: List[Dict[str, Any]] = Body(...),
):
    """
    Get trading decisions from multiple agents in parallel.

    Useful for weekly decision cycles.
    """
    try:
        # Prepare configuration with system prompts
        configs = []
        for config in decisions_config:
            style_prompt = agent_service.get_style_prompt(config["style"])
            configs.append({
                "agent_id": config["agent_id"],
                "model_name": config["model"],
                "system_prompt": style_prompt,
                "market_data": config["market_data"],
                "account_state": json.dumps(config["account_state"]),
            })

        # Get decisions in parallel
        decisions = await llm_orchestrator.get_decisions_parallel(configs)

        return JSONResponse(
            status_code=200,
            content={
                "decisions": {
                    str(agent_id): {
                        "action": decision.action,
                        "ticker": decision.ticker,
                        "quantity": decision.quantity,
                        "confidence": decision.confidence,
                        "reasoning": decision.reasoning,
                    }
                    for agent_id, decision in decisions.items()
                }
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Health check for trading service"""
    return {
        "status": "ok",
        "service": "ai-trading-fantasy",
        "agents_available": len(agent_service.generate_all_agents()),
    }
