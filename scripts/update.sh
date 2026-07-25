#!/bin/sh
set -eu

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CURRENT_BRANCH="$(git -C "$REPO_DIR" branch --show-current)"

if [ -z "$CURRENT_BRANCH" ]; then
  echo "Error: repository is in detached HEAD state." >&2
  exit 1
fi

if [ -n "$(git -C "$REPO_DIR" status --porcelain)" ]; then
  echo "Error: repository contains uncommitted changes. Commit or discard them first." >&2
  exit 1
fi

PREVIOUS_COMMIT="$(git -C "$REPO_DIR" rev-parse HEAD)"
printf '%s\n' "$PREVIOUS_COMMIT" > "$REPO_DIR/.previous_deploy_commit"

echo "Updating branch $CURRENT_BRANCH..."
git -C "$REPO_DIR" pull --ff-only origin "$CURRENT_BRANCH"

sh "$REPO_DIR/scripts/deploy.sh"
