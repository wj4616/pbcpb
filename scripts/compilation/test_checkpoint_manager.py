#!/usr/bin/env python3
"""Tests for checkpoint manager."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from checkpoint_manager import (
    compute_checksum,
    save_checkpoint,
    verify_checkpoint,
    get_checkpoint,
)


def test_compute_checksum_consistent():
    """Test that same content produces same checksum."""
    content = "test content"
    checksum1 = compute_checksum(content)
    checksum2 = compute_checksum(content)
    assert checksum1 == checksum2
    assert len(checksum1) == 16


def test_compute_checksum_different():
    """Test that different content produces different checksum."""
    checksum1 = compute_checksum("content a")
    checksum2 = compute_checksum("content b")
    assert checksum1 != checksum2


def test_save_checkpoint():
    """Test saving checkpoint creates file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        artifacts = {"test.md": "# Test\n\nContent here"}

        path = save_checkpoint(phase=1, artifacts=artifacts, checkpoint_dir=checkpoint_dir)

        assert path.exists()
        assert "checkpoint-phase01.json" in str(path)


def test_verify_checkpoint_phase_zero():
    """Test that Phase 0 verification passes (no previous phase)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        artifacts = {"test.md": "content"}

        passed, mismatches = verify_checkpoint(phase=0, artifacts=artifacts, checkpoint_dir=checkpoint_dir)
        assert passed
        assert len(mismatches) == 0


def test_verify_checkpoint_missing_previous():
    """Test that verification fails when previous checkpoint missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        artifacts = {"test.md": "content"}

        # Phase 1 has no phase 0 checkpoint
        passed, mismatches = verify_checkpoint(phase=1, artifacts=artifacts, checkpoint_dir=checkpoint_dir)
        assert not passed
        assert "No checkpoint" in mismatches[0]


def test_verify_checkpoint_match():
    """Test verification passes when checksums match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)

        # Save phase 0 checkpoint
        artifacts = {"test.md": "# Test\nContent"}
        save_checkpoint(phase=0, artifacts=artifacts, checkpoint_dir=checkpoint_dir)

        # Verify phase 1 against phase 0
        passed, mismatches = verify_checkpoint(phase=1, artifacts=artifacts, checkpoint_dir=checkpoint_dir)
        assert passed


def test_verify_checksum_mismatch():
    """Test verification fails when content changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)

        # Save phase 0 checkpoint
        save_checkpoint(phase=0, artifacts={"test.md": "original"}, checkpoint_dir=checkpoint_dir)

        # Verify with different content
        passed, mismatches = verify_checkpoint(phase=1, artifacts={"test.md": "changed"}, checkpoint_dir=checkpoint_dir)
        assert not passed
        assert "mismatch" in mismatches[0].lower()


def test_get_checkpoint():
    """Test getting checkpoint data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        save_checkpoint(phase=2, artifacts={"file.md": "content"}, checkpoint_dir=checkpoint_dir)

        data = get_checkpoint(phase=2, checkpoint_dir=checkpoint_dir)
        assert data is not None
        assert data["phase"] == 2


if __name__ == "__main__":
    test_compute_checksum_consistent()
    test_compute_checksum_different()
    test_save_checkpoint()
    test_verify_checkpoint_phase_zero()
    test_verify_checkpoint_missing_previous()
    test_verify_checkpoint_match()
    test_verify_checksum_mismatch()
    test_get_checkpoint()
    print("All tests passed!")