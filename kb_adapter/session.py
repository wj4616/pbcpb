"""
AdapterSession — single construction path for KB adapters.

Usage:
    session = AdapterSession.bind("pbcpb.config.json")
    results = session.query("my question")
    result  = session.populate(content, tier=1, metadata={...})
    gaps    = session.scan_gaps(schema_definition)

Config path override:
    Set PBCPB_CONFIG_PATH environment variable to override default config path.

Architecture patterns this follows:
    POSIX file-descriptor pattern — AdapterSession is the fd; once bound,
        all ops go through it (no direct adapter access after bind).
    JDBC connection-string selection — adapter_type in config selects backend,
        like a JDBC URL selects the driver; no code-level branching.
    TLS handshake pattern — bind() validates+negotiates upfront; if bind fails,
        no session exists (ConfigError raised before handle returned).
    Spring-DI dependency injection — business logic holds AdapterSession
        (interface), never the concrete adapter (implementation).

CALLER_INVARIANCE: business logic imports AdapterSession only.
    Concrete adapters are an internal implementation detail.
STATELESS_INTERFACE: no session state in query/populate/scan_gaps signatures.
"""

import json
import os
from pathlib import Path

from langfuse import observe, get_client

from .enums import VALID_ADAPTER_TYPES
from .errors import ConfigError, AdapterIOError
from .interface import BaseAdapter

# Sentinel enforcing AdapterSession.bind() as the only construction path.
# Callers cannot construct or guess this object, so direct __init__ calls fail.
_BIND_SENTINEL = object()


