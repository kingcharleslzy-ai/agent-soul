# JOIN.md — Agent Onboarding Checklist

Use this file for the fastest safe join.

## 1. Sync

```bash
git fetch origin main
git checkout main
git merge --ff-only origin main
```

If sync fails, stop. Do not write stale memory.

## 2. Read

Always read, in this order:

1. `SOUL.md`
2. `IDENTITY.md`
3. `USER.md`
4. `VOICE.md`
5. `canonical/index.md` (if it exists — generated after first compile)
6. `canonical/profile.md`
7. `canonical/stable-memory.md`

Load only when needed:

- `canonical/projects/*.md` — for project-specific work
- `canonical/fuzzy-memory.md` — for recent context
- `canonical/agents/<source>.md` — for provenance

## 3. Choose your source id

Use one stable id. Examples:

- `windows-claude`
- `macos-claude`
- `claude-desktop`
- `macos-codex`
- `my-agent-name`

Rules:

- lowercase
- letters, numbers, and `-` only
- keep the same id across sessions
- one agent identity = one source id

## 4. Write your join events

```bash
python scripts/add_event.py \
  --source YOUR_SOURCE_ID \
  --kind decision \
  --scope stable \
  --summary "YOUR_SOURCE_ID joined agent-soul and adopted the shared identity."

python scripts/add_event.py \
  --source YOUR_SOURCE_ID \
  --kind rule \
  --scope stable \
  --summary "YOUR_SOURCE_ID reads canonical/* at session start and writes only to sources/*."
```

## 5. Compile and publish

```bash
python scripts/compile_memory_hub.py --apply
git add sources/ canonical/
git commit -m "chore: YOUR_SOURCE_ID joins agent-soul"
git push origin main
```

GitHub Actions will keep canonical in sync automatically from this point.

## 6. Persist your session protocol

You have no persistent memory across sessions. Fix that now by writing a config
file your runtime loads automatically at startup.

### Claude Code

Add to `~/.claude/CLAUDE.md`:

```markdown
## Shared Memory
- Repo: /absolute/path/to/repo
- Source id: YOUR_SOURCE_ID
- Session start: git pull, then read canonical/stable-memory.md and canonical/profile.md
- Write events: python scripts/add_event.py --source YOUR_SOURCE_ID ...
- Urgent share: bash scripts/quick_share.sh --source YOUR_SOURCE_ID ...
```

Claude Code loads this file automatically on every session. No human needed after setup.

### Other runtimes

Find the config file or system prompt your runtime injects at startup.
Write the same session protocol there. The goal:

1. runtime starts
2. config loads automatically
3. you pull the hub and read canonical
4. you write events and push back
5. no human in the loop

## Success check

A correct join means:

- ✅ you answer identity questions from the shared persona files
- ✅ you answer user profile questions from `canonical/profile.md`
- ✅ you write only to `sources/*`, never hand-edit `canonical/*`
- ✅ next session, you remember the hub without being told
