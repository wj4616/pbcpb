# Playbook Creator Playbook - Design Specification

**Version:** 2.0
**Date:** 2026-03-30
**Status:** Implemented — see playbook-creator-playbook.json

---

## Overview

A meta-playbook for creating domain-specific playbooks. Produces structured JSON playbooks through 15 phases of research, KB construction, architecture, task engineering, and validation. Works with single-agent systems where one agent fills multiple functional roles.

---

## Problem Statement

The existing playbook-creator.txt was designed for a multi-agent Mattermost system with fixed agent handles (@piper, @isaac, @forge, @minion, @lux, @kirk). These references are unusable in a single-agent context like Claude Code sessions.

**Solution:** Create a generalized playbook creator that:
- Uses role placeholders instead of agent handles
- Supports single-agent execution (one person/AI fills multiple roles)
- Outputs clean, platform-agnostic JSON
- Preserves and extends phase structure (12 → 15 phases)

---

## Design Decisions

### Role Model

| Role | Responsibility | Original Handle(s) |
|------|---------------|---------------------|
| Coordinator | Phase gates, tracking, status updates, blocker escalation, decisions ledger and artifact manifest maintenance | @minion |
| Stakeholder | Purpose, scope, constraints, success criteria, business decisions, final approval | @isaac |
| Researcher | Domain research, best practices, SME knowledge, competitive analysis | @piper |
| Builder | Task titles/descriptions, JSON assembly, validation, implementation of fixes | @forge |
| Architect | Phase structure, task granularity, role design, dependency mapping, template design | @lux |
| Auditor | Quality review, scenario walkthroughs, gap analysis, stress testing, failure mode cataloging, contamination testing, final verification before handoff | @kira + @axiom |

### Execution Models

The playbook supports three execution models:

1. **Single-agent**: One person (or AI session) fills all roles. Switches mental context per phase.
2. **Multi-agent**: Each role maps to a different agent or person.
3. **AI-assisted**: Human fills Stakeholder and Coordinator; AI fills Researcher, Architect, Builder; Auditor shared.

### Mindset Switching Guide

For single-agent execution, explicitly switch mental context:

| Phase Range | Mindset | Mental Checklist |
|--------------|---------|------------------|
| 0 | Stakeholder | "I am defining purpose, scope, and constraints. I will not research yet." |
| 1 | Researcher | "I am gathering and synthesizing. I will not design yet." |
| 2-4 | Architect | "I am structuring KB, phases, and roles. I will not write tasks yet." |
| 5 | Builder | "I am writing concrete tasks. I will not audit yet." |
| 6 | Architect | "I am designing how the playbook operates. I will not audit yet." |
| 7 | Researcher | "I am defining what success looks like. I will not audit yet." |
| 8 | Builder | "I am assembling and validating JSON. I will not audit yet." |
| 9-10 | Auditor | "I am finding flaws and gaps. I will not approve yet." |
| 11-12 | Stakeholder/Coordinator | "I am reviewing, iterating, and piloting. I will not change scope." |
| 13-14 | Coordinator | "I am documenting and planning improvement. I will not add features." |

**Switching protocol:**
1. Before starting a phase: Read the role definition above
2. During tasks: Refer to role responsibilities before each decision
3. After completing a phase: List completed items before attempting gate
4. At gate: Switch to Coordinator mindset for validation

### Gate Failure Handling

When a phase gate condition is not met:

```
Gate Failure Protocol:
1. STOP - Do not proceed to the next phase
2. Document why the condition is not met
3. Determine: Can this be fixed now, or is it a blocker?
4. If fixable now: Fix it, then re-validate the gate
5. If blocked: Mark as blocker, document what's needed, escalate if multi-agent
6. Single agent: Be honest in self-assessment - skipping gates causes cascade failures
```

**Common gate failures by phase:**
- Phase 0: Scope not locked (keep refining until boundaries are clear)
- Phase 1: Domain not understood (need more SME input or research)
- Phase 2: KB architecture incomplete (layers, schemas, or population strategy missing)
- Phase 3: Process architecture incomplete (missing dependencies or gates)
- Phase 5: Tasks too vague (each task must name specific files/deliverables)
- Phase 8: JSON invalid (syntax errors, missing fields, validator fails)
- Phase 9-10: Gaps found (return to earlier phases to fix)

