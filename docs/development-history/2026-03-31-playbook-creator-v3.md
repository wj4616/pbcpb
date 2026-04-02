# Playbook Creator v3 Implementation Plan

> **Status: COMPLETED.** This plan was executed against `/home/myuser/Documents/playbookdev/`. All tasks are done — the checkboxes were not updated during execution. Paths in this document reference the original working directory, not this portable copy.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the playbook-creator-playbook v3 design spec — 9 friction points resolved, 2 new phases, 20 failure modes, structured CCCs, metrics measurement, complexity governance, multi-agent role support.

**Architecture:** Four files change: the playbook JSON (structural changes + content additions), the validator script (new checks), the output schema (new fields), and system_prompt.py (role_context extraction). Tooling updates go first so we can validate incrementally. JSON changes are grouped by dependency: top-level fields → phase structure → per-gate enhancements → summary views.

**Tech Stack:** Python 3, JSON, JSON Schema (draft-07)

**Spec:** `/home/myuser/Documents/playbookdev/specs/2026-03-31-playbook-creator-v3-design.md`

---

### Task 1: Update validator — new constants and persistent set

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/scripts/validate_playbook.py:34-36,41,446,491`

This task adds the foundation for all subsequent validator changes: the new workflow_model enum value, the metrics-tracker persistent file, and the MET-ID pattern.

- [ ] **Step 1: Write test — verify validator rejects "role-based-multi-agent" currently**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json, copy
with open('playbook-creator-playbook.json') as f:
    pb = json.load(f)
pb['workflow_model'] = 'role-based-multi-agent'
with open('/tmp/test_wm.json', 'w') as f:
    json.dump(pb, f)
from scripts.validate_playbook import validate
errors = validate('/tmp/test_wm.json')
wm_errors = [e for e in errors if 'workflow_model' in e]
assert len(wm_errors) > 0, 'Expected workflow_model error'
print('PASS: role-based-multi-agent currently rejected')
"
```

- [ ] **Step 2: Add "role-based-multi-agent" to VALID_WORKFLOW_MODELS (line 34-36)**

Change line 34-36 from:

```python
VALID_WORKFLOW_MODELS = {
    "human-in-the-loop", "fully-autonomous", "human-directed", "role-based-single-agent"
}
```

To:

```python
VALID_WORKFLOW_MODELS = {
    "human-in-the-loop", "fully-autonomous", "human-directed",
    "role-based-single-agent", "role-based-multi-agent"
}
```

- [ ] **Step 3: Add MET_ID_PATTERN constant after FM_ID_PATTERN (line 41)**

After line 41 (`FM_ID_PATTERN = re.compile(r"^FM-\d{3}$")`), add:

```python
MET_ID_PATTERN = re.compile(r"^MET-\d{2}$")
CCC_ID_PATTERN = re.compile(r"^CCC-\d{2}$")
VALID_ENFORCEMENT_METHODS = {
    "checklist_items", "gate_condition", "compilation_precheck", "task_description"
}
```

- [ ] **Step 4: Add "metrics-tracker" to persistent set (line 446)**

Change line 446 from:

```python
    persistent = {"decisions-ledger", "artifact-manifest"}
```

To:

```python
    persistent = {"decisions-ledger", "artifact-manifest", "metrics-tracker"}
```

- [ ] **Step 5: Verify validator still passes on current v2 playbook**

```bash
cd /home/myuser/Documents/playbookdev
python3 scripts/validate_playbook.py playbook-creator-playbook.json
```

Expected: `PASS: All structural checks passed`

- [ ] **Step 6: Verify "role-based-multi-agent" is now accepted**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    pb = json.load(f)
pb['workflow_model'] = 'role-based-multi-agent'
with open('/tmp/test_wm.json', 'w') as f:
    json.dump(pb, f)
from scripts.validate_playbook import validate
errors = validate('/tmp/test_wm.json')
wm_errors = [e for e in errors if 'workflow_model' in e]
assert len(wm_errors) == 0, f'Unexpected workflow_model error: {wm_errors}'
print('PASS: role-based-multi-agent now accepted')
"
```

---

### Task 2: Update validator — CCC object validation

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/scripts/validate_playbook.py:431-434`

- [ ] **Step 1: Write test — verify validator accepts string CCCs (backward compat)**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
from scripts.validate_playbook import validate
errors = validate('playbook-creator-playbook.json')
ccc_errors = [e for e in errors if 'cross_cutting' in e.lower()]
assert len(ccc_errors) == 0, f'Unexpected CCC error: {ccc_errors}'
print('PASS: string CCCs accepted')
"
```

- [ ] **Step 2: Replace CCC non-empty check (lines 431-434) with object validation**

Replace lines 431-434:

```python
    # 14. Cross-cutting concerns non-empty
    ccc = data.get("cross_cutting_concerns", [])
    if not ccc:
        errors.append("cross_cutting_concerns is empty")
```

With:

```python
    # 14. Cross-cutting concerns non-empty + object validation
    ccc = data.get("cross_cutting_concerns", [])
    if not ccc:
        errors.append("cross_cutting_concerns is empty")
    else:
        ccc_ids = set()
        for idx, item in enumerate(ccc):
            if isinstance(item, str):
                continue  # Backward compatible string format
            elif isinstance(item, dict):
                for req_field in ("id", "title", "description", "enforcement_method", "minimum_phases"):
                    if req_field not in item:
                        errors.append(f"cross_cutting_concerns[{idx}]: missing '{req_field}'")
                ccc_id = item.get("id", "")
                if ccc_id:
                    if not CCC_ID_PATTERN.match(ccc_id):
                        errors.append(f"cross_cutting_concerns[{idx}]: id '{ccc_id}' doesn't match CCC-NN")
                    if ccc_id in ccc_ids:
                        errors.append(f"Duplicate CCC-ID: {ccc_id}")
                    ccc_ids.add(ccc_id)
                em = item.get("enforcement_method", "")
                if em and em not in VALID_ENFORCEMENT_METHODS:
                    errors.append(f"cross_cutting_concerns[{idx}]: enforcement_method '{em}' not valid")
                min_phases = item.get("minimum_phases", 0)
                phases_applied = item.get("phases_applied", [])
                if isinstance(min_phases, int) and isinstance(phases_applied, list):
                    if len(phases_applied) < min_phases:
                        errors.append(
                            f"cross_cutting_concerns[{idx}] ({ccc_id}): "
                            f"phases_applied has {len(phases_applied)} entries, minimum_phases is {min_phases}"
                        )
            else:
                errors.append(f"cross_cutting_concerns[{idx}]: must be string or object")
