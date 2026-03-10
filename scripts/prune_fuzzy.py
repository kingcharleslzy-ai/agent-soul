#!/usr/bin/env python3
"""Prune fuzzy-scope events older than --days (default 30).

Dry-run by default; pass --apply to write changes.

Examples:
  python scripts/prune_fuzzy.py              # dry-run, 30-day cutoff
  python scripts/prune_fuzzy.py --days 14   # dry-run, 14-day cutoff
  python scripts/prune_fuzzy.py --apply     # write changes
"""
import argparse
import datetime
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources")
TZ = datetime.timezone(datetime.timedelta(hours=8))


def main():
    ap = argparse.ArgumentParser(description="Prune old fuzzy events from sources")
    ap.add_argument("--days", type=int, default=30, help="Cutoff in days (default: 30)")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = ap.parse_args()

    cutoff = datetime.datetime.now(TZ) - datetime.timedelta(days=args.days)
    files = sorted(glob.glob(os.path.join(SOURCES, "*", "*.ndjson")))

    total_kept = 0
    total_pruned = 0

    for path in files:
        kept_lines = []
        pruned_count = 0

        with open(path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    event = json.loads(stripped)
                except json.JSONDecodeError:
                    kept_lines.append(stripped)
                    continue

                if event.get("scope") == "fuzzy":
                    ts_str = event.get("ts", "")
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=TZ)
                        if ts < cutoff:
                            pruned_count += 1
                            continue
                    except ValueError:
                        pass

                kept_lines.append(stripped)

        total_pruned += pruned_count
        total_kept += len(kept_lines)

        if pruned_count == 0:
            continue

        label = "PRUNE" if args.apply else "DRY"
        print(f"{label} {path}: -{pruned_count} fuzzy events")

        if args.apply:
            if kept_lines:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(kept_lines) + "\n")
            else:
                os.remove(path)
                print(f"  removed empty file: {path}")

    mode = "Applied" if args.apply else "Dry-run"
    print(
        f"\n{mode}: kept {total_kept}, pruned {total_pruned} fuzzy event(s)"
        f" (cutoff: {cutoff.date()}, --days {args.days})"
    )
    if not args.apply and total_pruned > 0:
        print("Re-run with --apply to write changes.")


if __name__ == "__main__":
    main()
