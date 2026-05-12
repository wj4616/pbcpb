"""
Error types for the KB Adapter system.

Error shape for all failures:
    {
        "error_class": str,       # "ConfigError" | "AdapterIOError"
        "cause": str,             # Human-readable description
        "adapter_type": str|None, # Which adapter raised (None if pre-adapter)
        "recoverable": bool       # False = halt; True = retry possible
    }

Rules:
    ConfigError    — raised at bind() time; recoverable: false; halts immediately
    AdapterIOError — raised during query/populate/scan_gaps; recoverable: true;
                     default 60s timeout applies
    Silent degradation (empty response, hang, swallowed exception) MUST NOT occur.
"""


class ConfigError(Exception):
    """
    Raised when configuration is invalid at bind() time.

    Always recoverable: False — fix config, re-bind.

    Attributes:
        offending_field: The exact config field that failed validation.
        adapter_type: The adapter_type value at time of failure (or None).
        detail: Full structured error dict.
    """

    def __init__(self, cause: str, offending_field: str = None, adapter_type: str = None):
        super().__init__(cause)
        self.offending_field = offending_field
        self.adapter_type = adapter_type
        self.detail = {
            "error_class": "ConfigError",
            "cause": cause,
            "offending_field": offending_field,
            "adapter_type": adapter_type,
            "recoverable": False,
        }

    def __str__(self):
        if self.offending_field:
            return f"ConfigError: {self.args[0]} (field: {self.offending_field})"
        return f"ConfigError: {self.args[0]}"


class AdapterIOError(Exception):
    """
    Raised during query(), populate(), or scan_gaps() calls.

    Always recoverable: True — caller may retry or degrade gracefully.

    Attributes:
        adapter_type: Which adapter raised this.
        detail: Full structured error dict.
    """

    def __init__(self, cause: str, adapter_type: str = None):
        super().__init__(cause)
        self.adapter_type = adapter_type
        self.detail = {
            "error_class": "AdapterIOError",
            "cause": cause,
            "adapter_type": adapter_type,
            "recoverable": True,
        }

    def __str__(self):
        return f"AdapterIOError [{self.adapter_type or 'unknown'}]: {self.args[0]}"
