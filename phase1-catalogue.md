# Phase 1 Catalogue — PBCPB Unification

Generated: 2026-04-25

---

## 1.1 pbcpb — Primary Language, Runtime, Entry Points

**Language:** Python 3.13 (confirmed by __pycache__ .cpython-313.pyc files)
**Runtime:** CLI scripts via `python3 scripts/<name>.py`, test runner via pytest 9.0.2
**No web server, no daemon** — pure CLI/library system

**Entry Points:**
| Script | Entry Point | CLI Usage |
|---|---|---|
| scripts/validate_playbook.py | `main()` | `python3 scripts/validate_playbook.py <playbook.json>` |
| scripts/validate_semantic.py | `main()` | `python3 scripts/validate_semantic.py <playbook.json>` |
| scripts/generate_scaffold.py | `main()` | `python3 scripts/generate_scaffold.py <output.json>` |
| scripts/update_playbook.py | `main()` | `python3 scripts/update_playbook.py` |
| scripts/update_validation.py | (print-only, no functional entry) | dev-only migration script |
| scripts/execution_log.py | `main()` | `python3 scripts/execution_log.py list|show|latest` |
| scripts/complexity_gate.py | `main()` | `python3 scripts/complexity_gate.py classify|verify <playbook.json>` |
| scripts/checkpoint_manager.py | `main()` | `python3 scripts/checkpoint_manager.py save|verify|list|get` |
| scripts/show_handoff.py | `main()` | `python3 scripts/show_handoff.py --phase N` |

**Library Modules (imported, not CLI):**
| Module | Purpose |
|---|---|
| scripts/compilation/constants.py | Shared constants (model defaults, complexity limits) |
| scripts/compilation/context_budget.py | Token estimation for context_load |
| scripts/compilation/model_fallback.py | Model fallback chain resolution |
| scripts/compilation/system_prompt.py | System prompt assembly from playbook |
| scripts/__init__.py | Package init |

**Data files:**
- `playbook-creator-playbook.json` — main playbook (JSON database)
- `templates/output-schema.json` — JSON Schema for validation
- `templates/role-mapping.json` — role → agent mapping
- `prompts/playbook-updater.md` — LLM prompt template
- `docs/` — development history and usage docs
- `KB-SYSTEM-MANUAL.md` — KB operator manual

---

## 1.2 pbcpb-dify — Primary Language, Runtime, Entry Points

**Language:** Python 3.13 (same as pbcpb)
**Runtime:** Same CLI pattern. Plus Dify MCP server as external runtime dependency.

Identical script/module set plus:
- `DIFY-KB-GUIDE.md` — Operator guide for Dify RAG workflow
- `KB-STRUCTURE.md` — Markdown scaffold template for Dify dataset population
- `MIGRATION-NOTES.md` — Documents all changes from pbcpb to pbcpb-dify

**MCP Tool:** `mcp__dify-cognitive-kb__cognitive-research-kb-dify` (external, not part of codebase)

---

## 1.3 Feature Inventory (pbcpb base)

| Name | Entry Point | Expected Behavior |
|---|---|---|
| validate_playbook | scripts/validate_playbook.py | Structural + schema validation of playbook JSON; exits 0=PASS, 1=FAIL |
| validate_semantic | scripts/validate_semantic.py | Semantic consistency (role refs, FM phase refs, phase ordering); exits 0/1 |
| generate_scaffold | scripts/generate_scaffold.py | Produces valid skeleton playbook.json with all required fields + TODOs |
| update_playbook | scripts/update_playbook.py | Idempotently adds agent_config/system_prompt_auto/context_budget fields to existing playbook |
| execution_log | scripts/execution_log.py | Create/write/read/list execution log records from playbook runs |
| complexity_gate | scripts/complexity_gate.py | classify: score phases/roles/CCCs → simple/moderate/complex/structured; verify: check actual vs. expected |
| checkpoint_manager | scripts/checkpoint_manager.py | SHA-256 checksum-based artifact checkpoint across session boundaries |
| show_handoff | scripts/show_handoff.py | Print handoff files and next-phase context for a given phase number |
| system_prompt (lib) | scripts/compilation/system_prompt.py | Assemble system prompt from playbook + loaded files + behavioral profile |
| context_budget (lib) | scripts/compilation/context_budget.py | Token estimation for context_load sizing |
| model_fallback (lib) | scripts/compilation/model_fallback.py | Fallback chain resolution when primary model unavailable |
| constants (lib) | scripts/compilation/constants.py | Shared constants: model defaults, complexity limits, token heuristics |

---

## 1.4 Existing KB Access Abstraction Layer in pbcpb

**None exists in pbcpb.** The KB access is documented in `KB-SYSTEM-MANUAL.md` as a set of CLI skill conventions (`kb-harvest`, `kb-sync`, `kb-validate`, `kb-route`) implemented elsewhere (in ~/.claude/skills/). The pbcpb codebase itself has **no KB query code** — it only references KB via:
- `knowledge_base` JSON field in playbook structure (schema + population_strategy)
- `phase_kb_mapping` field (maps phases to KB layers)
- `skill_activation` field (references which skill to invoke)
- `validate_playbook.py` checks `kb_status` in handoff (counters only)

