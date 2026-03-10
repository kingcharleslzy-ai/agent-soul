#!/usr/bin/env python3
"""Validate all NDJSON event files in sources/."""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources")

ALLOWED_KIND = {"preference", "decision", "fact", "project-update", "temporary", "rule"}
ALLOWED_SCOPE = {"profile", "stable", "fuzzy", "project"}
SOURCE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SUMMARY_MIN_LEN = 8
SUMMARY_MAX_LEN = 250


def validate_event(event, file_path, line_num):
    errors = []

    for field in ("event_id", "source", "ts", "kind", "scope", "summary"):
        if not event.get(field):
            errors.append(f"missing required field: {field}")

    source = event.get("source", "")
    if source and not SOURCE_RE.match(source):
        errors.append(f"invalid source id: {source}")

    kind = event.get("kind", "")
    if kind and kind not in ALLOWED_KIND:
        errors.append(f"invalid kind: {kind}")

    scope = event.get("scope", "")
    if scope and scope not in ALLOWED_SCOPE:
        errors.append(f"invalid scope: {scope}")

    summary = (event.get("summary") or "").strip()
    if summary and len(summary) < SUMMARY_MIN_LEN:
        errors.append(f"summary too short ({len(summary)} chars)")
    if summary and len(summary) > SUMMARY_MAX_LEN:
        errors.append(f"summary too long ({len(summary)} chars)")

    if scope == "project" and not event.get("project"):
        errors.append("scope=project requires project field")

    importance = event.get("importance")
    if importance is not None:
        if not isinstance(importance, (int, float)) or not (0.0 <= importance <= 1.0):
            errors.append(f"importance must be 0.0-1.0, got {importance}")

    supersedes = event.get("supersedes")
    if supersedes is not None:
        if not isinstance(supersedes, list):
            errors.append("supersedes must be a list of event_id strings")
        else:
            for sid in supersedes:
                if not isinstance(sid, str) or len(sid) < 8:
                    errors.append(f"invalid supersedes entry: {sid}")

    return errors


def main():
    files = sorted(glob.glob(os.path.join(SOURCES, "*", "*.ndjson")))
    total_events = 0
    total_errors = 0

    for path in files:
        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                total_events += 1
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"ERROR {path}:{line_num} invalid JSON: {exc}")
                    total_errors += 1
                    continue

                errors = validate_event(event, path, line_num)
                for err in errors:
                    print(f"ERROR {path}:{line_num} {err}")
                    total_errors += 1

    print(f"\nValidated {total_events} events in {len(files)} files, {total_errors} errors.")
    if total_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