---

## Output Schema

Playbooks produced by this creator follow the structure defined in `templates/output-schema.json` (JSON Schema draft-07). Key top-level fields:

```json
{
  "title": "string",
  "version": "integer (starts at 1)",
  "description": "string (1-3 sentences)",
  "workflow_model": "'human-in-the-loop' | 'fully-autonomous' | 'human-directed' | 'role-based-single-agent'",
  "roles": { "role_name": "responsibility description" },
  "scope": { "in_scope": [], "out_of_scope": [], "adjacent": [] },
  "cross_cutting_concerns": ["string — flat list of concern descriptions"],
  "knowledge_base": {
    "complexity": "'flat' | 'structured'",
    "layers": [], "entry_schema": {}, "bridge_schema": {},
    "population_strategy": {}, "directory_structure": "string"
  },
  "checklists": [
    {
      "title": "Phase N: Name",
      "purpose": "string",
      "compilation": {
        "context_load": ["file paths to load"],
        "role_mindset": "string",
        "objective": "string",
        "pre_check": ["conditions to verify before starting"],
        "failure_modes_relevant": ["FM-IDs"]
      },
      "items": [
        {
          "title": "[Role] — Task title",
          "owner": "[Role]",
          "description": "string (optional for simple tasks)",
          "conditional": "string or null (when task is conditional)",
          "output": "string (file path or deliverable name)",
          "gate_conditions": ["conditions (gate tasks only)"],
          "blocker_examples": ["common blockers (gate tasks only)"],
          "handoff": {
            "output_artifacts": ["files produced this phase"],
            "next_phase_context": ["files needed by next phase"],
            "excluded_context": ["what to drop from context"],
            "skill": "skill name or 'none'"
          }
        }
      ]
    }
  ],
  "metrics": [
    {
      "title": "string", "description": "string",
      "type": "'metric_integer' | 'metric_currency' | 'metric_duration'",
      "category": "'process' | 'output_quality' | 'domain_outcome'",
      "target": "number or null", "measurement_method": "string"
    }
  ],
  "usage_instructions": {
    "how_to_run": [], "session_strategy": [],
    "cost_optimization": [],
    "post_run_review": { "assess": [] }
  },
  "failure_modes": [
    { "id": "FM-NNN", "symptom": "", "root_cause": "", "fix": "",
      "prevention": "", "phase": "", "severity": "", "source": "" }
  ],
  "phase_kb_mapping": { "Phase N": ["kb topics"] },
  "skill_activation": { "Phase N": "skill or 'none'" },
  "router": { "description": "", "decision_tree": [], "default": "" },
  "context_preservation": {
    "decisions_ledger": "path", "artifact_manifest": "path",
    "rules": ["persistence rules"]
  }
}
```

---

## Project Structure

Intermediate outputs are organized by phase:

