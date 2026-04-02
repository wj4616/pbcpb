# Playbook Creator Playbook v3 Design Specification

> **Status:** Design approved (pending implementation)
> **Date:** 2026-03-31
> **Scope:** 9 friction points from JUCE VST playbook execution
> **Audits:** 5 rounds, 37 issues found and resolved

---

## 1. Problem Statement

The playbook-creator-playbook v2 (2037 lines, 15 phases) was executed once to produce a JUCE VST3 plugin development playbook. That execution revealed 15 friction points. Six were fixed in the v2.1 compilation block enhancement. Nine remain and are addressed by this spec:

| # | Friction Point | Status | Severity |
|---|---------------|--------|----------|
| FP1 | No KB bootstrapping task | **v3** | Critical |
| FP2 | Phase 8 too heavy (10 tasks, 15 context files) | **v3** | High |
| FP3 | Validation entirely manual | Fixed in v2.1 | High |
| FP4 | Pilot testing impractical for AI agent context | **v3** | Medium |
| FP5 | 6 structural fixes needed that audits missed | Fixed in v2.1 | High |
| FP6 | Handoff chain inconsistencies pervasive | Fixed in v2.1 | High |
| FP7 | `failure_modes` array empty | **v3** | High |
| FP8 | Context budget fields decorative | Fixed in v2.1 | Medium |
| FP9 | Role switching overhead | **v3** | Medium |
| FP10 | Cross-cutting concerns are plain strings | **v3** | Medium |
| FP11 | Output playbook schema underspecified | Fixed in v2.1 | High |
| FP12 | No progressive KB population | **v3** | High |
| FP13 | Session boundaries poorly managed | Fixed in v2.1 | Medium |
| FP14 | No metrics measurement tooling | **v3** | High |
| FP15 | No complexity governance | **v3** | Medium |

---

## 2. Design Constraints

- Linear sequential phase model preserved
- Single-agent default preserved (`role-based-single-agent`)
- All 6 existing roles preserved
- Compilation block structure preserved (all existing fields intact)
- Gate structure preserved (gate_conditions, blocker_examples, handoff)
- Task format preserved (title with [Role], owner, description, output, conditional)
- Output schema backward-compatible where possible (2 breaking changes with migration path)
- Token efficiency maintained (estimated ~39% size increase, justified by failure mode seeding)

---

## 3. Phase Structure: v2 to v3 Mapping

v3 has 17 phases (0-16). Net change: +2 (KB Bootstrapping, Phase 8 split).

| v3 # | Name | v2 # | Change Type |
|------|------|------|-------------|
| 0 | Commission & Scoping | 0 | Modified (+1 task, +1 gate condition) |
| 1 | Domain Research & Process Discovery | 1 | Unchanged |
| 2 | KB Architecture | 2 | Modified (handoff redesigned for Phase 3) |
| 3 | **KB Bootstrapping** | — | **NEW** (solves FP1, FP12) |
| 4 | Process Architecture | 3 | Unchanged |
| 5 | Role Engineering | 4 | Modified (+agent_assignment, +role_context) |
| 6 | Task Engineering | 5 | Modified (CCC weaving uses enforcement_method) |
| 7 | Output Configuration | 6 | Unchanged |
| 8 | Metrics & KPI Definition | 7 | Modified (metrics gain `id` field) |
| 9 | **JSON Assembly** | 8 (tasks 0-1) | **SPLIT** (solves FP2) |
| 10 | **JSON Validation & Consistency** | 8 (tasks 2-9) | **SPLIT** (solves FP2) |
| 11 | Quality Audit — Gap Analysis | 9 | Modified (CCC audit uses phases_applied) |
| 12 | Quality Audit — Stress Testing | 10 | Unchanged |
| 13 | Stakeholder Review & Iteration | 11 | Unchanged |
| 14 | **Pilot / Structured Dry-Run** | 12 | **Restructured** (solves FP4) |
| 15 | Documentation & Version Control | 13 | Modified (+1 task: metrics report) |
| 16 | Continuous Improvement | 14 | Unchanged (better bootstrapped with seeded FMs) |

### Session Strategy (v3)

| Session | Phases | Rationale |
|---------|--------|-----------|
| 1 | 0-1 | Scoping + research (tightly coupled) |
| 2 | 2-3 | KB architecture + bootstrapping (design then build) |
| 3 | 4 | Process architecture (fresh eyes on structure) |
| 4 | 5-6 | Role + task engineering (roles inform tasks) |
| 5 | 7-8 | Output config + metrics |
| 6 | 9 | JSON assembly (heaviest context load, dedicated session) |
| 7 | 10 | JSON validation (fresh eyes on assembled JSON) |
| 8 | 11-12 | Gap analysis + stress testing (audit pair) |
| 9 | 13 | Stakeholder review (human gate) |
| 10 | 14 | Pilot / dry-run |
| 11 | 15-16 | Documentation + improvement |

---

## 4. Change Specifications

### 4.1 Phase 0: Complexity Classifier (solves FP15)

**Addresses:** FP15 (no complexity governance)

**New task** (inserts after task 6 "Identify related existing playbooks", before gate):

```json
{
  "title": "[Stakeholder] — Classify domain complexity",
  "owner": "[Stakeholder]",
  "description": "Answer three questions to set complexity guardrails for the creation process:\n\n1. PROCESS COMPLEXITY: How many distinct phases does the real-world process have?\n   - Simple (1-4 phases): single-skill workflow, linear steps\n   - Standard (5-10 phases): multi-skill workflow, some parallelism\n   - Complex (11+ phases): multi-discipline workflow, significant dependencies\n\n2. KNOWLEDGE COMPLEXITY: How many distinct types of knowledge does the domain require?\n   - Flat (1 type): single reference layer, no translation needed\n   - Layered (2-3 types): multiple knowledge domains, some cross-referencing\n   - Bridged (4+ types): distinct vocabularies that need translation between them\n\n3. ROLE COMPLEXITY: How many distinct functional roles does the process need?\n   - Minimal (2 roles): one doer, one approver\n   - Standard (3-4 roles): specialized functions with handoffs\n   - Full (5+ roles): distinct disciplines with complex handoff chains\n\nRecord the complexity_profile in decisions-ledger.md:\n  process: simple|standard|complex\n  knowledge: flat|layered|bridged\n  roles: minimal|standard|full\n  overall: highest of the three dimensions\n\nThe overall classification sets advisory guardrails (not hard limits) for the rest of the creation process."
}
```

**Guardrail ranges by profile:**

| Parameter | Simple | Standard | Complex |
|-----------|--------|----------|---------|
| Target phases | 5-8 | 8-13 | 12-18 |
| Target tasks | 30-60 | 60-150 | 120-300 |
| KB complexity | flat | flat or layered | layered or bridged |
| Role count | 2-3 | 3-5 | 4-8 |
| CCC count | 2-3 | 4-7 | 6-12 |
| Metrics count | 3-5 | 5-10 | 8-20 |

**New gate condition** added to Phase 0 gate:

```
"Complexity profile documented in decisions-ledger.md (process, knowledge, roles, overall)"
```

`guardrail_checks` is a new optional array field on gate items. Unlike `gate_conditions` (which block), guardrail checks are advisory — the agent presents them to the human for acknowledgment but does not block advancement. The validation script validates that `guardrail_checks` is an array of strings if present, but does not enforce the checks.

**Exact `guardrail_checks` strings per gate:**

Phase 2 gate:
```json
"guardrail_checks": [
  "KB complexity level matches complexity_profile.knowledge dimension from Phase 0 — if flat domain has bridged KB design, or bridged domain has flat KB, confirm with [Stakeholder] before proceeding"
]
```

Phase 4 gate:
```json
"guardrail_checks": [
  "Phase count matches complexity_profile.process dimension from Phase 0 — simple: 5-8 phases, standard: 8-13, complex: 12-18 — if outside range, confirm with [Stakeholder] before proceeding"
]
```

Phase 5 gate:
```json
"guardrail_checks": [
  "Role count matches complexity_profile.roles dimension from Phase 0 — minimal: 2-3 roles, standard: 3-5, full: 4-8 — if outside range, confirm with [Stakeholder] before proceeding"
]
```

Phase 6 gate:
```json
"guardrail_checks": [
  "Task count matches complexity_profile.process dimension from Phase 0 — simple: 30-60 tasks, standard: 60-150, complex: 120-300 — if outside range, confirm with [Stakeholder] before proceeding"
]
```

