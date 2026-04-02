# Compilation Block Enhancement Design

**Version:** 2.0
**Date:** 2026-03-31
**Status:** Design approved (post-audit revision)

---

## Overview

Enhance the playbook compilation block to define how to assemble a purpose-built agent instance before each phase runs. The current compilation block only handles context files and mindset — this design adds agent configuration, system prompt generation, and context budget controls.

---

## Problem Statement

The current compilation block structure:

```json
"compilation": {
  "context_load": ["file paths"],
  "role_mindset": "Role name",
  "objective": "Phase objective",
  "pre_check": ["conditions"],
  "failure_modes_relevant": ["FM-IDs"]
}
```

This is insufficient for assembling an agent instance because:

1. **No model selection** — All phases use the same model regardless of complexity
2. **No system prompt definition** — Only a mindset reminder, not a complete prompt
3. **No token budget** — Context loading has no limits or prioritization
4. **No agent parameters** — Temperature, max_tokens not configurable per phase
5. **No model fallback** — No handling for unavailable models
6. **No role-level defaults** — Cannot specify defaults per role for multi-agent
7. **No critical file protection** — Budget cuts can skip essential files

---

## Design Decisions

### Decision 1: Structure Approach

**Chosen: Extend existing structure**

Add new fields alongside existing `context_load`, `role_mindset`, `objective`. Minimal disruption to existing playbooks.

### Decision 2: Model Selection with Fallbacks

**Chosen: Three-level inheritance with fallback chains**

1. Phase `agent_config.model` (highest priority)
2. Role `defaults.model` (medium priority)
3. Playbook `defaults.model` (lowest priority)

Fallback chains allow graceful degradation when models unavailable.

### Decision 3: System Prompt Auto-Generation

**Chosen: Assemble from components with budget tracking**

System prompt assembled from:
- Role definition from `roles` object
- Role mindset from compilation block
- Phase objective
- Failure modes (looked up from `failure_modes` array)
- Pre-check guidance
- Context file descriptions (from `artifact-manifest.md`)
- Output requirements

Budget tracking reserves tokens for system prompt before file loading.

### Decision 4: Context Budget with Critical Protection

**Chosen: Priority-based loading with critical file protection**

- Each file assigned priority 1-10 (1 = highest)
- Files at or below `critical_priority_threshold` cannot be skipped
- `system_prompt_budget` reserved for generated prompt
- `response_reservation` reserves `max_tokens` for response

### Decision 5: Role-Level Defaults

**Chosen: Roles can override playbook defaults**

Each role can specify its own defaults for model, temperature, and other parameters. This supports both single-agent and multi-agent execution models.

### Decision 6: Skill Activation Timing

**Chosen: Pre-phase and post-phase skills**

- `compilation.skill_preparation` runs before phase
- `handoff.skill_validation` runs after phase

---

## Specification

### Top-Level Defaults

```json
{
  "title": "Playbook Title",
  "version": 1,
  "defaults": {
    "model": "opus",
    "model_fallbacks": {
      "opus": ["sonnet", "haiku"],
      "sonnet": ["haiku"],
      "glm-5:cloud": ["sonnet", "opus"]
    },
    "context_budget_tokens": 64000,
    "system_prompt_budget": 2000,
    "critical_priority_threshold": 3,
    "temperature": 0.3,
    "max_tokens": 4096
  },
  "roles": {
    "Coordinator": {
      "description": "Phase gates, tracking, status updates, blocker escalation, decisions ledger and artifact manifest maintenance",
      "defaults": {
        "model": "haiku",
        "temperature": [0.1, 0.3]
      },
      "temperature_rationale": "Coordinators need consistency for gate verification"
    },
    "Stakeholder": {
      "description": "Purpose, scope, constraints, success criteria, business decisions, final approval",
      "defaults": {
        "model": "opus",
        "temperature": [0.1, 0.2]
      },
      "temperature_rationale": "Stakeholders make critical decisions requiring precision"
    },
    "Researcher": {
      "description": "Domain research, best practices, SME knowledge, competitive analysis",
      "defaults": {
        "model": "sonnet",
        "temperature": [0.4, 0.7]
      },
      "temperature_rationale": "Research benefits from creative exploration"
    },
    "Builder": {
      "description": "Task titles/descriptions, JSON assembly, validation, implementation of fixes",
      "defaults": {
        "model": "sonnet",
        "temperature": [0.2, 0.4]
      },
      "temperature_rationale": "Building requires consistency with some flexibility"
    },
    "Architect": {
      "description": "Phase structure, task granularity, role design, dependency mapping, template design",
      "defaults": {
        "model": "opus",
        "temperature": [0.3, 0.5]
      },
      "temperature_rationale": "Architecture needs depth with structured thinking"
    },
    "Auditor": {
      "description": "Quality review, scenario walkthroughs, gap analysis, stress testing, failure mode cataloging, contamination testing, final verification before handoff",
      "defaults": {
        "model": "opus",
        "temperature": [0.0, 0.2]
      },
      "temperature_rationale": "Auditing requires deterministic verification"
    }
  },
  ...
}
```

