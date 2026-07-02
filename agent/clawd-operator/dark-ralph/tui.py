#!/usr/bin/env python3
"""
Dark Ralph TUI — reads the loop's JSONL on stdin, renders a single
80x24-ish ANSI dashboard. Stdlib only, no curses, no Ink. The lobster
is dark, the claws are ASCII, the theme is on-purpose.

Usage:
    python3 loop.py --tui --sleep 0.4 | python3 tui.py
"""

from __future__ import annotations

import json
import sys
from typing import Any

# --- ANSI ---
RESET = "\033[0m"
HOME = "\033[H"
CLEAR = "\033[2J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

LOBSTER = "\033[38;5;160m"   # deep red
CLAW = "\033[38;5;124m"      # darker red
SHELL = "\033[38;5;94m"      # rust/brown
GREEN = "\033[38;5;46m"
DIM = "\033[38;5;245m"
BOLD = "\033[1m"
BG = "\033[48;5;232m"        # near-black panel

SPARK = "▁▂▃▄▅▆▇█"

LOGO = [
    "      (\\(\\        ",
    "    ( -.-)        ",
    "    o_(\")(\")     ",
]

CLAW_BORDER_TOP = "╔" + "═" * 78 + "╗"
CLAW_BORDER_MID = "╠" + "═" * 78 + "╣"
CLAW_BORDER_BOT = "╚" + "═" * 78 + "╝"


def sparkline(values: list[float], width: int = 60) -> str:
    if not values:
        return ""
    vals = values[-width:]
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return SPARK[0] * len(vals)
    out = []
    for v in vals:
        idx = int((v - lo) / (hi - lo) * (len(SPARK) - 1))
        out.append(SPARK[idx])
    return "".join(out)


def fmt_lamports(n: int) -> str:
    sign = "-" if n < 0 else " "
    return f"{sign}{abs(n):>11,}ł"


def line(left: str, right: str = "", inner: int = 76) -> str:
    """Render one row inside the 80-wide border. Borders use ║...║ with
    one space pad on each side, leaving 76 visible columns for content."""
    visible = strip_ansi(left) + strip_ansi(right)
    pad = max(0, inner - len(visible))
    return f"║ {left}{' ' * pad}{right} ║"


