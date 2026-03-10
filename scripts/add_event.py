#!/usr/bin/env python3
import argparse
import json
import os
import re
import uuid

from event_utils import day_str, make_fingerprint, now_iso


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources")

ALLOWED_KIND = {"preference", "decision", "fact", "project-update", "temporary", "rule"}
ALLOWED_SCOPE = {"profile", "stable", "fuzzy", "project"}
SOURCE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SUMMARY_MIN_LEN = 8
SUMMARY_MAX_LEN = 250


def main():
    ap = argparse.ArgumentParser(description="Append one memory-hub v2 event")
    ap.add_argument("--source", required=True, help="unique source id, e.g. openclaw-kemi or macos-codex")
    ap.add_argument("--kind", required=True, choices=sorted(ALLOWED_KIND))
    ap.add_argument("--scope", required=True, choices=sorted(ALLOWED_SCOPE))
    ap.add_argument("--summary", required=True)
    ap.add_argument("--project", default=None)
    ap.add_argument("--importance", type=float, default=0.5)
    ap.add_argument("--supersedes", nargs="*", default=None, help="event_ids this event replaces")
    args = ap.parse_args()

    if args.scope == "project" and not args.project:
        raise SystemExit("scope=project requires --project")

    if not (0.0 <= args.importance <= 1.0):
        raise SystemExit("importance must be between 0.0 and 1.0")

    if not SOURCE_RE.match(args.source):
        raise SystemExit("source must match ^[a-z0-9][a-z0-9-]{1,63}$")

    summary = args.summary.strip()
    if len(summary) < SUMMARY_MIN_LEN:
        raise SystemExit(f"summary too short ({len(summary)} chars, min {SUMMARY_MIN_LEN})")
    if len(summary) > SUMMARY_MAX_LEN:
        raise SystemExit(f"summary too long ({len(summary)} chars, max {SUMMARY_MAX_LEN})")

    event = {
        "event_id": str(uuid.uuid4()),
        "source": args.source,
        "ts": now_iso(),
        "kind": args.kind,
        "scope": args.scope,
        "summary": args.summary.strip(),
        "project": args.project,
        "importance": round(args.importance, 3),
        "fingerprint": make_fingerprint(args.kind, args.scope, args.summary, args.project),
    }
    if args.supersedes:
        event["supersedes"] = args.supersedes

    out_dir = os.path.join(SOURCES, args.source)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{day_str()}.ndjson")

    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "path": out_path, "event": event}, ensure_ascii=False))


if __name__ == "__main__":
    main()