There is no Python module for KB access in either codebase.

---

## 1.5 Delta Files Between pbcpb and pbcpb-dify

**Files only in pbcpb-dify (additions):**
- `DIFY-KB-GUIDE.md` — Dify operator manual
- `KB-STRUCTURE.md` — Dify markdown scaffold template
- `MIGRATION-NOTES.md` — migration record from pbcpb to pbcpb-dify

**Files only in pbcpb (removals in dify):**
- `KB-SYSTEM-MANUAL.md` — replaced by DIFY-KB-GUIDE.md

**Files that differ:**
- `docs/README.md` — dify version references dify_kb section
- `docs/USAGE.md` — dify version uses phase_mcp_guidance
- `playbook-creator-playbook.json` — knowledge_base → dify_kb, phase_kb_mapping → phase_mcp_guidance
- `prompts/playbook-updater.md` — knowledge_base → dify_kb, kb_status removed
- `scripts/compilation/test_integration.py` — dify_kb and phase_mcp_guidance test variants
- `scripts/generate_scaffold.py` — knowledge_base → dify_kb, phase_kb_mapping → phase_mcp_guidance
- `scripts/update_playbook.py` — dify-specific update logic for dify_kb section
- `scripts/validate_playbook.py` — dify version validates dify_kb + phase_mcp_guidance instead of knowledge_base + phase_kb_mapping
- `templates/output-schema.json` — knowledge_base schema → dify_kb schema

---

## 1.6 Delta Categorization

### (a) Dify-Specific Additions → move into RAG_MCP adapter module

- `DIFY-KB-GUIDE.md` — move to `docs/adapters/rag-mcp-guide.md`
- `KB-STRUCTURE.md` — move to `docs/adapters/rag-mcp-kb-structure.md`
- `MIGRATION-NOTES.md` — move to `docs/adapters/rag-mcp-migration-notes.md`
- `dify_kb` section in playbook JSON — becomes RAG_MCP adapter config schema
- `phase_mcp_guidance` field — becomes RAG_MCP adapter routing hint
- Dify-specific test variants in test_integration.py — move to adapter-specific test file

### (b) General Improvements Applicable to All Backends → apply to pbcpb base

- Simplified KB architecture concept (topic-areas instead of complex layer/schema/bridge) — inform JSON_DB adapter simplification
- `KB-STRUCTURE.md` content-convention guidance (one concept per file, headings, size limits) — applicable to MARKDOWN_FOLDER adapter guidance
- MCP guidance annotation pattern (`explicit` | `natural` | `none`) — generalized to per-adapter query hints

### (c) Removals/Regressions → exclude from merge

- Removal of `kb_status` from handoff (regression — the original pbcpb had useful tracking)
- Removal of complex population_strategy (regression for JSON_DB users who need seeding strategy)
- Simplified validation in dify's validate_playbook.py skips knowledge_base structural checks — exclude

---

## 1.7 Master-Index Dependency Graph

pbcpb has NO master-index.json file. The `knowledge_base` section in the playbook JSON references a `directory_structure` and `layers` but there is no actual master-index.json in the pbcpb codebase itself (it lives in the juce-agent KB at /home/myuser/agents/juce-agent/playbookdata/).

**Dependency graph for playbook-creator-playbook.json schema sections:**

Nodes (top-level fields):
```
roles → checklists (role names used in items)
failure_modes → checklists (FM-IDs referenced in compilation.failure_modes_relevant)
metrics → checklists (MET-IDs referenced in handoff.metrics_snapshot.collect)
cross_cutting_concerns → checklists (phases_applied list)
phase_kb_mapping ← checklists (one entry per checklist phase)
skill_activation ← checklists (one entry per checklist phase)
knowledge_base → (no intra-field deps)
context_preservation → checklists (files referenced in handoff.context_update)
```

**Cycle detection result:** NO cycles. The dependency graph is a DAG.
- `checklists` is the central node with in-degree from roles, failure_modes, metrics, CCCs
- `phase_kb_mapping` and `skill_activation` have in-degree from checklists
- No SCC groups found

**SCC result:** None — proceed to scoring with DAG algorithm.

---

## Summary

| Dimension | pbcpb | pbcpb-dify |
|---|---|---|
| Language | Python 3.13 | Python 3.13 |
| KB backend | Local JSON files (via kb-skills) | Dify RAG via MCP |
| KB abstraction | None (skill-based convention) | None (MCP tool convention) |
| Entry points | 9 CLI scripts + 4 library modules | Same + Dify-specific docs |
| Unique additions | KB-SYSTEM-MANUAL.md | DIFY-KB-GUIDE.md, KB-STRUCTURE.md, MIGRATION-NOTES.md |
| Core scripts changed | 5 (generate_scaffold, update_playbook, validate_playbook, test_integration, output-schema) | — |
| Regressions in dify | kb_status tracking removed, population_strategy removed | — |
