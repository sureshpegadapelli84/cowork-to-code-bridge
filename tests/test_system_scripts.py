from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"
IS_MACOS = platform.system() == "Darwin"

# mac_ram.sh prints "Total RAM:" on macOS (sysctl branch) but uses `free`/`/proc`
# on Linux, where the output is the `free -h` table ("Mem:"). The expected
# fragment must match whichever OS the test actually runs on.
RAM_FRAGMENT = "Total RAM:" if IS_MACOS else "Mem:"


def _extract_script(script_name: str, marker: str) -> str:
    lines = INSTALL_SH.read_text().splitlines()
    start = None
    body: list[str] = []
    prefix = f'cat > "$BRIDGE_ROOT/scripts/{script_name}" <<\'{marker}\''

    for index, line in enumerate(lines):
        if line == prefix:
            start = index + 1
            break

    if start is None:
        raise AssertionError(f"Could not find {script_name} in install.sh")

    for line in lines[start:]:
        if line == marker:
            return "\n".join(body) + "\n"
        body.append(line)

    raise AssertionError(f"Could not find closing marker {marker} for {script_name}")


@pytest.fixture()
def generated_scripts(tmp_path: Path) -> Path:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    for script_name, marker in [
        ("mac_health.sh", "MH"),
        ("mac_ram.sh", "MR"),
        ("mac_disk.sh", "MD"),
        ("mac_top.sh", "MT"),
        ("mac_network.sh", "MN"),
    ]:
        script_path = scripts_dir / script_name
        script_path.write_text(_extract_script(script_name, marker))
        script_path.chmod(0o755)

    return scripts_dir


@pytest.mark.parametrize(
    ("script_name", "args", "expected_fragments"),
    [
        (
            "mac_health.sh",
            [],
            [
                "=== HOST ===",
                "=== UPTIME / LOAD ===",
                "=== CPU ===",
                "=== MEMORY ===",
                "=== DISK ===",
                "=== TOP 5 PROCS BY CPU ===",
            ],
        ),
        ("mac_ram.sh", [], [RAM_FRAGMENT]),
        ("mac_disk.sh", [], ["=== DISK USAGE ===", "=== ALL MOUNTED VOLUMES ==="]),
        ("mac_top.sh", ["5"], ["=== by CPU ===", "=== by MEM ==="]),
        (
            "mac_network.sh",
            [],
            [
                "=== interfaces (active) ===",
                "=== default route ===",
                "=== connectivity ===",
            ],
        ),
    ],
)
def test_generated_system_scripts_exit_zero_and_print_expected_sections(
    generated_scripts: Path, script_name: str, args: list[str], expected_fragments: list[str]
) -> None:
    result = subprocess.run(
        [str(generated_scripts / script_name), *args],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "LC_ALL": "C"},
    )

    assert result.returncode == 0, result.stderr
    for fragment in expected_fragments:
        # mac_ram.sh on Linux uses `free` (-> "Mem:"), or falls back to
        # /proc/meminfo (-> "MemTotal:") on the rare box without `free`.
        if fragment == "Mem:":
            assert ("Mem:" in result.stdout) or ("MemTotal" in result.stdout), result.stdout
        else:
            assert fragment in result.stdout


@pytest.mark.parametrize(
    ("script_name", "marker"),
    [
        ("mac_health.sh", "MH"),
        ("mac_ram.sh", "MR"),
        ("mac_disk.sh", "MD"),
        ("mac_top.sh", "MT"),
        ("mac_network.sh", "MN"),
    ],
)
def test_example_system_scripts_match_install_templates(script_name: str, marker: str) -> None:
    example_path = REPO_ROOT / "examples" / "allowed_scripts" / script_name
    assert example_path.read_text() == _extract_script(script_name, marker)


# ─────────────────────────────────────────────────────────────────────────────
# process_kill.sh tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def process_kill_script(tmp_path: Path) -> Path:
    """Extract process_kill.sh from install.sh into a tmp dir and make it executable."""
    script_path = tmp_path / "process_kill.sh"
    script_path.write_text(_extract_script("process_kill.sh", "PK"))
    script_path.chmod(0o755)
    return script_path


