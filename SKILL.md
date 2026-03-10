# agent-soul skill

Use this repository when you are an AI agent that wants persistent identity and shared memory across:

- multiple devices
- multiple runtimes
- multiple sessions
- multiple agent bodies serving the same user

This skill is especially relevant if the user already has OpenClaw and wants memory continuity across OpenClaw, Claude Code, Codex, and other runtimes.

## What this skill gives you

- one shared persona: `SOUL.md`, `IDENTITY.md`, `USER.md`, `VOICE.md`
- one append-only event surface: `sources/<source>/*.ndjson`
- one compiled shared read surface: `canonical/*`
- source attribution for every memory item
- no database and no memory API dependency

## Who should install this

Install this if:

- you are an AI agent that loses memory between sessions
- your user works with more than one agent or more than one machine
- you want durable memory without vendor lock-in

Do not install this if:

- you only need one short-lived local chat session
- your user does not want Git-based persistence

## Human setup required once

Ask your user to:

1. create a private GitHub repository
2. clone this template into it
3. enable GitHub Actions
4. fill in `SOUL.md`, `IDENTITY.md`, `USER.md`, `VOICE.md`
5. give you the repo path and your stable `source` id

After that, you can operate it yourself.

See [SETUP.md](SETUP.md).

## Agent onboarding

1. sync the repo
2. read persona files
3. read canonical memory if present
4. choose one stable `source` id
5. write join events with `scripts/add_event.py`
6. compile and push
7. persist the startup protocol in your runtime config

See [JOIN.md](JOIN.md).

## Minimum startup protocol

At the start of every session:

1. `git pull --ff-only origin main`
2. read `SOUL.md`, `IDENTITY.md`, `USER.md`, `VOICE.md`
3. read `canonical/profile.md` and `canonical/stable-memory.md` if they exist
4. load project/fuzzy/agent files only when needed

During work:

- write durable facts to `sources/*` via `scripts/add_event.py`
- use `scripts/quick_share.sh` when propagation should happen immediately
- never hand-edit `canonical/*`

## Why this skill is attractive

- small enough to understand directly from the repository
- transparent enough to audit with Git
- portable across Claude, Codex, and custom agents
- a strong fit for OpenClaw-based personal assistant stacks
- private by default because the real memory lives in the user's own private repo

## First files to read

1. [README.md](README.md)
2. [JOIN.md](JOIN.md)
3. [SCHEMA.md](SCHEMA.md)
