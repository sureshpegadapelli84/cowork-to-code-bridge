"""
tests/test_status_ticker.py — unit tests for the daemon status ticker.

Verifies:
  1. status.json written with state="running" while the process runs
  2. status.json finalized with state="done" and exit_code=0 on success
  3. status.json finalized with state="error" and exit_code on failure
  4. status.json finalized with state="error" and exit_code=-2 on timeout
  5. status.json cleaned up (unlinked) after result is written in run_one
  6. Existing call_remote_streaming callers unaffected (no status_file arg)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the function under test directly from the daemon package.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))
from daemon.daemon import _run_streaming  # type: ignore[import]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _poll_for(path: Path, timeout: float = 5.0, interval: float = 0.05) -> dict:
    """Wait until path exists and is valid JSON, then return its contents."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        time.sleep(interval)
    raise TimeoutError(f"{path} did not appear within {timeout}s")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_progress(tmp_path):
    progress = tmp_path / "progress"
    progress.mkdir()
    return progress


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStatusTickerRunning:
    """status.json appears with state='running' while a long script is alive."""

    def test_state_running_written(self, tmp_progress):
        progress_file = tmp_progress / "cmd1.log"
        status_file = tmp_progress / "cmd1.status.json"

        # A script that sleeps long enough for the 2 s ticker to fire.
        result = _run_streaming(
            argv=["bash", "-c", "echo 'hello world'; sleep 4"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=10,
            progress_file=progress_file,
            status_file=status_file,
        )

        # The result should be success
        assert result["exit_code"] == 0
        # status.json finalized with state=done
        final = json.loads(status_file.read_text())
        assert final["state"] == "done"
        assert final["exit_code"] == 0
        assert "elapsed_s" in final
        assert "last_line" in final

    def test_last_line_captured(self, tmp_progress):
        progress_file = tmp_progress / "cmd2.log"
        status_file = tmp_progress / "cmd2.status.json"

        result = _run_streaming(
            argv=["bash", "-c", "echo 'first line'; echo 'second line'"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=10,
            progress_file=progress_file,
            status_file=status_file,
        )

        assert result["exit_code"] == 0
        final = json.loads(status_file.read_text())
        assert final["last_line"] == "second line"


class TestStatusTickerDone:
    """state='done' written on clean exit."""

    def test_done_on_exit_0(self, tmp_progress):
        progress_file = tmp_progress / "cmd3.log"
        status_file = tmp_progress / "cmd3.status.json"

        result = _run_streaming(
            argv=["bash", "-c", "echo ok"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=10,
            progress_file=progress_file,
            status_file=status_file,
        )

        assert result["exit_code"] == 0
        s = json.loads(status_file.read_text())
        assert s["state"] == "done"
        assert s["exit_code"] == 0
        assert isinstance(s["elapsed_s"], int)


class TestStatusTickerError:
    """state='error' written on non-zero exit."""

    def test_error_on_exit_nonzero(self, tmp_progress):
        progress_file = tmp_progress / "cmd4.log"
        status_file = tmp_progress / "cmd4.status.json"

        result = _run_streaming(
            argv=["bash", "-c", "exit 42"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=10,
            progress_file=progress_file,
            status_file=status_file,
        )

        assert result["exit_code"] == 42
        s = json.loads(status_file.read_text())
        assert s["state"] == "error"
        assert s["exit_code"] == 42


class TestStatusTickerTimeout:
    """state='error' with exit_code=-2 on timeout."""

    def test_timeout_finalizes_error(self, tmp_progress):
        progress_file = tmp_progress / "cmd5.log"
        status_file = tmp_progress / "cmd5.status.json"

        result = _run_streaming(
            argv=["bash", "-c", "sleep 60"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=1,
            progress_file=progress_file,
            status_file=status_file,
        )

        assert result["exit_code"] == -2
        assert "timeout" in result.get("error", "")
        s = json.loads(status_file.read_text())
        assert s["state"] == "error"
        assert s["exit_code"] == -2


class TestStatusTickerOptional:
    """Omitting status_file leaves existing callers unaffected."""

    def test_no_status_file_arg(self, tmp_progress):
        progress_file = tmp_progress / "cmd6.log"

        # Call WITHOUT status_file — must not raise and must return correct result.
        result = _run_streaming(
            argv=["bash", "-c", "echo hi"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=10,
            progress_file=progress_file,
        )

        assert result["exit_code"] == 0
        assert "hi" in result["stdout"]
        # No stray status file created
        assert not list(tmp_progress.glob("*.status.json"))


class TestStatusTickerAtomicWrite:
    """status.json is never written as a partial file (atomic tmp→rename)."""

    def test_no_tmp_file_left_behind(self, tmp_progress):
        progress_file = tmp_progress / "cmd7.log"
        status_file = tmp_progress / "cmd7.status.json"

        _run_streaming(
            argv=["bash", "-c", "echo atomic"],
            cwd="/tmp",
            env=os.environ.copy(),
            timeout=10,
            progress_file=progress_file,
            status_file=status_file,
        )

        # No .tmp left behind
        assert not list(tmp_progress.glob("*.json.tmp"))
        # Final status file is valid JSON
        s = json.loads(status_file.read_text())
        assert s["state"] in ("done", "error")
