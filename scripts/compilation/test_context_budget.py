"""Tests for context_budget module."""

import sys
from pathlib import Path

# Add scripts to path for compilation module
sys.path.insert(0, str(Path(__file__).parent.parent))

from compilation.context_budget import load_context_with_budget, estimate_file_tokens


def test_basic_loading():
    """Test basic file loading within budget."""
    files = {
        "file1.md": "a" * 1000,  # ~250 tokens
        "file2.md": "b" * 1000,  # ~250 tokens
    }

    result = load_context_with_budget(
        files=files,
        priority={"file1.md": 1, "file2.md": 2},
        max_tokens=10000,
        critical_threshold=3,
    )

    assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
    assert "file1.md" in result.loaded_files
    assert "file2.md" in result.loaded_files
    print("PASS: test_basic_loading")


def test_budget_exceeded():
    """Test skipping non-critical files when budget exceeded."""
    files = {
        "essential.md": "a" * 1000,   # ~250 tokens, priority 1
        "optional.md": "b" * 20000,  # ~5000 tokens, priority 8
    }

    # Need enough budget for system_prompt (2000) + response (4096) + essential (250) = 6346
    # But not enough for optional (5000)
    result = load_context_with_budget(
        files=files,
        priority={"essential.md": 1, "optional.md": 8},
        max_tokens=10000,  # Budget for essential + system + response, but not optional
        critical_threshold=3,
    )

    assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
    assert "essential.md" in result.loaded_files
    assert "essential.md" not in result.skipped_files
    assert "optional.md" in result.skipped_files
    print("PASS: test_budget_exceeded")


def test_critical_file_error():
    """Test error when critical files cannot fit."""
    files = {
        "critical.md": "a" * 100000,  # ~25000 tokens
    }

    # Budget too small: 5000 - 2000 (system) - 4096 (response) = -1096 available
    result = load_context_with_budget(
        files=files,
        priority={"critical.md": 1},
        max_tokens=5000,  # Too small for system + response
        critical_threshold=3,
    )

    assert len(result.errors) > 0
    assert "Insufficient budget" in result.errors[0]
    print("PASS: test_critical_file_error")


def test_default_priority():
    """Test files without priority get default 5."""
    files = {
        "file1.md": "a" * 1000,
        "file2.md": "b" * 1000,  # No priority specified
    }

    result = load_context_with_budget(
        files=files,
        priority={"file1.md": 1},  # file2.md has no priority
        max_tokens=10000,
    )

    assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
    assert len(result.loaded_files) == 2
    print("PASS: test_default_priority")


def test_orphaned_priority_error():
    """Test error when priority references file not in context_load."""
    files = {
        "file1.md": "a" * 1000,
    }

    result = load_context_with_budget(
        files=files,
        priority={"file1.md": 1, "file2.md": 1},  # file2 not in files
        max_tokens=10000,
    )

    assert len(result.errors) > 0
    assert "not in context_load" in result.errors[0]
    print("PASS: test_orphaned_priority_error")


def test_invalid_priority_range():
    """Test error for priority values outside 1-10."""
    files = {
        "file1.md": "a" * 1000,
    }

    result = load_context_with_budget(
        files=files,
        priority={"file1.md": 15},  # Invalid
        max_tokens=10000,
    )

    assert len(result.errors) > 0
    assert "Invalid priority" in result.errors[0]
    print("PASS: test_invalid_priority_range")


def test_token_estimation():
    """Test token estimation."""
    content = "This is a test content"
    tokens = estimate_file_tokens(content)
    # ~22 chars / 4 = ~5 tokens
    assert 3 <= tokens <= 10
    print("PASS: test_token_estimation")


if __name__ == "__main__":
    test_basic_loading()
    test_budget_exceeded()
    test_critical_file_error()
    test_default_priority()
    test_orphaned_priority_error()
    test_invalid_priority_range()
    test_token_estimation()
    print("\nAll tests passed!")