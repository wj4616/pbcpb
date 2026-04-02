"""Tests for system_prompt module."""

import sys
from pathlib import Path

# Add scripts to path for compilation module
sys.path.insert(0, str(Path(__file__).parent.parent))

from compilation.system_prompt import generate_system_prompt, estimate_prompt_tokens


def test_basic_prompt():
    """Test basic prompt generation."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {
            "Researcher": "Domain research, best practices, SME knowledge."
        },
        "failure_modes": [
            {
                "id": "FM-001",
                "symptom": "Research scope creep",
                "prevention": "Stay within scope.md boundaries"
            }
        ]
    }

    phase = {
        "title": "Phase 1: Test",
        "compilation": {
            "role_mindset": "Researcher — gather information",
            "objective": "Gather domain information",
            "pre_check": ["Scope defined"],
            "failure_modes_relevant": ["FM-001"]
        },
        "items": [
            {
                "handoff": {
                    "output_artifacts": ["test.md"]
                }
            }
        ]
    }

    loaded_files = {"artifact-manifest.md": "| File | Phase | Status | Summary |\n| test.md | 1 | Done | Test file |"}

    prompt = generate_system_prompt(playbook, phase, loaded_files)

    assert "Researcher" in prompt
    assert "Domain research" in prompt
    assert "gather information" in prompt
    assert "Gather domain information" in prompt
    assert "FM-001" in prompt
    assert "test.md" in prompt
    assert "mindset is focused on" in prompt  # Expanded mindset
    print("PASS: test_basic_prompt")


def test_prompt_with_object_role():
    """Test prompt with object-style role definition."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {
            "Auditor": {
                "description": "Quality review and verification",
                "defaults": {
                    "model": "opus",
                    "temperature": [0.0, 0.2]
                }
            }
        }
    }

    phase = {
        "title": "Phase 9: Test",
        "compilation": {
            "role_mindset": "Auditor — find flaws and gaps"
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    assert "Auditor" in prompt
    assert "Quality review and verification" in prompt
    assert "find flaws and gaps" in prompt
    assert "mindset is focused on" in prompt
    print("PASS: test_prompt_with_object_role")


def test_prompt_with_flags_disabled():
    """Test prompt with some flags disabled."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {"Coordinator": "Phase gates and tracking."}
    }

    phase = {
        "title": "Phase 0: Test",
        "compilation": {
            "role_mindset": "Coordinator"
        },
        "items": []
    }

    flags = {
        "failure_modes": False,
        "context_files": False,
        "handoff_requirements": False
    }

    prompt = generate_system_prompt(playbook, phase, {}, flags)

    assert "Coordinator" in prompt
    assert "Failure Modes" not in prompt
    print("PASS: test_prompt_with_flags_disabled")


def test_token_estimation():
    """Test token estimation."""
    prompt = "This is a test prompt with some words."
    tokens = estimate_prompt_tokens(prompt)
    # Roughly 40 chars / 4 = 10 tokens
    assert 5 <= tokens <= 15
    print("PASS: test_token_estimation")


def test_prompt_with_role_context():
    """Test prompt includes role_context between description and mindset."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {
            "Builder": {
                "description": "Task titles/descriptions, JSON assembly, validation",
                "role_context": "Mechanical precision. Follow specifications exactly. No creative interpretation.",
                "defaults": {
                    "model": "sonnet",
                    "temperature": [0.2, 0.4]
                },
                "agent_assignment": "single"
            }
        },
        "failure_modes": []
    }

    phase = {
        "title": "Phase 3: Test",
        "compilation": {
            "role_mindset": "Builder — executing the KB blueprint",
            "objective": "Build the KB directory structure",
            "pre_check": [],
            "failure_modes_relevant": []
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    assert "Task titles/descriptions" in prompt, "description missing"
    assert "Mechanical precision" in prompt, "role_context missing"
    assert "executing the KB blueprint" in prompt, "mindset missing"

    # Verify ordering: description before role_context before mindset
    desc_pos = prompt.index("Task titles/descriptions")
    ctx_pos = prompt.index("Mechanical precision")
    mindset_pos = prompt.index("executing the KB blueprint")
    assert desc_pos < ctx_pos < mindset_pos, (
        f"Wrong order: description@{desc_pos}, context@{ctx_pos}, mindset@{mindset_pos}"
    )
    print("PASS: test_prompt_with_role_context")


def test_prompt_with_success_criteria():
    """Test prompt includes success_criteria section."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {"Builder": "Assembly and validation."},
        "failure_modes": []
    }

    phase = {
        "title": "Phase 9: Test",
        "compilation": {
            "role_mindset": "Builder — assembling JSON",
            "objective": "Assemble JSON",
            "pre_check": [],
            "failure_modes_relevant": [],
            "success_criteria": [
                "JSON parses without errors",
                "All 16 required fields present"
            ]
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    assert "Success Criteria" in prompt
    assert "JSON parses without errors" in prompt
    assert "All 16 required fields present" in prompt
    assert "ALL of the following are true" in prompt
    print("PASS: test_prompt_with_success_criteria")


def test_prompt_with_tools_available():
    """Test prompt includes tools_available section."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {"Researcher": "Research and synthesis."},
        "failure_modes": []
    }

    phase = {
        "title": "Phase 1: Test",
        "compilation": {
            "role_mindset": "Researcher — gather info",
            "objective": "Research the domain",
            "pre_check": [],
            "failure_modes_relevant": [],
            "tools_available": [
                "web_search",
                "file_reading",
                "user_questioning"
            ]
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    assert "Allowed Tools" in prompt
    assert "web_search" in prompt
    assert "file_reading" in prompt
    assert "Do NOT use tools or capabilities outside this list" in prompt
    print("PASS: test_prompt_with_tools_available")


def test_prompt_with_behavioral_profile():
    """Test prompt includes behavioral_profile section."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {"Auditor": "Quality review."},
        "failure_modes": []
    }

    phase = {
        "title": "Phase 12: Test",
        "compilation": {
            "role_mindset": "Auditor — stress testing",
            "objective": "Break the playbook",
            "pre_check": [],
            "failure_modes_relevant": [],
            "behavioral_profile": {
                "risk_tolerance": "minimal",
                "creativity_level": "strict",
                "verbosity": "comprehensive",
                "stance": "adversarial"
            }
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    assert "Behavioral Profile" in prompt
    assert "Risk tolerance: minimal" in prompt
    assert "Creativity: strict" in prompt
    assert "Verbosity: comprehensive" in prompt
    assert "Thorough coverage" in prompt  # Verbosity expansion map
    assert "Stance: adversarial" in prompt
    assert "Try to break it" in prompt
    print("PASS: test_prompt_with_behavioral_profile")


def test_prompt_without_new_fields():
    """Test that prompts still work fine without new optional fields."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {"Coordinator": "Tracking."},
        "failure_modes": []
    }

    phase = {
        "title": "Phase 0: Test",
        "compilation": {
            "role_mindset": "Coordinator",
            "objective": "Track progress",
            "pre_check": [],
            "failure_modes_relevant": []
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    # New sections should NOT appear
    assert "Success Criteria" not in prompt
    assert "Allowed Tools" not in prompt
    assert "Behavioral Profile" not in prompt
    # Old sections should still work
    assert "Coordinator" in prompt
    assert "Track progress" in prompt
    print("PASS: test_prompt_without_new_fields")


if __name__ == "__main__":
    test_basic_prompt()
    test_prompt_with_object_role()
    test_prompt_with_flags_disabled()
    test_token_estimation()
    test_prompt_with_role_context()
    test_prompt_with_success_criteria()
    test_prompt_with_tools_available()
    test_prompt_with_behavioral_profile()
    test_prompt_without_new_fields()
    print("\nAll tests passed!")