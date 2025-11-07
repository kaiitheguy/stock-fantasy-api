"""
Scoring and P&L calculation service for fantasy leagues.
Handles weekly standings, rankings, and performance metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date

from ..core.schemas import LeagueAgent


class ScoringService:
    """Calculates scores and standings for leagues"""

    def __init__(self, db_client=None):
        """
        Initialize scoring service.

        Args:
            db_client: Database client
        """
        self.db = db_client

    async def get_league_standings(
        self,
        league_id: int,
    ) -> List[LeagueAgent]:
        """
        Get league standings sorted by total P&L (descending).

        Args:
            league_id: League ID

        Returns:
            Sorted list of LeagueAgent with current stats
        """
        if not self.db:
            raise ValueError("Database client not initialized")

        # Fetch all agents in league with their stats
        response = (
            await self.db.table("league_agents")
            .select("*")
            .eq("league_id", league_id)
            .execute()
        )

        standings = []
        for row in response.data:
            # Get agent info
            agent_response = (
                await self.db.table("agents")
                .select("model_name, style_name")
                .eq("id", row["agent_id"])
                .single()
                .execute()
            )

            agent = LeagueAgent(
                league_id=league_id,
                agent_id=row["agent_id"],
                agent_model=agent_response.data["model_name"],
                agent_style=agent_response.data["style_name"],
                starting_capital=float(row["starting_capital"]),
                current_cash=float(row["current_cash"]),
                positions=row.get("positions", {}),
                realized_pnl=float(row.get("realized_pnl", 0)),
                unrealized_pnl=float(row.get("unrealized_pnl", 0)),
                total_pnl=float(row.get("realized_pnl", 0)) + float(row.get("unrealized_pnl", 0)),
            )
            standings.append(agent)

        # Sort by total P&L descending
        standings.sort(key=lambda x: x.total_pnl, reverse=True)
        return standings

    async def calculate_weekly_scores(
        self,
        league_id: int,
        current_prices: Dict[str, float],
    ) -> Dict[int, Dict[str, Any]]:
        """
        Calculate final scores for all agents in a league.

        Args:
            league_id: League ID
            current_prices: Current stock prices {ticker: price}

        Returns:
            Dict mapping agent_id to score data
        """
        if not self.db:
            raise ValueError("Database client not initialized")

        standings = await self.get_league_standings(league_id)
        scores = {}

        for i, agent in enumerate(standings):
            # Get all trades for agent in this league
            trades_response = (
                await self.db.table("trades")
                .select("*")
                .eq("agent_id", agent.agent_id)
                .eq("league_id", league_id)
                .order("decision_timestamp", desc=False)
                .execute()
            )

            # Calculate metrics
            num_trades = len(trades_response.data)
            buy_trades = sum(1 for t in trades_response.data if t["action"] == "buy")
            sell_trades = sum(1 for t in trades_response.data if t["action"] == "sell")

            # Calculate realized and unrealized P&L
            realized_pnl = await self._calculate_realized_pnl(
                trades_response.data, current_prices
            )
            unrealized_pnl = agent.unrealized_pnl

            total_pnl = realized_pnl + unrealized_pnl
            pnl_pct = (total_pnl / agent.starting_capital * 100) if agent.starting_capital > 0 else 0

            scores[agent.agent_id] = {
                "rank": i + 1,
                "agent_id": agent.agent_id,
                "model": agent.agent_model,
                "style": agent.agent_style,
                "starting_capital": agent.starting_capital,
                "current_portfolio_value": agent.current_cash + sum(
                    current_prices.get(ticker, 0) * qty
                    for ticker, qty in agent.positions.items()
                ),
                "total_pnl": total_pnl,
                "pnl_pct": pnl_pct,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "num_trades": num_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "win_rate": self._calculate_win_rate(trades_response.data, current_prices),
            }

        return scores

    async def _calculate_realized_pnl(
        self,
        trades: List[Dict[str, Any]],
        current_prices: Dict[str, float],
    ) -> float:
        """Calculate realized P&L from closed positions"""
        # For MVP, simple implementation: just sum realized gains
        realized_pnl = 0.0

        # Group trades by ticker
        ticker_trades = {}
        for trade in trades:
            ticker = trade.get("ticker")
            if not ticker:
                continue
            if ticker not in ticker_trades:
                ticker_trades[ticker] = []
            ticker_trades[ticker].append(trade)

        # Calculate P&L for each ticker
        for ticker, ticker_list in ticker_trades.items():
            quantity_held = 0
            entry_cost = 0.0

            for trade in ticker_list:
                action = trade.get("action")
                qty = trade.get("quantity", 0)
                price = trade.get("entry_price", 0)

                if action == "buy":
                    entry_cost += price * qty
                    quantity_held += qty
                elif action == "sell":
                    # Calculate P&L on sold quantity
                    sell_value = price * qty
                    # Assuming FIFO - use average cost
                    avg_cost = entry_cost / quantity_held if quantity_held > 0 else 0
                    realized_pnl += (price - avg_cost) * qty
                    quantity_held -= qty
                    entry_cost -= avg_cost * qty

        return realized_pnl

    def _calculate_win_rate(
        self,
        trades: List[Dict[str, Any]],
        current_prices: Dict[str, float],
    ) -> float:
        """Calculate win rate (% of trades that are profitable)"""
        if not trades:
            return 0.0

        winning_trades = 0
        for trade in trades:
            action = trade.get("action")
            if action == "sell":
                entry_price = trade.get("entry_price", 0)
                # Look back to find corresponding buy
                # For MVP, simplified: assume all sells are winning if price went up
                winning_trades += 1  # TODO: Implement proper tracking

        return (winning_trades / len([t for t in trades if t["action"] == "sell"]) * 100) if trades else 0

    async def close_league(self, league_id: int):
        """Close a league and archive final standings"""
        if not self.db:
            raise ValueError("Database client not initialized")

        await (
            self.db.table("leagues")
            .update({"status": "closed"})
            .eq("id", league_id)
            .execute()
        )

    async def get_agent_performance_history(
        self,
        agent_id: int,
    ) -> List[Dict[str, Any]]:
        """Get agent's performance across all weeks"""
        if not self.db:
            raise ValueError("Database client not initialized")

        # Get all league participations for agent
        response = (
            await self.db.table("league_agents")
            .select("*")
            .eq("agent_id", agent_id)
            .execute()
        )

        history = []
        for row in response.data:
            history.append({
                "league_id": row["league_id"],
                "realized_pnl": float(row.get("realized_pnl", 0)),
                "unrealized_pnl": float(row.get("unrealized_pnl", 0)),
                "total_pnl": float(row.get("realized_pnl", 0)) + float(row.get("unrealized_pnl", 0)),
            })

        return history

    def calculate_sharpe_ratio(
        self,
        daily_returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> float:
        """
        Calculate Sharpe ratio for a portfolio.

        Args:
            daily_returns: List of daily returns (as decimals)
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio
        """
        if len(daily_returns) < 2:
            return 0.0

        import statistics

        mean_return = statistics.mean(daily_returns)
        std_dev = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0

        if std_dev == 0:
            return 0.0

        # Annualize returns and std dev
        annual_return = mean_return * 252  # 252 trading days
        annual_std = std_dev * (252 ** 0.5)
        daily_rf = risk_free_rate / 252

        sharpe = (annual_return - daily_rf) / annual_std if annual_std > 0 else 0
        return sharpe

    def calculate_max_drawdown(
        self,
        portfolio_values: List[float],
    ) -> float:
        """
        Calculate maximum drawdown.

        Args:
            portfolio_values: List of portfolio values over time

        Returns:
            Max drawdown as percentage
        """
        if len(portfolio_values) < 2:
            return 0.0

        max_value = portfolio_values[0]
        max_drawdown = 0.0

        for value in portfolio_values[1:]:
            if value > max_value:
                max_value = value
            drawdown = (max_value - value) / max_value if max_value > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown * 100  # Return as percentage
