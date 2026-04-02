"""Integration tests for compilation block enhancements.

Tests end-to-end functionality:
- Config resolution from playbook + phase
- System prompt generation with real role
- Context budget loading with priority
- Model fallback with unavailable model
- Validation catches all new errors
"""

import sys
import json
from pathlib import Path

# Add scripts to path for compilation module
sys.path.insert(0, str(Path(__file__).parent.parent))

from compilation import (
    generate_system_prompt,
    load_context_with_budget,
    get_agent_config,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_CONTEXT_BUDGET_TOKENS,
)


def test_end_to_end_config_resolution():
    """Test full config resolution from playbook and phase."""
    print("Testing end-to-end config resolution...")

    # Simulate playbook structure
    playbook = {
        "defaults": {
            "model": "opus",
            "temperature": 0.3,
            "max_tokens": 8192,
            "context_budget_tokens": 100000,
        },
        "roles": {
            "Researcher": {
                "description": "Domain research and analysis",
                "defaults": {
                    "model": "sonnet",
                    "temperature": [0.4, 0.7],
                }
            },
            "Architect": {
                "description": "System design and structure",
                "defaults": {
                    "model": "opus",
                    "temperature": [0.2, 0.4],
                }
            }
        }
    }

    # Phase compilation block
    phase_compilation = {
        "role_mindset": "Researcher — exploring domain knowledge",
        "agent_config": {
            "temperature": 0.55,  # Override
        },
        "context_budget": {
            "max_tokens": 80000
        }
    }

    # Get agent config with model fallback chain
    available_models = ["sonnet", "haiku"]  # opus not available
    config = get_agent_config(phase_compilation, playbook, "Researcher — exploring domain knowledge", available_models)

    # Assertions
    # Role model is "sonnet", and it's available, so that's what we use
    assert config["model"] == "sonnet", f"Expected sonnet (role default), got {config['model']}"
    assert "model_fallback_chain" in config, "Should include fallback chain"
    # Fallback chain is [primary, ...fallbacks] = ["sonnet", "haiku"]
    assert config["model_fallback_chain"] == ["sonnet", "haiku"], \
        f"Expected ['sonnet', 'haiku'], got {config['model_fallback_chain']}"
    assert config["temperature"] == 0.55, f"Expected 0.55 (phase override), got {config['temperature']}"
    assert config["max_tokens"] == 8192, f"Expected 8192 (playbook default), got {config['max_tokens']}"
    assert config["context_budget_tokens"] == 80000, f"Expected 80000 (phase override), got {config['context_budget_tokens']}"

    print("PASS: test_end_to_end_config_resolution")


def test_system_prompt_generation():
    """Test system prompt generation from role and objective."""
    print("\nTesting system prompt generation...")

    playbook = {
        "roles": {
            "Researcher": {
                "description": "Conducts thorough domain research and synthesizes findings",
            }
        },
        "failure_modes": [
            {
                "id": "FM-001",
                "symptom": "Insufficient depth in research",
                "root_cause": "Rushing through sources",
                "fix": "Take time to go deep",
                "prevention": "Set minimum source count",
                "phase": "Phase 1",
                "severity": "error",
                "source": "experience"
            }
        ]
    }

    phase = {
        "title": "Phase 1: Research",
        "purpose": "Gather information",
        "compilation": {
            "role_mindset": "Researcher — investigating domain knowledge",
            "objective": "Gather comprehensive information about the problem domain",
            "failure_modes_relevant": ["FM-001"],
            "pre_check": [
                "Research scope is defined",
                "Key questions are identified"
            ],
            "context_load": ["brief.md", "scope.md"]
        }
    }

    # Mock context files
    loaded_files = {
        "brief.md": "# Project Brief\n\nCreate a domain-specific playbook...",
        "scope.md": "## In Scope\n- Research\n- Architecture\n\n## Out of Scope\n- Implementation"
    }

    prompt = generate_system_prompt(
        playbook=playbook,
        phase=phase,
        loaded_files=loaded_files,
        flags={
            "role_definition": True,
            "phase_objective": True,
            "failure_modes": True,
            "pre_check_guidance": True,
            "context_files": True,
            "handoff_requirements": False
        }
    )

    # Verify prompt structure
    assert "Researcher" in prompt, "Should include role name"
    assert "investigating domain knowledge" in prompt, "Should include role mindset"
    assert "Gather comprehensive" in prompt, "Should include objective"
    assert "FM-001" in prompt, "Should include failure mode reference"
    assert "Research scope is defined" in prompt, "Should include pre-check"
    assert "brief.md" in prompt, "Should include context file name"
    assert "scope.md" in prompt, "Should include context file name"

    print("PASS: test_system_prompt_generation")


