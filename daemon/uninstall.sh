#!/usr/bin/env bash
# uninstall.sh — one-command Mac-side teardown for cowork-to-code-bridge.
#
# Prefers the installed console script (cowork-to-code-bridge-uninstall) when
# available, since it knows which Python interpreter installed the package.
# Falls back to direct shell teardown if the package isn't on PATH.
#
# Usage:
#   bash daemon/uninstall.sh                # interactive prompts
#   bash daemon/uninstall.sh --yes          # no prompts
#   bash daemon/uninstall.sh --keep-data    # leave ~/.cowork-to-code-bridge/
#   bash daemon/uninstall.sh --keep-package # leave the pip package

set -euo pipefail

# ─── Prefer the installed console script ─────────────────────────────────────
if command -v cowork-to-code-bridge-uninstall >/dev/null 2>&1; then
  exec cowork-to-code-bridge-uninstall "$@"
fi

# Try locating it via the same python that may have installed it.
# Probe newest first; only `import` gates pass so the picked interpreter is
# guaranteed to be the one that owns the package.
for PY in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$PY" >/dev/null 2>&1 && \
     "$PY" -c "import cowork_to_code_bridge.uninstall" 2>/dev/null; then
    exec "$PY" -m cowork_to_code_bridge.uninstall "$@"
  fi
done

# Also try the per-user scripts dir directly, in case PATH is missing it.
for PYV in 3.13 3.12 3.11 3.10; do
  cand="$HOME/Library/Python/$PYV/bin/cowork-to-code-bridge-uninstall"
  if [[ -x "$cand" ]]; then
    exec "$cand" "$@"
  fi
done

# ─── Fallback: pure-shell teardown ───────────────────────────────────────────
echo "  ! cowork-to-code-bridge package not found on this system — running shell-only teardown."
echo "    (Daemon + plist + bridge data will be removed; pip uninstall is skipped.)"
echo

BRIDGE_ROOT="${BRIDGE_ROOT:-$HOME/.cowork-to-code-bridge}"
PLIST="$HOME/Library/LaunchAgents/dev.cowork-to-code-bridge.daemon.plist"

ASSUME_YES=0
KEEP_DATA=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y) ASSUME_YES=1 ;;
    --keep-data) KEEP_DATA=1 ;;
  esac
done

confirm() {
  if [[ "$ASSUME_YES" -eq 1 ]]; then return 0; fi
  read -r -p "$1 [y/N] " response
  [[ "$response" =~ ^[Yy]$ ]]
}

if [[ "$(uname -s)" == "Linux" ]]; then
  # Linux: tear down the systemd --user service.
  if command -v systemctl >/dev/null 2>&1; then
    echo "→ stopping + disabling systemd --user service"
    systemctl --user disable --now cowork-to-code-bridge.service 2>/dev/null || true
  fi
  UNIT="$HOME/.config/systemd/user/cowork-to-code-bridge.service"
  if [[ -f "$UNIT" ]]; then
    echo "→ removing $UNIT"
    rm -f "$UNIT"
    systemctl --user daemon-reload 2>/dev/null || true
  fi
else
  # macOS: tear down the launchd agent.
  if launchctl list 2>/dev/null | grep -q "dev.cowork-to-code-bridge.daemon"; then
    echo "→ unloading launchd agent"
    launchctl bootout "gui/$(id -u)/dev.cowork-to-code-bridge.daemon" 2>/dev/null \
      || launchctl unload "$PLIST" 2>/dev/null || true
  fi
  if [[ -f "$PLIST" ]]; then
    echo "→ removing $PLIST"
    rm -f "$PLIST"
  fi
fi

if [[ "$KEEP_DATA" -eq 1 ]]; then
  echo "→ keeping $BRIDGE_ROOT (--keep-data)"
elif [[ -d "$BRIDGE_ROOT" ]]; then
  if confirm "Delete $BRIDGE_ROOT (contains your bridge token and processed-command history)?"; then
    rm -rf "$BRIDGE_ROOT"
    echo "✓ removed $BRIDGE_ROOT"
  else
    echo "  kept $BRIDGE_ROOT"
  fi
fi

# Remove the global Cowork skill so it stops loading into sessions.
SKILL_DIR="$HOME/.claude/skills/cowork-to-code-bridge"
if [[ -d "$SKILL_DIR" ]]; then
  rm -rf "$SKILL_DIR"
  echo "✓ removed global skill $SKILL_DIR"
fi

echo "✓ daemon + plist + skill removed."
echo "  Package was not on PATH so nothing to pip-uninstall. If you did install it via pip,"
echo "  remove it with: python3 -m pip uninstall cowork-to-code-bridge"