Phase 8 gate:
```json
"guardrail_checks": [
  "Metrics count matches complexity_profile from Phase 0 — simple: 3-5 metrics, standard: 5-10, complex: 8-20 — if outside range, confirm with [Stakeholder] before proceeding"
]
```

Phase 10 gate (already specified in Section 4.7):
```json
"guardrail_checks": [
  "Total phases, tasks, roles, CCCs, and metrics are within complexity_profile guardrail ranges — if outside, confirm with [Stakeholder]"
]
```

---

### 4.2 Phase 2: KB Architecture Handoff Redesign (enables Phase 3)

**Addresses:** Handoff chain integrity for new Phase 3

Phase 2 content is unchanged. Only the gate handoff's `next_phase_context` changes to include full KB specification documents that Phase 3 needs:

**v2 handoff (current):**
```json
"next_phase_context": [
  "kb-architecture.md (summary — layer names and boundaries only)",
  "research/requirements.md",
  "research/cross-cutting-concerns.md",
  "scope.md",
  "constraints.md"
]
```

**v3 handoff (new):**
```json
"next_phase_context": [
  "kb-architecture.md (full)",
  "entry-schema.json",
  "bridge-schema.json (if applicable)",
  "population-strategy.md",
  "directory-structure.md",
  "research/domain-analysis.md (for KB harvesting)",
  "research/best-practices.md (for KB harvesting)",
  "research/cross-cutting-concerns.md"
]
```

**v2 excluded_files updated:**
```json
"excluded_files": [
  "scope.md and constraints.md — KB Bootstrapping does not need them; they re-enter context at Phase 4",
  "research/requirements.md — needed at Phase 4, not Phase 3"
]
```

Phase 3 (KB Bootstrapping) gate then restores the slim handoff for Phase 4 (Process Architecture), preserving the v2 context chain for all downstream phases.

---

### 4.3 Phase 3: KB Bootstrapping (NEW) (solves FP1, FP12)

**Addresses:** FP1 (no KB bootstrapping task), FP12 (no progressive KB population)

**Full phase specification:**

```json
{
  "title": "Phase 3: KB Bootstrapping",
  "purpose": "Execute the KB architecture designed in Phase 2. Create the directory tree, seed placeholders, harvest initial entries from Phase 1 research. The KB starts here and grows progressively — full curation is the user's responsibility after playbook completion.",
  "compilation": {
    "context_load": [
      "kb-architecture.md (full)",
      "entry-schema.json",
      "bridge-schema.json (if applicable)",
      "population-strategy.md",
      "directory-structure.md",
      "research/domain-analysis.md (for KB harvesting)",
      "research/best-practices.md (for KB harvesting)",
      "research/cross-cutting-concerns.md",
      "decisions-ledger.md",
      "artifact-manifest.md"
    ],
    "role_mindset": "Builder \u2014 executing the KB blueprint from Phase 2. Mechanical precision, not creative design.",
    "objective": "Build the KB directory structure, seed placeholder entries, harvest initial entries from Phase 1 research documents",
    "pre_check": [
      "KB complexity decision documented with rationale",
      "Entry schema defined with all required fields",
      "Population pipeline defined",
      "Directory tree specified"
    ],
    "failure_modes_relevant": ["FM-001", "FM-014"],
    "agent_config": {
      "temperature": 0.2
    },
    "system_prompt_auto": {
      "role_definition": true,
      "phase_objective": true,
      "failure_modes": true,
      "pre_check_guidance": true,
      "context_files": true,
      "handoff_requirements": true
    },
    "context_budget": {
      "max_tokens": 64000,
      "priority": {
        "kb-architecture.md": 5,
        "entry-schema.json": 5,
        "bridge-schema.json": 5,
        "population-strategy.md": 5,
        "directory-structure.md": 5,
        "research/domain-analysis.md": 4,
        "research/best-practices.md": 3,
        "research/cross-cutting-concerns.md": 3,
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2
      }
    },
    "skill_preparation": "none"
  },
  "items": [
    {
      "title": "[Builder] — Create KB directory tree",
      "owner": "[Builder]",
      "description": "Create the exact directory structure specified in directory-structure.md.\n\nFor flat KB: create kb/ directory with README.md containing table of contents.\nFor multi-layer KB: create all layer directories, topic subdirectories, and _archive subdirectories per the specification.\n\nVerify: directory tree matches specification exactly. No missing directories, no extras.",
      "output": "kb/ directory"
    },
    {
      "title": "[Builder] — Seed placeholder entries",
      "owner": "[Builder]",
      "conditional": "Only if multi-layer KB was chosen in Phase 2",
      "description": "Create one placeholder entry per topic per layer using the entry-schema.json format.\n\nEach placeholder: status='placeholder', all required fields present, description contains guidance for what content should be harvested here.\n\nMinimum: 1 placeholder per topic per layer (as specified in population-strategy.md).\n\nVerify: every topic directory has at least one .json file with status='placeholder'.",
      "output": "kb/ placeholder entries"
    },
    {
      "title": "[Builder] — Harvest initial entries from Phase 1 research",
      "owner": "[Builder]",
      "conditional": "Only if multi-layer KB was chosen in Phase 2",
      "description": "Parse Phase 1 research documents (domain-analysis.md, best-practices.md, cross-cutting-concerns.md) and extract concrete, reusable knowledge into KB entries.\n\nHarvest rules:\n- Extract patterns, rules, parameters, constraints, and concrete examples\n- Skip narrative, opinions, and context-dependent advice\n- Each entry must stand alone (understandable without reading the source document)\n- Use entry-schema.json format with status='harvested'\n- Assign to the correct layer based on KB architecture domain boundaries\n\nIf replacing an existing playbook (see audits/existing-playbook-audit.md if it exists), also harvest relevant entries from the existing playbook's KB.\n\nTarget: at least 1 harvested entry per layer. More is better but quality over quantity.",
      "output": "kb/ harvested entries"
    },
    {
      "title": "[Builder] — Create master-index and per-layer manifests",
      "owner": "[Builder]",
      "description": "Create master-index.json: list all layers, entry counts per layer, status counts (placeholder/harvested/curated), last sync timestamp.\n\nFor multi-layer KB: create per-layer manifest.json listing all entries by topic with status.\n\nFor flat KB: create kb/README.md with table of contents listing all reference files.\n\nVerify: master-index counts match actual file counts in the directory tree.",
      "output": "kb/master-index.json, per-layer manifest.json files"
    },
    {
      "title": "[Coordinator] — Phase gate: KB bootstrapped",
      "owner": "[Coordinator]",
      "gate_conditions": [
        "KB directory structure exists per Phase 2 specification",
        "If flat KB: kb/ directory exists with README.md and table of contents",
        "If multi-layer: placeholder entries seeded (at least 1 per topic per layer)",
        "If multi-layer: at least 1 harvested entry per layer from Phase 1 research",
        "master-index.json exists and entry counts match actual files"
      ],
      "blocker_examples": [
        "Directory tree missing topic subdirectories — build from directory-structure.md",
        "Placeholder entries use wrong schema format — regenerate from entry-schema.json",
        "Zero harvested entries in a layer — Phase 1 research must contain at least something relevant to each layer, re-examine domain-analysis.md"
      ],
      "guardrail_checks": [
        "KB complexity level matches complexity_profile.knowledge dimension from Phase 0 — if flat domain has bridged KB design, or bridged domain has flat KB, confirm with [Stakeholder] before proceeding"
      ],
      "handoff": {
        "output_artifacts": [
          "kb/ directory (full tree)",
          "kb/master-index.json",
          "per-layer manifest.json files (if multi-layer)"
        ],
        "next_phase_context": [
          "kb-architecture.md (summary — layer names and boundaries only)",
          "research/requirements.md",
          "research/cross-cutting-concerns.md",
          "scope.md",
          "constraints.md"
        ],
        "excluded_files": [
          "Full KB specification docs (entry-schema.json, population-strategy.md, directory-structure.md) — Phase 4 only needs layer names for phase-to-KB mapping. Full docs re-enter context at Phase 8 gate for JSON Assembly.",
          "Research documents — key points captured in requirements.md and KB entries",
          "KB directory contents — built and indexed, referenced via master-index.json when needed"
        ],
        "kb_status": {
          "_note": "Populated at runtime by executing agent",
          "total_entries": 0,
          "harvested": 0,
          "placeholder": 0
        },
        "skill_validation": "none"
      }
    }
  ]
}
```

**`out_of_scope` update:**

Old: `"Building the actual knowledge base (the creator produces the KB specification, not the KB itself)"`

New: `"Full KB curation and ongoing maintenance (the creator bootstraps the KB with placeholders and initial harvesting; full curation is the user's responsibility)"`

