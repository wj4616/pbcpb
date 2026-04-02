"""
Model fallback resolver for unavailable models.

Implements fallback chain resolution:
1. Try specified model
2. If unavailable, try first fallback
3. Continue until available model found
4. Log fallback decisions
"""

from typing import Any

from .constants import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_CONTEXT_BUDGET_TOKENS,
    DEFAULT_SYSTEM_PROMPT_BUDGET,
    DEFAULT_CRITICAL_THRESHOLD,
    AVAILABLE_MODELS,
    DEFAULT_MODEL_FALLBACKS,
)


def resolve_model(
    specified_model: str | None,
    playbook_defaults: dict[str, Any] | None,
    role_defaults: dict[str, Any] | None,
    available_models: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    Resolve model with fallback chain.

    Priority (highest to lowest):
    1. Phase agent_config.model
    2. Role defaults.model
    3. Playbook defaults.model
    4. Hardcoded default

    Args:
        specified_model: Model specified at phase level (or None)
        playbook_defaults: Playbook defaults dict (or None)
        role_defaults: Role defaults dict (or None)
        available_models: List of available model names (or None for default)

    Returns:
        Tuple of (resolved_model, fallback_chain_used)

    Raises:
        RuntimeError: If no model is available
    """
    # Use default available models if not provided
    if available_models is None:
        available_models = AVAILABLE_MODELS

    # Build priority chain
    if specified_model:
        primary = specified_model
        fallback_chain = _get_fallback_chain(primary, playbook_defaults)
    elif role_defaults and "model" in role_defaults:
        primary = role_defaults["model"]
        fallback_chain = _get_fallback_chain(primary, playbook_defaults)
    elif playbook_defaults and "model" in playbook_defaults:
        primary = playbook_defaults["model"]
        fallback_chain = _get_fallback_chain(primary, playbook_defaults)
    else:
        primary = DEFAULT_MODEL
        fallback_chain = DEFAULT_MODEL_FALLBACKS.get(DEFAULT_MODEL, [])

    # Find first available model
    all_models = [primary] + fallback_chain
    for model in all_models:
        if model in available_models:
            return model, all_models

    # No model available
    raise RuntimeError(
        f"No available model found. Tried: {all_models}. Available: {available_models}"
    )


def _get_fallback_chain(model: str, playbook_defaults: dict[str, Any] | None) -> list[str]:
    """Get fallback chain for a model from playbook defaults."""
    if not playbook_defaults:
        return DEFAULT_MODEL_FALLBACKS.get(model, [])

    fallbacks = playbook_defaults.get("model_fallbacks", {})
    if model in fallbacks:
        return fallbacks[model]
    return DEFAULT_MODEL_FALLBACKS.get(model, [])


def resolve_temperature(
    specified_temperature: float | None,
    role_defaults: dict[str, Any] | None,
    playbook_defaults: dict[str, Any] | None,
) -> float:
    """
    Resolve temperature with defaults.

    Priority:
    1. Phase agent_config.temperature
    2. Midpoint of role defaults.temperature range
    3. Playbook defaults.temperature
    4. Hardcoded default

    Args:
        specified_temperature: Temperature specified at phase level
        role_defaults: Role defaults dict (may have temperature range)
        playbook_defaults: Playbook defaults dict

    Returns:
        Resolved temperature value
    """
    if specified_temperature is not None:
        return specified_temperature

    # Check role temperature range
    if role_defaults and "temperature" in role_defaults:
        temp_range = role_defaults["temperature"]
        if isinstance(temp_range, list) and len(temp_range) == 2:
            return (temp_range[0] + temp_range[1]) / 2

    # Check playbook default
    if playbook_defaults and "temperature" in playbook_defaults:
        return playbook_defaults["temperature"]

    return DEFAULT_TEMPERATURE


def resolve_max_tokens(
    specified_tokens: int | None,
    playbook_defaults: dict[str, Any] | None,
) -> int:
    """
    Resolve max_tokens with defaults.

    Priority:
    1. Phase agent_config.max_tokens
    2. Playbook defaults.max_tokens
    3. Hardcoded default

    Args:
        specified_tokens: Max tokens specified at phase level
        playbook_defaults: Playbook defaults dict

    Returns:
        Resolved max_tokens value
    """
    if specified_tokens is not None:
        return specified_tokens

    if playbook_defaults and "max_tokens" in playbook_defaults:
        return playbook_defaults["max_tokens"]

    return DEFAULT_MAX_TOKENS


def get_agent_config(
    phase_compilation: dict[str, Any],
    playbook: dict[str, Any],
    role_mindset: str,
    available_models: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get fully resolved agent configuration for a phase.

    Args:
        phase_compilation: Phase compilation block
        playbook: Full playbook JSON
        role_mindset: Role name from compilation block
        available_models: List of available model names (or None for default)

    Returns:
        Dict with resolved model, temperature, max_tokens, and budget
    """
    # Extract role name
    if " — " in role_mindset:
        role_name = role_mindset.split(" — ")[0].strip()
    else:
        role_name = role_mindset.strip()

    # Get defaults
    playbook_defaults = playbook.get("defaults", {})
    roles = playbook.get("roles", {})
    role_def = roles.get(role_name, "")

    # Handle both string and object role definitions
    # FIX: Extract nested "defaults" from role object
    if isinstance(role_def, dict):
        role_defaults = role_def.get("defaults", {})
    else:
        role_defaults = {}

    # Get phase config
    agent_config = phase_compilation.get("agent_config", {})
    context_budget = phase_compilation.get("context_budget", {})

    # Resolve values
    model, fallback_chain = resolve_model(
        agent_config.get("model"),
        playbook_defaults,
        role_defaults,
        available_models,
    )

    temperature = resolve_temperature(
        agent_config.get("temperature"),
        role_defaults,
        playbook_defaults,
    )

    max_tokens = resolve_max_tokens(
        agent_config.get("max_tokens"),
        playbook_defaults,
    )

    # Resolve context budget
    context_budget_tokens = context_budget.get("max_tokens")
    if context_budget_tokens is None:
        context_budget_tokens = playbook_defaults.get("context_budget_tokens", DEFAULT_CONTEXT_BUDGET_TOKENS)

    # Resolve other defaults
    critical_threshold = playbook_defaults.get("critical_priority_threshold", DEFAULT_CRITICAL_THRESHOLD)
    system_prompt_budget = playbook_defaults.get("system_prompt_budget", DEFAULT_SYSTEM_PROMPT_BUDGET)

    return {
        "model": model,
        "model_fallback_chain": fallback_chain,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "context_budget_tokens": context_budget_tokens,
        "critical_threshold": critical_threshold,
        "system_prompt_budget": system_prompt_budget,
    }