"""
Compilation block utilities for playbook execution.

Provides:
- System prompt generation from role, objective, and flags
- Context budget loading with priority-based file selection
- Model fallback resolution for unavailable models
"""

from .constants import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_CONTEXT_BUDGET_TOKENS,
    DEFAULT_SYSTEM_PROMPT_BUDGET,
    DEFAULT_CRITICAL_THRESHOLD,
    AVAILABLE_MODELS,
    DEFAULT_MODEL_FALLBACKS,
    CHARS_PER_TOKEN,
    MIN_PRIORITY,
    MAX_PRIORITY,
    DEFAULT_PRIORITY,
    DEFAULT_FILE_TOKENS_ESTIMATE,
    COMPLEXITY_LIMITS,
    COMPLEXITY_VARIANCE_THRESHOLD,
)
from .system_prompt import generate_system_prompt, estimate_prompt_tokens
from .context_budget import (
    load_context_with_budget,
    estimate_file_tokens,
    estimate_context_tokens,
    estimate_critical_tokens,
)
from .model_fallback import resolve_model, resolve_temperature, resolve_max_tokens, get_agent_config

__all__ = [
    # Constants
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_CONTEXT_BUDGET_TOKENS",
    "DEFAULT_SYSTEM_PROMPT_BUDGET",
    "DEFAULT_CRITICAL_THRESHOLD",
    "AVAILABLE_MODELS",
    "DEFAULT_MODEL_FALLBACKS",
    "CHARS_PER_TOKEN",
    "MIN_PRIORITY",
    "MAX_PRIORITY",
    "DEFAULT_PRIORITY",
    "DEFAULT_FILE_TOKENS_ESTIMATE",
    "COMPLEXITY_LIMITS",
    "COMPLEXITY_VARIANCE_THRESHOLD",
    # Functions (system_prompt)
    "generate_system_prompt",
    "estimate_prompt_tokens",
    # Functions (context_budget)
    "load_context_with_budget",
    "estimate_file_tokens",
    "estimate_context_tokens",
    "estimate_critical_tokens",
    # Functions (model_fallback)
    "resolve_model",
    "resolve_temperature",
    "resolve_max_tokens",
    "get_agent_config",
]