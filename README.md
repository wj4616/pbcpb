# PBCPB — Playbook Creator Playbook Builder (Unified)

## SECTION 1 — System Overview

### Source Projects

| Project | Location | KB Backend |
|---|---|---|
| pbcpb (original) | ~/Documents/pbcpb-superseded/ | Local JSON file hierarchy |
| pbcpb-dify | ~/Documents/pbcpb-dify/ | Dify RAG via MCP server |
| **pbcpb (unified)** | **~/Documents/pbcpb/** | **Pluggable — config-driven** |

### Merge Rationale

The two source projects were functionally identical except for how they accessed
the knowledge base. pbcpb-dify replaced the JSON file KB with Dify RAG, but this
required duplicating the codebase rather than adding a configuration switch.

The unified system extracts KB access behind a 3-method adapter interface, so both
backends (and two others) coexist under a single codebase. Switching backends requires
only a config file edit — no code changes, no rebuild.

### Unified Target

~/Documents/pbcpb/ — this directory — is the single canonical PBCPB implementation.

All playbook operations (validate, generate_scaffold, show_handoff, execution_log,
checkpoint_manager, complexity_gate) work regardless of which KB backend is active.
The KB adapter is the only variable.

### Supported KB Backend Types

| adapter_type | Backend | populate() | Description |
|---|---|---|---|
| `JSON_DB` | Local JSON files | Writes directly | Original pbcpb KB — fully offline |
| `RAG_MCP` | Dify via MCP tool | Returns manifest | pbcpb-dify backend — cloud KB |
| `MARKDOWN_FOLDER` | User skill | Delegates to skill | Custom markdown-based KB |
| `CUSTOM_API` | HTTP API | POST (hard halt on failure) | Configurable external API |

Exact-string requirement: adapter_type values are case-sensitive. RAGMCP,
markdown-folder, etc. raise ConfigError at bind() time.

### Supported Role System Types

| role_type | Description |
|---|---|
| `MULTI_AGENT` | Executed by a multi-agent swarm with a linked_agent binding |
| `HUMAN` | Executed manually by a human; linked_agent is optional |
| `AI_ASSISTED` | Human+AI collaboration; linked_agent binds the AI component |

Mixed configurations (any combination of role types) coexist without conflict.
null linked_agent is always valid — it means the role is human-executed.

---

## Reference Architecture Orientation

### POSIX File-Descriptor Pattern

AdapterSession.bind(config_path) is the fd-open equivalent. Once bound, all KB
operations go through the session handle — no direct access to the concrete adapter
after bind(). Just as you never manipulate file internals directly, business logic
never imports concrete adapter modules.

### JDBC Connection-String Selection

adapter_type in pbcpb.config.json selects the backend, exactly like a JDBC URL
selects the driver. The calling code is identical regardless of backend. Switching
from JSON_DB to RAG_MCP requires only a config edit.

### TLS Handshake Pattern

bind() validates and negotiates everything upfront. If any config value is invalid
(wrong adapter_type string, missing skill_ref, bad role_type), ConfigError is raised
before the session handle is returned. No partially-initialized session exists — you
either get a fully bound session or an error.

### Spring-DI Dependency Injection

Business logic depends on AdapterSession (the interface), never on RagMcpAdapter,
JsonDbAdapter, etc. (the implementations). Concrete adapter modules are imported only
inside session.py's _instantiate_adapter() method. This is the CALLER_INVARIANCE
constraint: changing the backend never requires touching business logic.

---

## SECTION 2 — KB Adapter Module

Implemented in: kb_adapter/

### Three-Method Interface

All adapters expose:

```
query(query_string, filters=None) → list[QueryResult]
    Returns: [{ entry_id, content, metadata, source_adapter }]
    Raises: AdapterIOError (recoverable: True, 60s timeout)

populate(content, tier, metadata=None) → PopulateResult
    Returns discriminated union — MUST switch on .kind before consuming:
        kind="write_status"  → JSON_DB, MARKDOWN_FOLDER (writes occurred)
            { kind, success, written_count, errors }
        kind="manifest"      → RAG_MCP only (no Dify writes)
            { kind, manifest_path, items: [{entry_id, target_location, payload}] }
    Raises: AdapterIOError (recoverable: True) or ConfigError for CUSTOM_API failure

scan_gaps(schema_definition) → list[GapResult]
    Returns: [{ gap_id, location, type, schema_node }]
    gap_id MUST resolve to entry.id in schema_definition (namespace coherence)
    type ∈ { missing | placeholder | incomplete }
    Raises: AdapterIOError (recoverable: True)
```

### Per-Adapter Behavior

**RAG_MCP:**
- query(): requires live MCP connection; raises AdapterIOError in stub mode
- populate(): NEVER writes to Dify; returns kind="manifest" only
- scan_gaps(): classifies entries by required flag (missing vs placeholder)
- Connection config: mcp_tool_name (required), dataset_name, timeout

**MARKDOWN_FOLDER:**
- All 3 methods delegate to skill_ref subprocess
- skill_ref MUST be present in config — ConfigError raised at bind() if absent
- Skill protocol: `<skill_ref> <method> --input '<json>'` → JSON stdout
- Connection config: folder_path, timeout

**JSON_DB:**
- All 3 methods implemented directly against local JSON file hierarchy
- populate(): creates entry JSON file + updates master-index.json
- scan_gaps(): detects missing, placeholder (TODO content), incomplete (required fields)
- Connection config: kb_root (required), default_layer, timeout

**CUSTOM_API:**
- All 3 methods via HTTP POST to configured endpoints
- populate() failure = hard ConfigError halt (not silent skip)
- Connection config: base_url (required), query_path, populate_path, scan_gaps_path,
  api_key, api_key_header, method, timeout

### Example Config Snippets

See docs/adapters/ for full operator guides per adapter.

```json
// JSON_DB (default, fully offline)
{ "kb_adapter": { "adapter_type": "JSON_DB",
    "connection": { "kb_root": "./kb" } } }

// RAG_MCP (Dify via MCP)
{ "kb_adapter": { "adapter_type": "RAG_MCP",
    "connection": { "mcp_tool_name": "mcp__dify-cognitive-kb__cognitive-research-kb-dify",
                    "dataset_name": "my-kb" } } }

// MARKDOWN_FOLDER (requires skill_ref)
{ "kb_adapter": { "adapter_type": "MARKDOWN_FOLDER",
    "skill_ref": "./skills/my-kb-skill.sh",
    "connection": { "folder_path": "./kb-markdown" } } }

// CUSTOM_API (hard halt on populate failure)
{ "kb_adapter": { "adapter_type": "CUSTOM_API",
    "connection": { "base_url": "https://api.example.com/kb",
                    "api_key": "sk-..." } } }
```

### AdapterSession — Single Construction Path

```python
# ONLY way to get an adapter:
session = AdapterSession.bind("pbcpb.config.json")
# or:
session = AdapterSession.bind()  # uses PBCPB_CONFIG_PATH env var

# Business logic holds session, never concrete adapter:
results = session.query("my question")
result = session.populate(content, tier=1, metadata={...})
# MUST switch on result.kind before consuming:
if result.kind == "write_status":
    print(f"Wrote {result.written_count} entries")
elif result.kind == "manifest":
    print(f"Manifest at {result.manifest_path}")
```

### Error Handling

```python
from kb_adapter import ConfigError, AdapterIOError

# ConfigError — raised at bind() time, recoverable: False
try:
    session = AdapterSession.bind("bad-config.json")
except ConfigError as e:
    print(e.detail)  # { error_class, cause, offending_field, adapter_type, recoverable }

# AdapterIOError — raised during method calls, recoverable: True
try:
    results = session.query("test")
except AdapterIOError as e:
    print(e.detail)  # { error_class, cause, adapter_type, recoverable }
    # Retry or degrade gracefully
```

---

## SECTION 3 — Role System Module

Implemented in: role_system/

### Config Schema

```json
{
  "role_system": {
    "syntax_mode": "@name",
    "syntax_pattern": "@{name}",
    "roles": [
      { "placeholder_name": "@architect", "role_type": "MULTI_AGENT", "linked_agent": null },
      { "placeholder_name": "@reviewer",  "role_type": "HUMAN",       "linked_agent": null },
      { "placeholder_name": "@assistant", "role_type": "AI_ASSISTED",  "linked_agent": "claude-agent" }
    ]
  }
}
```

### Three Valid Config Variants

```json
// (a) Multi-agent: all roles MULTI_AGENT
{ "roles": [
    { "placeholder_name": "@planner",  "role_type": "MULTI_AGENT", "linked_agent": "planner-v1" },
    { "placeholder_name": "@executor", "role_type": "MULTI_AGENT", "linked_agent": "executor-v1" },
    { "placeholder_name": "@reviewer", "role_type": "MULTI_AGENT", "linked_agent": "reviewer-v1" }
] }

// (b) Human-only: all roles HUMAN
{ "roles": [
    { "placeholder_name": "@lead",    "role_type": "HUMAN", "linked_agent": null },
    { "placeholder_name": "@analyst", "role_type": "HUMAN", "linked_agent": null }
] }

// (c) AI-assisted: mixed HUMAN + AI_ASSISTED
{ "roles": [
    { "placeholder_name": "@human",     "role_type": "HUMAN",       "linked_agent": null },
    { "placeholder_name": "@assistant", "role_type": "AI_ASSISTED",  "linked_agent": null }
] }
```

### Usage

```python
from role_system import RoleSystem
import json

config = json.loads(open("pbcpb.config.json").read())
role_sys = RoleSystem.from_config(config["role_system"])

# Look up a role
role = role_sys.get_role("@architect")
print(role.role_type)         # "MULTI_AGENT"
print(role.linked_agent)      # None (valid)
print(role.resolve_executor()) # "[multi-agent] @architect → (unbound)"

# Update linked_agent (config-edit equivalent, no rebuild)
role_sys.bind_agent("@architect", "planner-agent-v2")

# Mixed types coexist
human_roles = role_sys.roles_by_type("HUMAN")
ai_roles = role_sys.roles_by_type("AI_ASSISTED")
```

### Rules

- Placeholders defined at design-time (placeholder_name)
- linked_agent bound at runtime via config — config edit only, no rebuild
- null linked_agent = human executes manually — NOT an error
- Mixed types coexist without conflict
- Pseudo-values (HUMAN_ONLY, MULTIAGENT, ai-assisted) raise ConfigError at bind() time

---

## SECTION 4 — Bootstrap Module

Implemented in: bootstrap/

### 5-Step CoT Bootstrap Sequence

```
Step 5.1  scan_gaps      → raw gap list [ { gap_id, location, type, schema_node } ]
Step 5.2  tier_scoring   → tier assignments + SCC detection via Kosaraju
Step 5.3  populate_core  → Tier 1 gaps populated (text KBs) / manifest items (RAG_MCP)
Step 5.4  defer_tier2+   → bootstrap/deferred-backlog.json written
Step 5.5  dify_manifest  → bootstrap/dify-upload-manifest.json (RAG_MCP only)
```

### Tier Scoring Rules

```
Tier 0 (opt-in):    in_degree >= bootstrap_tier_zero_threshold (default 0 = disabled)
Tier 1 (core):      in_degree >= 2  OR  required: true  OR  foundational: true  OR  SCC member
Tier 2 (important): in_degree == 1, no required flag
Tier 3+ (enrichment): leaf node, zero dependents, no required flag
Sort: ascending tier, then alphabetically by gap_id within tier
```

### Cycle Handling

Kosaraju SCC algorithm runs on every bootstrap. SCCs (cycles) are deterministically
handled: all SCC member entries are jointly promoted to Tier 1 with a scc_group_id
recorded for audit. CyclicSchemaError raised only on algorithmic failure. Never silent.

### Output Files

**deferred-backlog.json** (always written):
```json
{
  "generated_at": "2026-04-25T12:00:00+00:00",
  "tier_limit_used": 1,
  "deferred_count": 5,
  "deferred": [
    { "gap_id": "entry-002", "location": "kb/general/entry-002.json",
      "type": "missing", "tier": 2, "schema_node": {} }
  ]
}
```

**dify-upload-manifest.json** (written only when adapter_type == RAG_MCP):
```json
{
  "generated_at": "2026-04-25T12:00:00+00:00",
  "adapter_type": "RAG_MCP",
  "item_count": 3,
  "items": [
    { "entry_id": "e1", "target_location": "my-kb/core/e1",
      "payload": { "content": "...", "tier": 1, "metadata": {} } }
  ],
  "instructions": "Upload each item's payload.content to Dify at target_location."
}
```

### Re-run Semantics

scan_gaps runs fresh every time (idempotent). Existing deferred-backlog.json is read
for context but not trusted as authoritative. Fresh backlog written with updated
generated_at. Safe to re-run at any time.

### Usage

```python
from kb_adapter import AdapterSession
from bootstrap import BootstrapRunner
import json

config = json.loads(open("pbcpb.config.json").read())
session = AdapterSession.bind("pbcpb.config.json")
runner = BootstrapRunner(session, config, pbcpb_root=".")
result = runner.run()
print(result["summary"])
# { adapter_type, total_gaps, is_dag, scc_groups, tier_counts,
#   tier1_populated, deferred_count }
```

---

## Running Tests

```bash
cd ~/Documents/pbcpb

# New adapter/bootstrap/role system tests (31 tests, covers all 14 verification items)
python3 -m pytest tests/test_kb_adapter.py -v

# Original pbcpb functionality tests (64 tests, JSON_DB path validation)
python3 -m pytest scripts/compilation/ -v

# All tests combined
python3 -m pytest tests/ scripts/compilation/ -v
```