---

### 4.4 Phase 5: Role System Enhancement (solves FP9)

**Addresses:** FP9 (role switching overhead)

All 6 roles preserved. Two new optional fields added to each role definition.

**New fields on `roles{}` entries:**

```json
"Coordinator": {
  "description": "Phase gates, tracking, status updates, blocker escalation, decisions ledger and artifact manifest maintenance",
  "role_context": "Track progress systematically. Verify conditions before advancing. Maintain decisions-ledger and artifact-manifest at every gate.",
  "defaults": {
    "model": "sonnet",
    "temperature": [0.2, 0.4]
  },
  "agent_assignment": "single"
},
"Researcher": {
  "description": "Domain research, best practices, SME knowledge, competitive analysis",
  "role_context": "Gather broadly, synthesize precisely. Cite sources. Distinguish facts from opinions. Flag gaps in knowledge.",
  "defaults": {
    "model": "sonnet",
    "temperature": [0.4, 0.7]
  },
  "agent_assignment": "single"
},
"Architect": {
  "description": "Phase structure, task granularity, role design, dependency mapping, template design",
  "role_context": "Design for clarity and separation. Every boundary must be justified. Every dependency must be explicit. Favor simplicity.",
  "defaults": {
    "model": "opus",
    "temperature": [0.3, 0.5]
  },
  "agent_assignment": "single"
},
"Builder": {
  "description": "Task titles/descriptions, JSON assembly, validation, implementation of fixes",
  "role_context": "Mechanical precision. Follow specifications exactly. Verify output matches input requirements. No creative interpretation during assembly.",
  "defaults": {
    "model": "sonnet",
    "temperature": [0.2, 0.4]
  },
  "agent_assignment": "single"
},
"Auditor": {
  "description": "Quality review, scenario walkthroughs, gap analysis, stress testing, failure mode cataloging, contamination testing, final verification before handoff",
  "role_context": "Binary yes/no judgments, no hedging. Find what is broken. Review with fresh eyes. Do not defend previous work.",
  "defaults": {
    "model": "opus",
    "temperature": [0.2, 0.3]
  },
  "agent_assignment": "single"
},
"Stakeholder": {
  "description": "Purpose, scope, constraints, success criteria, business decisions, final approval",
  "role_context": "Business alignment. Does this serve the commission? Are constraints respected? Would you trust this playbook to run unsupervised?",
  "defaults": {
    "model": "sonnet",
    "temperature": [0.3, 0.5]
  },
  "agent_assignment": "single"
}
```

**`agent_assignment` semantics:**
- `"single"` — one agent fills all roles (default, current behavior)
- Any other string — identifies which agent handles this role in a multi-agent system
- Non-"single" values only take effect when `workflow_model` is `"role-based-multi-agent"`. If `workflow_model` is `"role-based-single-agent"`, `agent_assignment` is ignored regardless of its value.

**`workflow_model` enum addition:**
- Add `"role-based-multi-agent"` as a valid value
- The creator playbook itself stays `"role-based-single-agent"`
- Output playbooks can use either value

**`out_of_scope` update:**

Old: `"Multi-agent orchestration (single-agent fills all roles)"`

New: `"Multi-agent orchestration of the creation process itself (the creator runs as single-agent; output playbooks may use role-based-multi-agent with per-role agent_assignment)"`

**System prompt generation update (`system_prompt.py`):**

When `system_prompt_auto.role_definition` is `true`, the prompt includes three sections in order:

1. `role.description` — what the role does (functional description)
2. `role.role_context` — how the role thinks (baseline activation prompt)
3. `compilation.role_mindset` — phase-specific thinking overlay

Desired output format:
```
## Your Role
{role.description}
{role.role_context}

## Phase Mindset
{compilation.role_mindset}
```

**Exact code changes in `system_prompt.py`:**

1. Line 64 — extract `role_context` alongside `description`:
```python
# Current:
if isinstance(role_def, dict):
    role_description = role_def.get("description", "")
else:
    role_description = role_def

# Change to:
if isinstance(role_def, dict):
    role_description = role_def.get("description", "")
    role_context = role_def.get("role_context", "")
else:
    role_description = role_def
    role_context = ""
```

2. Line 78 — insert `role_context` after `role_description`:
```python
# Current:
if flags.get("role_definition", True) and role_description:
    sections.append(f"{role_description}\n")

# Change to:
if flags.get("role_definition", True) and role_description:
    sections.append(f"{role_description}")
    if role_context:
        sections.append(f"{role_context}")
    sections.append("")
```

---

### 4.5 Phase 6: Structured Cross-Cutting Concerns (solves FP10)

**Addresses:** FP10 (cross-cutting concerns are plain strings with vague enforcement)

**`cross_cutting_concerns` array changes from strings to objects:**

```json
"cross_cutting_concerns": [
  {
    "id": "CCC-01",
    "title": "Quality Standard",
    "description": "Every produced playbook must be comprehensive enough that any team can execute it without ambiguity. Every task must have an owner. Every non-obvious task must have a description. Every phase must have a gate with explicit conditions. No placeholder content.",
    "enforcement_method": "checklist_items",
    "enforcement_rule": "Embed as a verification checklist item in task descriptions where this concern applies. The item must be a concrete yes/no check, not a restatement of the concern.",
    "minimum_phases": 3,
    "phases_applied": [6, 9, 10, 11, 12]
  },
  {
    "id": "CCC-02",
    "title": "Role Consistency",
    "description": "Roles defined at playbook start must be used consistently throughout all tasks. Every task title must start with [Role]. Roles cannot appear fewer than 3 times (orphaned) or reference undefined roles.",
    "enforcement_method": "gate_condition",
    "enforcement_rule": "Include role consistency verification as an explicit gate condition at phases where tasks are written or assembled.",
    "minimum_phases": 3,
    "phases_applied": [5, 6, 9, 10]
  },
  {
    "id": "CCC-03",
    "title": "Gate Enforcement",
    "description": "Phase gates are firewall points — nothing advances until all conditions are met. Each gate must list explicit conditions, blocker examples, and handoff blocks. Conditions must be verifiable, not subjective.",
    "enforcement_method": "compilation_precheck",
    "enforcement_rule": "Include gate completeness as a pre_check condition in compilation blocks for phases that define or validate gates.",
    "minimum_phases": 3,
    "phases_applied": [4, 6, 9, 10]
  },
  {
    "id": "CCC-04",
    "title": "Deliverable Tracking",
    "description": "Every task that produces output must name the file path. The artifact manifest tracks all files across all phases. Later phases reference earlier deliverables through handoff chains.",
    "enforcement_method": "task_description",
    "enforcement_rule": "Every task that produces a deliverable must have an 'output' field with the exact file path. The artifact-manifest.md must be updated at every gate.",
    "minimum_phases": 3,
    "phases_applied": [0, 6, 9, 15]
  },
  {
    "id": "CCC-05",
    "title": "Context Preservation",
    "description": "decisions-ledger.md, artifact-manifest.md, and metrics-tracker.md are persistent tracking files. decisions-ledger and artifact-manifest are loaded in every phase and updated at every gate. No decision rationale is silently lost across session boundaries.",
    "enforcement_method": "compilation_precheck",
    "enforcement_rule": "Verify decisions-ledger.md and artifact-manifest.md appear in every phase's context_load (except Phase 0). Verify both are updated at every gate.",
    "minimum_phases": 3,
    "phases_applied": [0, 6, 9, 10]
  }
]
```

**Valid `enforcement_method` values:**
- `checklist_items` — embed as verification checklist items in task descriptions
- `gate_condition` — add as explicit gate condition
- `compilation_precheck` — add as pre_check in compilation block
- `task_description` — embed in task description prose

**Phase 6 (Task Engineering) impact:**

The "Weave cross-cutting concerns into relevant tasks" task description gains concrete instruction:

```
For each CCC: apply its enforcement_method per its enforcement_rule.
Record which phases receive the CCC in the CCC's phases_applied array.
After weaving, every CCC must appear in at least minimum_phases phases.
```

**Phase 10 (JSON Validation) impact:**

The "Validate structural completeness" task description gains CCC validation:

```
Validate cross_cutting_concerns: every CCC object has id, title, description,
enforcement_method, enforcement_rule, minimum_phases. Each CCC's phases_applied
lists at least minimum_phases entries. CCC IDs are unique (CCC-NNN format).
enforcement_method is one of: checklist_items, gate_condition,
compilation_precheck, task_description.
```

**Phase 11 (Gap Analysis) impact:**

