# Playbook Creator Playbook Implementation Plan

> **Status: COMPLETED.** This plan was executed against `/home/myuser/Documents/playbookdev/`. All tasks are done — the checkboxes were not updated during execution. Paths in this document reference the original working directory, not this portable copy.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a platform-agnostic playbook creator JSON that transforms the Mattermost-specific playbook-creator.txt into a role-based format usable by single-agent systems.

**Architecture:** Three deliverables: (1) output-schema.json defines playbook structure, (2) playbook-creator-playbook.json is the meta-playbook with role placeholders, (3) role-mapping.json provides transformation reference.

**Tech Stack:** JSON, no dependencies. Files are loaded as context for AI planning sessions.

---

## File Structure

```
playbookdev/
├── playbook-creator.txt              # SOURCE (read-only)
├── specs/
│   └── 2026-03-30-playbook-creator-design.md  # SPEC (read-only)
├── playbook-creator-playbook.json    # OUTPUT 1: Meta-playbook
└── templates/
    ├── output-schema.json            # OUTPUT 2: Schema
    └── role-mapping.json             # OUTPUT 3: Reference
```

---

### Task 1: Create Output Schema

**Files:**
- Create: `playbookdev/templates/output-schema.json`

- [ ] **Step 1: Create templates directory and write schema**

```bash
mkdir -p /home/myuser/Documents/playbookdev/templates
```

Create `playbookdev/templates/output-schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "playbook-output-schema",
  "title": "Playbook Output Schema",
  "description": "Schema for playbooks produced by the playbook-creator-playbook",
  "type": "object",
  "required": ["title", "version", "description", "workflow_model", "roles", "checklists", "usage_instructions"],
  "properties": {
    "title": { "type": "string", "description": "Playbook name", "minLength": 1 },
    "version": { "type": "integer", "description": "Playbook version, starts at 1", "minimum": 1 },
    "description": { "type": "string", "description": "1-3 sentences explaining what this playbook automates", "minLength": 10 },
    "workflow_model": { "type": "string", "enum": ["human-in-the-loop", "role-based", "automated"], "description": "How the playbook is executed" },
    "roles": { "type": "object", "description": "Role name to responsibility mapping", "additionalProperties": { "type": "string" } },
    "role_execution_guidance": {
      "type": "object",
      "description": "How roles map to execution contexts",
      "properties": {
        "single_agent": { "type": "string" },
        "multi_agent": { "type": "string" },
        "ai_assisted": { "type": "string" }
      }
    },
    "prerequisites": { "type": "array", "description": "What must exist before running", "items": { "type": "string" } },
    "cross_cutting_concerns": {
      "type": "array",
      "description": "Concerns that affect multiple phases",
      "items": {
        "type": "object",
        "required": ["concern", "description", "phases_affected"],
        "properties": {
          "concern": { "type": "string" },
          "description": { "type": "string" },
          "phases_affected": { "type": "array", "items": { "type": "string" } },
          "integration_guidance": { "type": "string" }
        }
      }
    },
    "deliverables": { "type": "object", "description": "Outputs per phase", "additionalProperties": { "type": "array", "items": { "type": "string" } } },
    "checklists": {
      "type": "array",
      "description": "Phase definitions with tasks",
      "items": {
        "type": "object",
        "required": ["title", "purpose", "items"],
        "properties": {
          "title": { "type": "string" },
          "purpose": { "type": "string" },
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["title"],
              "properties": {
                "title": { "type": "string" },
                "owner": { "type": "string" },
                "description": { "type": "string" },
                "validation": { "type": "string" },
                "output": { "type": "string" },
                "gate": {
                  "type": "object",
                  "properties": {
                    "conditions": { "type": "array", "items": { "type": "string" } },
                    "blocker_examples": { "type": "array", "items": { "type": "string" } }
                  }
                }
              }
            }
          }
        }
      }
    },
    "metrics": {
      "type": "array",
      "description": "Success metrics",
      "items": {
        "type": "object",
        "required": ["title", "description", "type"],
        "properties": {
          "title": { "type": "string" },
          "description": { "type": "string" },
          "type": { "type": "string", "enum": ["metric_integer", "metric_currency", "metric_duration"] },
          "target": { "type": ["number", "null"] }
        }
      }
    },
    "usage_instructions": {
      "type": "object",
      "required": ["how_to_run"],
      "properties": {
        "how_to_run": { "type": "array", "items": { "type": "string" } },
        "cost_optimization": { "type": "array", "items": { "type": "string" } },
        "resume_protocol": { "type": "string" }
      }
    }
  }
}
```

