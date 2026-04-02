#!/usr/bin/env python3
"""Tests for semantic validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_semantic import extract_role_name, validate_semantic


def test_extract_role_name_em_dash():
    """Test role extraction with em-dash separator."""
    assert extract_role_name("Researcher — exploring domain") == "Researcher"
    assert extract_role_name("Architect — designing structure") == "Architect"


def test_extract_role_name_regular_dash():
    """Test role extraction with regular dash separator."""
    assert extract_role_name("Researcher - exploring domain") == "Researcher"
    assert extract_role_name("Architect - designing structure") == "Architect"


def test_extract_role_name_no_separator():
    """Test role extraction without separator."""
    assert extract_role_name("Coordinator") == "Coordinator"


def test_validate_semantic_undefined_role():
    """Test that undefined role in role_mindset is caught."""
    playbook = {
        "roles": {"Coordinator": "Manages phases"},
        "checklists": [
            {
                "title": "Phase 0: Start",
                "compilation": {
                    "role_mindset": "Researcher — undefined role"
                }
            }
        ],
        "failure_modes": []
    }

    errors, warnings = validate_semantic(playbook)
    assert len(errors) > 0
    assert "undefined role" in errors[0]


def test_validate_semantic_invalid_phase_ref():
    """Test that failure mode with invalid phase reference is caught."""
    playbook = {
        "roles": {"Coordinator": "Manages"},
        "checklists": [
            {"title": "Phase 0: Start", "compilation": {"role_mindset": "Coordinator"}}
        ],
        "failure_modes": [
            {"id": "FM-001", "phase": "Phase 99: Nonexistent"}
        ]
    }

    errors, warnings = validate_semantic(playbook)
    assert len(errors) > 0
    assert "non-existent phase" in errors[0].lower()


def test_validate_semantic_invalid_classification():
    """Test that invalid complexity classification is caught."""
    playbook = {
        "roles": {},
        "checklists": [],
        "failure_modes": [],
        "complexity_profile": {
            "classification": "invalid_class",
            "expected_phases": 5
        }
    }

    errors, warnings = validate_semantic(playbook)
    assert len(errors) > 0
    assert "classification" in errors[0]


def test_validate_semantic_passes():
    """Test that valid playbook passes."""
    playbook = {
        "roles": {"Coordinator": "Manages phases"},
        "checklists": [
            {
                "title": "Phase 0: Start",
                "compilation": {"role_mindset": "Coordinator — managing"}
            }
        ],
        "failure_modes": []
    }

    errors, warnings = validate_semantic(playbook)
    assert len(errors) == 0


if __name__ == "__main__":
    test_extract_role_name_em_dash()
    test_extract_role_name_regular_dash()
    test_extract_role_name_no_separator()
    test_validate_semantic_undefined_role()
    test_validate_semantic_invalid_phase_ref()
    test_validate_semantic_invalid_classification()
    test_validate_semantic_passes()
    print("All tests passed!")