The "Are all cross-cutting concerns woven throughout?" audit now has machine-checkable data — compare `phases_applied` against `minimum_phases` instead of manual counting.

---

### 4.6 Phase 8: Metrics with IDs + Measurement Integration (solves FP14)

**Addresses:** FP14 (no metrics measurement tooling)

**Metric objects gain required `id` field:**

```json
{
  "id": "MET-01",
  "title": "Total Phases",
  "description": "Phases in the produced playbook",
  "type": "metric_integer",
  "category": "output_quality",
  "target": null,
  "measurement_method": "Count checklists[] array length"
}
```

**All 8 creator metrics with IDs:**

| ID | Title | Category | Collect At (v3 gate) |
|----|-------|----------|---------------------|
| MET-01 | Total Phases | output_quality | Phase 9 |
| MET-02 | Total Tasks | output_quality | Phase 9 |
| MET-03 | Tasks With Descriptions | output_quality | Phase 10 |
| MET-04 | Metrics Defined | output_quality | Phase 8 |
| MET-05 | Days to Complete | process | Phase 15 |
| MET-06 | Audit Issues Found | process | Phase 11, Phase 12 |
| MET-07 | Critical Issues at Pilot | process | Phase 14 |
| MET-08 | Pilot Completion Rate | domain_outcome | Phase 14 |

**New `metrics_snapshot` field on gate handoff blocks:**

```json
"handoff": {
  "output_artifacts": ["..."],
  "next_phase_context": ["..."],
  "metrics_snapshot": {
    "collect": ["MET-01", "MET-02"],
    "record_in": "metrics-tracker.md"
  }
}
```

Gates that have `metrics_snapshot`:

| Phase Gate | Metrics Collected |
|------------|------------------|
| Phase 8 | MET-04 |
| Phase 9 | MET-01, MET-02 |
| Phase 10 | MET-03 |
| Phase 11 | MET-06 |
| Phase 12 | MET-06 |
| Phase 14 | MET-07, MET-08 |
| Phase 15 | MET-05 |

**`metrics-tracker.md` initialization:**

Added to Phase 0's first task description:

```
Initialize metrics-tracker.md — empty, with header:
'# Metrics Tracker — record at every phase gate'
and columns: Metric | Phase | Value | Target | Date
```

**`metrics-tracker.md` in context_load:**

Added to `context_load` of phases whose gates have `metrics_snapshot` (Phases 8, 9, 10, 11, 12, 14, 15) with priority 1 (low — small file). NOT added to every phase.

**`context_preservation` update:**

Add third tracked file:

```json
"context_preservation": {
  "decisions_ledger": "decisions-ledger.md — ...",
  "artifact_manifest": "artifact-manifest.md — ...",
  "metrics_tracker": "metrics-tracker.md — running log of metric values collected at phase gates. Columns: Metric ID | Phase | Value | Target | Date",
  "rules": [
    "All three files are initialized in Phase 0 and updated at relevant gates",
    "decisions-ledger.md and artifact-manifest.md are always included in context_load — exempt from token optimization cuts",
    "metrics-tracker.md is included in context_load only for phases whose gates collect metrics",
    "At session breaks, verify all three files are saved and current before ending",
    "If context compaction occurs mid-session, these files serve as ground truth for recovering state"
  ]
}
```

**Phase 15 (Documentation) new task:**

```json
{
  "title": "[Coordinator] — Compile final metrics report",
  "owner": "[Coordinator]",
  "description": "Read metrics-tracker.md. For each metric: compare final value against target from the metrics[] array. Produce a summary table:\n\n| Metric | Target | Actual | Status |\n\nStatus: PASS (met target), MISS (below target), N/A (no target defined).\n\nInclude brief analysis: which metrics indicate process health, which indicate output quality, what to improve in the next run.",
  "output": "final/metrics-report.md"
}
```

---

### 4.7 Phases 9-10: JSON Assembly Split (solves FP2)

**Addresses:** FP2 (Phase 8 too heavy)

**Phase 9: JSON Assembly**

```json
{
  "title": "Phase 9: JSON Assembly",
  "purpose": "Assemble the complete output playbook JSON from all design documents. This phase focuses on assembly and syntax — structural validation happens in Phase 10.",
  "compilation": {
    "context_load": [
      "metrics-definition.md",
      "drafts/task-list-v0.1.md",
      "output-config.md",
      "scope.md",
      "constraints.md",
      "research/cross-cutting-concerns.md",
      "kb-architecture.md (full)",
      "entry-schema.json",
      "bridge-schema.json (if applicable)",
      "population-strategy.md",
      "directory-structure.md",
      "architecture/role-definitions.md",
      "architecture/phase-structure.md",
      "decisions-ledger.md",
      "artifact-manifest.md",
      "metrics-tracker.md"
    ],
    "role_mindset": "Builder \u2014 assembling JSON from source documents. Mechanical precision, no creative interpretation.",
    "objective": "Assemble the complete output playbook JSON with all 16 required top-level fields and validate syntax",
    "pre_check": [
      "At least one metric per category defined",
      "All metrics approved by Stakeholder"
    ],
    "failure_modes_relevant": ["FM-003", "FM-004", "FM-005", "FM-006", "FM-007", "FM-008", "FM-011", "FM-019"],
    "agent_config": {},
    "system_prompt_auto": {
      "role_definition": true,
      "phase_objective": true,
      "failure_modes": true,
      "pre_check_guidance": true,
      "context_files": true,
      "handoff_requirements": true
    },
    "context_budget": {
      "max_tokens": 64000,
      "priority": {
        "metrics-definition.md": 5,
        "drafts/task-list-v0.1.md": 5,
        "output-config.md": 5,
        "kb-architecture.md": 5,
        "architecture/role-definitions.md": 5,
        "architecture/phase-structure.md": 5,
        "research/cross-cutting-concerns.md": 4,
        "entry-schema.json": 4,
        "scope.md": 3,
        "constraints.md": 3,
        "bridge-schema.json": 3,
        "population-strategy.md": 3,
        "directory-structure.md": 3,
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2,
        "metrics-tracker.md": 1
      }
    },
    "skill_preparation": "none"
  },
  "items": [
    {
      "title": "[Builder] — Assemble the playbook JSON structure",
      "owner": "[Builder]",
      "description": "Required top-level fields: title, version, description, workflow_model, roles, scope, cross_cutting_concerns, knowledge_base, checklists, metrics, usage_instructions, failure_modes, phase_kb_mapping, skill_activation, router, context_preservation.\n\nChecklist item fields: title (required, starts with [Role]), owner (required, must match [Role] in title), description (optional), conditional (optional), output (optional).\n\nGate item additional fields: gate_conditions (required array), blocker_examples (required array), handoff (required object with output_artifacts, next_phase_context, excluded_files).\n\nCompilation block fields: context_load, role_mindset, objective, pre_check, failure_modes_relevant, agent_config, system_prompt_auto, context_budget, skill_preparation."
    },
    {
      "title": "[Builder] — Validate JSON syntax",
      "owner": "[Builder]",
      "description": "Parse without errors. No trailing commas, unescaped characters, mismatched brackets. All string values properly escaped.\n\nVerification: python3 -c \"import json; json.load(open('drafts/playbook-v0.1.json'))\""
    },
    {
      "title": "[Coordinator] — Phase gate: JSON assembled and syntactically valid",
      "owner": "[Coordinator]",
      "gate_conditions": [
        "JSON parses without errors",
        "All 16 required top-level fields present",
        "All checklists have title, purpose, compilation, and non-empty items array",
        "Every item has title and owner fields"
      ],
      "blocker_examples": [
        "JSON has trailing comma after last array element — parser rejects it, fix syntax",
        "Missing required top-level field — check the 16-field checklist"
      ],
      "metrics_snapshot": {
        "collect": ["MET-01", "MET-02"],
        "record_in": "metrics-tracker.md"
      },
      "handoff": {
        "output_artifacts": [
          "drafts/playbook-v0.1.json"
        ],
        "next_phase_context": [
          "drafts/playbook-v0.1.json (full)",
          "research/requirements.md",
          "research/cross-cutting-concerns.md"
        ],
        "excluded_files": [
          "All source documents — consolidated into JSON",
          "KB specification docs — embedded in JSON knowledge_base section"
        ],
        "skill_validation": "none"
      }
    }
  ]
}
```

**Phase 10: JSON Validation & Consistency**