def test_context_budget_with_priority():
    """Test context loading with priority-based budget allocation."""
    print("\nTesting context budget with priority...")

    files = {
        "critical.md": "a" * 1000,      # ~250 tokens, priority 1
        "important.md": "b" * 2000,      # ~500 tokens, priority 3
        "optional.md": "c" * 10000,       # ~2500 tokens, priority 8
        "extra.md": "d" * 5000,           # ~1250 tokens, priority 7
    }

    priority = {
        "critical.md": 1,
        "important.md": 3,
        "optional.md": 8,
        "extra.md": 7
    }

    # Budget enough for critical + important + system_prompt + response
    # System prompt budget: 2000, response budget: 4096
    # Available for files: 20000 - 2000 - 4096 = 13904
    result = load_context_with_budget(
        files=files,
        priority=priority,
        max_tokens=20000,
        critical_threshold=3  # Files at priority 1-3 cannot be skipped
    )

    assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"
    assert "critical.md" in result.loaded_files, "Critical file must be loaded"
    assert "important.md" in result.loaded_files, "Important file must be loaded (priority <= threshold)"
    # Optional and extra should be skipped due to budget or priority
    assert len(result.loaded_files) >= 2, "At least critical and important must be loaded"

    print("PASS: test_context_budget_with_priority")


def test_context_budget_critical_protection():
    """Test that critical files cannot be skipped even if they exceed budget."""
    print("\nTesting critical file protection...")

    files = {
        "essential.md": "a" * 50000,  # ~12500 tokens, priority 1 (critical)
    }

    # Budget too small
    result = load_context_with_budget(
        files=files,
        priority={"essential.md": 1},
        max_tokens=5000,  # Too small
        critical_threshold=3
    )

    # Should error because critical file can't fit
    assert len(result.errors) > 0, "Should error when critical file can't fit"
    assert "Insufficient budget" in result.errors[0], f"Expected budget error, got: {result.errors[0]}"

    print("PASS: test_context_budget_critical_protection")


def test_model_fallback_chain():
    """Test model fallback when primary is unavailable."""
    print("\nTesting model fallback chain...")

    playbook = {
        "defaults": {
            "model": "opus",
            "model_fallbacks": {
                "opus": ["sonnet", "haiku"],
                "sonnet": ["haiku"]
            }
        },
        "roles": {}
    }

    # Test when opus (playbook default) is not available
    # Since no role model, should try playbook default "opus" first,
    # then fall back through its chain ["sonnet", "haiku"]
    config = get_agent_config(
        {"role_mindset": "Coordinator"},
        playbook,
        "Coordinator",
        available_models=["sonnet", "haiku"]  # opus not available
    )

    # Primary is opus (from playbook defaults), fallback chain is ["sonnet", "haiku"]
    # Since opus not available, we pick sonnet (first available in chain)
    assert config["model"] == "sonnet", f"Expected fallback to sonnet, got {config['model']}"
    # The fallback chain returned is [primary, ...fallbacks] = ["opus", "sonnet", "haiku"]
    assert config["model_fallback_chain"] == ["opus", "sonnet", "haiku"], \
        f"Expected full fallback chain, got {config['model_fallback_chain']}"

    # Test when no models are available
    try:
        get_agent_config(
            {"role_mindset": "Coordinator"},
            playbook,
            "Coordinator",
            available_models=[]
        )
        assert False, "Should raise RuntimeError"
    except RuntimeError as e:
        assert "No available model" in str(e)

    print("PASS: test_model_fallback_chain")


