---
name: cowork-to-code-bridge-setup
description: Walk the user through installing the cowork-to-code-bridge so Cowork can run commands on their Mac. Triggers on natural-language requests like "set up the cowork-to-code bridge", "set up cowork bridge", "install cowork bridge", "connect cowork to my Mac", "hook Cowork up to my Mac", or any similar phrasing about bridging Cowork to the user's local machine.
---

# Setup skill — cowork-to-code-bridge

You are walking the user through a **one-paste-and-go install**. The user said something like "set up the cowork-to-code bridge" in natural language. You figure out the right commands and drive the rest.

## Your job in one sentence

Get the Mac daemon installed and verified working, with the user running **exactly one terminal command** of their own.

## Step 0 — ensure the plugin marketplace is added

The bridge ships as a Claude Code plugin distributed through the `cowork-bridge-marketplace`. If this is the first time the user has interacted with the bridge plugin in Claude Code, the marketplace probably isn't added yet.

Check whether the marketplace is already registered. If you can't tell, just attempt to add it — it's idempotent. Run:

```
/plugin marketplace add abhinaykrupa/cowork-bridge-marketplace
```

If the user reports it's already added, skip ahead. If you see an "already added" message, that's fine — move on.

## Step 0.5 — ensure the plugin is installed in this session

If the bridge plugin isn't installed yet in this Claude Code session, install it:

```
/plugin install cowork-to-code-bridge@cowork-bridge-marketplace
```

Once installed, this skill is "self-installed" — subsequent sessions will already have it and Steps 0 and 0.5 become no-ops. If the user confirms the plugin is already installed, skip straight to Step 1.

## Step 1 — probe for existing install

Before asking the user to do anything on their Mac, check if the daemon is already set up. Use the bridge client to call the ping path:

```python
from cowork_to_code_bridge import call_remote, daemon_alive
if daemon_alive(ping_timeout=5):
    print("Bridge is already configured and live.")
```

Three possible outcomes:

1. **`daemon_alive()` returns `True`** → daemon is up and responding. **Skip to Step 6 (declare ready).** Don't put the user through setup they don't need.
2. **Daemon directory + plist exist on Mac, but `daemon_alive()` returns `False`** → the daemon is installed but not currently loaded. **Jump to Step 2.5 (reload existing daemon).**
3. **No daemon directory at all** → fresh install needed. Continue to Step 2.

If you can't tell which state you're in, ask the user to check on their Mac:

```bash
ls ~/.cowork-to-code-bridge/.env 2>/dev/null && echo "INSTALLED" || echo "NOT INSTALLED"
launchctl list | grep cowork-to-code-bridge || echo "NOT LOADED"
```

If `INSTALLED` + `NOT LOADED` → Step 2.5. If `NOT INSTALLED` → Step 2.

## Step 2 — show the user the install command (fresh install)

Tell the user this, verbatim, in a code block:

> I need you to run **one command** in your Mac terminal (not in Cowork — open Terminal.app or iTerm on your Mac).
>
> Copy this and paste it into your Mac terminal:
>
> ```bash
> curl -fsSL https://raw.githubusercontent.com/abhinaykrupa/cowork-to-code-bridge/main/install.sh | bash
> ```
>
> It takes about 30 seconds. It will:
> - Install the bridge Python package
> - Create `~/.cowork-to-code-bridge/` on your Mac
> - Generate a security token
> - Start a background daemon that auto-restarts on login
>
> Tell me when it finishes, or paste any error you see.

Then go to Step 3.

## Step 2.5 — reload existing daemon (skip full reinstall)

If the daemon is already installed but `launchctl` shows it's not loaded, there's no need for a full reinstall. Tell the user:

> Your bridge is already installed but the background daemon isn't running. Just reload it — run this in your Mac terminal:
>
> ```bash
> launchctl load ~/Library/LaunchAgents/dev.cowork-to-code-bridge.daemon.plist
> ```
>
> Then tell me when it's done.

After they confirm, re-probe with `daemon_alive()`. If it now returns `True`, jump to Step 6. If it still returns `False`, ask for `tail -20 ~/.cowork-to-code-bridge/daemon.err` and move into Step 4 diagnostics.

## Step 3 — wait for user confirmation

Accept variants: "done", "finished", "ok", "ran it", "installed", "complete", or any short affirmative. Also handle:

- **User pastes the install.sh output** → confirm it looks successful (look for the "DONE. Bridge is installed and running." line) and proceed.
- **User pastes an error** → diagnose using Step 4.

## Step 4 — error recovery

Common failure modes and what to tell the user:

