# Session Cost

Track Claude Code session costs. Zero dependencies, Python 3.8+.

L0→L3 layered thresholds: from passive collection to auto-generated optimization reports.

## Layered Thresholds

| Layer | Sessions | Behavior |
|-------|----------|----------|
| **L0** (collect) | 1–4 | Record only — not enough data for patterns |
| **L1** (observe) | 5–14 | Flag outliers (>2× mean edits), baseline established |
| **L2** (analyze) | 15–29 | Simple vs complex comparison, first actionable suggestion |
| **L3** (decide) | 30+ | Auto-generate monthly optimization report |

## Install

```bash
cp session-cost.py ~/.claude/scripts/
```

No dependencies. Python 3.8+. Windows, macOS, Linux.

Works standalone or paired with [delivery-gate](https://github.com/gategrow/delivery-gate) (quality-gate.py writes to the same `cost-log.jsonl`).

## Usage

```bash
# Show current layer, cumulative stats, last 2 sessions
python3 ~/.claude/scripts/session-cost.py show

# All-time/week/month summary
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

## Data Storage

All data stays local in `~/.claude/session-data/`:

```
session-data/
├── cost-log.jsonl       # Per-session records (append-only)
├── cumulative.json       # Running totals
├── reports/              # Auto-generated at L3 (30+ sessions)
│   └── 2026-06.md
└── archive/              # Quarterly archives (90d+)
    └── 2026-Q1.jsonl
```

## Limitations

Tracks **operations** (edits, duration), not **quality**. It answers "how much?" not "how good?" For output quality checks, pair with [self-audit](https://github.com/gategrow/self-audit).

## License

MIT