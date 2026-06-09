# Recipes — things to ask Cowork once the bridge is set up

Each recipe shows the plain-English prompt you give Cowork, the Cowork code
that runs it, and what actually happens on your machine. All of them are
copy-pasteable as-is (swap the paths for your own).

---

## 1. Build and run a FastAPI app, then hit /health

**You ask:**
> "Build a FastAPI app with a /health route in ~/projects/myapi, install deps, run it on port 8000, and confirm /health returns 200."

**Cowork runs:**
```python
r = call_remote(
    "scripts/run_claude.sh",
    args=[
        "Create a FastAPI app in this directory with a /health route that returns "
        '{"status": "ok"}. Install dependencies with pip, start the server on '
        "port 8000 in the background, then curl http://localhost:8000/health and "
        "print the response.",
        "/Users/you/projects/myapi",
    ],
    timeout=300,
    idempotency_key="build-fastapi-health-1",
)
print(r["stdout"])
```

**What happens:** Claude Code scaffolds `main.py`, runs `pip install fastapi uvicorn`,
starts the server with `uvicorn main:app --port 8000 &`, curls `/health`, and
reports back the JSON response. You get a working API in under a minute.

---

## 2. Find and fix the failing test, then commit

**You ask:**
> "Run the test suite in ~/projects/myapp, find whatever's failing, fix it, and commit with a clear message."

**Cowork runs:**
```python
r = call_remote_streaming(
    "scripts/run_claude.sh",
    args=[
        "Run pytest. If any tests fail, read the relevant source files, fix the "
        "root cause (don't just delete the tests), run pytest again to confirm "
        "they pass, then git commit with a message that describes what was broken "
        "and how you fixed it.",
        "/Users/you/projects/myapp",
    ],
    timeout=600,
    idempotency_key="fix-tests-2026-06-09-a",
    on_progress=lambda chunk: print(chunk, end="", flush=True),
)
print("exit:", r["exit_code"])
```

**What happens:** You watch the test output stream in real time. Claude Code reads
the failure, traces it to the source, makes a targeted fix, reruns the suite,
and commits. No copy-pasting stack traces back and forth.

---

## 3. What's eating my disk? Clean up after I confirm

**You ask:**
> "What's using the most disk space on my Mac? Show me the top 5 directories, then wait for me to say which one to clean up."

