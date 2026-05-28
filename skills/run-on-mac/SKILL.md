---
name: run-on-mac
description: Use this skill when the user asks to do something that has to happen on their Mac, outside the Cowork sandbox — running shell commands, git push/pull, docker, brew, accessing their SSH keys, editing files outside the bind-mount, or anything that needs their local environment. Routes the request through the cowork-to-code-bridge daemon.
---

# run-on-mac skill

You can execute whitelisted scripts on the user's Mac via the bridge daemon. Use this any time the user asks for an action that needs their local machine.

## When to use this skill

Use `call_remote()` when the user wants:

- Shell commands that need their local environment (`brew install ...`, `gh ...`, `docker ...`)
- Git operations that need their SSH keys (`git push`, `git pull` from private repos)
- Reading/writing files outside the Cowork bind-mount
- Running tools installed only on the Mac (xcode, native apps, Spotlight)
- Anything that would fail with "command not found" or "permission denied" in the Cowork sandbox

## When NOT to use this skill

Don't use the bridge for:

- File operations inside the bind-mounted project (use normal file tools — faster, no daemon roundtrip)
- Read-only API calls that work fine from the sandbox (most HTTP, most MCP servers)
- Anything the user is doing in claude.ai web chat (no bridge there)

## How to call it

```python
from cowork_to_code_bridge import call_remote

result = call_remote(
    script="scripts/git_status.sh",   # must be whitelisted on Mac
    args=["AAQuant"],                  # optional positional args
    timeout=60,                        # max seconds the script can run
)

print(result["exit_code"])  # 0 = success
print(result["stdout"])
print(result["stderr"])
```

## The whitelist constraint

The daemon only runs scripts under `~/.cowork-to-code-bridge/scripts/` on the Mac. You **cannot** call `bash -c "..."` or arbitrary commands. This is intentional — it's the security model.

If the user wants to run something not yet whitelisted:

1. Ask them what they want to run.
2. Help them write a small shell script for it.
3. Tell them to save it as `~/.cowork-to-code-bridge/scripts/<name>.sh` on their Mac and `chmod +x` it.
4. Once they confirm it's saved, call it via `call_remote("scripts/<name>.sh", ...)`.

If the bridge isn't installed yet (`daemon_alive()` returns `False` and there's no `~/.cowork-to-code-bridge/` on the Mac), trigger the `cowork-to-code-bridge-setup` skill. The user installs via the Claude Code plugin marketplace: `/plugin marketplace add abhinaykrupa/cowork-bridge-marketplace` then `/plugin install cowork-to-code-bridge@cowork-bridge-marketplace`, followed by the one-line `install.sh` curl on their Mac. The setup skill drives that flow end to end.

Pre-installed scripts (always available after `install.sh`):

- `scripts/ping.sh` — health check, echoes OK + pwd + timestamp
- `scripts/hello.sh` — example, echoes args

## Error handling

```python
result = call_remote("scripts/foo.sh", timeout=30)

if result["exit_code"] == 0:
    # success
    pass
elif result["exit_code"] == -1:
    # daemon refused — bad script path, token mismatch, or script doesn't exist
    print(f"Daemon refused: {result.get('error')}")
elif result["exit_code"] == -2:
    # script ran but timed out
    print(f"Script exceeded {result.get('error')}")
    print(f"Partial output: {result.get('stdout')}")
elif result["exit_code"] == -3:
    # internal daemon error
    print(f"Daemon error: {result.get('error')}")
else:
    # script's own non-zero exit
    print(f"Script failed: {result['stderr']}")
```

`call_remote()` raises `TimeoutError` if the daemon doesn't respond at all (vs. the script running and timing out). On `TimeoutError`, suggest the user check the daemon: `launchctl list | grep cowork-to-code-bridge`.

## Configuration

The client auto-finds the bridge directory. If it can't:

```python
result = call_remote(
    "scripts/ping.sh",
    bridge_root="/path/to/.cowork-to-code-bridge",  # explicit override
)
```

The `BRIDGE_ROOT` and `BRIDGE_TOKEN` env vars also work for global override.

## What to surface to the user

When you call the bridge, tell the user briefly what you're doing:

> Running `git status` on your Mac via the bridge…

Don't dump the full `result` dict on them unless they ask. Show the relevant output (usually `stdout`) and any failure context.