def test_role_defaults_override():
    """Test that role defaults override playbook defaults."""
    print("\nTesting role defaults override...")

    playbook = {
        "defaults": {
            "model": "opus",
            "temperature": 0.3,
        },
        "roles": {
            "Researcher": {
                "description": "Research role",
                "defaults": {
                    "model": "sonnet",
                    "temperature": [0.5, 0.8],
                }
            }
        }
    }

    # No phase-level overrides
    config = get_agent_config(
        {"role_mindset": "Researcher"},
        playbook,
        "Researcher",
        available_models=["opus", "sonnet", "haiku"]
    )

    assert config["model"] == "sonnet", f"Expected role default model, got {config['model']}"
    assert config["temperature"] == 0.65, f"Expected midpoint of [0.5, 0.8], got {config['temperature']}"

    print("PASS: test_role_defaults_override")


def test_string_role_backward_compatibility():
    """Test backward compatibility with string-style role definitions."""
    print("\nTesting string role backward compatibility...")

    playbook = {
        "roles": {
            "Coordinator": "Phase gates and tracking"  # String, not object
        },
        "defaults": {
            "model": "sonnet",
            "temperature": 0.3
        }
    }

    config = get_agent_config(
        {"role_mindset": "Coordinator"},
        playbook,
        "Coordinator",
        available_models=["sonnet"]
    )

    # Should use playbook defaults
    assert config["model"] == "sonnet"
    assert config["temperature"] == 0.3

    print("PASS: test_string_role_backward_compatibility")


def test_validation_catches_new_errors():
    """Test that validation script catches new field errors."""
    print("\nTesting validation catches new errors...")

    # Import validation function
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validate_playbook import validate

    # Create a minimal invalid playbook
    invalid_playbook = {
        "title": "Test",
        "version": 1,
        "description": "Test",
        "workflow_model": "role-based-single-agent",
        "roles": {"Test": "Test role"},
        "scope": {"in_scope": [], "out_of_scope": [], "adjacent": []},
        "cross_cutting_concerns": ["test"],
        "knowledge_base": {"complexity": "flat", "directory_structure": "test/"},
        "checklists": [{
            "title": "Phase 0",
            "purpose": "Test",
            "compilation": {
                "context_load": ["test.md"],
                "role_mindset": "Test",
                "objective": "Test"
            },
            "items": [{
                "title": "[Test] Test",
                "owner": "[Test]",
                "gate_conditions": ["test"],
                "blocker_examples": ["test"],
                "handoff": {
                    "output_artifacts": ["test.md"],
                    "next_phase_context": ["test.md"]
                }
            }]
        }],
        "metrics": [],
        "usage_instructions": {
            "how_to_run": [],
            "session_strategy": [],
            "cost_optimization": [],
            "post_run_review": {"assess": []}
        },
        "failure_modes": [],
        "phase_kb_mapping": {"Phase 0": []},
        "skill_activation": {"Phase 0": "none"},
        "router": {"description": "", "decision_tree": [], "default": ""},
        "context_preservation": {
            "decisions_ledger": "",
            "artifact_manifest": "",
            "rules": []
        },
        # Invalid defaults
        "defaults": {
            "temperature": 3.0,  # Invalid: > 2
            "max_tokens": 100,   # Invalid: < 256
            "critical_priority_threshold": 15  # Invalid: > 10
        }
    }

    # Write to temp file and validate
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_playbook, f)
        temp_path = f.name

    try:
        errors, warnings = validate(temp_path)
        assert len(errors) > 0, "Should catch validation errors"

        # Check for specific errors
        error_str = " ".join(errors)
        assert "temperature" in error_str, "Should catch invalid temperature"
        assert "max_tokens" in error_str, "Should catch invalid max_tokens"
        assert "critical_priority_threshold" in error_str, "Should catch invalid threshold"

        print("PASS: test_validation_catches_new_errors")
    finally:
        Path(temp_path).unlink()


