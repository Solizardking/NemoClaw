"""Solana Trading Adapter – autonomous SPL token trading via Jupiter Swap V2.

Implements the ToolAdapter base class and drives the autonomous trading
loop: price fetch → strategy check → decide action → execute swap →
monitor position → report.  Operates within the RalphOrchestrator's arun()
loop as a regular adapter.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from solders.keypair import Keypair

from ..clients.swap_v2_client import (
    JupiterSwapV2Client,
    SwapV2Quote,
    SwapV2Result,
    WRAPPED_SOL_MINT,
)
from .base import ToolAdapter, ToolResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Strategy & state models
# ---------------------------------------------------------------------------


class TradeAction(Enum):
    HOLD = "hold"
    BUY = "buy"
    SELL = "sell"
    REBALANCE = "rebalance"


class TradeMode(Enum):
    """Risk mode for trade sizing."""
    CONSERVATIVE = "conservative"    # 5-10% of available
    MODERATE = "moderate"            # 15-25% of available
    AGGRESSIVE = "aggressive"        # 40-60% of available
    DEGEN = "degen"                  # 80-100% of available


@dataclass
class StrategyConfig:
    """Trading strategy parameters."""
    mode: TradeMode = TradeMode.MODERATE
    buy_threshold_drop_pct: float = -5.0   # Buy when price drops this % from entry
    sell_threshold_gain_pct: float = 15.0  # Sell when price gains this % from entry
    stop_loss_pct: float = -20.0            # Stop-loss level
    trailing_stop_activation_pct: float = 10.0  # Trail after this gain
    trailing_stop_distance_pct: float = 5.0     # Trail distance
    max_position_size_sol: float = 5.0      # Max SOL per position
    min_hold_time_seconds: int = 60         # Min hold before selling
    cooldown_seconds: int = 30              # Wait between trades on same token
    max_slippage_bps: int = 500             # Max slippage (5% default)
    rebalance_interval_seconds: int = 3600  # Check rebalance every hour

    @classmethod
    def from_dict(cls, d: dict) -> StrategyConfig:
        return cls(
            mode=TradeMode(d.get("mode", "moderate")),
            buy_threshold_drop_pct=float(d.get("buy_threshold_drop_pct", -5.0)),
            sell_threshold_gain_pct=float(d.get("sell_threshold_gain_pct", 15.0)),
            stop_loss_pct=float(d.get("stop_loss_pct", -20.0)),
            trailing_stop_activation_pct=float(d.get("trailing_stop_activation_pct", 10.0)),
            trailing_stop_distance_pct=float(d.get("trailing_stop_distance_pct", 5.0)),
            max_position_size_sol=float(d.get("max_position_size_sol", 5.0)),
            min_hold_time_seconds=int(d.get("min_hold_time_seconds", 60)),
            cooldown_seconds=int(d.get("cooldown_seconds", 30)),
            max_slippage_bps=int(d.get("max_slippage_bps", 500)),
            rebalance_interval_seconds=int(d.get("rebalance_interval_seconds", 3600)),
        )


@dataclass
class OpenPosition:
    """Track an open token position."""
    token_mint: str
    token_symbol: str
    entry_price: float        # Price per token in USD
    entry_amount_sol: float   # SOL spent
    token_amount: int         # Raw token amount (smallest unit)
    token_decimals: int
    timestamp: float          # Entry time
    highest_price_since_entry: float = 0.0
    latest_price: float = 0.0
    unrealized_pnl_pct: float = 0.0

    def current_value_sol(self, current_price_sol: float) -> float:
        """Value of position in SOL at current token price."""
        return (self.token_amount / (10 ** self.token_decimals)) * current_price_sol

    def pnl_pct(self, current_price_sol: float) -> float:
        if self.entry_price <= 0:
            return 0.0
        return ((current_price_sol / self.entry_price) - 1.0) * 100.0

    def should_trail_stop(self, strategy: StrategyConfig) -> bool:
        gain = self.pnl_pct(self.latest_price)
        if gain >= strategy.trailing_stop_activation_pct:
            if self.latest_price < self.highest_price_since_entry * (1 - strategy.trailing_stop_distance_pct / 100.0):
                return True
        return False


@dataclass
class TradeHistoryEntry:
    timestamp: float
    action: str  # "buy" | "sell"
    token_mint: str
    token_symbol: str
    amount_sol: float
    token_amount: int
    price: float
    signature: str
    pnl_pct: Optional[float] = None


# ---------------------------------------------------------------------------
#  Solana Trading Adapter
# ---------------------------------------------------------------------------


class SolanaTradingAdapter(ToolAdapter):
    """Autonomous Solana trading adapter using Jupiter Swap V2.

    Operates in the RalphOrchestrator loop:
      1. Fetch token price + wallet balance
      2. Check strategy (should buy / sell / hold)
      3. Execute swap via Jupiter /order + /execute
      4. Monitor open positions
      5. Report results

    Configuration via env vars:
      JUPITER_API_KEY        – from https://developers.jup.ag/portal
      SOLANA_PRIVATE_KEY     – base58-encoded private key
      SOLANA_WALLET_PUBKEY   – wallet public key (optional, derived from keypair)
      TRADE_MODE             – conservative | moderate | aggressive | degen
      DEFAULT_TOKEN_MINT     – the token address to focus on
      MAX_POSITION_SIZE_SOL  – max SOL per position
      DRY_RUN                – if "true", quote but don't execute swaps
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key: Optional[str] = None,
        wallet_pubkey: Optional[str] = None,
        strategy: Optional[StrategyConfig] = None,
        default_token_mint: Optional[str] = None,
        dry_run: bool = False,
        config=None,
    ):
        super().__init__("solana-trading", config=config)

        self.api_key = api_key or os.getenv("JUPITER_API_KEY", "")
        self.dry_run = dry_run or os.getenv("DRY_RUN", "").lower() == "true"

        # Load or derive keypair
        pk = private_key or os.getenv("SOLANA_PRIVATE_KEY")
        self.keypair: Optional[Keypair] = None
        if pk:
            try:
                # Base58-encoded secret key
                import base58
                secret_bytes = base58.b58decode(pk)
                if len(secret_bytes) == 64:
                    self.keypair = Keypair.from_bytes(secret_bytes)
                else:
                    self.keypair = Keypair.from_seed(secret_bytes[:32])
            except Exception as e:
                logger.warning("Failed to load Solana keypair: %s", e)

        # Resolve wallet public key
        self.wallet_pubkey = wallet_pubkey or os.getenv("SOLANA_WALLET_PUBKEY")
        if not self.wallet_pubkey and self.keypair:
            self.wallet_pubkey = str(self.keypair.pubkey())

        # Token configuration
        self.default_token_mint = default_token_mint or os.getenv("DEFAULT_TOKEN_MINT", "")

        # Strategy
        strategy_config = {
            "mode": os.getenv("TRADE_MODE", "moderate"),
        }
        if config and getattr(config, "extra", None):
            configured_strategy = config.extra.get("strategy")
            if isinstance(configured_strategy, dict):
                strategy_config.update(configured_strategy)
        self.strategy = strategy or StrategyConfig.from_dict(strategy_config)

        # Jupiter client (lazy-init)
        self._jupiter: Optional[JupiterSwapV2Client] = None

        # Runtime state
        self.positions: dict[str, OpenPosition] = {}       # token_mint -> position
        self.trade_history: list[TradeHistoryEntry] = []
        self.last_trade_time: dict[str, float] = {}        # token_mint -> timestamp
        self.last_rebalance_time: float = 0.0
        self.entry_prices: dict[str, float] = {}            # token_mint -> entry USD price
        self.total_pnl_usd: float = 0.0
        self.total_trades: int = 0
        self.successful_trades: int = 0
        self.failed_trades: int = 0

        # Track cumulative metrics for ToolResponse metadata
        self._total_quotes: int = 0
        self._total_swaps: int = 0
        self._total_errors: int = 0

        # Iteration log – each tick produces a structured entry
        self.iteration_log: list[dict] = []
        self._broadcast_callback = None

        logger.info(
            "SolanaTradingAdapter initialized (wallet=%s, token=%s, mode=%s, dry_run=%s)",
            self.wallet_pubkey or "?",
            self.default_token_mint or "any",
            self.strategy.mode.value,
            self.dry_run,
        )

    def set_broadcast_callback(self, callback):
        """Register a callback invoked after each trading tick with the tick data."""
        self._broadcast_callback = callback

    # ------------------------------------------------------------------ #
    #  Property: available
    # ------------------------------------------------------------------ #

    def check_availability(self) -> bool:
        """Available if we have an API key + wallet."""
        if not self.api_key:
            logger.warning("JUPITER_API_KEY not set")
            return False
        if not self.wallet_pubkey:
            logger.warning("No wallet public key available")
            return False
        if not self.default_token_mint:
            logger.warning("No DEFAULT_TOKEN_MINT configured; set in ralph.yml or env")
            return False
        return True

    # ------------------------------------------------------------------ #
    #  Lazy Jupiter client
    # ------------------------------------------------------------------ #

    @property
    def jupiter(self) -> JupiterSwapV2Client:
        if self._jupiter is None:
            self._jupiter = JupiterSwapV2Client(
                api_key=self.api_key,
                wallet_pubkey=self.wallet_pubkey,
                keypair=self.keypair,
            )
        return self._jupiter

    # ------------------------------------------------------------------ #
    #  ToolAdapter interface
    # ------------------------------------------------------------------ #

    def estimate_cost(self, prompt: str) -> float:
        """Approximate cost per iteration (API calls, no LLM)."""
        # Jupiter API calls: ~$0.0001 per quote, $0.0005 per swap execution
        return 0.001  # fixed estimate per iteration

    def execute(self, prompt: str, **kwargs) -> ToolResponse:
        """Sync execute – delegates to async."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.aexecute(prompt, **kwargs))

    async def aexecute(self, prompt: str, **kwargs) -> ToolResponse:
        """Execute one iteration of the autonomous trading loop.

        Each iteration:
          1. Parse prompt for a specific token mint (or use default)
          2. Fetch token price and wallet balance
          3. Run strategy check -> decide action
          4. Execute action (buy/sell/hold)
          5. Monitor open positions for stop-loss / take-profit
          6. Return results
        """
        try:
            start_time = time.time()

            # Determine target token
            token_mint = self._extract_token_mint(prompt) or self.default_token_mint
            if not token_mint:
                return ToolResponse(
                    success=False,
                    output="No token mint configured. Set DEFAULT_TOKEN_MINT or pass it in the prompt.",
                    error="No token mint",
                )

            # Step 1: Fetch price + wallet balance
            price_info = await self._fetch_price_info(token_mint)
            if not price_info:
                return ToolResponse(
                    success=False,
                    output="Could not fetch token price.",
                    error="Price fetch failed",
                )

            balance_info = await self._fetch_balance()

            # Step 2: Check strategy
            action = self._decide_action(token_mint, price_info, balance_info)

            # Step 3: Execute
            result_text = ""
            swap_result: Optional[SwapV2Result] = None

            if action == TradeAction.BUY and not self.dry_run:
                swap_result = await self._execute_buy(token_mint, price_info, balance_info)
                result_text = self._format_swap_result(swap_result, "BUY")
            elif action == TradeAction.SELL and not self.dry_run:
                swap_result = await self._execute_sell(token_mint, price_info)
                result_text = self._format_swap_result(swap_result, "SELL")
            elif action == TradeAction.REBALANCE and not self.dry_run:
                result_text = await self._rebalance_portfolio(price_info)
            else:
                result_text = self._format_hold_report(token_mint, price_info, balance_info, action)

            # Step 4: Monitor positions
            monitor_report = self._monitor_positions(token_mint, price_info)

            # Build output
            output_lines = [
                f"## Solana Trading Iteration",
                f"**Time**: {datetime.now(timezone.utc).isoformat()}",
                f"**Token**: {token_mint}",
                f"**Action**: {action.value}",
                f"**Dry Run**: {self.dry_run}",
                "",
                result_text,
                "",
                monitor_report,
                "",
                self._format_summary(),
            ]

            elapsed = time.time() - start_time
            output = "\n".join(output_lines)

            # Build tick log entry
            tick_entry = {
                "ts": time.time(),
                "token_mint": token_mint,
                "price_usd": price_info.get("price_usd", 0),
                "sol_balance": balance_info.get("sol_balance", 0),
                "action": action.value,
                "total_trades": self.total_trades,
                "total_pnl_usd": round(self.total_pnl_usd, 6),
                "open_positions": len(self.positions),
                "elapsed_seconds": round(elapsed, 2),
                "signature": swap_result.signature if swap_result else None,
                "dry_run": self.dry_run,
            }
            self.iteration_log.append(tick_entry)
            # Keep only last 500 entries
            if len(self.iteration_log) > 500:
                self.iteration_log = self.iteration_log[-500:]

            # Broadcast tick via callback if registered
            if self._broadcast_callback:
                try:
                    self._broadcast_callback(tick_entry)
                except Exception:
                    logger.exception("Broadcast callback failed for trading tick")

            return ToolResponse(
                success=True,
                output=output,
                tokens_used=0,
                cost=0.0,
                metadata={
                    "action": action.value,
                    "token_mint": token_mint,
                    "token_price_usd": price_info.get("price_usd"),
                    "sol_balance": balance_info.get("sol_balance", 0),
                    "total_trades": self.total_trades,
                    "total_pnl_usd": self.total_pnl_usd,
                    "open_positions": len(self.positions),
                    "elapsed_seconds": round(elapsed, 2),
                    "dry_run": self.dry_run,
                    "signature": swap_result.signature if swap_result else None,
                },
            )

        except Exception as e:
            logger.exception("Solana trading iteration failed")
            self._total_errors += 1
            self.failed_trades += 1
            return ToolResponse(
                success=False,
                output=f"Trading iteration failed: {e}",
                error=str(e),
                metadata={"total_errors": self._total_errors},
            )

    # ------------------------------------------------------------------ #
    #  Internal: data fetching
    # ------------------------------------------------------------------ #

    async def _fetch_price_info(self, token_mint: str) -> dict:
        """Fetch token price from Jupiter Price V3 API.

        Returns dict with price_usd, price_sol, and raw data.
        """
        token_mints = [token_mint, WRAPPED_SOL_MINT]
        try:
            data = await self.jupiter.get_token_prices(token_mints, vs_token="USDC")
            price_data = data.get("data", {})

            token_info = price_data.get(token_mint, {})
            sol_info = price_data.get(WRAPPED_SOL_MINT, {})

            price_usd = float(token_info.get("price", 0))
            sol_price_usd = float(sol_info.get("price", 0)) or 1.0
            price_sol = price_usd / sol_price_usd if sol_price_usd > 0 else 0.0

            return {
                "price_usd": price_usd,
                "price_sol": price_sol,
                "sol_price_usd": sol_price_usd,
                "price_change_24h": float(token_info.get("priceChange24h", 0)),
                "volume_24h": float(token_info.get("volume24h", 0)),
                "market_cap": float(token_info.get("marketCap", 0)),
                "raw": token_info,
            }
        except Exception as e:
            logger.warning("Failed to fetch price for %s: %s", token_mint, e)
            return {"price_usd": 0.0, "price_sol": 0.0, "error": str(e)}

    async def _fetch_balance(self) -> dict:
        """Fetch wallet SOL balance via Jupiter Portfolio API."""
        if not self.wallet_pubkey:
            return {"sol_balance": 0.0, "tokens": {}}

        try:
            data = await self.jupiter.get_wallet_positions(self.wallet_pubkey)
            positions = data.get("data", {}).get("positions", [])

            sol_balance = 0.0
            token_balances: dict[str, float] = {}

            for pos in positions:
                mint = pos.get("mint", "")
                balance = float(pos.get("balance", 0))
                if mint == WRAPPED_SOL_MINT or mint == "So11111111111111111111111111111111111111112":
                    sol_balance += balance
                else:
                    token_balances[mint] = balance

            # If no sol from positions, try total info
            if sol_balance == 0:
                sol_balance = float(data.get("data", {}).get("totalBalance", 0))

            return {"sol_balance": sol_balance, "tokens": token_balances, "raw": data}
        except Exception as e:
            logger.warning("Failed to fetch balance: %s", e)
            return {"sol_balance": 0.0, "tokens": {}, "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Internal: strategy
    # ------------------------------------------------------------------ #

    def _decide_action(
        self,
        token_mint: str,
        price_info: dict,
        balance_info: dict,
    ) -> TradeAction:
        """Run strategy checks and decide what to do.

        Rules:
          - If we hold the token and it's above sell threshold -> SELL
          - If we hold the token and it's below stop-loss -> SELL
          - If we hold and trailing stop triggered -> SELL
          - If we don't hold and price dropped enough from entry -> BUY
          - If we haven't traded recently and it's time to rebalance -> REBALANCE
          - Otherwise -> HOLD
        """
        price_usd = price_info.get("price_usd", 0)
        sol_balance = balance_info.get("sol_balance", 0)
        now = time.time()

        # Check if we have an open position
        if token_mint in self.positions:
            pos = self.positions[token_mint]
            pos.latest_price = price_usd
            pnl = pos.pnl_pct(price_usd)
            pos.unrealized_pnl_pct = pnl

            # Update highest price for trailing stop
            if price_usd > pos.highest_price_since_entry:
                pos.highest_price_since_entry = price_usd

            # Check cooldown
            last_trade = self.last_trade_time.get(token_mint, 0)
            if now - last_trade < self.strategy.cooldown_seconds:
                logger.debug("Cooldown active for %s", token_mint)
                return TradeAction.HOLD

            # Check min hold time
            if now - pos.timestamp < self.strategy.min_hold_time_seconds:
                logger.debug("Min hold time not reached for %s", token_mint)
                return TradeAction.HOLD

            # Stop-loss
            if pnl <= self.strategy.stop_loss_pct:
                logger.info("STOP-LOSS triggered for %s: pnl=%.2f%%", token_mint, pnl)
                return TradeAction.SELL

            # Trailing stop
            if pos.should_trail_stop(self.strategy):
                logger.info("TRAILING STOP triggered for %s: pnl=%.2f%%", token_mint, pnl)
                return TradeAction.SELL

            # Take profit
            if pnl >= self.strategy.sell_threshold_gain_pct:
                logger.info("TAKE PROFIT triggered for %s: pnl=%.2f%%", token_mint, pnl)
                return TradeAction.SELL

            return TradeAction.HOLD

        # No position: check if we should buy
        if sol_balance <= 0.01:  # Need at least 0.01 SOL for fees
            logger.debug("Insufficient SOL balance for trading: %.4f", sol_balance)
            return TradeAction.HOLD

        # Check buy threshold
        entry_price = self.entry_prices.get(token_mint, price_usd)
        if entry_price > 0:
            price_change = ((price_usd / entry_price) - 1.0) * 100.0
            if price_change <= self.strategy.buy_threshold_drop_pct:
                logger.info("BUY signal: price dropped %.2f%% (threshold: %.2f%%)", price_change, self.strategy.buy_threshold_drop_pct)
                return TradeAction.BUY

        # First buy if price is above 0 (initial entry)
        if token_mint not in self.entry_prices:
            if price_usd > 0 and sol_balance >= 0.1:
                logger.info("BUY signal: new token entry at $%.6f", price_usd)
                return TradeAction.BUY

        # Rebalance check
        if now - self.last_rebalance_time >= self.strategy.rebalance_interval_seconds:
            if len(self.positions) > 1:
                return TradeAction.REBALANCE

        return TradeAction.HOLD

    # ------------------------------------------------------------------ #
    #  Internal: execution
    # ------------------------------------------------------------------ #

    async def _execute_buy(
        self,
        token_mint: str,
        price_info: dict,
        balance_info: dict,
    ) -> Optional[SwapV2Result]:
        """Buy token with SOL – position sized per strategy mode."""
        sol_balance = balance_info.get("sol_balance", 0)
        if sol_balance <= 0.01:
            logger.warning("Insufficient SOL to buy")
            return None

        # Calculate position size based on risk mode
        sol_to_spend = self._calculate_position_size(sol_balance)
        if sol_to_spend <= 0:
            return None

        slippage_bps = self.strategy.max_slippage_bps

        logger.info("BUY %.4f SOL → %s (slippage=%d bps)", sol_to_spend, token_mint, slippage_bps)

        try:
            result = await self.jupiter.buy_token(
                token_mint=token_mint,
                sol_amount=sol_to_spend,
                slippage_bps=slippage_bps,
                execute=True,
            )

            if result.quote and result.signature:
                # Record position
                price_usd = price_info.get("price_usd", 0)
                out_amount = int(result.quote.out_amount)
                token_decimals = self._estimate_decimals(out_amount, price_usd, sol_to_spend)

                pos = OpenPosition(
                    token_mint=token_mint,
                    token_symbol=token_mint[:8],
                    entry_price=price_usd,
                    entry_amount_sol=sol_to_spend,
                    token_amount=out_amount,
                    token_decimals=token_decimals,
                    timestamp=time.time(),
                    highest_price_since_entry=price_usd,
                    latest_price=price_usd,
                )
                self.positions[token_mint] = pos
                self.entry_prices[token_mint] = price_usd
                self.last_trade_time[token_mint] = time.time()
                self.total_trades += 1
                self.successful_trades += 1

                history = TradeHistoryEntry(
                    timestamp=time.time(),
                    action="buy",
                    token_mint=token_mint,
                    token_symbol=token_mint[:8],
                    amount_sol=sol_to_spend,
                    token_amount=out_amount,
                    price=price_usd,
                    signature=result.signature,
                )
                self.trade_history.append(history)

            return result

        except Exception as e:
            logger.error("Buy failed: %s", e)
            self._total_errors += 1
            self.failed_trades += 1
            return None

    async def _execute_sell(
        self,
        token_mint: str,
        price_info: dict,
    ) -> Optional[SwapV2Result]:
        """Sell position back to SOL."""
        if token_mint not in self.positions:
            logger.warning("No position to sell for %s", token_mint)
            return None

        pos = self.positions[token_mint]
        slippage_bps = self.strategy.max_slippage_bps

        logger.info(
            "SELL %d tokens of %s (entry=$%.6f, current=$%.6f)",
            pos.token_amount,
            token_mint,
            pos.entry_price,
            price_info.get("price_usd", 0),
        )

        try:
            result = await self.jupiter.sell_token(
                token_mint=token_mint,
                token_amount=pos.token_amount,
                slippage_bps=slippage_bps,
                execute=True,
            )

            if result.signature:
                # Calculate P&L
                exit_price = price_info.get("price_usd", 0)
                pnl_pct = pos.pnl_pct(exit_price)
                sol_returned = self._estimate_sol_from_sell(result)
                pnl_sol = sol_returned - pos.entry_amount_sol

                self.total_pnl_usd += pnl_sol * price_info.get("sol_price_usd", 0)
                self.total_trades += 1
                self.successful_trades += 1

                history = TradeHistoryEntry(
                    timestamp=time.time(),
                    action="sell",
                    token_mint=token_mint,
                    token_symbol=pos.token_symbol,
                    amount_sol=sol_returned,
                    token_amount=pos.token_amount,
                    price=exit_price,
                    signature=result.signature,
                    pnl_pct=pnl_pct,
                )
                self.trade_history.append(history)

                # Remove position
                del self.positions[token_mint]
                self.last_trade_time[token_mint] = time.time()

            return result

        except Exception as e:
            logger.error("Sell failed: %s", e)
            self._total_errors += 1
            self.failed_trades += 1
            return None

    async def _rebalance_portfolio(self, price_info: dict) -> str:
        """Rebalance portfolio – sell underperformers, keep best performers."""
        self.last_rebalance_time = time.time()

        if len(self.positions) <= 1:
            return "No rebalance needed (≤1 position)."

        # Sort positions by PnL (worst first)
        sorted_positions = sorted(
            self.positions.values(),
            key=lambda p: p.pnl_pct(price_info.get("price_usd", 0)),
        )

        # Sell bottom half (worst performers)
        to_sell = sorted_positions[: len(sorted_positions) // 2]
        results = []
        for pos in to_sell:
            result = await self._execute_sell(pos.token_mint, price_info)
            if result and result.signature:
                results.append(f"Sold {pos.token_symbol}: +{result.signature[:8]}...")

        if results:
            return "Rebalanced:\n" + "\n".join(results)
        return "Rebalance: nothing sold."

    # ------------------------------------------------------------------ #
    #  Internal: monitoring
    # ------------------------------------------------------------------ #

    def _monitor_positions(self, token_mint: str, price_info: dict) -> str:
        """Monitor all open positions and return a report."""
        if not self.positions:
            return "**Open Positions**: None"

        lines = ["**Open Positions**:", ""]
        for mint, pos in self.positions.items():
            pnl = pos.pnl_pct(price_info.get("price_usd", 0))
            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(
                f"  {emoji} `{mint[:12]}...` "
                f"Entry=${pos.entry_price:.8f} "
                f"P&L={pnl:+.2f}% "
                f"Size={pos.entry_amount_sol:.4f} SOL"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _extract_token_mint(self, prompt: str) -> Optional[str]:
        """Try to extract a Solana token mint from the prompt."""
        import re
        # Solana base58 mint addresses are 32-44 chars
        matches = re.findall(r'[1-9A-HJ-NP-Za-km-z]{32,44}', prompt)
        if matches:
            # Filter out known non-token addresses
            for m in matches:
                if m != self.wallet_pubkey and not m.startswith("96gY"):
                    return m
        return None

    def _calculate_position_size(self, sol_balance: float) -> float:
        """Calculate SOL to spend based on strategy mode."""
        ratios = {
            TradeMode.CONSERVATIVE: (0.05, 0.10),
            TradeMode.MODERATE: (0.15, 0.25),
            TradeMode.AGGRESSIVE: (0.40, 0.60),
            TradeMode.DEGEN: (0.80, 1.0),
        }
        min_ratio, max_ratio = ratios.get(self.strategy.mode, (0.15, 0.25))

        position = sol_balance * ((min_ratio + max_ratio) / 2.0)
        position = min(position, self.strategy.max_position_size_sol)

        # Leave at least 0.01 SOL for fees
        return max(0.0, min(position, sol_balance - 0.01))

    def _estimate_decimals(self, token_amount: int, price_usd: float, sol_spent: float) -> int:
        """Estimate token decimals from amount and price."""
        if price_usd <= 0 or sol_spent <= 0:
            return 9  # default
        # Rough estimate: if amount is very large, decimals are high
        if token_amount > 10 ** 12:
            return 9
        if token_amount > 10 ** 9:
            return 6
        if token_amount > 10 ** 6:
            return 6
        return 9

    def _estimate_sol_from_sell(self, result: SwapV2Result) -> float:
        """Estimate SOL returned from a sell result."""
        if result.quote:
            out_amount = int(result.quote.out_amount)
            return out_amount / 1_000_000_000  # lamports to SOL
        return 0.0

    def _format_swap_result(self, result: Optional[SwapV2Result], action: str) -> str:
        """Format a swap result for output."""
        if not result:
            return f"**{action}**: Failed (no result)"

        lines = [f"**{action}**:", ""]
        if result.quote:
            q = result.quote
            lines.append(f"  Input:  {int(q.in_amount) / 1e9:.6f} {q.input_mint[:8]}...")
            lines.append(f"  Output: {int(q.out_amount) / 1e9:.6f} {q.output_mint[:8]}...")
            lines.append(f"  Price Impact: {q.price_impact:.4f}%")
            lines.append(f"  Slippage: {q.slippage_bps} bps")
            lines.append(f"  Router: {q.router}")
            lines.append(f"  Mode: {q.mode}")
            lines.append(f"  Fee: {q.fee_bps} bps")
        if result.signature:
            lines.append(f"  Signature: {result.signature}")
        else:
            lines.append(f"  Status: unsigned (dry_run={self.dry_run})")

        return "\n".join(lines)

    def _format_hold_report(
        self,
        token_mint: str,
        price_info: dict,
        balance_info: dict,
        action: TradeAction,
    ) -> str:
        """Format a hold/no-action report."""
        price_usd = price_info.get("price_usd", 0)
        sol_balance = balance_info.get("sol_balance", 0)
        change_24h = price_info.get("price_change_24h", 0)

        lines = [
            f"**Status**: {action.value.upper()}",
            f"  Token Price: ${price_usd:.8f}",
            f"  24h Change: {change_24h:+.2f}%",
            f"  SOL Balance: {sol_balance:.4f}",
        ]

        if token_mint in self.positions:
            pos = self.positions[token_mint]
            lines.append(f"  Position: {pos.token_amount / (10**pos.token_decimals):.2f} tokens")
            lines.append(f"  Unrealized P&L: {pos.unrealized_pnl_pct:+.2f}%")

        return "\n".join(lines)

    def _format_summary(self) -> str:
        """Format the overall trading summary."""
        lines = [
            "---",
            "**Trading Summary**:",
            f"  Total Trades: {self.total_trades}",
            f"  Successful: {self.successful_trades}",
            f"  Failed: {self.failed_trades}",
            f"  Total P&L: ${self.total_pnl_usd:.4f} USD",
            f"  Open Positions: {len(self.positions)}",
        ]
        return "\n".join(lines)
