#!/usr/bin/env bash
# disk_hogs.sh — biggest files and folders in a directory (default: home).
# Args: [path] [count]   e.g. call_remote("scripts/disk_hogs.sh", args=["~/Downloads","15"])
set -uo pipefail
TARGET="${1:-$HOME}"
COUNT="${2:-15}"
# expand a leading ~ since args arrive as literal strings
case "$TARGET" in "~"|"~/"*) TARGET="$HOME${TARGET#\~}";; esac
if ! [[ "$COUNT" =~ ^[0-9]+$ ]]; then
  echo "count must be a number, got: $COUNT" >&2; exit 1
fi
if [ ! -d "$TARGET" ]; then
  echo "not a directory: $TARGET" >&2; exit 1
fi
echo "=== TOP $COUNT LARGEST ITEMS IN $TARGET ==="
# du over immediate children; sort by size desc; human-readable.
du -sh "$TARGET"/* "$TARGET"/.[!.]* 2>/dev/null \
  | sort -rh \
  | head -n "$COUNT"
exit 0
