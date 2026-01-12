"""
REST API for the Stock Fantasy MVP.
Provides endpoints for user onboarding, agent selection, trade logging, and standings.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from datetime import datetime

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from ..core.llm_service import LLMOrchestrator
from ..services.agent_service import AgentService
from ..services.storage_factory import get_data_service


def require_internal_key(request: Request, x_internal_key: Optional[str] = Header(default=None)) -> None:
    """Simple header-based auth for TestFlight builds."""
    expected = os.environ.get("INTERNAL_API_KEY")
    if not expected:
        return
    if request.url.path == "/api/health":
        return
    if x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


router = APIRouter(prefix="/api", tags=["fantasy"], dependencies=[Depends(require_internal_key)])

agent_service = AgentService()
data_service = get_data_service()
llm_orchestrator = LLMOrchestrator()

# Cache the 10-agent catalog for quick access and persist for observability
AGENT_CATALOG = agent_service.generate_all_agents()
data_service.sync_agent_catalog(AGENT_CATALOG)
AGENT_IDS = {agent["id"] for agent in AGENT_CATALOG}


# --------------------------- Schemas --------------------------- #

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class AgentSelectionRequest(BaseModel):
    agent_ids: List[int] = Field(..., min_items=3, max_items=5)
    month_number: Optional[int] = None


class DropAgentRequest(BaseModel):
    agent_id: int
    month_number: Optional[int] = None


class TradeRecordRequest(BaseModel):
    week_number: int
    action: str = Field(..., pattern="^(buy|sell)$")
    stock_ticker: str = Field(..., min_length=1, max_length=10)
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    action_reason: str = Field(..., min_length=3)
    pnl_delta: float = 0.0
    user_id: Optional[int] = None


class DecisionRequest(BaseModel):
    model: str
    style: str
    market_data: str
    account_state: Dict[str, Any]


class BatchDecisionRequest(BaseModel):
    decisions_config: List[Dict[str, Any]]


# --------------------------- Agent APIs --------------------------- #

@router.get("")
def api_root():
    """Lightweight root handler to confirm the API is running."""
    return {
        "service": "stock-fantasy-api",
        "status": "ok",
        "docs": "/docs",
        "endpoints": {
            "agents": "/api/agents",
            "users": "/api/users/{id}",
            "standings": "/api/standings",
            "health": "/api/health",
        },
    }


@router.get("/agents")
def list_agents(limit: int = Query(10, ge=1, le=10)):
    """List up to 10 configured agents."""
    return AGENT_CATALOG[:limit]


@router.get("/agents/{agent_id}")
def get_agent(agent_id: int):
    for agent in AGENT_CATALOG:
        if agent["id"] == agent_id:
            return agent
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")


@router.get("/agents/{agent_id}/trades")
def get_agent_trades(agent_id: int):
    trades = data_service.get_agent_trades(agent_id)
    return {"agent_id": agent_id, "trades": trades}


@router.post("/agents/{agent_id}/trades", status_code=201)
def record_agent_trade(agent_id: int, payload: TradeRecordRequest):
    if agent_id not in AGENT_IDS:
        raise HTTPException(status_code=404, detail="Agent not found")

    trade = data_service.record_trade({
        "agent_id": agent_id,
        "user_id": payload.user_id,
        "week_number": payload.week_number,
        "action": payload.action,
        "stock_ticker": payload.stock_ticker.upper(),
        "quantity": payload.quantity,
        "price": payload.price,
        "pnl_delta": payload.pnl_delta,
        "action_reason": payload.action_reason,
    })
    return trade


# --------------------------- User APIs --------------------------- #

@router.post("/users/register", status_code=201)
def register_user(payload: UserRegisterRequest):
    user = data_service.create_user(payload.username, payload.email)
    return user


@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = data_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["agents"] = data_service.get_user_agents(user_id)
    return user


@router.get("/users/{user_id}/agents")
def get_user_agents(user_id: int):
    return {"user_id": user_id, "agents": data_service.get_user_agents(user_id)}


@router.post("/users/{user_id}/select-agents", status_code=201)
def select_user_agents(user_id: int, payload: AgentSelectionRequest):
    if not data_service.get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if any(agent_id not in AGENT_IDS for agent_id in payload.agent_ids):
        raise HTTPException(status_code=400, detail="Invalid agent ID in selection")

    event = data_service.record_agent_selection(
        user_id=user_id,
        agent_ids=payload.agent_ids,
        month_number=payload.month_number,
    )
    return event


@router.post("/users/{user_id}/drop-agent", status_code=201)
def drop_user_agent(user_id: int, payload: DropAgentRequest):
    if not data_service.get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    event = data_service.record_agent_drop(
        user_id=user_id,
        agent_id=payload.agent_id,
        month_number=payload.month_number,
    )
    return event


@router.get("/users/{user_id}/pnl")
def get_user_pnl(user_id: int):
    if not data_service.get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    pnl = data_service.get_user_pnl(user_id)
    return pnl


# --------------------------- Standings --------------------------- #

@router.get("/standings")
def get_standings():
    standings = data_service.get_standings(AGENT_CATALOG)
    return {
        "standings": standings,
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.post("/standings/snapshot", status_code=201)
def save_weekly_snapshot(week_number: int = Body(..., embed=True)):
    standings = data_service.get_standings(AGENT_CATALOG)
    snapshot = data_service.record_weekly_snapshot(week_number, standings)
    return snapshot


@router.get("/standings/snapshots")
def list_snapshots():
    return data_service.list_snapshots()


# --------------------------- LLM Decisions --------------------------- #

@router.post("/decisions/run")
async def run_decision(payload: DecisionRequest):
    if not agent_service.validate_agent_config(payload.model, payload.style):
        raise HTTPException(status_code=404, detail="Unknown model/style combination")

    system_prompt = agent_service.get_style_prompt(payload.style)
    decision = await llm_orchestrator.get_decision(
        model_name=payload.model,
        system_prompt=system_prompt,
        market_data=payload.market_data,
        account_state=json.dumps(payload.account_state),
    )
    return decision


@router.post("/decisions/batch")
async def run_batch_decisions(payload: BatchDecisionRequest):
    configs = []
    for config in payload.decisions_config:
        style_prompt = agent_service.get_style_prompt(config["style"])
        configs.append({
            "agent_id": config["agent_id"],
            "model_name": config["model"],
            "system_prompt": style_prompt,
            "market_data": config["market_data"],
            "account_state": json.dumps(config["account_state"]),
        })

    decisions = await llm_orchestrator.get_decisions_parallel(configs)
    return {
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
    }


# --------------------------- Health --------------------------- #

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "agents_available": len(AGENT_CATALOG),
        "storage_mode": "local-json",
    }