```

- [ ] **Step 3: Run validator — still passes on v2 (string CCCs)**

```bash
cd /home/myuser/Documents/playbookdev
python3 scripts/validate_playbook.py playbook-creator-playbook.json
```

Expected: `PASS: All structural checks passed`

---

### Task 3: Update validator — metric ID, guardrail_checks, metrics_snapshot, role fields

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/scripts/validate_playbook.py:295-302,356-364,420-429`

- [ ] **Step 1: Add guardrail_checks validation inside the gate detection block (after line 302)**

After line 302 (`errors.append(f"{item_label}: gate missing handoff block")`), within the same `if "gate_conditions" in item:` block, before the `else:` on line 303 that starts handoff validation, add:

```python
                # Validate guardrail_checks (optional)
                if "guardrail_checks" in item:
                    gc = item["guardrail_checks"]
                    if not isinstance(gc, list):
                        errors.append(f"{item_label}: guardrail_checks must be an array")
                    elif not all(isinstance(g, str) for g in gc):
                        errors.append(f"{item_label}: guardrail_checks must contain strings")
```

- [ ] **Step 2: Add metrics_snapshot validation inside the handoff validation block (after line 339)**

After the `if "skill" in handoff:` deprecation warning block (line 337-339), add:

```python
                    # Validate metrics_snapshot
                    if "metrics_snapshot" in handoff:
                        ms = handoff["metrics_snapshot"]
                        if not isinstance(ms, dict):
                            errors.append(f"{item_label}: metrics_snapshot must be an object")
                        else:
                            if "collect" not in ms:
                                errors.append(f"{item_label}: metrics_snapshot missing 'collect'")
                            elif not isinstance(ms["collect"], list):
                                errors.append(f"{item_label}: metrics_snapshot.collect must be an array")
                            if "record_in" not in ms:
                                errors.append(f"{item_label}: metrics_snapshot missing 'record_in'")
                            elif not isinstance(ms["record_in"], str):
                                errors.append(f"{item_label}: metrics_snapshot.record_in must be a string")

                    # Validate kb_status
                    if "kb_status" in handoff:
                        ks = handoff["kb_status"]
                        if not isinstance(ks, dict):
                            errors.append(f"{item_label}: kb_status must be an object")
```

- [ ] **Step 3: Add metric ID validation to metrics section (extend lines 420-429)**

After the existing metric validation block (line 429), add metric ID validation:

```python
    # 13b. Metric ID validation (required for version >= 3)
    met_ids = set()
    version = data.get("version", 1)
    for m in metrics:
        mid = m.get("id")
        if mid:
            if not MET_ID_PATTERN.match(mid):
                errors.append(f"metric '{m.get('title', '?')}': id '{mid}' doesn't match MET-NN")
            if mid in met_ids:
                errors.append(f"Duplicate MET-ID: {mid}")
            met_ids.add(mid)
        elif version >= 3:
            errors.append(f"metric '{m.get('title', '?')}': missing id (required for version >= 3)")

    # 13c. Validate metrics_snapshot references
    for i, phase in enumerate(checklists):
        phase_label = phase.get("title", f"checklist[{i}]")
        for j, item in enumerate(phase.get("items", [])):
            ms = item.get("handoff", {}).get("metrics_snapshot", {})
            if ms and "collect" in ms and isinstance(ms["collect"], list) and met_ids:
                for ref in ms["collect"]:
                    if ref not in met_ids:
                        errors.append(f"{phase_label} item[{j}]: metrics_snapshot references unknown metric '{ref}'")
```

- [ ] **Step 4: Add role_context and agent_assignment validation (extend role validation, after line 163)**

Inside the `elif isinstance(role_def, dict):` block for role validation, after the temperature validation (around line 163), add:

```python
            # Validate role_context
            if "role_context" in role_def:
                if not isinstance(role_def["role_context"], str):
                    errors.append(f"Role '{role_name}' role_context must be a string")

            # Validate agent_assignment
            if "agent_assignment" in role_def:
                if not isinstance(role_def["agent_assignment"], str):
                    errors.append(f"Role '{role_name}' agent_assignment must be a string")
```

- [ ] **Step 5: Run validator — still passes on v2**

```bash
cd /home/myuser/Documents/playbookdev
python3 scripts/validate_playbook.py playbook-creator-playbook.json
```

Expected: `PASS: All structural checks passed`

---

### Task 4: Update output-schema.json — all new field definitions

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/templates/output-schema.json:29-32,94-111,124-127,253-254,257-289,296-310,345-353`

- [ ] **Step 1: Add "role-based-multi-agent" to workflow_model enum (line 31)**

Change line 31 from:

```json
      "enum": ["human-in-the-loop", "fully-autonomous", "human-directed", "role-based-single-agent"]
```

To:

```json
      "enum": ["human-in-the-loop", "fully-autonomous", "human-directed", "role-based-single-agent", "role-based-multi-agent"]
```

- [ ] **Step 2: Add role_context and agent_assignment to role object variant (after line 109)**

After `"temperature_rationale": { "type": "string" }` (line 109), add:

```json
              "role_context": {
                "type": "string",
                "description": "Baseline activation prompt for this role. Included in system prompt between description and role_mindset."
              },
              "agent_assignment": {
                "type": "string",
                "description": "Agent identifier for multi-agent systems. 'single' = one agent fills all roles (default). Only takes effect when workflow_model is 'role-based-multi-agent'.",
                "default": "single"
              }
