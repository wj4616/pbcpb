# Playbook Creator Configuration Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configuration task to Phase 0 that establishes output location and external data permissions before any other work begins.

**Architecture:** Insert a new Coordinator task as the first task in Phase 0. Add gate conditions for configuration. Add cross-cutting concern CCC-CONFIG. Update context preservation rules.

**Tech Stack:** JSON modification, no external dependencies.

---

## Files Modified

| File | Change |
|------|--------|
| `playbook-creator-playbook.json` | Add configuration task, gate condition, cross-cutting concern, context preservation rules, update phase_summary |

---

### Task 1: Add Configuration Task to Phase 0

**Files:**
- Modify: `playbook-creator-playbook.json` (line ~294, items array)

- [ ] **Step 1: Locate Phase 0 items array**

The items array for Phase 0 starts at line 294. The first task is "[Coordinator] — Create project knowledge base folder".

- [ ] **Step 2: Add new configuration task before the first existing task**

Insert this task object at the beginning of the items array:

```json
        {
          "title": "[Coordinator] — Establish configuration",
          "owner": "[Coordinator]",
          "description": "Ask the user to establish runtime configuration before any other work begins:\n\n1. OUTPUT LOCATION\n   - Default: ~/playbooks/<playbook-name>/\n   - Ask: \"Save location: ~/playbooks/<playbook-name>/ — correct, or specify different path?\"\n   - If user specifies different path: use exact path provided\n   - If directory exists: create ~/playbooks/<playbook-name>-v2/ (or next available: -v3, -v4, etc.)\n   - Never merge or replace existing content in any directory\n\n2. EXTERNAL DATA SOURCES\n   - Ask item-by-item with explicit paths:\n     * \"Pull knowledge base from [path]? (yes/no)\"\n     * \"Pull other playbooks from [path]? (yes/no)\"\n     * \"Pull references from [path]? (yes/no)\"\n   - Record all decisions in scope.md configuration section\n   - Only access sources user explicitly approved\n   - If no external sources needed, document \"No external data sources required\"\n\nOutput: scope.md with configuration section documenting all decisions.",
          "output": "scope.md (configuration section)"
        },
```

- [ ] **Step 3: Verify JSON syntax is valid**

The new task must be a valid JSON object within the items array. Ensure comma placement is correct between tasks.

- [ ] **Step 4: Commit**

```bash
git add playbook-creator-playbook.json
git commit -m "feat: add configuration task to Phase 0 (establish output location + external data permissions)"
```

---

### Task 2: Add Gate Conditions for Configuration

**Files:**
- Modify: `playbook-creator-playbook.json` (Phase 0 gate task, ~line 353)

- [ ] **Step 1: Locate Phase 0 gate task**

Find the task with title "[Coordinator] — Phase gate: Purpose defined, scope locked, constraints documented, success criteria measurable, knowledge base initialized"

- [ ] **Step 2: Add configuration gate condition**

Add this condition to the `gate_conditions` array:

```json
            "Configuration established (output location + external data decisions documented in scope.md)"
```

The gate_conditions array should now include this condition before "Phase inventory: all 16 phases acknowledged".

- [ ] **Step 3: Add blocker example**

Add this to the `blocker_examples` array:

```json
            "scope.md missing configuration section — ask user for output location and external data permissions before proceeding"
```

- [ ] **Step 4: Commit**

```bash
git add playbook-creator-playbook.json
git commit -m "feat: add configuration gate condition to Phase 0"
```

---

### Task 3: Add Cross-Cutting Concern CCC-CONFIG

**Files:**
- Modify: `playbook-creator-playbook.json` (cross_cutting_concerns array)

- [ ] **Step 1: Locate cross_cutting_concerns array**

Find the `cross_cutting_concerns` array in the playbook JSON. It's after the `scope` section.

- [ ] **Step 2: Add CCC-CONFIG concern**

Add this object to the array:

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

- [ ] **Step 3: Commit**

```bash
git add playbook-creator-playbook.json
git commit -m "feat: add CCC-CONFIG cross-cutting concern for path configuration"
```

---

### Task 4: Update Context Preservation Rules

**Files:**
- Modify: `playbook-creator-playbook.json` (context_preservation section, ~line 2873)

- [ ] **Step 1: Locate context_preservation.rules array**

Find the `context_preservation` object and its `rules` array.

- [ ] **Step 2: Add configuration rules**

Add these two rules to the `rules` array:

```json
      "Configuration decisions (output location, external data sources) from scope.md are ALWAYS loaded in context",
      "If scope.md is missing configuration section, halt and request Phase 0 completion"
```

- [ ] **Step 3: Commit**

```bash
git add playbook-creator-playbook.json
git commit -m "feat: add context preservation rules for configuration decisions"
```

---

### Task 5: Update Phase Summary

**Files:**
- Modify: `playbook-creator-playbook.json` (phase_summary array, ~line 5)

- [ ] **Step 1: Locate phase_summary array**