**Field descriptions:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `defaults.model` | string | "opus" | Default model: opus, sonnet, haiku, or provider:model |
| `defaults.model_fallbacks` | object | {} | Fallback chains for unavailable models |
| `defaults.context_budget_tokens` | integer | 64000 | Default context budget if phase doesn't specify |
| `defaults.system_prompt_budget` | integer | 2000 | Tokens reserved for generated system prompt |
| `defaults.critical_priority_threshold` | integer | 3 | Files at priority 1-N cannot be skipped |
| `defaults.temperature` | number | 0.3 | Default temperature (0-2) |
| `defaults.max_tokens` | integer | 4096 | Default max output tokens |

**Role-level defaults:**

| Field | Type | Description |
|-------|------|-------------|
| `roles.{role}.description` | string | Role responsibilities |
| `roles.{role}.defaults.model` | string | Preferred model for this role |
| `roles.{role}.defaults.temperature` | array | Recommended range [min, max] |
| `roles.{role}.temperature_rationale` | string | Why this range is appropriate |

### Enhanced Compilation Block

```json
{
  "title": "Phase 1: Domain Research & Process Discovery",
  "purpose": "Understand the domain deeply enough to build a playbook for it...",
  "compilation": {
    "context_load": [
      "README.md",
      "scope.md",
      "constraints.md",
      "decisions-ledger.md",
      "artifact-manifest.md"
    ],
    "role_mindset": "Researcher",
    "objective": "Produce comprehensive flat research documents covering domain processes...",
    "pre_check": [
      "Purpose statement is unambiguous",
      "Scope has in/out/adjacent lists",
      "Constraints documented"
    ],
    "failure_modes_relevant": ["FM-001", "FM-003"],

    "agent_config": {
      "model": "sonnet",
      "temperature": 0.4,
      "max_tokens": 8192
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
      "max_tokens": 48000,
      "priority": {
        "README.md": 1,
        "scope.md": 1,
        "constraints.md": 1,
        "decisions-ledger.md": 2,
        "artifact-manifest.md": 2,
        "research/domain-analysis.md": 3
      }
    },
    "skill_preparation": "none"
  },
  "items": [...],
  "gate_task": {
    ...
  },
  "handoff": {
    "output_artifacts": [...],
    "next_phase_context": [...],
    "excluded_files": [
      "research/sme-interviews.md"
    ],
    "skill_validation": "none"
  }
}
```

**All compilation fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_load` | array | yes | Files to load into context |
| `role_mindset` | string | yes | Role to adopt for this phase |
| `objective` | string | yes | Phase objective |
| `pre_check` | array | no | Conditions to verify before starting |
| `failure_modes_relevant` | array | no | FM-IDs to include in prompt |
| `agent_config` | object | no | Override model parameters |
| `agent_config.model` | string | no | Override model |
| `agent_config.temperature` | number | no | Override temperature |
| `agent_config.max_tokens` | integer | no | Override max output tokens |
| `system_prompt_auto` | object | no | System prompt generation flags |
| `context_budget` | object | no | Token budget configuration |
| `context_budget.max_tokens` | integer | no | Hard token limit (optional, uses defaults if omitted) |
| `context_budget.priority` | object | no | File-to-priority mapping |
| `skill_preparation` | string | no | Skill to run before phase |

### Inheritance Rules

```
Model selection (highest to lowest priority):
1. Phase agent_config.model
2. Role defaults.model for current role_mindset
3. Playbook defaults.model

Temperature selection:
1. Phase agent_config.temperature (if specified)
2. Midpoint of role defaults.temperature range
3. Playbook defaults.temperature

