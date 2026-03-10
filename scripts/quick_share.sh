#!/usr/bin/env bash
# quick_share.sh — fast-path: add one event, compile, and push immediately.
# Skips mirror sync. Use when cross-agent propagation is time-sensitive.
#
# Usage:
#   bash scripts/quick_share.sh \
#     --source windows-codex --kind decision --scope stable \
#     --summary "We decided X" [--project NAME] [--importance 0.8] \
#     [--supersedes EVENT_ID ...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v python3 &>/dev/null; then PYTHON=python3; else PYTHON=python; fi

# 1) validate & append event
"$PYTHON" scripts/add_event.py "$@"

# 2) pull latest to minimise conflicts
git fetch origin main
git merge --ff-only origin/main

# 3) compile canonical
"$PYTHON" scripts/compile_memory_hub.py --apply

# 4) distribute fresh canonical to local allowed participants
bash scripts/sync_cloud_to_workspace.sh

# 5) stage and guard
git add canonical sources
if git diff --cached --quiet; then
  echo "NO_CHANGES"
  exit 0
fi

git commit -m "chore(memory-hub): quick-share event"

# 6) push with retry
for attempt in 1 2 3; do
  if git push origin main; then
    echo "QUICK_SHARE_DONE"
    exit 0
  fi
  echo "push failed (attempt $attempt/3), rebasing..."
  git fetch origin main
  git rebase origin/main
  "$PYTHON" scripts/compile_memory_hub.py --apply
  bash scripts/sync_cloud_to_workspace.sh
  git add canonical sources
  if ! git diff --cached --quiet; then
    git commit -m "chore(memory-hub): recompile after rebase"
  fi
done

echo "PUSH_FAILED after 3 attempts" >&2
exit 1
