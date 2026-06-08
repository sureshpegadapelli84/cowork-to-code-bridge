#!/usr/bin/env bash
# list_scripts.sh — list every script the bridge can run, with its one-line description.
# Lets Cowork discover what's available instead of guessing. Args: none.
# Usage from Cowork: call_remote("scripts/list_scripts.sh")
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== AVAILABLE BRIDGE SCRIPTS ==="
echo "(call any of these with call_remote(\"scripts/<name>\"))"
echo
shopt -s nullglob
found=0
for f in "$DIR"/*.sh; do
  name="$(basename "$f")"
  [ "$name" = "list_scripts.sh" ] && continue
  # Pull the first comment line after the shebang as the description.
  desc="$(awk 'NR>1 && /^#/ {sub(/^# */,""); print; exit}' "$f")"
  printf '  %-22s %s\n' "$name" "${desc:-(no description)}"
  found=$((found + 1))
done
[ "$found" -eq 0 ] && echo "  (no scripts found in $DIR)"
exit 0