| Symptom in user's paste | Diagnosis | Tell the user |
|---|---|---|
| `command not found: python3` | No Python | "Install Python first: `brew install python@3.12`, then re-run the curl command." |
| `Python ... is too old` | Python < 3.10 | "Your Python is too old. Install 3.10+: `brew install python@3.12`, then re-run." |
| `pip: command not found` | No pip | "Run `python3 -m ensurepip --upgrade`, then re-run the curl command." |
| `Permission denied` writing `~/Library/LaunchAgents` | Filesystem perms | "Check that you own `~/Library/LaunchAgents` — `ls -ld ~/Library/LaunchAgents`. If it's missing, `mkdir -p ~/Library/LaunchAgents` and re-run." |
| `launchctl: ... already loaded` | Re-install | This is fine — installer handles it. Tell them to re-run; if still stuck, run `launchctl unload ~/Library/LaunchAgents/dev.cowork-to-code-bridge.daemon.plist` manually then re-run installer. |
| Daemon previously installed, `launchctl list \| grep cowork` returns nothing | Daemon unloaded (sleep, crash, manual unload) | **Don't reinstall.** Tell them: `launchctl load ~/Library/LaunchAgents/dev.cowork-to-code-bridge.daemon.plist`, then re-probe. |
| `daemon_alive()` returns False from inside Cowork, but `launchctl list` shows the daemon running on Mac | **BRIDGE_ROOT mismatch** between Cowork sandbox and Mac | Ask the user to run `cat ~/.cowork-to-code-bridge/.env` in their Mac terminal and paste the `BRIDGE_ROOT=...` and `BRIDGE_TOKEN=...` lines. Then in Cowork, set the env vars to match: `os.environ["BRIDGE_ROOT"] = "<path from .env>"` (and same for `BRIDGE_TOKEN` if needed). Re-probe with `daemon_alive()`. |
| `daemon failed to register` | launchd refused the plist | Ask them to paste the tail of `~/.cowork-to-code-bridge/daemon.err`. |
| `curl: command not found` | No curl (rare on Mac) | Provide wget alternative: `wget -qO- https://... \| bash` or manual download. |
| Network timeout / DNS error | Connectivity | "Check your internet connection, then re-run." |

If the symptom doesn't match any of these, ask the user for:
1. The last 20 lines of installer output
2. Output of `which python3 && python3 --version`
3. Output of `ls ~/.cowork-to-code-bridge/` if the directory exists
4. Output of `cat ~/.cowork-to-code-bridge/.env` (so you can verify `BRIDGE_ROOT`)

## Step 5 — verify the bridge actually works

Do not declare success based on the user's word. Probe the bridge yourself:

```python
from cowork_to_code_bridge import daemon_alive
if daemon_alive(ping_timeout=10):
    # success
else:
    # the user thinks it worked but the daemon isn't responding
```

If the probe fails after the user reports success, check in order:

1. **Daemon not running:** "Check `launchctl list | grep cowork-to-code-bridge` on your Mac — it should show one line. If it doesn't, run `launchctl load ~/Library/LaunchAgents/dev.cowork-to-code-bridge.daemon.plist`."
2. **BRIDGE_ROOT mismatch:** ask the user to paste `cat ~/.cowork-to-code-bridge/.env`, then set `BRIDGE_ROOT` in your Cowork session to match the value on the Mac side. Re-probe.
3. **Daemon erroring:** ask for `tail -20 ~/.cowork-to-code-bridge/daemon.err`.

## Step 6 — declare ready

Once `daemon_alive()` returns `True`, tell the user:

> Bridge is live. You can now ask me to run things on your Mac. Try:
>
> - "run `ls` on my Mac"
> - "git status on my AAQuant repo"
> - "run `pytest` on my project"
>
> I'll route those through the bridge automatically. The `run-on-mac` skill handles it from here.
>
> If you ever want to remove the bridge, just run `cowork-to-code-bridge-uninstall` on your Mac (full path if your PATH doesn't pick it up: `~/Library/Python/3.10/bin/cowork-to-code-bridge-uninstall`).

## What not to do

- **Don't** try to install anything on the Mac yourself via shell commands. Your Cowork sandbox can't reach the user's Mac except through the bridge.
- **Don't** ask the user to read the README. The skill *is* the README from their perspective.
- **Don't** declare success based on the user saying "done". Always verify with `daemon_alive()`.
- **Don't** keep retrying silently. If something fails after 2 attempts, surface it to the user with a concrete diagnostic ask.
- **Don't** push the user through a full reinstall when the daemon is just unloaded — use Step 2.5.

## State preservation

After successful setup, future Cowork sessions in the same project will find the daemon already alive on probe (Step 1) and jump straight to Step 6. No re-onboarding. The marketplace + plugin install (Steps 0 and 0.5) only need to happen once per Claude Code install.
