#!/usr/bin/env bash
# Create a git worktree for a feature branch, off an up-to-date main.
#
# Usage: scripts/new_worktree.sh feat/analysis-response
# Result: ../immune-atlas-wt/analysis-response on branch feat/analysis-response

set -euo pipefail

BRANCH="${1:?usage: $0 <branch-name>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WT_ROOT="$(dirname "$ROOT")/$(basename "$ROOT")-wt"
DIR="$WT_ROOT/${BRANCH#*/}"

cd "$ROOT"
git fetch -q origin main
mkdir -p "$WT_ROOT"

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git worktree add "$DIR" "$BRANCH"
else
  git worktree add -b "$BRANCH" "$DIR" origin/main
fi

echo "worktree: $DIR"
echo "branch:   $BRANCH"
echo "when merged: git worktree remove \"$DIR\" && git branch -d $BRANCH"