- [ ] **Step 2: Validate schema syntax**

Run: `python3 -c "import json; json.load(open('/home/myuser/Documents/playbookdev/templates/output-schema.json'))"`

Expected: No errors

---

### Task 2: Create Role Mapping Reference

**Files:**
- Create: `playbookdev/templates/role-mapping.json`

- [ ] **Step 1: Write role mapping JSON**

Create `playbookdev/templates/role-mapping.json`:

```json
{
  "description": "Mapping from Mattermost @handles to role placeholders for single-agent systems",
  "role_mapping": {
    "@minion": "[Coordinator]",
    "@isaac": "[Stakeholder]",
    "@piper": "[Researcher]",
    "@forge": "[Builder]",
    "@lux": "[Architect]",
    "@kira": "[Auditor]",
    "@axiom": "[Auditor]"
  },
  "role_definitions": {
    "Coordinator": "Phase gates, tracking, status updates, blocker escalation, decisions ledger and artifact manifest maintenance",
    "Stakeholder": "Purpose, scope, constraints, success criteria, business decisions, final approval",
    "Researcher": "Domain research, best practices, SME knowledge, competitive analysis",
    "Builder": "Task titles/descriptions, JSON assembly, validation, implementation of fixes",
    "Architect": "Phase structure, task granularity, role design, dependency mapping, template design",
    "Auditor": "Quality review, scenario walkthroughs, gap analysis, stress testing, failure mode cataloging, final verification before handoff"
  },
  "execution_models": {
    "single_agent": {
      "description": "One person or AI session fills all roles",
      "mindset_phases": {
        "0": "Stakeholder mindset - define purpose, scope, constraints",
        "1": "Researcher mindset - gather, synthesize, document",
        "2-4": "Architect mindset - structure KB, phases, roles",
        "5": "Builder mindset - write concrete tasks",
        "6": "Architect mindset - design output configuration",
        "7": "Researcher mindset - define metrics and KPIs",
        "8": "Builder mindset - assemble and validate JSON",
        "9-10": "Auditor mindset - gap analysis, stress testing",
        "11-12": "Stakeholder/Coordinator mindset - review, iterate, pilot",
        "13-14": "Coordinator mindset - document, plan improvement"
      }
    },
    "multi_agent": {
      "description": "Each role maps to a different agent or person",
      "note": "Assign roles at playbook start, track ownership throughout"
    },
    "ai_assisted": {
      "description": "Human fills Stakeholder and Coordinator; AI fills Researcher, Builder, Architect",
      "human_roles": ["Stakeholder", "Coordinator"],
      "ai_roles": ["Researcher", "Builder", "Architect"],
      "shared_roles": ["Auditor"]
    }
  }
}
```

- [ ] **Step 2: Validate JSON syntax**

Run: `python3 -c "import json; json.load(open('/home/myuser/Documents/playbookdev/templates/role-mapping.json'))"`

Expected: No errors

---

### Task 3: Create Main Playbook JSON (Complete)

**Files:**
- Create: `playbookdev/playbook-creator-playbook.json`

**Purpose:** Write the complete playbook JSON in one file with all phases transformed from @handles to [Role] placeholders.

- [ ] **Step 1: Write complete playbook JSON**

Write `playbookdev/playbook-creator-playbook.json` with the full content. The file is large - write it with all phases (0-14) including:
- Header and metadata
- Roles and role_execution_guidance
- prerequisites and cross_cutting_concerns
- deliverables per phase
- All 15 phases (0-14) with tasks transformed to [Role] format
- metrics section
- usage_instructions

Key transformations from original:
- `@minion` → `[Coordinator]`
- `@isaac` → `[Approver]`
- `@piper` → `[Researcher]`
- `@forge` → `[Implementer]`
- `@lux` → `[Architect]`
- `@kira` → `[Reviewer]`
- `@axiom` → `[Auditor]`
- Remove Mattermost-specific fields (channel_name_template, message_on_join, etc.)
- Add pilot_alternatives for Phase 12 single-agent execution
- Add gate object structure to each phase

