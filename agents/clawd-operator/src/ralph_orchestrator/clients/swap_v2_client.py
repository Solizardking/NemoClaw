"""Jupiter Swap V2 API Client.

Full Python wrapper for https://api.jup.ag/swap/v2 supporting:
  - /order  (GET)  – quote + assembled transaction (all routers compete)
  - /execute (POST) – managed landing of a signed /order transaction
  - /build   (GET)  – raw swap instructions (Metis only)
  - /submit  (POST) – submit any signed transaction with SOL tips

Also provides /price/v3, /tokens/v2, /portfolio/v1, and
/ultra/v1 endpoints for supplementary data.

Usage:
  client = JupiterSwapV2Client(api_key="...", keypair=my_keypair)
  quote = await client.get_quote(WRAPPED_SOL_MINT, token_mint, amount_lamports)
  result = await client.quote_to_swap_result(quote)
  sig = await client.sign_and_send_tx(result)
"""

from __future__ import annotations

import base64
import hashlib
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

import httpx

from solders.keypair import Keypair
from solders.message import to_bytes_versioned
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JUPITER_BASE = "https://api.jup.ag"
JUPITER_SWAP_V2 = f"{JUPITER_BASE}/swap/v2"
JUPITER_ULTRA_V1 = f"{JUPITER_BASE}/ultra/v1"
JUPITER_TOKENS_V2 = f"{JUPITER_BASE}/tokens/v2"
JUPITER_PRICE_V3 = f"{JUPITER_BASE}/price/v3"  # also in /price/v2
JUPITER_PORTFOLIO_V1 = f"{JUPITER_BASE}/portfolio/v1"
JUPITER_TX_V1 = f"{JUPITER_BASE}/tx/v1"

WRAPPED_SOL_MINT = "So11111111111111111111111111111111111111112"

