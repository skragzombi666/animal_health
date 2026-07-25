#!/bin/sh
set -eu

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
SOURCE_DIR="$REPO_DIR/custom_components/animal_health"
TARGET_ROOT="/config/custom_components"
TARGET_DIR="$TARGET_ROOT/animal_health"
BACKUP_ROOT="/config/animal_health_backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || printf 'unknown')"

if [ ! -f "$SOURCE_DIR/manifest.json" ]; then
  echo "Error: integration source not found at $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_ROOT" "$BACKUP_ROOT"

if [ -d "$TARGET_DIR" ]; then
  BACKUP_DIR="$BACKUP_ROOT/${TIMESTAMP}-${COMMIT}"
  echo "Backing up current installation to $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
  cp -a "$TARGET_DIR/." "$BACKUP_DIR/"
fi

TMP_DIR="${TARGET_DIR}.new"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
cp -a "$SOURCE_DIR/." "$TMP_DIR/"

rm -rf "$TARGET_DIR"
mv "$TMP_DIR" "$TARGET_DIR"

printf '%s\n' "$(git -C "$REPO_DIR" rev-parse HEAD)" > "$REPO_DIR/.last_deployed_commit"

echo "Animal Health deployed from commit $COMMIT."

if command -v ha >/dev/null 2>&1; then
  echo "Checking Home Assistant configuration..."
  ha core check
  echo "Restarting Home Assistant Core..."
  ha core restart
else
  echo "Home Assistant CLI not found; restart Home Assistant manually."
fi
