#!/usr/bin/env python3
"""
Dark Ralph — OODA-loop driver.

Paper-trading only, devnet-only, stdlib only. v0.

Read agent/README.md before running. The signing path is intentionally
absent. There is no key handling in this file. There is no mainnet RPC
client in this file. If you are looking for those, this is not the
right file and v0 is not the right milestone.

The loop:
    Observe   - get a fresh candle (mocked feed in v0)
    Orient    - update rolling window + book state
    Decide    - call the decision function (v0: deterministic rule;
                wire-in point for an LLM is decision_fn=)
    Act       - apply to paper book under guardrails
    Journal   - append decision + outcome to journal/ticks.jsonl
    Commit    - git-commit the journal every COMMIT_EVERY ticks
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
JOURNAL_DIR = ROOT / "journal"
JOURNAL_FILE = JOURNAL_DIR / "ticks.jsonl"
RALPH_MD = ROOT / "RALPH.md"

DISALLOWED_RPC_HOSTS = (
    "api.mainnet-beta.solana.com",
    "solana-mainnet",
    "rpc.helius.xyz",
    "rpc.ankr.com/solana",
)


@dataclasses.dataclass
class Candle:
    t: float
    o: float
    h: float
    l: float
    c: float
    v: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Position:
    id: str
    side: str  # "long" | "short"
    size_lamports: int
    entry: float
    opened_tick: int

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Book:
    positions: list[Position]
    cash_lamports: int
    realized_pnl_lamports: int = 0

    def to_dict(self) -> dict:
        return {
            "positions": [p.to_dict() for p in self.positions],
            "cash_lamports": self.cash_lamports,
            "realized_pnl_lamports": self.realized_pnl_lamports,
        }


@dataclasses.dataclass
class State:
    tick: int
    candles: list[Candle]
    book: Book
    consecutive_losses: int
    last_decisions: list[dict]


def parse_frontmatter(md_path: Path) -> dict:
    """Tiny YAML-ish frontmatter parser. Only supports `key: scalar` lines."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"{md_path} is missing frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise SystemExit(f"{md_path} frontmatter is unterminated")
    out: dict = {}
    for line in text[4:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.lstrip("-").isdigit():
            out[k.strip()] = int(v)
        else:
            out[k.strip()] = v
    return out


def reject_mainnet(rpc_url: str | None) -> None:
    """Refuse to run if anything looks like mainnet. v0 has no signing path
    anyway — this is belt-and-suspenders."""
    if not rpc_url:
        return
    lowered = rpc_url.lower()
    if any(h in lowered for h in DISALLOWED_RPC_HOSTS) and os.environ.get("MAINNET_OK") != "1":
        sys.exit(
            f"refusing to start: RPC URL {rpc_url!r} looks like mainnet. "
            "v0 is paper-only, devnet-only. If you intend to run mainnet "
            "from a future version, set MAINNET_OK=1 and ship a separate "
            "mainnet config — but that path does not exist in v0."
        )


def synth_candle(state: State, rng: random.Random) -> Candle:
    """Deterministic-ish random walk so the loop runs without a network feed.
    Real feed integration is a TODO(future PR) seam in observe()."""
    last_c = state.candles[-1].c if state.candles else 100.0
    drift = rng.uniform(-0.6, 0.6)
    o = last_c
    c = max(1.0, last_c + drift)
    high = max(o, c) + abs(rng.uniform(0, 0.25))
    low = max(0.5, min(o, c) - abs(rng.uniform(0, 0.25)))
    vol = rng.uniform(100.0, 1000.0)
    return Candle(t=time.time(), o=o, h=high, l=low, c=c, v=vol)


def observe(state: State, rng: random.Random) -> Candle:
    # TODO(future PR): replace with a real Pyth / Switchboard / DEX feed
    # adapter. Adapter MUST stay devnet-gated and MUST refuse to start
    # against a mainnet RPC unless MAINNET_OK=1 (see reject_mainnet()).
    return synth_candle(state, rng)


def rule_based_decision(state: State, caps: dict) -> dict:
    """v0 decision function. Mirrors the rule documented in RALPH.md so the
    loop runs end-to-end without an LLM. To swap in a real model, pass a
    different callable to run_loop(decision_fn=...)."""
    if len(state.candles) < 3:
        return {"action": "hold", "reason": "warmup: <3 candles"}

    closes = [c.c for c in state.candles[-3:]]
    monotonic_up = closes[0] < closes[1] < closes[2]
    monotonic_down = closes[0] > closes[1] > closes[2]

    if state.book.positions:
        pos = state.book.positions[0]
        # 2-bar reversal against the position?
        if pos.side == "long" and closes[-1] < closes[-2] < closes[-3]:
            return {"action": "close", "position_id": pos.id, "reason": "2-bar reversal vs long"}
        if pos.side == "short" and closes[-1] > closes[-2] > closes[-3]:
            return {"action": "close", "position_id": pos.id, "reason": "2-bar reversal vs short"}
        return {"action": "hold", "reason": "position open, no reversal"}

    cap = int(caps.get("max_position_size_lamports", 1_000_000))
    size = min(cap, 500_000)
    if monotonic_up:
        return {"action": "open", "side": "long", "size_lamports": size, "reason": "3 closes monotonic up"}
    if monotonic_down:
        return {"action": "open", "side": "short", "size_lamports": size, "reason": "3 closes monotonic down"}
    return {"action": "hold", "reason": "no signal"}


def validate_decision(decision: dict, caps: dict) -> str | None:
    action = decision.get("action")
    if action not in {"hold", "open", "close"}:
        return f"unknown action {action!r}"
    if action == "open":
        side = decision.get("side")
        if side not in {"long", "short"}:
            return f"open requires side in long/short, got {side!r}"
        size = decision.get("size_lamports")
        if not isinstance(size, int) or size <= 0:
            return "open requires positive int size_lamports"
        cap = int(caps.get("max_position_size_lamports", 0))
        if size > cap:
            return f"size {size} > cap {cap}"
    if action == "close":
        if not decision.get("position_id"):
            return "close requires position_id"
    return None


def act(decision: dict, state: State, last_close: float) -> dict:
    """Apply the decision to the paper book. Returns an outcome dict
    appended to the journal entry. Never signs anything; never reaches
    a network."""
    action = decision["action"]

    if action == "hold":
        return {"applied": True, "kind": "hold"}

    if action == "open":
        # v0: only one position at a time
        if state.book.positions:
            return {"applied": False, "kind": "open", "reason": "position already open"}
        pos = Position(
            id=f"p-{uuid.uuid4().hex[:8]}",
            side=decision["side"],
            size_lamports=int(decision["size_lamports"]),
            entry=last_close,
            opened_tick=state.tick,
        )
        state.book.positions.append(pos)
        return {"applied": True, "kind": "open", "position": pos.to_dict()}

    if action == "close":
        target_id = decision["position_id"]
        for i, pos in enumerate(state.book.positions):
            if pos.id == target_id:
                state.book.positions.pop(i)
                # paper PnL: simple linear in price delta * size proxy
                price_delta = last_close - pos.entry
                if pos.side == "short":
                    price_delta = -price_delta
                pnl = int(price_delta * pos.size_lamports / max(pos.entry, 1.0))
                state.book.realized_pnl_lamports += pnl
                if pnl < 0:
                    state.consecutive_losses += 1
                else:
                    state.consecutive_losses = 0
                return {
                    "applied": True,
                    "kind": "close",
                    "position_id": target_id,
                    "exit": last_close,
                    "pnl_lamports": pnl,
                    "consecutive_losses": state.consecutive_losses,
                }
        return {"applied": False, "kind": "close", "reason": f"position {target_id!r} not found"}

    return {"applied": False, "kind": action, "reason": "unhandled action"}


def journal_append(entry: dict) -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    with JOURNAL_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def git_commit_journal(tick: int) -> None:
    """Commit the journal. Best-effort; we don't fail the loop if git is
    unhappy (e.g. detached HEAD in CI). The journal still exists on disk.

    The commit is scoped to the journal pathspec via `--only --` so it
    can never accidentally sweep in unrelated changes the operator has
    already staged in the surrounding repo.
    """
    journal_rel = str(JOURNAL_FILE.relative_to(ROOT.parent))
    try:
        subprocess.run(
            ["git", "add", "--", journal_rel],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
        )
        subprocess.run(
            [
                "git", "commit",
                "--only", "--allow-empty",
                "-m", f"agent: tick {tick}",
                "--", journal_rel,
            ],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        # git not installed; that's fine for a demo run
        pass


def emit(payload: dict, tui: bool) -> None:
    """Single line of output. The TUI consumes this same JSONL stream
    over a pipe, so emit() is the only stdout path."""
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def run_loop(
    *,
    ticks: int,
    sleep_s: float,
    seed: int,
    commit_every: int,
    tui: bool,
    decision_fn: Callable[[State, dict], dict] = rule_based_decision,
) -> int:
    frontmatter = parse_frontmatter(RALPH_MD)
    if frontmatter.get("mode") != "paper":
        sys.exit("v0 only supports mode: paper in RALPH.md frontmatter")
    if frontmatter.get("network") != "devnet":
        sys.exit("v0 only supports network: devnet in RALPH.md frontmatter")

    reject_mainnet(os.environ.get("SOLANA_RPC_URL"))

    rng = random.Random(seed)
    state = State(
        tick=0,
        candles=[],
        book=Book(positions=[], cash_lamports=10_000_000),
        consecutive_losses=0,
        last_decisions=[],
    )

    kill_threshold = int(frontmatter.get("loss_killswitch_consecutive", 3))

    emit({"event": "start", "frontmatter": frontmatter, "seed": seed, "ticks": ticks}, tui)

    for n in range(1, ticks + 1):
        state.tick = n
        candle = observe(state, rng)
        state.candles.append(candle)
        if len(state.candles) > 64:
            state.candles = state.candles[-64:]

        decision = decision_fn(state, frontmatter)
        err = validate_decision(decision, frontmatter)
        if err:
            decision = {"action": "hold", "reason": f"rejected by harness: {err}"}

        outcome = act(decision, state, last_close=candle.c)

        entry = {
            "tick": n,
            "now": datetime.now(timezone.utc).isoformat(),
            "candle": candle.to_dict(),
            "decision": decision,
            "outcome": outcome,
            "book": state.book.to_dict(),
            "consecutive_losses": state.consecutive_losses,
        }
        journal_append(entry)
        state.last_decisions = (state.last_decisions + [entry])[-3:]
        emit({"event": "tick", **entry}, tui)

        if state.consecutive_losses >= kill_threshold:
            emit(
                {
                    "event": "killswitch",
                    "tick": n,
                    "reason": f"{state.consecutive_losses} consecutive losses >= threshold {kill_threshold}",
                },
                tui,
            )
            return 2

        if commit_every > 0 and n % commit_every == 0:
            git_commit_journal(n)

        if sleep_s > 0:
            time.sleep(sleep_s)

    if commit_every > 0:
        git_commit_journal(state.tick)
    emit({"event": "done", "tick": state.tick, "book": state.book.to_dict()}, tui)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Dark Ralph OODA loop (paper, devnet)")
    p.add_argument("--ticks", type=int, default=50)
    p.add_argument("--sleep", type=float, default=0.25, help="seconds between ticks")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--commit-every", type=int, default=10, help="git-commit journal every N ticks; 0 disables")
    p.add_argument("--tui", action="store_true", help="emit TUI-consumable JSONL on stdout (same format)")
    p.add_argument("--mode", default="paper", choices=["paper"], help="v0 only supports paper")
    args = p.parse_args(argv)

    return run_loop(
        ticks=args.ticks,
        sleep_s=args.sleep,
        seed=args.seed,
        commit_every=args.commit_every,
        tui=args.tui,
    )


if __name__ == "__main__":
    raise SystemExit(main())