```json
{
  "title": "Phase 10: JSON Validation & Consistency",
  "purpose": "Validate the assembled JSON for structural completeness, role consistency, KB schema integrity, compilation block consistency, and cross-cutting concern coverage. Fresh session with lighter context.",
  "compilation": {
    "context_load": [
      "drafts/playbook-v0.1.json",
      "research/requirements.md",
      "research/cross-cutting-concerns.md",
      "decisions-ledger.md",
      "artifact-manifest.md",
      "metrics-tracker.md"
    ],
    "role_mindset": "Auditor \u2014 validating with fresh eyes. The JSON was assembled in a previous session; now verify it independently.",
    "objective": "Validate structural completeness, role consistency, KB schema, compilation blocks, summary views, failure modes, and cross-cutting concerns",
    "pre_check": [
      "JSON parses without errors",
      "All 16 required top-level fields present"
    ],
    "failure_modes_relevant": ["FM-003", "FM-004", "FM-005", "FM-006", "FM-007", "FM-008", "FM-009", "FM-010", "FM-011"],
    "agent_config": {
      "temperature": 0.25
    },
    "system_prompt_auto": {
      "role_definition": true,
      "phase_objective": true,
      "failure_modes": true,
      "pre_check_guidance": true,
      "context_files": true,
      "handoff_requirements": true
    },
    "context_budget": {
      "max_tokens": 64000,
      "priority": {
        "drafts/playbook-v0.1.json": 5,
        "research/requirements.md": 5,
        "research/cross-cutting-concerns.md": 5,
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2,
        "metrics-tracker.md": 1
      }
    },
    "skill_preparation": "none"
  },
  "items": [
    {
      "title": "[Auditor] — Validate structural completeness",
      "owner": "[Auditor]",
      "description": "Every checklist has title, purpose, and non-empty items array. Every item has a title starting with [Role]. Every item has an owner field matching the [Role] in title. Phase numbering is sequential. metrics[] is not empty. All required top-level fields present and non-empty.\n\nValidate cross_cutting_concerns: every CCC object has id, title, description, enforcement_method, enforcement_rule, minimum_phases. Each CCC's phases_applied lists at least minimum_phases entries. CCC IDs are unique (CCC-NNN format). enforcement_method is one of: checklist_items, gate_condition, compilation_precheck, task_description."
    },
    {
      "title": "[Auditor] — Validate [Role] consistency",
      "owner": "[Auditor]",
      "description": "Extract all [Role] references from task titles. Compare against roles defined in the roles{} section. No typos, no orphaned roles (appear < 3 times), no undefined roles. Every owner field matches the [Role] in its task title."
    },
    {
      "title": "[Auditor] — Validate KB schema section",
      "owner": "[Auditor]",
      "description": "If knowledge_base.layers is non-empty: every layer has name, domain boundary, authority score, separation rule. Entry schema has all required fields. Bridge schema (if present) has all required fields. Population strategy is complete. Directory structure is buildable.\n\nIf knowledge_base is minimal/flat: at minimum a description of the reference format and location."
    },
    {
      "title": "[Auditor] — Validate compilation blocks on every phase",
      "owner": "[Auditor]",
      "description": "Every checklist entry has a compilation block with all required fields. context_load always includes decisions-ledger.md and artifact-manifest.md (except Phase 0). pre_check conditions are verifiable (not subjective). role_mindset is defined. objective is a single clear line. failure_modes_relevant references valid FM-IDs (or is empty for v1.0). Each phase's context_load is consistent with the previous phase's next_phase_context."
    },
    {
      "title": "[Auditor] — Validate summary views match gate sources",
      "owner": "[Auditor]",
      "description": "phase_kb_mapping entries must be consistent with next_phase_context in gate handoffs. skill_activation entries must match skill_validation field in gate handoffs. Flag any inconsistencies as errors."
    },
    {
      "title": "[Auditor] — Validate failure_modes section",
      "owner": "[Auditor]",
      "description": "failure_modes array exists (may be empty for v1.0). If populated: every entry has all required fields (id, symptom, root_cause, fix, prevention, phase, severity, source). severity values valid: crash | error | degraded | cosmetic. phase values reference actual phases. FM-IDs in compilation blocks reference existing entries. No duplicate FM-IDs."
    },
    {
      "title": "[Auditor] — Validate metrics section",
      "owner": "[Auditor]",
      "description": "Every metric has id (MET-NNN), title, description, type, category, measurement_method. Metric IDs are unique. At least one metric per category (process, output_quality, domain_outcome). If metrics_snapshot fields exist in gate handoffs, all referenced metric IDs exist in metrics[]."
    },
    {
      "title": "[Auditor] — Manual review of assembled JSON",
      "owner": "[Auditor]",
      "description": "Read through entire playbook as a user would: Do tasks flow logically within each phase? Are descriptions consistent in tone and detail level? Would you know how to complete every task from title + description alone? Are metrics measurable with the tools/access defined?"
    },
    {
      "title": "[Coordinator] — Phase gate: JSON valid and structurally complete",
      "owner": "[Coordinator]",
      "gate_conditions": [
        "All structural validation checks pass",
        "All [Role] references are consistent and defined",
        "KB schema section is valid and complete (or explicitly minimal)",
        "Every phase has a compilation block with all required fields",
        "Compilation context_load is consistent with previous phase's next_phase_context",
        "failure_modes section valid (empty or well-formed)",
        "Summary views (phase_kb_mapping, skill_activation) match gate handoffs",
        "All CCC objects have required fields and phases_applied meets minimum_phases",
        "All metric IDs are unique and metrics_snapshot references are valid",
        "Manual review passed"
      ],
      "blocker_examples": [
        "A [Role] appears in 2 task titles but is not in the roles{} section — undefined role, fix",
        "phase_kb_mapping says Phase 3 uses 'dsp-kb' but no gate handoff references that layer — reconcile",
        "CCC-02 has phases_applied with only 2 entries but minimum_phases is 3 — weave into additional phase"
      ],
      "guardrail_checks": [
        "Total phases, tasks, roles, CCCs, and metrics are within complexity_profile guardrail ranges — if outside, confirm with [Stakeholder]"
      ],
      "metrics_snapshot": {
        "collect": ["MET-03"],
        "record_in": "metrics-tracker.md"
      },
      "handoff": {
        "output_artifacts": [
          "drafts/playbook-v0.1.json"
        ],
        "next_phase_context": [
          "drafts/playbook-v0.1.json (full)",
          "research/requirements.md",
          "research/cross-cutting-concerns.md"
        ],
        "excluded_files": [
          "All intermediate drafts — consolidated into JSON",
          "Validation logs — issues fixed"
        ],
        "skill_validation": "none"
      }
    }
  ]
}
```

---

### 4.8 Phase 14: Structured Dry-Run Protocol (solves FP4)

**Addresses:** FP4 (pilot testing impractical for AI agent context)

**Phase purpose updated:**

Old: `"Run the playbook on a real project to find issues that design review can't catch."`

New: `"Validate the playbook through structured dry-run scenarios. A real pilot run is preferred when practical; the structured dry-run is the minimum requirement when real execution is impractical within the creation context."`

**Draft version progression:**

The output playbook draft evolves through the creation process:
- `drafts/playbook-v0.1.json` — produced by Phase 9 (Assembly), validated by Phase 10
- `drafts/playbook-v0.2.json` — updated after Phase 11-12 audit fixes (if fixes needed)
- `drafts/playbook-v0.3.json` — updated after Phase 13 stakeholder feedback (if changes needed)

Phase 14 references the latest draft. If fewer revision cycles occur (e.g., no stakeholder changes), the filename will differ. The agent should load the highest-versioned draft available.

**Full task list:**

