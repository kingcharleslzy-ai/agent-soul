#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v python3 &>/dev/null; then PYTHON=python3; else PYTHON=python; fi

git fetch origin main
git merge --ff-only origin/main

result="$("$PYTHON" scripts/ingest_participant_memory.py)"

if [[ "$result" != "INGEST_DONE" ]]; then
  echo "INGEST_NOOP"
  exit 0
fi

git add sources

if git diff --cached --quiet; then
  echo "INGEST_NOOP"
  exit 0
fi

git commit -m "chore(memory-hub): ingest participant events"

for attempt in 1 2 3; do
  if git push origin main; then
    echo "INGEST_DONE"
    exit 0
  fi
  echo "push failed (attempt $attempt/3), rebasing..."
  git fetch origin main
  git rebase origin/main
done

echo "PUSH_FAILED after 3 attempts" >&2
exit 1
