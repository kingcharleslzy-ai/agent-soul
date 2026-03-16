# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v2.1.0] - 2026-03-16

### Added

- Published to **ClawHub** as `soul-sharing` — install via `npx clawhub install soul-sharing`.
- `scripts/prune_fuzzy.py` — TTL-based cleanup of old fuzzy events.
- `scripts/dedup_profile.py` — detect and resolve duplicate profile events.
- ClawHub badge in README.

### Changed

- README updated with ClawHub install section and file tree.
- Both new scripts use locale-aware timezone (`utc.astimezone()`) instead of hardcoded UTC+8.

## [v2.0.0] - 2026-03-16

### Added

- `soul.json` manifest — standardized entry point with version, loading protocol, and file pointers.
- **Three-level loading protocol (L0/L1/L2)** — keeps default context at ~4K tokens.
  - L0 Soul: SOUL.md + IDENTITY.md + USER.md + VOICE.md (always load)
  - L1 Memory: canonical/index.md + profile.md + stable-memory.md (always load)
  - L2 Context: projects/\* + fuzzy + agents/\* (on-demand only)
- `valid_until` field — temporal expiry for events; compiler auto-filters past expiration date.
- Updated comparison table with Graphiti/Zep and context overhead column.

### Changed

- README fully rewritten with architecture diagram, L0/L1/L2 protocol, and cleaner Quick Start.
- JOIN.md updated to use L0/L1/L2 terminology.
- Compiler index.md output now shows Loading Protocol with L0/L1/L2 sections.
- `add_event.py` now supports `--valid-until` flag.
- `compile_memory_hub.py` now filters expired events before dedup.

## [v0.1.0] - 2026-03-10

### Added

- Initial release of agent‑soul with Git‑native shared memory and identity layer.
- Supports sharing memory across Claude Code, Codex and OpenClaw runtimes.
- Provides scripts to add and compile memory events and validate JSON sources.
- Includes comprehensive README and quick‑start guide.
