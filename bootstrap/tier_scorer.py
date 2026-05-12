"""
TierScorer — dependency graph analysis and tier scoring for KB entries.

Algorithm:
    1. Build directed graph G from schema_definition (entries as nodes, deps as edges)
    2. Run cycle detection via Kosaraju's SCC algorithm
    3. If SCCs exist: record scc_group_id for each SCC member, promote to Tier 1
    4. If DAG: proceed to standard scoring

Tier scoring rules:
    Tier 0 (opt-in):    in_degree >= bootstrap_tier_zero_threshold (default 0 = disabled)
    Tier 1 (core):      in_degree >= 2, OR required: true, OR foundational, OR SCC member
    Tier 2 (important): in_degree == 1, no required flag
    Tier 3+ (enrichment): leaf node, zero dependents, no required flag

Sort order: ascending tier, then alphabetically by gap_id within tier.

Cyclic schema handling:
    SCCs are detected. All SCC members jointly promoted to Tier 1.
    scc_group_id recorded for audit. Never silent divergence.
    CyclicSchemaError raised if cycle detection fails unexpectedly.
"""

from collections import defaultdict


class CyclicSchemaError(Exception):
    """
    Raised if Kosaraju SCC decomposition encounters an unexpected error.

    Never raised for normal SCCs — those are handled by SCC promotion.
    Only raised for algorithmic failures (e.g., graph corruption).
    """
    pass


class SccGroup:
    """Record of a Strongly Connected Component found in the dependency graph."""

    def __init__(self, scc_group_id: str, member_entry_ids: list):
        self.scc_group_id = scc_group_id
        self.member_entry_ids = member_entry_ids

    def to_dict(self) -> dict:
        return {
            "scc_group_id": self.scc_group_id,
            "member_entry_ids": self.member_entry_ids,
        }