```

- [ ] **Step 3: Change cross_cutting_concerns to support both strings and objects (lines 124-127)**

Replace:

```json
    "cross_cutting_concerns": {
      "type": "array",
      "items": { "type": "string" }
    },
```

With:

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
    },
```

- [ ] **Step 4: Add guardrail_checks to checklist item properties (after line 254)**

After `"blocker_examples": { "type": "array", "items": { "type": "string" } },` add:

```json
                "guardrail_checks": {
                  "type": "array",
                  "items": { "type": "string" },
                  "description": "Advisory checks presented to the human at gate. Unlike gate_conditions, these do not block advancement."
                },
```

- [ ] **Step 5: Add metrics_snapshot and kb_status to handoff properties (after line 287)**

After `"skill": { ... }` (the last handoff property, around line 287), add:

```json
                    "metrics_snapshot": {
                      "type": "object",
                      "required": ["collect", "record_in"],
                      "properties": {
                        "collect": {
                          "type": "array",
                          "items": { "type": "string", "pattern": "^MET-\\d{2}$" },
                          "minItems": 1
                        },
                        "record_in": { "type": "string" }
                      }
                    },
                    "kb_status": {
                      "type": "object",
                      "properties": {
                        "total_entries": { "type": "integer", "minimum": 0 },
                        "harvested": { "type": "integer", "minimum": 0 },
                        "placeholder": { "type": "integer", "minimum": 0 }
                      }
                    }
```

- [ ] **Step 6: Add optional id field to metrics items (after line 301)**

After `"required": ["title", "description", "type", "category", "measurement_method"],` (line 301), in the `properties` object, add:

```json
          "id": {
            "type": "string",
            "pattern": "^MET-\\d{2}$",
            "description": "Unique metric identifier. Required for version >= 3."
          },
```

- [ ] **Step 7: Add metrics_tracker to context_preservation (after line 350)**

After `"artifact_manifest": { "type": "string" },` (line 350), add:

```json
        "metrics_tracker": {
          "type": "string",
          "description": "Running log of metric values collected at phase gates"
        },
```

- [ ] **Step 8: Validate schema is valid JSON**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('templates/output-schema.json') as f:
    schema = json.load(f)
print(f'Schema loaded: {len(schema[\"properties\"])} top-level properties')
print('PASS: output-schema.json is valid JSON')
"
```

---

### Task 5: Update system_prompt.py — role_context extraction

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/scripts/compilation/system_prompt.py:62-66,77-78`
- Modify: `/home/myuser/Documents/playbookdev/scripts/compilation/test_system_prompt.py`

- [ ] **Step 1: Write failing test for role_context**

Add to `test_system_prompt.py` before `if __name__`:

```python
def test_prompt_with_role_context():
    """Test prompt includes role_context between description and mindset."""
    playbook = {
        "workflow_model": "role-based-single-agent",
        "roles": {
            "Builder": {
                "description": "Task titles/descriptions, JSON assembly, validation",
                "role_context": "Mechanical precision. Follow specifications exactly. No creative interpretation.",
                "defaults": {
                    "model": "sonnet",
                    "temperature": [0.2, 0.4]
                },
                "agent_assignment": "single"
            }
        },
        "failure_modes": []
    }

    phase = {
        "title": "Phase 3: Test",
        "compilation": {
            "role_mindset": "Builder — executing the KB blueprint",
            "objective": "Build the KB directory structure",
            "pre_check": [],
            "failure_modes_relevant": []
        },
        "items": []
    }

    prompt = generate_system_prompt(playbook, phase, {})

    assert "Task titles/descriptions" in prompt, "description missing"
    assert "Mechanical precision" in prompt, "role_context missing"
    assert "executing the KB blueprint" in prompt, "mindset missing"

    # Verify ordering: description before role_context before mindset
    desc_pos = prompt.index("Task titles/descriptions")
    ctx_pos = prompt.index("Mechanical precision")
    mindset_pos = prompt.index("executing the KB blueprint")
    assert desc_pos < ctx_pos < mindset_pos, (
        f"Wrong order: description@{desc_pos}, context@{ctx_pos}, mindset@{mindset_pos}"
    )
    print("PASS: test_prompt_with_role_context")
```

Add the call in `__main__`:

```python
if __name__ == "__main__":
    test_basic_prompt()
    test_prompt_with_object_role()
    test_prompt_with_flags_disabled()
    test_token_estimation()
    test_prompt_with_role_context()
    print("\nAll tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/myuser/Documents/playbookdev/scripts
python3 compilation/test_system_prompt.py
```

Expected: FAIL — `role_context missing`

- [ ] **Step 3: Update system_prompt.py — extract role_context (lines 62-66)**

Replace lines 62-66:

```python
    # Handle both string and object role definitions
    if isinstance(role_def, dict):
        role_description = role_def.get("description", "")
    else:
        role_description = role_def
```

With:

```python
    # Handle both string and object role definitions
    if isinstance(role_def, dict):
        role_description = role_def.get("description", "")
        role_context = role_def.get("role_context", "")
    else:
        role_description = role_def
        role_context = ""
```

- [ ] **Step 4: Update system_prompt.py — insert role_context in prompt (lines 77-78)**

Replace lines 77-78:

```python
    if flags.get("role_definition", True) and role_description:
        sections.append(f"{role_description}\n")
```

With:

```python
    if flags.get("role_definition", True) and role_description:
        sections.append(f"{role_description}")
        if role_context:
            sections.append(f"{role_context}")
        sections.append("")
```

- [ ] **Step 5: Run tests to verify all pass**

```bash
cd /home/myuser/Documents/playbookdev/scripts
python3 compilation/test_system_prompt.py
```

Expected: All 5 tests pass.

---