- [ ] **Step 2: Validate complete JSON**

Run: `python3 -c "import json; json.load(open('/home/myuser/Documents/playbookdev/playbook-creator-playbook.json'))"`

Expected: No errors

- [ ] **Step 3: Validate against schema**

Run: `python3 -c "
import json
schema = json.load(open('/home/myuser/Documents/playbookdev/templates/output-schema.json'))
playbook = json.load(open('/home/myuser/Documents/playbookdev/playbook-creator-playbook.json'))
required = schema['required']
for field in required:
    if field not in playbook:
        print(f'MISSING REQUIRED FIELD: {field}')
print('Validation complete')
"`

Expected: "Validation complete" with no missing fields

---

### Task 4: Write Phase 0 Content

**Files:**
- Modify: `playbookdev/playbook-creator-playbook.json`

This task writes the Phase 0 checklist content. The JSON structure is already created in Task 3 - this documents the specific transformation.

Phase 0 tasks from original playbook-creator.txt:
- `[Coordinator] — Create project knowledge base` (from `@minion`)
- `[Coordinator] — Own playbook tracking and status updates throughout the run`
- `[Approver] — Define the playbook's purpose and problem statement` (from `@isaac`)
- `[Approver] — Define target users and team composition`
- `[Approver] — Define scope boundaries`
- `[Approver] — Define success criteria for the playbook itself`
- `[Approver] — Define strategic constraints`
- `[Researcher] — Identify related existing playbooks` (from `@piper`)
- `[Coordinator] — Phase gate: Purpose defined, scope locked...`

Gate conditions remain identical - just verify the JSON in Task 3 includes this content.

---

### Task 5: Write Phase 1-3 Content

**Files:**
- Verify: `playbookdev/playbook-creator-playbook.json`

Phase 1: Domain Research & Process Discovery
Phase 2: Process Architecture
Phase 3: Role Engineering

Transform all tasks from original using role mapping:
- `@piper` → `[Researcher]`
- `@axiom` → `[Auditor]`
- `@lux` → `[Architect]`
- `@minion` → `[Coordinator]`
- `@isaac` → `[Approver]`

Verify the JSON in Task 3 includes all tasks from original lines 54-154 for Phase 1, lines 92-126 for Phase 2, lines 129-154 for Phase 3.

---

### Task 6: Write Phase 4-6 Content

**Files:**
- Verify: `playbookdev/playbook-creator-playbook.json`

Phase 4: Task Engineering (lines 156-190)
Phase 5: Template & Messaging Design (lines 192-226)
Phase 6: Metrics & KPI Definition (lines 228-250)

Transform:
- `@forge` → `[Implementer]`
- `@lux` → `[Architect]`
- `@kira` → `[Reviewer]`
- `@piper` → `[Researcher]`
- `@isaac` → `[Approver]`
- `@minion` → `[Coordinator]`

Note: Phase 5 includes Mattermost-specific templates (message_on_join, channel_name_template). Replace with:
- `[Architect] — Design run summary template` (keep, remove platform-specific)
- `[Architect] — Design status update template` (keep)
- `[Architect] — Design retrospective template` (keep)

Remove: channel_name_template, reminder_timer_default_seconds (platform-specific)

---

### Task 7: Write Phase 7-9 Content

**Files:**
- Verify: `playbookdev/playbook-creator-playbook.json`

Phase 7: JSON Assembly & Schema Compliance (lines 252-278)
Phase 8: Quality Audit — Gap Analysis (lines 280-314)
Phase 9: Quality Audit — Stress Testing (lines 316-351)

Transform all @handles to [Role] format.

---

### Task 8: Write Phase 10-12 Content

**Files:**
- Verify: `playbookdev/playbook-creator-playbook.json`

Phase 10: Stakeholder Review & Iteration (lines 353-381)
Phase 11: Stakeholder Review & Iteration (continues)
Phase 12: Pilot Test

**Critical modification for Phase 12:**
Replace Mattermost-specific task `[Implementer] — Import playbook into Mattermost` with:

