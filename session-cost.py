#!/usr/bin/env python3
"""Session cost tracker — operational metrics, not learning data.

Data stored in ~/.claude/session-data/ (separate from projects/memory):
  session-data/
  ├── cost-log.jsonl       # Per-session records (append-only)
  ├── cumulative.json       # Running totals (overwritten each session)
  ├── reports/              # Auto-generated at L3 (30+ sessions)
  │   └── YYYY-MM-DD.md
  └── archive/              # Quarterly archives of old cost-log
      └── YYYY-QN.jsonl

Layered thresholds:
  L0 (1-4):   collect, no conclusions
  L1 (5-14):  flag outliers (>2x mean)
  L2 (15-29): compare simple vs complex, one suggestion
  L3 (30+):   auto-generate optimization report
"""
from __future__ import annotations

import json, os, sys, datetime, shutil
from pathlib import Path

DATA = Path(os.path.expanduser('~/.claude/session-data'))
LOG = DATA / 'cost-log.jsonl'
CUMULATIVE = DATA / 'cumulative.json'
REPORTS = DATA / 'reports'
ARCHIVE = DATA / 'archive'

def ensure_dirs():
    for d in [DATA, REPORTS, ARCHIVE]:
        d.mkdir(parents=True, exist_ok=True)

def record(edits: int, duration_min: int) -> dict:
    ensure_dirs()
    ts = datetime.datetime.now()
    entry = {
        'ts': ts.isoformat(),
        'date': ts.strftime('%Y-%m-%d'),
        'time': ts.strftime('%H:%M'),
        'edits': edits,
        'min': duration_min,
        'complex': edits >= 3,
    }
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    _update_cumulative()
    return entry

def _update_cumulative():
    entries = read_all()
    today = datetime.date.today().isoformat()
    this_week = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    this_month = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()

    total = len(entries)
    total_edits = sum(e['edits'] for e in entries)
    complex_n = sum(1 for e in entries if e.get('complex', False))
    simple_n = total - complex_n

    week_entries = [e for e in entries if e['date'] >= this_week]
    month_entries = [e for e in entries if e['date'] >= this_month]

    cumulative = {
        'updated': today,
        'total_sessions': total,
        'total_edits': total_edits,
        'complex_sessions': complex_n,
        'simple_sessions': simple_n,
        'week': {'sessions': len(week_entries), 'edits': sum(e['edits'] for e in week_entries)},
        'month': {'sessions': len(month_entries), 'edits': sum(e['edits'] for e in month_entries)},
    }
    try:
        with open(CUMULATIVE, 'w', encoding='utf-8') as f:
            json.dump(cumulative, f, indent=2, ensure_ascii=False)
    except (OSError, IOError):
        pass  # Non-critical — show() will re-sync on next read

def read_all() -> list[dict]:
    if not LOG.exists(): return []
    entries = []
    with open(LOG, 'r', encoding='utf-8') as f:
        for line in f:
            try: entries.append(json.loads(line.strip()))
            except json.JSONDecodeError: continue
    return entries

def read_recent(n: int = 30) -> list[dict]:
    return read_all()[-n:]

def compute_layer(entries: list[dict]) -> dict:
    n = len(entries)
    if n < 1:
        return {'L': 0, 'n': 0, 'status': 'new', 'msg': 'No data yet. Recording starts this session.'}

    month_cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    recent = [e for e in entries if e['date'] >= month_cutoff]
    rn = len(recent)

    if n < 5:
        return {'L': 0, 'n': n, 'recent': rn, 'status': 'baseline',
                'msg': f'L0 · {n} sessions · need {5-n} more for pattern detection'}

    edits_list = [e['edits'] for e in recent if e['edits'] > 0]
    if not edits_list:
        return {'L': 0, 'n': n, 'status': 'idle', 'msg': 'No editing sessions recorded.'}

    avg_e = sum(edits_list) / len(edits_list)
    result = {'L': 0, 'n': n, 'recent': rn, 'avg_edits': round(avg_e, 1)}

    if n < 15:
        outliers = sum(1 for e in recent if e['edits'] > avg_e * 2)
        result['L'] = 1
        result['status'] = 'observing'
        result['msg'] = (
            f'L1 · {rn} sessions in 30d · avg {avg_e:.0f} edits · '
            f'{outliers} outlier(s)' if outliers else
            f'L1 · {rn} sessions in 30d · avg {avg_e:.0f} edits · all normal'
        )
    elif n < 30:
        cx = [e for e in recent if e.get('complex')]
        sx = [e for e in recent if not e.get('complex')]
        result['L'] = 2
        result['status'] = 'analyzing'
        result['complex_n'] = len(cx)
        result['simple_n'] = len(sx)
        cx_avg = sum(e['edits'] for e in cx) // max(len(cx), 1)
        result['msg'] = (
            f'L2 · {rn} sessions · {len(cx)} complex(avg {cx_avg}e) · {len(sx)} simple · ready for suggestion'
        )
    else:
        cx = [e for e in recent if e.get('complex')]
        result['L'] = 3
        result['status'] = 'ready'
        result['complex_n'] = len(cx)
        result['msg'] = f'L3 · {n} total ({rn} in 30d) · sufficient for optimization decisions'

    return result

