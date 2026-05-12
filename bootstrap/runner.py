"""
BootstrapRunner — executes the 5-step CoT KB bootstrap sequence.

Steps:
    5.1 scan_gaps      — invoke adapter.scan_gaps(schema_definition)
    5.2 tier_scoring   — score gaps; detect cycles; promote SCC members to Tier 1
    5.3 populate_core  — populate Tier 1 gaps (text KBs) or generate manifest items (RAG_MCP)
    5.4 defer_tier2+   — write deferred-backlog.json
    5.5 dify_manifest  — write dify-upload-manifest.json (RAG_MCP only)

Re-run semantics:
    scan_gaps runs fresh for idempotency.
    Existing backlog is read for context but not trusted as authoritative.
    Fresh backlog written with updated generated_at timestamp.

Output paths:
    Deferred backlog: <pbcpb_root>/bootstrap/deferred-backlog.json
    Dify manifest:    <pbcpb_root>/bootstrap/dify-upload-manifest.json (RAG_MCP only)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from langfuse import observe, get_client

from .tier_scorer import TierScorer, CyclicSchemaError


class BootstrapRunner:
    """
    Orchestrates the 5-step bootstrap sequence.

    Usage:
        runner = BootstrapRunner(session, config, pbcpb_root=".")
        result = runner.run()
        print(result["summary"])
    """

    def __init__(self, session, config: dict, pbcpb_root: str = "."):
        """
        Args:
            session: AdapterSession (bound) — provides query/populate/scan_gaps
            config: Full pbcpb.config.json as dict
            pbcpb_root: Root path for output files (default: current directory)
        """
        self._session = session
        self._config = config
        self._pbcpb_root = Path(pbcpb_root)

        kb_adapter_config = config.get("kb_adapter", {})
        self._adapter_type = kb_adapter_config.get("adapter_type")
        self._tier_limit = kb_adapter_config.get("bootstrap_tier_limit", 1)
        self._tier_zero_threshold = kb_adapter_config.get("bootstrap_tier_zero_threshold", 0)

    def _get_schema_definition(self) -> dict:
        """
        Load or derive schema_definition.

        For JSON_DB: derives from master-index if available.
        For all adapters: returns minimal schema if no master-index found.
        Falls back to config-defined schema if present.
        """
        # Check for schema in config
        schema = self._config.get("kb_schema")
        if schema:
            return schema

        # Try to derive from master-index (JSON_DB path)
        kb_adapter_config = self._config.get("kb_adapter", {})
        connection = kb_adapter_config.get("connection", {})
        kb_root = connection.get("kb_root")

        if kb_root:
            master_index_path = Path(kb_root) / "master-index.json"
            if master_index_path.exists():
                try:
                    index = json.loads(master_index_path.read_text())
                    # Convert master-index entries to schema_definition format
                    entries = []
                    for entry_ref in index.get("entries", []):
                        entry_id = entry_ref.get("id")
                        if entry_id:
                            entries.append({
                                "id": entry_id,
                                "topic": entry_ref.get("topic", "general"),
                                "layer": entry_ref.get("layer", "general"),
                                "required": entry_ref.get("required", False),
                                "depends_on": entry_ref.get("depends_on", []),
                            })
                    return {"entries": entries}
                except (json.JSONDecodeError, OSError):
                    pass

        # Minimal fallback schema
        return {"entries": []}

    @observe(name="scan-gaps", capture_input=False, capture_output=False)
    def step1_scan_gaps(self, schema_definition: dict) -> list:
        """
        Step 5.1: Invoke adapter.scan_gaps(schema_definition).

        Returns:
            Raw gap list (list of GapResult objects)
        """
        _lf = get_client()
        _lf.update_current_span(input={"entry_count": len(schema_definition.get("entries", []))})
        gaps = self._session.scan_gaps(schema_definition)
        _lf.update_current_span(output={"gap_count": len(gaps)})
        return gaps

    @observe(name="tier-scoring", capture_input=False, capture_output=False)
    def step2_tier_scoring(self, schema_definition: dict) -> tuple:
        """
        Step 5.2: Build dependency graph, detect cycles, score entries into tiers.

        Returns:
            tuple of (scored_entries: list, scc_groups: list, is_dag: bool)
        """
        _lf = get_client()
        _lf.update_current_span(input={"entry_count": len(schema_definition.get("entries", []))})
        scorer = TierScorer(schema_definition, tier_zero_threshold=self._tier_zero_threshold)
        try:
            scored = scorer.score()
        except CyclicSchemaError as e:
            # Structured error — not silent divergence
            raise RuntimeError(f"CyclicSchemaError during tier_scoring: {e}")

        scc_groups = scorer.scc_groups
        is_dag = len(scc_groups) == 0
        _lf.update_current_span(output={"scored_count": len(scored), "is_dag": is_dag, "scc_count": len(scc_groups)})
        return scored, scc_groups, is_dag

    @observe(name="populate-core", capture_input=False, capture_output=False)
    def step3_populate_core(self, gaps: list, scored_entries: dict) -> list:
        """
        Step 5.3: Populate Tier 1 gaps only.

        For text KBs (JSON_DB, MARKDOWN_FOLDER, CUSTOM_API):
            Invoke adapter.populate(content, tier=1, metadata)
        For RAG_MCP:
            Skip auto-populate; generate manifest entries instead.

        Args:
            gaps: list of GapResult objects from step1
            scored_entries: dict of entry_id → scored entry dict from step2

        Returns:
            list of populate results or manifest items
        """
        _lf = get_client()
        tier1_gap_ids = {
            e["entry_id"] for e in scored_entries.values()
            if e["tier"] == 1
        }
        _lf.update_current_span(input={"total_gaps": len(gaps), "tier1_gaps": len(tier1_gap_ids)})

        results = []
        for gap in gaps:
            if gap.gap_id not in tier1_gap_ids:
                continue

            schema_node = gap.schema_node or {}
            metadata = {
                "entry_id": gap.gap_id,
                "topic": schema_node.get("topic", "general"),
                "layer": schema_node.get("layer", "general"),
                "gap_type": gap.type,
            }

            if self._adapter_type == "RAG_MCP":
                # Generate manifest entry only — no direct write
                populate_result = self._session.populate(
                    content=f"[TIER-1-GAP] {gap.gap_id}: {gap.location}",
                    tier=1,
                    metadata=metadata,
                )
                # kind == "manifest" — accumulate for step5
                if populate_result.kind == "manifest":
                    results.extend(populate_result.items)
            else:
                # Write-capable adapters
                content = schema_node.get("seed_content", f"[PLACEHOLDER] {gap.gap_id} — populate with domain knowledge")
                populate_result = self._session.populate(content=content, tier=1, metadata=metadata)
                results.append(populate_result.to_dict())

        _lf.update_current_span(output={"populated_count": len(results)})
        return results

    @observe(name="write-backlog", capture_input=False, capture_output=False)
    def step4_write_deferred_backlog(self, gaps: list, scored_entries: dict) -> Path:
        """
        Step 5.4: Write deferred-backlog.json for Tier 2+ gaps.

        Re-run idempotent: reads existing backlog for context, writes fresh with updated timestamp.

        Args:
            gaps: All gaps from step1
            scored_entries: dict entry_id → scored dict from step2

        Returns:
            Path to written backlog file
        """
        _lf = get_client()
        _lf.update_current_span(input={"gap_count": len(gaps)})

        output_dir = self._pbcpb_root / "bootstrap"
        output_dir.mkdir(parents=True, exist_ok=True)
        backlog_path = output_dir / "deferred-backlog.json"

        # Build fresh deferred list (Tier 2+)
        deferred = []
        for gap in gaps:
            scored = scored_entries.get(gap.gap_id, {})
            tier = scored.get("tier", 3)
            if tier >= 2:
                deferred.append({
                    "gap_id": gap.gap_id,
                    "location": gap.location,
                    "type": gap.type,
                    "tier": tier,
                    "schema_node": gap.schema_node,
                })

        # Sort deferred: ascending tier, then alphabetically
        deferred.sort(key=lambda x: (x["tier"], x["gap_id"]))

        backlog = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tier_limit_used": self._tier_limit,
            "deferred_count": len(deferred),
            "deferred": deferred,
        }

        backlog_path.write_text(json.dumps(backlog, indent=2))
        _lf.update_current_span(output={"deferred_count": len(deferred), "backlog_path": str(backlog_path)})
        return backlog_path

    @observe(name="write-manifest", capture_input=False, capture_output=False)
    def step5_write_dify_manifest(self, manifest_items: list) -> Path | None:
        """
        Step 5.5: Write dify-upload-manifest.json (RAG_MCP only).

        Only called when adapter_type == RAG_MCP. Returns None otherwise.

        Args:
            manifest_items: list of manifest item dicts from step3

        Returns:
            Path to manifest file, or None if not RAG_MCP
        """
        _lf = get_client()
        _lf.update_current_span(input={"item_count": len(manifest_items)})

        if self._adapter_type != "RAG_MCP":
            _lf.update_current_span(output={"skipped": True, "reason": "not RAG_MCP"})
            return None

        output_dir = self._pbcpb_root / "bootstrap"
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "dify-upload-manifest.json"

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "adapter_type": "RAG_MCP",
            "item_count": len(manifest_items),
            "items": manifest_items,
            "instructions": (
                "Upload each item's payload.content to the Dify dataset "
                "at item.target_location. See docs/adapters/rag-mcp-guide.md "
                "for upload procedures."
            ),
        }

        manifest_path.write_text(json.dumps(manifest, indent=2))
        _lf.update_current_span(output={"manifest_path": str(manifest_path), "item_count": len(manifest_items)})
        return manifest_path

    @observe(name="bootstrap-run", as_type="agent", capture_input=False, capture_output=False)
    def run(self) -> dict:
        """
        Execute all 5 bootstrap steps in sequence.

        Returns:
            Summary dict with step results, file paths, SCC groups, counts.

        Note: Errors in step1-step3 propagate. Steps 4-5 write files.

        Trace propagation: to attach this run to the root PBCPB trace, pass the
        active trace_id as a keyword argument at call time::

            from tracing import RunTrace
            result = runner.run(langfuse_trace_id=RunTrace.current_trace_id())
        """
        _lf = get_client()
        _lf.update_current_span(input={
            "adapter_type": self._adapter_type,
            "tier_limit": self._tier_limit,
        })

        schema_definition = self._get_schema_definition()

        # Step 5.1: scan_gaps
        try:
            gaps = self.step1_scan_gaps(schema_definition)
        except Exception as e:
            gaps = []
            scan_error = str(e)
        else:
            scan_error = None

        gap_dicts = [g.to_dict() for g in gaps]

        # Step 5.2: tier_scoring
        scored_list, scc_groups, is_dag = self.step2_tier_scoring(schema_definition)
        scored_by_id = {s["entry_id"]: s for s in scored_list}

        # Step 5.3: populate_core (Tier 1 only)
        if not scan_error and gaps:
            populate_results = self.step3_populate_core(gaps, scored_by_id)
        else:
            populate_results = []

        # Step 5.4: deferred backlog
        backlog_path = self.step4_write_deferred_backlog(gaps, scored_by_id)

        # Step 5.5: Dify manifest (RAG_MCP only)
        manifest_items = [r for r in populate_results if isinstance(r, dict) and "entry_id" in r]
        manifest_path = self.step5_write_dify_manifest(manifest_items)

        tier_counts = {}
        for s in scored_list:
            t = s["tier"]
            tier_counts[t] = tier_counts.get(t, 0) + 1

        summary = {
            "adapter_type": self._adapter_type,
            "total_gaps": len(gaps),
            "scan_error": scan_error,
            "is_dag": is_dag,
            "scc_groups": [g.to_dict() for g in scc_groups],
            "tier_counts": tier_counts,
            "tier1_populated": len([s for s in scored_list if s["tier"] == 1]),
            "deferred_count": len([s for s in scored_list if s["tier"] >= 2]),
        }
        _lf.update_current_span(output=summary)

        return {
            "summary": summary,
            "gaps": gap_dicts,
            "scored_entries": scored_list,
            "backlog_path": str(backlog_path),
            "manifest_path": str(manifest_path) if manifest_path else None,
        }