Max tokens selection:
1. Phase agent_config.max_tokens (if specified)
2. Playbook defaults.max_tokens

Context budget selection:
1. Phase context_budget.max_tokens (if specified)
2. Playbook defaults.context_budget_tokens

Priority assignment:
1. File in context_budget.priority
2. Default priority 5
3. Validation: All files in priority MUST exist in context_load
```

### Model Fallback

When specified model is unavailable, use fallback chain:

```json
"model_fallbacks": {
  "opus": ["sonnet", "haiku"],
  "sonnet": ["haiku"],
  "glm-5:cloud": ["sonnet", "opus"]
}
```

**Fallback resolution:**
1. Try specified model
2. If unavailable, try first fallback
3. Continue until available model found
4. Log fallback: `[MODEL FALLBACK] opus unavailable, using sonnet`

**Provider awareness:**
- Model strings can include provider: "glm-5:cloud", "anthropic:opus"
- Provider prefix is optional (default to current platform)
- Fallback chain respects provider boundaries

### System Prompt Generation

**Template:**

```
You are a {role_name} in a {workflow_model} workflow.

{role_definition}

## Your Role
{role_mindset} — {expanded_mindset_guidance}

## Your Objective This Phase
{objective}

## Pre-Flight Checks
Before starting, verify:
{pre_check_bullets}

## Failure Modes to Watch For
{failure_modes_detailed}

## Context Files Loaded
{context_files_with_descriptions_from_artifact_manifest}

## Output Requirements
This phase produces:
{output_artifacts}
```

**Generation process:**

1. **Role definition**: Look up `roles.{role_mindset}.description`
2. **Expanded mindset**: Generate guidance from role and phase context
3. **Failure modes**: Look up each FM-ID in `failure_modes` array, include `symptom` and `prevention`
4. **Context files**: Read descriptions from `artifact-manifest.md`
5. **Output requirements**: From handoff `output_artifacts`

**Example artifact-manifest lookup:**

```json
// artifact-manifest.md contains:
| File | Phase | Status | Summary |
|------|-------|--------|---------|
| README.md | 0 | Complete | Project overview and purpose |
| scope.md | 0 | Complete | In/out/adjacent scope boundaries |

// System prompt shows:
## Context Files Loaded
- README.md: Project overview and purpose
- scope.md: In/out/adjacent scope boundaries
```

**Budget calculation:**

```
Available for files = context_budget.max_tokens
                      - system_prompt_budget
                      - max_tokens (response reservation)
```

Example:
```
Phase budget: 48,000 tokens
System prompt reservation: 2,000 tokens
Response reservation (max_tokens): 8,192 tokens
Available for files: 48,000 - 2,000 - 8,192 = 37,808 tokens
```

### Context Budget Loading

**Priority semantics:**

| Priority | Meaning | Typical Files | Skip Policy |
|----------|---------|---------------|-------------|
| 1-3 | Critical | scope.md, constraints.md, decisions-ledger.md | Cannot skip (error if budget insufficient) |
| 4-7 | Reference | KB entries, best practices | Can skip with warning |
| 8-10 | Optional | Historical logs, previous run data | Can skip silently |

**Loading algorithm:**

```
1. Calculate available token budget:
   available = max_tokens - system_prompt_budget - response_reservation

2. Validate all files in priority exist in context_load:
   for file in priority:
     if file not in context_load:
       ERROR: priority file not in context_load

3. Assign default priority to files without explicit priority:
   for file in context_load:
     if file not in priority:
       priority[file] = 5

4. Sort files by priority (ascending): 1 = highest

5. For each priority level:
   a. Calculate token count for all files at this priority
   b. If (loaded + this_level) <= available:
      - Load all files at this priority
      - loaded += this_level
   c. Else if priority <= critical_priority_threshold:
      - ERROR: Insufficient budget for critical files
      - List critical files that cannot fit
      - Halt phase execution
   d. Else:
      - Skip this level and all remaining
      - Log warning with skipped files
      - Stop loading

6. Generate system prompt with loaded files

7. Log summary:
   [CONTEXT LOAD]
   Budget: {available} tokens available
   Loaded: {loaded} tokens ({file_count} files)
   Skipped: {skipped} tokens ({file_count} files)
   Files skipped: {list}
```

**Error handling:**

```
[CONTEXT BUDGET ERROR]
Critical files cannot fit in budget.
Budget: 8000 tokens
Required (priority 1-3): 12000 tokens