class AdapterSession:
    """
    Bound KB adapter session. Exposes only query/populate/scan_gaps.

    Construction: AdapterSession.bind(config_path) → AdapterSession
    Direct instantiation raises TypeError — bind() is the only path.

    Attributes (read-only after bind):
        adapter_type: The bound adapter_type string
    """

    def __init__(self, adapter: BaseAdapter, _sentinel=None):
        """
        Internal constructor. Use AdapterSession.bind() instead.

        Args:
            adapter: Concrete adapter instance (bound at bind-time)
            _sentinel: Must be _BIND_SENTINEL — enforces bind()-only construction
        """
        if _sentinel is not _BIND_SENTINEL:
            raise TypeError(
                "AdapterSession cannot be instantiated directly. "
                "Use AdapterSession.bind(config_path) instead."
            )
        self._adapter = adapter

    @property
    def adapter_type(self) -> str:
        return self._adapter.adapter_type

    @classmethod
    def bind(cls, config_path: str = None) -> "AdapterSession":
        """
        Load config, validate, instantiate concrete adapter, return session.

        Only construction path. Validates:
            - Config file exists and is valid JSON
            - kb_adapter.adapter_type is an exact-string enum value
            - Required adapter-specific connection fields are present
            - skill_ref present for MARKDOWN_FOLDER
            - Role system config (if present) uses exact-string role_type values

        Args:
            config_path: Path to pbcpb.config.json
                         Overridden by PBCPB_CONFIG_PATH env var.

        Returns:
            AdapterSession with bound concrete adapter

        Raises:
            ConfigError: Any validation failure — recoverable: False
        """
        # Resolve config path (env var overrides argument)
        env_path = os.environ.get("PBCPB_CONFIG_PATH")
        resolved_path = Path(env_path or config_path or "pbcpb.config.json")

        if not resolved_path.exists():
            raise ConfigError(
                f"Config file not found: '{resolved_path}'. "
                "Create pbcpb.config.json or set PBCPB_CONFIG_PATH.",
                offending_field="config_path",
                adapter_type=None,
            )

        # Parse config
        try:
            config = json.loads(resolved_path.read_text())
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Config file '{resolved_path}' is not valid JSON: {e}",
                offending_field="config_path",
                adapter_type=None,
            )

        # Validate kb_adapter section
        kb_adapter_config = config.get("kb_adapter")
        if not kb_adapter_config:
            raise ConfigError(
                "Config missing required 'kb_adapter' section",
                offending_field="kb_adapter",
                adapter_type=None,
            )

        adapter_type = kb_adapter_config.get("adapter_type")
        if adapter_type not in VALID_ADAPTER_TYPES:
            raise ConfigError(
                f"'kb_adapter.adapter_type' value '{adapter_type}' is not valid. "
                f"Must be one of: {sorted(VALID_ADAPTER_TYPES)} (exact strings, case-sensitive). "
                f"Common mistakes: RAGMCP, markdown-folder, JSON-DB, custom_api.",
                offending_field="kb_adapter.adapter_type",
                adapter_type=adapter_type,
            )

        connection = kb_adapter_config.get("connection", {})
        skill_ref = kb_adapter_config.get("skill_ref")

        # Validate bootstrap_tier_zero_threshold — must be a non-negative integer
        tier_zero_threshold = kb_adapter_config.get("bootstrap_tier_zero_threshold", 0)
        if isinstance(tier_zero_threshold, bool) or not isinstance(tier_zero_threshold, int):
            raise ConfigError(
                f"'kb_adapter.bootstrap_tier_zero_threshold' must be a non-negative integer, "
                f"got: {tier_zero_threshold!r}",
                offending_field="kb_adapter.bootstrap_tier_zero_threshold",
                adapter_type=adapter_type,
            )
        if tier_zero_threshold < 0:
            raise ConfigError(
                f"'kb_adapter.bootstrap_tier_zero_threshold' must be >= 0 "
                f"(got {tier_zero_threshold}). Use 0 to disable Tier 0.",
                offending_field="kb_adapter.bootstrap_tier_zero_threshold",
                adapter_type=adapter_type,
            )

        # Validate role_system config if present
        role_system_config = config.get("role_system")
        if role_system_config:
            cls._validate_role_system(role_system_config)

        # Instantiate concrete adapter (ONLY place concrete adapters are imported)
        adapter = cls._instantiate_adapter(adapter_type, connection, skill_ref)

        return cls(adapter, _sentinel=_BIND_SENTINEL)

    @staticmethod
    def _validate_role_system(role_system_config: dict):
        """
        Validate role_system config block.

        Raises:
            ConfigError: invalid role_type values or missing required fields
        """
        from .enums import VALID_ROLE_TYPES

        roles = role_system_config.get("roles", [])
        for i, role in enumerate(roles):
            role_type = role.get("role_type")
            if role_type not in VALID_ROLE_TYPES:
                raise ConfigError(
                    f"role_system.roles[{i}].role_type '{role_type}' is not valid. "
                    f"Must be one of: {sorted(VALID_ROLE_TYPES)} (exact strings). "
                    f"Common mistakes: HUMAN_ONLY, MULTIAGENT, ai-assisted.",
                    offending_field=f"role_system.roles[{i}].role_type",
                    adapter_type=None,
                )

            # null linked_agent is valid — not an error
            placeholder_name = role.get("placeholder_name")
            if not placeholder_name:
                raise ConfigError(
                    f"role_system.roles[{i}] missing required 'placeholder_name'",
                    offending_field=f"role_system.roles[{i}].placeholder_name",
                    adapter_type=None,
                )

    @staticmethod
    def _instantiate_adapter(adapter_type: str, connection: dict, skill_ref: str) -> BaseAdapter:
        """
        Instantiate the concrete adapter for the given adapter_type.

        This is the ONLY location where concrete adapter modules are imported.
        Business logic never reaches this far directly.

        Raises:
            ConfigError: adapter-specific validation failure
        """
        if adapter_type == "RAG_MCP":
            from .adapters.rag_mcp import RagMcpAdapter
            return RagMcpAdapter(connection)

        elif adapter_type == "MARKDOWN_FOLDER":
            # MARKDOWN_FOLDER requires skill_ref — validate before construction
            if not skill_ref:
                raise ConfigError(
                    "MARKDOWN_FOLDER adapter requires 'skill_ref' in kb_adapter config. "
                    "Set kb_adapter.skill_ref to the path or name of the delegating skill.",
                    offending_field="kb_adapter.skill_ref",
                    adapter_type="MARKDOWN_FOLDER",
                )
            from .adapters.markdown_folder import MarkdownFolderAdapter
            return MarkdownFolderAdapter(connection, skill_ref)

        elif adapter_type == "JSON_DB":
            from .adapters.json_db import JsonDbAdapter
            return JsonDbAdapter(connection)

        elif adapter_type == "CUSTOM_API":
            from .adapters.custom_api import CustomApiAdapter
            return CustomApiAdapter(connection)

        # This branch is unreachable due to VALID_ADAPTER_TYPES check above,
        # but guards against future code drift.
        raise ConfigError(
            f"Unknown adapter_type '{adapter_type}' — internal error in _instantiate_adapter",
            offending_field="kb_adapter.adapter_type",
            adapter_type=adapter_type,
        )

    # ── Public interface (the only methods business logic should call) ────────

    @observe(name="kb-query", as_type="retriever", capture_input=False, capture_output=False)
    def query(self, query_string: str, filters: dict = None) -> list:
        """
        Query the bound KB backend.

        Args:
            query_string: Search string / question
            filters: Optional filter criteria

        Returns:
            list of QueryResult objects

        Raises:
            AdapterIOError: backend failure (recoverable: True)
        """
        _lf = get_client()
        _lf.update_current_span(input={"query": query_string[:500], "adapter_type": self._adapter.adapter_type})
        results = self._adapter.query(query_string, filters)
        _lf.update_current_span(output={"result_count": len(results)})
        return results

    def populate(self, content: str, tier: int, metadata: dict = None):
        """
        Write content to the bound KB backend.

        Returns:
            PopulateResult — MUST switch on .kind before consuming payload
                kind="write_status" → JSON_DB, MARKDOWN_FOLDER
                kind="manifest"     → RAG_MCP only

        Raises:
            AdapterIOError: backend write failure (recoverable: True)
            ConfigError: CUSTOM_API hard failure (recoverable: False)
        """
        return self._adapter.populate(content, tier, metadata)

    def scan_gaps(self, schema_definition: dict) -> list:
        """
        Scan the bound KB backend for gaps.

        Args:
            schema_definition: Dict with "entries" list, each entry having "id"

        Returns:
            list of GapResult objects

        Raises:
            AdapterIOError: backend failure (recoverable: True)
        """
        return self._adapter.scan_gaps(schema_definition)
