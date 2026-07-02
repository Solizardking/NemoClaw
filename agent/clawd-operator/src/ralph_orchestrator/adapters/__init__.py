# ABOUTME: Tool adapter interfaces and implementations
# ABOUTME: Provides unified interface for Claude, Q Chat, Gemini, ACP, Solana trading, and other tools

"""Tool adapters for OpenClawd Operator."""

from .base import ToolAdapter, ToolResponse
from .claude import ClaudeAdapter
from .qchat import QChatAdapter
from .kiro import KiroAdapter
from .gemini import GeminiAdapter
from .acp import ACPAdapter
from .acp_handlers import ACPHandlers, PermissionRequest, PermissionResult, Terminal

try:
    from .solana import SolanaTradingAdapter, TradeAction, TradeMode, StrategyConfig, OpenPosition
except ModuleNotFoundError:
    SolanaTradingAdapter = None
    TradeAction = None
    TradeMode = None
    StrategyConfig = None
    OpenPosition = None

__all__ = [
    "ToolAdapter",
    "ToolResponse",
    "ClaudeAdapter",
    "QChatAdapter",
    "KiroAdapter",
    "GeminiAdapter",
    "ACPAdapter",
    "ACPHandlers",
    "PermissionRequest",
    "PermissionResult",
    "Terminal",
    "SolanaTradingAdapter",
    "TradeAction",
    "TradeMode",
    "StrategyConfig",
    "OpenPosition",
]