### Task 6: Playbook JSON — update top-level fields

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json:2-4,85-98,105-111,1881-1984,2028-2037`

This task updates version, description, scope, cross_cutting_concerns, metrics, usage_instructions, failure_modes, and context_preservation. Roles and phases come in later tasks.

- [ ] **Step 1: Update version and description (lines 2-4)**

Change:

```json
  "version": 2,
  "description": "Meta-playbook for creating domain-specific playbooks. Produces structured JSON playbooks through 15 phases of research, KB construction, architecture, task engineering, and validation. Works with single-agent systems where one agent fills multiple functional roles.",
```

To:

```json
  "version": 3,
  "description": "Meta-playbook for creating domain-specific playbooks. Produces structured JSON playbooks through 17 phases of research, KB construction and bootstrapping, architecture, task engineering, assembly, validation, and structured dry-run. Works with single-agent systems where one agent fills multiple functional roles; output playbooks may optionally use role-based-multi-agent with per-role agent_assignment.",
```

- [ ] **Step 2: Update scope (lines 85-98)**

Replace the scope object:

```json
  "scope": {
    "in_scope": [
      "Creating domain-specific playbook JSON files",
      "Knowledge base architecture specification",
      "Knowledge base bootstrapping (directory creation, placeholder seeding, initial harvesting)",
      "Quality audit and stress testing",
      "Structured dry-run validation with scenario matrix",
      "Failure mode cataloging across runs"
    ],
    "out_of_scope": [
      "Executing the produced playbook (that is the user's responsibility)",
      "Full KB curation and ongoing maintenance (the creator bootstraps the KB with placeholders and initial harvesting; full curation is the user's responsibility)",
      "Platform-specific deployment or hosting",
      "Multi-agent orchestration of the creation process itself (the creator runs as single-agent; output playbooks may use role-based-multi-agent with per-role agent_assignment)"
    ],
    "adjacent": [
      "Skills/prompting frameworks that may be activated per-phase",
      "Knowledge bases built from the produced KB specification",
      "CI/CD or version control for produced playbooks"
    ]
  },
