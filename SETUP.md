# SETUP.md

> **Setup is now a single Mac command — there's nothing to do in Cowork.**

As of v0.4.0 the bridge installs a **global Claude skill**, so it loads into
every Cowork session automatically. There is no longer any "paste a URL into
Cowork" / fetch / popup step.

## Install (the only step)

On your Mac, in Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/abhinaykrupa/cowork-to-code-bridge/main/install.sh | bash
```

That installs the daemon (auto-starts, reboot-safe) **and** the global skill at
`~/.claude/skills/cowork-to-code-bridge/`. Done.

## Then just talk to Cowork

In any Cowork chat: *"build me an app on my Mac"*, *"run my tests"*,
*"check my Mac's health"*. The skill triggers, connects, and routes the work to
Claude Code on your Mac.

## How it works (for maintainers)

- The skill (`SKILL.md` + `bridge_client.py` + `bridge_env.json`) lives in
  `~/.claude/skills/cowork-to-code-bridge/` and auto-loads in every session.
- `bridge_client.py` is pure stdlib; `bridge_env.json` carries `BRIDGE_ROOT`, so
  the sandbox connects with **no env var, no fetch, no paste, no popups**.
- The canonical skill source is in this repo at
  [`skill/cowork-to-code-bridge/`](./skill/cowork-to-code-bridge/); the installer
  writes it to `~/.claude/skills/`.
- macOS (launchd) and Linux (systemd) supported; Windows not yet.
