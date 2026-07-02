#!/usr/bin/env python3
"""
Clawd Operator TUI — reads the orchestrator's JSONL on stdin, renders an
80x30-ish ANSI dashboard. Stdlib only. Dark lobster aesthetic inherited from
dark-ralph/tui.py, adapted for the multi-agent orchestrator domain.

Usage:
    python -m clawd_operator --tui | python tui.py
    python -m clawd_operator --tui --agent claude | python tui.py
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

# ── ANSI ────────────────────────────────────────────────────────────────────
RESET       = "\033[0m"
HOME        = "\033[H"
CLEAR       = "\033[2J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

LOBSTER  = "\033[38;5;160m"   # deep red
CLAW     = "\033[38;5;124m"   # darker red
SHELL    = "\033[38;5;94m"    # rust/brown
CYAN     = "\033[38;5;38m"    # agent accent
GREEN    = "\033[38;5;46m"
YELLOW   = "\033[38;5;220m"
DIM      = "\033[38;5;245m"
DIMMER   = "\033[38;5;238m"
BOLD     = "\033[1m"
BG       = "\033[48;5;232m"   # near-black panel

SPARK = "▁▂▃▄▅▆▇█"

AGENT_COLORS = {
    "claude":  "\033[38;5;99m",   # purple
    "gemini":  "\033[38;5;33m",   # blue
    "qchat":   "\033[38;5;214m",  # orange
    "kiro":    "\033[38;5;48m",   # mint
    "acp":     "\033[38;5;177m",  # lavender
    "auto":    "\033[38;5;245m",  # dim
}

LOGO = [
    r"  /\_/\  CLAWD  ",
    r" ( o.o ) OPERATOR",
    r"  > ^ <          ",
]

BORDER_TOP = "╔" + "═" * 78 + "╗"
BORDER_MID = "╠" + "═" * 78 + "╣"
BORDER_BOT = "╚" + "═" * 78 + "╝"
BORDER_SEP = "╟" + "─" * 78 + "╢"


# ── helpers ─────────────────────────────────────────────────────────────────

def strip_ansi(s: str) -> str:
    out: list[str] = []
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


def row(left: str, right: str = "", inner: int = 76) -> str:
    """One content row inside the 80-wide border (1 space pad each side)."""
    pad = max(0, inner - len(strip_ansi(left)) - len(strip_ansi(right)))
    return f"║ {left}{' ' * pad}{right} ║"


def bar(value: float, total: float, width: int = 20, color: str = GREEN) -> str:
    """ASCII progress bar."""
    if total <= 0:
        frac = 0.0
    else:
        frac = min(1.0, value / total)
    filled = int(frac * width)
    empty = width - filled
    b = f"{color}{'█' * filled}{DIMMER}{'░' * empty}{RESET}"
    pct = f"{frac * 100:5.1f}%"
    return f"{b} {DIM}{pct}{RESET}"


def sparkline(values: list[float], width: int = 50) -> str:
    vals = values[-width:]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return SPARK[0] * len(vals)
    return "".join(SPARK[int((v - lo) / (hi - lo) * (len(SPARK) - 1))] for v in vals)


def fmt_duration(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{sec:02d}s"
    if m:
        return f"{m}m{sec:02d}s"
    return f"{sec}s"


def fmt_cost(c: float) -> str:
    if c >= 1.0:
        return f"${c:.3f}"
    return f"${c:.4f}"


def agent_pill(name: str) -> str:
    color = AGENT_COLORS.get(name.lower(), DIM)
    return f"{color}{BOLD}{name.upper()}{RESET}"


def trigger_badge(trigger: str) -> str:
    color = {
        "initial":          CYAN,
        "task_incomplete":  YELLOW,
        "previous_success": GREEN,
        "recovery":         LOBSTER,
        "loop_detected":    LOBSTER,
        "safety_limit":     LOBSTER,
        "user_stop":        DIM,
    }.get(trigger, DIM)
    return f"{color}{trigger}{RESET}"


# ── dashboard state ──────────────────────────────────────────────────────────

class Dashboard:
    def __init__(self) -> None:
        self.start_cfg: dict[str, Any] = {}
        self.iteration    = 0
        self.adapter      = "—"
        self.trigger      = "—"
        self.metrics: dict[str, int] = {
            "iterations": 0, "successful": 0, "failed": 0,
            "errors": 0, "checkpoints": 0,
        }
        self.cost         = 0.0
        self.max_cost: float | None = None
        self.max_iters    = 0
        self.output_preview = ""
        self.current_task: dict[str, Any] | None = None
        self.queue_length = 0
        self.last_duration = 0.0
        self.durations: list[float] = []
        self.loop_detected = False
        self.done: dict[str, Any] | None = None
        self.wall_start   = time.time()
        self.status       = "waiting…"
        self.last_success: bool | None = None
        self.last_error   = ""

    def ingest(self, evt: dict) -> None:
        kind = evt.get("event")
        if kind == "start":
            self.start_cfg  = evt
            self.adapter    = evt.get("agent", "auto")
            self.max_iters  = int(evt.get("max_iterations", 0))
            self.max_cost   = evt.get("max_cost")
            self.wall_start = time.time()
            self.status     = "running"
        elif kind == "iteration_start":
            self.iteration  = evt.get("iteration", self.iteration)
            self.adapter    = evt.get("adapter", self.adapter)
            self.trigger    = evt.get("trigger", "—")
            self.current_task  = evt.get("current_task")
            self.queue_length  = int(evt.get("queue_length", 0))
            self.cost          = float(evt.get("cost", self.cost))
            self.status     = f"iter {self.iteration} — running"
            m = evt.get("metrics", {})
            if m:
                self.metrics.update({k: int(v) for k, v in m.items() if k in self.metrics})
        elif kind == "iteration_done":
            self.iteration     = evt.get("iteration", self.iteration)
            self.last_success  = bool(evt.get("success", False))
            self.last_error    = evt.get("error", "")
            self.last_duration = float(evt.get("duration", 0))
            self.durations.append(self.last_duration)
            self.output_preview = evt.get("output_preview", "")
            self.loop_detected  = bool(evt.get("loop_detected", False))
            self.cost           = float(evt.get("cost", self.cost))
            self.current_task   = evt.get("current_task")
            self.queue_length   = int(evt.get("queue_length", 0))
            m = evt.get("metrics", {})
            if m:
                self.metrics.update({k: int(v) for k, v in m.items() if k in self.metrics})
            self.status = "running"
        elif kind == "loop_detected":
            self.loop_detected = True
            self.status = "LOOP DETECTED"
        elif kind == "done":
            self.done   = evt
            self.cost   = float(evt.get("cost", self.cost))
            self.status = "done"

    def render(self) -> str:
        elapsed = time.time() - self.wall_start
        agent_str  = agent_pill(self.adapter)
        status_dim = f"{DIM}·{RESET}"

        # ── header row ──────────────────────────────────────────────────────
        header_left = (
            f"{LOBSTER}{BOLD}CLAWD OPERATOR{RESET}  {status_dim}  "
            f"{agent_str}  {status_dim}  "
            f"{SHELL}OODA{RESET}"
        )
        header_right = (
            f"{DIM}iter{RESET} {BOLD}{self.iteration:>4}{RESET}   "
            f"{DIM}up{RESET} {DIM}{fmt_duration(elapsed)}{RESET}"
        )

        # ── logo (3 lines, right-justified within border) ───────────────────
        logo_lines = [
            row(f"{LOBSTER}{ln}{RESET}") for ln in LOGO
        ]

        # ── metrics row ─────────────────────────────────────────────────────
        m = self.metrics
        metrics_str = (
            f"{GREEN}✓ {m['successful']}{RESET}  "
            f"{LOBSTER}✗ {m['failed']}{RESET}  "
            f"{YELLOW}! {m['errors']}{RESET}  "
            f"{DIM}⬡ {m['checkpoints']} ckpt{RESET}"
        )

        # ── iteration progress bar ───────────────────────────────────────────
        if self.max_iters > 0:
            iter_bar = bar(self.iteration, self.max_iters, width=30, color=CYAN)
            iter_label = f"{DIM}progress{RESET}  {iter_bar}  {DIM}{self.iteration}/{self.max_iters}{RESET}"
        else:
            iter_label = f"{DIM}iterations{RESET}  {BOLD}{self.iteration}{RESET}"

        # ── cost bar ─────────────────────────────────────────────────────────
        cost_color = LOBSTER if (self.max_cost and self.cost >= self.max_cost * 0.8) else GREEN
        if self.max_cost:
            cost_bar = bar(self.cost, self.max_cost, width=20, color=cost_color)
            cost_label = f"{DIM}cost{RESET}  {cost_bar}  {cost_color}{fmt_cost(self.cost)}{RESET}{DIM}/{fmt_cost(self.max_cost)}{RESET}"
        else:
            cost_label = f"{DIM}cost{RESET}  {cost_color}{fmt_cost(self.cost)}{RESET}"

        # ── duration sparkline ───────────────────────────────────────────────
        spark = sparkline(self.durations, width=50)
        spark_line = (
            f"{DIM}iter time (s){RESET}  "
            f"{SHELL}{spark}{RESET}"
            + (f"  {DIM}{self.last_duration:.1f}s{RESET}" if self.last_duration else "")
        )

        # ── current task ─────────────────────────────────────────────────────
        if self.current_task:
            desc = str(self.current_task.get("description", ""))[:62]
            task_status = self.current_task.get("status", "")
            t_color = YELLOW if task_status == "in_progress" else (GREEN if task_status == "completed" else DIM)
            task_line = f"{t_color}▶ {desc}{RESET}  {DIM}(+{self.queue_length} queued){RESET}"
        else:
            if self.queue_length:
                task_line = f"{DIM}({self.queue_length} task(s) queued){RESET}"
            else:
                task_line = f"{DIM}(no active task){RESET}"

        # ── last decision / trigger ───────────────────────────────────────────
        trigger_line = (
            f"{DIM}trigger{RESET}  {trigger_badge(self.trigger)}   "
            f"{DIM}last{RESET} "
            + (f"{GREEN}✓ ok{RESET}" if self.last_success is True
               else (f"{LOBSTER}✗ {self.last_error[:40]}{RESET}" if self.last_success is False
                     else f"{DIM}—{RESET}"))
        )

        # ── output preview ────────────────────────────────────────────────────
        preview = self.output_preview.replace("\n", " ").strip()
        if preview:
            preview = preview[:72]
            preview_lines = [
                row(f"{DIM}last output{RESET}"),
                row(f"  {DIM}{preview}{RESET}"),
            ]
        else:
            preview_lines = [row(f"{DIM}last output  (none yet){RESET}")]

        # ── status footer ─────────────────────────────────────────────────────
        if self.done:
            footer = row(
                f"{GREEN}{BOLD}DONE{RESET}  "
                f"iter {self.done.get('iterations','?')}  "
                f"{GREEN}✓ {self.done.get('successful',0)}{RESET}  "
                f"{LOBSTER}✗ {self.done.get('failed',0)}{RESET}  "
                f"cost {fmt_cost(self.done.get('cost', self.cost))}"
            )
        elif self.loop_detected:
            footer = row(f"{LOBSTER}{BOLD}HALTED{RESET}  loop detected — agent producing repetitive output")
        else:
            status_color = GREEN if self.status.startswith("iter") else (LOBSTER if "HALT" in self.status else DIM)
            footer = row(f"{status_color}{self.status}{RESET}")

        # ── assemble ──────────────────────────────────────────────────────────
        rows = [
            f"{CLAW}{BORDER_TOP}{RESET}",
            row(header_left, header_right),
            f"{CLAW}{BORDER_MID}{RESET}",
            *logo_lines,
            f"{CLAW}{BORDER_SEP}{RESET}",
            row(""),
            row(f"{DIM}METRICS{RESET}"),
            row(f"  {metrics_str}"),
            row(""),
            row(f"  {iter_label}"),
            row(f"  {cost_label}"),
            row(""),
            row(f"{DIM}TIMING{RESET}"),
            row(f"  {spark_line}"),
            row(""),
            f"{CLAW}{BORDER_SEP}{RESET}",
            row(f"{DIM}CURRENT TASK{RESET}"),
            row(f"  {task_line}"),
            row(""),
            row(f"{DIM}LAST ITERATION{RESET}"),
            row(f"  {trigger_line}"),
            row(""),
            *preview_lines,
            row(""),
            f"{CLAW}{BORDER_MID}{RESET}",
            footer,
            f"{CLAW}{BORDER_BOT}{RESET}",
        ]
        return "\n".join(rows)


# ── entrypoint ───────────────────────────────────────────────────────────────

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