def test_compilation_new_fields_validation():
    """Test validation of success_criteria, tools_available, behavioral_profile."""
    print("\nTesting compilation new fields validation...")

    import tempfile
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validate_playbook import validate

    def make_playbook(compilation_extra):
        """Helper to create a minimal playbook with custom compilation fields."""
        comp = {
            "context_load": ["test.md"],
            "role_mindset": "Test",
            "objective": "Test",
            "pre_check": [],
            "failure_modes_relevant": []
        }
        comp.update(compilation_extra)
        return {
            "title": "Test", "version": 3, "description": "Test",
            "workflow_model": "role-based-single-agent",
            "roles": {"Test": {"description": "Test role"}},
            "scope": {"in_scope": [], "out_of_scope": [], "adjacent": []},
            "cross_cutting_concerns": [
                {"id": "CCC-01", "title": "T", "description": "D",
                 "enforcement_method": "gate_condition", "minimum_phases": 1,
                 "phases_applied": [0]}
            ],
            "knowledge_base": {"complexity": "flat", "directory_structure": "test/"},
            "checklists": [{
                "title": "Phase 0", "purpose": "Test",
                "compilation": comp,
                "items": [{
                    "title": "[Test] — Test task", "owner": "[Test]",
                    "gate_conditions": ["condition 1"],
                    "blocker_examples": ["blocker"],
                    "handoff": {
                        "output_artifacts": ["test.md"],
                        "next_phase_context": ["test.md"]
                    }
                }]
            }],
            "metrics": [
                {"id": "MET-01", "title": "T", "description": "D",
                 "type": "metric_integer", "category": "process",
                 "measurement_method": "count"}
            ],
            "usage_instructions": {
                "how_to_run": [], "session_strategy": [],
                "cost_optimization": [],
                "post_run_review": {"assess": []}
            },
            "failure_modes": [],
            "phase_kb_mapping": {"phase_0": []},
            "skill_activation": {"phase_0": "none"},
            "router": {"description": "", "decision_tree": [], "default": ""},
            "context_preservation": {
                "decisions_ledger": "", "artifact_manifest": "", "rules": []
            }
        }

    def validate_playbook(pb):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pb, f)
            temp_path = f.name
        try:
            errors, warnings = validate(temp_path)
            return errors, warnings
        finally:
            Path(temp_path).unlink()

    # Test 1: Valid success_criteria passes
    pb = make_playbook({"success_criteria": ["JSON valid", "Fields present"]})
    errors, warnings = validate_playbook(pb)
    assert not any("success_criteria" in e for e in errors), \
        f"Valid success_criteria should pass: {errors}"

    # Test 2: Empty success_criteria fails
    pb = make_playbook({"success_criteria": []})
    errors, warnings = validate_playbook(pb)
    assert any("success_criteria must not be empty" in e for e in errors), \
        f"Empty success_criteria should fail: {errors}"

    # Test 3: Non-string success_criteria fails
    pb = make_playbook({"success_criteria": [123, "valid"]})
    errors, warnings = validate_playbook(pb)
    assert any("success_criteria must contain strings" in e for e in errors), \
        f"Non-string success_criteria should fail: {errors}"

    # Test 4: Valid tools_available passes
    pb = make_playbook({"tools_available": ["web_search", "file_reading"]})
    errors, warnings = validate_playbook(pb)
    assert not any("tools_available" in e for e in errors), \
        f"Valid tools_available should pass: {errors}"

    # Test 5: Empty tools_available fails
    pb = make_playbook({"tools_available": []})
    errors, warnings = validate_playbook(pb)
    assert any("tools_available must not be empty" in e for e in errors), \
        f"Empty tools_available should fail: {errors}"

    # Test 6: Valid behavioral_profile passes
    pb = make_playbook({
        "behavioral_profile": {
            "risk_tolerance": "minimal",
            "creativity_level": "strict",
            "verbosity": "concise",
            "stance": "adversarial"
        }
    })
    errors, warnings = validate_playbook(pb)
    assert not any("behavioral_profile" in e for e in errors), \
        f"Valid behavioral_profile should pass: {errors}"

    # Test 7: Invalid behavioral_profile value fails
    pb = make_playbook({
        "behavioral_profile": {"risk_tolerance": "yolo"}
    })
    errors, warnings = validate_playbook(pb)
    assert any("risk_tolerance" in e and "yolo" in e for e in errors), \
        f"Invalid risk_tolerance should fail: {errors}"

    # Test 8: Invalid stance fails
    pb = make_playbook({
        "behavioral_profile": {"stance": "passive-aggressive"}
    })
    errors, warnings = validate_playbook(pb)
    assert any("stance" in e for e in errors), \
        f"Invalid stance should fail: {errors}"

    # Test 9: No new fields still passes (backward compat)
    pb = make_playbook({})
    errors, warnings = validate_playbook(pb)
    assert not any("success_criteria" in e or "tools_available" in e or "behavioral_profile" in e
                   for e in errors), \
        f"Missing optional fields should not fail: {errors}"

    print("PASS: test_compilation_new_fields_validation")