```

- [ ] **Step 3: Update context_preservation (lines 2028-2037)**

Replace the context_preservation object:

```json
  "context_preservation": {
    "decisions_ledger": "decisions-ledger.md — append-only, one paragraph per phase gate: phase number, key decisions, constraints discovered, rejected alternatives with brief rationale",
    "artifact_manifest": "artifact-manifest.md — running index of every file: path, producing phase, status (active|superseded|archived), one-line summary",
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

- [ ] **Step 4: Update session_strategy (inside usage_instructions, lines 1956-1965)**

Replace the session_strategy array:

```json
    "session_strategy": [
      "Phases 0-1: Share a session (scoping and research are tightly coupled)",
      "Phases 2-3 (KB Architecture + Bootstrapping): Share a session — design then build",
      "Phase 4 (Process Architecture): Fresh session with new eyes on structure",
      "Phases 5-6 (Role + Task Engineering): Share a session — roles inform task writing",
      "Phases 7-8 (Output Config + Metrics): Share a session",
      "Phase 9 (JSON Assembly): Dedicated session — heaviest context load",
      "Phase 10 (JSON Validation): Fresh session — validate with fresh eyes",
      "Phases 11-12 (Gap Analysis + Stress Testing): Share a session — audit pair",
      "Phase 13 (Stakeholder Review): Human review gate — break session here",
      "Phase 14 (Pilot / Dry-Run): Dedicated session",
      "Phases 15-16 (Documentation + Improvement): Complete the cycle"
    ],
```

- [ ] **Step 5: Update how_to_run to mention metrics-tracker (lines 1948-1955)**

Replace:

```json
    "how_to_run": [
      "Load this playbook as context for a planning session",
      "A single agent fills all roles — switch mental context per phase",
      "Work through phases sequentially — each phase gate must pass before the next",
      "For each task: read the title and description, complete the work, verify completion",
      "At phase gates: verify all conditions are met before proceeding",
      "Final output: a domain-specific playbook JSON following output-schema.json"
    ],
```

With:

```json
    "how_to_run": [
      "Load this playbook as context for a planning session",
      "A single agent fills all roles — switch mental context per phase",
      "Work through phases sequentially — each phase gate must pass before the next",
      "For each task: read the title and description, complete the work, verify completion",
      "At phase gates: verify all conditions are met, collect metrics_snapshot if present, then proceed",
      "Final output: a domain-specific playbook JSON following output-schema.json"
    ],
```

- [ ] **Step 6: Verify JSON still parses**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "import json; data = json.load(open('playbook-creator-playbook.json')); print(f'version={data[\"version\"]}, phases={len(data[\"checklists\"])}')"
```

Expected: `version=3, phases=15` (phase count changes in later tasks)

---

### Task 7: Playbook JSON — update roles with role_context and agent_assignment

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json:23-83`

- [ ] **Step 1: Replace the entire roles object (lines 23-83)**

Replace with the 6 roles from spec Section 4.4, each gaining `role_context` and `agent_assignment`:

```json
  "roles": {
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
  },
```

- [ ] **Step 2: Run system_prompt tests to verify role_context works end-to-end**

```bash
cd /home/myuser/Documents/playbookdev/scripts
python3 compilation/test_system_prompt.py
```

Expected: All 5 tests pass.

---

### Task 8: Playbook JSON — convert CCCs to structured objects

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json:105-111`

- [ ] **Step 1: Replace the cross_cutting_concerns array (lines 105-111)**

Replace the 5 string entries with 5 structured objects per spec Section 4.5:

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
  ],
```

- [ ] **Step 2: Verify JSON parses and CCC validation passes**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
ccc = data['cross_cutting_concerns']
print(f'CCCs: {len(ccc)} objects')
for c in ccc:
    print(f'  {c[\"id\"]}: {c[\"title\"]} ({len(c[\"phases_applied\"])} phases >= {c[\"minimum_phases\"]} min)')
"
```

---

### Task 9: Playbook JSON — add metric IDs and seed failure modes

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json:1881-1984` (metrics + failure_modes)

- [ ] **Step 1: Replace metrics array with ID'd metrics (lines 1881-1945)**

Replace the 8 metrics with ID'd versions per spec Section 4.6:

```json
  "metrics": [
    {
      "id": "MET-01",
      "title": "Total Phases",
      "description": "Phases in the produced playbook",
      "type": "metric_integer",
      "category": "output_quality",
      "target": null,
      "measurement_method": "Count checklists[] array length"
    },
    {
      "id": "MET-02",
      "title": "Total Tasks",
      "description": "Tasks across all phases in the produced playbook",
      "type": "metric_integer",
      "category": "output_quality",
      "target": null,
      "measurement_method": "Count all items[] across checklists"
    },
    {
      "id": "MET-03",
      "title": "Tasks With Descriptions",
      "description": "Percentage of tasks that have descriptions",
      "type": "metric_integer",
      "category": "output_quality",
      "target": 70,
      "measurement_method": "(tasks with description / total tasks) x 100 — reported as integer percentage"
    },
    {
      "id": "MET-04",
      "title": "Metrics Defined",
      "description": "KPI metrics defined in the produced playbook (never zero)",
      "type": "metric_integer",
      "category": "output_quality",
      "target": 6,
      "measurement_method": "Count metrics[] array length"
    },
    {
      "id": "MET-05",
      "title": "Days to Complete",
      "description": "Calendar days from commission (Phase 0) to documentation (Phase 15)",
      "type": "metric_integer",
      "category": "process",
      "target": 10,
      "measurement_method": "Calendar days between Phase 0 start and Phase 15 gate"
    },
    {
      "id": "MET-06",
      "title": "Audit Issues Found",
      "description": "Total issues found during quality audit phases (lower = better initial drafting)",
      "type": "metric_integer",
      "category": "process",
      "target": null,
      "measurement_method": "Count entries in audits/fix-list.md"
    },
    {
      "id": "MET-07",
      "title": "Critical Issues at Pilot",
      "description": "Issues discovered during pilot/dry-run that should have been caught earlier",
      "type": "metric_integer",
      "category": "process",
      "target": 0,
      "measurement_method": "Count issues in testing/pilot-friction.md and testing/failure-modes-pilot.md rated critical/high"
    },
    {
      "id": "MET-08",
      "title": "Pilot Completion Rate",
      "description": "Percentage of tasks in the pilot/dry-run completed as written (no ad-hoc modifications)",
      "type": "metric_integer",
      "category": "domain_outcome",
      "target": 90,
      "measurement_method": "(tasks completed as-written / total tasks attempted) x 100 — reported as integer percentage"
    }
  ],
```

- [ ] **Step 2: Replace empty failure_modes with 20 seeded entries (line 1984)**

Replace `"failure_modes": [],` with the full 20-entry array from spec Section 4.9. This is large — copy the exact JSON from spec lines 1099-1301 (the `"failure_modes": [...]` array). All entries use em dash (—), not double hyphen (--).

The failure_modes array contains FM-001 through FM-020 with all 8 required fields each: id, symptom, root_cause, fix, prevention, phase, severity, source.

- [ ] **Step 3: Verify JSON parses and FMs validate**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
fms = data['failure_modes']
mets = data['metrics']
print(f'Failure modes: {len(fms)}')
print(f'Metrics: {len(mets)}')
for m in mets:
    print(f'  {m[\"id\"]}: {m[\"title\"]}')
for fm in fms[:3]:
    print(f'  {fm[\"id\"]}: {fm[\"symptom\"][:60]}...')
print(f'  ... and {len(fms)-3} more')
"
```

---

### Task 10: Playbook JSON — modify Phase 0 (complexity classifier + metrics-tracker init)

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json:159-235` (Phase 0 items and gate)

- [ ] **Step 1: Update Phase 0 first task description to include metrics-tracker.md initialization**

In the Phase 0 first task (line 163), change the description to add metrics-tracker initialization. Replace:

```json
          "description": "Folder structure: README.md, research/, architecture/, drafts/, audits/, testing/, final/\n\nInitialize decisions-ledger.md — empty, with header: '# Decisions Ledger — append at every phase gate'\n\nInitialize artifact-manifest.md — empty, with header: '# Artifact Manifest — update at every phase gate' and columns: File | Phase | Status | Summary",
          "output": "README.md, project folder structure, decisions-ledger.md, artifact-manifest.md"
```

With:

```json
          "description": "Folder structure: README.md, research/, architecture/, drafts/, audits/, testing/, final/\n\nInitialize decisions-ledger.md — empty, with header: '# Decisions Ledger — append at every phase gate'\n\nInitialize artifact-manifest.md — empty, with header: '# Artifact Manifest — update at every phase gate' and columns: File | Phase | Status | Summary\n\nInitialize metrics-tracker.md — empty, with header: '# Metrics Tracker — record at every phase gate' and columns: Metric | Phase | Value | Target | Date",
          "output": "README.md, project folder structure, decisions-ledger.md, artifact-manifest.md, metrics-tracker.md"
```

- [ ] **Step 2: Insert complexity classifier task before the Phase 0 gate**

Before the Phase 0 gate task (the item with `gate_conditions`), insert the new task:

```json
        {
          "title": "[Stakeholder] — Classify domain complexity",
          "owner": "[Stakeholder]",
          "description": "Answer three questions to set complexity guardrails for the creation process:\n\n1. PROCESS COMPLEXITY: How many distinct phases does the real-world process have?\n   - Simple (1-4 phases): single-skill workflow, linear steps\n   - Standard (5-10 phases): multi-skill workflow, some parallelism\n   - Complex (11+ phases): multi-discipline workflow, significant dependencies\n\n2. KNOWLEDGE COMPLEXITY: How many distinct types of knowledge does the domain require?\n   - Flat (1 type): single reference layer, no translation needed\n   - Layered (2-3 types): multiple knowledge domains, some cross-referencing\n   - Bridged (4+ types): distinct vocabularies that need translation between them\n\n3. ROLE COMPLEXITY: How many distinct functional roles does the process need?\n   - Minimal (2 roles): one doer, one approver\n   - Standard (3-4 roles): specialized functions with handoffs\n   - Full (5+ roles): distinct disciplines with complex handoff chains\n\nRecord the complexity_profile in decisions-ledger.md:\n  process: simple|standard|complex\n  knowledge: flat|layered|bridged\n  roles: minimal|standard|full\n  overall: highest of the three dimensions\n\nThe overall classification sets advisory guardrails (not hard limits) for the rest of the creation process."
        },
```

- [ ] **Step 3: Add complexity profile gate condition + guardrail_checks to Phase 0 gate**

Add to the Phase 0 gate_conditions array:

```json
            "Complexity profile documented in decisions-ledger.md (process, knowledge, roles, overall)"
```

- [ ] **Step 4: Add failure_modes_relevant to Phase 0 compilation block**

Change Phase 0's `"failure_modes_relevant": []` to:

```json
        "failure_modes_relevant": ["FM-015"],
```

- [ ] **Step 5: Verify Phase 0 parses correctly**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
phase0 = data['checklists'][0]
print(f'Phase 0 items: {len(phase0[\"items\"])}')
for item in phase0['items']:
    print(f'  {item[\"title\"][:70]}')
gate = [i for i in phase0['items'] if 'gate_conditions' in i][0]
print(f'Gate conditions: {len(gate[\"gate_conditions\"])}')
"
```

---

### Task 11: Playbook JSON — redesign Phase 2 handoff + insert Phase 3 (KB Bootstrapping)

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json` — Phase 2 gate handoff + new Phase 3 insertion

This is the largest structural change. Phase 2's handoff must be redesigned to feed Phase 3, then Phase 3 (KB Bootstrapping) is inserted as a new phase after Phase 2.

- [ ] **Step 1: Update Phase 2 gate handoff (next_phase_context and excluded_files)**

Find the Phase 2 gate handoff (around line 484). Replace the `next_phase_context` and `excluded_files`:

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
            ],
            "excluded_files": [
              "scope.md and constraints.md — KB Bootstrapping does not need them; they re-enter context at Phase 4",
              "research/requirements.md — needed at Phase 4, not Phase 3"
            ],