```
playbook-project/
├── README.md                 # Phase 0: Commission brief, scope, constraints
├── scope.md                  # Phase 0: In/out/adjacent scope
├── constraints.md            # Phase 0: Strategic constraints
├── success-criteria.md       # Phase 0: Measurable success criteria
├── decisions-ledger.md       # Persistent: Updated at every phase gate
├── artifact-manifest.md      # Persistent: Updated at every phase gate
├── research/
│   ├── domain-analysis.md    # Phase 1: Domain research
│   ├── best-practices.md     # Phase 1: Industry standards
│   ├── competitive-templates.md  # Phase 1: Existing playbooks
│   ├── sme-interviews.md     # Phase 1: Subject matter expert input
│   ├── cross-cutting-concerns.md  # Phase 1: Concerns affecting all phases
│   ├── platform-concerns.md  # Phase 1: Platform-specific issues
│   └── requirements.md       # Phase 1: Synthesized requirements
├── kb-architecture.md        # Phase 2: KB layers, complexity decision
├── entry-schema.json         # Phase 2: KB entry template (conditional)
├── bridge-schema.json        # Phase 2: Cross-layer reference schema (conditional)
├── population-strategy.md    # Phase 2: KB population and sync rules
├── directory-structure.md    # Phase 2: KB directory layout
├── architecture/
│   ├── phase-structure.md    # Phase 3: Phase list and objectives
│   ├── dependency-map.md     # Phase 3: Dependencies between phases
│   ├── phase-gates.md        # Phase 3: Gate conditions per phase
│   ├── task-granularity.md   # Phase 3: Task sizing guidelines
│   ├── document-tree.md      # Phase 3: Deliverable file tree
│   ├── role-definitions.md   # Phase 4: Role descriptions
│   ├── handoff-points.md     # Phase 4: Role-to-role handoffs
│   └── escalation-paths.md   # Phase 4: Blocker escalation rules
├── drafts/
│   ├── task-list-v0.1.md     # Phase 5: Initial task list
│   ├── playbook-v0.1.json    # Phase 8: First assembly
│   ├── playbook-v0.2.json    # Phase 10: Post-audit fixes
│   └── playbook-v0.3.json    # Phase 11: Post-stakeholder feedback
├── output-config.md          # Phase 6: Workflow model, usage, router, etc.
├── metrics-definition.md     # Phase 7: Metric definitions
├── audits/
│   ├── existing-playbook-audit.md    # Phase 1: Existing playbook audit (conditional)
│   ├── requirements-gap-analysis.md  # Phase 9: Requirements coverage
│   ├── cross-cutting-audit.md        # Phase 9: Cross-cutting coverage
│   ├── phase-gap-analysis.md         # Phase 9: Phase boundary gaps
│   ├── contradiction-audit.md        # Phase 9: Internal contradictions
│   ├── task-completability-audit.md  # Phase 9: Task executability
│   ├── detail-level-audit.md         # Phase 9: Description sufficiency
│   ├── kb-buildability-audit.md      # Phase 9: KB construction feasibility
│   ├── fix-list.md                   # Phase 9: Prioritized issues
│   ├── stress-test-verification.md   # Phase 10: Post-fix verification
│   └── final-verification.md         # Phase 12: Final audit before handoff
├── testing/
│   ├── scenario-happy-path.md        # Phase 10: Ideal execution walkthrough
│   ├── scenario-domain-novice.md     # Phase 10: New user walkthrough
│   ├── scenario-kb-construction.md   # Phase 10: KB building walkthrough
│   ├── scenario-blockers.md          # Phase 10: Blocker scenarios
│   ├── scenario-variants.md          # Phase 10: Domain variant scenarios
│   ├── edge-cases.md                 # Phase 10: Edge cases
│   ├── pilot-selection.md            # Phase 12: Pilot project criteria
│   ├── pilot-friction.md             # Phase 12: Pilot friction points
│   └── failure-modes-pilot.md        # Phase 12: Failure modes from pilot
├── stakeholder-feedback.md   # Phase 11: Review feedback
└── final/
    ├── playbook-v1.0.json    # Phase 12: Production playbook
    └── changelog.md          # Phase 13: Version history
```

---

## Phase Structure

All 15 phases with dependencies, deliverables, and audit inputs:

