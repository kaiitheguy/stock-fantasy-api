"""
Local JSON storage service for MVP/demo mode.
Handles reads/writes to `data/*.json` files and provides helper methods
for user, agent, trade, and standings data.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional


class DataService:
    """Abstraction over local JSON files for demo/testing mode."""

    FILE_NAMES = {
        "agent_info": "agent_info.json",
        "agent_events": "agent_events.json",
        "user_info": "user_info.json",
        "user_events": "user_events.json",
        "weekly_pnl": "weekly_pnl.json",
    }

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.environ.get("DATA_DIR", "data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._file_paths = {
            name: self.data_dir / filename
            for name, filename in self.FILE_NAMES.items()
        }
        self._lock = Lock()
        self._ensure_files()

    def _ensure_files(self) -> None:
        for path in self._file_paths.values():
            if not path.exists():
                path.write_text("[]", encoding="utf-8")

    def _load(self, name: str) -> List[Dict[str, Any]]:
        path = self._file_paths[name]
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []

    def _save(self, name: str, data: List[Dict[str, Any]]) -> None:
        path = self._file_paths[name]
        with self._lock:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    # --------------------------- Users --------------------------- #

    def sync_agent_catalog(self, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Persist the current agent catalog to disk so it can be inspected in demo mode.
        """
        path = self._file_paths["agent_info"]
        with self._lock:
            with path.open("w", encoding="utf-8") as f:
                json.dump(agents, f, indent=2)
        return agents

    def load_agent_catalog(self) -> List[Dict[str, Any]]:
        return self._load("agent_info")

    def create_user(self, username: str, email: str) -> Dict[str, Any]:
        users = self._load("user_info")
        new_id = max((user.get("user_id", 0) for user in users), default=0) + 1
        now = datetime.utcnow().isoformat()
        user = {
            "user_id": new_id,
            "username": username,
            "email": email,
            "created_at": now,
        }
        users.append(user)
        self._save("user_info", users)
        return user

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        users = self._load("user_info")
        for user in users:
            if user.get("user_id") == user_id:
                return user
        return None

    def list_users(self) -> List[Dict[str, Any]]:
        return self._load("user_info")

    # ------------------------- User Events ----------------------- #

    def record_agent_selection(
        self,
        user_id: int,
        agent_ids: List[int],
        month_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not agent_ids or not 3 <= len(agent_ids) <= 5:
            raise ValueError("Users must pick between 3 and 5 agents")

        events = self._load("user_events")
        event_id = len(events) + 1
        event = {
            "event_id": event_id,
            "user_id": user_id,
            "action": "select",
            "agent_ids": agent_ids,
            "month_number": month_number or self._current_month_number(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        events.append(event)
        self._save("user_events", events)
        return event

    def record_agent_drop(
        self,
        user_id: int,
        agent_id: int,
        month_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        events = self._load("user_events")
        event_id = len(events) + 1
        event = {
            "event_id": event_id,
            "user_id": user_id,
            "action": "drop",
            "agent_id": agent_id,
            "month_number": month_number or self._current_month_number(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        events.append(event)
        self._save("user_events", events)
        return event

    def get_user_agents(self, user_id: int) -> List[int]:
        events = sorted(self._load("user_events"), key=lambda e: e.get("timestamp", ""))
        roster: List[int] = []
        for event in events:
            if event.get("user_id") != user_id:
                continue
            if event.get("action") == "select":
                roster = list(event.get("agent_ids", []))
            elif event.get("action") == "drop":
                agent_id = event.get("agent_id")
                roster = [aid for aid in roster if aid != agent_id]
        return roster

    # -------------------------- Trades -------------------------- #

    def record_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = [
            "agent_id",
            "week_number",
            "action",
            "stock_ticker",
            "quantity",
            "price",
            "action_reason",
        ]
        for field in required_fields:
            if field not in trade_data:
                raise ValueError(f"Missing field: {field}")

        trades = self._load("agent_events")
        event_id = len(trades) + 1
        trade = {
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "pnl_delta": 0.0,
            **trade_data,
        }
        trades.append(trade)
        self._save("agent_events", trades)
        return trade

    def get_agent_trades(self, agent_id: int) -> List[Dict[str, Any]]:
        trades = self._load("agent_events")
        return [trade for trade in trades if trade.get("agent_id") == agent_id]

    # --------------------- Standings / P&L ----------------------- #

    def compute_agent_stats(self) -> Dict[int, Dict[str, Any]]:
        trades = self._load("agent_events")
        stats: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            "agent_id": None,
            "total_pnl": 0.0,
            "trade_count": 0,
            "last_trade": None,
        })
        for trade in trades:
            agent_id = int(trade.get("agent_id"))
            entry = stats[agent_id]
            entry["agent_id"] = agent_id
            entry["total_pnl"] += float(trade.get("pnl_delta") or 0.0)
            entry["trade_count"] += 1
            entry["last_trade"] = trade
        return stats

    def get_standings(
        self,
        agent_catalog: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        stats = self.compute_agent_stats()

        # Ensure every configured agent appears even if no trades yet
        if agent_catalog:
            for agent in agent_catalog:
                agent_id = agent.get("id")
                if agent_id not in stats:
                    stats[agent_id] = {
                        "agent_id": agent_id,
                        "total_pnl": 0.0,
                        "trade_count": 0,
                        "last_trade": None,
                    }

        standings = sorted(
            stats.values(),
            key=lambda entry: entry.get("total_pnl", 0.0),
            reverse=True,
        )
        for idx, entry in enumerate(standings, start=1):
            entry["rank"] = idx
        return standings

    def get_user_pnl(self, user_id: int) -> Dict[str, Any]:
        roster = self.get_user_agents(user_id)
        stats = self.compute_agent_stats()
        agent_summaries = []
        total = 0.0
        for agent_id in roster:
            entry = stats.get(agent_id, {"total_pnl": 0.0, "trade_count": 0, "last_trade": None})
            total += entry.get("total_pnl", 0.0)
            agent_summaries.append({
                "agent_id": agent_id,
                "total_pnl": entry.get("total_pnl", 0.0),
                "trade_count": entry.get("trade_count", 0),
            })

        return {
            "user_id": user_id,
            "agents": agent_summaries,
            "total_pnl": total,
        }

    def record_weekly_snapshot(self, week_number: int, standings: List[Dict[str, Any]]) -> Dict[str, Any]:
        snapshots = self._load("weekly_pnl")
        snapshot_id = len(snapshots) + 1
        payload = {
            "snapshot_id": snapshot_id,
            "week_number": week_number,
            "standings": standings,
            "created_at": datetime.utcnow().isoformat(),
        }
        snapshots.append(payload)
        self._save("weekly_pnl", snapshots)
        return payload

    def list_snapshots(self) -> List[Dict[str, Any]]:
        return self._load("weekly_pnl")

    # -------------------------- Helpers ------------------------- #

    @staticmethod
    def _current_month_number() -> int:
        now = datetime.utcnow()
        return now.year * 100 + now.month
