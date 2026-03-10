#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v python3 &>/dev/null; then PYTHON=python3; else PYTHON=python; fi

# 1) pull latest shared state
git fetch origin main
git merge --ff-only origin/main

# 2) mirror local OpenClaw memory into mirrors/* (backup/audit only; not staged to git)
bash scripts/sync_workspace_memory.sh

# 3) compile canonical from sources
"$PYTHON" scripts/compile_memory_hub.py --apply

# 4) distribute fresh canonical to local allowed participants
bash scripts/sync_cloud_to_workspace.sh

# 5) stage shared state (mirrors excluded — audit-only, lives in .gitignore)
git add canonical sources

# 6) no-op guard
if git diff --cached --quiet; then
  echo "NO_CHANGES"
  exit 0
fi

# 7) commit & push with retry
git commit -m "chore(memory-hub): compile canonical from sources"

for attempt in 1 2 3; do
  if git push origin main; then
    echo "CHANGES_PUSHED"
    exit 0
  fi
  echo "push failed (attempt $attempt/3), rebasing..."
  git fetch origin main
  git rebase origin/main
  # Rebase may have brought new sources — recompile and re-distribute
  "$PYTHON" scripts/compile_memory_hub.py --apply
  bash scripts/sync_cloud_to_workspace.sh
  git add canonical sources
  if ! git diff --cached --quiet; then
    git commit -m "chore(memory-hub): recompile after rebase"
  fi
done

echo "PUSH_FAILED after 3 attempts" >&2
exit 1