Find the `phase_summary` array near the top of the file.

- [ ] **Step 2: Update Phase 0 summary**

Change line 6 from:
```json
    "Phase 0: Commission & Scoping — Define purpose, scope, constraints, complexity profile. Agent must acknowledge all 16 phases.",
```

To:
```json
    "Phase 0: Commission & Scoping — Establish configuration (output location, external data permissions), define purpose, scope, constraints, complexity profile. Agent must acknowledge all 16 phases.",
```

- [ ] **Step 3: Commit**

```bash
git add playbook-creator-playbook.json
git commit -m "feat: update Phase 0 summary to include configuration"
```

---

### Task 6: Update Scope Output Reference

**Files:**
- Modify: `playbook-creator-playbook.json` (multiple locations)

- [ ] **Step 1: Find all scope.md references**

Search for tasks that output to `scope.md`. There should be a task "[Stakeholder] — Define scope boundaries" that outputs to scope.md.

- [ ] **Step 2: Verify configuration task outputs to scope.md**

The new configuration task already outputs to `scope.md` with `(configuration section)`. Ensure this is clear that it creates the initial scope.md with the configuration section.

- [ ] **Step 3: Update handoff references**

In the Phase 0 gate handoff block, verify `scope.md` is listed in `output_artifacts`. If not, add it.

- [ ] **Step 4: Commit**

```bash
git add playbook-creator-playbook.json
git commit -m "fix: ensure scope.md with configuration is in handoff output_artifacts"
```

---

### Task 7: Verification Test

**Files:**
- Test: `playbook-creator-playbook.json`

- [ ] **Step 1: Validate JSON syntax**

```bash
cd ~/Documents/pbcpb && python3 -c "import json; json.load(open('playbook-creator-playbook.json'))" && echo "JSON valid"
```

Expected: "JSON valid"

- [ ] **Step 2: Verify Phase 0 has configuration task as first item**

```bash
cd ~/Documents/pbcpb && python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
phases = data.get('checklists', [])
phase0 = next((p for p in phases if 'Phase 0' in p.get('title', '')), None)
if phase0:
    items = phase0.get('items', [])
    first_task = items[0] if items else None
    if first_task and 'Establish configuration' in first_task.get('title', ''):
        print('PASS: Configuration task is first task in Phase 0')
    else:
        print('FAIL: Configuration task not found as first task')
        print(f'First task: {first_task.get(\"title\", \"unknown\") if first_task else \"none\"}')
else:
    print('FAIL: Phase 0 not found')
"
```

Expected: "PASS: Configuration task is first task in Phase 0"

- [ ] **Step 3: Verify gate condition includes configuration**

```bash
cd ~/Documents/pbcpb && python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
phases = data.get('checklists', [])
phase0 = next((p for p in phases if 'Phase 0' in p.get('title', '')), None)
if phase0:
    gate_task = next((t for t in phase0.get('items', []) if 'Phase gate' in t.get('title', '')), None)
    if gate_task:
        conditions = gate_task.get('gate_conditions', [])
        config_found = any('Configuration established' in c for c in conditions)
        if config_found:
            print('PASS: Gate condition includes configuration')
        else:
            print('FAIL: Gate condition missing configuration')
            print(f'Conditions: {conditions}')
    else:
        print('FAIL: No gate task found')
else:
    print('FAIL: Phase 0 not found')
"
```

Expected: "PASS: Gate condition includes configuration"

- [ ] **Step 4: Verify CCC-CONFIG exists**

```bash
cd ~/Documents/pbcpb && python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
concerns = data.get('cross_cutting_concerns', [])
ccc_config = next((c for c in concerns if c.get('id') == 'CCC-CONFIG'), None)
if ccc_config:
    print('PASS: CCC-CONFIG cross-cutting concern exists')
else:
    print('FAIL: CCC-CONFIG not found')
"
```

Expected: "PASS: CCC-CONFIG cross-cutting concern exists"

- [ ] **Step 5: Verify context preservation rules**

```bash
cd ~/Documents/pbcpb && python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
rules = data.get('context_preservation', {}).get('rules', [])
config_found = any('Configuration decisions' in r for r in rules)
if config_found:
    print('PASS: Context preservation includes configuration rules')
else:
    print('FAIL: Configuration rules not found in context preservation')
"
```

Expected: "PASS: Context preservation includes configuration rules"

- [ ] **Step 6: Final commit if needed**

If any fixes were required, commit them:
```bash
git add playbook-creator-playbook.json
git commit -m "fix: verification test fixes"
```

---

## Self-Review Checklist

- [x] Spec coverage: Each requirement from the design doc maps to a task
- [x] No placeholders: Every code block contains actual JSON content
- [x] Type consistency: All JSON objects use consistent property names
- [x] File paths: All modifications reference exact locations in the JSON

---

Plan complete and saved to `docs/superpowers/plans/2026-04-02-playbook-creator-config-plan.md`. 

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?