def _fake_kill(tmp_path: Path, behaviour: str) -> Path:
    """Create a fake `kill` binary.

    behaviour values:
      'success'   — exits 0 for -0 (exists check) and -TERM (kill)
      'no_proc'   — exits 1 for -0 (process does not exist)
      'term_fail' — exits 0 for -0 but 1 for -TERM
    """
    kill = tmp_path / "fake_kill"
    if behaviour == "success":
        kill.write_text(
            "#!/usr/bin/env bash\n"
            "# -0 = exists check, -TERM = terminate, both succeed\n"
            "exit 0\n"
        )
    elif behaviour == "no_proc":
        kill.write_text(
            "#!/usr/bin/env bash\n"
            "exit 1\n"
        )
    elif behaviour == "term_fail":
        kill.write_text(
            "#!/usr/bin/env bash\n"
            "[[ \"$1\" == '-0' ]] && exit 0\n"
            "exit 1\n"
        )
    kill.chmod(0o755)
    return kill


def _fake_pgrep(tmp_path: Path, pids: list[int] | None) -> Path:
    """Create a fake `pgrep -x` binary returning the given PIDs (one per line).

    pids=None means the process is not found (exit 1, no output).
    """
    pgrep = tmp_path / "fake_pgrep"
    if pids is None:
        pgrep.write_text("#!/usr/bin/env bash\nexit 1\n")
    else:
        output = "\\n".join(str(p) for p in pids)
        pgrep.write_text(
            "#!/usr/bin/env bash\n"
            f'printf "{output}\\n"\n'
            "exit 0\n"
        )
    pgrep.chmod(0o755)
    return pgrep


def _run_pk(script: Path, args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    base_env = {**os.environ}
    if env:
        base_env.update(env)
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        check=False,
        env=base_env,
    )


# ── Safety guards ─────────────────────────────────────────────────────────────

def test_process_kill_refuses_pid_le_10(process_kill_script: Path, tmp_path: Path) -> None:
    """PIDs ≤ 10 must always be refused, regardless of what kill returns."""
    fake_kill = _fake_kill(tmp_path, "success")
    result = _run_pk(process_kill_script, ["5"], {"BRIDGE_KILL_CMD": str(fake_kill)})
    assert result.returncode != 0
    assert "≤ 10" in result.stderr or "10" in result.stderr


def test_process_kill_refuses_pid_1(process_kill_script: Path, tmp_path: Path) -> None:
    fake_kill = _fake_kill(tmp_path, "success")
    result = _run_pk(process_kill_script, ["1"], {"BRIDGE_KILL_CMD": str(fake_kill)})
    assert result.returncode != 0


@pytest.mark.parametrize("protected", ["launchd", "kernel_task", "systemd", "init", "kernel", "kthreadd"])
def test_process_kill_refuses_protected_names(
    process_kill_script: Path, tmp_path: Path, protected: str
) -> None:
    """Protected process names must be refused before any pgrep/kill call."""
    fake_pgrep = _fake_pgrep(tmp_path, [12345])
    fake_kill = _fake_kill(tmp_path, "success")
    result = _run_pk(
        process_kill_script, [protected],
        {"BRIDGE_PGREP_CMD": str(fake_pgrep), "BRIDGE_KILL_CMD": str(fake_kill)},
    )
    assert result.returncode != 0
    assert "protected" in result.stderr.lower() or "refusing" in result.stderr.lower()


def test_process_kill_refuses_nonexistent_pid(process_kill_script: Path, tmp_path: Path) -> None:
    """A PID that does not exist (kill -0 fails) should be refused."""
    fake_kill = _fake_kill(tmp_path, "no_proc")
    result = _run_pk(process_kill_script, ["9999"], {"BRIDGE_KILL_CMD": str(fake_kill)})
    assert result.returncode != 0
    assert "no process" in result.stderr.lower() or "9999" in result.stderr


# ── Name-path behaviour ───────────────────────────────────────────────────────

