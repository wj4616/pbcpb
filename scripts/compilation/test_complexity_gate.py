#!/usr/bin/env python3
"""Tests for complexity gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from complexity_gate import (
    calculate_complexity_score,
    classify_from_score,
    classify_complexity,
    verify_complexity_match,
)


def test_calculate_complexity_score_simple():
    """Test score calculation for simple playbook."""
    # 4 phases, 2 roles, 2 cccs = 1 + 1 + 0 = 2 (simple)
    score = calculate_complexity_score(phases=4, roles=2, cccs=2)
    assert score == 2


def test_calculate_complexity_score_complex():
    """Test score calculation for complex playbook."""
    # 16 phases, 6 roles, 9 cccs = 4 + 3 + 3 = 10 (structured)
    score = calculate_complexity_score(phases=16, roles=6, cccs=9)
    assert score == 10


def test_classify_from_score():
    """Test classification from score."""
    assert classify_from_score(0) == "simple"
    assert classify_from_score(2) == "simple"
    assert classify_from_score(3) == "moderate"
    assert classify_from_score(5) == "moderate"
    assert classify_from_score(6) == "complex"
    assert classify_from_score(8) == "complex"
    assert classify_from_score(9) == "structured"
    assert classify_from_score(12) == "structured"


def test_classify_complexity():
    """Test full classification."""
    playbook = {
        "checklists": [{}] * 8,  # 8 phases
        "roles": {"A": "a", "B": "b", "C": "c"},  # 3 roles
        "cross_cutting_concerns": ["x", "y", "z"]  # 3 cccs
    }

    result = classify_complexity(playbook)
    assert result["actual_phases"] == 8
    assert result["actual_roles"] == 3
    assert result["actual_cccs"] == 3
    assert "classification" in result
    assert "complexity_score" in result


def test_verify_complexity_match_no_profile():
    """Test verification fails without profile."""
    playbook = {"checklists": [], "roles": {}, "cross_cutting_concerns": []}
    passed, issues = verify_complexity_match(playbook)
    assert not passed
    assert "No complexity_profile" in issues[0]


def test_verify_complexity_match_passes():
    """Test verification passes when within limits."""
    playbook = {
        "checklists": [{}] * 8,
        "roles": {"A": "a"},
        "cross_cutting_concerns": [],
        "complexity_profile": {
            "classification": "moderate",
            "expected_phases": 10
        }
    }

    passed, issues = verify_complexity_match(playbook)
    assert passed


def test_verify_complexity_match_exceeds_variance():
    """Test verification fails when exceeding variance."""
    playbook = {
        "checklists": [{}] * 20,  # Way more than expected
        "roles": {"A": "a"},
        "cross_cutting_concerns": [],
        "complexity_profile": {
            "classification": "simple",
            "expected_phases": 5  # 20 phases is 300% over
        }
    }

    passed, issues = verify_complexity_match(playbook)
    assert not passed


if __name__ == "__main__":
    test_calculate_complexity_score_simple()
    test_calculate_complexity_score_complex()
    test_classify_from_score()
    test_classify_complexity()
    test_verify_complexity_match_no_profile()
    test_verify_complexity_match_passes()
    test_verify_complexity_match_exceeds_variance()
    print("All tests passed!")