Files that cannot fit:
- README.md (priority 1): 3000 tokens
- scope.md (priority 1): 4000 tokens
- constraints.md (priority 1): 5000 tokens

Solution: Increase context_budget.max_tokens to at least 14000 tokens
or reduce critical_priority_threshold.
```

**Warning format:**

```
[CONTEXT BUDGET WARNING]
Budget: 37808 tokens available
Loaded: 32000 tokens (priority 1-5 files)
Skipped: 8000 tokens (priority 6-8 files)

Files skipped:
- research/best-practices.md (priority 6)
- research/competitive-templates.md (priority 7)
```

### Enhanced Handoff Block

```json
"handoff": {
  "output_artifacts": [
    "README.md",
    "scope.md",
    "constraints.md",
    "success-criteria.md",
    "decisions-ledger.md",
    "artifact-manifest.md"
  ],
  "next_phase_context": [
    "README.md",
    "scope.md",
    "constraints.md"
  ],
  "excluded_files": [
    "research/sme-interviews.md"
  ],
  "context_update": {
    "decisions-ledger.md": "append",
    "artifact-manifest.md": "update"
  },
  "skill_validation": "none"
}
```

**All handoff fields:**

| Field | Type | Description |
|-------|------|-------------|
| `output_artifacts` | array | Files produced by this phase |
| `next_phase_context` | array | Files needed by next phase |
| `excluded_files` | array | Explicit files to exclude from context (replaces vague `excluded_context`) |
| `context_update` | object | How persistent files change |
| `skill_validation` | string | Skill to run after phase (replaces `skill`) |

**Context update semantics:**

| Value | Meaning | Example |
|-------|---------|---------|
| `append` | File grows, never shrinks | decisions-ledger.md |
| `update` | File contents change, same file | artifact-manifest.md |
| `create` | New file created this phase | scope.md (Phase 0) |

**Note:** `phase_complete_markers` has been removed. Use `gate_conditions` in the gate task for verification.

---

## JSON Schema Extension

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "defaults": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "description": "Default model: opus, sonnet, haiku, or provider:model format"
        },
        "model_fallbacks": {
          "type": "object",
          "description": "Fallback chains for unavailable models",
          "additionalProperties": {
            "type": "array",
            "items": { "type": "string" }
          }
        },
        "context_budget_tokens": {
          "type": "integer",
          "minimum": 1000
        },
        "system_prompt_budget": {
          "type": "integer",
          "minimum": 500,
          "default": 2000
        },
        "critical_priority_threshold": {
          "type": "integer",
          "minimum": 1,
          "maximum": 10,
          "default": 3
        },
        "temperature": {
          "type": "number",
          "minimum": 0,
          "maximum": 2
        },
        "max_tokens": {
          "type": "integer",
          "minimum": 256
        }
      }
    },
    "roles": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["description"],
        "properties": {
          "description": { "type": "string" },
          "defaults": {
            "type": "object",
            "properties": {
              "model": { "type": "string" },
              "temperature": {
                "type": "array",
                "items": { "type": "number" },
                "minItems": 2,
                "maxItems": 2
              }
            }
          },
          "temperature_rationale": { "type": "string" }
        }
      }
    },
    "checklists": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "compilation": {
            "type": "object",
            "required": ["context_load", "role_mindset", "objective"],
            "properties": {
              "context_load": {
                "type": "array",
                "items": { "type": "string" }
              },
              "role_mindset": { "type": "string" },
              "objective": { "type": "string" },
              "pre_check": {
                "type": "array",
                "items": { "type": "string" }
              },
              "failure_modes_relevant": {
                "type": "array",
                "items": { "type": "string" }
              },
              "agent_config": {
                "type": "object",
                "properties": {
                  "model": { "type": "string" },
                  "temperature": { "type": "number", "minimum": 0, "maximum": 2 },
                  "max_tokens": { "type": "integer", "minimum": 256 }
                }
              },
              "system_prompt_auto": {
                "type": "object",
                "properties": {
                  "role_definition": { "type": "boolean", "default": true },
                  "phase_objective": { "type": "boolean", "default": true },
                  "failure_modes": { "type": "boolean", "default": true },
                  "pre_check_guidance": { "type": "boolean", "default": true },
                  "context_files": { "type": "boolean", "default": true },
                  "handoff_requirements": { "type": "boolean", "default": true }
                }
              },
              "context_budget": {
                "type": "object",
                "properties": {
                  "max_tokens": { "type": "integer" },
                  "priority": {
                    "type": "object",
                    "additionalProperties": {
                      "type": "integer",
                      "minimum": 1,
                      "maximum": 10
                    }
                  }
                }
              },
              "skill_preparation": { "type": "string" }
            }
          },
          "handoff": {
            "type": "object",
            "properties": {
              "output_artifacts": {
                "type": "array",
                "items": { "type": "string" }
              },
              "next_phase_context": {
                "type": "array",
                "items": { "type": "string" }
              },
              "excluded_files": {
                "type": "array",
                "items": { "type": "string" }
              },
              "context_update": {
                "type": "object",
                "additionalProperties": {
                  "type": "string",
                  "enum": ["append", "update", "create"]
                }
              },
              "skill_validation": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

## Validation Rules

The following validation rules must be enforced:

### Context Load Validation

```
1. All files in context_budget.priority MUST exist in context_load
   ERROR: File "scope.md" in priority but not in context_load

