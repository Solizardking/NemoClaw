# `agent/` — Dark Ralph OODA loop (v0)

A paper-trading, devnet-only, stdlib-Python implementation of the
"Dark Ralph" adaptation of [Geoffrey Huntley's Ralph harness](https://ghuntley.com/ralph/).

**Read [`../how-to-ralph-wiggum/references/dark-ralph.md`](https://github.com/x402agent/how-to-ralph-wiggum/blob/main/references/dark-ralph.md) before this file.**
This README assumes you already understand the Ralph pattern and just
want to run the thing.

---

## Safety contract for v0

These are not aspirational; they are enforced in code. If you are
extending the loop, do not weaken any of them without an explicit
discussion.

| Guarantee | Where it lives |
| --- | --- |
| Mode is `paper` only | `loop.py:run_loop` rejects any other `mode:` in `RALPH.md` |
| Network is `devnet` only | same |
| Mainnet RPC URLs are rejected | `loop.py:reject_mainnet`, gated by `MAINNET_OK=1` env (which is *still* not enough — there is no signing path in v0) |
| No key handling anywhere in this directory | `grep -ri 'private_key\|seed\|signer' agent/` returns nothing on purpose |
| Position size capped per tick | `validate_decision` enforces `max_position_size_lamports` from frontmatter |
| One position at a time | `act` rejects a second `open` |
| Kill-switch on N consecutive losses | `loop.py` exits non-zero with `event: killswitch` |
| Every decision is journalled | `journal/ticks.jsonl`, append-only, git-committed |

### What's deliberately missing in v0

These are seams, not features:

- **Real market data** — `observe()` synthesises a candle. To wire a
  real feed, replace `observe()` with an adapter that pulls Pyth /
  Switchboard / a DEX REST endpoint. The adapter must respect
  `reject_mainnet()`.
- **Real signing path** — does not exist. Adding one is its own PR
  with its own review and its own threat model.
- **LLM in the loop** — `decision_fn` is a deterministic rule. You can
  pass any `Callable[[State, dict], dict]` to `run_loop` to swap in a
  model call. Whatever you pass must still produce a decision that
  passes `validate_decision`.
- **Browser-use, Dexter, social streaming** — all explicitly out of v0.

---

## Running it

Stdlib only. Python 3.10+.

```bash
# Single run, 50 ticks, fast
python3 agent/loop.py --ticks 50 --sleep 0.0 --commit-every 0

# With the dark TUI (pipe loop output into the renderer)
python3 agent/loop.py --ticks 200 --sleep 0.4 --tui --commit-every 0 \
  | python3 agent/tui.py

# With git-committed journal every 10 ticks (run from a clone of this repo)
python3 agent/loop.py --ticks 100 --sleep 0.2 --commit-every 10
```

### CLI flags

```
--ticks N            number of OODA iterations (default 50)
--sleep SECONDS      delay between ticks (default 0.25)
--seed N             RNG seed for the synthesised candles (default 42)
--commit-every N     git-commit the journal every N ticks; 0 disables
--tui                emit JSONL on stdout for `tui.py` to render
--mode paper         v0 only supports paper
```

### Environment

```
SOLANA_RPC_URL       optional. devnet endpoint only. Mainnet hostnames
                     are rejected at startup unless MAINNET_OK=1, and
                     mainnet is still not actually supported in v0.
MAINNET_OK           do not set this. There is no signing path.
```

---

## Files

```
agent/
├── README.md         this file
├── RALPH.md          per-tick prompt (small, scoped, fresh-context)
├── loop.py           OODA driver
├── tui.py            dark ANSI TUI (consumes loop --tui output)
└── journal/
    ├── .gitkeep
    └── ticks.jsonl   (generated; one JSON line per tick)
```

---

## Mapping back to the Ralph playbook

| Ralph rule | How this code respects it |
| --- | --- |
| Small scoped task | `RALPH.md` asks for one decision per tick, one action max |
| Fresh context per iteration | The prompt is re-read each tick; there is no conversation |
| State lives in git | `journal/ticks.jsonl`, committed every `--commit-every` ticks |
| Strong feedback loop | Paper PnL accounting + kill-switch on consecutive losses |
| Branch isolation | Strategy changes go on a branch and get backtested before they touch `main` |
| Walk-away safety | Kill-switch + size caps + one-position-at-a-time + paper-only |

If a future change to this directory makes any of these *less* true
than it is today, that change is wrong.

---

## Credit

The Ralph harness pattern is [@GeoffreyHuntley](https://x.com/GeoffreyHuntley)'s
work. See [ghuntley.com/ralph](https://ghuntley.com/ralph/) and
[the recent video](https://www.youtube.com/watch?v=O2bBWDoxO4s).
This directory is one adaptation of it; the underlying loop, the
"fresh context, small task, commit, repeat" insight, and the
discipline of state-in-git are all his.