def strip_ansi(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\033":
            j = s.find("m", i)
            if j < 0:
                break
            i = j + 1
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


class Dashboard:
    def __init__(self) -> None:
        self.tick = 0
        self.frontmatter: dict[str, Any] = {}
        self.closes: list[float] = []
        self.last_decision: dict[str, Any] = {"action": "—", "reason": "waiting for first tick"}
        self.book: dict[str, Any] = {"positions": [], "cash_lamports": 0, "realized_pnl_lamports": 0}
        self.consecutive_losses = 0
        self.killswitch_threshold = 3
        self.killed: dict[str, Any] | None = None
        self.done: dict[str, Any] | None = None

    def ingest(self, evt: dict) -> None:
        kind = evt.get("event")
        if kind == "start":
            self.frontmatter = evt.get("frontmatter", {})
            self.killswitch_threshold = int(self.frontmatter.get("loss_killswitch_consecutive", 3))
        elif kind == "tick":
            self.tick = evt["tick"]
            self.closes.append(evt["candle"]["c"])
            self.last_decision = evt.get("decision", self.last_decision)
            self.book = evt.get("book", self.book)
            self.consecutive_losses = evt.get("consecutive_losses", self.consecutive_losses)
        elif kind == "killswitch":
            self.killed = evt
        elif kind == "done":
            self.done = evt

    def render(self) -> str:
        mode = self.frontmatter.get("mode", "?")
        net = self.frontmatter.get("network", "?")
        pnl = int(self.book.get("realized_pnl_lamports", 0))
        pnl_color = GREEN if pnl >= 0 else LOBSTER
        status_pill = (
            f"{LOBSTER}● {BOLD}OODA{RESET}{DIM}  ·  {RESET}"
            f"{SHELL}{mode.upper()}{RESET}{DIM}  ·  {RESET}"
            f"{SHELL}{net.upper()}{RESET}"
        )
        header_left = f"{LOBSTER}{BOLD}DARK RALPH{RESET}   {status_pill}"
        header_right = (
            f"{DIM}tick{RESET} {BOLD}{self.tick:>5}{RESET}   "
            f"{DIM}pnl{RESET} {pnl_color}{pnl:+,}{RESET}"
        )

        spark = sparkline(self.closes, width=66)
        last_close = self.closes[-1] if self.closes else 0.0

        positions = self.book.get("positions", [])
        if positions:
            p = positions[0]
            mark = last_close
            entry = float(p["entry"])
            delta = (mark - entry) if p["side"] == "long" else (entry - mark)
            unreal = int(delta * int(p["size_lamports"]) / max(entry, 1.0))
            unreal_color = GREEN if unreal >= 0 else LOBSTER
            pos_line = (
                f"{BOLD}{p['side'].upper():<5}{RESET} "
                f"{fmt_lamports(int(p['size_lamports']))}   "
                f"{DIM}entry{RESET} {entry:7.3f}   "
                f"{DIM}mark{RESET} {mark:7.3f}   "
                f"{DIM}u-pnl{RESET} {unreal_color}{unreal:+,}{RESET}"
            )
        else:
            pos_line = f"{DIM}(no open position){RESET}"

        action = self.last_decision.get("action", "—")
        reason = self.last_decision.get("reason", "")
        action_color = {
            "open": GREEN,
            "close": SHELL,
            "hold": DIM,
        }.get(action, LOBSTER)
        decision_line = f"{action_color}{BOLD}{action:<6}{RESET}{DIM}—{RESET} {reason[:60]}"

        ks = self.consecutive_losses
        kt = self.killswitch_threshold
        dots = "".join(("●" if i < ks else "○") for i in range(kt))
        ks_color = LOBSTER if ks >= kt else (SHELL if ks > 0 else DIM)
        ks_line = f"{ks_color}{dots}{RESET}  {DIM}({ks} / {kt} consecutive losses){RESET}"

        rows = [
            f"{CLAW}{CLAW_BORDER_TOP}{RESET}",
            line(header_left, header_right),
            f"{CLAW}{CLAW_BORDER_MID}{RESET}",
            line(""),
            line(f"{DIM}PRICE  (last 66 closes){RESET}"),
            line(f"  {LOBSTER}{spark}{RESET}", f"{BOLD}{last_close:7.3f}{RESET}"),
            line(""),
            line(f"{DIM}POSITION{RESET}"),
            line(f"  {pos_line}"),
            line(""),
            line(f"{DIM}LAST DECISION{RESET}"),
            line(f"  {decision_line}"),
            line(""),
            line(f"{DIM}KILLSWITCH{RESET}"),
            line(f"  {ks_line}"),
            line(""),
        ]

        if self.killed:
            rows.append(line(f"{LOBSTER}{BOLD}HALTED{RESET}  {self.killed.get('reason','')}"[:78]))
        elif self.done:
            rows.append(line(f"{GREEN}DONE{RESET}    tick {self.done.get('tick','?')}"))
        else:
            rows.append(line(f"{DIM}running…{RESET}"))

        rows.append(f"{CLAW}{CLAW_BORDER_BOT}{RESET}")
        return "\n".join(rows)


def main() -> int:
    sys.stdout.write(HIDE_CURSOR + CLEAR)
    sys.stdout.flush()
    dash = Dashboard()
    try:
        for raw in sys.stdin:
            raw = raw.strip()
            if not raw:
                continue
            try:
                evt = json.loads(raw)
            except json.JSONDecodeError:
                continue
            dash.ingest(evt)
            sys.stdout.write(HOME + dash.render() + "\n")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
