#!/usr/bin/env bash
# env_check.sh — show the environment values Cowork and Claude Code care about.
# Never prints secret VALUES (only whether they are set). Args: none.
# Usage from Cowork: call_remote("scripts/env_check.sh")
set -uo pipefail
echo "=== BRIDGE ENVIRONMENT ==="
printf '%-13s: %s\n' "PATH" "${PATH:-}"
root="${BRIDGE_ROOT:-$HOME/.cowork-to-code-bridge}"
if [ -d "$root" ]; then
  printf '%-13s: %s  (exists)\n' "BRIDGE_ROOT" "$root"
else
  printf '%-13s: %s  (MISSING)\n' "BRIDGE_ROOT" "$root"
fi
if [ -n "${BRIDGE_TOKEN:-}" ]; then
  printf '%-13s: set\n' "BRIDGE_TOKEN"
elif [ -f "$root/.env" ] && grep -q '^BRIDGE_TOKEN=' "$root/.env" 2>/dev/null; then
  printf '%-13s: set (in .env)\n' "BRIDGE_TOKEN"
else
  printf '%-13s: not set\n' "BRIDGE_TOKEN"
fi
printf '%-13s: %s\n' "CLAUDE_FLAGS" "${CLAUDE_FLAGS:-(not set)}"
printf '%-13s: %s\n' "SHELL" "${SHELL:-unknown}"
printf '%-13s: %s\n' "HOME" "${HOME:-unknown}"
if [ "$(uname)" = "Darwin" ]; then
  printf '%-13s: macOS %s\n' "OS" "$(sw_vers -productVersion 2>/dev/null || echo '?')"
elif [ -r /etc/os-release ]; then
  printf '%-13s: %s\n' "OS" "$(. /etc/os-release && echo "$PRETTY_NAME")"
else
  printf '%-13s: %s\n' "OS" "$(uname -s) $(uname -r)"
fi
claude_path="$(command -v claude 2>/dev/null || true)"
printf '%-13s: %s\n' "claude CLI" "${claude_path:-not found on PATH}"
exit 0