class TierScorer:
    """
    Scores KB entries into bootstrap tiers based on dependency analysis.

    Usage:
        scorer = TierScorer(schema_definition, tier_zero_threshold=0)
        scored = scorer.score()
        scc_groups = scorer.scc_groups  # [] if DAG
    """

    def __init__(self, schema_definition: dict, tier_zero_threshold: int = 0):
        """
        Args:
            schema_definition: Dict with "entries" list, each having:
                id: str
                depends_on: list[str] (optional) — IDs this entry depends on
                required: bool (optional)
                foundational: bool (optional)
            tier_zero_threshold: in_degree threshold for Tier 0 (0 = disabled)
        """
        self._entries = {e["id"]: e for e in schema_definition.get("entries", []) if "id" in e}
        self._tier_zero_threshold = tier_zero_threshold
        self._scc_groups = []
        self._scc_member_ids = set()

        # Build adjacency: entry_id → set of entry_ids that depend on it (reverse edges for in-degree)
        self._forward_edges = defaultdict(set)   # entry → entries it depends on
        self._reverse_edges = defaultdict(set)   # entry → entries that depend on it (in-degree sources)

        for entry_id, entry in self._entries.items():
            for dep_id in entry.get("depends_on", []):
                if dep_id in self._entries:
                    self._forward_edges[entry_id].add(dep_id)
                    self._reverse_edges[dep_id].add(entry_id)

    @property
    def scc_groups(self) -> list:
        """List of SccGroup objects found during cycle detection. Empty if DAG."""
        return self._scc_groups

    def _kosaraju_scc(self) -> list:
        """
        Kosaraju's two-pass SCC algorithm.

        Pass 1: DFS on original graph, push nodes to stack in finish order.
        Pass 2: DFS on transposed graph in reverse finish order → SCCs.

        Returns:
            list of SCC groups (each group is a list of entry_ids)
            Single-node groups are NOT cycles; they are just individual nodes.
        """
        node_ids = list(self._entries.keys())
        visited = set()
        finish_order = []

        def dfs1(node):
            """Iterative DFS to avoid Python recursion limits."""
            local_stack = [(node, iter(self._forward_edges[node]))]
            in_stack = {node}

            while local_stack:
                current, neighbors = local_stack[-1]
                try:
                    neighbor = next(neighbors)
                    if neighbor not in visited and neighbor not in in_stack:
                        in_stack.add(neighbor)
                        local_stack.append((neighbor, iter(self._forward_edges[neighbor])))
                except StopIteration:
                    visited.add(current)
                    finish_order.append(current)
                    local_stack.pop()
                    in_stack.discard(current)

        for node in node_ids:
            if node not in visited:
                dfs1(node)

        # Pass 2: DFS on transposed graph
        visited2 = set()
        sccs = []

        def dfs2(start):
            component = []
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited2:
                    continue
                visited2.add(node)
                component.append(node)
                for neighbor in self._reverse_edges[node]:
                    if neighbor not in visited2:
                        stack.append(neighbor)
            return component

        for node in reversed(finish_order):
            if node not in visited2:
                component = dfs2(node)
                sccs.append(component)

        return sccs

    def _detect_cycles(self):
        """
        Run Kosaraju SCC detection. Populate self._scc_groups and self._scc_member_ids.

        SCCs with size > 1 are true cycles. Single-node SCCs are normal nodes.
        """
        try:
            sccs = self._kosaraju_scc()
        except Exception as e:
            raise CyclicSchemaError(
                f"Kosaraju SCC decomposition failed unexpectedly: {e}"
            )

        for i, component in enumerate(sccs):
            if len(component) > 1:
                scc_id = f"SCC-{i+1:03d}"
                group = SccGroup(scc_group_id=scc_id, member_entry_ids=sorted(component))
                self._scc_groups.append(group)
                self._scc_member_ids.update(component)

    def _in_degree(self, entry_id: str) -> int:
        """Number of entries that depend on this entry (i.e., it is a dependency of others)."""
        return len(self._reverse_edges.get(entry_id, set()))

    def _score_entry(self, entry_id: str, entry: dict) -> int:
        """
        Score a single entry into a tier.

        Returns:
            0: Tier 0 (opt-in, only if threshold > 0 and in_degree >= threshold)
            1: Tier 1 (core-necessary)
            2: Tier 2 (important, deferrable)
            3: Tier 3+ (enrichment, leaf)
        """
        in_deg = self._in_degree(entry_id)
        required = entry.get("required", False)
        foundational = entry.get("foundational", False)
        is_scc_member = entry_id in self._scc_member_ids

        # Tier 0 (opt-in): only if threshold > 0
        if self._tier_zero_threshold > 0 and in_deg >= self._tier_zero_threshold:
            return 0

        # Tier 1: referenced by >=2 entries, required, foundational, or SCC member
        if in_deg >= 2 or required or foundational or is_scc_member:
            return 1

        # Tier 2: referenced by exactly 1 entry
        if in_deg == 1:
            return 2

        # Tier 3+: leaf node (no dependents)
        return 3

    def score(self) -> list:
        """
        Score all entries and return sorted list.

        Runs cycle detection first, then scores each entry.

        Returns:
            list of dicts: {
                entry_id: str,
                tier: int,
                in_degree: int,
                required: bool,
                foundational: bool,
                scc_group_id: str | None,
            }
            Sorted: ascending tier, then alphabetically by entry_id within tier.
        """
        self._detect_cycles()

        # Build scc_group_id lookup
        entry_to_scc = {}
        for group in self._scc_groups:
            for member in group.member_entry_ids:
                entry_to_scc[member] = group.scc_group_id

        scored = []
        for entry_id, entry in self._entries.items():
            tier = self._score_entry(entry_id, entry)
            scored.append({
                "entry_id": entry_id,
                "tier": tier,
                "in_degree": self._in_degree(entry_id),
                "required": entry.get("required", False),
                "foundational": entry.get("foundational", False),
                "scc_group_id": entry_to_scc.get(entry_id),
            })

        # Sort: ascending tier, then alphabetically by entry_id
        scored.sort(key=lambda x: (x["tier"], x["entry_id"]))
        return scored
