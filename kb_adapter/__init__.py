"""
KB Adapter Interface — PBCPB Unified

Provides AdapterSession.bind(config_path) as the single construction path.
Business logic holds AdapterSession, never a concrete adapter reference.

Supported adapter_type values (exact strings only):
    RAG_MCP          — Dify RAG accessed via MCP server
    MARKDOWN_FOLDER  — User-provided skill handles all 3 methods
    JSON_DB          — pbcpb original JSON-based knowledge base
    CUSTOM_API       — Configurable HTTP passthrough
"""

from .session import AdapterSession
from .errors import ConfigError, AdapterIOError
from .enums import AdapterType

__all__ = ["AdapterSession", "ConfigError", "AdapterIOError", "AdapterType"]
