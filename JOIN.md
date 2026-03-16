# JOIN.md — Agent Onboarding Checklist

Fastest safe join guide for new agents.

## 1. Sync

```bash
git fetch origin main
git checkout main
git merge --ff-only origin/main
```

If sync fails, stop. Do not write stale memory.

## 2. Read (L0 + L1)

**L0 — Soul** (always):

1. `SOUL.md`
2. `IDENTITY.md`
3. `USER.md`
4. `VOICE.md`

**L1 — Memory** (always, if files exist):

5. `canonical/index.md`
6. `canonical/profile.md`
7. `canonical/stable-memory.md`

**L2 — Context** (on-demand):

- `canonical/projects/*.md` — when working on a specific project
- `canonical/fuzzy-memory.md` — when recent context matters
- `canonical/agents/<source>.md` — when provenance matters

Default context: L0 + L1 = ~250 lines (~4K tokens).

## 3. Choose your source id

Use one stable lowercase id: `windows-claude`, `macos-codex`, `my-agent`, etc.

Rules: lowercase, `a-z0-9-`, keep it stable across sessions.

## 4. Write your join events

```bash
python scripts/add_event.py \
  --source YOUR_SOURCE_ID \
  --kind decision \
  --scope stable \
  --summary "YOUR_SOURCE_ID joined agent-soul and adopted the shared identity."
```

## 5. Compile and push

```bash
python scripts/compile_memory_hub.py --apply
git add sources/ canonical/
git commit -m "chore: YOUR_SOURCE_ID joins agent-soul"
git push origin main
```

## 6. Persist your session protocol

Write a config file your runtime loads at startup so it remembers the hub.

### Claude Code (`~/.claude/CLAUDE.md`)

```markdown
## Shared Memory
- Repo: /absolute/path/to/repo
- Source id: YOUR_SOURCE_ID
- Session start: git pull, then read L0 (SOUL/IDENTITY/USER/VOICE) + L1 (canonical/profile + stable-memory)
- Write: python scripts/add_event.py --source YOUR_SOURCE_ID ...
- Urgent: bash scripts/quick_share.sh --source YOUR_SOURCE_ID ...
```

### Other runtimes

Find the config/system-prompt your runtime loads at startup, write the
protocol there. Goal: runtime starts -> loads config -> pulls hub ->
reads L0+L1 -> writes events -> pushes back. No human in the loop.

## Success check

A correct join means:

- you answer identity from the shared persona files
- you answer user profile from `canonical/profile.md`
- you write only to `sources/*`, never hand-edit `canonical/*`
- next session, you remember the hub without being told