# 16 tip receiver accounts for /submit priority landing
TIP_ACCOUNTS: list[str] = [
    "96gYZGDnCz4ti4L4ZhVFDKkvWNsq4LMJxAMWMCRJtKcU",
    "AVWiL4ouPPucM6B3MoTASQ7P8SCQvT1GCamhMr3BqNND",
    "DCN82qknThFe7arGG8KBC1dtrCFd8pYXvbghE7uVLoXL",
    "HWE2BbtNm56SfERaidDq54E71BbamurHzQ2FGJsXGEy8",
    "CD6NBPFuzpGJKtpALHVscPSneRYpx7L3TyjMQZqkHoWi",
    "DteLNts1qN63Bf5H66WZGWABNSbiCqg64CgdSwWSXhCm",
    "FVve3JFjyoZz3f9CHzAXFmQXZyJVKAQvgCMjNPKjhUQi",
    "3Zt1cC3H4AhafvqFMxa7EddfBTsoiKqNUzbZZYAXRczf",
    "F6Gt5xDZGWEYPLWD1LBFUBj5WjZZHy7Tpmqy8TLLaABH",
    "Es4GKKJTuNLJPiKQMbAg6L2xeNsTpMweR5DCkmDxjFqX",
    "2v1uNhRb2stWZJRjcWPasdmAkmYy5VKpCQYbM6Qz6KxR",
    "Ft9acBKZAmqgMVsSZUZgY8VNcXdJrETK4DQUULMRGniY",
    "FxgCnYRoQP1uY17rNyhBw6mNXxMsjM3PEBPFEkKz2KM7",
    "DR8vGEHnzFBBbsxq2iunocqsZMWCLVnAcCPzSMUTLq4h",
    "2JMh3E3GVFs6rjKBWF2LpCZYraA15r4FpxUoSMmCJp28",
    "AUtAaJhwwjpqrgGUYYtWTPmCF6eMRqEfNk2sPDei3APn",
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SwapV2Quote:
    """Response from the /order endpoint on swap/v2."""

    mode: str  # "ultra" | "manual"
    input_mint: str
    output_mint: str
    in_amount: str
    out_amount: str
    in_usd_value: float = 0.0
    out_usd_value: float = 0.0
    price_impact: float = 0.0
    swap_usd_value: float = 0.0
    other_amount_threshold: str = ""
    swap_mode: str = ""
    slippage_bps: int = 0
    route_plan: list[dict] = field(default_factory=list)
    fee_bps: int = 0
    platform_fee: dict = field(default_factory=dict)
    signature_fee_lamports: int = 0
    signature_fee_payer: Optional[str] = None
    prioritization_fee_lamports: int = 0
    prioritization_fee_payer: Optional[str] = None
    rent_fee_lamports: int = 0
    rent_fee_payer: Optional[str] = None
    router: str = ""
    transaction: Optional[str] = None  # base64 assembled tx (unsigned)
    gasless: bool = False
    request_id: str = ""
    total_time: float = 0.0
    taker: Optional[str] = None
    quote_id: str = ""
    maker: str = ""
    expire_at: str = ""
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    raw_response: dict = field(default_factory=dict)

    def compute_effective_price(self) -> Optional[float]:
        """Return output_amount / input_amount as a float, or None."""
        try:
            return int(self.out_amount) / int(self.in_amount)
        except (ValueError, ZeroDivisionError):
            return None

    def __post_init__(self):
        if not self.raw_response:
            self.raw_response = {}


@dataclass
class SwapV2BuildResponse:
    """Response from the /build endpoint on swap/v2 (raw instructions)."""

    compute_budget_instructions: list[dict] = field(default_factory=list)
    setup_instructions: list[dict] = field(default_factory=list)
    swap_instruction: dict = field(default_factory=dict)
    cleanup_instruction: dict = field(default_factory=dict)
    other_instructions: list[dict] = field(default_factory=list)
    tip_instruction: Optional[dict] = None
    addresses_by_lookup_table_address: dict = field(default_factory=dict)
    blockhash_with_metadata: dict = field(default_factory=dict)
    raw_response: dict = field(default_factory=dict)


@dataclass
class SwapV2Result:
    """A ready-to-sign-or-submit swap result.

    For the /order+/execute flow:   quote + unsigned_transaction
    For the /build+/submit  flow:   build_instructions
    """

    quote: Optional[SwapV2Quote] = None
    unsigned_transaction: Optional[str] = None  # base64
    signed_transaction: Optional[str] = None  # base64
    build: Optional[SwapV2BuildResponse] = None
    signature: Optional[str] = None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class JupiterSwapV2Client:
    """Async HTTP client for the Jupiter Swap V2 API.

    Typical happy-path (recommended):
        quote = await client.get_quote(input_mint, output_mint, amount, taker)
        result = await client.quote_to_swap_result(quote)       # decode + optionally sign
        sig   = await client.execute_swap(result)               # POST /execute (managed landing)

    Custom transaction path:
        build = await client.build_swap(input_mint, output_mint, amount, taker)
        # … manually construct the transaction using build.instructions …
        signed_b64 = client.sign_raw_tx(versioned_tx)
        sig = await client.submit_transaction(signed_b64)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        wallet_pubkey: Optional[str] = None,
        keypair: Optional[Keypair] = None,
        referral_account: Optional[str] = None,
        referral_fee_bps: Optional[int] = None,
        timeout: float = 30.0,
    ):
        headers = {"Accept": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key

        self._http = httpx.AsyncClient(headers=headers, timeout=httpx.Timeout(timeout))
        self.wallet_pubkey = wallet_pubkey
        self.keypair = keypair
        self.referral_account = referral_account
        self.referral_fee_bps = referral_fee_bps

    # ------------------------------------------------------------------ #
    #  Lifecycle
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> JupiterSwapV2Client:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------ #
    #  /order  –  quote + assembled transaction  (all routers compete)
    # ------------------------------------------------------------------ #

    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        taker: Optional[str] = None,
        slippage_bps: int = 300,
        receiver: Optional[str] = None,
        payer: Optional[str] = None,
        referral_account: Optional[str] = None,
        referral_fee: Optional[int] = None,
        exclude_routers: Optional[list[str]] = None,
        exclude_dexes: Optional[list[str]] = None,
        mode: Optional[str] = None,  # "ultra" | "manual"
        max_accounts: Optional[int] = None,
        platform_fee_bps: Optional[int] = None,
        fee_account: Optional[str] = None,
        wrap_and_unwrap_sol: Optional[bool] = None,
        dexes: Optional[list[str]] = None,
        destination_token_account: Optional[str] = None,
        native_destination_account: Optional[str] = None,
        blockhash_slots_to_expiry: Optional[int] = None,
    ) -> SwapV2Quote:
        """Fetch a quote and assembled transaction from /order.

        All routers (Metis, JupiterZ/RFQ, Dflow, OKX) compete to give the
        best price.  Returns a base64-encoded unsigned VersionedTransaction
        in ``quote.transaction``.
        """
        if taker is None:
            if self.wallet_pubkey is None:
                raise ValueError("No wallet configured and no taker provided")
            taker = self.wallet_pubkey

        params: dict[str, Any] = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "taker": taker,
            "slippageBps": slippage_bps,
        }
        if receiver:
            params["receiver"] = receiver
        if payer:
            params["payer"] = payer
        if referral_account or self.referral_account:
            params["referralAccount"] = referral_account or self.referral_account
        if referral_fee or self.referral_fee_bps:
            params["referralFee"] = str(referral_fee or self.referral_fee_bps)
        if exclude_routers:
            params["excludeRouters"] = ",".join(exclude_routers)
        if exclude_dexes:
            params["excludeDexes"] = exclude_dexes
        if mode:
            params["mode"] = mode
        if max_accounts is not None:
            params["maxAccounts"] = max_accounts
        if platform_fee_bps is not None:
            params["platformFeeBps"] = platform_fee_bps
        if fee_account:
            params["feeAccount"] = fee_account
        if wrap_and_unwrap_sol is not None:
            params["wrapAndUnwrapSol"] = str(wrap_and_unwrap_sol).lower()
        if dexes:
            params["dexes"] = ",".join(dexes)
        if destination_token_account:
            params["destinationTokenAccount"] = destination_token_account
        if native_destination_account:
            params["nativeDestinationAccount"] = native_destination_account
        if blockhash_slots_to_expiry is not None:
            params["blockhashSlotsToExpiry"] = blockhash_slots_to_expiry

        response = await self._http.get(f"{JUPITER_SWAP_V2}/order", params=params)
        response.raise_for_status()
        data: dict = response.json()

        return SwapV2Quote(
            mode=data.get("mode", "ultra"),
            input_mint=data["inputMint"],
            output_mint=data["outputMint"],
            in_amount=data["inAmount"],
            out_amount=data["outAmount"],
            in_usd_value=float(data.get("inUsdValue", 0)),
            out_usd_value=float(data.get("outUsdValue", 0)),
            price_impact=float(data.get("priceImpact", 0)),
            swap_usd_value=float(data.get("swapUsdValue", 0)),
            other_amount_threshold=data.get("otherAmountThreshold", ""),
            swap_mode=data.get("swapMode", ""),
            slippage_bps=data.get("slippageBps", 0),
            route_plan=data.get("routePlan", []),
            fee_bps=data.get("feeBps", 0),
            platform_fee=data.get("platformFee", {}),
            signature_fee_lamports=data.get("signatureFeeLamports", 0),
            signature_fee_payer=data.get("signatureFeePayer"),
            prioritization_fee_lamports=data.get("prioritizationFeeLamports", 0),
            prioritization_fee_payer=data.get("prioritizationFeePayer"),
            rent_fee_lamports=data.get("rentFeeLamports", 0),
            rent_fee_payer=data.get("rentFeePayer"),
            router=data.get("router", ""),
            transaction=data.get("transaction"),
            gasless=data.get("gasless", False),
            request_id=data.get("requestId", ""),
            total_time=float(data.get("totalTime", 0)),
            taker=data.get("taker"),
            quote_id=data.get("quoteId", ""),
            maker=data.get("maker", ""),
            expire_at=data.get("expireAt", ""),
            error_code=data.get("errorCode"),
            error_message=data.get("errorMessage"),
            raw_response=data,
        )

    # ------------------------------------------------------------------ #
    #  /execute  –  managed landing of a signed /order transaction
    # ------------------------------------------------------------------ #

    async def execute_swap(
        self,
        swap_result: SwapV2Result,
    ) -> str:
        """POST /execute to land a signed /order transaction.

        SwapV2Result must have ``quote.request_id`` and
        ``signed_transaction`` (base64) populated.

        Returns the on-chain transaction signature.
        """
        if not swap_result.quote or not swap_result.quote.request_id:
            raise ValueError("SwapV2Result must have a quote with request_id")
        if not swap_result.signed_transaction:
            raise ValueError("SwapV2Result must have a signed_transaction")

        payload = {
            "requestId": swap_result.quote.request_id,
            "transaction": swap_result.signed_transaction,
        }

        response = await self._http.post(f"{JUPITER_SWAP_V2}/execute", json=payload)
        response.raise_for_status()
        data = response.json()
        sig = data.get("signature", "")
        swap_result.signature = sig
        return sig

    # --------------------------------------------------------------- #
    #  /build  –  raw swap instructions  (Metis only)
    # --------------------------------------------------------------- #

    async def build_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        taker: Optional[str] = None,
        slippage_bps: int = 300,
        receiver: Optional[str] = None,
        payer: Optional[str] = None,
        exclude_routers: Optional[list[str]] = None,
        exclude_dexes: Optional[list[str]] = None,
        wrap_and_unwrap_sol: Optional[bool] = None,
        dexes: Optional[list[str]] = None,
        compute_unit_limit: Optional[int] = None,
        destination_token_account: Optional[str] = None,
        native_destination_account: Optional[str] = None,
    ) -> SwapV2BuildResponse:
        """Get raw swap instructions from /build.

        Unlike /order, /build returns instructions you must assemble yourself.
        This only uses the Metis (on-chain) router.
        """
        if taker is None:
            if self.wallet_pubkey is None:
                raise ValueError("No wallet configured and no taker provided")
            taker = self.wallet_pubkey

        params: dict[str, Any] = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "taker": taker,
            "slippageBps": slippage_bps,
        }
        if receiver:
            params["receiver"] = receiver
        if payer:
            params["payer"] = payer
        if exclude_routers:
            params["excludeRouters"] = ",".join(exclude_routers)
        if exclude_dexes:
            params["excludeDexes"] = exclude_dexes
        if wrap_and_unwrap_sol is not None:
            params["wrapAndUnwrapSol"] = str(wrap_and_unwrap_sol).lower()
        if dexes:
            params["dexes"] = ",".join(dexes)
        if destination_token_account:
            params["destinationTokenAccount"] = destination_token_account
        if native_destination_account:
            params["nativeDestinationAccount"] = native_destination_account
        if compute_unit_limit is not None:
            params["computeUnitLimit"] = compute_unit_limit

        response = await self._http.get(f"{JUPITER_SWAP_V2}/build", params=params)
        response.raise_for_status()
        data: dict = response.json()

        return SwapV2BuildResponse(
            compute_budget_instructions=data.get("computeBudgetInstructions", []),
            setup_instructions=data.get("setupInstructions", []),
            swap_instruction=data.get("swapInstruction", {}),
            cleanup_instruction=data.get("cleanupInstruction", {}),
            other_instructions=data.get("otherInstructions", []),
            tip_instruction=data.get("tipInstruction"),
            addresses_by_lookup_table_address=data.get(
                "addressesByLookupTableAddress", {}
            ),
            blockhash_with_metadata=data.get("blockhashWithMetadata", {}),
            raw_response=data,
        )

    # --------------------------------------------------------------- #
    #  /submit  –  submit any signed tx  (with SOL tips)
    # --------------------------------------------------------------- #

    async def submit_transaction(self, signed_transaction_b64: str) -> str:
        """POST /submit to land any signed transaction.

        For priority landing the tx must include a SOL tip of at least
        0.001 SOL directed to one of the ``TIP_ACCOUNTS``.

        Returns the on-chain signature.
        """
        response = await self._http.post(
            f"{JUPITER_SWAP_V2}/submit",
            json={"signedTransaction": signed_transaction_b64},
        )
        response.raise_for_status()
        return response.json().get("signature", "")

    # --------------------------------------------------------------- #
    #  /tx/v1/submit  –  alternative landing endpoint
    # --------------------------------------------------------------- #

    async def submit_tx_v1(self, signed_transaction_b64: str) -> str:
        """Submit a transaction via the legacy tx/v1 endpoint."""
        response = await self._http.post(
            f"{JUPITER_TX_V1}/submit",
            json={"signedTransaction": signed_transaction_b64},
        )
        response.raise_for_status()
        return response.json().get("signature", "")

    # --------------------------------------------------------------- #
    #  Transaction helpers
    # --------------------------------------------------------------- #

    def decode_transaction(self, b64_tx: str) -> VersionedTransaction:
        """Decode a base64-encoded VersionedTransaction."""
        return VersionedTransaction.from_bytes(base64.b64decode(b64_tx))

    def sign_transaction(self, unsigned_b64: str) -> str:
        """Sign an unsigned VersionedTransaction and return base64.

        Uses the configured keypair.
        """
        if self.keypair is None:
            raise ValueError("No keypair configured for signing")

        tx = self.decode_transaction(unsigned_b64)
        message_bytes = to_bytes_versioned(tx.message)
        sig = self.keypair.sign_message(message_bytes)
        signed_tx = VersionedTransaction.populate(tx.message, [sig])
        return base64.b64encode(bytes(signed_tx)).decode()

    def sign_raw_tx(self, tx: VersionedTransaction) -> str:
        """Sign an already-decoded VersionedTransaction and return base64."""
        if self.keypair is None:
            raise ValueError("No keypair configured for signing")
        message_bytes = to_bytes_versioned(tx.message)
        sig = self.keypair.sign_message(message_bytes)
        signed_tx = VersionedTransaction.populate(tx.message, [sig])
        return base64.b64encode(bytes(signed_tx)).decode()

    # --------------------------------------------------------------- #
    #  Convenience: end-to-end swap via /order + /execute
    # --------------------------------------------------------------- #

    async def quote_to_swap_result(
        self,
        quote: SwapV2Quote,
        sign: bool = True,
    ) -> SwapV2Result:
        """Convert a quote into a SwapV2Result ready for /execute.

        If ``sign`` is True and a keypair is configured, the transaction
        will be signed automatically.
        """
        result = SwapV2Result(quote=quote, unsigned_transaction=quote.transaction)
        if sign and self.keypair and quote.transaction:
            result.signed_transaction = self.sign_transaction(quote.transaction)
        elif sign and not self.keypair:
            logger.warning("No keypair set – skipping signing")
        return result

    async def swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 300,
        sign: bool = True,
        execute: bool = True,
    ) -> SwapV2Result:
        """End-to-end swap: /order → optionally sign → optionally /execute.

        Args:
            input_mint:  Input token mint.
            output_mint: Output token mint.
            amount:      Amount in the smallest unit (lamports).
            slippage_bps: Slippage tolerance in basis points (default 300 = 3%).
            sign:        Whether to sign the transaction automatically.
            execute:     Whether to POST /execute automatically.

        Returns a SwapV2Result with the quote, (optionally signed tx),
        and (optionally) the on-chain signature.
        """
        quote = await self.get_quote(
            input_mint=input_mint,
            output_mint=output_mint,
            amount=amount,
            slippage_bps=slippage_bps,
        )

        result = await self.quote_to_swap_result(quote, sign=sign)
        if execute and result.signed_transaction:
            sig = await self.execute_swap(result)
            result.signature = sig
        return result

    async def buy_token(
        self,
        token_mint: str,
        sol_amount: float,
        slippage_bps: int = 300,
        execute: bool = True,
    ) -> SwapV2Result:
        """Buy a token with SOL."""
        lamports = int(sol_amount * 1_000_000_000)
        return await self.swap(
            input_mint=WRAPPED_SOL_MINT,
            output_mint=token_mint,
            amount=lamports,
            slippage_bps=slippage_bps,
            execute=execute,
        )

    async def sell_token(
        self,
        token_mint: str,
        token_amount: int,
        slippage_bps: int = 300,
        execute: bool = True,
    ) -> SwapV2Result:
        """Sell a token for SOL."""
        return await self.swap(
            input_mint=token_mint,
            output_mint=WRAPPED_SOL_MINT,
            amount=token_amount,
            slippage_bps=slippage_bps,
            execute=execute,
        )

    # --------------------------------------------------------------- #
    #  Supplementary Jupiter API methods
    # --------------------------------------------------------------- #

    async def get_token_prices(
        self,
        token_mints: list[str],
        vs_token: str = "USDC",
        show_extra_info: bool = False,
    ) -> dict:
        """Fetch prices via Jupiter Price V3 API."""
        params: dict[str, Any] = {"ids": ",".join(token_mints), "vsToken": vs_token}
        if show_extra_info:
            params["showExtraInfo"] = "true"
        response = await self._http.get(JUPITER_PRICE_V3, params=params)
        response.raise_for_status()
        return response.json()

    async def get_sol_price(self) -> float:
        """Convenience: get SOL price in USD."""
        data = await self.get_token_prices([WRAPPED_SOL_MINT], vs_token="USDC")
        try:
            return float(data["data"][WRAPPED_SOL_MINT]["price"])
        except (KeyError, TypeError, ValueError):
            return 0.0

    async def get_wallet_positions(self, wallet: Optional[str] = None) -> dict:
        """Get wallet portfolio positions."""
        wallet = wallet or self.wallet_pubkey
        if not wallet:
            raise ValueError("No wallet address available")
        response = await self._http.get(f"{JUPITER_PORTFOLIO_V1}/positions/{wallet}")
        response.raise_for_status()
        return response.json()

    async def search_tokens(
        self, query: str, limit: int = 20, verified_only: bool = False
    ) -> dict:
        """Search tokens via Jupiter Tokens V2 API."""
        params: dict[str, Any] = {"query": query, "limit": limit}
        if verified_only:
            params["verified"] = "true"
        response = await self._http.get(f"{JUPITER_TOKENS_V2}/search", params=params)
        response.raise_for_status()
        return response.json()

    async def get_trending_tokens(
        self, category: str = "top", interval: str = "24h"
    ) -> dict:
        """Get trending tokens from Jupiter Tokens V2."""
        response = await self._http.get(f"{JUPITER_TOKENS_V2}/{category}/{interval}")
        response.raise_for_status()
        return response.json()

    async def get_token_info(self, mint: str) -> dict:
        """Get token metadata from Jupiter Tokens V2."""
        response = await self._http.get(f"{JUPITER_TOKENS_V2}/token/{mint}")
        response.raise_for_status()
        return response.json()

    async def get_shield_warnings(self, token_mint: str) -> dict:
        """Check token safety via Jupiter Ultra Shield."""
        response = await self._http.get(f"{JUPITER_ULTRA_V1}/shield/{token_mint}")
        response.raise_for_status()
        return response.json()