```json
{
  "title": "[Coordinator] — Pilot alternatives (for single-agent execution)",
  "description": "The pilot phase assumes multiple participants. For single-agent execution, choose one:\n\n**Solo Pilot Protocol:**\n1. Execute the playbook on a real project\n2. Document friction points in real-time\n3. After completion, review pilot-notes.md for patterns\n4. Fix issues in playbook-v1.x.json\n\n**AI Adversarial Validation:**\n1. Prompt AI to play stakeholder role: 'Review this playbook from the perspective of [stakeholder type]. What would confuse you?'\n2. Prompt AI to play edge case generator: 'Generate 5 edge cases this playbook might not handle well.'\n3. Document AI feedback in pilot-notes.md\n\n**Peer Review Protocol:**\n1. Share playbook with another person familiar with domain\n2. Ask them to read and attempt Phase 0 tasks hypothetically\n3. Document feedback in stakeholder-feedback.md",
  "output": "pilot/pilot-notes.md"
}
```

---

### Task 9: Add Metrics Section

**Files:**
- Verify: `playbookdev/playbook-creator-playbook.json`

Metrics section (from original lines 460-505):

```json
"metrics": [
  {
    "title": "Total Phases",
    "description": "Number of phases in the produced playbook",
    "type": "metric_integer"
  },
  {
    "title": "Total Tasks",
    "description": "Number of tasks across all phases",
    "type": "metric_integer"
  },
  {
    "title": "Tasks With Descriptions",
    "description": "Percentage of tasks that have descriptions",
    "type": "metric_integer",
    "target": 70
  },
  {
    "title": "Metrics Defined",
    "description": "Number of KPI metrics defined",
    "type": "metric_integer",
    "target": 6
  },
  {
    "title": "Days to Complete",
    "description": "Calendar days from commission to deployment",
    "type": "metric_integer",
    "target": 10
  },
  {
    "title": "Audit Issues Found",
    "description": "Total issues found during quality audit phases",
    "type": "metric_integer"
  },
  {
    "title": "Critical Issues at Pilot",
    "description": "Issues discovered during pilot that should have been caught earlier",
    "type": "metric_integer",
    "target": 0
  },
  {
    "title": "Pilot Completion Rate",
    "description": "Percentage of tasks completed as written during pilot",
    "type": "metric_integer",
    "target": 90
  }
]
```

---

### Task 10: Add Usage Instructions

**Files:**
- Verify: `playbookdev/playbook-creator-playbook.json`

```json
"usage_instructions": {
  "how_to_run": [
    "1. Load this playbook as context for a planning session",
    "2. Identify which roles you will fill (single agent = all roles; AI-assisted = human = Approver/Coordinator)",
    "3. Work through phases sequentially - each phase gate must pass before the next",
    "4. For each task: read the description, complete the work, mark complete",
    "5. At phase gates: verify all conditions are met before proceeding",
    "6. Final output: a domain-specific playbook following output_schema.json"
  ],
  "single_agent_workflow": [
    "Phase 0-1: Adopt Researcher mindset - gather, synthesize, document",
    "Phase 2-3: Adopt Architect mindset - structure, design, map",
    "Phase 4-6: Adopt Implementer mindset - write, assemble, define",
    "Phase 7-9: Adopt Reviewer mindset - audit, test, validate",
    "Phase 10-11: Adopt Coordinator/Approver mindset - align, approve, ship"
  ],
  "ai_assisted_workflow": [
    "Human fills: Approver (decisions), Coordinator (progress tracking)",
    "AI fills: Researcher, Implementer, Architect",
    "Shared: Reviewer (AI drafts, human validates)"
  ],
  "resume_protocol": "If execution stops: (1) Find latest deliverable file, (2) Check if phase gate passed, (3) Resume at current or next phase, (4) Continue from last incomplete task"
}
```

---

### Task 11: Final Validation

**Files:**
- Validate: `playbookdev/playbook-creator-playbook.json`
- Validate: `playbookdev/templates/output-schema.json`
- Validate: `playbookdev/templates/role-mapping.json`

- [ ] **Step 1: Validate all JSON files parse correctly**

