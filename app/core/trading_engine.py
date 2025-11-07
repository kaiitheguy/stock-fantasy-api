"""
Paper trading engine for simulating trades.
Handles buy/sell execution, position tracking, and P&L calculation.
"""

import json
from typing import Dict, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime

from .schemas import Trade, TradeCreate, LeagueAgent, LLMDecision


class TradingEngine:
    """Simulates paper trading execution and position management"""

    # S&P 500 constraints
    MAX_POSITIONS = 5
    MAX_POSITION_SIZE_PCT = 0.30  # 30% of portfolio
    MIN_POSITION_SIZE = 100  # $100 minimum

    def __init__(self, db_client=None):
        """
        Initialize trading engine.

        Args:
            db_client: Database client for persistence
        """
        self.db = db_client

    async def execute_decision(
        self,
        decision: LLMDecision,
        agent_id: int,
        league_id: int,
        current_price: float,
        account_state: Dict[str, Any],
    ) -> Tuple[bool, Trade, Optional[str]]:
        """
        Execute a trading decision.

        Args:
            decision: LLMDecision from the agent
            agent_id: Agent ID
            league_id: League ID
            current_price: Current stock price
            account_state: Current account state with positions and cash

        Returns:
            (success: bool, trade: Trade, error: Optional[str])
        """
        action = decision.action.lower()

        # Validate decision
        if action == "hold":
            return True, None, None

        if action not in ["buy", "sell"]:
            return False, None, f"Invalid action: {action}"

        if not decision.ticker:
            return False, None, "No ticker provided"

        # Execute buy or sell
        if action == "buy":
            success, trade, error = await self._execute_buy(
                decision, agent_id, league_id, current_price, account_state
            )
        else:  # sell
            success, trade, error = await self._execute_sell(
                decision, agent_id, league_id, current_price, account_state
            )

        return success, trade, error

    async def _execute_buy(
        self,
        decision: LLMDecision,
        agent_id: int,
        league_id: int,
        current_price: float,
        account_state: Dict[str, Any],
    ) -> Tuple[bool, Optional[Trade], Optional[str]]:
        """Execute a buy order"""
        ticker = decision.ticker.upper()
        quantity = decision.quantity or 1

        if quantity <= 0:
            return False, None, "Quantity must be positive"

        # Calculate order value
        order_value = current_price * quantity

        # Check cash availability
        current_cash = float(account_state.get("current_cash", 0))
        if order_value > current_cash:
            return False, None, f"Insufficient cash: {order_value} > {current_cash}"

        # Check position limits
        positions = account_state.get("positions", {})
        starting_capital = float(account_state.get("starting_capital", 10000))

        # Max position size check
        max_position_value = starting_capital * self.MAX_POSITION_SIZE_PCT
        if order_value > max_position_value:
            return False, None, f"Position too large: {order_value} > {max_position_value}"

        # Max concurrent positions check
        if len(positions) >= self.MAX_POSITIONS and ticker not in positions:
            return False, None, f"Max {self.MAX_POSITIONS} positions reached"

        # Execute the buy
        trade = Trade(
            id=None,  # Will be assigned by DB
            agent_id=agent_id,
            league_id=league_id,
            decision_timestamp=datetime.utcnow(),
            action="buy",
            ticker=ticker,
            quantity=quantity,
            entry_price=current_price,
            llm_reasoning=decision.reasoning,
            executed=True,
        )

        # Update account state
        new_positions = positions.copy()
        new_positions[ticker] = new_positions.get(ticker, 0) + quantity
        new_cash = current_cash - order_value

        if self.db:
            # Persist to database
            await self._persist_trade(trade)
            await self._update_league_agent_state(
                agent_id, league_id, new_cash, new_positions
            )

        return True, trade, None

    async def _execute_sell(
        self,
        decision: LLMDecision,
        agent_id: int,
        league_id: int,
        current_price: float,
        account_state: Dict[str, Any],
    ) -> Tuple[bool, Optional[Trade], Optional[str]]:
        """Execute a sell order"""
        ticker = decision.ticker.upper()
        quantity = decision.quantity or 1

        if quantity <= 0:
            return False, None, "Quantity must be positive"

        # Check position exists
        positions = account_state.get("positions", {})
        if ticker not in positions or positions[ticker] < quantity:
            return False, None, f"Insufficient {ticker} position: {positions.get(ticker, 0)} < {quantity}"

        # Execute the sell
        sell_proceeds = current_price * quantity
        trade = Trade(
            id=None,  # Will be assigned by DB
            agent_id=agent_id,
            league_id=league_id,
            decision_timestamp=datetime.utcnow(),
            action="sell",
            ticker=ticker,
            quantity=quantity,
            entry_price=current_price,
            llm_reasoning=decision.reasoning,
            executed=True,
        )

        # Update account state
        new_positions = positions.copy()
        new_positions[ticker] -= quantity
        if new_positions[ticker] == 0:
            del new_positions[ticker]

        current_cash = float(account_state.get("current_cash", 0))
        new_cash = current_cash + sell_proceeds

        if self.db:
            # Persist to database
            await self._persist_trade(trade)
            await self._update_league_agent_state(
                agent_id, league_id, new_cash, new_positions
            )

        return True, trade, None

    async def _persist_trade(self, trade: Trade):
        """Persist trade to database"""
        trade_dict = trade.dict()
        trade_dict.pop("id", None)  # Remove ID for insert
        await self.db.table("trades").insert(trade_dict).execute()

    async def _update_league_agent_state(
        self,
        agent_id: int,
        league_id: int,
        new_cash: float,
        new_positions: Dict[str, int],
    ):
        """Update league agent account state"""
        await (
            self.db.table("league_agents")
            .update({
                "current_cash": new_cash,
                "positions": new_positions,
            })
            .eq("agent_id", agent_id)
            .eq("league_id", league_id)
            .execute()
        )

    def calculate_unrealized_pnl(
        self,
        positions: Dict[str, int],
        current_prices: Dict[str, float],
        entry_prices: Dict[str, float],
    ) -> float:
        """
        Calculate unrealized P&L for open positions.

        Args:
            positions: {ticker: quantity}
            current_prices: {ticker: current_price}
            entry_prices: {ticker: avg_entry_price}

        Returns:
            Unrealized P&L amount
        """
        pnl = 0.0
        for ticker, quantity in positions.items():
            current_price = current_prices.get(ticker, 0)
            entry_price = entry_prices.get(ticker, 0)
            if entry_price > 0:
                pnl += (current_price - entry_price) * quantity
        return pnl

    def calculate_total_portfolio_value(
        self,
        current_cash: float,
        positions: Dict[str, int],
        current_prices: Dict[str, float],
    ) -> float:
        """
        Calculate total portfolio value.

        Args:
            current_cash: Available cash
            positions: {ticker: quantity}
            current_prices: {ticker: current_price}

        Returns:
            Total portfolio value
        """
        position_value = sum(
            current_prices.get(ticker, 0) * quantity
            for ticker, quantity in positions.items()
        )
        return current_cash + position_value

    def get_position_stats(
        self,
        positions: Dict[str, int],
        current_prices: Dict[str, float],
        portfolio_value: float,
    ) -> Dict[str, Any]:
        """
        Get portfolio statistics.

        Args:
            positions: {ticker: quantity}
            current_prices: {ticker: current_price}
            portfolio_value: Total portfolio value

        Returns:
            Dict with position stats
        """
        stats = {
            "num_positions": len(positions),
            "position_pct_allocation": {},
        }

        for ticker, quantity in positions.items():
            price = current_prices.get(ticker, 0)
            position_value = price * quantity
            pct = (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
            stats["position_pct_allocation"][ticker] = pct

        return stats
