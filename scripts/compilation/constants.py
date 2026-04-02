"""
Constants for compilation block enhancement.

All default values are defined here to avoid hardcoding throughout the codebase.
"""

# Default model configuration
DEFAULT_MODEL = "opus"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4096

# Default context budget
DEFAULT_CONTEXT_BUDGET_TOKENS = 64000
DEFAULT_SYSTEM_PROMPT_BUDGET = 2000
DEFAULT_CRITICAL_THRESHOLD = 3

# Available models (can be extended by platform)
AVAILABLE_MODELS = ["opus", "sonnet", "haiku"]

# Default fallback chains
DEFAULT_MODEL_FALLBACKS = {
    "opus": ["sonnet", "haiku"],
    "sonnet": ["haiku"],
    "haiku": [],
}

# Token estimation constant
CHARS_PER_TOKEN = 4  # Rough heuristic

# Priority range
MIN_PRIORITY = 1
MAX_PRIORITY = 10
DEFAULT_PRIORITY = 5

# Context budget estimation
DEFAULT_FILE_TOKENS_ESTIMATE = 2000  # Heuristic for unknown file sizes

# Complexity classification thresholds
COMPLEXITY_LIMITS = {
    "simple": {"phases": 8, "roles": 3, "cccs": 4},
    "moderate": {"phases": 12, "roles": 4, "cccs": 6},
    "complex": {"phases": 15, "roles": 5, "cccs": 8},
    "structured": {"phases": 20, "roles": 7, "cccs": 12},
}
COMPLEXITY_VARIANCE_THRESHOLD = 0.20  # 20% allowed variance