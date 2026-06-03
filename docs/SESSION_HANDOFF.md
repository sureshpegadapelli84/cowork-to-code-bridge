# Session handoff — cowork-to-code-bridge

_Updated: 2026-06-02. Repo clean, synced @ `c82f808`, CI green (macOS+Linux+WSL × 3 Python versions)._

## State
v0.5.0 on main. Platforms: macOS + Linux + WSL2. 5 stars, 5 forks, 5 contributors.
0 open PRs. 15 open issues. 31 tests pass, daemon LIVE.

## In flight — nothing (all PRs merged/closed)

| Item | Status |
|---|---|
| PR #31 WSL2 | ✅ Merged this session |
| PR #35 Reverse-direction inbox | ✅ Merged prior session |
| PR #32/#27 skill table | ✅ Closed (already satisfied on main) |

## High-priority open issues (the active to-do list)

| # | Issue | Notes |
|---|---|---|
| **#36** | Publish to PyPI | Publish workflow already written (`publish.yml`); needs PyPI trusted-publisher setup (owner-side, one-time) + version tag. High visibility/badge value. |
| **#37** | Homebrew tap | Discovery + trust signal for Mac users. One new repo (`homebrew-tap`) with a formula. |
| **#38** | Recipes doc | `docs/RECIPES.md` — copy-pasteable showcase tasks. Good-first-issue. |
| **#39** | "How it compares" section | Comparison vs MCP/SSH — drives discovery. |
| **#33** | Router: auto-pick model/effort | Top priority feature. `claude --model/--effort` flags exist; `CLAUDE_FLAGS` plumbing already works from PR #14. |
| **#17** | selfcheck command | Verify install end-to-end. Reduces bad bug reports. |
| **#15** | Demo GIF | Only the human can record. Shot list in `docs/demo-recording-script.md`. |

## Key facts for next session
- Security fixes are all intact post-WSL2 merge: CLAUDE_FLAGS env-override guard, `fullmatch`, inbox perm-hardening (verified).
- `to_cowork/` + `cowork_results/` dirs now created by daemon on startup (0700).
- 3 client copies must stay in sync (`cowork_to_code_bridge/client.py`, root `bridge_client.py`, `skill/.../bridge_client.py`) + `daemon/daemon.py` mirrors `cowork_to_code_bridge/daemon.py`.
- Promotion rule: never auto-post to forums; human posts, copy in `docs/reddit-post-ready.md`.

## First action next session
Either: tackle #36 (PyPI — mostly config, high bang/effort) or #33 (router — `claude --model/--effort` flags confirmed available). Both are buildable now.
