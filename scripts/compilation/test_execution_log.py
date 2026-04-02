#!/usr/bin/env python3
"""Tests for execution log."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution_log import (
    create_execution_log,
    write_execution_log,
    read_execution_log,
    get_latest_execution_log,
)


def test_create_execution_log():
    """Test creating execution log structure."""
    log = create_execution_log(
        playbook_path="test.json",
        status="completed",
        phases_completed=5,
        duration_seconds=120
    )

    assert log["status"] == "completed"
    assert log["phases_completed"] == 5
    assert log["duration_seconds"] == 120
    assert "run_id" in log
    assert "failure_modes_discovered" in log


def test_create_execution_log_with_failure_modes():
    """Test creating log with failure modes."""
    fms = [{"id": "FM-NEW-001", "symptom": "Test issue"}]
    log = create_execution_log(
        playbook_path="test.json",
        status="completed",
        phases_completed=5,
        duration_seconds=120,
        failure_modes_discovered=fms
    )

    assert log["failure_modes_discovered"] == fms


def test_write_and_read_execution_log():
    """Test write/read roundtrip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = create_execution_log(
            playbook_path="test.json",
            status="completed",
            phases_completed=10,
            duration_seconds=300
        )

        path = write_execution_log(log, Path(tmpdir))
        assert path.exists()

        read_log = read_execution_log(path)
        assert read_log["status"] == "completed"
        assert read_log["phases_completed"] == 10


def test_get_latest_execution_log():
    """Test finding latest log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple logs
        log1 = create_execution_log("test.json", "completed", 5, 100)
        log2 = create_execution_log("test.json", "completed", 10, 200)

        import time
        path1 = write_execution_log(log1, Path(tmpdir))
        time.sleep(0.1)  # Ensure different mtime
        path2 = write_execution_log(log2, Path(tmpdir))

        latest = get_latest_execution_log(Path(tmpdir))
        assert latest == path2


def test_get_latest_execution_log_empty():
    """Test finding latest log when none exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        latest = get_latest_execution_log(Path(tmpdir))
        assert latest is None


def test_read_execution_log_not_found():
    """Test reading non-existent log."""
    result = read_execution_log(Path("/nonexistent/file.json"))
    assert result is None


if __name__ == "__main__":
    test_create_execution_log()
    test_create_execution_log_with_failure_modes()
    test_write_and_read_execution_log()
    test_get_latest_execution_log()
    test_get_latest_execution_log_empty()
    test_read_execution_log_not_found()
    print("All tests passed!")