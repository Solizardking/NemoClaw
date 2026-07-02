"""PumpFun Client - Launch and trade tokens on pump.fun"""

import httpx
import base58
import struct
import json
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path
import random

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.hash import Hash
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solders.sysvar import RENT as SYSVAR_RENT_ID


# Program IDs
PUMP_PROGRAM_ID = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
PUMP_GLOBAL = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")
PUMP_FEE_RECIPIENT = Pubkey.from_string("62qc2CNXwrYqQScmEdiZFFAnJR262PxWEuNQtxfafNgV")
PUMP_EVENT_AUTHORITY = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
PUMP_FEES_PROGRAM_ID = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
NATIVE_MINT = Pubkey.from_string("So11111111111111111111111111111111111111112")

# Mayhem mode (new token creation)
MAYHEM_PROGRAM_ID = Pubkey.from_string("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e")
MAYHEM_GLOBAL_PARAMS = Pubkey.from_string("13ec7XdrjF3h3YcqBTFDSReRcUFwbCnJaAQspM4j6DDJ")
MAYHEM_SOL_VAULT = Pubkey.from_string("BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s")

# Mayhem fee recipients — for is_mayhem_mode=true coins.
# Source: pumpfun-docs/README.md (12:00 UTC, 11 November 2025 breaking change).
MAYHEM_FEE_RECIPIENTS = [
    Pubkey.from_string("GesfTA3X2arioaHp8bbKdjG9vJtskViWACZoYvxp4twS"),
    Pubkey.from_string("4budycTjhs9fD6xw62VBducVTNgMgJJ5BgtKq7mAZwn6"),
    Pubkey.from_string("8SBKzEQU4nLSzcwF4a74F2iaUDQyTfjGndn6qUWBnrpR"),
    Pubkey.from_string("4UQeTP1T39KZ9Sfxzo3WR5skgsaP6NZa87BAkuazLEKH"),
    Pubkey.from_string("8sNeir4QsLsJdYpc9RZacohhK1Y5FLU3nC5LXgYB4aa6"),
    Pubkey.from_string("Fh9HmeLNUMVCvejxCtCL2DbYaRyBFVJ5xrWkLnMH6fdk"),
    Pubkey.from_string("463MEnMeGyJekNZFQSTUABBEbLnvMTALbT6ZmsxAbAdq"),
    Pubkey.from_string("6AUH3WEHucYZyC61hqpqYUWVto5qA5hjHuNQ32GNnNxA"),
]

# Token programs
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN_2022_PROGRAM_ID = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

# Metaplex
METAPLEX_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

# Instruction discriminators (from IDL)
CREATE_DISCRIMINATOR = bytes([24, 30, 200, 40, 5, 28, 7, 119])
CREATE_V2_DISCRIMINATOR = bytes([31, 240, 17, 64, 245, 233, 167, 192])
BUY_DISCRIMINATOR = bytes([102, 6, 61, 18, 1, 218, 235, 234])
SELL_DISCRIMINATOR = bytes([51, 230, 133, 164, 1, 127, 131, 173])
BUY_V2_DISCRIMINATOR = bytes([184, 23, 238, 97, 103, 197, 211, 61])
SELL_V2_DISCRIMINATOR = bytes([93, 246, 130, 60, 231, 233, 64, 178])

CURRENT_FEE_RECIPIENTS = [
    Pubkey.from_string("62qc2CNXwrYqQScmEdiZFFAnJR262PxWEuNQtxfafNgV"),
    Pubkey.from_string("7VtfL8fvgNfhz17qKRMjzQEXgbdpnHHHQRh54R9jP2RJ"),
    Pubkey.from_string("7hTckgnGnLQR6sdH7YkqFTAA7VwTfYFaZ6EhEsU3saCX"),
    Pubkey.from_string("9rPYyANsfQZw3DnDmKE3YCQF5E8oD89UXoHn9JFEhJUz"),
    Pubkey.from_string("AVmoTthdrX6tKt4nDjco2D775W2YK3sDhxPcMmzUAmTY"),
    Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM"),
    Pubkey.from_string("FWsW1xNtWscwNmKv6wVsU1iTzRN6wmmk3MjxRP5tT7hz"),
    Pubkey.from_string("G5UZAVbAf46s7cKWoyKu8kYTip9DGTpbLZ2qa9Aq69dP"),
]

CURRENT_BUYBACK_FEE_RECIPIENTS = [
    Pubkey.from_string("5YxQFdt3Tr9zJLvkFccqXVUwhdTWJQc1fFg2YPbxvxeD"),
    Pubkey.from_string("9M4giFFMxmFGXtc3feFzRai56WbBqehoSeRE5GK7gf7"),
    Pubkey.from_string("GXPFM2caqTtQYC2cJ5yJRi9VDkpsYZXzYdwYpGnLmtDL"),
    Pubkey.from_string("3BpXnfJaUTiwXnJNe7Ej1rcbzqTTQUvLShZaWazebsVR"),
    Pubkey.from_string("5cjcW9wExnJJiqgLjq7DEG75Pm6JBgE1hNv4B2vHXUW6"),
    Pubkey.from_string("EHAAiTxcdDwQ3U4bU6YcMsQGaekdzLS3B5SmYo46kJtL"),
    Pubkey.from_string("5eHhjP8JaYkz83CWwvGU2uMUXefd3AazWGx4gpcuEEYD"),
    Pubkey.from_string("A7hAgCzFw14fejgCp387JUJRMNyz4j89JKnhtKU8piqW"),
]

# pump.fun API
PUMPFUN_API_BASE = "https://pump.fun/api"
IPFS_UPLOAD_URL = "https://pump.fun/api/ipfs"


@dataclass
class TokenMetadata:
    """Token metadata for pump.fun"""
    name: str
    symbol: str
    description: str
    image_url: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    website: Optional[str] = None


@dataclass
class BondingCurveState:
    """Bonding curve account state"""
    virtual_token_reserves: int
    virtual_quote_reserves: int
    real_token_reserves: int
    real_quote_reserves: int
    token_total_supply: int
    complete: bool
    creator: Pubkey
    is_mayhem_mode: bool
    is_cashback_coin: bool = False
    quote_mint: Pubkey = NATIVE_MINT

    @property
    def virtual_sol_reserves(self) -> int:
        return self.virtual_quote_reserves

    @property
    def real_sol_reserves(self) -> int:
        return self.real_quote_reserves


@dataclass
class GlobalState:
    """Global account state needed for buy_v2/sell_v2."""
    fee_recipient: Pubkey
    fee_recipients: list[Pubkey]
    reserved_fee_recipient: Pubkey
    reserved_fee_recipients: list[Pubkey]
    buyback_fee_recipients: list[Pubkey]
    fee_basis_points: int
    creator_fee_basis_points: int
    initial_virtual_token_reserves: int
    initial_virtual_quote_reserves: int
    token_total_supply: int


