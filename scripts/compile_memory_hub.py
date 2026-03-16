#!/usr/bin/env python3
import argparse, collections, datetime, glob, json, os, re, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources")
CANON = os.path.join(ROOT, "canonical")
STATE = os.path.join(ROOT, "state")
LOCK_PATH = os.path.join(STATE, "lock.json")
RUNTIME = os.path.join(STATE, "runtime")
STATE_PATH = os.path.join(RUNTIME, "compiler-state.json")
LOG_PATH = os.path.join(RUNTIME, "compile-log.md")
LEGACY_STATE_PATH = os.path.join(STATE, "compiler-state.json")
LEGACY_LOG_PATH = os.path.join(STATE, "compile-log.md")
LOCK_TTL_SECONDS = 600

from event_utils import make_fingerprint, normalize_summary, tokenize_for_similarity, jaccard_similarity


def now_local():
    return datetime.datetime.now(datetime.timezone.utc).astimezone()


def load_events():
    files = glob.glob(os.path.join(SOURCES, "*", "*.ndjson"))
    events = []
    errors = []
    for p in sorted(files):
        with open(p, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    e["_file"] = p
                    e["_line"] = i
                    if not e.get("fingerprint"):
                        e["fingerprint"] = make_fingerprint(
                            e.get("kind"),
                            e.get("scope"),
                            e.get("summary"),
                            e.get("project"),
                        )
                    events.append(e)
                except Exception as exc:
                    errors.append(
                        {
                            "file": p,
                            "line": i,
                            "error": str(exc),
                            "content": line[:200],
                        }
                    )
    return files, events, errors


def filter_superseded(events):
    """Remove events that have been superseded by newer events."""
    superseded_ids = set()
    for e in events:
        for sid in e.get("supersedes") or []:
            superseded_ids.add(sid)
    if not superseded_ids:
        return events, 0
    kept = [e for e in events if e.get("event_id") not in superseded_ids]
    return kept, len(events) - len(kept)


def filter_expired(events):
    """Remove events whose valid_until date has passed."""
    today = now_local().strftime("%Y-%m-%d")
    kept = []
    expired_count = 0
    for e in events:
        valid_until = e.get("valid_until")
        if valid_until and valid_until < today:
            expired_count += 1
        else:
            kept.append(e)
    return kept, expired_count


def dedup(events):
    seen = set()
    uniq = []
    for e in events:
        k = e.get("fingerprint") or make_fingerprint(
            e.get("kind"),
            e.get("scope"),
            e.get("summary"),
            e.get("project"),
        )
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    return sorted(uniq, key=lambda x: x.get("ts", ""))


CONFLICT_SIMILARITY_THRESHOLD = 0.35


def detect_conflicts(events):
    """Detect potential conflicts: same scope+kind, different fingerprints,
    but high token overlap in summary.  Returns list of (event_a, event_b, similarity)."""
    conflicts = []
    by_group = collections.defaultdict(list)
    for e in events:
        key = (e.get("scope"), e.get("kind"))
        by_group[key].append(e)

    for (scope, kind), group in by_group.items():
        if scope not in ("profile", "stable"):
            continue
        n = len(group)
        for i in range(n):
            tok_i = tokenize_for_similarity(group[i].get("summary"))
            for j in range(i + 1, n):
                if group[i].get("fingerprint") == group[j].get("fingerprint"):
                    continue
                tok_j = tokenize_for_similarity(group[j].get("summary"))
                sim = jaccard_similarity(tok_i, tok_j)
                if sim >= CONFLICT_SIMILARITY_THRESHOLD:
                    conflicts.append((group[i], group[j], sim))
    conflicts.sort(key=lambda x: -x[2])
    return conflicts


def render_event_line(event, include_ts=False, include_kind=False):
    parts = []
    if include_ts:
        parts.append(f"[{event.get('ts', '?')}]")
    if include_kind:
        parts.append(f"({event.get('kind', '?')})")
    parts.append(event.get("summary", "").strip())
    parts.append(f"[source: {event.get('source', '?')}]")
    return "- " + " ".join(part for part in parts if part)


def render(uniq, conflicts=None):
    by_scope = collections.defaultdict(list)
    for e in uniq:
        by_scope[e.get("scope", "fuzzy")].append(e)

    anchor = uniq[-1].get("ts") if uniq else "NO_EVENTS"
    out = {}

    def mk_head(title):
        return [f"# {title}", "", "> generated_by: memory-hub-compiler", f"> event_anchor_ts: {anchor}", ""]

    def emit(lines):
        return "\n".join(lines).rstrip() + "\n"

    source_counts = collections.Counter()
    source_last_ts = {}
    for event in uniq:
        source = event.get("source") or "unknown"
        source_counts[source] += 1
        source_last_ts[source] = event.get("ts") or "?"

    project_names = sorted({(e.get("project") or "general").strip() or "general" for e in by_scope.get("project", [])})

    idx = mk_head("canonical/index.md")
    idx += [
        "## Loading Protocol",
        "",
        "### L0 -- Soul (always, every turn)",
        "",
        "1. `SOUL.md`",
        "2. `IDENTITY.md`",
        "3. `USER.md`",
        "4. `VOICE.md`",
        "",
        "### L1 -- Memory (always, at session start)",
        "",
        "5. `canonical/index.md`",
        "6. `canonical/profile.md`",
        "7. `canonical/stable-memory.md`",
        "",
        "### L2 -- Context (on-demand only)",
        "",
        "8. `canonical/projects/<name>.md` -- when working on that project",
        "9. `canonical/fuzzy-memory.md` -- when recent context matters",
        "10. `canonical/agents/<source>.md` -- when provenance matters",
        "",
        "Default context: L0 + L1 ~= 250 lines (~4K tokens). Never load everything.",
        "",
        "## Active Sources",
        "",
    ]
    idx += [
        f"- `{source}`: {source_counts[source]} events, last={source_last_ts.get(source, '?')}"
        for source in sorted(source_counts)
    ] or ["- (no sources yet)"]
    idx += ["", "## Active Projects", ""]
    idx += [f"- `{name}` -> `canonical/projects/{name}.md`" for name in project_names] or ["- (no project events yet)"]
    out[os.path.join(CANON, "index.md")] = emit(idx)

    p = mk_head("canonical/profile.md")
    p += [render_event_line(e) for e in by_scope.get("profile", [])[-50:]] or ["- (no profile events yet)"]
    out[os.path.join(CANON, "profile.md")] = emit(p)

    s = mk_head("canonical/stable-memory.md")
    stable_events = by_scope.get("stable", [])
    sections = [
        ("Decisions", [e for e in stable_events if e.get("kind") == "decision"]),
        ("Rules", [e for e in stable_events if e.get("kind") == "rule"]),
        ("Facts", [e for e in stable_events if e.get("kind") == "fact"]),
        (
            "Other",
            [e for e in stable_events if e.get("kind") not in {"decision", "rule", "fact"}],
        ),
    ]
    for title, items in sections:
        if not items:
            continue
        s += [f"## {title}", ""]
        s += [render_event_line(e) for e in items[-40:]]
        s += [""]
    if len(s) == 5:
        s += ["- (no stable events yet)"]
    out[os.path.join(CANON, "stable-memory.md")] = emit(s)

    fz = mk_head("canonical/fuzzy-memory.md")
    fz += [render_event_line(e, include_ts=True) for e in by_scope.get("fuzzy", [])[-120:]] or ["- (no fuzzy events yet)"]
    out[os.path.join(CANON, "fuzzy-memory.md")] = emit(fz)

    projs = collections.defaultdict(list)
    for e in by_scope.get("project", []):
        name = (e.get("project") or "general").strip() or "general"
        projs[name].append(e)
    if not projs:
        projs["general"] = []

    for name, arr in projs.items():
        pp = mk_head(f"canonical/projects/{name}.md")
        pp += [render_event_line(e, include_ts=True, include_kind=True) for e in arr[-160:]] or ["- (no events yet)"]
        out[os.path.join(CANON, "projects", f"{name}.md")] = emit(pp)

    by_source = collections.defaultdict(list)
    for event in uniq:
        by_source[event.get("source") or "unknown"].append(event)
    for source, arr in by_source.items():
        sp = mk_head(f"canonical/agents/{source}.md")
        sp += [
            f"## Participant",
            "",
            f"- `{source}`",
            "",
            "## Recent Shared Events",
            "",
        ]
        sp += [render_event_line(e, include_ts=True, include_kind=True) for e in arr[-160:]] or ["- (no events yet)"]
        out[os.path.join(CANON, "agents", f"{source}.md")] = emit(sp)

    # conflicts.md
    cf = mk_head("canonical/conflicts.md")
    if conflicts:
        cf += [
            f"Found {len(conflicts)} potential conflict(s).  Review and resolve by",
            "writing a new event with `supersedes` pointing to the outdated event_id(s).",
            "",
        ]
        for a, b, sim in conflicts:
            cf += [
                f"### similarity {sim:.0%} — {a.get('scope')}/{a.get('kind')}",
                "",
                f"- A `{a.get('event_id')}` [{a.get('source')}] {a.get('summary', '').strip()[:120]}",
                f"- B `{b.get('event_id')}` [{b.get('source')}] {b.get('summary', '').strip()[:120]}",
                "",
            ]
    else:
        cf += ["No conflicts detected."]
    out[os.path.join(CANON, "conflicts.md")] = emit(cf)

    return out


def cleanup_generated_children(rendered):
    keep = {os.path.normpath(path) for path in rendered}
    for subdir in ("projects", "agents"):
        target = os.path.join(CANON, subdir)
        os.makedirs(target, exist_ok=True)
        for path in glob.glob(os.path.join(target, "*.md")):
            if os.path.normpath(path) not in keep:
                os.remove(path)


def acquire_lock():
    os.makedirs(STATE, exist_ok=True)
    now = now_local()
    if os.path.exists(LOCK_PATH):
        try:
            with open(LOCK_PATH, "r", encoding="utf-8") as f:
                lock = json.load(f)
            exp = datetime.datetime.fromisoformat(lock.get("expires_at"))
            if exp > now:
                return False, lock
        except Exception:
            pass
    lock = {
        "locked_by": "memory-hub-compiler",
        "run_id": str(uuid.uuid4()),
        "started_at": now.isoformat(),
        "expires_at": (now + datetime.timedelta(seconds=LOCK_TTL_SECONDS)).isoformat(),
    }
    with open(LOCK_PATH, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)
    return True, lock


def release_lock():
    if os.path.exists(LOCK_PATH):
        os.remove(LOCK_PATH)


def update_state(last_ts, changed):
    state = {
        "version": 1,
        "lastRunAt": now_local().isoformat(),
        "lastProcessedTs": last_ts,
        "lastProcessedEventId": None,
        "lastChangeCount": changed,
        "notes": "Updated by compile_memory_hub.py",
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def cleanup_legacy_runtime_files():
    for p in (LEGACY_STATE_PATH, LEGACY_LOG_PATH):
        if os.path.exists(p):
            os.remove(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write canonical files")
    ap.add_argument("--fuzzy-days", type=int, default=None,
                    help="exclude fuzzy events older than N days from canonical output (sources are never modified)")
    args = ap.parse_args()

    got, lock = acquire_lock()
    if not got:
        print(json.dumps({"status": "skipped", "reason": "lock-active", "lock": lock}, ensure_ascii=False))
        return

    changed_files = 0
    try:
        files, events, errors = load_events()
        raw_count = len(events)
        if errors:
            report = [
                f"# Compile Report ({now_local().isoformat(timespec='seconds')})",
                "",
                f"- source files: {len(files)}",
                f"- raw events: {raw_count}",
                f"- invalid event lines: {len(errors)}",
                "",
                "## Invalid Lines",
                "",
            ]
            for err in errors[:20]:
                report.append(
                    f"- {err['file']}:{err['line']} :: {err['error']} :: {err['content']}"
                )
            if len(errors) > 20:
                report.append(f"- ... and {len(errors) - 20} more")
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write("\n".join(report) + "\n")
            print("\n".join(report))
            raise SystemExit(1)
        events, superseded_count = filter_superseded(events)
        events, expired_count = filter_expired(events)
        uniq = dedup(events)

        # Fuzzy TTL: exclude old fuzzy events from canonical output only.
        # sources/* are never modified — append-only is preserved.
        fuzzy_pruned = 0
        if args.fuzzy_days is not None:
            cutoff = now_local() - datetime.timedelta(days=args.fuzzy_days)
            before = len(uniq)
            def _keep(e):
                if e.get("scope") != "fuzzy":
                    return True
                ts_str = e.get("ts", "")
                try:
                    ts = datetime.datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=now_local().tzinfo)
                    return ts >= cutoff
                except ValueError:
                    return True
            uniq = [e for e in uniq if _keep(e)]
            fuzzy_pruned = before - len(uniq)

        conflicts = detect_conflicts(uniq)
        rendered = render(uniq, conflicts)

        os.makedirs(os.path.join(CANON, "projects"), exist_ok=True)
        os.makedirs(os.path.join(CANON, "agents"), exist_ok=True)
        os.makedirs(RUNTIME, exist_ok=True)
        cleanup_legacy_runtime_files()

        report = [
            f"# Compile Report ({now_local().isoformat(timespec='seconds')})",
            "",
            f"- source files: {len(files)}",
            f"- raw events: {raw_count}",
            f"- superseded events removed: {superseded_count}",
            f"- expired events removed: {expired_count}",
            f"- fuzzy events excluded (TTL): {fuzzy_pruned}",
            f"- unique events: {len(uniq)}",
            f"- potential conflicts: {len(conflicts)}",
            f"- mode: {'apply' if args.apply else 'dry-run'}",
            "",
        ]

        if args.apply:
            cleanup_generated_children(rendered)
            for p, content in rendered.items():
                old = ""
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        old = f.read()
                if old != content:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(content)
                    changed_files += 1
            report.append(f"- wrote canonical files: yes ({changed_files} changed)")
        else:
            report.append("- wrote canonical files: no")

        last_ts = uniq[-1].get("ts") if uniq else None
        update_state(last_ts, changed_files)

        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")

        print("\n".join(report))
    finally:
        release_lock()


if __name__ == "__main__":
    main()
