# ABOUTME: OpenClawd Operator package for AI agent orchestration
# ABOUTME: Implements the Llobster Legend operator loop with multi-tool support

"""OpenClawd Operator - Solana-native AI agent orchestration."""

__version__ = "0.2.0"

OPENCLAWD_OPERATOR_IDENTITY = {
    "platform": "OpenClawd",
    "operator": "Llobster Legend",
    "tagline": "Autonomous trading agents for Solana DeFi",
    "symbol": "$CLAWD",
    "token": "8cHzQHUS2s2h8TzCmfqPKYiM4dSt4roa3n7MyRLApump",
}

from .orchestrator import RalphOrchestrator
from .metrics import Metrics, CostTracker, IterationStats
from .error_formatter import ClaudeErrorFormatter, ErrorMessage
from .verbose_logger import VerboseLogger
from .output import DiffStats, DiffFormatter, RalphConsole

try:
    from .adapters.solana import SolanaTradingAdapter, StrategyConfig, TradeMode, TradeAction, OpenPosition
    from .clients import (
        JupiterSwapV2Client,
        SwapV2Quote,
        SwapV2BuildResponse,
        SwapV2Result,
        WRAPPED_SOL_MINT,
        TIP_ACCOUNTS,
    )
except ModuleNotFoundError:
    SolanaTradingAdapter = None
    StrategyConfig = None
    TradeMode = None
    TradeAction = None
    OpenPosition = None
    JupiterSwapV2Client = None
    SwapV2Quote = None
    SwapV2BuildResponse = None
    SwapV2Result = None
    WRAPPED_SOL_MINT = None
    TIP_ACCOUNTS = None

__all__ = [
    "RalphOrchestrator",
    "Metrics",
    "CostTracker",
    "IterationStats",
    "ClaudeErrorFormatter",
    "ErrorMessage",
    "VerboseLogger",
    "DiffStats",
    "DiffFormatter",
    "RalphConsole",
    "OPENCLAWD_OPERATOR_IDENTITY",
    "SolanaTradingAdapter",
    "StrategyConfig",
    "TradeMode",
    "TradeAction",
    "OpenPosition",
    "JupiterSwapV2Client",
    "SwapV2Quote",
    "SwapV2BuildResponse",
    "SwapV2Result",
    "WRAPPED_SOL_MINT",
    "TIP_ACCOUNTS",
]
