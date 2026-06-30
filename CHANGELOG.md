# Changelog

All notable changes to session-cost will be documented in this file.

## [1.0.0] - 2026-07-01

### Added
- Initial release: session cost tracker with L0-L3 layered thresholds
- `record` command: log session edits + duration from environment variables
- `show` command: display current layer, cumulative stats, last 2 sessions
- `cumulative` command: quick all-time/week/month summary
- `structure` command: visualize data directory layout
- L0-L3 auto-escalation: collect (1-4) → observe (5-14) → analyze (15-29) → decide (30+)
- Auto monthly optimization reports at L3 threshold
- Auto 90-day archival to quarterly files
- Cumulative JSON with week/month aggregations
- Stale cumulative auto-detection + re-sync
- Integration with delivery-gate quality-gate.py cost-log.jsonl output