```json
{
  "title": "Phase 14: Pilot / Structured Dry-Run",
  "purpose": "Validate the playbook through structured dry-run scenarios. A real pilot run is preferred when practical; the structured dry-run protocol is the minimum requirement when real execution is impractical within the creation context.",
  "compilation": {
    "context_load": [
      "drafts/playbook-v{latest}.json",
      "decisions-ledger.md",
      "artifact-manifest.md",
      "metrics-tracker.md"
    ],
    "role_mindset": "Coordinator/Auditor \u2014 executing scenarios and documenting friction. Do not rationalize problems away.",
    "objective": "Run structured dry-run for 2+ scenarios (or real pilot), document friction, incorporate feedback, get Auditor sign-off",
    "pre_check": [
      "All stakeholder feedback addressed",
      "Final approval given",
      "JSON valid",
      "Success criteria from Phase 0 satisfied"
    ],
    "failure_modes_relevant": ["FM-012"],
    "agent_config": {},
    "system_prompt_auto": {
      "role_definition": true,
      "phase_objective": true,
      "failure_modes": true,
      "pre_check_guidance": true,
      "context_files": true,
      "handoff_requirements": true
    },
    "context_budget": {
      "max_tokens": 64000,
      "priority": {
        "drafts/playbook-v{latest}.json": 5,
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2,
        "metrics-tracker.md": 1
      }
    },
    "skill_preparation": "none"
  },
  "items": [
    {
      "title": "[Coordinator] — Define dry-run scenario matrix",
      "owner": "[Coordinator]",
      "description": "Define 2-3 scenarios with concrete parameters:\n\n1. MINIMAL CASE: smallest possible project in this domain. Exercises the fewest tasks and conditional paths.\n2. TYPICAL CASE: representative mid-complexity project. Exercises the most common path.\n3. COMPLEX CASE (optional): high-complexity variant. Exercises conditional tasks, all KB layers, maximum dependency chains.\n\nFor each scenario: name, key parameters, expected phase count, expected task count, which conditional tasks should activate, which KB layers should be needed.",
      "output": "testing/scenario-matrix.md"
    },
    {
      "title": "[Auditor] — Phase-by-phase walkthrough for all scenarios",
      "owner": "[Auditor]",
      "description": "For each scenario in the matrix, walk through every phase:\n- Can each task be completed given this scenario's parameters? Y/N\n- What would the task produce for this scenario?\n- Are there any blockers, ambiguities, or missing information?\n- Does the gate make sense for this scenario?\n\nDocument findings per scenario per phase.",
      "output": "testing/scenario-walkthroughs.md"
    },
    {
      "title": "[Auditor] — Verify conditional task logic across scenarios",
      "owner": "[Auditor]",
      "description": "For each conditional task in the playbook:\n- Does the condition evaluate correctly for each scenario? Y/N\n- Are there scenarios where the condition is ambiguous? Y/N\n- Are there missing conditional tasks (tasks that should be conditional but aren't)? Y/N"
    },
    {
      "title": "[Auditor] — Trace handoff chain for all scenarios",
      "owner": "[Auditor]",
      "description": "For each scenario, trace the full handoff chain from Phase 0 to final phase:\n- Does each phase's next_phase_context provide everything the next phase needs? Y/N per transition\n- Are there context_load items that no previous phase produces? Y/N\n- Does the context budget allow loading all critical files at every phase? Y/N\n\nThis is the most mechanical check — trace every file reference through the chain.",
      "output": "testing/handoff-chain-trace.md"
    },
    {
      "title": "[Auditor] — Document friction and catalog failure modes",
      "owner": "[Auditor]",
      "description": "Compile all findings from walkthroughs into:\n\n1. Friction log: questions that arose, ambiguities found, tasks that need more detail, tasks in wrong order, missing tasks.\n\n2. Failure mode catalog: for every issue discovered, create FM entry (symptom, root_cause, fix, prevention, phase, severity, source). Source should be 'dry-run-{scenario-name}'.",
      "output": "testing/pilot-friction.md, testing/failure-modes-pilot.md"
    },
    {
      "title": "[Builder] — Incorporate feedback into playbook",
      "owner": "[Builder]",
      "description": "Common updates: clarifying descriptions, reordering tasks, adjusting scope, fixing gate conditions, updating KB spec based on dry-run findings. Add new failure modes to failure_modes[] array. Update failure_modes_relevant in affected phase compilation blocks."
    },
    {
      "title": "[Builder] — Re-validate and produce final JSON",
      "owner": "[Builder]",
      "description": "Run the structural validation script. Save validated output as final/playbook-v1.0.json.",
      "output": "final/playbook-v1.0.json"
    },
    {
      "title": "[Auditor] — Final verification before handoff",
      "owner": "[Auditor]",
      "description": "The Auditor is always the last role to touch the playbook before it leaves the creator process.\n\nVerify: all dry-run fixes are clean — no new contradictions. JSON still validates. KB specification still buildable after updates. No regression from earlier audit fixes. Gate conditions accurate after task modifications.\n\nIf issues found: return to [Builder] for fixes, then re-verify. Do not advance.",
      "output": "audits/final-verification.md"
    },
    {
      "title": "[Coordinator] — Phase gate: Dry-run complete, feedback incorporated, Auditor verified",
      "owner": "[Coordinator]",
      "gate_conditions": [
        "Structured dry-run completed for 2+ scenarios OR pilot run completed on a real project",
        "Scenario walkthroughs documented with Y/N per task per scenario",
        "Handoff chain traced and verified for all scenarios",
        "Friction documented",
        "Failure modes from dry-run cataloged (or 'none found' documented)",
        "Feedback incorporated into playbook",
        "Updated JSON validated",
        "[Auditor] final verification passed — no regressions, no new contradictions"
      ],
      "blocker_examples": [
        "Only 1 scenario tested — minimum 2 required for meaningful coverage",
        "Handoff chain trace found broken links — fix before proceeding",
        "Auditor found regression from dry-run fixes — return to Builder",
        "Failure modes from dry-run not cataloged with FM-IDs — format properly before proceeding"
      ],
      "metrics_snapshot": {
        "collect": ["MET-07", "MET-08"],
        "record_in": "metrics-tracker.md"
      },
      "handoff": {
        "output_artifacts": [
          "final/playbook-v1.0.json",
          "testing/scenario-matrix.md",
          "testing/scenario-walkthroughs.md",
          "testing/handoff-chain-trace.md",
          "testing/pilot-friction.md",
          "testing/failure-modes-pilot.md",
          "audits/final-verification.md"
        ],
        "next_phase_context": [
          "final/playbook-v1.0.json"
        ],
        "excluded_files": [
          "All dry-run execution artifacts — findings captured in friction log and failure modes, applied to JSON",
          "Previous draft versions"
        ],
        "skill_validation": "none"
      }
    }
  ]
}
```

---

### 4.9 Failure Mode Seeding (solves FP7)

**Addresses:** FP7 (empty failure_modes array)

**20 failure modes seeded from JUCE VST playbook execution:**

