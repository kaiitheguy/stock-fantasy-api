"""
Supabase-backed storage service (skeleton).

Intended to mirror DataService signatures so the API layer stays unchanged.
Fill in the methods to read/write Supabase tables defined in app/db_schema.sql.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# from supabase import create_client, Client  # uncomment when wiring supabase


class SupabaseDataService:
    """Placeholder Supabase implementation; methods need to be completed."""

    def __init__(self, client=None):
        """
        Args:
            client: optional injected Supabase client (create_client(...))
        """
        # self.db: Client = client or create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        self.db = client

    # --------------------------- Agents --------------------------- #

    def sync_agent_catalog(self, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Upsert the agent catalog into agent_info.
        TODO: implement Supabase upsert.
        """
        raise NotImplementedError("SupabaseDataService.sync_agent_catalog not implemented yet")

    def load_agent_catalog(self) -> List[Dict[str, Any]]:
        """Fetch agent_info table."""
        raise NotImplementedError("SupabaseDataService.load_agent_catalog not implemented yet")

    # --------------------------- Users --------------------------- #

    def create_user(self, username: str, email: str) -> Dict[str, Any]:
        raise NotImplementedError("SupabaseDataService.create_user not implemented yet")

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("SupabaseDataService.get_user not implemented yet")

    def list_users(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("SupabaseDataService.list_users not implemented yet")

    # ------------------------- User Events ----------------------- #

    def record_agent_selection(
        self,
        user_id: int,
        agent_ids: List[int],
        month_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("SupabaseDataService.record_agent_selection not implemented yet")

    def record_agent_drop(
        self,
        user_id: int,
        agent_id: int,
        month_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("SupabaseDataService.record_agent_drop not implemented yet")

    def get_user_agents(self, user_id: int) -> List[int]:
        raise NotImplementedError("SupabaseDataService.get_user_agents not implemented yet")

    # -------------------------- Trades -------------------------- #

    def record_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("SupabaseDataService.record_trade not implemented yet")

    def get_agent_trades(self, agent_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError("SupabaseDataService.get_agent_trades not implemented yet")

    # --------------------- Standings / P&L ----------------------- #

    def compute_agent_stats(self) -> Dict[int, Dict[str, Any]]:
        raise NotImplementedError("SupabaseDataService.compute_agent_stats not implemented yet")

    def get_standings(self, agent_catalog: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("SupabaseDataService.get_standings not implemented yet")

    def get_user_pnl(self, user_id: int) -> Dict[str, Any]:
        raise NotImplementedError("SupabaseDataService.get_user_pnl not implemented yet")

    def record_weekly_snapshot(self, week_number: int, standings: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError("SupabaseDataService.record_weekly_snapshot not implemented yet")

    def list_snapshots(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("SupabaseDataService.list_snapshots not implemented yet")
