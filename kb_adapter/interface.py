"""
BaseAdapter — abstract interface all adapters must implement.

Three-method contract:
    query(query_string, filters=None) → list[QueryResult]
    populate(content, tier, metadata=None) → PopulateResult
    scan_gaps(schema_definition) → list[GapResult]

STATELESS_INTERFACE: no session state in method signatures.
CALLER_INVARIANCE: business logic imports BaseAdapter only, never concrete adapters.
"""

from abc import ABC, abstractmethod
from typing import Any


# ── Result types ──────────────────────────────────────────────────────────────

class QueryResult:
    """
    A single result from adapter.query().

    Fields:
        entry_id      — unique identifier within the KB
        content       — text content of the entry
        metadata      — arbitrary dict of entry metadata
        source_adapter— the adapter_type string that produced this result
    """
    __slots__ = ("entry_id", "content", "metadata", "source_adapter")

    def __init__(self, entry_id: str, content: str, metadata: dict, source_adapter: str):
        self.entry_id = entry_id
        self.content = content
        self.metadata = metadata
        self.source_adapter = source_adapter

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "content": self.content,
            "metadata": self.metadata,
            "source_adapter": self.source_adapter,
        }


class PopulateResult:
    """
    Discriminated union result from adapter.populate().

    kind is ALWAYS present. Callers MUST switch on kind before consuming payload.

    kind == "write_status"  → write-capable adapters (JSON_DB, MARKDOWN_FOLDER via skill)
        success: bool
        written_count: int
        errors: list[str]

    kind == "manifest"      → RAG_MCP only (no direct writes to Dify)
        manifest_path: str
        items: list[{entry_id, target_location, payload}]
    """
    __slots__ = ("kind", "success", "written_count", "errors", "manifest_path", "items")

    def __init__(self, kind: str, **kwargs):
        if kind not in ("write_status", "manifest"):
            raise ValueError(f"PopulateResult.kind must be 'write_status' or 'manifest', got '{kind}'")
        self.kind = kind
        # write_status fields
        self.success = kwargs.get("success")
        self.written_count = kwargs.get("written_count")
        self.errors = kwargs.get("errors", [])
        # manifest fields
        self.manifest_path = kwargs.get("manifest_path")
        self.items = kwargs.get("items", [])

    def to_dict(self) -> dict:
        if self.kind == "write_status":
            return {
                "kind": "write_status",
                "success": self.success,
                "written_count": self.written_count,
                "errors": self.errors,
            }
        else:
            return {
                "kind": "manifest",
                "manifest_path": self.manifest_path,
                "items": self.items,
            }


class GapResult:
    """
    A single gap found by adapter.scan_gaps().

    Fields:
        gap_id      — resolves to entry.id in schema_definition (namespace coherence rule)
        location    — human-readable location description
        type        — "missing" | "placeholder" | "incomplete"
        schema_node — the schema node this gap relates to
    """
    VALID_TYPES = {"missing", "placeholder", "incomplete"}
    __slots__ = ("gap_id", "location", "type", "schema_node")

    def __init__(self, gap_id: str, location: str, gap_type: str, schema_node: Any):
        if gap_type not in self.VALID_TYPES:
            raise ValueError(f"gap_type must be one of {self.VALID_TYPES}, got '{gap_type}'")
        self.gap_id = gap_id
        self.location = location
        self.type = gap_type
        self.schema_node = schema_node

    def to_dict(self) -> dict:
        return {
            "gap_id": self.gap_id,
            "location": self.location,
            "type": self.type,
            "schema_node": self.schema_node,
        }


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseAdapter(ABC):
    """
    Abstract interface all KB adapters must implement.

    Concrete adapters are instantiated by AdapterSession.bind() only.
    Business logic MUST NOT import concrete adapters.
    """

    def __init__(self, adapter_type: str, connection_config: dict):
        """
        Initialize adapter with its type label and connection config.

        Args:
            adapter_type: One of the VALID_ADAPTER_TYPES exact strings
            connection_config: Adapter-specific connection parameters
        """
        self._adapter_type = adapter_type
        self._connection_config = connection_config

    @property
    def adapter_type(self) -> str:
        return self._adapter_type

    @abstractmethod
    def query(self, query_string: str, filters: dict = None) -> list:
        """
        Query the knowledge base.

        Args:
            query_string: Search string / question
            filters: Optional dict of filter criteria

        Returns:
            list of QueryResult objects

        Raises:
            AdapterIOError on timeout (default 60s) or backend failure
        """
        raise NotImplementedError

    @abstractmethod
    def populate(self, content: str, tier: int, metadata: dict = None) -> PopulateResult:
        """
        Write content to the knowledge base (or generate upload manifest for RAG_MCP).

        Args:
            content: The content to populate
            tier: Tier level (0=opt-in, 1=core, 2=important, 3+=enrichment)
            metadata: Optional metadata dict

        Returns:
            PopulateResult — callers MUST switch on .kind before consuming

        Raises:
            AdapterIOError on write failure (recoverable: True)
            ConfigError for CUSTOM_API hard failures (recoverable: False)
        """
        raise NotImplementedError

    @abstractmethod
    def scan_gaps(self, schema_definition: dict) -> list:
        """
        Scan the KB for gaps against a schema definition.

        Args:
            schema_definition: Dict describing expected KB structure.
                Each entry must have an "id" field (gap_id namespace coherence).

        Returns:
            list of GapResult objects

        Raises:
            AdapterIOError on backend failure
        """
        raise NotImplementedError
