# Session Cost — Claude Code Metabolic Tracker

**How much do your sessions cost? Stop guessing. Start measuring.**

> A zero-dependency Python script that tracks session edits, categorizes simple vs complex, and escalates through L0→L3 layered thresholds — from passive collection to auto-generated optimization reports.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## What This Gives You

| Without Session Cost | With Session Cost |
|---|---|
| No idea how many sessions you've run | Cumulative count, week/month breakdowns |
| All sessions feel the same | Simple vs complex split, avg edits per type |
| Optimization is guesswork | L3 auto-generates monthly optimization reports |
| Data piles up forever | 90-day auto-archival to quarterly files |
| Config changes have no measurable baseline | Before/after session cost comparison |

---

## Layered Thresholds

Session Cost **doesn't draw conclusions from 3 data points.** It escalates through four layers as data accumulates:

| Layer | Sessions | Behavior |
|-------|----------|----------|
| **L0** (collect) | 1–4 | Record only — not enough data for patterns |
| **L1** (observe) | 5–14 | Flag outliers (>2× mean edits), baseline established |
| **L2** (analyze) | 15–29 | Simple vs complex comparison, first actionable suggestion |
| **L3** (decide) | 30+ | Auto-generate monthly optimization report, project savings |

This is the same pattern used by delivery-gate's config-health.py dashboard — session cost tier is displayed every time you run `--check`.

---

## Install

```bash
cp session-cost.py ~/.claude/scripts/
```

No dependencies. Python 3.8+. Windows, macOS, Linux.

### Integration with delivery-gate

If you use [delivery-gate](https://github.com/gategrow/delivery-gate), quality-gate.py already writes to `cost-log.jsonl`. Run `session-cost.py show` to see your stats.

If you're using session-cost standalone, call `record` from your own Stop hook:

```bash
EDIT_COUNT=12 SESSION_DURATION_MIN=45 python3 ~/.claude/scripts/session-cost.py record
```

---

## Usage

```bash
# Show current layer, cumulative stats, last 2 sessions
python3 ~/.claude/scripts/session-cost.py show

# Quick all-time/week/month summary
python3 ~/.claude/scripts/session-cost.py cumulative

# Visualize data directory structure
python3 ~/.claude/scripts/session-cost.py structure

# Record a session (called by quality-gate.py or your own hook)
EDIT_COUNT=12 SESSION_DURATION_MIN=45 python3 ~/.claude/scripts/session-cost.py record
```

Example output:
```
[L3] L3 · 47 total (12 in 30d) · sufficient for optimization decisions
  All-time: 47 sessions · 341 edits · 18 complex · 29 simple
  This week: 3 sessions · 24 edits | This month: 12 sessions · 89 edits
  Last: 2026-06-30 14:22 · 8 edits · 35min
  Prev: 2026-06-30 10:15 · 3 edits · 12min
```

---

## Data Storage

All data stays local in `~/.claude/session-data/`:

```
session-data/
├── cost-log.jsonl       # Per-session records (append-only)
├── cumulative.json       # Running totals (overwritten each session)
├── reports/              # Auto-generated at L3 (30+ sessions)
│   └── 2026-06.md
└── archive/              # Quarterly archives (90d+)
    └── 2026-Q1.jsonl
```

---

## How It Fits

Session Cost is the **metabolic layer** of the gategrow ecosystem:

| Repo | Role |
|---|---|
| [checkgrow](https://github.com/gategrow/checkgrow) | Methodology — why and what |
| [delivery-gate](https://github.com/gategrow/delivery-gate) | Quality enforcement — config-health + quality-gate |
| **session-cost** (this repo) | Metabolic tracking — session analytics |
| [dual-pool-review](https://github.com/gategrow/dual-pool-review) | Adversarial review methodology |
| [self-audit](https://github.com/gategrow/self-audit) | Reasoning quality audit |

---

## Limitations

Session Cost tracks **operations** (edits, duration), not **content quality**. It answers "how much?" not "how good?" For quality, pair with [self-audit](https://github.com/gategrow/self-audit) or [delivery-gate](https://github.com/gategrow/delivery-gate).

---

## Community

- **Found a bug?** [Open an issue](https://github.com/gategrow/session-cost/issues/new)
- **Have an idea?** [Start a discussion](https://github.com/gategrow/session-cost/issues/new)

Maintained by [@YuhaoLin2005](https://github.com/YuhaoLin2005)

---

## License

MIT
