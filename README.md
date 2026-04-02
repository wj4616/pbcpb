# Playbook Creator

Meta-playbook for creating domain-specific playbooks. Works with single-agent systems where one agent fills multiple roles.

## Files

- `playbook-creator-playbook.json` - The main playbook creator (17 phases)
- `templates/output-schema.json` - Schema for validating produced playbooks
- `templates/role-mapping.json` - Reference for @handle to [Role] transformation
- `scripts/compilation/` - Compilation block utilities for agent configuration

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

## Role Mapping

| Original | New Role |
|----------|----------|
| @minion | [Coordinator] |
| @isaac | [Approver] |
| @piper | [Researcher] |
| @forge | [Implementer] |
| @lux | [Architect] |
| @kira | [Reviewer] |
| @axiom | [Auditor] |

## Phases

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
| 12 | Quality Audit — Stress Testing |
| 13 | Stakeholder Review & Iteration |
| 14 | Pilot / Structured Dry-Run |
| 15 | Documentation & Version Control |
| 16 | Continuous Improvement |

## Key Differences from Original Mattermost Playbook

- Removed Mattermost-specific fields (channel_name_template, message_on_join, reminder_timer_default_seconds)
- Replaced @handles with [Role] placeholders for single-agent compatibility
- Added pilot alternatives for single-agent execution (Solo, AI Adversarial, Peer Review)
- Added cross_cutting_concerns section with integration guidance
- Added deliverables section for outputs per phase
- Added explicit phase gates with conditions and blocker_examples
- Added role_execution_guidance for single-agent, multi-agent, and AI-assisted workflows

## Self-Review Checklist

Before using the produced playbook:

- [ ] All JSON files validate without errors
- [ ] No @handle references remain (all transformed to [Role])
- [ ] All 12 phases (0-11) present with full task content
- [ ] Each phase has gate object with conditions and blocker_examples
- [ ] deliverables section defines outputs per phase
- [ ] cross_cutting_concerns documented
- [ ] metrics section complete
- [ ] usage_instructions includes all three execution models