```

- [ ] **Step 2: Add failure_modes_relevant to Phase 2 compilation**

Change Phase 2's `"failure_modes_relevant": []` to:

```json
        "failure_modes_relevant": ["FM-001", "FM-014"],
```

- [ ] **Step 3: Insert Phase 3 (KB Bootstrapping) after Phase 2**

Insert the full Phase 3 JSON object from spec Section 4.3 (lines 219-346) as a new entry in the checklists array, right after Phase 2. Use the exact JSON from the spec — all text uses em dash (—).

The phase has:
- title: "Phase 3: KB Bootstrapping"
- 4 work tasks + 1 gate task
- compilation block with context_load matching Phase 2's new next_phase_context
- Gate with guardrail_checks and kb_status in handoff
- Gate handoff restores slim context for Phase 4

- [ ] **Step 4: Verify insertion — count phases**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
for i, phase in enumerate(data['checklists']):
    print(f'  [{i}] {phase[\"title\"]}')
print(f'Total phases: {len(data[\"checklists\"])}')
"
```

Expected: 16 phases (was 15, added 1). Phase 3 should be "KB Bootstrapping".

---

### Task 12: Playbook JSON — split Phase 8 into Phase 9 (Assembly) + Phase 10 (Validation)

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json` — replace old "Phase 8: JSON Assembly & Validation"

- [ ] **Step 1: Identify the Phase 8 checklist entry (now at index 9 after Phase 3 insertion)**

The old "Phase 8: JSON Assembly & Validation" is now at checklists index 9. Replace it with two new phases per spec Section 4.7.

- [ ] **Step 2: Replace the single phase with Phase 9 (Assembly) + Phase 10 (Validation)**

Remove the old "Phase 8: JSON Assembly & Validation" entry. Insert two new entries in its place:

**Phase 9: JSON Assembly** — from spec lines 688-796. Has:
- 2 work tasks + 1 gate task
- compilation block with 16 context_load files
- Differentiated priorities (not all 5)
- failure_modes_relevant: ["FM-003", "FM-004", "FM-005", "FM-006", "FM-007", "FM-008", "FM-011", "FM-019"]
- Gate with metrics_snapshot: collect ["MET-01", "MET-02"]

**Phase 10: JSON Validation & Consistency** — from spec lines 801-930. Has:
- 8 work tasks + 1 gate task
- Lighter context_load (6 files)
- failure_modes_relevant: ["FM-003", "FM-004", "FM-005", "FM-006", "FM-007", "FM-008", "FM-009", "FM-010", "FM-011"]
- Gate with guardrail_checks and metrics_snapshot: collect ["MET-03"]
- Includes CCC validation task per spec

- [ ] **Step 3: Verify — count phases and new titles**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
for i, phase in enumerate(data['checklists']):
    print(f'  [{i}] {phase[\"title\"]}')
print(f'Total phases: {len(data[\"checklists\"])}')
"
```

Expected: 17 phases. Should see "JSON Assembly" and "JSON Validation" as separate entries.

---

### Task 13: Playbook JSON — restructure Pilot into Structured Dry-Run

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json` — the old "Phase 12: Pilot Test" entry

- [ ] **Step 1: Identify the old Pilot Test phase (now at index 14 after previous insertions)**

After inserting Phase 3 and splitting Phase 8, the old "Phase 12: Pilot Test" should be at index 14.

- [ ] **Step 2: Replace with Structured Dry-Run per spec Section 4.8**

Replace the entire phase entry with the new Phase 14: Pilot / Structured Dry-Run from spec lines 956-1087. Key changes:
- New purpose text about structured dry-run
- 8 work tasks + 1 gate task (was 6 + 1)
- New tasks: scenario matrix, conditional task verification, handoff chain trace, failure mode cataloging
- Gate accepts either structured dry-run (2+ scenarios) OR real pilot
- Gate with metrics_snapshot: collect ["MET-07", "MET-08"]
- All text uses em dash (—)

- [ ] **Step 3: Verify phase structure**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
phase = data['checklists'][14]
print(f'Phase title: {phase[\"title\"]}')
print(f'Items: {len(phase[\"items\"])}')
for item in phase['items']:
    print(f'  {item[\"title\"][:70]}')
"
```

