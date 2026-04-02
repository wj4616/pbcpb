# Playbook Creator

Meta-playbook for creating domain-specific playbooks. Works with single-agent systems where one agent fills multiple roles.

## Files

- `playbook-creator-playbook.json` - The main playbook creator (16 phases)
- `templates/output-schema.json` - Schema for validating produced playbooks
- `templates/role-mapping.json` - Reference for @handle to [Role] transformation
- `scripts/compilation/` - Compilation block utilities for agent configuration
- `scripts/generate_scaffold.py` - Generate a valid skeleton playbook JSON
- `scripts/show_handoff.py` - Show what files to load between sessions
- `USAGE.md` - Comprehensive usage guide for end users

## Usage

1. Load `playbook-creator-playbook.json` as context for a planning session
2. Follow phases sequentially, passing each gate before proceeding
3. Output: A domain-specific playbook matching `output-schema.json`

## Execution Models

| Model | Description |
|-------|-------------|
| Single-agent | One person/AI fills all roles, switches mindset per phase |
| Multi-agent | Each role maps to different person/agent |
| AI-assisted | Human = Stakeholder/Coordinator, AI = Researcher/Builder/Architect |

## Compilation Block

Each phase has a compilation block that configures the agent:

```json
"compilation": {
  "context_load": ["file paths"],
  "role_mindset": "Role — focus",
  "objective": "Phase objective",
  "pre_check": ["conditions"],
  "failure_modes_relevant": ["FM-001"],
  "agent_config": { "model": "opus", "temperature": 0.5 },
  "system_prompt_auto": { "role_definition": true, ... },
  "context_budget": { "max_tokens": 64000, "priority": {...} },
  "skill_preparation": "none"
}
```

### Model Resolution

Model selection follows priority order:
1. Phase `agent_config.model` (highest)
2. Role `defaults.model` (medium)
3. Playbook `defaults.model` (lowest)
4. Hardcoded default (`opus`)

If a model is unavailable, fallback chains are used.

### Context Budget

Files are loaded in priority order (1=highest, 10=lowest). Critical files (priority ≤ threshold) cannot be skipped even if budget is exceeded.

### Role Defaults

Roles can override playbook defaults:

```json
"roles": {
  "Researcher": {
    "description": "Domain research",
    "defaults": {
      "model": "sonnet",
      "temperature": [0.4, 0.7]
    }
  }
}
```

## Scripts

The `scripts/compilation/` module provides utilities:

- `constants.py` - Default values for model, budget, thresholds
- `model_fallback.py` - Model resolution with fallback chains
- `context_budget.py` - Priority-based context loading
- `system_prompt.py` - System prompt generation

## Validation

Run `scripts/validate_playbook.py` to check playbook structure:

```bash
python3 scripts/validate_playbook.py playbook-creator-playbook.json
```

Validation includes:
- Required top-level fields
- Role consistency (used in tasks, defined in roles)
- Handoff chain continuity
- Priority file references exist in context_load
- Model/temperature/budget ranges

## Roles

| Role | Responsibility | Primary Phases |
|------|----------------|----------------|
| Coordinator | Phase gates, tracking, status updates, blocker escalation | Every gate |
| Researcher | Domain research, best practices, SME knowledge, competitive analysis | 1 |
| Architect | Phase structure, task granularity, role design, dependency mapping | 2, 4-8 |
| Builder | Task titles/descriptions, JSON assembly, validation, fixes | 3, 6-10 |
| Auditor | Quality review, scenario walkthroughs, gap analysis, stress testing | 10-12 |
| Stakeholder | Purpose, scope, constraints, success criteria, final approval | 0, 13 |

## Phases (16)

| Phase | Purpose |
|-------|---------|
| 0 | Commission & Scoping |
| 1 | Domain Research & Process Discovery |
| 2 | KB Architecture |
| 3 | KB Bootstrapping |
| 4 | Process Architecture |
| 5 | Role Engineering |
| 6 | Task Engineering |
| 7 | Output Configuration |
| 8 | Metrics & KPI Definition |
| 9 | JSON Assembly |
| 10 | JSON Validation & Consistency |
| 11 | Quality Audit — Gap Analysis |
| 12 | Stress Testing & Structured Dry-Run |
| 13 | Stakeholder Review & Iteration |
| 14 | Documentation & Version Control |
| 15 | Continuous Improvement |

## Self-Review Checklist

Before using the produced playbook:

- [ ] All JSON files validate without errors (`python3 scripts/validate_playbook.py`)
- [ ] Semantic checks pass (`python3 scripts/validate_semantic.py`)
- [ ] All 16 phases (0-15) present with full task content
- [ ] Each phase has compilation block and gate with conditions
- [ ] Handoff chain is continuous (each phase's context_load matches prior phase's output)
- [ ] All roles used in tasks are defined in roles{}
- [ ] metrics section complete
- [ ] usage_instructions includes execution models

## Development History

The `docs/development-history/` directory contains archived design specs and
implementation plans from the original development. These are not required to
use the playbook — see the README in that directory for details.