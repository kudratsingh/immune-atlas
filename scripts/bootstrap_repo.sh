#!/usr/bin/env bash
# One-time repository bootstrap: initial commit, GitHub repo, merge settings,
# branch protection. Requires git and an authenticated gh CLI.
#
# Usage: scripts/bootstrap_repo.sh [github-repo-name]   (default: immune-atlas)

set -euo pipefail

REPO_NAME="${1:-immune-atlas}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v gh >/dev/null || { echo "gh CLI is required: https://cli.github.com"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "run 'gh auth login' first"; exit 1; }
git config user.name >/dev/null || { echo "set git config user.name / user.email first"; exit 1; }

if [ ! -d .git ]; then
  git init -b main
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  git add -A
  git commit -q -m "chore: project scaffold, specification, and build plan" \
    -m "Assignment transcription and acceptance checklist, architecture and ADRs, workstream plan, dashboard UX brief, bundle contract, Makefile, CI, and devcontainer."
  echo "initial commit created"
fi

OWNER="$(gh api user -q .login)"
if ! gh repo view "$OWNER/$REPO_NAME" >/dev/null 2>&1; then
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push \
    --description "Immune cell population analysis pipeline and dashboard for a clinical trial dataset"
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/$REPO_NAME.git"
  git push -u origin main
fi

# Merge strategy: squash only, auto-merge allowed, branches deleted after merge.
gh repo edit "$OWNER/$REPO_NAME" \
  --enable-auto-merge \
  --delete-branch-on-merge \
  --enable-squash-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge=false \
  --allow-update-branch

# Branch protection: PR required (no approvals — solo repo), CI required and
# current, linear history, applies to admins, no force pushes or deletions.
gh api -X PUT "repos/$OWNER/$REPO_NAME/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["python", "dashboard", "pipeline"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false
}
JSON

echo
echo "Repository: https://github.com/$OWNER/$REPO_NAME"
echo "Next: scripts/new_worktree.sh feat/foundation   (docs/PLAN.md WS-1)"