---

### Task 14: Playbook JSON — renumber phases + add per-gate enhancements

**Files:**
- Modify: `/home/myuser/Documents/playbookdev/playbook-creator-playbook.json` — phase titles, phase_kb_mapping, skill_activation, failure_modes_relevant, guardrail_checks, metrics_snapshot, metrics-tracker in context_load

This task renumbers all phase titles to match v3 numbering and adds the remaining per-gate enhancements.

- [ ] **Step 1: Renumber all phase titles to v3 numbering**

The checklists array now has 17 entries. Update each title to match:

| Index | New Title |
|-------|-----------|
| 0 | Phase 0: Commission & Scoping |
| 1 | Phase 1: Domain Research & Process Discovery |
| 2 | Phase 2: Knowledge Base Construction |
| 3 | Phase 3: KB Bootstrapping |
| 4 | Phase 4: Process Architecture |
| 5 | Phase 5: Role Engineering |
| 6 | Phase 6: Task Engineering |
| 7 | Phase 7: Output Configuration |
| 8 | Phase 8: Metrics & KPI Definition |
| 9 | Phase 9: JSON Assembly |
| 10 | Phase 10: JSON Validation & Consistency |
| 11 | Phase 11: Quality Audit — Gap Analysis |
| 12 | Phase 12: Quality Audit — Stress Testing |
| 13 | Phase 13: Stakeholder Review & Iteration |
| 14 | Phase 14: Pilot / Structured Dry-Run |
| 15 | Phase 15: Documentation & Version Control |
| 16 | Phase 16: Continuous Improvement |

- [ ] **Step 2: Update all failure_modes_relevant arrays per spec mapping table**

For each phase, set failure_modes_relevant per spec Section 4.9:

| Phase | failure_modes_relevant |
|-------|----------------------|
| 0 | ["FM-015"] |
| 1 | [] |
| 2 | ["FM-001", "FM-014"] |
| 3 | ["FM-001", "FM-014"] |
| 4 | ["FM-018"] |
| 5 | [] |
| 6 | ["FM-002", "FM-013"] |
| 7 | ["FM-020"] |
| 8 | ["FM-016"] |
| 9 | (already set in Task 12) |
| 10 | (already set in Task 12) |
| 11 | ["FM-002"] |
| 12 | ["FM-009", "FM-010", "FM-012"] |
| 13 | [] |
| 14 | (already set in Task 13) |
| 15 | [] |
| 16 | ["FM-017"] |

- [ ] **Step 3: Add guardrail_checks to gates at Phases 2, 4, 5, 6, 8**

Per spec Section 4.1, add the guardrail_checks array to these gates. Phase 3 and Phase 10 already have them from Tasks 11 and 12.

Phase 2 gate:
```json
      "guardrail_checks": [
        "KB complexity level matches complexity_profile.knowledge dimension from Phase 0 — if flat domain has bridged KB design, or bridged domain has flat KB, confirm with [Stakeholder] before proceeding"
      ],
```

Phase 4 gate:
```json
      "guardrail_checks": [
        "Phase count matches complexity_profile.process dimension from Phase 0 — simple: 5-8 phases, standard: 8-13, complex: 12-18 — if outside range, confirm with [Stakeholder] before proceeding"
      ],
```

Phase 5 gate:
```json
      "guardrail_checks": [
        "Role count matches complexity_profile.roles dimension from Phase 0 — minimal: 2-3 roles, standard: 3-5, full: 4-8 — if outside range, confirm with [Stakeholder] before proceeding"
      ],
```

Phase 6 gate:
```json
      "guardrail_checks": [
        "Task count matches complexity_profile.process dimension from Phase 0 — simple: 30-60 tasks, standard: 60-150, complex: 120-300 — if outside range, confirm with [Stakeholder] before proceeding"
      ],
```

Phase 8 gate:
```json
      "guardrail_checks": [
        "Metrics count matches complexity_profile from Phase 0 — simple: 3-5 metrics, standard: 5-10, complex: 8-20 — if outside range, confirm with [Stakeholder] before proceeding"
      ],
```

- [ ] **Step 4: Add metrics_snapshot to gates at Phases 8, 11, 12, 15**

Phase 9, 10, and 14 already have metrics_snapshot from Tasks 12 and 13.

Phase 8 gate handoff — add:
```json
        "metrics_snapshot": {
          "collect": ["MET-04"],
          "record_in": "metrics-tracker.md"
        },
```

Phase 11 gate handoff — add:
```json
        "metrics_snapshot": {
          "collect": ["MET-06"],
          "record_in": "metrics-tracker.md"
        },
```

Phase 12 gate handoff — add:
```json
        "metrics_snapshot": {
          "collect": ["MET-06"],
          "record_in": "metrics-tracker.md"
        },
```

Phase 15 gate handoff — add:
```json
        "metrics_snapshot": {
          "collect": ["MET-05"],
          "record_in": "metrics-tracker.md"
        },
```

- [ ] **Step 5: Add metrics-tracker.md to context_load of phases with metrics_snapshot**

Add `"metrics-tracker.md"` to the context_load arrays of Phases 8, 9, 10, 11, 12, 14, 15 (with priority 1 in context_budget).

Phase 9 and 10 already have it from Task 12. Phase 14 already has it from Task 13.

For Phases 8, 11, 12, 15: add `"metrics-tracker.md"` to context_load and add `"metrics-tracker.md": 1` to context_budget.priority.

- [ ] **Step 6: Add metrics report task to Phase 15 (Documentation)**

Insert before the Phase 15 gate task:

