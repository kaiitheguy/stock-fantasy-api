"""
Market data service for fetching real-time stock data from Yahoo Finance.
Provides prices, technical indicators, and caching.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataCache:
    """Simple in-memory cache for market data with TTL"""

    def __init__(self, ttl_seconds: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.timestamps: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value if not expired"""
        if key not in self.cache:
            return None

        age = (datetime.utcnow() - self.timestamps[key]).total_seconds()
        if age > self.ttl_seconds:
            del self.cache[key]
            del self.timestamps[key]
            return None

        return self.cache[key]

    def set(self, key: str, value: Dict[str, Any]):
        """Set cache value"""
        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow()

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()


class MarketDataService:
    """Fetches and processes real-time market data"""

    # S&P 500 symbols (subset for MVP)
    SP500_SYMBOLS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "BRK.B", "JNJ", "V",
        "WMT", "PG", "MA", "HD", "DIS",
        "PYPL", "NFLX", "INTC", "AMD", "CRM",
        "ADBE", "CSCO", "AVGO", "COST", "ABT",
    ]

    def __init__(self, cache_ttl_seconds: int = 60):
        """
        Initialize market data service.

        Args:
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.cache = MarketDataCache(ttl_seconds=cache_ttl_seconds)
        self.logger = logging.getLogger(__name__)

    async def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price for a ticker.

        Args:
            ticker: Stock symbol (e.g., 'AAPL')

        Returns:
            Current price or None if unavailable
        """
        data = await self.get_ticker_data(ticker)
        return data.get("price") if data else None

    async def get_ticker_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive ticker data including price and indicators.

        Args:
            ticker: Stock symbol

        Returns:
            Dict with price, change%, RSI, MACD, EMA, etc.
        """
        # Check cache
        cached = self.cache.get(ticker)
        if cached:
            return cached

        # Fetch fresh data
        data = await asyncio.to_thread(self._fetch_ticker_sync, ticker)
        if data:
            self.cache.set(ticker, data)
        return data

    async def get_multiple_tickers(
        self,
        tickers: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get data for multiple tickers in parallel.

        Args:
            tickers: List of stock symbols

        Returns:
            Dict mapping ticker → data
        """
        tasks = [self.get_ticker_data(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                self.logger.warning(f"Failed to fetch {ticker}: {result}")
                data[ticker] = None
            else:
                data[ticker] = result

        return data

    def _fetch_ticker_sync(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Synchronous ticker fetch (run in thread)"""
        try:
            tick = yf.Ticker(ticker)

            # Get current price and basic info
            info = tick.info or {}
            price = info.get("currentPrice") or info.get("regularMarketPrice")

            # Get historical data for indicators
            hist = tick.history(period="3mo", interval="1d")
            if hist.empty:
                self.logger.warning(f"No historical data for {ticker}")
                return {"ticker": ticker, "price": price, "error": "No history"}

            close_prices = hist["Close"].dropna().tolist()
            if not close_prices:
                return None

            # Calculate indicators
            rsi = self._calculate_rsi(close_prices)
            ema_50 = self._calculate_ema(close_prices, 50)
            ema_200 = self._calculate_ema(close_prices, 200)
            macd_line, signal_line, histogram = self._calculate_macd(close_prices)

            # Calculate 3-month change
            if len(close_prices) > 0:
                three_month_change = ((close_prices[-1] - close_prices[0]) / close_prices[0] * 100) if close_prices[0] != 0 else 0
            else:
                three_month_change = 0

            return {
                "ticker": ticker,
                "price": price,
                "three_month_change_pct": round(three_month_change, 2),
                "rsi": rsi,
                "ema_50": ema_50,
                "ema_200": ema_200,
                "macd_line": macd_line,
                "macd_signal": signal_line,
                "macd_histogram": histogram,
                "volume": int(hist["Volume"].iloc[-1]) if not hist.empty else 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error fetching {ticker}: {e}")
            return None

    @staticmethod
    def _calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: List of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value (0-100) or None
        """
        if len(prices) < period + 1:
            return None

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    @staticmethod
    def _calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            prices: List of closing prices
            period: EMA period

        Returns:
            EMA value or None
        """
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return round(ema, 2)

    @staticmethod
    def _calculate_macd(
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: List of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            (macd_line, signal_line, histogram)
        """
        if len(prices) < slow + signal:
            return None, None, None

        ema_fast = MarketDataService._calculate_ema(prices, fast)
        ema_slow = MarketDataService._calculate_ema(prices, slow)

        if ema_fast is None or ema_slow is None:
            return None, None, None

        macd_line = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD)
        macd_values = []
        for i in range(len(prices) - slow + 1):
            ema_f = MarketDataService._calculate_ema(prices[:i+slow], fast)
            ema_s = MarketDataService._calculate_ema(prices[:i+slow], slow)
            if ema_f and ema_s:
                macd_values.append(ema_f - ema_s)

        if len(macd_values) < signal:
            signal_line = None
        else:
            signal_line = sum(macd_values[-signal:]) / signal

        histogram = (macd_line - signal_line) if signal_line else None

        return (
            round(macd_line, 4) if macd_line else None,
            round(signal_line, 4) if signal_line else None,
            round(histogram, 4) if histogram else None,
        )

    def format_market_data_for_llm(self, ticker_data: Dict[str, Any]) -> str:
        """
        Format market data as a string for LLM input.

        Args:
            ticker_data: Market data dict from get_ticker_data()

        Returns:
            Formatted string suitable for LLM prompts
        """
        if not ticker_data:
            return "No data available"

        return f"""
Stock: {ticker_data.get('ticker', 'N/A')}
Price: ${ticker_data.get('price', 'N/A')}
3-Month Change: {ticker_data.get('three_month_change_pct', 0)}%
RSI (14): {ticker_data.get('rsi', 'N/A')}
EMA 50: ${ticker_data.get('ema_50', 'N/A')}
EMA 200: ${ticker_data.get('ema_200', 'N/A')}
MACD Line: {ticker_data.get('macd_line', 'N/A')}
MACD Signal: {ticker_data.get('macd_signal', 'N/A')}
MACD Histogram: {ticker_data.get('macd_histogram', 'N/A')}
Volume: {ticker_data.get('volume', 'N/A')}
"""

    async def get_sp500_subset(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get data for a subset of S&P 500 stocks"""
        return await self.get_multiple_tickers(self.SP500_SYMBOLS)
