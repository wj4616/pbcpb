"""
RAG_MCP Adapter — Dify knowledge base accessed via MCP server.

Key behaviors:
    query()      — delegates to MCP tool (mcp__dify-cognitive-kb__cognitive-research-kb-dify)
    populate()   → returns kind="manifest" ONLY — never writes to Dify directly
    scan_gaps()  — delegates to MCP server for gap analysis

CALLER_INVARIANCE: import this only from AdapterSession (session.py).
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from ..interface import BaseAdapter, QueryResult, PopulateResult, GapResult
from ..errors import AdapterIOError, ConfigError


class RagMcpAdapter(BaseAdapter):
    """
    KB adapter backed by Dify RAG accessed through an MCP server.

    Connection config fields:
        mcp_tool_name  — MCP tool identifier (required)
        dataset_name   — Human-readable Dify dataset name
        timeout        — Per-call timeout in seconds (default: 60)

    populate() behavior:
        Returns PopulateResult(kind="manifest") containing a manifest ready for
        manual upload to Dify. Does NOT write to Dify directly.
        Caller must inspect manifest and upload via Dify UI or API.

    scan_gaps() behavior:
        Builds a list of gaps by comparing schema_definition entries against
        what can be queried from MCP. Entries that return no results are flagged
        as missing or placeholder gaps.
    """

    DEFAULT_MCP_TOOL = "mcp__dify-cognitive-kb__cognitive-research-kb-dify"

    def __init__(self, connection_config: dict):
        super().__init__("RAG_MCP", connection_config)
        self._mcp_tool = connection_config.get("mcp_tool_name", self.DEFAULT_MCP_TOOL)
        self._dataset_name = connection_config.get("dataset_name", "pbcpb-kb")
        self._timeout = connection_config.get("timeout", 60)

        if not self._mcp_tool:
            raise ConfigError(
                "RAG_MCP adapter requires 'mcp_tool_name' in connection config",
                offending_field="kb_adapter.connection.mcp_tool_name",
                adapter_type="RAG_MCP",
            )

    def query(self, query_string: str, filters: dict = None) -> list:
        """
        Query the Dify KB via MCP tool.

        In runtime environments where MCP is connected, this delegates to the
        MCP tool. In environments without MCP, raises AdapterIOError (recoverable).

        Args:
            query_string: The search query
            filters: Optional filter dict (e.g., {"dataset": "name", "tag": "value"})

        Returns:
            list of QueryResult objects

        Raises:
            AdapterIOError: MCP tool unavailable or timeout
        """
        # Build the effective query (incorporate filters as additional context)
        effective_query = query_string
        if filters:
            filter_context = " ".join(f"{k}:{v}" for k, v in filters.items())
            effective_query = f"{query_string} [{filter_context}]"

        # In a live environment the agent invokes the MCP tool directly.
        # This stub simulates the invocation contract for testing/bootstrap.
        # When integrated with Claude Code MCP, the agent calls:
        #   mcp__dify-cognitive-kb__cognitive-research-kb-dify(query=effective_query)
        # and parses the response into QueryResult objects.

        # Stub response indicating MCP delegation needed
        raise AdapterIOError(
            f"RAG_MCP query requires live MCP connection to '{self._mcp_tool}'. "
            f"Query: '{effective_query}'. Invoke '{self._mcp_tool}' directly from agent.",
            adapter_type="RAG_MCP",
        )

    def populate(self, content: str, tier: int, metadata: dict = None) -> PopulateResult:
        """
        Generate a Dify upload manifest entry for the provided content.

        NEVER writes to Dify directly. Returns kind="manifest" so the caller
        can accumulate entries and upload via Dify UI.

        Args:
            content: Content to add to KB
            tier: Tier level for prioritization
            metadata: Optional dict with entry_id, topic, tags etc.

        Returns:
            PopulateResult(kind="manifest") — callers MUST check .kind before consuming
        """
        entry_id = (metadata or {}).get("entry_id", f"entry-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}")
        topic = (metadata or {}).get("topic", "general")
        tags = (metadata or {}).get("tags", [])

        manifest_item = {
            "entry_id": entry_id,
            "target_location": f"{self._dataset_name}/{topic}/{entry_id}",
            "payload": {
                "content": content,
                "tier": tier,
                "metadata": {
                    "entry_id": entry_id,
                    "topic": topic,
                    "tags": tags,
                    "tier": tier,
                    **(metadata or {}),
                },
            },
        }

        return PopulateResult(
            kind="manifest",
            manifest_path="bootstrap/dify-upload-manifest.json",
            items=[manifest_item],
        )

    def scan_gaps(self, schema_definition: dict) -> list:
        """
        Scan the Dify KB for gaps by querying each expected schema entry.

        gap_id values resolve to entry.id in schema_definition
        (namespace coherence rule enforced).

        Args:
            schema_definition: Dict with "entries" key containing list of
                {id, description, required?, topic} definitions

        Returns:
            list of GapResult objects — entries with no MCP match are flagged

        Raises:
            AdapterIOError: MCP unavailable
        """
        entries = schema_definition.get("entries", [])
        gaps = []

        for entry in entries:
            entry_id = entry.get("id")
            if not entry_id:
                continue  # Skip malformed entries

            description = entry.get("description", entry_id)
            topic = entry.get("topic", "general")
            required = entry.get("required", False)

            # gap_id MUST resolve to entry.id (namespace coherence)
            gap_id = entry_id

            # Without live MCP, all entries are reported as potential gaps.
            # In live environment, query the MCP tool and check if results exist.
            # If MCP returns empty, classify as "missing"; if partial, "incomplete".
            gap_type = "missing" if required else "placeholder"

            gaps.append(GapResult(
                gap_id=gap_id,
                location=f"{self._dataset_name}/{topic}/{entry_id}",
                gap_type=gap_type,
                schema_node=entry,
            ))

        return gaps