```json
        {
          "title": "[Coordinator] — Compile final metrics report",
          "owner": "[Coordinator]",
          "description": "Read metrics-tracker.md. For each metric: compare final value against target from the metrics[] array. Produce a summary table:\n\n| Metric | Target | Actual | Status |\n\nStatus: PASS (met target), MISS (below target), N/A (no target defined).\n\nInclude brief analysis: which metrics indicate process health, which indicate output quality, what to improve in the next run.",
          "output": "final/metrics-report.md"
        },
```

- [ ] **Step 7: Update phase_kb_mapping to 17 phases**

Replace the phase_kb_mapping object:

```json
  "phase_kb_mapping": {
    "phase_0": [],
    "phase_1": [],
    "phase_2": [],
    "phase_3": [],
    "phase_4": [],
    "phase_5": [],
    "phase_6": [],
    "phase_7": [],
    "phase_8": [],
    "phase_9": [],
    "phase_10": [],
    "phase_11": [],
    "phase_12": [],
    "phase_13": [],
    "phase_14": [],
    "phase_15": [],
    "phase_16": []
  },
```

- [ ] **Step 8: Update skill_activation to 17 phases**

Replace the skill_activation object:

```json
  "skill_activation": {
    "phase_0": "none",
    "phase_1": "none",
    "phase_2": "none",
    "phase_3": "none",
    "phase_4": "none",
    "phase_5": "none",
    "phase_6": "none",
    "phase_7": "none",
    "phase_8": "none",
    "phase_9": "none",
    "phase_10": "none",
    "phase_11": "none",
    "phase_12": "none",
    "phase_13": "none",
    "phase_14": "none",
    "phase_15": "none",
    "phase_16": "none"
  },
```

- [ ] **Step 9: Verify phase count matches summary views**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)
phases = len(data['checklists'])
kb_map = len(data['phase_kb_mapping'])
skill = len(data['skill_activation'])
print(f'Phases: {phases}, KB mapping: {kb_map}, Skill activation: {skill}')
assert phases == kb_map == skill == 17, f'Mismatch: {phases} != {kb_map} != {skill}'
print('PASS: all counts match at 17')
"
```

---

### Task 15: Run full validation and fix any issues

**Files:**
- All modified files

- [ ] **Step 1: Run validator on v3 playbook**

```bash
cd /home/myuser/Documents/playbookdev
python3 scripts/validate_playbook.py playbook-creator-playbook.json
```

Expected: `PASS` (possibly with warnings). If errors, fix them before proceeding.

- [ ] **Step 2: Run system_prompt tests**

```bash
cd /home/myuser/Documents/playbookdev/scripts
python3 compilation/test_system_prompt.py
```

Expected: All 5 tests pass.

- [ ] **Step 3: Verify output-schema.json is valid JSON**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "import json; json.load(open('templates/output-schema.json')); print('PASS')"
```

- [ ] **Step 4: Verify v3 playbook against spec verification checklist**

Run a comprehensive check:

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    data = json.load(f)

checks = []

# Version
checks.append(('version == 3', data['version'] == 3))

# Phase count
checks.append(('17 phases', len(data['checklists']) == 17))

# All phases have compilation blocks
for i, p in enumerate(data['checklists']):
    checks.append((f'Phase {i} has compilation', 'compilation' in p))

# 20 failure modes
checks.append(('20 failure modes', len(data['failure_modes']) == 20))

# All FMs have 8 required fields
for fm in data['failure_modes']:
    for f in ('id', 'symptom', 'root_cause', 'fix', 'prevention', 'phase', 'severity', 'source'):
        if f not in fm:
            checks.append((f'FM {fm.get(\"id\", \"?\")} has {f}', False))

# 5 CCC objects
ccc = data['cross_cutting_concerns']
checks.append(('5 CCCs', len(ccc) == 5))
for c in ccc:
    checks.append((f'{c[\"id\"]} phases >= min', len(c['phases_applied']) >= c['minimum_phases']))

# 8 metrics with IDs
metrics = data['metrics']
checks.append(('8 metrics', len(metrics) == 8))
for m in metrics:
    checks.append((f'{m[\"id\"]} exists', 'id' in m))

# Roles have role_context and agent_assignment
for role_name, role_def in data['roles'].items():
    checks.append((f'{role_name} has role_context', 'role_context' in role_def))
    checks.append((f'{role_name} has agent_assignment', 'agent_assignment' in role_def))

# context_preservation has metrics_tracker
checks.append(('metrics_tracker in context_preservation', 'metrics_tracker' in data['context_preservation']))

# Summary views match
checks.append(('phase_kb_mapping has 17', len(data['phase_kb_mapping']) == 17))
checks.append(('skill_activation has 17', len(data['skill_activation']) == 17))

# Print results
passed = sum(1 for _, v in checks if v)
failed = [(n, v) for n, v in checks if not v]
print(f'{passed}/{len(checks)} checks passed')
if failed:
    print('FAILURES:')
    for name, _ in failed:
        print(f'  FAIL: {name}')
else:
    print('ALL CHECKS PASSED')
"
```

- [ ] **Step 5: Fix any validation errors found in steps 1-4**

If any errors were found, fix them and re-run validation until all pass.

- [ ] **Step 6: Verify no double hyphens in playbook JSON string values**

```bash
cd /home/myuser/Documents/playbookdev
python3 -c "
import json
with open('playbook-creator-playbook.json') as f:
    content = f.read()
    data = json.loads(content)

def find_double_hyphens(obj, path=''):
    issues = []
    if isinstance(obj, str):
        if ' -- ' in obj:
            issues.append(f'{path}: contains \" -- \"')
    elif isinstance(obj, dict):
        for k, v in obj.items():
            issues.extend(find_double_hyphens(v, f'{path}.{k}'))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            issues.extend(find_double_hyphens(v, f'{path}[{i}]'))
    return issues

issues = find_double_hyphens(data)
if issues:
    print(f'FAIL: {len(issues)} double-hyphen instances found:')
    for i in issues[:10]:
        print(f'  {i}')
else:
    print('PASS: No double hyphens in string values')
"
```

Expected: `PASS: No double hyphens in string values`