| Phase | Name | Dependencies | Primary Roles | Deliverables |
|-------|------|--------------|---------------|--------------|
| 0 | Commission & Scoping | None | Stakeholder, Coordinator | scope.md, constraints.md, success-criteria.md |
| 1 | Domain Research & Process Discovery | Phase 0 | Researcher, Stakeholder | domain-analysis.md, requirements.md |
| 2 | Knowledge Base Construction | Phase 1 | Architect | kb-architecture.md, entry-schema.json |
| 3 | Process Architecture | Phase 2 | Architect | phase-structure.md, dependency-map.md |
| 4 | Role Engineering | Phase 3 | Architect | role-definitions.md, handoff-points.md |
| 5 | Task Engineering | Phase 4 | Builder | task-list-v0.1.md |
| 6 | Output Configuration | Phase 5 | Architect | output-config.md |
| 7 | Metrics & KPI Definition | Phase 6 | Researcher, Stakeholder | metrics-definition.md |
| 8 | JSON Assembly & Validation | Phase 7 | Builder | playbook-v0.1.json |
| 9 | Quality Audit — Gap Analysis | Phase 8 | Auditor, Coordinator | audits/*.md, fix-list.md |
| 10 | Quality Audit — Stress Testing | Phase 9 | Auditor, Builder | scenario-*.md, edge-cases.md |
| 11 | Stakeholder Review & Iteration | Phase 10 | Stakeholder, Builder | stakeholder-feedback.md |
| 12 | Pilot Test | Phase 11 | Coordinator, Auditor, Builder | pilot-friction.md, playbook-v1.0.json |
| 13 | Documentation & Version Control | Phase 12 | Coordinator | changelog.md |
| 14 | Continuous Improvement | Phase 13 | Coordinator, Stakeholder | decisions-ledger.md (updated) |

### Audit Phase Inputs

Phases 9 and 10 require specific inputs from earlier phases:

**Phase 9 (Gap Analysis) inputs:**
- `requirements.md` (from Phase 1) — to verify requirements coverage
- `research/cross-cutting-concerns.md` (from Phase 1) — to check weaving
- `architecture/phase-structure.md` (from Phase 3) — to check phase gaps
- `drafts/task-list-v0.1.md` (from Phase 5) — to check task completeness
- `drafts/playbook-v0.1.json` (from Phase 8) — the assembled playbook to audit

**Phase 10 (Stress Testing) inputs:**
- `audits/fix-list.md` (from Phase 9) — prioritized issues to fix before stress testing
- `drafts/playbook-v0.1.json` (from Phase 8) — the assembled playbook (fixes produce v0.2 mid-phase)
- `decisions-ledger.md` and `artifact-manifest.md` (persistent)

---

## Phase 12: Pilot Alternatives

The pilot phase assumes multiple participants. For single-agent execution:

### Solo Pilot Protocol

```
1. Execute Phase 11 on a real project (use the playbook for its intended purpose)
2. Document friction points in real-time:
   - Where did I have to stop and think?
   - Where was task description unclear?
   - Where did I reference external knowledge not in the playbook?
3. After completion, review pilot-notes.md for patterns
4. Fix issues in playbook-v1.x.json
5. Re-validate affected phases (may need to return to Phase 7, 8, or 9)
```

### AI Adversarial Validation

```
1. Prompt AI to play stakeholder role:
   "Review this playbook from the perspective of [stakeholder type].
    What would confuse you? What would you skip?"
2. Prompt AI to play edge case generator:
   "Generate 5 edge cases this playbook might not handle well.
    [Domain: X, Platform: Y, Constraints: Z]"
3. Document AI feedback in pilot-notes.md
4. Fix identified issues
```

### Peer Review Protocol

```
1. Share playbook with another person familiar with the domain
2. Ask them to:
   - Read welcome/overview
   - Attempt Phase 0 tasks hypothetically
   - Note questions or confusion
3. Document feedback in stakeholder-feedback.md (Phase 10)
4. Iterate before Phase 11
```

---

## Key Differences from Original

| Aspect | Original | New |
|--------|----------|-----|
| Agent references | `@minion`, `@isaac`, `@forge` | `[Coordinator]`, `[Stakeholder]`, `[Builder]` |
| Role count | 7 roles | 6 roles (Reviewer+Auditor merged → Auditor, Approver → Stakeholder, Implementer → Builder) |
| Role flexibility | Fixed agents per handle | Single agent fills multiple roles |
| Output format | Mattermost JSON schema | Platform-agnostic JSON with compilation/handoff bookends |
| Platform features | Channels, message_on_join, reminders | Removed (add if needed) |
| Phase count | 12 phases | 15 phases (added KB Construction, Documentation, Continuous Improvement) |
| Gate structure | Embedded in task | Gate task with `gate_conditions`, `blocker_examples`, and `handoff` block |
| Context management | None | Compilation blocks (entry) + handoff blocks (exit) per phase |
| Persistent state | None | `decisions-ledger.md` + `artifact-manifest.md` loaded every phase |
| Role definitions | Scattered in descriptions | Centralized `roles` object |
| Deliverables | Implied in task descriptions | Explicit per-phase file paths with artifact provenance tracking |
| Pilot protocol | Assumes multi-agent | Three alternatives provided |
| Metrics | Defined in schema but not structure | Full schema with types, categories, and measurement methods |
| Failure modes | None | Cataloged with FM-IDs, severity, source, and prevention |
| Validation | None | Python structural validator with 17 checks |

### Removed Mattermost-Specific Elements

- `channel_name_template` - platform-specific
- `create_channel_member_on_new_participant` - platform feature
- `message_on_join` - can be added if targeting a platform
- `reminder_message_template` - can be added for scheduled reminders
- `run_summary_template` - kept as concept, not as platform field

### Preserved Essential Elements

- All original phases with full rigor (expanded from 12 to 15)
- Role-based task ownership (every task starts with `[Role]`)
- Phase gates with conditions, blocker examples, and handoff blocks
- Quality audits (gap analysis + stress testing as separate phases)
- Pilot phase with alternatives for single-agent
- Cross-cutting concern weaving
- Explicit deliverables per phase with artifact provenance
- Project folder structure
- Context preservation across session boundaries

---

## Usage

### Single-Agent Workflow

```
Phase 0:     Stakeholder — define purpose, scope, constraints
Phase 1:     Researcher — gather, synthesize, document
Phase 2-4:   Architect — KB, phases, roles
Phase 5:     Builder — write concrete tasks
Phase 6:     Architect — design output configuration
Phase 7:     Researcher — define metrics and KPIs
Phase 8:     Builder — assemble and validate JSON
Phase 9-10:  Auditor — gap analysis, stress testing
Phase 11-12: Stakeholder/Coordinator — review, iterate, pilot
Phase 13-14: Coordinator — document, plan improvement
```

### AI-Assisted Workflow

```
Human fills: Stakeholder (decisions), Coordinator (progress tracking)
AI fills: Researcher, Architect, Builder
Shared: Auditor (AI drafts audits, human validates; or vice versa)
```

### Resume Protocol

If execution stops mid-playbook:

```
1. Check which phase you're in by looking for the latest deliverable file
2. Open the deliverable for that phase - incomplete files indicate in-progress
3. Check if phase gate was validated (look for gate checkpoint in notes)
4. If gate passed: Resume at next phase
5. If gate not passed: Resume at current phase, re-validate gate
6. If mid-task: Continue from last incomplete task
```

---

## Output Files

The playbook creator project contains:

```
playbook-creator/
├── playbook-creator-playbook.json    # The meta-playbook itself (15 phases, 111 tasks)
├── specs/
│   └── 2026-03-30-playbook-creator-design.md  # This design specification
├── templates/
│   └── output-schema.json            # JSON Schema for produced playbooks
└── scripts/
    └── validate_playbook.py          # Structural validator (17 checks)
```

---

## Implementation Notes

1. The playbook JSON is loadable as context for planning sessions
2. Each phase executes sequentially with gate validation via compilation/handoff bookends
3. The output schema (`templates/output-schema.json`) ensures consistent playbook structure
4. The structural validator (`scripts/validate_playbook.py`) checks 17 integrity conditions
5. Role mapping guidance enables single-agent execution with mindset switching
6. Project structure provides organization for intermediate outputs
7. Pilot alternatives ensure single-agent can complete Phase 12
8. Resume protocol handles interrupted executions via `decisions-ledger.md` and `artifact-manifest.md`
9. Cross-cutting concerns are flat strings (not nested objects) for simplicity
10. Failure modes are cataloged with FM-IDs and linked to phases via `compilation.failure_modes_relevant`
11. Handoff chain consistency is enforced: Phase N's `next_phase_context` must match Phase N+1's `context_load`