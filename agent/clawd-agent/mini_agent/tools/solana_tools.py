"""Solana Trading Tools for CLAWD Agent"""

import json
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any, Optional

from .base import Tool, ToolResult


# Global client instances (set during agent initialization)
_bags_client = None
_helius_client = None
_birdeye_client = None
_cdp_client = None
_hyperliquid_client = None
_pumpfun_client = None
_jupiter_client = None


def set_solana_clients(bags_client=None, helius_client=None, birdeye_client=None, cdp_client=None, hyperliquid_client=None, pumpfun_client=None, jupiter_client=None):
    """Set the global client instances for tools to use."""
    global _bags_client, _helius_client, _birdeye_client, _cdp_client, _hyperliquid_client, _pumpfun_client, _jupiter_client
    _bags_client = bags_client
    _helius_client = helius_client
    _birdeye_client = birdeye_client
    _cdp_client = cdp_client
    _hyperliquid_client = hyperliquid_client
    _pumpfun_client = pumpfun_client
    _jupiter_client = jupiter_client


def get_pumpfun_client():
    """Get PumpFun client (may be None if not configured)."""
    return _pumpfun_client


def get_bags_client():
    if _bags_client is None:
        raise RuntimeError("BagsClient not initialized")
    return _bags_client


def get_helius_client():
    if _helius_client is None:
        raise RuntimeError("HeliusClient not initialized")
    return _helius_client


def get_birdeye_client():
    if _birdeye_client is None:
        raise RuntimeError("BirdeyeClient not initialized")
    return _birdeye_client


def get_cdp_client():
    if _cdp_client is None:
        raise RuntimeError("CDPClient not initialized - check CDP credentials in .env")
    return _cdp_client


def get_hyperliquid_client():
    if _hyperliquid_client is None:
        raise RuntimeError("HyperliquidClient not initialized - check HYPERLIQUID credentials in .env")
    return _hyperliquid_client


def get_jupiter_client():
    if _jupiter_client is None:
        raise RuntimeError("JupiterClient not initialized - check JUPITER_API_KEY in .env")
    return _jupiter_client


SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


async def resolve_token_decimals(mint: str) -> int:
    """Resolve mint decimals using known constants, Birdeye, then Helius."""
    if mint == SOL_MINT:
        return 9
    if mint == USDC_MINT:
        return 6

    try:
        birdeye = get_birdeye_client()
        overview = await birdeye.get_token_overview(mint)
        if overview and isinstance(overview.decimals, int):
            return overview.decimals
    except Exception:
        pass

    try:
        helius = get_helius_client()
        info = await helius.get_account_info(mint, encoding="jsonParsed")
        if info and isinstance(info.data, dict):
            parsed = info.data.get("parsed", {})
            token_info = parsed.get("info", {})
            decimals = token_info.get("decimals")
            if isinstance(decimals, int):
                return decimals
    except Exception:
        pass

    raise ValueError(f"Could not resolve decimals for mint {mint}")


def ui_amount_to_raw(amount_ui: Any, decimals: int) -> int:
    """Convert a UI token amount to raw smallest units."""
    try:
        quantized = (Decimal(str(amount_ui)) * (Decimal(10) ** decimals)).to_integral_value(rounding=ROUND_DOWN)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid UI amount: {amount_ui}") from e

    raw = int(quantized)
    if raw <= 0:
        raise ValueError("Converted raw amount must be > 0")
    return raw


