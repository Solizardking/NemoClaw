# CLAWD Agent

<div align="center">
  <img src="https://img.shields.io/badge/network-Solana-14F195?style=for-the-badge&logo=solana&logoColor=000000" alt="Solana" />
  <img src="https://img.shields.io/badge/mode-Cypherpunk%20Lobster-0f172a?style=for-the-badge" alt="Cypherpunk Lobster" />
  <img src="https://img.shields.io/badge/interfaces-CLI%20%7C%20Web%20%7C%20Telegram-c2410c?style=for-the-badge" alt="Interfaces" />
</div>

<div align="center">
  <h1>CLAWD</h1>
  <p><strong>Autonomous Solana trading infrastructure with a cypherpunk crustacean shell.</strong></p>
  <p>
    CLAWD Agent combines market intelligence, DEX execution, wallet analysis, content generation,
    and operator workflows into a single Solana-native command surface.
  </p>
</div>

<details>
<summary><strong>Terminal Splash</strong></summary>

```text
            .-.
           (o o)   CLAWD // Solana-native operator shell
           | O \\   Trade. Analyze. Launch. Signal.
            \\   \\
             `~~~'
```

</details>

---

## Overview

CLAWD Agent is a multi-interface operator stack for Solana and adjacent crypto workflows. It is designed for live token monitoring, discretionary trading support, wallet intelligence, perpetuals execution, content automation, and rapid operator feedback loops.

The project is opinionated:

- Solana first
- Real-time data over stale dashboards
- Human-in-the-loop execution for risky actions
- Useful defaults with optional pro routing
- Operator UX over generic chatbot polish

### Canonical Token

CLAWD tracks the project token by default:

- Symbol: `$CLAWD`
- Mint: `8cHzQHUS2s2h8TzCmfqPKYiM4dSt4roa3n7MyRLApump`

This mint is now wired into configuration as the default `CLAWD_TOKEN_MINT`.

---

## What It Does

### Trading

- Jupiter-routed Solana swaps
- Aster perpetuals and spot support
- Hyperliquid perpetuals and spot-style workflows
- Quote-first execution patterns
- Balance checks, holdings views, and wallet-state visibility

### Intelligence

- Birdeye token analytics
- Solana address analysis
- CoinGecko macro market data
- Search-backed market research
- Wallet PnL and net-worth views

### Operations

- CLI for direct operator usage
- Web API for dashboard and automation surfaces
- Telegram bot for mobile control
- CDP-managed Solana account support
- Prompt-driven agent loop with configurable model routing

### Media and Signaling

- Tweet/X posting
- Image generation
- Music generation
- Video generation
- Text-to-speech for alerts or content packaging

---

## System Style

This repo is intended to feel like an operator console, not a generic SaaS product. If you extend the UI or docs, preserve the visual language:

- Dark, sharp, tactical
- Solana neon accents
- Dense but legible information
- Minimal fluff
- Motion used sparingly for emphasis, not decoration

### README Motion Layer

GitHub README files cannot run real CSS/JS animations reliably, but this document uses:

- Bold section framing
- terminal blocks
- badge-based visual hierarchy
- collapsible panels for layered disclosure

For richer animated presentation, use the web surface in `clawd-agent/web`.

---

## Feature Surface

### Solana Trading

| Capability | Description |
|---|---|
| `get_wallet_balance` | Inspect SOL and SPL balances |
| `get_token_price` | Pull token price data |
| `get_token_info` | Price, liquidity, holders, market structure |
| `get_swap_quote` | Simulate swaps before execution |
| `buy_token` | Execute buy orders with SOL |
| `sell_token` | Execute sell orders into SOL |
| `get_portfolio` | Consolidated wallet portfolio |
| `get_trending_tokens` | Discover trending Solana assets |
| `search_token` | Resolve tokens by symbol or name |

### Perpetuals and Spot

- Aster
  - long/short positions
  - leverage configuration
  - spot orders and transfers
- Hyperliquid
  - account visibility
  - perp entries/exits
  - open orders
  - leverage and transfer actions

### Analytics

- wallet net worth
- wallet PnL
- OHLCV token charts
- token security analysis
- Solana address inspection
- global market snapshots

---

## Architecture

```text
clawd-agent/
├── agent.py                 # main runtime and orchestration layer
├── cli.py                   # local operator CLI
├── config.py                # environment-backed configuration loader
├── telegram_bot.py          # Telegram command surface
├── web/                     # API and browser-facing services
├── clients/                 # exchange, data, and provider clients
├── tools/                   # tool adapters exposed to the agent
├── workspace/               # runtime workspace and outputs
├── idl/                     # Solana / program interface artifacts
└── README.md                # this file
```

---

## Quick Start

### 1. Install

```bash
cd clawd-agent
pip install -r requirements.txt
```

### 2. Configure

Create `.env.local` and set the required values:

```env
HELIUS_API_KEY=...
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=...
HELIUS_WSS_URL=wss://mainnet.helius-rpc.com/?api-key=...