def test_process_kill_name_not_found(process_kill_script: Path, tmp_path: Path) -> None:
    fake_pgrep = _fake_pgrep(tmp_path, None)
    result = _run_pk(process_kill_script, ["myapp"], {"BRIDGE_PGREP_CMD": str(fake_pgrep)})
    assert result.returncode != 0
    assert "no process" in result.stderr.lower() or "myapp" in result.stderr


def test_process_kill_name_multiple_match_no_all_flag(
    process_kill_script: Path, tmp_path: Path
) -> None:
    """Multiple matches without --all should fail with a helpful message."""
    fake_pgrep = _fake_pgrep(tmp_path, [1234, 5678])
    fake_kill = _fake_kill(tmp_path, "success")
    result = _run_pk(
        process_kill_script, ["myapp"],
        {"BRIDGE_PGREP_CMD": str(fake_pgrep), "BRIDGE_KILL_CMD": str(fake_kill)},
    )
    assert result.returncode != 0
    assert "--all" in result.stderr or "2" in result.stderr


def test_process_kill_name_multiple_match_with_all_flag(
    process_kill_script: Path, tmp_path: Path
) -> None:
    """Multiple matches with --all should kill all and succeed."""
    fake_pgrep = _fake_pgrep(tmp_path, [1234, 5678])
    # kill always succeeds; pgrep returns empty on second call (all gone)
    fake_kill = _fake_kill(tmp_path, "success")
    # second pgrep call (post-kill check) returns no matches
    fake_pgrep2 = _fake_pgrep(tmp_path / "p2", None)
    # We can't easily swap pgrep mid-run, so we provide one that returns empty
    # on any call (simulates all processes gone immediately after kill)
    fake_pgrep_gone = tmp_path / "fake_pgrep_gone"
    fake_pgrep_gone.write_text(
        "#!/usr/bin/env bash\n"
        "# First call returns two PIDs, subsequent calls return nothing\n"
        'STATE_FILE="$(dirname "$0")/.pgrep_called"\n'
        'if [[ ! -f "$STATE_FILE" ]]; then\n'
        '  touch "$STATE_FILE"\n'
        '  printf "1234\\n5678\\n"\n'
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )
    fake_pgrep_gone.chmod(0o755)
    result = _run_pk(
        process_kill_script, ["myapp", "--all"],
        {"BRIDGE_PGREP_CMD": str(fake_pgrep_gone), "BRIDGE_KILL_CMD": str(fake_kill)},
    )
    assert result.returncode == 0
    assert "terminated" in result.stdout.lower() or "✓" in result.stdout


def test_process_kill_name_single_match_succeeds(
    process_kill_script: Path, tmp_path: Path
) -> None:
    """Single name match with a cooperating fake kill should succeed."""
    fake_pgrep_stateful = tmp_path / "fake_pgrep_single"
    fake_pgrep_stateful.write_text(
        "#!/usr/bin/env bash\n"
        'STATE_FILE="$(dirname "$0")/.pgrep_called"\n'
        'if [[ ! -f "$STATE_FILE" ]]; then\n'
        '  touch "$STATE_FILE"\n'
        '  printf "9999\\n"\n'
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )
    fake_pgrep_stateful.chmod(0o755)
    fake_kill = _fake_kill(tmp_path, "success")
    result = _run_pk(
        process_kill_script, ["myapp"],
        {"BRIDGE_PGREP_CMD": str(fake_pgrep_stateful), "BRIDGE_KILL_CMD": str(fake_kill)},
    )
    assert result.returncode == 0
    assert "✓" in result.stdout or "terminated" in result.stdout.lower()


# ── Template sync ─────────────────────────────────────────────────────────────

def test_process_kill_example_matches_install_template() -> None:
    """examples/allowed_scripts/process_kill.sh must match the install.sh heredoc exactly."""
    example_path = REPO_ROOT / "examples" / "allowed_scripts" / "process_kill.sh"
    assert example_path.read_text() == _extract_script("process_kill.sh", "PK")