def test_success_criteria_gate_alignment_warning():
    """Test that mismatched success_criteria and gate_conditions produce a warning."""
    print("\nTesting success_criteria/gate_conditions alignment...")

    import tempfile
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validate_playbook import validate

    pb = {
        "title": "Test", "version": 3, "description": "Test",
        "workflow_model": "role-based-single-agent",
        "roles": {"Test": {"description": "Test role"}},
        "scope": {"in_scope": [], "out_of_scope": [], "adjacent": []},
        "cross_cutting_concerns": [
            {"id": "CCC-01", "title": "T", "description": "D",
             "enforcement_method": "gate_condition", "minimum_phases": 1,
             "phases_applied": [0]}
        ],
        "knowledge_base": {"complexity": "flat", "directory_structure": "test/"},
        "checklists": [{
            "title": "Phase 0", "purpose": "Test",
            "compilation": {
                "context_load": ["test.md"],
                "role_mindset": "Test",
                "objective": "Test",
                "pre_check": [],
                "failure_modes_relevant": [],
                "success_criteria": ["one criterion"]
            },
            "items": [{
                "title": "[Test] — Gate", "owner": "[Test]",
                "gate_conditions": ["cond1", "cond2", "cond3", "cond4",
                                    "cond5", "cond6", "cond7", "cond8",
                                    "cond9", "cond10"],
                "blocker_examples": ["b"],
                "handoff": {
                    "output_artifacts": ["test.md"],
                    "next_phase_context": ["test.md"]
                }
            }]
        }],
        "metrics": [
            {"id": "MET-01", "title": "T", "description": "D",
             "type": "metric_integer", "category": "process",
             "measurement_method": "count"}
        ],
        "usage_instructions": {
            "how_to_run": [], "session_strategy": [],
            "cost_optimization": [],
            "post_run_review": {"assess": []}
        },
        "failure_modes": [],
        "phase_kb_mapping": {"phase_0": []},
        "skill_activation": {"phase_0": "none"},
        "router": {"description": "", "decision_tree": [], "default": ""},
        "context_preservation": {
            "decisions_ledger": "", "artifact_manifest": "", "rules": []
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(pb, f)
        temp_path = f.name

    try:
        errors, warnings = validate(temp_path)
        assert any("success_criteria" in w and "differs significantly" in w for w in warnings), \
            f"Should warn about mismatched criteria: {warnings}"
    finally:
        Path(temp_path).unlink()

    print("PASS: test_success_criteria_gate_alignment_warning")


if __name__ == "__main__":
    test_end_to_end_config_resolution()
    test_system_prompt_generation()
    test_context_budget_with_priority()
    test_context_budget_critical_protection()
    test_model_fallback_chain()
    test_role_defaults_override()
    test_string_role_backward_compatibility()
    test_validation_catches_new_errors()
    test_compilation_new_fields_validation()
    test_success_criteria_gate_alignment_warning()

    print("\n" + "="*50)
    print("All integration tests passed!")
    print("="*50)