BIRDEYE_API_KEY=...

JUPITER_API_KEY=...
JUPITER_REFERRAL_ACCOUNT=...

CLAWD_WALLET=your_public_key
CLAWD_PRIVATE_KEY=your_base58_private_key
CLAWD_TOKEN_MINT=8cHzQHUS2s2h8TzCmfqPKYiM4dSt4roa3n7MyRLApump

OPENROUTER_API_KEY=...
OPENROUTER_MODEL=minimax/minimax-m2-her
```

Optional providers:

- `ASTER_*`
- `HYPERLIQUID_*`
- `CDP_*`
- `COINGECKO_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TWITTER_*`
- `MINIMAX_API_KEY`
- `SEARCH_API_KEY`
- `XAI_API_KEY`

### 3. Run

Interactive CLI:

```bash
python agent.py
```

Single query:

```bash
python cli.py -q "Check the price and security profile of $CLAWD"
```

Telegram bot:

```bash
python telegram_bot.py
```

Web API:

```bash
cd web
python api_server.py
```

---

## Example Operator Prompts

```text
Check my wallet, then compare my largest token holdings to current Solana movers.
```

```text
Show me the current price, liquidity, and recent trade activity for 8cHzQHUS2s2h8TzCmfqPKYiM4dSt4roa3n7MyRLApump.
```

```text
Get a quote to buy 0.25 SOL of $CLAWD, but do not execute.
```

```text
Analyze this Solana address and tell me whether it looks like a wallet, token, or transaction.
```

---

## Telegram Commands

### Core

- `/start`
- `/help`
- `/balance`
- `/portfolio`
- `/trending`
- `/price <token>`

### Trading

- `/buy <amount> <token>`
- `/sell <amount> <token>`
- `/quote <amount> <from> <to>`
- `/long <pair> <leverage> <amount>`
- `/short <pair> <leverage> <amount>`
- `/positions`
- `/close <pair>`

### Intelligence

- `/analyze <address>`
- `/search <query>`
- `/security <token>`
- `/crypto <coins>`
- `/global`

---

## Safety Model

CLAWD is built for live markets. Treat it like production infrastructure.

- Never commit private keys or API secrets
- Prefer quote-first workflows before market execution
- Verify token addresses before swapping
- Treat leverage as hazardous by default
- Review token security data before touching thin liquidity
- Keep devnet and mainnet credentials clearly separated

---

## Notes for Contributors

When extending CLAWD:

- keep Solana flows explicit
- avoid hiding execution risk
- preserve command-line ergonomics
- favor inspectable tool outputs over vague summaries
- keep the operator tone sharp and technical

If you are building UI on top of this repo, aim for deliberate visual identity rather than default component-library aesthetics.

---

## Status

CLAWD Agent is an active operator workspace. Interfaces and providers evolve quickly. Expect occasional rough edges around third-party exchange APIs, auth flows, and upstream SDK changes.

If you want the shortest accurate summary:

> CLAWD is a Solana-native cypherpunk trading shell with wallet intelligence, live market tooling, and a lobster problem.