class GetWalletBalanceTool(Tool):
    """Tool to get wallet SOL and token balances."""
    
    @property
    def name(self) -> str:
        return "get_wallet_balance"
    
    @property
    def description(self) -> str:
        return "Get SOL balance and token holdings for a Solana wallet. Uses agent wallet if none provided."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wallet_address": {
                    "type": "string",
                    "description": "Solana wallet address. Optional - uses agent wallet if not provided.",
                }
            },
            "required": [],
        }
    
    async def execute(self, wallet_address: str = None) -> ToolResult:
        try:
            helius = get_helius_client()
            bags = get_bags_client()
            
            address = wallet_address or bags.wallet_pubkey
            if not address:
                return ToolResult(success=False, error="No wallet address provided")
            
            sol_balance = await helius.get_sol_balance(address)
            token_balances = await helius.get_token_accounts_by_owner(address)
            
            result = {
                "wallet": address,
                "sol_balance": sol_balance,
                "tokens": [
                    {"mint": tb.mint, "amount": tb.ui_amount, "decimals": tb.decimals}
                    for tb in token_balances if tb.ui_amount > 0
                ]
            }
            
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetTokenPriceTool(Tool):
    """Tool to get current token price."""
    
    @property
    def name(self) -> str:
        return "get_token_price"
    
    @property
    def description(self) -> str:
        return "Get current price and 24h change for a Solana token by mint address."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {
                    "type": "string",
                    "description": "Token mint address.",
                }
            },
            "required": ["token_mint"],
        }
    
    async def execute(self, token_mint: str) -> ToolResult:
        try:
            birdeye = get_birdeye_client()
            price_data = await birdeye.get_token_price(token_mint)
            
            result = {
                "mint": token_mint,
                "price_usd": price_data.get("value", 0),
                "price_change_24h": price_data.get("priceChange24h", 0),
            }
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetTokenInfoTool(Tool):
    """Tool to get comprehensive token information."""
    
    @property
    def name(self) -> str:
        return "get_token_info"
    
    @property
    def description(self) -> str:
        return "Get comprehensive token info: name, symbol, price, volume, liquidity, market cap, holders."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {"type": "string", "description": "Token mint address."}
            },
            "required": ["token_mint"],
        }
    
    async def execute(self, token_mint: str) -> ToolResult:
        try:
            birdeye = get_birdeye_client()
            overview = await birdeye.get_token_overview(token_mint)
            
            result = {
                "mint": overview.mint,
                "name": overview.name,
                "symbol": overview.symbol,
                "decimals": overview.decimals,
                "price_usd": overview.price,
                "price_change_1h": overview.price_change_1h,
                "price_change_24h": overview.price_change_24h,
                "volume_24h": overview.volume_24h,
                "liquidity": overview.liquidity,
                "market_cap": overview.market_cap,
                "holder_count": overview.holder_count,
            }
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetSwapQuoteTool(Tool):
    """Tool to get a swap quote without executing."""
    
    @property
    def name(self) -> str:
        return "get_swap_quote"
    
    @property
    def description(self) -> str:
        return "Get swap quote to check expected output before trading. SOL mint: So11111111111111111111111111111111111111112"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_mint": {"type": "string", "description": "Input token mint."},
                "output_mint": {"type": "string", "description": "Output token mint."},
                "amount": {"type": "number", "description": "Amount in smallest unit (lamports)."},
                "slippage_bps": {"type": "integer", "description": "Slippage (100=1%). Default 300.", "default": 300},
            },
            "required": ["input_mint", "output_mint", "amount"],
        }
    
    async def execute(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 300) -> ToolResult:
        try:
            bags = get_bags_client()
            quote = await bags.get_quote(input_mint, output_mint, int(amount), slippage_bps)
            
            result = {
                "input_mint": quote.input_mint,
                "output_mint": quote.output_mint,
                "input_amount": quote.in_amount,
                "output_amount": quote.out_amount,
                "min_output": quote.min_out_amount,
                "price_impact_pct": quote.price_impact_pct,
                "slippage_bps": quote.slippage_bps,
            }
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BuyTokenTool(Tool):
    """Tool to buy a token with SOL."""
    
    @property
    def name(self) -> str:
        return "buy_token"
    
    @property
    def description(self) -> str:
        return "⚠️ EXECUTES REAL TRADE - Buy tokens with SOL. Returns transaction signature."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {"type": "string", "description": "Token to buy."},
                "sol_amount": {"type": "number", "description": "SOL to spend."},
                "slippage_bps": {"type": "integer", "description": "Slippage (100=1%). Default 300.", "default": 300},
            },
            "required": ["token_mint", "sol_amount"],
        }
    
    async def execute(self, token_mint: str, sol_amount: float, slippage_bps: int = 300) -> ToolResult:
        try:
            bags = get_bags_client()
            if bags.keypair is None:
                return ToolResult(success=False, error="No wallet configured for trading")
            
            result = await bags.buy_token(token_mint, sol_amount, slippage_bps)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "signature": result["signature"],
                "sol_spent": result["quote"]["in_amount"],
                "tokens_received": result["quote"]["out_amount"],
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SellTokenTool(Tool):
    """Tool to sell a token for SOL."""
    
    @property
    def name(self) -> str:
        return "sell_token"
    
    @property
    def description(self) -> str:
        return "⚠️ EXECUTES REAL TRADE - Sell tokens for SOL. Returns transaction signature."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {"type": "string", "description": "Token to sell."},
                "token_amount": {"type": "integer", "description": "Amount in smallest unit."},
                "slippage_bps": {"type": "integer", "description": "Slippage (100=1%). Default 300.", "default": 300},
            },
            "required": ["token_mint", "token_amount"],
        }
    
    async def execute(self, token_mint: str, token_amount: int, slippage_bps: int = 300) -> ToolResult:
        try:
            bags = get_bags_client()
            if bags.keypair is None:
                return ToolResult(success=False, error="No wallet configured for trading")
            
            result = await bags.sell_token(token_mint, int(token_amount), slippage_bps)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "signature": result["signature"],
                "tokens_sold": result["quote"]["in_amount"],
                "sol_received": result["quote"]["out_amount"],
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetPortfolioTool(Tool):
    """Tool to get wallet portfolio with USD values."""
    
    @property
    def name(self) -> str:
        return "get_portfolio"
    
    @property
    def description(self) -> str:
        return "Get complete portfolio with all tokens and USD values."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wallet_address": {"type": "string", "description": "Wallet. Optional - uses agent wallet."}
            },
            "required": [],
        }
    
    async def execute(self, wallet_address: str = None) -> ToolResult:
        try:
            birdeye = get_birdeye_client()
            bags = get_bags_client()
            address = wallet_address or bags.wallet_pubkey
            if not address:
                return ToolResult(success=False, error="No wallet address")
            
            portfolio = await birdeye.get_wallet_portfolio(address)
            return ToolResult(success=True, content=json.dumps({"wallet": address, "portfolio": portfolio}, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetTrendingTokensTool(Tool):
    """Tool to get trending tokens."""
    
    @property
    def name(self) -> str:
        return "get_trending_tokens"
    
    @property
    def description(self) -> str:
        return "Get trending Solana tokens sorted by volume, market cap, or liquidity."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sort_by": {"type": "string", "description": "Sort: v24hUSD (volume), mc (market cap), liquidity.", "default": "v24hUSD"},
                "limit": {"type": "integer", "description": "Max tokens. Default 20.", "default": 20},
            },
            "required": [],
        }
    
    async def execute(self, sort_by: str = "v24hUSD", limit: int = 20) -> ToolResult:
        try:
            birdeye = get_birdeye_client()
            # Map user-friendly names to API params
            sort_map = {
                "volume24h": "v24hUSD",
                "volume": "v24hUSD",
                "rank": "v24hUSD",
                "marketcap": "mc",
                "market_cap": "mc",
            }
            api_sort = sort_map.get(sort_by.lower(), sort_by)
            tokens = await birdeye.get_trending_tokens(sort_by=api_sort, sort_type="desc", limit=limit)
            return ToolResult(success=True, content=json.dumps({"trending_tokens": tokens, "count": len(tokens) if isinstance(tokens, list) else 0}, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchTokenTool(Tool):
    """Tool to search for tokens."""
    
    @property
    def name(self) -> str:
        return "search_token"
    
    @property
    def description(self) -> str:
        return "Search for Solana tokens by name or symbol. Returns mint addresses."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Token name or symbol."},
                "limit": {"type": "integer", "description": "Max results. Default 10.", "default": 10},
            },
            "required": ["query"],
        }
    
    async def execute(self, query: str, limit: int = 10) -> ToolResult:
        try:
            birdeye = get_birdeye_client()
            results = await birdeye.search_token(query, limit=limit)
            return ToolResult(success=True, content=json.dumps({"query": query, "results": results}, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class LaunchTokenTool(Tool):
    """Tool to launch a new token on Solana via Bags."""
    
    @property
    def name(self) -> str:
        return "launch_token"
    
    @property
    def description(self) -> str:
        return "⚠️ LAUNCHES REAL TOKEN - Create and launch a new token on Solana via Bags/Meteora. Returns mint address and launch URL."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Token name (e.g., 'My Token')"},
                "symbol": {"type": "string", "description": "Token symbol (e.g., 'MYT')"},
                "description": {"type": "string", "description": "Token description"},
                "image_url": {"type": "string", "description": "URL to token image"},
                "initial_buy_sol": {"type": "number", "description": "Initial SOL to buy. Default 0.01", "default": 0.01},
                "twitter": {"type": "string", "description": "Twitter/X URL (optional)"},
                "website": {"type": "string", "description": "Website URL (optional)"},
                "telegram": {"type": "string", "description": "Telegram URL (optional)"},
            },
            "required": ["name", "symbol", "description", "image_url"],
        }
    
    async def execute(
        self, 
        name: str, 
        symbol: str, 
        description: str, 
        image_url: str,
        initial_buy_sol: float = 0.01,
        twitter: str = None,
        website: str = None,
        telegram: str = None,
    ) -> ToolResult:
        try:
            bags = get_bags_client()
            if bags.keypair is None:
                return ToolResult(success=False, error="No wallet configured for launching tokens")
            
            result = await bags.launch_token(
                name=name,
                symbol=symbol,
                description=description,
                image_url=image_url,
                initial_buy_sol=initial_buy_sol,
                twitter=twitter,
                website=website,
                telegram=telegram,
            )
            
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "token_mint": result["token_mint"],
                "token_url": result["token_url"],
                "signature": result["signature"],
                "metadata_uri": result["metadata_uri"],
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetClaimableFeesTool(Tool):
    """Tool to get claimable fees from tokens."""
    
    @property
    def name(self) -> str:
        return "get_claimable_fees"
    
    @property
    def description(self) -> str:
        return "Get all claimable fee positions from tokens you have fee shares in."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
    
    async def execute(self) -> ToolResult:
        try:
            bags = get_bags_client()
            positions = await bags.get_claimable_fees()
            return ToolResult(success=True, content=json.dumps({
                "positions": positions,
                "count": len(positions),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ClaimFeesTool(Tool):
    """Tool to claim fees from a token."""
    
    @property
    def name(self) -> str:
        return "claim_fees"
    
    @property
    def description(self) -> str:
        return "⚠️ EXECUTES TRANSACTION - Claim accumulated fees from token positions."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {"type": "string", "description": "Token mint to claim fees from (optional, claims all if not specified)"},
            },
            "required": [],
        }
    
    async def execute(self, token_mint: str = None) -> ToolResult:
        try:
            bags = get_bags_client()
            if bags.keypair is None:
                return ToolResult(success=False, error="No wallet configured for claiming fees")
            
            positions = await bags.get_claimable_fees()
            
            if token_mint:
                positions = [p for p in positions if p.get("baseMint") == token_mint]
            
            if not positions:
                return ToolResult(success=True, content=json.dumps({"message": "No claimable positions found"}))
            
            signatures = []
            for position in positions:
                sig = await bags.claim_fees(position)
                if sig:
                    signatures.append(sig)
            
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "claimed_positions": len(signatures),
                "signatures": signatures,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ============================================================
# CDP (Coinbase Developer Platform) Tools  
# ============================================================

class CDPCreateAccountTool(Tool):
    """Tool to create a new CDP-managed Solana account."""
    
    @property
    def name(self) -> str:
        return "cdp_create_account"
    
    @property
    def description(self) -> str:
        return "Create a new Solana account managed by Coinbase Developer Platform (CDP). Returns the new account address."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Optional name/label for the account."}
            },
            "required": [],
        }
    
    async def execute(self, name: str = None) -> ToolResult:
        try:
            cdp = get_cdp_client()
            result = await cdp.create_account(name=name)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "address": result["address"],
                "name": result.get("name"),
                "network": "solana-devnet",
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CDPRequestFaucetTool(Tool):
    """Tool to request devnet SOL from faucet."""
    
    @property
    def name(self) -> str:
        return "cdp_request_faucet"
    
    @property
    def description(self) -> str:
        return "Request free devnet SOL tokens from the faucet for a CDP account. Only works on devnet."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Solana address to fund. Uses first CDP account if not provided."}
            },
            "required": [],
        }
    
    async def execute(self, address: str = None) -> ToolResult:
        try:
            cdp = get_cdp_client()
            result = await cdp.request_faucet(address=address)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "address": result["address"],
                "transaction": result.get("tx_hash"),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CDPGetBalanceTool(Tool):
    """Tool to get SOL balance for a CDP account."""
    
    @property
    def name(self) -> str:
        return "cdp_get_balance"
    
    @property
    def description(self) -> str:
        return "Get the SOL balance for a Solana address using CDP."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Solana address to check balance for."}
            },
            "required": ["address"],
        }
    
    async def execute(self, address: str) -> ToolResult:
        try:
            cdp = get_cdp_client()
            result = await cdp.get_balance(address=address)
            return ToolResult(success=True, content=json.dumps({
                "address": address,
                "balance_sol": result.get("balance", 0),
                "balance_lamports": result.get("lamports", 0),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CDPSendSOLTool(Tool):
    """Tool to send SOL using CDP for signing."""
    
    @property
    def name(self) -> str:
        return "cdp_send_sol"
    
    @property
    def description(self) -> str:
        return "⚠️ EXECUTES REAL TRANSACTION - Send SOL from a CDP-managed account to another address."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "from_address": {"type": "string", "description": "Source CDP-managed Solana address."},
                "to_address": {"type": "string", "description": "Destination Solana address."},
                "amount_sol": {"type": "number", "description": "Amount of SOL to send."},
            },
            "required": ["from_address", "to_address", "amount_sol"],
        }
    
    async def execute(self, from_address: str, to_address: str, amount_sol: float) -> ToolResult:
        try:
            cdp = get_cdp_client()
            result = await cdp.send_sol(from_address=from_address, to_address=to_address, amount_sol=amount_sol)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "from": from_address,
                "to": to_address,
                "amount_sol": amount_sol,
                "signature": result.get("signature"),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CDPListAccountsTool(Tool):
    """Tool to list all CDP-managed accounts."""
    
    @property
    def name(self) -> str:
        return "cdp_list_accounts"
    
    @property
    def description(self) -> str:
        return "List all Solana accounts managed by CDP."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
    
    async def execute(self) -> ToolResult:
        try:
            cdp = get_cdp_client()
            result = await cdp.list_accounts()
            return ToolResult(success=True, content=json.dumps({
                "accounts": result.get("accounts", []),
                "count": len(result.get("accounts", [])),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# CDP Tools list
CDP_TOOLS = [
    CDPCreateAccountTool,
    CDPRequestFaucetTool,
    CDPGetBalanceTool,
    CDPSendSOLTool,
    CDPListAccountsTool,
]


# ============================================================
# Hyperliquid DEX Trading Tools
# ============================================================

class HyperliquidGetAccountTool(Tool):
    """Tool to get Hyperliquid account info."""

    @property
    def name(self) -> str:
        return "hyperliquid_get_account"

    @property
    def description(self) -> str:
        return "Get Hyperliquid account info including balance, margin summary, and open positions."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.get_account_state()
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidGetPriceTool(Tool):
    """Tool to get current prices on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_get_price"

    @property
    def description(self) -> str:
        return "Get current price, 24h change, and funding rate for assets on Hyperliquid."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL). Optional - returns all if not specified."}
            },
            "required": [],
        }

    async def execute(self, coin: str = None) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.get_all_mids()
            if coin:
                coin_upper = coin.upper()
                if coin_upper in result:
                    return ToolResult(success=True, content=json.dumps({
                        "coin": coin_upper,
                        "mid_price": result[coin_upper]
                    }, indent=2))
                else:
                    return ToolResult(success=False, error=f"Coin {coin} not found on Hyperliquid")
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidOpenLongTool(Tool):
    """Tool to open a long position on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_open_long"

    @property
    def description(self) -> str:
        return "⚠️ EXECUTES REAL TRADE - Open a LONG perpetual position on Hyperliquid. Uses market order."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL)"},
                "size": {"type": "number", "description": "Position size in coin units (e.g., 0.01 for 0.01 BTC)"},
                "leverage": {"type": "integer", "description": "Leverage multiplier (1-50). Default 5.", "default": 5},
            },
            "required": ["coin", "size"],
        }

    async def execute(self, coin: str, size: float, leverage: int = 5) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.open_position(
                coin=coin.upper(),
                is_long=True,
                size=size,
                leverage=leverage,
            )
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "coin": coin.upper(),
                "side": "LONG",
                "size": size,
                "leverage": leverage,
                "order_id": result.get("response", {}).get("data", {}).get("statuses", [{}])[0].get("resting", {}).get("oid"),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidOpenShortTool(Tool):
    """Tool to open a short position on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_open_short"

    @property
    def description(self) -> str:
        return "⚠️ EXECUTES REAL TRADE - Open a SHORT perpetual position on Hyperliquid. Uses market order."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL)"},
                "size": {"type": "number", "description": "Position size in coin units"},
                "leverage": {"type": "integer", "description": "Leverage multiplier (1-50). Default 5.", "default": 5},
            },
            "required": ["coin", "size"],
        }

    async def execute(self, coin: str, size: float, leverage: int = 5) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.open_position(
                coin=coin.upper(),
                is_long=False,
                size=size,
                leverage=leverage,
            )
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "coin": coin.upper(),
                "side": "SHORT",
                "size": size,
                "leverage": leverage,
                "order_id": result.get("response", {}).get("data", {}).get("statuses", [{}])[0].get("resting", {}).get("oid"),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidClosePositionTool(Tool):
    """Tool to close a position on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_close_position"

    @property
    def description(self) -> str:
        return "⚠️ EXECUTES REAL TRADE - Close an open position on Hyperliquid (full or partial)."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL)"},
                "size": {"type": "number", "description": "Size to close. If not provided, closes entire position."},
            },
            "required": ["coin"],
        }

    async def execute(self, coin: str, size: float = None) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.close_position(coin=coin.upper(), size=size)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "coin": coin.upper(),
                "closed_size": size or "all",
                "result": result,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidGetPositionsTool(Tool):
    """Tool to get open positions on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_get_positions"

    @property
    def description(self) -> str:
        return "Get all open perpetual positions on Hyperliquid with PnL."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            positions = await hl.get_positions()
            return ToolResult(success=True, content=json.dumps({
                "positions": positions,
                "count": len(positions) if isinstance(positions, list) else 0,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidSetLeverageTool(Tool):
    """Tool to set leverage on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_set_leverage"

    @property
    def description(self) -> str:
        return "Set leverage for a coin on Hyperliquid. Can use cross or isolated margin."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL)"},
                "leverage": {"type": "integer", "description": "Leverage multiplier (1-50)"},
                "is_cross": {"type": "boolean", "description": "True for cross margin, False for isolated. Default True.", "default": True},
            },
            "required": ["coin", "leverage"],
        }

    async def execute(self, coin: str, leverage: int, is_cross: bool = True) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.set_leverage(coin=coin.upper(), leverage=leverage, is_cross=is_cross)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "coin": coin.upper(),
                "leverage": leverage,
                "margin_type": "cross" if is_cross else "isolated",
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidGetAvailableCoinsTool(Tool):
    """Tool to list available coins on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_get_available_coins"

    @property
    def description(self) -> str:
        return "Get list of all available perpetual markets on Hyperliquid."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            coins = await hl.get_available_coins()
            return ToolResult(success=True, content=json.dumps({
                "coins": coins,
                "count": len(coins) if isinstance(coins, list) else 0,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class HyperliquidTransferTool(Tool):
    """Tool to transfer USDC between perp and spot on Hyperliquid."""

    @property
    def name(self) -> str:
        return "hyperliquid_transfer"

    @property
    def description(self) -> str:
        return "⚠️ EXECUTES TRANSFER - Transfer USDC between perpetual and spot accounts on Hyperliquid."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Amount of USDC to transfer"},
                "to_perp": {"type": "boolean", "description": "True to transfer TO perp account, False to transfer TO spot account"},
            },
            "required": ["amount", "to_perp"],
        }

    async def execute(self, amount: float, to_perp: bool) -> ToolResult:
        try:
            hl = get_hyperliquid_client()
            result = await hl.transfer_between_accounts(amount=amount, to_perp=to_perp)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "amount": amount,
                "direction": "spot -> perp" if to_perp else "perp -> spot",
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Hyperliquid Tools list
HYPERLIQUID_TOOLS = [
    HyperliquidGetAccountTool,
    HyperliquidGetPriceTool,
    HyperliquidOpenLongTool,
    HyperliquidOpenShortTool,
    HyperliquidClosePositionTool,
    HyperliquidGetPositionsTool,
    HyperliquidSetLeverageTool,
    HyperliquidGetAvailableCoinsTool,
    HyperliquidTransferTool,
]


# =====================================================================
# PumpFun Tools (bonding-curve launches + trading; Mayhem / Token2022 aware)
# =====================================================================
# These import lazily inside execute() because pumpfun_client uses solders/
# struct packing — keeping the import out of module load avoids paying the
# cost when the client isn't configured.


class PumpFunLaunchTokenTool(Tool):
    """Launch a token via the legacy pump.fun create instruction (SPL Token + Metaplex)."""

    @property
    def name(self) -> str:
        return "pumpfun_launch_token"

    @property
    def description(self) -> str:
        return (
            "Launch a new pump.fun token using the legacy `create` instruction "
            "(SPL Token + Metaplex metadata). For new launches you should "
            "usually prefer pumpfun_launch_token_v2 — this is kept for parity."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "symbol": {"type": "string"},
                "description": {"type": "string"},
                "image_url": {"type": "string"},
                "image_path": {"type": "string"},
                "twitter": {"type": "string"},
                "telegram": {"type": "string"},
                "website": {"type": "string"},
                "initial_buy_sol": {"type": "number", "default": 0.0},
            },
            "required": ["name", "symbol", "description"],
        }

    async def execute(
        self, name: str, symbol: str, description: str,
        image_url: Optional[str] = None, image_path: Optional[str] = None,
        twitter: Optional[str] = None, telegram: Optional[str] = None,
        website: Optional[str] = None, initial_buy_sol: float = 0.0,
    ) -> ToolResult:
        try:
            pumpfun = get_pumpfun_client()
            if pumpfun is None:
                return ToolResult(success=False, error="PumpFun client not configured.")
            result = await pumpfun.create_token(
                name=name, symbol=symbol, description=description,
                image_url=image_url, image_path=image_path,
                twitter=twitter, telegram=telegram, website=website,
                initial_buy_sol=initial_buy_sol,
            )
            return ToolResult(success=True, content=json.dumps({
                "mint": str(result.mint),
                "bonding_curve": str(result.bonding_curve),
                "signature": result.signature,
                "token_url": result.token_url,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=f"Launch failed: {e}")


class PumpFunLaunchTokenV2Tool(Tool):
    """Launch a token via create_v2 (Token2022 + optional Mayhem mode)."""

    @property
    def name(self) -> str:
        return "pumpfun_launch_token_v2"

    @property
    def description(self) -> str:
        return (
            "⚠️ EXECUTES REAL TRANSACTION — Launch a pump.fun token via the new "
            "create_v2 instruction (Token2022 + on-chain metadata). Set "
            "is_mayhem_mode=true to opt the coin into Mayhem mode at launch; "
            "this routes trade fees to the Mayhem fee recipients and cannot be "
            "changed later."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "symbol": {"type": "string"},
                "description": {"type": "string"},
                "image_url": {"type": "string"},
                "image_path": {"type": "string"},
                "twitter": {"type": "string"},
                "telegram": {"type": "string"},
                "website": {"type": "string"},
                "initial_buy_sol": {"type": "number", "default": 0.0},
                "is_mayhem_mode": {"type": "boolean", "default": False},
            },
            "required": ["name", "symbol", "description"],
        }

    async def execute(
        self, name: str, symbol: str, description: str,
        image_url: Optional[str] = None, image_path: Optional[str] = None,
        twitter: Optional[str] = None, telegram: Optional[str] = None,
        website: Optional[str] = None, initial_buy_sol: float = 0.0,
        is_mayhem_mode: bool = False,
    ) -> ToolResult:
        try:
            pumpfun = get_pumpfun_client()
            if pumpfun is None:
                return ToolResult(success=False, error="PumpFun client not configured.")
            result = await pumpfun.create_token_v2(
                name=name, symbol=symbol, description=description,
                image_url=image_url, image_path=image_path,
                twitter=twitter, telegram=telegram, website=website,
                initial_buy_sol=initial_buy_sol,
                is_mayhem_mode=is_mayhem_mode,
            )
            return ToolResult(success=True, content=json.dumps({
                "mode": "create_v2",
                "is_mayhem_mode": is_mayhem_mode,
                "mint": str(result.mint),
                "bonding_curve": str(result.bonding_curve),
                "signature": result.signature,
                "token_url": result.token_url,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=f"create_v2 launch failed: {e}")


class PumpFunBuyTool(Tool):
    """Buy from a pump.fun bonding curve (auto-detects Mayhem + Token2022)."""

    @property
    def name(self) -> str:
        return "pumpfun_buy"

    @property
    def description(self) -> str:
        return (
            "⚠️ EXECUTES REAL TRANSACTION — Buy tokens from a pump.fun bonding "
            "curve using buy_v2. Supports SOL-paired coins via sol_amount, or "
            "explicit quote-mint routes via base_amount + max_quote_cost."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mint": {"type": "string", "description": "Token mint address"},
                "sol_amount": {"type": "number", "description": "SOL to spend for SOL-paired curves. Backward-compatible shortcut."},
                "base_amount": {"type": "integer", "description": "Exact base token amount to buy in smallest units."},
                "base_amount_ui": {"type": "number", "description": "Exact base token amount to buy in UI units, e.g. 1000.5."},
                "max_quote_cost": {"type": "integer", "description": "Maximum quote token amount to pay, in smallest units."},
                "max_quote_cost_ui": {"type": "number", "description": "Maximum quote token amount to pay in UI units, e.g. 1.25 USDC or 0.5 SOL."},
                "quote_mint": {"type": "string", "description": "Optional explicit quote mint. Defaults to the curve's quote mint."},
                "slippage_bps": {"type": "integer", "default": 500},
            },
            "required": ["mint"],
        }

    async def execute(
        self,
        mint: str,
        sol_amount: float = None,
        base_amount: int = None,
        base_amount_ui: float = None,
        max_quote_cost: int = None,
        max_quote_cost_ui: float = None,
        quote_mint: str = None,
        slippage_bps: int = 500,
    ) -> ToolResult:
        try:
            from solders.pubkey import Pubkey
            pumpfun = get_pumpfun_client()
            if pumpfun is None:
                return ToolResult(success=False, error="PumpFun client not configured.")
            mint_pk = Pubkey.from_string(mint)
            quote_pk = Pubkey.from_string(quote_mint) if quote_mint else None

            if base_amount is None and base_amount_ui is not None:
                base_decimals = await resolve_token_decimals(mint)
                base_amount = ui_amount_to_raw(base_amount_ui, base_decimals)
            if max_quote_cost is None and max_quote_cost_ui is not None:
                resolved_quote_mint = quote_mint
                if not resolved_quote_mint:
                    state = await pumpfun.get_bonding_curve_state(mint_pk)
                    if state is None:
                        return ToolResult(success=False, error="Bonding curve not found")
                    resolved_quote_mint = str(state.quote_mint)
                quote_decimals = await resolve_token_decimals(resolved_quote_mint)
                max_quote_cost = ui_amount_to_raw(max_quote_cost_ui, quote_decimals)

            if base_amount is not None or max_quote_cost is not None:
                if base_amount is None or max_quote_cost is None:
                    return ToolResult(success=False, error="base_amount and max_quote_cost must be provided together")
                sig = await pumpfun.buy_v2(
                    mint_pk,
                    base_amount=base_amount,
                    max_quote_cost=max_quote_cost,
                    quote_mint=quote_pk,
                )
                payload = {
                    "signature": sig,
                    "mint": mint,
                    "base_amount": base_amount,
                    "base_amount_ui": base_amount_ui,
                    "max_quote_cost": max_quote_cost,
                    "max_quote_cost_ui": max_quote_cost_ui,
                    "quote_mint": quote_mint,
                }
            else:
                if sol_amount is None:
                    return ToolResult(success=False, error="Provide sol_amount or base_amount + max_quote_cost")
                sig = await pumpfun.buy(mint_pk, sol_amount, slippage_bps)
                payload = {
                    "signature": sig,
                    "mint": mint,
                    "sol_spent": sol_amount,
                }
            return ToolResult(success=True, content=json.dumps({
                **payload,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=f"Buy failed: {e}")


class PumpFunSellTool(Tool):
    """Sell to a pump.fun bonding curve (auto-detects Mayhem + Token2022)."""

    @property
    def name(self) -> str:
        return "pumpfun_sell"

    @property
    def description(self) -> str:
        return (
            "⚠️ EXECUTES REAL TRANSACTION — Sell tokens to a pump.fun bonding "
            "curve using sell_v2. token_amount is in raw smallest units. "
            "Optionally provide min_quote_output and quote_mint for non-SOL pairs."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mint": {"type": "string"},
                "token_amount": {"type": "integer", "description": "Raw amount in smallest units"},
                "token_amount_ui": {"type": "number", "description": "Token amount in UI units, e.g. 1234.56."},
                "min_quote_output": {"type": "integer", "description": "Optional explicit quote floor in smallest units."},
                "min_quote_output_ui": {"type": "number", "description": "Optional quote floor in UI units, e.g. 0.75 SOL or 100 USDC."},
                "quote_mint": {"type": "string", "description": "Optional explicit quote mint. Defaults to the curve's quote mint."},
                "slippage_bps": {"type": "integer", "default": 500},
            },
            "required": ["mint"],
        }

    async def execute(
        self,
        mint: str,
        token_amount: int = None,
        token_amount_ui: float = None,
        min_quote_output: int = None,
        min_quote_output_ui: float = None,
        quote_mint: str = None,
        slippage_bps: int = 500,
    ) -> ToolResult:
        try:
            from solders.pubkey import Pubkey
            pumpfun = get_pumpfun_client()
            if pumpfun is None:
                return ToolResult(success=False, error="PumpFun client not configured.")
            mint_pk = Pubkey.from_string(mint)
            quote_pk = Pubkey.from_string(quote_mint) if quote_mint else None
            if token_amount is None and token_amount_ui is not None:
                base_decimals = await resolve_token_decimals(mint)
                token_amount = ui_amount_to_raw(token_amount_ui, base_decimals)
            if token_amount is None:
                return ToolResult(success=False, error="Provide token_amount or token_amount_ui")
            if min_quote_output is None and min_quote_output_ui is not None:
                resolved_quote_mint = quote_mint
                if not resolved_quote_mint:
                    state = await pumpfun.get_bonding_curve_state(mint_pk)
                    if state is None:
                        return ToolResult(success=False, error="Bonding curve not found")
                    resolved_quote_mint = str(state.quote_mint)
                quote_decimals = await resolve_token_decimals(resolved_quote_mint)
                min_quote_output = ui_amount_to_raw(min_quote_output_ui, quote_decimals)
            if min_quote_output is not None:
                sig = await pumpfun.sell_v2(
                    mint_pk,
                    token_amount=token_amount,
                    min_quote_output=min_quote_output,
                    quote_mint=quote_pk,
                )
                payload = {
                    "signature": sig,
                    "mint": mint,
                    "tokens_sold": token_amount,
                    "token_amount_ui": token_amount_ui,
                    "min_quote_output": min_quote_output,
                    "min_quote_output_ui": min_quote_output_ui,
                    "quote_mint": quote_mint,
                }
            else:
                sig = await pumpfun.sell(mint_pk, token_amount, slippage_bps)
                payload = {
                    "signature": sig,
                    "mint": mint,
                    "tokens_sold": token_amount,
                }
            return ToolResult(success=True, content=json.dumps({
                **payload,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=f"Sell failed: {e}")


class PumpFunGetQuoteTool(Tool):
    """Preview pump.fun buy_v2/sell_v2 quote details."""

    @property
    def name(self) -> str:
        return "pumpfun_get_quote"

    @property
    def description(self) -> str:
        return (
            "Preview pump.fun buy_v2 or sell_v2 quotes, including resolved quote "
            "mint, base amount, and quote amount, without executing a trade."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mint": {"type": "string", "description": "pump.fun mint address"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "quote_amount": {"type": "integer", "description": "For buy previews: quote input in smallest units."},
                "quote_amount_ui": {"type": "number", "description": "For buy previews: quote input in UI units."},
                "base_amount": {"type": "integer", "description": "For buy previews exact output or sell previews exact input, in smallest units."},
                "base_amount_ui": {"type": "number", "description": "For buy previews exact output or sell previews exact input, in UI units."},
                "quote_mint": {"type": "string", "description": "Optional explicit quote mint override."},
            },
            "required": ["mint", "side"],
        }

    async def execute(
        self,
        mint: str,
        side: str,
        quote_amount: int = None,
        quote_amount_ui: float = None,
        base_amount: int = None,
        base_amount_ui: float = None,
        quote_mint: str = None,
    ) -> ToolResult:
        try:
            from solders.pubkey import Pubkey
            pumpfun = get_pumpfun_client()
            if pumpfun is None:
                return ToolResult(success=False, error="PumpFun client not configured.")
            mint_pk = Pubkey.from_string(mint)
            quote_pk = Pubkey.from_string(quote_mint) if quote_mint else None
            if base_amount is None and base_amount_ui is not None:
                base_decimals = await resolve_token_decimals(mint)
                base_amount = ui_amount_to_raw(base_amount_ui, base_decimals)
            if quote_amount is None and quote_amount_ui is not None:
                resolved_quote_mint = quote_mint
                if not resolved_quote_mint:
                    state = await pumpfun.get_bonding_curve_state(mint_pk)
                    if state is None:
                        return ToolResult(success=False, error="Bonding curve not found")
                    resolved_quote_mint = str(state.quote_mint)
                quote_decimals = await resolve_token_decimals(resolved_quote_mint)
                quote_amount = ui_amount_to_raw(quote_amount_ui, quote_decimals)
            if side == "buy":
                result = await pumpfun.get_buy_v2_quote(
                    mint_pk,
                    quote_amount=quote_amount,
                    base_amount=base_amount,
                    quote_mint=quote_pk,
                )
            elif side == "sell":
                if base_amount is None:
                    return ToolResult(success=False, error="base_amount is required for sell previews")
                result = await pumpfun.get_sell_v2_quote(
                    mint_pk,
                    token_amount=base_amount,
                    quote_mint=quote_pk,
                )
            else:
                return ToolResult(success=False, error="side must be buy or sell")
            return ToolResult(success=True, content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=f"Quote failed: {e}")


class PumpFunGetPriceTool(Tool):
    """Read bonding curve price + reserves for a pump.fun mint."""

    @property
    def name(self) -> str:
        return "pumpfun_get_price"

    @property
    def description(self) -> str:
        return (
            "Get the current bonding-curve price, market cap, virtual/real "
            "reserves, completion progress, and is_mayhem_mode flag for a "
            "pump.fun token mint."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"mint": {"type": "string"}},
            "required": ["mint"],
        }

    async def execute(self, mint: str) -> ToolResult:
        try:
            from solders.pubkey import Pubkey
            pumpfun = get_pumpfun_client()
            if pumpfun is None:
                return ToolResult(success=False, error="PumpFun client not configured.")
            mint_pk = Pubkey.from_string(mint)
            price = await pumpfun.get_token_price(mint_pk)
            if price is None:
                return ToolResult(success=False, error="Bonding curve not found")
            state = await pumpfun.get_bonding_curve_state(mint_pk)
            price["is_mayhem_mode"] = bool(state.is_mayhem_mode) if state else False
            return ToolResult(success=True, content=json.dumps(price, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=f"Price lookup failed: {e}")


# =====================================================================
# Jupiter Ultra Tools (one-shot swap/buy/sell via Jupiter Ultra API)
# =====================================================================

SOL_MINT = "So11111111111111111111111111111111111111112"


class JupiterBuyTokenTool(Tool):
    """One-shot buy any Solana token with SOL via Jupiter Ultra."""

    @property
    def name(self) -> str:
        return "jupiter_buy_token"

    @property
    def description(self) -> str:
        return (
            "⚠️ EXECUTES REAL TRADE — Buy any Solana token with SOL using Jupiter Ultra. "
            "Works for pump.fun tokens, memecoins, and any token tradeable on Jupiter. "
            "SOL mint: So11111111111111111111111111111111111111112"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {"type": "string", "description": "Mint address of the token to buy."},
                "sol_amount": {"type": "number", "description": "Amount of SOL to spend (e.g. 0.1)."},
                "slippage_bps": {"type": "integer", "description": "Slippage tolerance in bps (100=1%). Default 300.", "default": 300},
            },
            "required": ["token_mint", "sol_amount"],
        }

    async def execute(self, token_mint: str, sol_amount: float, slippage_bps: int = 300) -> ToolResult:
        try:
            jup = get_jupiter_client()
            signature = await jup.buy_token(token_mint, sol_amount, slippage_bps)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "action": "buy",
                "token_mint": token_mint,
                "sol_spent": sol_amount,
                "signature": signature,
                "explorer": f"https://solscan.io/tx/{signature}",
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class JupiterSellTokenTool(Tool):
    """One-shot sell any Solana token for SOL via Jupiter Ultra."""

    @property
    def name(self) -> str:
        return "jupiter_sell_token"

    @property
    def description(self) -> str:
        return (
            "⚠️ EXECUTES REAL TRADE — Sell any Solana token for SOL using Jupiter Ultra. "
            "token_amount is in raw smallest units (multiply UI amount by 10^decimals)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "token_mint": {"type": "string", "description": "Mint address of the token to sell."},
                "token_amount": {"type": "integer", "description": "Amount in raw smallest units (e.g. 1000000 for 1 USDC at 6 decimals)."},
                "slippage_bps": {"type": "integer", "description": "Slippage tolerance in bps. Default 300.", "default": 300},
            },
            "required": ["token_mint", "token_amount"],
        }

    async def execute(self, token_mint: str, token_amount: int, slippage_bps: int = 300) -> ToolResult:
        try:
            jup = get_jupiter_client()
            signature = await jup.sell_token(token_mint, int(token_amount), slippage_bps)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "action": "sell",
                "token_mint": token_mint,
                "tokens_sold": token_amount,
                "signature": signature,
                "explorer": f"https://solscan.io/tx/{signature}",
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class JupiterSwapTool(Tool):
    """Generic one-shot swap between any two tokens via Jupiter Ultra."""

    @property
    def name(self) -> str:
        return "jupiter_swap"

    @property
    def description(self) -> str:
        return (
            "⚠️ EXECUTES REAL TRADE — Swap any token for any other token via Jupiter Ultra. "
            "Use this for token-to-token swaps (not just SOL pairs). "
            "SOL mint: So11111111111111111111111111111111111111112"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_mint": {"type": "string", "description": "Mint of the token to sell."},
                "output_mint": {"type": "string", "description": "Mint of the token to buy."},
                "amount": {"type": "integer", "description": "Input amount in raw smallest units."},
                "slippage_bps": {"type": "integer", "description": "Slippage in bps. Default 300.", "default": 300},
            },
            "required": ["input_mint", "output_mint", "amount"],
        }

    async def execute(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 300) -> ToolResult:
        try:
            jup = get_jupiter_client()
            signature = await jup.swap(input_mint, output_mint, int(amount), slippage_bps)
            return ToolResult(success=True, content=json.dumps({
                "status": "success",
                "input_mint": input_mint,
                "output_mint": output_mint,
                "amount": amount,
                "signature": signature,
                "explorer": f"https://solscan.io/tx/{signature}",
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class JupiterGetQuoteTool(Tool):
    """Get a Jupiter Ultra swap quote (no execution)."""

    @property
    def name(self) -> str:
        return "jupiter_get_quote"

    @property
    def description(self) -> str:
        return (
            "Get a Jupiter Ultra swap quote — price impact, expected output, route — "
            "without executing the trade. Use before jupiter_buy_token or jupiter_swap "
            "to preview the trade."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_mint": {"type": "string", "description": "Input token mint."},
                "output_mint": {"type": "string", "description": "Output token mint."},
                "amount": {"type": "integer", "description": "Input amount in raw smallest units."},
                "slippage_bps": {"type": "integer", "description": "Slippage in bps. Default 300.", "default": 300},
            },
            "required": ["input_mint", "output_mint", "amount"],
        }

    async def execute(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 300) -> ToolResult:
        try:
            jup = get_jupiter_client()
            quote = await jup.get_quote(input_mint, output_mint, int(amount), slippage_bps=slippage_bps)
            return ToolResult(success=True, content=json.dumps({
                "input_mint": quote.input_mint,
                "output_mint": quote.output_mint,
                "in_amount": quote.in_amount,
                "out_amount": quote.out_amount,
                "in_usd": quote.in_usd_value,
                "out_usd": quote.out_usd_value,
                "price_impact": quote.price_impact,
                "slippage_bps": quote.slippage_bps,
                "router": quote.router,
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# =====================================================================
# Helius Wallet Transfer Tools
# =====================================================================

class GetWalletTransfersTool(Tool):
    """Get token transfer history for a wallet via Helius."""

    @property
    def name(self) -> str:
        return "get_wallet_transfers"

    @property
    def description(self) -> str:
        return (
            "Get token transfer history (sent/received) for any Solana wallet "
            "using the Helius Wallet API. Returns counterparty, amount, token, "
            "direction (in/out), and transaction signature."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wallet_address": {"type": "string", "description": "Solana wallet address. Uses agent wallet if not provided."},
                "limit": {"type": "integer", "description": "Max transfers to return (1-100). Default 50.", "default": 50},
                "cursor": {"type": "string", "description": "Pagination cursor from a previous response."},
            },
            "required": [],
        }

    async def execute(self, wallet_address: str = None, limit: int = 50, cursor: str = None) -> ToolResult:
        try:
            helius = get_helius_client()
            bags = get_bags_client()
            address = wallet_address or bags.wallet_pubkey
            if not address:
                return ToolResult(success=False, error="No wallet address provided")

            data = await helius.get_wallet_transfers(address, limit=limit, cursor=cursor)
            transfers = data.get("data", [])
            pagination = data.get("pagination", {})

            summary = []
            for t in transfers:
                summary.append({
                    "direction": t.get("direction"),
                    "amount": t.get("amount"),
                    "symbol": t.get("symbol") or t.get("mint", "")[:8] + "...",
                    "mint": t.get("mint"),
                    "counterparty": t.get("counterparty"),
                    "timestamp": t.get("timestamp"),
                    "signature": t.get("signature"),
                })

            return ToolResult(success=True, content=json.dumps({
                "wallet": address,
                "transfers": summary,
                "count": len(summary),
                "has_more": pagination.get("hasMore", False),
                "next_cursor": pagination.get("nextCursor"),
            }, indent=2))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Tool factory
ALL_TRADING_TOOLS = [
    GetWalletBalanceTool,
    GetTokenPriceTool,
    GetTokenInfoTool,
    GetSwapQuoteTool,
    BuyTokenTool,
    SellTokenTool,
    GetPortfolioTool,
    GetTrendingTokensTool,
    SearchTokenTool,
    LaunchTokenTool,
    GetClaimableFeesTool,
    ClaimFeesTool,
    # PumpFun (bonding curve)
    PumpFunLaunchTokenTool,
    PumpFunLaunchTokenV2Tool,
    PumpFunGetQuoteTool,
    PumpFunBuyTool,
    PumpFunSellTool,
    PumpFunGetPriceTool,
    # Jupiter Ultra (one-shot swap for any token)
    JupiterBuyTokenTool,
    JupiterSellTokenTool,
    JupiterSwapTool,
    JupiterGetQuoteTool,
    # Helius wallet transfers
    GetWalletTransfersTool,
] + CDP_TOOLS + HYPERLIQUID_TOOLS


def create_all_trading_tools() -> list[Tool]:
    """Create instances of all Solana trading tools."""
    return [ToolCls() for ToolCls in ALL_TRADING_TOOLS]