def _read_cumulative() -> dict:
    """Read cumulative.json, returning {} if missing or stale."""
    if not CUMULATIVE.exists():
        return {}
    try:
        with open(CUMULATIVE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def show() -> str:
    entries = read_all()
    stats = compute_layer(entries)
    cumulative = _read_cumulative()

    # Detect stale cumulative: log has more entries than cumulative recorded
    log_n = len(entries)
    cum_n = cumulative.get('total_sessions', 0) if cumulative else 0
    if log_n > cum_n:
        _update_cumulative()
        cumulative = _read_cumulative()

    lines = [
        f"[L{stats['L']}] {stats['msg']}",
    ]
    if cumulative:
        lines.append(
            f"  All-time: {cumulative.get('total_sessions','?')} sessions · "
            f"{cumulative.get('total_edits','?')} edits · "
            f"{cumulative.get('complex_sessions','?')} complex · "
            f"{cumulative.get('simple_sessions','?')} simple"
        )
        w = cumulative.get('week', {})
        m = cumulative.get('month', {})
        lines.append(
            f"  This week: {w.get('sessions','?')} sessions · {w.get('edits','?')} edits | "
            f"This month: {m.get('sessions','?')} sessions · {m.get('edits','?')} edits"
        )

    if entries:
        last = entries[-1]
        lines.append(f"  Last: {last['date']} {last['time']} · {last['edits']} edits · {last['min']}min")
        if len(entries) >= 2:
            prev = entries[-2]
            lines.append(f"  Prev: {prev['date']} {prev['time']} · {prev['edits']} edits · {prev['min']}min")

    return '\n'.join(lines)

def maybe_generate_report():
    """At L3, generate optimization report if one doesn't exist this month."""
    entries = read_all()
    stats = compute_layer(entries)
    if stats['L'] < 3:
        return

    this_month = datetime.date.today().strftime('%Y-%m')
    report_path = REPORTS / f'{this_month}.md'
    if report_path.exists():
        return  # Already generated this month

    cumulative = {}
    if CUMULATIVE.exists():
        with open(CUMULATIVE, 'r', encoding='utf-8') as f:
            cumulative = json.load(f)

    month_entries = [e for e in entries if e['date'][:7] == this_month]
    cx = [e for e in month_entries if e.get('complex')]
    sx = [e for e in month_entries if not e.get('complex')]

    report = f"""# Session Cost Report — {this_month}

## Summary
- Total sessions: {len(month_entries)}
- Complex: {len(cx)} · Simple: {len(sx)}
- Total edits: {sum(e['edits'] for e in month_entries)}
- Complex avg: {sum(e['edits'] for e in cx)//max(len(cx),1) if cx else 0} edits/session

## Cumulative
- All-time sessions: {cumulative.get('total_sessions', '?')}
- All-time edits: {cumulative.get('total_edits', '?')}

## Layer 3 Recommendations
Based on 30+ sessions of data, the system can now:
1. Compare simple vs complex session costs with statistical confidence
2. Identify the most expensive session type and suggest targeted optimization
3. Project monthly token savings for any proposed config change

## Raw Data
See `~/.claude/session-data/cost-log.jsonl`
"""
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

def maybe_archive():
    """Archive cost-log entries older than 90 days to quarterly files."""
    entries = read_all()
    if len(entries) < 100:
        return  # Don't bother archiving small datasets

    cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    old = [e for e in entries if e['date'] < cutoff]
    if len(old) < 50:
        return

    # Group by quarter
    quarters = {}
    for e in old:
        d = datetime.date.fromisoformat(e['date'])
        q = f'{d.year}-Q{(d.month-1)//3+1}'
        quarters.setdefault(q, []).append(e)

    for q, q_entries in quarters.items():
        qf = ARCHIVE / f'{q}.jsonl'
        if not qf.exists():
            with open(qf, 'w', encoding='utf-8') as f:
                for e in q_entries:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')

    # Keep last 90 days in main log
    recent = [e for e in entries if e['date'] >= cutoff]
    with open(LOG, 'w', encoding='utf-8') as f:
        for e in recent:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'show'

    if action == 'record':
        edits = int(os.environ.get('EDIT_COUNT', 0))
        dur = int(os.environ.get('SESSION_DURATION_MIN', 0))
        entry = record(edits, dur)
        print(f'Recorded: {entry["date"]} {entry["time"]} · {edits} edits · {dur}min')
        maybe_archive()
        maybe_generate_report()

    elif action == 'show':
        print(show())

    elif action == 'cumulative':
        if CUMULATIVE.exists():
            with open(CUMULATIVE, 'r', encoding='utf-8') as f:
                c = json.load(f)
            print(f"All-time: {c['total_sessions']} sessions · {c['total_edits']} edits")
            print(f"Complex: {c['complex_sessions']} · Simple: {c['simple_sessions']}")
            print(f"Week: {c['week']['sessions']} sessions · Month: {c['month']['sessions']} sessions")
        else:
            print("No data yet.")

    elif action == 'structure':
        print("session-data/")
        print("├── cost-log.jsonl       # Per-session records")
        print("├── cumulative.json       # Running totals")
        print("├── reports/              # Monthly reports (L3+)")
        if REPORTS.exists():
            for f in sorted(REPORTS.glob('*.md')):
                print(f"│   └── {f.name}")
        print("└── archive/              # Quarterly archives (90d+)")
        if ARCHIVE.exists():
            for f in sorted(ARCHIVE.glob('*.jsonl')):
                print(f"    └── {f.name}")
