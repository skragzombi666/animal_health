#!/bin/sh
set -eu

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
STATE_FILE="$REPO_DIR/.previous_deploy_commit"
TARGET_ROOT="/config/custom_components"
TARGET_DIR="$TARGET_ROOT/animal_health"
TMP_ROOT="/tmp/animal_health_rollback"

if [ ! -f "$STATE_FILE" ]; then
  echo "Error: no previous deployment commit has been recorded." >&2
  exit 1
fi

ROLLBACK_COMMIT="$(cat "$STATE_FILE")"

if ! git -C "$REPO_DIR" cat-file -e "$ROLLBACK_COMMIT^{commit}" 2>/dev/null; then
  echo "Error: recorded commit $ROLLBACK_COMMIT is not available locally." >&2
  exit 1
fi

rm -rf "$TMP_ROOT"
mkdir -p "$TMP_ROOT" "$TARGET_ROOT"

git -C "$REPO_DIR" archive "$ROLLBACK_COMMIT" custom_components/animal_health | tar -x -C "$TMP_ROOT"

if [ ! -f "$TMP_ROOT/custom_components/animal_health/manifest.json" ]; then
  echo "Error: rollback commit does not contain the integration." >&2
  exit 1
fi

rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"
cp -a "$TMP_ROOT/custom_components/animal_health/." "$TARGET_DIR/"
rm -rf "$TMP_ROOT"

printf '%s\n' "$ROLLBACK_COMMIT" > "$REPO_DIR/.last_deployed_commit"

echo "Animal Health rolled back to commit ${ROLLBACK_COMMIT}."

if command -v ha >/dev/null 2>&1; then
  echo "Checking Home Assistant configuration..."
  ha core check
  echo "Restarting Home Assistant Core..."
  ha core restart
else
  echo "Home Assistant CLI not found; restart Home Assistant manually."
fi
