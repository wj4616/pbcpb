# Playbook Creator Configuration Enhancement

**Date:** 2026-04-02
**Status:** Approved for Implementation

---

## Summary

Add configuration task to Phase 0 of playbook-creator-playbook.json to establish:
1. Output playbook save location (`~/playbooks/` default, configurable)
2. External data source permissions (explicit item-by-item consent)

---

## Problem

The playbook creator lacks explicit configuration for:
- Where output playbooks should be saved
- Whether external data sources (KBs, other playbooks, references) can be pulled

This led to hardcoded path assumptions and unclear permission boundaries.

---

## Solution

### New Task: "[Coordinator] — Establish Configuration"

**Position:** First task in Phase 0, before scope/complexity analysis

**Description:**
```
Ask the user to establish runtime configuration:

1. OUTPUT LOCATION
   - Default: ~/playbooks/<playbook-name>/
   - Override: User specifies different path
   - If directory exists: create ~/playbooks/<playbook-name>-v2/ (or next available)
   - Never merge or replace existing content

2. EXTERNAL DATA SOURCES
   - List each potential source:
     * Knowledge base: Pull from [path]? (yes/no)
     * Other playbooks: Pull from [path]? (yes/no)
     * References: Pull from [path]? (yes/no)
   - Record all decisions in scope.md
   - Only pull what user explicitly approved

Output: scope.md with configuration section documenting all decisions.
```

**Output:** `scope.md` (with configuration section)

**Owner:** Coordinator

---

### Gate Condition Addition

Add to Phase 0 gate conditions:
```
- Configuration established (output location + external data decisions)
- No hardcoded paths in subsequent phases
```

---

### Cross-Cutting Concern Addition

Add to `cross_cutting_concerns` array:

```json
{
  "id": "CCC-CONFIG",
  "title": "Path Configuration Compliance",
  "description": "All file operations use configured paths from Phase 0. No hardcoded external paths.",
  "enforcement_method": "gate_check",
  "enforcement_rule": "Every phase that reads external files must reference paths from scope.md configuration section.",
  "minimum_phases": 1,
  "phases_applied": ["Phase 0"]
}
```

---

### Context Preservation Update

Add to `context_preservation.rules`:
```
- Configuration decisions (output location, external data) from scope.md are ALWAYS loaded
- If scope.md is missing configuration section, halt and request Phase 0 completion
```

---

## Files Modified

| File | Change |
|------|--------|
| `playbook-creator-playbook.json` | Add configuration task to Phase 0, update gate, add cross-cutting concern |

---

## Implementation Steps

1. Add new task to Phase 0 `items` array (first position)
2. Add gate condition for configuration
3. Add `CCC-CONFIG` to `cross_cutting_concerns` array
4. Update `context_preservation.rules` array
5. Update `phase_summary` for Phase 0 to mention configuration

---

## Testing

- Verify Phase 0 gate fails if configuration section missing from scope.md
- Verify external data sources are not accessed without explicit approval
- Verify output saves to correct location (default or override)
- Verify directory conflict creates new folder (v2, v3, etc.)