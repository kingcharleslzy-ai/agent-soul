# SCHEMA.md — Event Format Specification

## Goal

Carry memory increments across devices and agents using a unified NDJSON event format.

Each participant appends only to `sources/<source>/YYYY-MM-DD.ndjson`.
The compiler merges all streams into `canonical/*`.

## File Convention

- Path: `sources/<source>/YYYY-MM-DD.ndjson`
- Encoding: UTF-8
- Format: one JSON object per line (NDJSON)

## Choosing a Source ID

Rules:

- lowercase letters, numbers, and `-` only
- keep it stable over time — one agent identity should use one source id always

Examples: `windows-claude`, `macos-codex`, `claude-desktop`, `my-custom-agent`

## Event Structure

```json
{
  "event_id": "uuid-v4",
  "source": "windows-claude",
  "ts": "2026-01-01T10:00:00+00:00",
  "kind": "decision",
  "scope": "stable",
  "summary": "Agreed to use TypeScript for all new services.",
  "project": "my-project",
  "importance": 0.9,
  "fingerprint": "sha256:..."
}
```

## Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `event_id` | yes | Globally unique UUID |
| `source` | yes | Your stable source id |
| `ts` | yes | ISO-8601 timestamp with timezone |
| `kind` | yes | `preference` / `decision` / `fact` / `project-update` / `temporary` / `rule` |
| `scope` | yes | `profile` / `stable` / `fuzzy` / `project` |
| `summary` | yes | Short summary — no raw transcripts |
| `project` | when `scope=project` | Project name |
| `importance` | optional | 0.0–1.0 |
| `fingerprint` | recommended | Dedup fingerprint |
| `supersedes` | optional | `["event_id_1", ...]` — marks older events as replaced |

## Scope Reference

| Scope | Use for |
|-------|---------|
| `profile` | Stable user preferences and identity facts |
| `stable` | Durable decisions, rules, reusable facts |
| `project` | Project progress, constraints, decisions |
| `fuzzy` | Recent context, temporary notes (prunable) |

## Fingerprint Rules

Fingerprint for deduplication should be source-agnostic, based on:

- `kind` + `scope` + `project` + normalized `summary`

Do not include `source` — the same fact from two agents should not appear twice in canonical.

## Superseding Old Events

When new information replaces old, write a new event with `supersedes`:

```json
{
  "event_id": "new-uuid",
  "source": "windows-claude",
  "kind": "preference",
  "scope": "profile",
  "summary": "User prefers light mode.",
  "supersedes": ["old-event-id-1"]
}
```

The compiler removes superseded events before building canonical.

## Write Constraints

- Write 3–8 high-value events per task
- Summaries only — no raw transcripts
- Append only — do not rewrite history
- When facts conflict, keep both; the compiler detects and reports conflicts
