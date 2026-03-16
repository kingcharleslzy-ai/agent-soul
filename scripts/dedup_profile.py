#!/usr/bin/env python3
"""Detect and resolve duplicate / near-duplicate profile events.

Usage:
    python scripts/dedup_profile.py              # dry-run: show duplicates
    python scripts/dedup_profile.py --apply      # write superseding events
    python scripts/dedup_profile.py --scope stable  # also check stable scope
"""
import argparse
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from event_utils import day_str, make_fingerprint, now_iso, tokenize_for_similarity, jaccard_similarity

SOURCES = os.path.join(ROOT, "sources")
DEFAULT_SIMILARITY_THRESHOLD = 0.35
_threshold = DEFAULT_SIMILARITY_THRESHOLD


def load_all_events():
    import glob

    events = []
    for f in sorted(glob.glob(os.path.join(SOURCES, "*", "*.ndjson"))):
        with open(f, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    e["_file"] = f
                    events.append(e)
                except json.JSONDecodeError:
                    pass
    return events


def filter_active(events):
    """Remove already-superseded events."""
    superseded_ids = set()
    for e in events:
        for sid in e.get("supersedes") or []:
            superseded_ids.add(sid)
    return [e for e in events if e.get("event_id") not in superseded_ids]


def find_duplicate_groups(events, scopes):
    """Group events by scope+kind, then find clusters with high similarity."""
    by_group = collections.defaultdict(list)
    for e in events:
        if e.get("scope") in scopes:
            by_group[(e.get("scope"), e.get("kind"))].append(e)

    groups = []
    for (_scope, _kind), members in by_group.items():
        members = sorted(members, key=lambda x: x.get("ts", ""))
        n = len(members)
        merged = [False] * n
        for i in range(n):
            if merged[i]:
                continue
            cluster = [members[i]]
            tok_i = tokenize_for_similarity(members[i].get("summary"))
            for j in range(i + 1, n):
                if merged[j]:
                    continue
                tok_j = tokenize_for_similarity(members[j].get("summary"))
                if jaccard_similarity(tok_i, tok_j) >= _threshold:
                    cluster.append(members[j])
                    merged[j] = True
            if len(cluster) > 1:
                groups.append(cluster)
    return groups


def main():
    ap = argparse.ArgumentParser(description="Detect and resolve duplicate profile events")
    ap.add_argument("--apply", action="store_true", help="write superseding events")
    ap.add_argument("--scope", nargs="*", default=["profile"], help="scopes to check (default: profile)")
    ap.add_argument("--source", default="memory-hub-dedup", help="source id for dedup events")
    ap.add_argument("--threshold", type=float, default=DEFAULT_SIMILARITY_THRESHOLD, help="similarity threshold")
    args = ap.parse_args()

    global _threshold
    _threshold = args.threshold

    all_events = load_all_events()
    active = filter_active(all_events)
    groups = find_duplicate_groups(active, set(args.scope))

    if not groups:
        print(f"No duplicates found in scope(s) {args.scope} (threshold={args.threshold:.0%}).")
        return

    print(f"Found {len(groups)} duplicate group(s):\n")
    supersede_actions = []

    for gi, cluster in enumerate(groups, 1):
        cluster_sorted = sorted(cluster, key=lambda x: x.get("ts", ""))
        keeper = cluster_sorted[-1]
        obsolete = cluster_sorted[:-1]

        print(f"Group {gi}: keep latest, supersede {len(obsolete)} older event(s)")
        print(f"  KEEP:  [{keeper.get('source')}] {keeper.get('summary', '').strip()[:100]}")
        for o in obsolete:
            print(f"  DROP:  [{o.get('source')}] {o.get('summary', '').strip()[:100]}")
            print(f"         event_id={o.get('event_id')}")
        print()

        supersede_actions.append({
            "keeper": keeper,
            "obsolete_ids": [o.get("event_id") for o in obsolete],
        })

    if not args.apply:
        print("Dry run. Use --apply to write superseding events.")
        return

    written = 0
    for action in supersede_actions:
        keeper = action["keeper"]
        event = {
            "event_id": str(__import__("uuid").uuid4()),
            "source": args.source,
            "ts": now_iso(),
            "kind": keeper.get("kind", "preference"),
            "scope": keeper.get("scope", "profile"),
            "summary": keeper.get("summary", "").strip(),
            "project": keeper.get("project"),
            "importance": keeper.get("importance", 0.5),
            "fingerprint": make_fingerprint(
                keeper.get("kind"), keeper.get("scope"),
                keeper.get("summary"), keeper.get("project"),
            ),
            "supersedes": action["obsolete_ids"],
        }

        out_dir = os.path.join(SOURCES, args.source)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{day_str()}.ndjson")
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        written += 1

    print(f"Wrote {written} superseding event(s) to sources/{args.source}/")
    print("Run the compiler to update canonical output.")


if __name__ == "__main__":
    main()