@dataclass
class FeeTier:
    market_cap_lamports_threshold: int
    protocol_fee_bps: int
    creator_fee_bps: int


@dataclass
class FeeConfigState:
    fee_tiers: list[FeeTier]


@dataclass
class CreateTokenResult:
    """Result of token creation"""
    mint: Pubkey
    bonding_curve: Pubkey
    signature: str
    token_url: str


class PumpFunClient:
    """Client for pump.fun token launches and trading"""

    def __init__(
        self,
        rpc_url: str,
        private_key: Optional[str] = None,
    ):
        """
        Initialize PumpFun client.

        Args:
            rpc_url: Solana RPC URL
            private_key: Wallet private key (base58 encoded)
        """
        self.rpc_url = rpc_url
        self.keypair = None

        if private_key:
            try:
                secret_bytes = base58.b58decode(private_key)
                self.keypair = Keypair.from_bytes(secret_bytes)
            except Exception as e:
                raise ValueError(f"Invalid private key: {e}")

        self._http_client = httpx.AsyncClient(timeout=60.0)
        self._rpc_client = httpx.AsyncClient(
            headers={"Content-Type": "application/json"},
            timeout=60.0
        )

    @property
    def wallet_pubkey(self) -> Optional[Pubkey]:
        """Get wallet public key"""
        if self.keypair:
            return self.keypair.pubkey()
        return None

    # ===================
    # PDA Derivations
    # ===================

    def get_mint_authority_pda(self) -> Pubkey:
        """Derive mint authority PDA"""
        seeds = [b"mint-authority"]
        pda, _ = Pubkey.find_program_address(seeds, PUMP_PROGRAM_ID)
        return pda

    def get_bonding_curve_pda(self, mint: Pubkey) -> Pubkey:
        """Derive bonding curve PDA for a mint"""
        seeds = [b"bonding-curve", bytes(mint)]
        pda, _ = Pubkey.find_program_address(seeds, PUMP_PROGRAM_ID)
        return pda

    def get_metadata_pda(self, mint: Pubkey) -> Pubkey:
        """Derive metadata PDA for a mint"""
        seeds = [b"metadata", bytes(METAPLEX_PROGRAM_ID), bytes(mint)]
        pda, _ = Pubkey.find_program_address(seeds, METAPLEX_PROGRAM_ID)
        return pda

    def get_event_authority_pda(self) -> Pubkey:
        """Derive event authority PDA"""
        seeds = [b"__event_authority"]
        pda, _ = Pubkey.find_program_address(seeds, PUMP_PROGRAM_ID)
        return pda

    def get_mayhem_state_pda(self, mint: Pubkey) -> Pubkey:
        """Derive mayhem state PDA for create_v2"""
        seeds = [b"mayhem-state", bytes(mint)]
        pda, _ = Pubkey.find_program_address(seeds, MAYHEM_PROGRAM_ID)
        return pda

    def get_associated_token_address(
        self,
        owner: Pubkey,
        mint: Pubkey,
        token_program: Pubkey = TOKEN_PROGRAM_ID
    ) -> Pubkey:
        """Get associated token address"""
        seeds = [bytes(owner), bytes(token_program), bytes(mint)]
        pda, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
        return pda

    # ===================
    # RPC Methods
    # ===================

    async def _rpc_request(self, method: str, params: list) -> dict:
        """Make RPC request"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        response = await self._rpc_client.post(self.rpc_url, json=payload)
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise Exception(f"RPC error: {result['error']}")
        return result.get("result")

    async def get_latest_blockhash(self) -> Hash:
        """Get latest blockhash"""
        result = await self._rpc_request("getLatestBlockhash", [{"commitment": "confirmed"}])
        return Hash.from_string(result["value"]["blockhash"])

    async def get_account_info(self, pubkey: Pubkey) -> Optional[dict]:
        """Get account info"""
        result = await self._rpc_request(
            "getAccountInfo",
            [str(pubkey), {"encoding": "base64", "commitment": "confirmed"}]
        )
        return result.get("value")

    async def _get_account_data(self, pubkey: Pubkey) -> Optional[bytes]:
        """Fetch and decode account data."""
        account_info = await self.get_account_info(pubkey)
        if not account_info or not account_info.get("data"):
            return None

        import base64
        return base64.b64decode(account_info["data"][0])

    async def get_mint_token_program(self, mint: Pubkey) -> Pubkey:
        """Return the token program (legacy SPL or Token2022) that owns this mint.

        For create_v2 / Mayhem coins the mint is owned by the Token2022 program;
        legacy pump.fun coins use the original SPL Token program.
        """
        info = await self.get_account_info(mint)
        if info and info.get("owner"):
            owner = Pubkey.from_string(info["owner"])
            if owner == TOKEN_2022_PROGRAM_ID:
                return TOKEN_2022_PROGRAM_ID
        return TOKEN_PROGRAM_ID

    async def get_quote_token_program(self, quote_mint: Pubkey) -> Pubkey:
        """Return the token program for the quote mint."""
        if quote_mint == NATIVE_MINT or quote_mint == Pubkey.default():
            return TOKEN_PROGRAM_ID
        return await self.get_mint_token_program(quote_mint)

    def pick_mayhem_fee_recipient(self, mint: Optional[Pubkey] = None) -> Pubkey:
        """Pick a Mayhem fee recipient. Deterministic per-mint when provided,
        round-robin via mint bytes; falls back to the first recipient otherwise.
        """
        if mint is None:
            return MAYHEM_FEE_RECIPIENTS[0]
        idx = bytes(mint)[0] % len(MAYHEM_FEE_RECIPIENTS)
        return MAYHEM_FEE_RECIPIENTS[idx]

    def pick_fee_recipient(self, global_state: Optional[GlobalState], is_mayhem_mode: bool) -> Pubkey:
        """Pick a current fee recipient matching official SDK behavior."""
        if global_state:
            fee_recipients = (
                [global_state.reserved_fee_recipient, *global_state.reserved_fee_recipients]
                if is_mayhem_mode
                else [global_state.fee_recipient, *global_state.fee_recipients]
            )
            return random.choice(fee_recipients)

        return (
            random.choice(MAYHEM_FEE_RECIPIENTS)
            if is_mayhem_mode
            else random.choice(CURRENT_FEE_RECIPIENTS)
        )

    def pick_buyback_fee_recipient(self, global_state: Optional[GlobalState]) -> Pubkey:
        """Pick a buyback fee recipient matching official SDK behavior."""
        recipients = (
            global_state.buyback_fee_recipients
            if global_state and global_state.buyback_fee_recipients
            else CURRENT_BUYBACK_FEE_RECIPIENTS
        )
        return random.choice(recipients)

    async def send_transaction(self, tx: VersionedTransaction) -> str:
        """Send and confirm transaction"""
        tx_bytes = bytes(tx)
        tx_base64 = base58.b58encode(tx_bytes).decode()

        result = await self._rpc_request(
            "sendTransaction",
            [tx_base64, {"encoding": "base58", "skipPreflight": False}]
        )
        return result

    async def get_bonding_curve_state(self, mint: Pubkey) -> Optional[BondingCurveState]:
        """Get bonding curve state for a mint"""
        bonding_curve = self.get_bonding_curve_pda(mint)
        data = await self._get_account_data(bonding_curve)
        if not data:
            return None

        # Skip 8-byte discriminator
        data = data[8:]

        # Current struct layout:
        # u64,u64,u64,u64,u64,bool,pubkey,bool,bool,pubkey
        if len(data) < 115:
            return None

        virtual_token_reserves = struct.unpack("<Q", data[0:8])[0]
        virtual_quote_reserves = struct.unpack("<Q", data[8:16])[0]
        real_token_reserves = struct.unpack("<Q", data[16:24])[0]
        real_quote_reserves = struct.unpack("<Q", data[24:32])[0]
        token_total_supply = struct.unpack("<Q", data[32:40])[0]
        complete = data[40] == 1
        creator = Pubkey.from_bytes(data[41:73])
        is_mayhem_mode = data[73] == 1 if len(data) > 73 else False
        is_cashback_coin = data[74] == 1 if len(data) > 74 else False
        quote_mint = Pubkey.from_bytes(data[75:107]) if len(data) >= 107 else NATIVE_MINT
        if quote_mint == Pubkey.default():
            quote_mint = NATIVE_MINT

        return BondingCurveState(
            virtual_token_reserves=virtual_token_reserves,
            virtual_quote_reserves=virtual_quote_reserves,
            real_token_reserves=real_token_reserves,
            real_quote_reserves=real_quote_reserves,
            token_total_supply=token_total_supply,
            complete=complete,
            creator=creator,
            is_mayhem_mode=is_mayhem_mode,
            is_cashback_coin=is_cashback_coin,
            quote_mint=quote_mint,
        )

    async def get_global_state(self) -> Optional[GlobalState]:
        """Fetch and parse the Pump global account."""
        data = await self._get_account_data(PUMP_GLOBAL)
        if not data:
            return None

        buf = memoryview(data)[8:]
        offset = 0

        def read_u64() -> int:
            nonlocal offset
            value = struct.unpack_from("<Q", buf, offset)[0]
            offset += 8
            return value

        def read_bool() -> bool:
            nonlocal offset
            value = buf[offset] == 1
            offset += 1
            return value

        def read_pubkey() -> Pubkey:
            nonlocal offset
            value = Pubkey.from_bytes(bytes(buf[offset:offset + 32]))
            offset += 32
            return value

        def read_pubkeys(count: int) -> list[Pubkey]:
            return [read_pubkey() for _ in range(count)]

        _initialized = read_bool()
        _authority = read_pubkey()
        fee_recipient = read_pubkey()
        initial_virtual_token_reserves = read_u64()
        _initial_virtual_sol_reserves = read_u64()
        _initial_real_token_reserves = read_u64()
        token_total_supply = read_u64()
        fee_basis_points = read_u64()
        _withdraw_authority = read_pubkey()
        _enable_migrate = read_bool()
        _pool_migration_fee = read_u64()
        creator_fee_basis_points = read_u64()
        fee_recipients = read_pubkeys(7)
        _set_creator_authority = read_pubkey()
        _admin_set_creator_authority = read_pubkey()
        _create_v2_enabled = read_bool()
        _whitelist_pda = read_pubkey()
        reserved_fee_recipient = read_pubkey()
        _mayhem_mode_enabled = read_bool()
        reserved_fee_recipients = read_pubkeys(7)
        _is_cashback_enabled = read_bool()
        buyback_fee_recipients = read_pubkeys(8)
        _buyback_basis_points = read_u64()
        initial_virtual_quote_reserves = read_u64()

        # Current official SDK exposes one whitelisted quote mint slot.
        if len(buf) >= offset + 32:
            _whitelisted_quote_mint = read_pubkey()

        return GlobalState(
            fee_recipient=fee_recipient,
            fee_recipients=fee_recipients,
            reserved_fee_recipient=reserved_fee_recipient,
            reserved_fee_recipients=reserved_fee_recipients,
            buyback_fee_recipients=buyback_fee_recipients,
            fee_basis_points=fee_basis_points,
            creator_fee_basis_points=creator_fee_basis_points,
            initial_virtual_token_reserves=initial_virtual_token_reserves,
            initial_virtual_quote_reserves=initial_virtual_quote_reserves,
            token_total_supply=token_total_supply,
        )

    async def get_fee_config_state(self) -> Optional[FeeConfigState]:
        """Fetch and parse the fee-config PDA."""
        fee_config_pda, _ = Pubkey.find_program_address(
            [b"fee_config", bytes(PUMP_PROGRAM_ID)],
            PUMP_FEES_PROGRAM_ID,
        )
        data = await self._get_account_data(fee_config_pda)
        if not data:
            return None

        buf = memoryview(data)[8:]
        offset = 0

        def read_u8() -> int:
            nonlocal offset
            value = buf[offset]
            offset += 1
            return value

        def read_u32() -> int:
            nonlocal offset
            value = struct.unpack_from("<I", buf, offset)[0]
            offset += 4
            return value

        def read_u64() -> int:
            nonlocal offset
            value = struct.unpack_from("<Q", buf, offset)[0]
            offset += 8
            return value

        def read_u128() -> int:
            nonlocal offset
            value = int.from_bytes(bytes(buf[offset:offset + 16]), "little")
            offset += 16
            return value

        offset += 1  # bump
        offset += 32  # admin

        # flat_fees
        _flat_lp_fee_bps = read_u64()
        _flat_protocol_fee_bps = read_u64()
        _flat_creator_fee_bps = read_u64()

        fee_tier_count = read_u32()
        fee_tiers: list[FeeTier] = []
        for _ in range(fee_tier_count):
            threshold = read_u128()
            _lp_fee_bps = read_u64()
            protocol_fee_bps = read_u64()
            creator_fee_bps = read_u64()
            fee_tiers.append(
                FeeTier(
                    market_cap_lamports_threshold=threshold,
                    protocol_fee_bps=protocol_fee_bps,
                    creator_fee_bps=creator_fee_bps,
                )
            )

        return FeeConfigState(fee_tiers=fee_tiers)

    # ===================
    # Metadata Upload
    # ===================

    async def upload_metadata(
        self,
        metadata: TokenMetadata,
        image_path: Optional[str] = None,
    ) -> str:
        """
        Upload token metadata to pump.fun IPFS.

        Args:
            metadata: Token metadata
            image_path: Path to local image file (optional)

        Returns:
            IPFS URI for metadata
        """
        # If we have a local image, upload it first
        if image_path:
            image_url = await self._upload_image(image_path)
            metadata.image_url = image_url

        # Build metadata JSON
        metadata_json = {
            "name": metadata.name,
            "symbol": metadata.symbol,
            "description": metadata.description,
        }

        if metadata.image_url:
            metadata_json["image"] = metadata.image_url
        if metadata.twitter:
            metadata_json["twitter"] = metadata.twitter
        if metadata.telegram:
            metadata_json["telegram"] = metadata.telegram
        if metadata.website:
            metadata_json["website"] = metadata.website

        # Upload to pump.fun IPFS
        response = await self._http_client.post(
            IPFS_UPLOAD_URL,
            json=metadata_json,
        )
        response.raise_for_status()
        result = response.json()

        return result.get("metadataUri", result.get("uri"))

    async def _upload_image(self, image_path: str) -> str:
        """Upload image to pump.fun"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine mime type
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(path.suffix.lower(), "application/octet-stream")

        with open(path, "rb") as f:
            files = {"file": (path.name, f, mime_type)}
            response = await self._http_client.post(
                f"{PUMPFUN_API_BASE}/ipfs",
                files=files,
            )

        response.raise_for_status()
        result = response.json()
        return result.get("imageUri", result.get("uri"))

    # ===================
    # Token Creation
    # ===================

    async def create_token(
        self,
        name: str,
        symbol: str,
        description: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        twitter: Optional[str] = None,
        telegram: Optional[str] = None,
        website: Optional[str] = None,
        initial_buy_sol: float = 0.0,
    ) -> CreateTokenResult:
        """
        Create a new token on pump.fun.

        Args:
            name: Token name
            symbol: Token symbol (ticker)
            description: Token description
            image_url: URL to token image
            image_path: Path to local image file (alternative to image_url)
            twitter: Twitter URL
            telegram: Telegram URL
            website: Website URL
            initial_buy_sol: Initial buy amount in SOL (0 = no initial buy)

        Returns:
            CreateTokenResult with mint, bonding curve, and signature
        """
        if not self.keypair:
            raise ValueError("Keypair required for token creation")

        # Create metadata
        metadata = TokenMetadata(
            name=name,
            symbol=symbol.upper().replace("$", ""),
            description=description,
            image_url=image_url,
            twitter=twitter,
            telegram=telegram,
            website=website,
        )

        # Upload metadata
        metadata_uri = await self.upload_metadata(metadata, image_path)

        # Generate mint keypair
        mint_keypair = Keypair()
        mint = mint_keypair.pubkey()

        # Derive PDAs
        mint_authority = self.get_mint_authority_pda()
        bonding_curve = self.get_bonding_curve_pda(mint)
        associated_bonding_curve = self.get_associated_token_address(bonding_curve, mint)
        metadata_pda = self.get_metadata_pda(mint)
        event_authority = self.get_event_authority_pda()

        # Build create instruction data
        name_bytes = name.encode("utf-8")
        symbol_bytes = symbol.upper().replace("$", "").encode("utf-8")
        uri_bytes = metadata_uri.encode("utf-8")

        # Serialize: discriminator + strings (each prefixed with 4-byte length)
        data = CREATE_DISCRIMINATOR
        data += struct.pack("<I", len(name_bytes)) + name_bytes
        data += struct.pack("<I", len(symbol_bytes)) + symbol_bytes
        data += struct.pack("<I", len(uri_bytes)) + uri_bytes

        # Build accounts
        accounts = [
            AccountMeta(mint, is_signer=True, is_writable=True),
            AccountMeta(mint_authority, is_signer=False, is_writable=False),
            AccountMeta(bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(associated_bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(PUMP_GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(METAPLEX_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(metadata_pda, is_signer=False, is_writable=True),
            AccountMeta(self.wallet_pubkey, is_signer=True, is_writable=True),
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(SYSVAR_RENT_ID, is_signer=False, is_writable=False),
            AccountMeta(event_authority, is_signer=False, is_writable=False),
            AccountMeta(PUMP_PROGRAM_ID, is_signer=False, is_writable=False),
        ]

        create_ix = Instruction(PUMP_PROGRAM_ID, data, accounts)

        # Build transaction
        blockhash = await self.get_latest_blockhash()

        instructions = [create_ix]

        # Add initial buy if requested
        if initial_buy_sol > 0:
            buy_ix = await self._build_buy_instruction(
                mint=mint,
                bonding_curve=bonding_curve,
                associated_bonding_curve=associated_bonding_curve,
                amount=int(initial_buy_sol * 1_000_000_000),  # Convert to lamports
                max_sol_cost=int(initial_buy_sol * 1.1 * 1_000_000_000),  # 10% slippage
            )
            instructions.append(buy_ix)

        message = MessageV0.try_compile(
            payer=self.wallet_pubkey,
            instructions=instructions,
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )

        tx = VersionedTransaction(message, [self.keypair, mint_keypair])

        # Send transaction
        signature = await self.send_transaction(tx)

        return CreateTokenResult(
            mint=mint,
            bonding_curve=bonding_curve,
            signature=signature,
            token_url=f"https://pump.fun/{mint}",
        )

    async def create_token_v2(
        self,
        name: str,
        symbol: str,
        description: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        twitter: Optional[str] = None,
        telegram: Optional[str] = None,
        website: Optional[str] = None,
        initial_buy_sol: float = 0.0,
        is_mayhem_mode: bool = False,
    ) -> CreateTokenResult:
        """Create a new token via the create_v2 instruction (Token2022 + Mayhem).

        Per pumpfun-docs/README.md (12:00 UTC, 11 Nov 2025): create_v2 mints
        the new SPL Token2022 token and hosts metadata via the Token2022
        program (replacing the legacy Metaplex flow). Set is_mayhem_mode=True
        to opt the coin into Mayhem mode at creation time.
        """
        if not self.keypair:
            raise ValueError("Keypair required for token creation")

        metadata = TokenMetadata(
            name=name,
            symbol=symbol.upper().replace("$", ""),
            description=description,
            image_url=image_url,
            twitter=twitter,
            telegram=telegram,
            website=website,
        )
        metadata_uri = await self.upload_metadata(metadata, image_path)

        mint_keypair = Keypair()
        mint = mint_keypair.pubkey()

        mint_authority = self.get_mint_authority_pda()
        bonding_curve = self.get_bonding_curve_pda(mint)
        # Token2022-owned ATA for the bonding curve
        associated_bonding_curve = self.get_associated_token_address(
            bonding_curve, mint, token_program=TOKEN_2022_PROGRAM_ID
        )
        event_authority = self.get_event_authority_pda()
        mayhem_state = self.get_mayhem_state_pda(mint)
        # Token2022 token account of the Mayhem sol vault
        mayhem_token_vault = self.get_associated_token_address(
            MAYHEM_SOL_VAULT, mint, token_program=TOKEN_2022_PROGRAM_ID
        )

        # Serialize: discriminator + name + symbol + uri + is_mayhem_mode (bool)
        name_bytes = name.encode("utf-8")
        symbol_bytes = metadata.symbol.encode("utf-8")
        uri_bytes = metadata_uri.encode("utf-8")
        data = CREATE_V2_DISCRIMINATOR
        data += struct.pack("<I", len(name_bytes)) + name_bytes
        data += struct.pack("<I", len(symbol_bytes)) + symbol_bytes
        data += struct.pack("<I", len(uri_bytes)) + uri_bytes
        data += struct.pack("<?", bool(is_mayhem_mode))

        # Account list per pumpfun-docs/README.md "create_v2" table:
        # 1 mint, 2 mint authority, 3 bonding curve, 4 associated bonding curve
        # (Token2022-owned), 5 global, 6 user, 7 system program, 8 token2022
        # program, 9 associated token program, 10 mayhem program, 11 global
        # params, 12 sol vault, 13 mayhem state, 14 mayhem token vault.
        accounts = [
            AccountMeta(mint, is_signer=True, is_writable=True),
            AccountMeta(mint_authority, is_signer=False, is_writable=False),
            AccountMeta(bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(associated_bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(PUMP_GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(self.wallet_pubkey, is_signer=True, is_writable=True),
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(TOKEN_2022_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(MAYHEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(MAYHEM_GLOBAL_PARAMS, is_signer=False, is_writable=False),
            AccountMeta(MAYHEM_SOL_VAULT, is_signer=False, is_writable=True),
            AccountMeta(mayhem_state, is_signer=False, is_writable=True),
            AccountMeta(mayhem_token_vault, is_signer=False, is_writable=True),
            AccountMeta(event_authority, is_signer=False, is_writable=False),
            AccountMeta(PUMP_PROGRAM_ID, is_signer=False, is_writable=False),
        ]

        create_ix = Instruction(PUMP_PROGRAM_ID, data, accounts)
        instructions = [create_ix]

        if initial_buy_sol > 0:
            fee_recipient = (
                self.pick_mayhem_fee_recipient(mint)
                if is_mayhem_mode else PUMP_FEE_RECIPIENT
            )
            buy_ix = await self._build_buy_instruction(
                mint=mint,
                bonding_curve=bonding_curve,
                associated_bonding_curve=associated_bonding_curve,
                amount=int(initial_buy_sol * 1_000_000_000),
                max_sol_cost=int(initial_buy_sol * 1.1 * 1_000_000_000),
                token_program=TOKEN_2022_PROGRAM_ID,
                fee_recipient=fee_recipient,
            )
            instructions.append(buy_ix)

        blockhash = await self.get_latest_blockhash()
        message = MessageV0.try_compile(
            payer=self.wallet_pubkey,
            instructions=instructions,
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )
        tx = VersionedTransaction(message, [self.keypair, mint_keypair])
        signature = await self.send_transaction(tx)

        return CreateTokenResult(
            mint=mint,
            bonding_curve=bonding_curve,
            signature=signature,
            token_url=f"https://pump.fun/{mint}",
        )

    # ===================
    # Trading
    # ===================

    async def _build_buy_instruction(
        self,
        mint: Pubkey,
        bonding_curve: Pubkey,
        associated_bonding_curve: Pubkey,
        amount: int,
        max_sol_cost: int,
        token_program: Pubkey = TOKEN_PROGRAM_ID,
        fee_recipient: Pubkey = PUMP_FEE_RECIPIENT,
    ) -> Instruction:
        """Build buy instruction.

        For mayhem-mode coins (is_mayhem_mode=true) pass a Mayhem fee recipient
        as account index 1 (see pumpfun-docs/README.md). For coins owned by
        Token2022, pass TOKEN_2022_PROGRAM_ID and derive the user ATA accordingly.
        """
        user_token_account = self.get_associated_token_address(
            self.wallet_pubkey, mint, token_program=token_program
        )

        # Serialize data: discriminator + amount (u64) + max_sol_cost (u64)
        data = BUY_DISCRIMINATOR
        data += struct.pack("<Q", amount)
        data += struct.pack("<Q", max_sol_cost)

        accounts = [
            AccountMeta(PUMP_GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(fee_recipient, is_signer=False, is_writable=True),
            AccountMeta(mint, is_signer=False, is_writable=False),
            AccountMeta(bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(associated_bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(user_token_account, is_signer=False, is_writable=True),
            AccountMeta(self.wallet_pubkey, is_signer=True, is_writable=True),
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(token_program, is_signer=False, is_writable=False),
            AccountMeta(SYSVAR_RENT_ID, is_signer=False, is_writable=False),
            AccountMeta(self.get_event_authority_pda(), is_signer=False, is_writable=False),
            AccountMeta(PUMP_PROGRAM_ID, is_signer=False, is_writable=False),
        ]

        return Instruction(PUMP_PROGRAM_ID, data, accounts)

    async def buy(
        self,
        mint: Pubkey,
        sol_amount: float,
        slippage_bps: int = 500,
    ) -> str:
        """
        Buy tokens from a pump.fun bonding curve.

        Args:
            mint: Token mint address
            sol_amount: Amount of SOL to spend
            slippage_bps: Slippage tolerance in basis points (default 5%)

        Returns:
            Transaction signature
        """
        if not self.keypair:
            raise ValueError("Keypair required for trading")

        state = await self.get_bonding_curve_state(mint)
        if not state:
            raise ValueError(f"Bonding curve not found for {mint}")
        if state.complete:
            raise ValueError("Bonding curve is complete - trade on PumpSwap instead")

        global_state = await self.get_global_state()
        fee_config = await self.get_fee_config_state()

        quote_amount = int(sol_amount * 1_000_000_000)
        tokens_out = self._get_buy_token_amount_from_quote_amount(
            global_state=global_state,
            fee_config=fee_config,
            state=state,
            quote_amount=quote_amount,
        )
        if tokens_out <= 0:
            raise ValueError("Calculated token output is zero")

        max_quote_cost = int(quote_amount * (1 + slippage_bps / 10000))
        token_program = await self.get_mint_token_program(mint)
        quote_mint = state.quote_mint
        quote_token_program = TOKEN_PROGRAM_ID
        fee_recipient = self.pick_fee_recipient(global_state, state.is_mayhem_mode)
        buyback_fee_recipient = self.pick_buyback_fee_recipient(global_state)

        buy_ix = self._build_buy_v2_instruction(
            mint=mint,
            creator=state.creator,
            amount=tokens_out,
            max_quote_cost=max_quote_cost,
            token_program=token_program,
            quote_mint=quote_mint,
            quote_token_program=quote_token_program,
            fee_recipient=fee_recipient,
            buyback_fee_recipient=buyback_fee_recipient,
        )

        blockhash = await self.get_latest_blockhash()
        message = MessageV0.try_compile(
            payer=self.wallet_pubkey,
            instructions=[buy_ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )

        tx = VersionedTransaction(message, [self.keypair])
        return await self.send_transaction(tx)

    async def buy_v2(
        self,
        mint: Pubkey,
        base_amount: int,
        max_quote_cost: int,
        quote_mint: Optional[Pubkey] = None,
        quote_token_program: Optional[Pubkey] = None,
        fee_recipient: Optional[Pubkey] = None,
        buyback_fee_recipient: Optional[Pubkey] = None,
    ) -> str:
        """Execute a raw buy_v2 using exact base token output + quote slippage cap."""
        if not self.keypair:
            raise ValueError("Keypair required for trading")

        state = await self.get_bonding_curve_state(mint)
        if not state:
            raise ValueError(f"Bonding curve not found for {mint}")
        if state.complete:
            raise ValueError("Bonding curve is complete - trade on PumpSwap instead")
        if base_amount <= 0:
            raise ValueError("base_amount must be > 0")

        global_state = await self.get_global_state()
        token_program = await self.get_mint_token_program(mint)
        resolved_quote_mint = quote_mint or state.quote_mint
        resolved_quote_token_program = quote_token_program or await self.get_quote_token_program(resolved_quote_mint)
        resolved_fee_recipient = fee_recipient or self.pick_fee_recipient(global_state, state.is_mayhem_mode)
        resolved_buyback_fee_recipient = buyback_fee_recipient or self.pick_buyback_fee_recipient(global_state)

        ix = self._build_buy_v2_instruction(
            mint=mint,
            creator=state.creator,
            amount=base_amount,
            max_quote_cost=max_quote_cost,
            token_program=token_program,
            quote_mint=resolved_quote_mint,
            quote_token_program=resolved_quote_token_program,
            fee_recipient=resolved_fee_recipient,
            buyback_fee_recipient=resolved_buyback_fee_recipient,
        )
        blockhash = await self.get_latest_blockhash()
        message = MessageV0.try_compile(
            payer=self.wallet_pubkey,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )
        tx = VersionedTransaction(message, [self.keypair])
        return await self.send_transaction(tx)

    async def sell(
        self,
        mint: Pubkey,
        token_amount: int,
        slippage_bps: int = 500,
    ) -> str:
        """
        Sell tokens to a pump.fun bonding curve.

        Args:
            mint: Token mint address
            token_amount: Amount of tokens to sell (in smallest unit)
            slippage_bps: Slippage tolerance in basis points (default 5%)

        Returns:
            Transaction signature
        """
        if not self.keypair:
            raise ValueError("Keypair required for trading")

        state = await self.get_bonding_curve_state(mint)
        if not state:
            raise ValueError(f"Bonding curve not found for {mint}")
        if state.complete:
            raise ValueError("Bonding curve is complete - trade on PumpSwap instead")

        global_state = await self.get_global_state()
        fee_config = await self.get_fee_config_state()

        quote_amount = self._get_sell_quote_amount_from_token_amount(
            global_state=global_state,
            fee_config=fee_config,
            state=state,
            token_amount=token_amount,
        )
        min_quote_output = max(1, int(quote_amount * (1 - slippage_bps / 10000)))
        token_program = await self.get_mint_token_program(mint)
        quote_mint = state.quote_mint
        quote_token_program = TOKEN_PROGRAM_ID
        fee_recipient = self.pick_fee_recipient(global_state, state.is_mayhem_mode)
        buyback_fee_recipient = self.pick_buyback_fee_recipient(global_state)

        sell_ix = self._build_sell_v2_instruction(
            mint=mint,
            creator=state.creator,
            amount=token_amount,
            min_quote_output=min_quote_output,
            token_program=token_program,
            quote_mint=quote_mint,
            quote_token_program=quote_token_program,
            fee_recipient=fee_recipient,
            buyback_fee_recipient=buyback_fee_recipient,
        )

        blockhash = await self.get_latest_blockhash()
        message = MessageV0.try_compile(
            payer=self.wallet_pubkey,
            instructions=[sell_ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )

        tx = VersionedTransaction(message, [self.keypair])
        return await self.send_transaction(tx)

    async def sell_v2(
        self,
        mint: Pubkey,
        token_amount: int,
        min_quote_output: int,
        quote_mint: Optional[Pubkey] = None,
        quote_token_program: Optional[Pubkey] = None,
        fee_recipient: Optional[Pubkey] = None,
        buyback_fee_recipient: Optional[Pubkey] = None,
    ) -> str:
        """Execute a raw sell_v2 using exact base token input + quote floor."""
        if not self.keypair:
            raise ValueError("Keypair required for trading")

        state = await self.get_bonding_curve_state(mint)
        if not state:
            raise ValueError(f"Bonding curve not found for {mint}")
        if state.complete:
            raise ValueError("Bonding curve is complete - trade on PumpSwap instead")
        if token_amount <= 0:
            raise ValueError("token_amount must be > 0")

        global_state = await self.get_global_state()
        token_program = await self.get_mint_token_program(mint)
        resolved_quote_mint = quote_mint or state.quote_mint
        resolved_quote_token_program = quote_token_program or await self.get_quote_token_program(resolved_quote_mint)
        resolved_fee_recipient = fee_recipient or self.pick_fee_recipient(global_state, state.is_mayhem_mode)
        resolved_buyback_fee_recipient = buyback_fee_recipient or self.pick_buyback_fee_recipient(global_state)

        ix = self._build_sell_v2_instruction(
            mint=mint,
            creator=state.creator,
            amount=token_amount,
            min_quote_output=min_quote_output,
            token_program=token_program,
            quote_mint=resolved_quote_mint,
            quote_token_program=resolved_quote_token_program,
            fee_recipient=resolved_fee_recipient,
            buyback_fee_recipient=resolved_buyback_fee_recipient,
        )
        blockhash = await self.get_latest_blockhash()
        message = MessageV0.try_compile(
            payer=self.wallet_pubkey,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )
        tx = VersionedTransaction(message, [self.keypair])
        return await self.send_transaction(tx)

    # ===================
    # Utility Methods
    # ===================

    def _ceil_div(self, a: int, b: int) -> int:
        return (a + b - 1) // b

    def _compute_fees_bps(
        self,
        global_state: Optional[GlobalState],
        fee_config: Optional[FeeConfigState],
        mint_supply: int,
        virtual_quote_reserves: int,
        virtual_token_reserves: int,
    ) -> tuple[int, int]:
        if fee_config and fee_config.fee_tiers:
            market_cap = (virtual_quote_reserves * mint_supply) // max(virtual_token_reserves, 1)
            for tier in reversed(fee_config.fee_tiers):
                if market_cap >= tier.market_cap_lamports_threshold:
                    return tier.protocol_fee_bps, tier.creator_fee_bps
            first = fee_config.fee_tiers[0]
            return first.protocol_fee_bps, first.creator_fee_bps

        if global_state is None:
            return 100, 0

        return global_state.fee_basis_points, global_state.creator_fee_basis_points

    def _get_fee_amount(
        self,
        global_state: Optional[GlobalState],
        fee_config: Optional[FeeConfigState],
        state: BondingCurveState,
        amount: int,
    ) -> int:
        protocol_fee_bps, creator_fee_bps = self._compute_fees_bps(
            global_state=global_state,
            fee_config=fee_config,
            mint_supply=state.token_total_supply,
            virtual_quote_reserves=state.virtual_quote_reserves,
            virtual_token_reserves=state.virtual_token_reserves,
        )
        total = self._ceil_div(amount * protocol_fee_bps, 10_000)
        if state.creator != Pubkey.default():
            total += self._ceil_div(amount * creator_fee_bps, 10_000)
        return total

    def _get_buy_token_amount_from_quote_amount(
        self,
        global_state: Optional[GlobalState],
        fee_config: Optional[FeeConfigState],
        state: BondingCurveState,
        quote_amount: int,
    ) -> int:
        if quote_amount <= 0 or state.virtual_token_reserves <= 0:
            return 0

        protocol_fee_bps, creator_fee_bps = self._compute_fees_bps(
            global_state=global_state,
            fee_config=fee_config,
            mint_supply=state.token_total_supply,
            virtual_quote_reserves=state.virtual_quote_reserves,
            virtual_token_reserves=state.virtual_token_reserves,
        )
        total_fee_bps = protocol_fee_bps + (creator_fee_bps if state.creator != Pubkey.default() else 0)
        input_amount = ((quote_amount - 1) * 10_000) // (10_000 + total_fee_bps)
        tokens_received = (
            input_amount * state.virtual_token_reserves
        ) // (state.virtual_quote_reserves + input_amount)
        return min(tokens_received, state.real_token_reserves)

    def _get_buy_quote_amount_from_base_amount(
        self,
        global_state: Optional[GlobalState],
        fee_config: Optional[FeeConfigState],
        state: BondingCurveState,
        base_amount: int,
    ) -> int:
        if base_amount <= 0:
            return 0

        min_amount = min(base_amount, state.real_token_reserves)
        net_quote_cost = self._ceil_div(
            min_amount * state.virtual_quote_reserves,
            max(state.virtual_token_reserves - min_amount, 1),
        ) + 1
        return net_quote_cost + self._get_fee_amount(
            global_state=global_state,
            fee_config=fee_config,
            state=state,
            amount=net_quote_cost,
        )

    def _get_sell_quote_amount_from_token_amount(
        self,
        global_state: Optional[GlobalState],
        fee_config: Optional[FeeConfigState],
        state: BondingCurveState,
        token_amount: int,
    ) -> int:
        if token_amount <= 0 or state.virtual_token_reserves <= 0:
            return 0

        gross_quote = (
            token_amount * state.virtual_quote_reserves
        ) // (state.virtual_token_reserves + token_amount)
        return gross_quote - self._get_fee_amount(
            global_state=global_state,
            fee_config=fee_config,
            state=state,
            amount=gross_quote,
        )

    def get_creator_vault_pda(self, creator: Pubkey) -> Pubkey:
        """Derive creator-vault PDA."""
        pda, _ = Pubkey.find_program_address([b"creator-vault", bytes(creator)], PUMP_PROGRAM_ID)
        return pda

    def get_global_volume_accumulator_pda(self) -> Pubkey:
        """Derive global volume accumulator PDA."""
        pda, _ = Pubkey.find_program_address([b"global_volume_accumulator"], PUMP_PROGRAM_ID)
        return pda

    def get_user_volume_accumulator_pda(self, user: Pubkey) -> Pubkey:
        """Derive user volume accumulator PDA."""
        pda, _ = Pubkey.find_program_address([b"user_volume_accumulator", bytes(user)], PUMP_PROGRAM_ID)
        return pda

    def get_sharing_config_pda(self, mint: Pubkey) -> Pubkey:
        """Derive sharing-config PDA."""
        pda, _ = Pubkey.find_program_address([b"sharing-config", bytes(mint)], PUMP_FEES_PROGRAM_ID)
        return pda

    def get_fee_config_pda(self) -> Pubkey:
        """Derive fee-config PDA."""
        pda, _ = Pubkey.find_program_address([b"fee_config", bytes(PUMP_PROGRAM_ID)], PUMP_FEES_PROGRAM_ID)
        return pda

    def _build_buy_v2_instruction(
        self,
        mint: Pubkey,
        creator: Pubkey,
        amount: int,
        max_quote_cost: int,
        token_program: Pubkey,
        quote_mint: Pubkey,
        quote_token_program: Pubkey,
        fee_recipient: Pubkey,
        buyback_fee_recipient: Pubkey,
    ) -> Instruction:
        bonding_curve = self.get_bonding_curve_pda(mint)
        creator_vault = self.get_creator_vault_pda(creator)
        user_volume_accumulator = self.get_user_volume_accumulator_pda(self.wallet_pubkey)
        data = BUY_V2_DISCRIMINATOR + struct.pack("<Q", amount) + struct.pack("<Q", max_quote_cost)

        accounts = [
            AccountMeta(PUMP_GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(mint, is_signer=False, is_writable=False),
            AccountMeta(quote_mint, is_signer=False, is_writable=False),
            AccountMeta(token_program, is_signer=False, is_writable=False),
            AccountMeta(quote_token_program, is_signer=False, is_writable=False),
            AccountMeta(ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(fee_recipient, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(fee_recipient, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(buyback_fee_recipient, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(buyback_fee_recipient, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(bonding_curve, mint, token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(bonding_curve, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(self.wallet_pubkey, is_signer=True, is_writable=True),
            AccountMeta(self.get_associated_token_address(self.wallet_pubkey, mint, token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(self.wallet_pubkey, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(creator_vault, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(creator_vault, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_sharing_config_pda(mint), is_signer=False, is_writable=False),
            AccountMeta(self.get_global_volume_accumulator_pda(), is_signer=False, is_writable=False),
            AccountMeta(user_volume_accumulator, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(user_volume_accumulator, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_fee_config_pda(), is_signer=False, is_writable=False),
            AccountMeta(PUMP_FEES_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(self.get_event_authority_pda(), is_signer=False, is_writable=False),
            AccountMeta(PUMP_PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        return Instruction(PUMP_PROGRAM_ID, data, accounts)

    def _build_sell_v2_instruction(
        self,
        mint: Pubkey,
        creator: Pubkey,
        amount: int,
        min_quote_output: int,
        token_program: Pubkey,
        quote_mint: Pubkey,
        quote_token_program: Pubkey,
        fee_recipient: Pubkey,
        buyback_fee_recipient: Pubkey,
    ) -> Instruction:
        bonding_curve = self.get_bonding_curve_pda(mint)
        creator_vault = self.get_creator_vault_pda(creator)
        user_volume_accumulator = self.get_user_volume_accumulator_pda(self.wallet_pubkey)
        data = SELL_V2_DISCRIMINATOR + struct.pack("<Q", amount) + struct.pack("<Q", min_quote_output)

        accounts = [
            AccountMeta(PUMP_GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(mint, is_signer=False, is_writable=False),
            AccountMeta(quote_mint, is_signer=False, is_writable=False),
            AccountMeta(token_program, is_signer=False, is_writable=False),
            AccountMeta(quote_token_program, is_signer=False, is_writable=False),
            AccountMeta(ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(fee_recipient, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(fee_recipient, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(buyback_fee_recipient, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(buyback_fee_recipient, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(bonding_curve, mint, token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(bonding_curve, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(self.wallet_pubkey, is_signer=True, is_writable=True),
            AccountMeta(self.get_associated_token_address(self.wallet_pubkey, mint, token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(self.wallet_pubkey, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(creator_vault, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(creator_vault, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_sharing_config_pda(mint), is_signer=False, is_writable=False),
            AccountMeta(user_volume_accumulator, is_signer=False, is_writable=True),
            AccountMeta(self.get_associated_token_address(user_volume_accumulator, quote_mint, quote_token_program), is_signer=False, is_writable=True),
            AccountMeta(self.get_fee_config_pda(), is_signer=False, is_writable=False),
            AccountMeta(PUMP_FEES_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(self.get_event_authority_pda(), is_signer=False, is_writable=False),
            AccountMeta(PUMP_PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        return Instruction(PUMP_PROGRAM_ID, data, accounts)

    async def get_buy_v2_quote(
        self,
        mint: Pubkey,
        *,
        quote_amount: Optional[int] = None,
        base_amount: Optional[int] = None,
        quote_mint: Optional[Pubkey] = None,
    ) -> dict:
        """Preview buy_v2 quote details without executing."""
        state = await self.get_bonding_curve_state(mint)
        if not state:
            raise ValueError(f"Bonding curve not found for {mint}")
        if state.complete:
            raise ValueError("Bonding curve is complete - trade on PumpSwap instead")
        if quote_amount is None and base_amount is None:
            raise ValueError("Provide quote_amount or base_amount")

        global_state = await self.get_global_state()
        fee_config = await self.get_fee_config_state()
        resolved_quote_mint = quote_mint or state.quote_mint

        if quote_amount is not None:
            base_amount = self._get_buy_token_amount_from_quote_amount(
                global_state=global_state,
                fee_config=fee_config,
                state=state,
                quote_amount=quote_amount,
            )
        else:
            quote_amount = self._get_buy_quote_amount_from_base_amount(
                global_state=global_state,
                fee_config=fee_config,
                state=state,
                base_amount=base_amount or 0,
            )

        return {
            "side": "buy",
            "mint": str(mint),
            "quote_mint": str(resolved_quote_mint),
            "base_amount": int(base_amount or 0),
            "quote_amount": int(quote_amount or 0),
            "complete": state.complete,
            "creator": str(state.creator),
            "is_mayhem_mode": state.is_mayhem_mode,
            "is_cashback_coin": state.is_cashback_coin,
        }

    async def get_sell_v2_quote(
        self,
        mint: Pubkey,
        token_amount: int,
        *,
        quote_mint: Optional[Pubkey] = None,
    ) -> dict:
        """Preview sell_v2 quote details without executing."""
        state = await self.get_bonding_curve_state(mint)
        if not state:
            raise ValueError(f"Bonding curve not found for {mint}")
        if state.complete:
            raise ValueError("Bonding curve is complete - trade on PumpSwap instead")

        global_state = await self.get_global_state()
        fee_config = await self.get_fee_config_state()
        resolved_quote_mint = quote_mint or state.quote_mint
        quote_amount = self._get_sell_quote_amount_from_token_amount(
            global_state=global_state,
            fee_config=fee_config,
            state=state,
            token_amount=token_amount,
        )
        return {
            "side": "sell",
            "mint": str(mint),
            "quote_mint": str(resolved_quote_mint),
            "base_amount": int(token_amount),
            "quote_amount": int(quote_amount),
            "complete": state.complete,
            "creator": str(state.creator),
            "is_mayhem_mode": state.is_mayhem_mode,
            "is_cashback_coin": state.is_cashback_coin,
        }

    async def get_token_price(self, mint: Pubkey) -> Optional[dict]:
        """Get current token price from bonding curve"""
        state = await self.get_bonding_curve_state(mint)
        if not state:
            return None
        if state.virtual_token_reserves <= 0:
            return {
                "price_per_token_lamports": 0,
                "price_per_token_sol": 0,
                "market_cap_lamports": 0,
                "market_cap_sol": 0,
                "virtual_sol_reserves": state.virtual_quote_reserves / 1_000_000_000,
                "virtual_token_reserves": state.virtual_token_reserves,
                "real_sol_reserves": state.real_quote_reserves / 1_000_000_000,
                "real_token_reserves": state.real_token_reserves,
                "complete": state.complete,
                "creator": str(state.creator),
                "is_mayhem_mode": state.is_mayhem_mode,
                "is_cashback_coin": state.is_cashback_coin,
                "quote_mint": str(state.quote_mint),
                "progress_percent": 100.0 if state.complete else 0.0,
            }

        # Price = virtual quote reserves / virtual token reserves
        price_per_token = state.virtual_quote_reserves / state.virtual_token_reserves
        price_per_token_sol = price_per_token / 1_000_000_000

        # Market cap = price * total_supply
        market_cap_lamports = price_per_token * state.token_total_supply
        market_cap_sol = market_cap_lamports / 1_000_000_000

        return {
            "price_per_token_lamports": price_per_token,
            "price_per_token_sol": price_per_token_sol,
            "market_cap_lamports": market_cap_lamports,
            "market_cap_sol": market_cap_sol,
            "virtual_sol_reserves": state.virtual_quote_reserves / 1_000_000_000,
            "virtual_token_reserves": state.virtual_token_reserves,
            "real_sol_reserves": state.real_quote_reserves / 1_000_000_000,
            "real_token_reserves": state.real_token_reserves,
            "complete": state.complete,
            "creator": str(state.creator),
            "is_mayhem_mode": state.is_mayhem_mode,
            "is_cashback_coin": state.is_cashback_coin,
            "quote_mint": str(state.quote_mint),
            "progress_percent": (1 - state.real_token_reserves / 793_100_000_000_000) * 100,
        }

    async def close(self):
        """Close HTTP clients"""
        await self._http_client.aclose()
        await self._rpc_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
