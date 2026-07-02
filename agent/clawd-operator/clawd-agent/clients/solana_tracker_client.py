"""Solana Tracker API Client - Token data, charts, holders, bundlers, and more"""

import httpx
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime


SOLANA_TRACKER_BASE_URL = "https://data.solanatracker.io"


@dataclass
class TradeData:
    """Individual trade data"""
    signature: str
    token: str
    type: str  # buy / sell
    amount: float
    price: float
    value_usd: float
    user: str
    timestamp: datetime


class SolanaTrackerClient:
    """Client for Solana Tracker Data API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = SOLANA_TRACKER_BASE_URL
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"x-api-key": api_key},
            timeout=30.0,
        )

    async def _get(self, endpoint: str, params: dict = None) -> Any:
        """Make GET request to Solana Tracker API"""
        response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    # =====================
    # Token Endpoints
    # =====================

    async def get_token_overview(self, token_addresses: list[str]) -> dict:
        """
        Get overview for one or more tokens.
        GET /tokens/multi/all
        """
        return await self._get("/tokens/multi/all", params={"token": token_addresses})

    async def get_graduating_tokens(self) -> dict:
        """
        Get graduating tokens (from bonding curve).
        GET /tokens/multi/graduating
        """
        return await self._get("/tokens/multi/graduating")

    async def get_trending_tokens(self) -> dict:
        """
        Get trending tokens.
        GET /tokens/trending
        """
        return await self._get("/tokens/trending")

    async def get_trending_tokens_by_timeframe(self, timeframe: str) -> dict:
        """
        Get trending tokens by timeframe.
        GET /tokens/trending/{timeframe}
        timeframe: '1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '24h'
        """
        return await self._get(f"/tokens/trending/{timeframe}")

    async def get_top_performers(self, timeframe: str = "24h") -> dict:
        """
        Get top performing tokens.
        GET /top-performers/{timeframe}
        timeframe: '1h', '4h', '24h', '7d', '30d'
        """
        return await self._get(f"/top-performers/{timeframe}")

    async def get_token_stats(self, token_address: str) -> dict:
        """
        Get token statistics.
        GET /stats/{token}
        """
        return await self._get(f"/stats/{token_address}")

    async def get_token_events(self, token_address: str) -> dict:
        """
        Get token events.
        GET /events/{tokenAddress}
        """
        return await self._get(f"/events/{token_address}")

    # =====================
    # Chart / OHLCV
    # =====================

    async def get_ohlcv(self, token_address: str, timeframe: str = "1h", currency: str = "usd", remove_outliers: bool = True, dynamic_pools: bool = True) -> dict:
        """
        Get OHLCV chart data for a token.
        GET /chart/{token}
        timeframe: '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d'
        currency: 'usd' or 'sol'
        remove_outliers: filter out outlier candles
        dynamic_pools: include dynamic pool data
        """
        return await self._get(
            f"/chart/{token_address}",
            params={
                "timeframe": timeframe,
                "currency": currency,
                "removeOutliers": str(remove_outliers).lower(),
                "dynamicPools": str(dynamic_pools).lower(),
            }
        )

    # =====================
    # Price Endpoints
    # =====================

    async def get_token_price(self, token_address: str) -> dict:
        """
        Get current token price.
        GET /price
        """
        return await self._get("/price", params={"token": token_address})

    async def get_price_history(self, token_address: str, timeframe: str = "1h") -> dict:
        """
        Get historic price information.
        GET /price/history
        timeframe: '1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '24h'
        """
        return await self._get("/price/history", params={"token": token_address, "timeframe": timeframe})

    async def get_multi_token_prices(self, token_addresses: list[str]) -> dict:
        """
        Get prices for multiple tokens.
        GET /price/multi
        """
        return await self._get("/price/multi", params={"token": token_addresses})

    # =====================
    # Trades
    # =====================

    async def get_token_trades(self, token_address: str, limit: int = 50, offset: int = 0) -> dict:
        """
        Get trades for a token.
        GET /trades/{tokenAddress}
        """
        return await self._get(f"/trades/{token_address}", params={"limit": limit, "offset": offset})

    async def get_first_buyers(self, token_address: str, limit: int = 50) -> dict:
        """
        Get first buyers of a token.
        GET /first-buyers/{token}
        """
        return await self._get(f"/first-buyers/{token_address}", params={"limit": limit})

    # =====================
    # Holders / Bundlers / Snipers / Insiders
    # =====================

    async def get_token_bundlers(self, token_address: str) -> dict:
        """
        Get token bundlers (wallets that bought at launch together).
        GET /tokens/{token}/bundlers
        """
        return await self._get(f"/tokens/{token_address}/bundlers")

    async def get_holders_paginated(self, token_address: str, page: int = 1, limit: int = 50) -> dict:
        """
        Get all token holders (paginated).
        GET /tokens/{tokenAddress}/holders/paginated
        """
        return await self._get(f"/tokens/{token_address}/holders/paginated", params={"page": page, "limit": limit})

    async def get_holders_chart(self, token_address: str) -> dict:
        """
        Get holders chart data.
        GET /holders/chart/{token}
        """
        return await self._get(f"/holders/chart/{token_address}")

    async def get_insiders_chart(self, token_address: str) -> dict:
        """
        Get insiders chart data.
        GET /insiders/chart/{token}
        """
        return await self._get(f"/insiders/chart/{token_address}")

    async def get_snipers_chart(self, token_address: str) -> dict:
        """
        Get snipers chart data.
        GET /snipers/chart/{token}
        """
        return await self._get(f"/snipers/chart/{token_address}")

    async def get_bundlers_chart(self, token_address: str) -> dict:
        """
        Get bundlers chart data.
        GET /bundlers/chart/{token}
        """
        return await self._get(f"/bundlers/chart/{token_address}")

    # =====================
    # Wallet Endpoints
    # =====================

    async def get_wallet_tokens(self, wallet_address: str) -> dict:
        """
        Get all tokens held by a wallet.
        GET /wallet/{owner}
        """
        return await self._get(f"/wallet/{wallet_address}")

    async def get_wallet_basic(self, wallet_address: str) -> dict:
        """
        Get basic wallet information.
        GET /wallet/{owner}/basic
        """
        return await self._get(f"/wallet/{wallet_address}/basic")

    async def get_wallet_trades(self, wallet_address: str, limit: int = 50, offset: int = 0) -> dict:
        """
        Get wallet trade history.
        GET /wallet/{owner}/trades
        """
        return await self._get(f"/wallet/{wallet_address}/trades", params={"limit": limit, "offset": offset})

    async def get_wallet_chart(self, wallet_address: str) -> dict:
        """
        Get wallet portfolio chart.
        GET /wallet/{owner}/chart
        """
        return await self._get(f"/wallet/{wallet_address}/chart")

    # =====================
    # PnL Endpoints
    # =====================

    async def get_wallet_pnl(self, wallet_address: str) -> dict:
        """
        Get wallet PnL.
        GET /pnl/{wallet}
        """
        return await self._get(f"/pnl/{wallet_address}")

    async def get_token_pnl(self, wallet_address: str, token_address: str) -> dict:
        """
        Get token-specific PnL for a wallet.
        GET /pnl/{wallet}/{token}
        """
        return await self._get(f"/pnl/{wallet_address}/{token_address}")

    # =====================
    # Top Traders
    # =====================

    async def get_top_traders(self) -> dict:
        """
        Get top traders globally.
        GET /top-traders/all
        """
        return await self._get("/top-traders/all")

    async def get_top_traders_for_token(self, token_address: str) -> dict:
        """
        Get top traders for a specific token.
        GET /top-traders/{token}
        """
        return await self._get(f"/top-traders/{token_address}")

    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