```json
"failure_modes": [
  {
    "id": "FM-001",
    "symptom": "KB architecture designed in Phase 2 but no directory, placeholders, or entries exist after creation completes",
    "root_cause": "No phase executes the KB blueprint — Phase 2 designs it, but building was out of scope",
    "fix": "Execute Phase 3 (KB Bootstrapping) to create directory tree, seed placeholders, harvest initial entries",
    "prevention": "Phase 3 gate verifies KB directory exists with populated entries before advancing",
    "phase": "2",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-002",
    "symptom": "Cross-cutting concern appears in only 1-2 phases despite 3+ minimum requirement",
    "root_cause": "Weaving instruction is vague — 'must appear in 3+ phases' without specifying enforcement method",
    "fix": "Check each CCC's phases_applied array, add enforcement to additional phases until minimum_phases met",
    "prevention": "CCC objects have enforcement_method and phases_applied fields; Phase 10 validates count >= minimum_phases",
    "phase": "6",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-003",
    "symptom": "Task title uses [Human] but owner field says 'human' — role validation fails",
    "root_cause": "Inconsistent bracket syntax between title and owner field during manual JSON assembly",
    "fix": "Normalize all owner fields to bracket syntax matching title: owner must be '[Role]' not 'Role' or 'role'",
    "prevention": "Validation script checks owner field matches [Role] in title exactly",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-004",
    "symptom": "KB layers defined as JSON array instead of named keys — agents cannot look up layers by name",
    "root_cause": "Entry schema says 'layers' but doesn't specify whether it's an array or object",
    "fix": "Restructure layers as named keys in the knowledge_base object, or as array of objects with required 'name' field",
    "prevention": "KB schema validation task explicitly checks layer structure format",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-005",
    "symptom": "Failure mode entries missing required fields (title or description) — FM references are broken",
    "root_cause": "FM entry schema not enforced during manual assembly",
    "fix": "Add all required fields to each FM entry: id, symptom, root_cause, fix, prevention, phase, severity, source",
    "prevention": "Validation script checks all 8 required FM fields, FM-ID pattern, and no duplicates",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-006",
    "symptom": "Metrics missing ID fields — cannot cross-reference from tasks or gates",
    "root_cause": "Metric schema did not require an ID field",
    "fix": "Assign sequential MET-NNN IDs to all metrics",
    "prevention": "Validation script checks metric ID uniqueness and MET-NNN format for v3+ playbooks",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-007",
    "symptom": "Cross-cutting concerns stored as plain strings — no enforcement metadata, no tracking of where they're applied",
    "root_cause": "CCC schema only required a description string, not structured enforcement data",
    "fix": "Convert each CCC string to object with id, title, description, enforcement_method, enforcement_rule, minimum_phases, phases_applied",
    "prevention": "Validation script checks CCC object structure, phases_applied count >= minimum_phases",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-008",
    "symptom": "Phase N+1 context_load references file not in Phase N's next_phase_context — handoff chain gap",
    "root_cause": "Handoff blocks assembled manually without systematic chain verification",
    "fix": "Trace full handoff chain and add missing files to next_phase_context or remove from context_load",
    "prevention": "Validation script checks handoff chain consistency (check 16); dry-run protocol traces chains for all scenarios",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-009",
    "symptom": "Gate handoff skill_validation field references wrong phase's skill — 10 mismatches found",
    "root_cause": "Gates were copied between phases and skill field not updated",
    "fix": "Audit every gate's skill_validation against the phase it hands off TO, not the current phase",
    "prevention": "Stress testing scenario traces skill activation chain; validation script checks skill_activation consistency",
    "phase": "12",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-010",
    "symptom": "KB layer directories missing from context_load — 12 directories not loadable",
    "root_cause": "KB directories referenced in phase_kb_mapping but not in compilation block context_load",
    "fix": "Add all referenced KB directories to relevant phase context_load arrays",
    "prevention": "Validation script cross-checks phase_kb_mapping against context_load; stress test verifies KB access per phase",
    "phase": "12",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-011",
    "symptom": "All 13+ context_load files at priority 5 — budget system cannot make intelligent loading decisions",
    "root_cause": "Priorities assigned uniformly without considering which files are core vs reference-only",
    "fix": "Differentiate priorities: 5 for core inputs, 4 for section-specific, 3 for reference, 1-2 for persistent tracking files",
    "prevention": "Phase 9 and 10 split into assembly (heavy context) and validation (light context); priorities differentiated per file importance",
    "phase": "9",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-012",
    "symptom": "Pilot testing is a mental walkthrough, not real execution — misses runtime issues",
    "root_cause": "Real pilot requires multiple sessions outside the creation context, which is impractical",
    "fix": "Use structured dry-run protocol with scenario matrix, phase-by-phase walkthrough, handoff chain trace",
    "prevention": "Phase 14 gate accepts either structured dry-run (2+ scenarios) OR real pilot; dry-run protocol is systematic and documented",
    "phase": "14",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-013",
    "symptom": "Task description says 'build X' without method, specs, or verification — task is unexecutable",
    "root_cause": "Task granularity standard not enforced during task writing",
    "fix": "Add WHAT/HOW/SPECS/VERIFY structure to all non-obvious task descriptions",
    "prevention": "Auditor review in Phase 6 uses binary checklist: does each description answer what, how, and how to verify?",
    "phase": "6",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-014",
    "symptom": "4-layer bridged KB designed for a domain that could use a flat folder — massive over-engineering",
    "root_cause": "No complexity assessment before KB design; defaults to maximum complexity",
    "fix": "Re-evaluate using Phase 2 Task 1 complexity questions; switch to flat if warranted",
    "prevention": "Phase 0 complexity classifier sets knowledge dimension; Phase 2 gate guardrail_checks flag mismatches",
    "phase": "2",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-015",
    "symptom": "Playbook scope covers all variants (effects + instruments + synthesizers) instead of common case with conditionals",
    "root_cause": "Scope definition didn't distinguish primary path from variant paths",
    "fix": "Define primary scope (common case), mark variant-specific tasks as conditional",
    "prevention": "Phase 0 scope task explicitly requires primary/variant distinction; complexity classifier informs scope breadth",
    "phase": "0",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-016",
    "symptom": "Metrics defined with targets but never measured during execution — metrics are decorative",
    "root_cause": "No measurement task in gates, no tracking file, no collection mechanism",
    "fix": "Add metrics_snapshot to gate handoff blocks; initialize metrics-tracker.md in Phase 0",
    "prevention": "metrics_snapshot.collect lists metric IDs to record at each gate; metrics-tracker.md persists across sessions",
    "phase": "8",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-017",
    "symptom": "failure_modes array empty after first execution — no guidance when things go wrong",
    "root_cause": "Cold start problem: v1.0 playbooks have no execution history to draw failure modes from",
    "fix": "Seed failure_modes with entries from first execution; update failure_modes_relevant in affected phases",
    "prevention": "v3 creator ships with 20 seeded FMs from JUCE execution; Phase 16 catalogs new FMs from each run",
    "phase": "16",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-018",
    "symptom": "Phase N requires Phase M's output but Phase M requires Phase N's — circular dependency",
    "root_cause": "Dependency map not validated for cycles during process architecture",
    "fix": "Break the cycle by reordering phases or splitting the shared dependency into a prerequisite phase",
    "prevention": "Phase 4 dependency mapping task requires DAG proof (no circular dependencies); validated in architecture review",
    "phase": "4",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-019",
    "symptom": "project-state.json referenced in tasks and gate handoffs but never created by any task",
    "root_cause": "File referenced before a creation task was written for it",
    "fix": "Add initialization task or remove all references",
    "prevention": "Artifact provenance validation (check 17) catches files in context_load not produced by any prior phase",
    "phase": "9",
    "severity": "error",
    "source": "juce-vst-playbook-v0.1-execution"
  },
  {
    "id": "FM-020",
    "symptom": "Context compaction at session boundary loses critical details — decisions and rationale silently dropped",
    "root_cause": "Session strategy doesn't account for LLM context window compaction behavior",
    "fix": "Ensure all critical decisions are persisted in decisions-ledger.md before session breaks",
    "prevention": "Session strategy aligns breaks to phase gates where decisions-ledger is updated; context_preservation rules enforce persistence",
    "phase": "7",
    "severity": "degraded",
    "source": "juce-vst-playbook-v0.1-execution"
  }
]
```

**`failure_modes_relevant` mapping (v3 phase numbers):**

| v3 Phase | failure_modes_relevant |
|----------|----------------------|
| 0 | ["FM-015"] |
| 1 | [] |
| 2 | ["FM-001", "FM-014"] |
| 3 | ["FM-001", "FM-014"] |
| 4 | ["FM-018"] |
| 5 | [] |
| 6 | ["FM-002", "FM-013"] |
| 7 | ["FM-020"] |
| 8 | ["FM-016"] |
| 9 | ["FM-003", "FM-004", "FM-005", "FM-006", "FM-007", "FM-008", "FM-011", "FM-019"] |
| 10 | ["FM-003", "FM-004", "FM-005", "FM-006", "FM-007", "FM-008", "FM-009", "FM-010", "FM-011"] |
| 11 | ["FM-002"] |
| 12 | ["FM-009", "FM-010", "FM-012"] |
| 13 | [] |
| 14 | ["FM-012"] |
| 15 | [] |
| 16 | ["FM-017"] |

---

## 5. Schema & Validation Changes

### 5.1 Output Schema (output-schema.json) Changes

**Breaking changes (require migration for v2 output playbooks):**

1. `cross_cutting_concerns` items: string OR object (backward-compatible via oneOf)
2. `metrics[].id`: new field (optional in schema, enforced by validator for version >= 3)

**Non-breaking additions (with JSON Schema fragments):**

3\. `roles{}.*.agent_assignment` — add to role object variant properties:
```json
"agent_assignment": {
  "type": "string",
  "description": "Agent identifier for multi-agent systems. 'single' = one agent fills all roles (default). Any other string identifies which agent handles this role. Only takes effect when workflow_model is 'role-based-multi-agent'.",
  "default": "single"
}
```

4\. `roles{}.*.role_context` — add to role object variant properties:
```json
"role_context": {
  "type": "string",
  "description": "Baseline activation prompt for this role. Included in system prompt between description and role_mindset."
}
```

5\. `workflow_model` enum — add value:
```json
"workflow_model": {
  "type": "string",
  "enum": ["human-in-the-loop", "fully-autonomous", "human-directed", "role-based-single-agent", "role-based-multi-agent"]
}
```

6\. Gate items: `guardrail_checks` — add to checklist item properties:
```json
"guardrail_checks": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Advisory checks presented to the human at gate. Unlike gate_conditions, these do not block advancement."
}
```

7\. Handoff blocks: `metrics_snapshot` — add to handoff properties:
```json
"metrics_snapshot": {
  "type": "object",
  "required": ["collect", "record_in"],
  "properties": {
    "collect": {
      "type": "array",
      "items": { "type": "string", "pattern": "^MET-\\d{2}$" },
      "minItems": 1,
      "description": "Metric IDs to record at this gate"
    },
    "record_in": {
      "type": "string",
      "description": "File to append metric values to"
    }
  }
}
```

