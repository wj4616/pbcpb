"""
JSON_DB Adapter — pbcpb's original local JSON knowledge base.

Implements all 3 methods directly against the JSON file hierarchy.
No external dependencies. Suitable for local, offline KB operation.

KB structure (from KB-SYSTEM-MANUAL.md):
    <kb_root>/
        master-index.json           — entry registry
        <layer>/
            manifest.json           — layer manifest
            <topic>/
                <entry_id>.json     — individual entries

CALLER_INVARIANCE: import this only from AdapterSession (session.py).
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ..interface import BaseAdapter, QueryResult, PopulateResult, GapResult
from ..errors import AdapterIOError, ConfigError


class JsonDbAdapter(BaseAdapter):
    """
    KB adapter backed by the pbcpb local JSON knowledge base.

    Connection config fields:
        kb_root        — root path of the KB directory (required)
        default_layer  — default layer name for writes (default: "general")
        timeout        — per-call timeout in seconds (default: 60, used for fs ops)

    All 3 methods are implemented directly — no external process or network call.
    """

    def __init__(self, connection_config: dict):
        super().__init__("JSON_DB", connection_config)
        kb_root = connection_config.get("kb_root")
        if not kb_root:
            raise ConfigError(
                "JSON_DB adapter requires 'kb_root' in connection config",
                offending_field="kb_adapter.connection.kb_root",
                adapter_type="JSON_DB",
            )
        self._kb_root = Path(kb_root)
        self._default_layer = connection_config.get("default_layer", "general")
        self._timeout = connection_config.get("timeout", 60)

    def _load_master_index(self) -> dict:
        """Load master-index.json from kb_root."""
        index_path = self._kb_root / "master-index.json"
        if not index_path.exists():
            return {"entries": []}
        try:
            return json.loads(index_path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise AdapterIOError(
                f"JSON_DB: failed to read master-index.json: {e}",
                adapter_type="JSON_DB",
            )

    def _save_master_index(self, index: dict):
        """Write master-index.json to kb_root."""
        index_path = self._kb_root / "master-index.json"
        try:
            self._kb_root.mkdir(parents=True, exist_ok=True)
            index_path.write_text(json.dumps(index, indent=2))
        except OSError as e:
            raise AdapterIOError(
                f"JSON_DB: failed to write master-index.json: {e}",
                adapter_type="JSON_DB",
            )

    def _load_entry(self, layer: str, topic: str, entry_id: str) -> dict | None:
        """Load a single entry JSON file."""
        entry_path = self._kb_root / layer / topic / f"{entry_id}.json"
        if not entry_path.exists():
            return None
        try:
            return json.loads(entry_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _match_entry(self, entry: dict, query_string: str, filters: dict) -> bool:
        """
        Simple text-match scoring for JSON_DB query.

        Returns True if query terms appear in entry content or metadata.
        Filters are applied as exact-match on metadata fields.
        """
        query_lower = query_string.lower()
        content = str(entry.get("content", "")).lower()
        metadata = entry.get("metadata", {})

        # Apply filters first (all must match)
        if filters:
            for key, value in filters.items():
                entry_val = metadata.get(key, "")
                if str(value).lower() not in str(entry_val).lower():
                    return False

        # Score: at least one query token must appear in content
        tokens = query_lower.split()
        return any(tok in content for tok in tokens)

    def query(self, query_string: str, filters: dict = None) -> list:
        """
        Query the JSON knowledge base.

        Loads all entries from master-index and returns those matching
        query_string (simple text match) with filters applied.

        Returns:
            list of QueryResult objects

        Raises:
            AdapterIOError: cannot read master-index or entry files
        """
        if not self._kb_root.exists():
            raise AdapterIOError(
                f"JSON_DB: kb_root '{self._kb_root}' does not exist",
                adapter_type="JSON_DB",
            )

        index = self._load_master_index()
        results = []

        for entry_ref in index.get("entries", []):
            layer = entry_ref.get("layer", self._default_layer)
            topic = entry_ref.get("topic", "general")
            entry_id = entry_ref.get("id")
            if not entry_id:
                continue

            entry = self._load_entry(layer, topic, entry_id)
            if not entry:
                continue

            if self._match_entry(entry, query_string, filters or {}):
                results.append(QueryResult(
                    entry_id=entry_id,
                    content=entry.get("content", ""),
                    metadata=entry.get("metadata", {}),
                    source_adapter="JSON_DB",
                ))

        return results

    def populate(self, content: str, tier: int, metadata: dict = None) -> PopulateResult:
        """
        Write content to the JSON knowledge base.

        Creates a new entry JSON file and registers it in master-index.json.

        Returns:
            PopulateResult(kind="write_status") — callers MUST check .kind

        Raises:
            AdapterIOError: cannot write to kb_root
        """
        meta = metadata or {}
        entry_id = meta.get("entry_id", f"entry-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}")
        layer = meta.get("layer", self._default_layer)
        topic = meta.get("topic", "general")

        entry_dir = self._kb_root / layer / topic
        entry_path = entry_dir / f"{entry_id}.json"

        entry_data = {
            "id": entry_id,
            "content": content,
            "tier": tier,
            "metadata": {
                "layer": layer,
                "topic": topic,
                "tier": tier,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **meta,
            },
        }

        try:
            entry_dir.mkdir(parents=True, exist_ok=True)
            entry_path.write_text(json.dumps(entry_data, indent=2))
        except OSError as e:
            return PopulateResult(
                kind="write_status",
                success=False,
                written_count=0,
                errors=[str(e)],
            )

        # Register in master-index
        index = self._load_master_index()
        existing_ids = {e.get("id") for e in index.get("entries", [])}
        if entry_id not in existing_ids:
            index.setdefault("entries", []).append({
                "id": entry_id,
                "layer": layer,
                "topic": topic,
                "tier": tier,
            })
            self._save_master_index(index)

        return PopulateResult(
            kind="write_status",
            success=True,
            written_count=1,
            errors=[],
        )

    def scan_gaps(self, schema_definition: dict) -> list:
        """
        Scan the JSON KB for gaps against schema_definition.

        Compares schema entries against master-index. Missing entries are
        reported as "missing"; entries present but with placeholder content
        are "placeholder"; entries with incomplete required fields are "incomplete".

        gap_id resolves to entry.id in schema_definition (namespace coherence).

        Returns:
            list of GapResult objects

        Raises:
            AdapterIOError: cannot read master-index
        """
        index = self._load_master_index()
        existing_ids = {e.get("id") for e in index.get("entries", [])}

        gaps = []
        for entry in schema_definition.get("entries", []):
            entry_id = entry.get("id")
            if not entry_id:
                continue

            gap_id = entry_id  # namespace coherence: gap_id = entry.id

            if entry_id not in existing_ids:
                gaps.append(GapResult(
                    gap_id=gap_id,
                    location=f"{self._kb_root}/{entry.get('layer', self._default_layer)}/{entry.get('topic', 'general')}/{entry_id}.json",
                    gap_type="missing",
                    schema_node=entry,
                ))
            else:
                # Load the entry and check for placeholder content
                layer = entry.get("layer", self._default_layer)
                topic = entry.get("topic", "general")
                loaded = self._load_entry(layer, topic, entry_id)

                if loaded is None:
                    gaps.append(GapResult(
                        gap_id=gap_id,
                        location=f"{self._kb_root}/{layer}/{topic}/{entry_id}.json",
                        gap_type="missing",
                        schema_node=entry,
                    ))
                else:
                    content = loaded.get("content", "")
                    # Placeholder detection: "TODO" or empty content
                    if not content or re.search(r"\bTODO\b", content, re.IGNORECASE):
                        gaps.append(GapResult(
                            gap_id=gap_id,
                            location=f"{self._kb_root}/{layer}/{topic}/{entry_id}.json",
                            gap_type="placeholder",
                            schema_node=entry,
                        ))
                    # Incomplete detection: required metadata fields missing
                    elif entry.get("required", False):
                        required_fields = entry.get("required_fields", [])
                        meta = loaded.get("metadata", {})
                        missing_fields = [f for f in required_fields if f not in meta]
                        if missing_fields:
                            gaps.append(GapResult(
                                gap_id=gap_id,
                                location=f"{self._kb_root}/{layer}/{topic}/{entry_id}.json",
                                gap_type="incomplete",
                                schema_node=entry,
                            ))

        return gaps
