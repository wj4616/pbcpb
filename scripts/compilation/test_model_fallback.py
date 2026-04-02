"""Tests for model_fallback module."""

import sys
from pathlib import Path

# Add scripts to path for compilation module
sys.path.insert(0, str(Path(__file__).parent.parent))

from compilation.model_fallback import (
    resolve_model,
    resolve_temperature,
    resolve_max_tokens,
    get_agent_config,
)
from compilation.constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS


def test_model_resolution_phase():
    """Test phase-level model takes priority."""
    playbook_defaults = {"model": "sonnet"}
    role_defaults = {"model": "haiku"}

    model, chain = resolve_model(
        "opus", playbook_defaults, role_defaults, ["opus", "sonnet", "haiku"]
    )

    assert model == "opus"
    print("PASS: test_model_resolution_phase")


def test_model_resolution_role():
    """Test role-level model when phase not specified."""
    playbook_defaults = {"model": "sonnet"}
    role_defaults = {"model": "haiku"}

    model, chain = resolve_model(
        None, playbook_defaults, role_defaults, ["opus", "sonnet", "haiku"]
    )

    assert model == "haiku"
    print("PASS: test_model_resolution_role")


def test_model_resolution_playbook():
    """Test playbook-level model when others not specified."""
    playbook_defaults = {"model": "sonnet"}

    model, chain = resolve_model(
        None, playbook_defaults, None, ["opus", "sonnet", "haiku"]
    )

    assert model == "sonnet"
    print("PASS: test_model_resolution_playbook")


def test_model_fallback():
    """Test fallback when model unavailable."""
    playbook_defaults = {
        "model": "opus",
        "model_fallbacks": {"opus": ["sonnet", "haiku"]},
    }

    model, chain = resolve_model(
        None, playbook_defaults, None, ["sonnet", "haiku"]  # opus not available
    )

    assert model == "sonnet", f"Expected sonnet, got {model}"
    assert "opus" in chain, "Fallback chain should include opus"
    print("PASS: test_model_fallback")


def test_all_models_unavailable():
    """Test error when no models are available."""
    try:
        resolve_model(
            None, None, None, []  # No models available
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "No available model" in str(e)
        print("PASS: test_all_models_unavailable")


def test_temperature_resolution():
    """Test temperature resolution."""
    # Phase specified
    assert resolve_temperature(0.5, None, None) == 0.5

    # Role range midpoint
    assert resolve_temperature(None, {"temperature": [0.2, 0.6]}, None) == 0.4

    # Playbook default
    assert resolve_temperature(None, None, {"temperature": 0.3}) == 0.3

    # Hardcoded default
    assert resolve_temperature(None, None, None) == DEFAULT_TEMPERATURE

    print("PASS: test_temperature_resolution")


def test_max_tokens_resolution():
    """Test max_tokens resolution."""
    assert resolve_max_tokens(8000, None) == 8000
    assert resolve_max_tokens(None, {"max_tokens": 4096}) == 4096
    assert resolve_max_tokens(None, None) == DEFAULT_MAX_TOKENS
    print("PASS: test_max_tokens_resolution")


def test_get_agent_config():
    """Test full agent config resolution."""
    playbook = {
        "defaults": {
            "model": "opus",
            "temperature": 0.3,
            "max_tokens": 4096,
            "context_budget_tokens": 64000,
        },
        "roles": {
            "Researcher": {
                "description": "Domain research",
                "defaults": {
                    "model": "sonnet",
                    "temperature": [0.4, 0.7],
                },
            }
        },
    }

    phase_compilation = {
        "role_mindset": "Researcher — gather information",
        "agent_config": {
            "temperature": 0.5,  # Phase override
        },
    }

    config = get_agent_config(phase_compilation, playbook, "Researcher — gather information")

    # Model from role default (sonnet)
    assert config["model"] == "sonnet", f"Expected sonnet, got {config['model']}"
    # Temperature from phase override
    assert config["temperature"] == 0.5, f"Expected 0.5, got {config['temperature']}"
    # Max tokens from playbook default
    assert config["max_tokens"] == 4096, f"Expected 4096, got {config['max_tokens']}"
    # Context budget from playbook default
    assert config["context_budget_tokens"] == 64000, f"Expected 64000, got {config['context_budget_tokens']}"
    # Fallback chain should be present
    assert "model_fallback_chain" in config

    print("PASS: test_get_agent_config")


def test_get_agent_config_string_role():
    """Test agent config with string-style role definition."""
    playbook = {
        "roles": {
            "Coordinator": "Phase gates and tracking"  # String, not object
        }
    }

    phase_compilation = {
        "role_mindset": "Coordinator"
    }

    config = get_agent_config(phase_compilation, playbook, "Coordinator")

    # Should use defaults
    assert config["model"] == DEFAULT_MODEL
    assert config["temperature"] == DEFAULT_TEMPERATURE

    print("PASS: test_get_agent_config_string_role")


def test_fallback_chain_in_result():
    """Test that fallback chain is returned in agent config."""
    playbook = {
        "defaults": {
            "model": "opus",
            "model_fallbacks": {"opus": ["sonnet", "haiku"]}
        }
    }

    config = get_agent_config(
        {"role_mindset": "Coordinator"},
        playbook,
        "Coordinator",
        ["opus", "sonnet", "haiku"]
    )

    assert "model_fallback_chain" in config, "Should include fallback chain"
    assert config["model_fallback_chain"] == ["opus", "sonnet", "haiku"], \
        f"Expected ['opus', 'sonnet', 'haiku'], got {config['model_fallback_chain']}"

    print("PASS: test_fallback_chain_in_result")


if __name__ == "__main__":
    test_model_resolution_phase()
    test_model_resolution_role()
    test_model_resolution_playbook()
    test_model_fallback()
    test_all_models_unavailable()
    test_temperature_resolution()
    test_max_tokens_resolution()
    test_get_agent_config()
    test_get_agent_config_string_role()
    test_fallback_chain_in_result()
    print("\nAll tests passed!")