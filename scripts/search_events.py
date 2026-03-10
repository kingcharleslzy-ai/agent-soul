#!/usr/bin/env python3
"""Search memory-hub source events by scope, kind, source, project, or keyword.

Examples:
  python scripts/search_events.py --query "memory-hub"
  python scripts/search_events.py --scope stable --kind decision
  python scripts/search_events.py --source windows-codex --limit 20
  python scripts/search_events.py --scope project --project memory-hub
  python scripts/search_events.py --query rebase --json
"""
import argparse
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources")


def load_events():
    events = []
    for path in sorted(glob.glob(os.path.join(SOURCES, "*", "*.ndjson"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    events.append(json.loads(stripped))
                except json.JSONDecodeError:
                    pass
    return events


def matches(event, args):
    if args.scope and event.get("scope") != args.scope:
        return False
    if args.kind and event.get("kind") != args.kind:
        return False
    if args.source and event.get("source") != args.source:
        return False
    if args.project and event.get("project") != args.project:
        return False
    if args.query:
        text = " ".join([
            event.get("summary", ""),
            event.get("project") or "",
            event.get("source") or "",
        ]).lower()
        if not all(q.lower() in text for q in args.query):
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description="Search memory-hub source events")
    ap.add_argument("--scope", choices=["profile", "stable", "fuzzy", "project"])
    ap.add_argument("--kind", choices=["preference", "decision", "fact", "project-update", "temporary", "rule"])
    ap.add_argument("--source", help="Filter by source id")
    ap.add_argument("--project", help="Filter by project name")
    ap.add_argument("--query", nargs="+", help="Keywords (AND logic) matched against summary")
    ap.add_argument("--limit", type=int, default=50, help="Max results, most recent first (default: 50)")
    ap.add_argument("--json", action="store_true", help="Output raw JSON lines")
    args = ap.parse_args()

    events = [e for e in load_events() if matches(e, args)]
    events = events[-args.limit:]

    if not events:
        print("No matching events.")
        return

    for e in events:
        if args.json:
            print(json.dumps(e, ensure_ascii=False))
        else:
            ts = (e.get("ts") or "?")[:16]
            source = e.get("source", "?")
            scope = e.get("scope", "?")
            kind = e.get("kind", "?")
            summary = e.get("summary", "").strip()
            project = f" [{e['project']}]" if e.get("project") else ""
            print(f"[{ts}] {source} | {scope}/{kind}{project} | {summary[:120]}")

    print(f"\n{len(events)} result(s)")


if __name__ == "__main__":
    main()