2. Files in context_load without priority get default 5
   INFO: "research/domain-analysis.md" assigned default priority 5

3. Total critical files (priority <= threshold) MUST fit within budget
   ERROR: Critical files exceed budget (see Error handling)
```

### Handoff Chain Validation

```
1. Phase N handoff.next_phase_context MUST be subset of Phase N+1 compilation.context_load
   ERROR: Phase 1 handoff includes "scope.md" but Phase 2 context_load missing it

2. Phase N handoff.excluded_files MUST NOT appear in next_phase_context
   WARNING: "research/sme-interviews.md" excluded but not in next_phase_context anyway
```

### Model Validation

```
1. If model_fallbacks specified, all fallback models must be valid
   ERROR: Fallback model "invalid-model" not recognized

2. Fallback chain must have at least one model available
   ERROR: No available model in chain: opus -> sonnet -> haiku (none available)
```

---

## Backward Compatibility

All new fields are optional:

| Field | Behavior if Omitted |
|-------|---------------------|
| `defaults` | Use hardcoded defaults |
| `defaults.model_fallbacks` | No fallback (error if model unavailable) |
| `defaults.system_prompt_budget` | Use 2000 tokens |
| `defaults.critical_priority_threshold` | Use 3 |
| `roles.{role}.defaults` | Use playbook defaults |
| `agent_config` | Use playbook/role defaults |
| `system_prompt_auto` | All flags default to `true` |
| `context_budget` | Use playbook default, all files priority 5 |
| `context_budget.priority` | All files default to priority 5 |
| `handoff.excluded_files` | Replaces `excluded_context` (deprecated) |
| `skill_preparation` | No skill runs before phase |
| `skill_validation` | Replaces `skill` (deprecated) |

**Deprecated fields (still work but prefer new):**

| Old | New |
|-----|-----|
| `handoff.excluded_context` (array of descriptions) | `handoff.excluded_files` (array of filenames) |
| `handoff.skill` | `handoff.skill_validation` |

---

## Implementation Checklist

- [ ] Add `defaults` section to playbook JSON schema with all new fields
- [ ] Add `roles.{role}.defaults` structure to role definitions
- [ ] Add `agent_config` to compilation block schema
- [ ] Add `system_prompt_auto` to compilation block schema
- [ ] Add `context_budget` to compilation block schema (max_tokens optional)
- [ ] Add `skill_preparation` to compilation block
- [ ] Replace `excluded_context` with `excluded_files` in handoff
- [ ] Replace `skill` with `skill_validation` in handoff
- [ ] Remove `phase_complete_markers` (redundant with gate_conditions)
- [ ] Update output-schema.json with new fields
- [ ] Create system prompt generator function
- [ ] Create context budget loader with priority ordering and critical protection
- [ ] Create model fallback resolver
- [ ] Create artifact-manifest description reader
- [ ] Create failure mode lookup from `failure_modes` array
- [ ] Update validate_playbook.py with new validation rules
- [ ] Add handoff chain validation
- [ ] Add priority-to-context_load validation
- [ ] Document all new fields in playbook creator spec
- [ ] Create migration guide for existing playbooks

---

## Example: Complete Phase 0 with All Enhancements

```json
{
  "title": "Phase 0: Commission & Scoping",
  "purpose": "Define exactly what playbook is being built, for whom, and under what constraints. Nothing else starts until this is locked.",
  "compilation": {
    "context_load": [
      "README.md"
    ],
    "role_mindset": "Stakeholder",
    "objective": "Lock purpose, scope, constraints, and success criteria so every subsequent phase has a fixed target",
    "pre_check": [
      "User has provided a commission brief or verbal description of the playbook they want"
    ],
    "failure_modes_relevant": [],
    "agent_config": {
      "model": "opus",
      "temperature": 0.2,
      "max_tokens": 4096
    },
    "system_prompt_auto": {
      "role_definition": true,
      "phase_objective": true,
      "failure_modes": true,
      "pre_check_guidance": true,
      "context_files": false,
      "handoff_requirements": true
    },
    "context_budget": {
      "max_tokens": 16000,
      "priority": {
        "README.md": 1
      }
    },
    "skill_preparation": "none"
  },
  "items": [
    {
      "title": "[Coordinator] — Create project knowledge base folder",
      "owner": "[Coordinator]",
      "description": "Folder structure: README.md, research/, architecture/, drafts/, audits/, testing/, final/...",
      "output": "README.md, project folder structure, decisions-ledger.md, artifact-manifest.md"
    },
    {
      "title": "[Stakeholder] — Define the playbook's purpose and problem statement",
      "owner": "[Stakeholder]",
      "description": "Answer precisely: What process does this playbook automate/guide?...",
      "output": "README.md (purpose statement)"
    }
  ],
  "handoff": {
    "output_artifacts": [
      "README.md",
      "scope.md",
      "constraints.md",
      "success-criteria.md",
      "decisions-ledger.md",
      "artifact-manifest.md"
    ],
    "next_phase_context": [
      "README.md",
      "scope.md",
      "constraints.md"
    ],
    "excluded_files": [],
    "context_update": {
      "decisions-ledger.md": "append",
      "artifact-manifest.md": "update",
      "scope.md": "create",
      "constraints.md": "create",
      "success-criteria.md": "create"
    },
    "skill_validation": "none"
  }
}
```

---

## Example: Phase with Critical File Protection

```json
{
  "title": "Phase 9: Quality Audit — Gap Analysis",
  "compilation": {
    "context_load": [
      "README.md",
      "scope.md",
      "constraints.md",
      "requirements.md",
      "phase-structure.md",
      "task-list.md",
      "playbook-v0.1.json",
      "decisions-ledger.md",
      "artifact-manifest.md"
    ],
    "role_mindset": "Auditor",
    "objective": "Find gaps, contradictions, and missing coverage in the playbook",
    "failure_modes_relevant": ["FM-007", "FM-008", "FM-012"],
    "agent_config": {
      "model": "opus",
      "temperature": 0.1
    },
    "context_budget": {
      "max_tokens": 100000,
      "priority": {
        "README.md": 1,
        "scope.md": 1,
        "constraints.md": 1,
        "requirements.md": 2,
        "phase-structure.md": 2,
        "task-list.md": 2,
        "playbook-v0.1.json": 3,
        "decisions-ledger.md": 4,
        "artifact-manifest.md": 4
      }
    }
  }
}
```

In this example:
- Critical files (priority 1-3) cannot be skipped
- If budget is insufficient, phase halts with error
- Auditor role uses opus with low temperature (0.1) for precision

---

## Example: Model Fallback in Action

```json
{
  "defaults": {
    "model": "opus",
    "model_fallbacks": {
      "opus": ["sonnet", "haiku"],
      "glm-5:cloud": ["sonnet", "opus"]
    }
  },
  "roles": {
    "Researcher": {
      "defaults": { "model": "sonnet" }
    }
  },
  "checklists": [
    {
      "title": "Phase 1: Domain Research",
      "compilation": {
        "role_mindset": "Researcher",
        "agent_config": { "model": "haiku" }
      }
    }
  ]
}
```

**Model resolution for Phase 1:**
1. Phase specifies `haiku` → use `haiku`
2. If `haiku` unavailable → check fallback chain (none specified)
3. If no chain → use `sonnet` from Researcher defaults
4. If `sonnet` unavailable → check fallback chain: `sonnet` → `haiku`
5. Result: `haiku` or `sonnet` depending on availability

---

*Design version 2.0 completed: 2026-03-31*
*Post-audit revision addressing 15 identified issues*