8\. Handoff blocks: `kb_status` — add to handoff properties:
```json
"kb_status": {
  "type": "object",
  "properties": {
    "total_entries": { "type": "integer", "minimum": 0 },
    "harvested": { "type": "integer", "minimum": 0 },
    "placeholder": { "type": "integer", "minimum": 0 }
  },
  "description": "KB population snapshot. Populated at runtime by executing agent."
}
```

9\. `context_preservation.metrics_tracker` — add to context_preservation properties:
```json
"metrics_tracker": {
  "type": "string",
  "description": "Running log of metric values collected at phase gates"
}
```

10\. `metrics[].id` — add to metric item properties:
```json
"id": {
  "type": "string",
  "pattern": "^MET-\\d{2}$",
  "description": "Unique metric identifier. Optional in schema for v2 backward compat; enforced by validator for version >= 3."
}
```

**CCC schema (oneOf for backward compatibility):**

```json
"cross_cutting_concerns": {
  "type": "array",
  "items": {
    "oneOf": [
      { "type": "string" },
      {
        "type": "object",
        "required": ["id", "title", "description", "enforcement_method", "minimum_phases"],
        "properties": {
          "id": { "type": "string", "pattern": "^CCC-\\d{2}$" },
          "title": { "type": "string" },
          "description": { "type": "string" },
          "enforcement_method": {
            "type": "string",
            "enum": ["checklist_items", "gate_condition", "compilation_precheck", "task_description"]
          },
          "enforcement_rule": { "type": "string" },
          "minimum_phases": { "type": "integer", "minimum": 1 },
          "phases_applied": { "type": "array", "items": { "type": "integer" } }
        }
      }
    ]
  }
}
```

### 5.2 Validation Script (validate_playbook.py) Changes

**New checks:**

| Check | Description |
|-------|-------------|
| CCC object validation | If CCC items are objects: validate required fields, phases_applied >= minimum_phases, unique CCC-IDs, valid enforcement_method |
| Metric ID validation | If version >= 3: require `id` on all metrics, unique MET-NNN format |
| Metric cross-reference | metrics_snapshot.collect items must reference valid metric IDs |
| role_context validation | If present, must be string |
| agent_assignment validation | If present, must be string |
| guardrail_checks validation | If present on gate items, must be array of strings |
| metrics_snapshot validation | If present on handoff, validate collect (array) and record_in (string) |
| kb_status validation | If present on handoff, validate total_entries/harvested/placeholder are integers |
| workflow_model enum | Add `"role-based-multi-agent"` to VALID_WORKFLOW_MODELS |
| Phase count | Update expected count from 15 to 17 for creator playbook |

**Updated checks:**

| Check | Change |
|-------|--------|
| Persistent files set (line 446) | Add `"metrics-tracker"` to `persistent` set: `persistent = {"decisions-ledger", "artifact-manifest", "metrics-tracker"}`. Without this, the handoff chain check (check 16) produces false positives on all 7 phases that load metrics-tracker.md (Phases 8, 9, 10, 11, 12, 14, 15). |
| CCC non-empty (check 14) | Also validate object structure if items are objects |
| FM cross-reference | Verify failure_modes_relevant FM-IDs exist in failure_modes[] (now non-empty) |
| Handoff chain (check 16) | Works unchanged after persistent set update — validates Phase 2→3 and Phase 9→10 transitions by index |
| Artifact provenance (check 17) | Works unchanged — finds KB docs in Phase 2 output_artifacts for Phase 9. Also add `"metrics-tracker"` to persistent skip in provenance check (line 492). |

### 5.3 Compilation Module Changes

| Module | Change |
|--------|--------|
| `system_prompt.py` | Extract `role_context` from role definition objects; include in prompt between `description` and `role_mindset` |
| `context_budget.py` | No changes needed |
| `model_fallback.py` | No changes needed |
| `constants.py` | No changes needed |

---

## 6. Migration Path

### v2 Creator Playbook to v3

Mechanical transformation (steps 1-4 are interdependent — apply as a single structural change, not sequentially):
1. Renumber phases per Section 3 mapping table
2. Insert Phase 3 (KB Bootstrapping) per Section 4.3
3. Split Phase 8 into Phases 9-10 per Section 4.7
4. Restructure Phase 12 into Phase 14 per Section 4.8
5. Convert CCC strings to objects per Section 4.5
6. Add `id` fields to metrics per Section 4.6
7. Add `role_context` and `agent_assignment` to roles per Section 4.4
8. Populate failure_modes per Section 4.9
9. Update all failure_modes_relevant arrays per Section 4.9 mapping table
10. Add metrics_snapshot to relevant gates per Section 4.6
11. Add guardrail_checks to relevant gates per Section 4.1
12. Update session_strategy per Section 3
13. Update out_of_scope per Section 4.3 (KB bootstrapping) and Section 4.4 (multi-agent)
14. Update context_preservation per Section 4.6
15. Add complexity classifier task to Phase 0 per Section 4.1
16. Add metrics report task to Phase 15 per Section 4.6
17. Update Phase 2 handoff per Section 4.2
18. Add metrics-tracker.md to Phase 0 initialization per Section 4.6
19. Add metrics-tracker.md to context_load of phases with metrics_snapshot
20. Add workflow_model enum value per Section 4.4
21. Run validate_playbook.py (updated) to verify

### v2 Output Playbooks to v3

Optional migration for existing output playbooks:
1. Wrap CCC strings in object format (id, title from first word, description from full string, enforcement_method: "checklist_items", minimum_phases: 3, phases_applied: [])
2. Add MET-NNN IDs to metrics
3. Optionally add role_context and agent_assignment to roles

---

## 7. Verification Checklist

After implementation, verify:

- [ ] All 17 phases have compilation blocks with required fields
- [ ] All handoff chains valid (Phase N next_phase_context matches Phase N+1 context_load)
- [ ] All 20 FM entries have 8 required fields
- [ ] All failure_modes_relevant arrays reference existing FM-IDs
- [ ] All 5 CCC objects have required fields and phases_applied >= minimum_phases
- [ ] All 8 metrics have unique MET-NNN IDs
- [ ] All gates with metrics_snapshot reference valid metric IDs
- [ ] Phase 0 initializes decisions-ledger.md, artifact-manifest.md, and metrics-tracker.md
- [ ] Phase 2 handoff includes full KB docs for Phase 3
- [ ] Phase 3 handoff restores slim context for Phase 4
- [ ] Phase 9 context_budget has differentiated priorities (not all 5)
- [ ] Phase 10 context_load is lighter than Phase 9 (5-6 files vs 15-16)
- [ ] guardrail_checks present on gates at Phases 2, 3, 4, 5, 6, 8, 10 with concrete natural-language strings
- [ ] metrics_snapshot present on gates at Phases 8, 9, 10, 11, 12, 14, 15
- [ ] workflow_model enum includes "role-based-multi-agent"
- [ ] output-schema.json accepts both string and object CCCs
- [ ] output-schema.json includes all 7 new field definitions (agent_assignment, role_context, guardrail_checks, metrics_snapshot, kb_status, metrics.id, context_preservation.metrics_tracker)
- [ ] validate_playbook.py persistent set includes "metrics-tracker" alongside "decisions-ledger" and "artifact-manifest"
- [ ] validate_playbook.py passes on the v3 creator playbook
- [ ] All role_mindset values use em dash (—, U+2014), not double hyphen (--)
- [ ] out_of_scope updated for both KB bootstrapping and multi-agent
- [ ] Session strategy matches v3 phase numbers
- [ ] system_prompt.py extracts role_context and inserts between description and role_mindset

---

## 8. Friction Point Resolution Summary

| FP | Problem | Solution | Section |
|----|---------|----------|---------|
| FP1 | No KB bootstrapping task | Phase 3: KB Bootstrapping | 4.3 |
| FP2 | Phase 8 too heavy | Split into Phase 9 (Assembly) + Phase 10 (Validation) | 4.7 |
| FP4 | Pilot testing impractical | Structured dry-run protocol with scenario matrix | 4.8 |
| FP7 | Empty failure_modes | 20 FMs seeded from JUCE execution | 4.9 |
| FP9 | Role switching overhead | role_context + agent_assignment on roles | 4.4 |
| FP10 | CCCs are plain strings | Structured objects with enforcement_method and phases_applied | 4.5 |
| FP12 | No progressive KB population | Phase 3 bootstraps; Phase 16 harvests post-run | 4.3 |
| FP14 | No metrics measurement | metrics_snapshot in gates + metrics-tracker.md | 4.6 |
| FP15 | No complexity governance | Complexity classifier + guardrail_checks | 4.1 |