```bash
python3 -c "import json; json.load(open('/home/myuser/Documents/playbookdev/playbook-creator-playbook.json')); print('playbook OK')"
python3 -c "import json; json.load(open('/home/myuser/Documents/playbookdev/templates/output-schema.json')); print('schema OK')"
python3 -c "import json; json.load(open('/home/myuser/Documents/playbookdev/templates/role-mapping.json')); print('role-mapping OK')"
```

Expected: All three print "OK"

- [ ] **Step 2: Verify role transformation is complete**

```bash
grep -c '@minion\|@isaac\|@piper\|@forge\|@lux\|@kira\|@axiom' /home/myuser/Documents/playbookdev/playbook-creator-playbook.json || echo "No @handles found - transformation complete"
```

Expected: "No @handles found - transformation complete"

- [ ] **Step 3: Verify all 15 phases present**

```bash
python3 -c "
import json
p = json.load(open('/home/myuser/Documents/playbookdev/playbook-creator-playbook.json'))
phases = [c['title'] for c in p['checklists']]
print(f'Found {len(phases)} phases:')
for ph in phases:
    print(f'  - {ph}')
"
```

Expected: 15 phases listed (Phase 0 through Phase 14)

---

### Task 12: Create README Documentation

**Files:**
- Create: `playbookdev/README.md`

```markdown
# Playbook Creator

Meta-playbook for creating domain-specific playbooks. Works with single-agent systems where one agent fills multiple roles.

## Files

- `playbook-creator-playbook.json` - The main playbook creator (15 phases)
- `templates/output-schema.json` - Schema for validating produced playbooks
- `templates/role-mapping.json` - Reference for @handle to [Role] transformation

## Usage

1. Load `playbook-creator-playbook.json` as context for a planning session
2. Follow phases sequentially, passing each gate before proceeding
3. Output: A domain-specific playbook matching `output-schema.json`

## Execution Models

| Model | Description |
|-------|-------------|
| Single-agent | One person/AI fills all roles, switches mindset per phase |
| Multi-agent | Each role maps to different person/agent |
| AI-assisted | Human = Approver/Coordinator, AI = Researcher/Implementer/Architect |

## Role Mapping

| Original Handle | New Role |
|-----------------|----------|
| @minion | [Coordinator] |
| @isaac | [Stakeholder] |
| @piper | [Researcher] |
| @forge | [Builder] |
| @lux | [Architect] |
| @kira, @axiom | [Auditor] |

**Note:** The spec merges @kira and @axiom into a single [Auditor] role that handles quality review, gap analysis, stress testing, and final verification.

## Phases

| Phase | Purpose |
|-------|---------|
| 0 | Commission & Scoping |
| 1 | Domain Research & Process Discovery |
| 2 | Knowledge Base Construction |
| 3 | Process Architecture |
| 4 | Role Engineering |
| 5 | Task Engineering |
| 6 | Output Configuration |
| 7 | Metrics & KPI Definition |
| 8 | JSON Assembly & Validation |
| 9 | Quality Audit — Gap Analysis |
| 10 | Quality Audit — Stress Testing |
| 11 | Stakeholder Review & Iteration |
| 12 | Pilot Test |
| 13 | Documentation & Version Control |
| 14 | Continuous Improvement |

## Key Differences from Original

- Expanded from 12 to 15 phases (added KB Construction, Documentation, Continuous Improvement)
- Removed Mattermost-specific fields (channel_name_template, message_on_join)
- Replaced @handles with [Role] placeholders
- Added pilot alternatives for single-agent execution
- Added cross_cutting_concerns and deliverables sections
- Added explicit phase gates with conditions and blocker_examples
- Added compilation blocks with context_load, role_mindset, objective, pre_check
- Added handoff blocks with output_artifacts, next_phase_context, excluded_context, skill
```

---

## Self-Review Checklist

After completing all tasks:

- [ ] All JSON files validate without errors
- [ ] No @handle references remain (all transformed to [Role])
- [ ] All 15 phases (0-14) present with full task content
- [ ] Each phase has gate object with conditions and blocker_examples
- [ ] deliverables section defines outputs per phase
- [ ] cross_cutting_concerns documented
- [ ] pilot alternatives included for single-agent execution
- [ ] metrics section complete with 8 metrics
- [ ] usage_instructions includes all three execution models
- [ ] README documents usage and role mapping