**Cowork runs:**
```python
# Step 1 — audit (fast, no side effects)
r = call_remote("scripts/mac_disk.sh")
print(r["stdout"])

# Step 2 — after you review and confirm the target:
r2 = call_remote(
    "scripts/run_claude.sh",
    args=[
        "Run `du -sh ~/Library/Caches/* | sort -rh | head -20` and show the "
        "output. Then delete only the top offender inside ~/Library/Caches — "
        "nothing outside that directory. Show the before/after disk usage.",
        "/Users/you",
    ],
    timeout=120,
    idempotency_key="disk-cleanup-caches-2026-06-09",
    permission_mode="bypassPermissions",
)
print(r2["stdout"])
```

**What happens:** First call is read-only — you see exactly what's big before
anything is touched. Second call runs only after you've reviewed and decided.
`permission_mode="bypassPermissions"` lets Claude Code delete files; for the
audit step it isn't needed.

---

## 4. Bump the version, tag a release, and push

**You ask:**
> "Bump the version in pyproject.toml to 0.6.0, update the CHANGELOG, commit, tag v0.6.0, and push."

**Cowork runs:**
```python
r = call_remote(
    "scripts/run_claude.sh",
    args=[
        "Do a release: (1) update the version in pyproject.toml to 0.6.0, "
        "(2) add a CHANGELOG entry under ## [0.6.0] with today's date and a "
        "summary of recent commits, (3) git commit -m 'chore: release v0.6.0', "
        "(4) git tag v0.6.0, (5) git push origin main --tags. "
        "Show each step's output.",
        "/Users/you/projects/mypackage",
    ],
    timeout=120,
    idempotency_key="release-v0.6.0",
    permission_mode="bypassPermissions",
)
print(r["stdout"])
```

**What happens:** Claude Code edits the files, writes the changelog, commits,
tags, and pushes — your CI publish workflow fires automatically. The
`idempotency_key` means if the connection drops halfway through and you retry,
the daemon returns the cached result instead of running the release twice.

---

## 5. Spin up the dev server and screenshot the homepage

**You ask:**
> "Start the dev server for my Next.js app and screenshot the homepage."

**Cowork runs:**
```python
r = call_remote(
    "scripts/run_claude.sh",
    args=[
        "Run `npm run dev` in the background (port 3000). Wait up to 15s for "
        "the server to be ready (poll http://localhost:3000). Once it responds, "
        "use `screencapture -x /tmp/homepage.png` to screenshot the screen, "
        "then print 'SCREENSHOT_SAVED:/tmp/homepage.png' so I know it's done.",
        "/Users/you/projects/myapp",
    ],
    timeout=60,
    idempotency_key="screenshot-homepage-1",
    permission_mode="bypassPermissions",
)
print(r["stdout"])
```

**What happens:** Claude Code starts the dev server, polls until it's live, and
takes a native macOS screenshot. You can then ask Cowork to open and review the
image, or diff it against a previous run.

---

## 6. Set up a brand-new project from scratch

**You ask:**
> "Create a new Python CLI project called 'tidyup' in ~/projects — argparse, a basic test suite, a Makefile with test/lint/build targets, and push it to a new GitHub repo."

**Cowork runs:**
```python
r = call_remote_streaming(
    "scripts/run_claude.sh",
    args=[
        "Bootstrap a Python CLI project called 'tidyup': (1) mkdir ~/projects/tidyup "
        "and cd into it, (2) create src/tidyup/__main__.py with argparse + a --help, "
        "(3) create tests/test_cli.py with at least 2 tests, (4) create a Makefile "
        "with test / lint / build targets, (5) git init + initial commit, "
        "(6) gh repo create tidyup --private --source=. --push. "
        "Print each step as you go.",
        "/Users/you/projects",
    ],
    timeout=300,
    idempotency_key="bootstrap-tidyup-1",
    on_progress=lambda chunk: print(chunk, end="", flush=True),
)
print("exit:", r["exit_code"])
```

**What happens:** A complete, working project appears in `~/projects/tidyup` and
on GitHub — scaffolded, tested, committed, and pushed. What would take 20 minutes
of copy-pasting boilerplate takes ~60 seconds.

---

## 7. Review a PR diff and leave inline comments

**You ask:**
> "Review the open PR #42 in my repo — read the diff, check for bugs or style issues, and post inline review comments via the GitHub CLI."

**Cowork runs:**
```python
r = call_remote(
    "scripts/run_claude.sh",
    args=[
        "Use `gh pr diff 42` to get the diff for PR #42 in this repo. Review it "
        "for bugs, unhandled edge cases, and style issues. For each issue found, "
        "post an inline comment using `gh pr review 42 --comment`. Summarise what "
        "you found at the end.",
        "/Users/you/projects/myrepo",
    ],
    timeout=180,
    idempotency_key="review-pr-42",
    permission_mode="bypassPermissions",
)
print(r["stdout"])
```

**What happens:** Claude Code fetches the diff, analyses it, and posts real GitHub
review comments — visible to your teammates in the PR. You get a code review
without opening the browser.

---

## 8. Migrate a database schema and verify it

**You ask:**
> "Run the pending Alembic migrations on my local dev DB, then run the test suite to confirm nothing broke."

**Cowork runs:**
```python
r = call_remote_streaming(
    "scripts/run_claude.sh",
    args=[
        "Run `alembic upgrade head` and show the output. If it succeeds, run "
        "`pytest tests/db/` and show the results. If either step fails, show the "
        "full error and stop — do not attempt to auto-fix migrations.",
        "/Users/you/projects/myapp",
    ],
    timeout=300,
    idempotency_key="migrate-and-test-2026-06-09",
    on_progress=lambda chunk: print(chunk, end="", flush=True),
    permission_mode="bypassPermissions",
)
print("exit:", r["exit_code"])
```

**What happens:** Migration runs, then tests confirm the schema is consistent.
The `idempotency_key` means a retry after a dropped connection won't run the
migration twice.

---

## 9. Kill a runaway process by name

**You ask:**
> "My dev server is stuck — kill the 'node' process."

**Cowork runs:**
```python
r = call_remote(
    "scripts/process_kill.sh",
    args=["node"],
)
print(r["stdout"])
```

**What happens:** `pgrep -x node` finds the PID, sends SIGTERM (not SIGKILL —
lets it clean up open files and sockets), and confirms the process is gone.
If multiple `node` processes are running, it refuses and tells you to pass
`--all` or use a specific PID — so you never accidentally kill the wrong thing.

---

## 10. Daily standup: what did I actually ship yesterday?

**You ask:**
> "Summarise what I committed across all my active repos yesterday — one bullet per repo, skip anything with no commits."

**Cowork runs:**
```python
import datetime
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

r = call_remote(
    "scripts/run_claude.sh",
    args=[
        f"For each directory in ~/projects that is a git repo with commits since "
        f"{yesterday}, run `git log --oneline --since='{yesterday}' --author=$(git config user.email)` "
        f"and summarise the work in one bullet. Skip repos with no commits. "
        f"Format the output as a standup update I can paste into Slack.",
        "/Users/you/projects",
    ],
    timeout=60,
    idempotency_key=f"standup-{yesterday}",
    permission_mode="plan",   # read-only — no need for write access
)
print(r["stdout"])
```

**What happens:** Claude Code walks your projects directory, queries git history
for each repo, and writes a standup summary formatted for Slack. `permission_mode="plan"`
locks it to read-only — it can't touch any files, only read and report.

---

## Tips for writing your own recipes

- **Always set `idempotency_key`** for tasks that write, commit, or push — safe to retry after a dropped connection.
- **Use `permission_mode="plan"`** for read-only tasks (audits, summaries, diffs). Use `"bypassPermissions"` only when the task needs to write files, run installs, or push.
- **Stream long tasks** with `call_remote_streaming` + `on_progress` so you see what's happening instead of waiting blind.
- **Set `max_budget_usd`** on expensive tasks (`max_budget_usd=2.00`) so a runaway agent can't drain your API credits.
- **Be explicit about what not to do** — "do not delete anything outside ~/Library/Caches" is more reliable than hoping the agent infers it.
