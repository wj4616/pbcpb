# MIGRATION-NOTES.md

pbcpb → pbcpb-dify migration record. Documents every removed component, its Dify replacement, and rationale.

## Overview

pbcpb-dify replaces the legacy local JSON knowledge base system with Dify RAG accessed via MCP (`mcp__dify-cognitive-kb__cognitive-research-kb-dify`). Knowledge is now stored as markdown files, uploaded to Dify manually, and queried at runtime through MCP instead of maintained as a local JSON file hierarchy.

---

## Removed Components

### Phase 2: KB Architecture → Dify KB Architecture

| Field | Old | New |
|---|---|---|
| Purpose | Design local KB layers, schemas, bridge, population strategy | Design Dify dataset structure, markdown conventions, MCP query guidance |
| Output | `kb-architecture.md`, `entry-schema.json`, `bridge-schema.json`, `population-strategy.md`, `directory-structure.md` | `dify-kb-spec.md` |
| Key task removed | "Define knowledge layers" (local layer/schema design) | Replaced with "Define Dify KB topic coverage" |
| Key task removed | "Define entry schema" (JSON entry format) | Removed — Dify manages structure |
| Key task removed | "Define bridge layer" (subjective→technical JSON mapping) | Removed — bridge is now a KB content concern, not a schema concern |

**Rationale:** The legacy KB system required designing and maintaining a complex JSON schema per domain. Dify manages storage and retrieval; pbcpb-dify only needs to specify what topic areas the KB should cover and how markdown content should be organized.

---

### Phase 3: KB Bootstrapping → Dify KB Scaffold Generation

| Field | Old | New |
|---|---|---|
| Purpose | Create directory tree, seed placeholder JSON entries, harvest content, create master-index.json + manifests, populate kb-registry.json | Produce KB-STRUCTURE.md markdown scaffold for manual population and Dify upload |
| Output | `kb/` directory tree, `master-index.json`, per-layer `manifest.json`, `kb-registry.json`, placeholder entries, harvested entries, bridge entries, `search-terms.json`, `harvest-log.json`, `validation-report.md` | `KB-STRUCTURE.md` |
| Items removed | Create KB directory tree | Removed — no local KB directory |
| Items removed | Register KB layers (kb-registry.json) | Removed — Dify manages the registry |
| Items removed | Seed placeholder entries | Removed — no local placeholder files |
| Items removed | Seeding milestone gate | Removed |
| Items removed | Harvest initial content from research documents | Removed — content gathered manually as markdown |
| Items removed | Generate web harvest search terms | Removed — no automated harvesting |
| Items removed | Execute web harvest (kb-harvest) | Removed — no automated harvesting |
| Items removed | Create bridge entries | Removed — bridge is KB content, not a schema file |
| Items removed | Validate file paths and schema conformance | Removed — Dify validates its own content |
| Items removed | Phase gate: KB bootstrapped and populated | Simplified to: KB-STRUCTURE.md produced |

**Rationale:** The bootstrapping phase was entirely infrastructure for the legacy local KB. With Dify, knowledge gathering is a human process (collect markdown, upload to Dify) not an automated agent process. The agent's role is to produce a scaffold guide, not build and populate a file system.

---

### `knowledge_base` JSON section → `dify_kb`

| Field | Old | New |
|---|---|---|
| `complexity` | flat / multi-layer / bridge | Removed |
| `layers` | Array of layer definitions | Removed |
| `entry_schema` | JSON schema for entries | Removed |
| `bridge_schema` | JSON schema for bridge entries | Removed |
| `population_strategy.placeholder_seeding` | Strategy for seeding empty entries | Removed |
| `population_strategy.harvesting_sources` | Web harvest backends | Removed |
| `population_strategy.quality_threshold` | Confidence score threshold | Removed |
| `population_strategy.max_urls_per_session` | Harvest rate limiting | Removed |
| `population_strategy.curation_rules` | Curation workflow | Removed |
| `population_strategy.sync_rules` | kb-sync rules | Removed |
| `directory_structure` | Folder layout spec | Removed |
| → `mcp_tool` | — | `mcp__dify-cognitive-kb__cognitive-research-kb-dify` |
| → `dataset_description` | — | Human-readable description of KB content |
| → `content_structure` | — | Markdown folder conventions for gathering |
| → `query_guidance` | — | When to invoke MCP explicitly vs. rely on natural behavior |

---

### `phase_kb_mapping` → `phase_mcp_guidance`

| Field | Old | New |
|---|---|---|
| Type | `{ phase_N: [kb_layer_names] }` | `{ phase_N: "explicit" \| "natural" \| "none" }` |
| Purpose | Map phases to local KB layers for scoped queries | Map phases to MCP query guidance level |

**Rationale:** Local KB layer scoping is no longer relevant. The guidance now specifies whether a phase should explicitly invoke MCP, rely on natural invocation, or skip KB queries entirely.

---

### `KB-SYSTEM-MANUAL.md` → `DIFY-KB-GUIDE.md`

The full KB system manual (kb-harvest, kb-sync, kb-validate, kb-route, entry lifecycle, manifests, master-index, confidence scoring, bridge system) has been replaced by `DIFY-KB-GUIDE.md` which covers Dify dataset setup, markdown upload workflow, and MCP tool usage.

---

### `scripts/generate_scaffold.py`

Removed `knowledge_base` section (population_strategy with harvesting_sources, quality_threshold, max_urls_per_session; directory_structure; kb_registry). Replaced with `dify_kb` section. `phase_kb_mapping` replaced with `phase_mcp_guidance`.

---

### `templates/output-schema.json`

`knowledge_base` schema definition (with harvesting, kb_registry, kb_status validation) replaced with `dify_kb` schema. `phase_kb_mapping` schema replaced with `phase_mcp_guidance` enum schema. `kb_status` field removed from handoff schema.

---

### `prompts/playbook-updater.md`

`knowledge_base` block in JSON template replaced with `dify_kb`. `kb_status` field removed from handoff template. `phase_kb_mapping` replaced with `phase_mcp_guidance`.

---

## Ambiguous MCP Trigger Points

The following playbook locations have been annotated with MCP guidance comments where it is hard to determine whether the agent will trigger retrieval naturally. Review after running an initial playbook to determine if explicit invocation is needed:

1. **Phase 2, Task: Define phase-to-MCP-guidance mapping** — annotated with `<!-- MCP annotation: when in doubt about explicit vs natural, default to natural and add an inline comment -->`. The mapping produced here directly determines all subsequent MCP invocation behavior; review carefully after first playbook run.

2. **Phase 4: Process Architecture** — success criteria reference "Dify MCP guidance mapping" — this is a light reference; natural behavior should suffice.

---

## What Was NOT Changed

- `scripts/compilation/system_prompt.py` — no KB references; unchanged
- All phases 0, 1, 4–15 except as noted above — core structure preserved
- `scripts/complexity_gate.py`, `scripts/execution_log.py`, `scripts/validate_playbook.py`, `scripts/validate_semantic.py` — no KB references; unchanged
- `scripts/checkpoint_manager.py` — no KB references; unchanged
- All test files — unchanged
- `templates/role-mapping.json` — no KB references; unchanged
