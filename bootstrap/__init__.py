"""
KB Bootstrap Module — PBCPB Unified

5-step CoT bootstrap sequence:
    Step 1: scan_gaps     — identify missing/placeholder/incomplete entries
    Step 2: tier_scoring  — score entries by dependency tier (with cycle detection)
    Step 3: populate_core — populate Tier 1 entries
    Step 4: defer_tier2+  — write deferred-backlog.json
    Step 5: dify_manifest — write dify-upload-manifest.json (RAG_MCP only)

Prerequisite: AdapterSession.bind() must succeed before calling any bootstrap step.

Usage:
    from bootstrap import BootstrapRunner
    runner = BootstrapRunner(session, config)
    result = runner.run()
"""

from .runner import BootstrapRunner
from .tier_scorer import TierScorer

__all__ = ["BootstrapRunner", "TierScorer"]
