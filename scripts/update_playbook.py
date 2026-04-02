#!/usr/bin/env python3
"""Update playbook-creator-playbook.json with new compilation block fields.

This script adds:
- agent_config to compilation blocks
- system_prompt_auto flags
- context_budget with priority mappings
- Updates handoff fields (excluded_files, skill_validation)
"""

import json
import re
from pathlib import Path

# Priority mappings for common context files
# Priority 1-3 = critical (cannot be skipped)
# Priority 4-6 = important (skip only if necessary)
# Priority 7-10 = optional (can skip for budget)

PRIORITY_MAPPINGS = {
    # Phase-specific mappings - these are examples, should be customized per phase
    "Phase 0": {
        "commission brief": 1,
        "README.md": 5
    },
    "Phase 1": {
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2,
        "scope.md": 2,
        "constraints.md": 3,
        "success-criteria.md": 4,
        "research/": 6
    },
    "Phase 2": {
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2,
        "kb-spec.md": 3
    },
    "default": {
        "decisions-ledger.md": 1,
        "artifact-manifest.md": 2
    }
}


def get_priority(filename: str, phase_title: str) -> int:
    """Get priority for a file based on phase context."""
    phase_name = phase_title.split(":")[0] if ":" in phase_title else phase_title
    phase_mapping = PRIORITY_MAPPINGS.get(phase_name, PRIORITY_MAPPINGS["default"])

    # Check phase-specific mapping first
    for pattern, priority in phase_mapping.items():
        if pattern in filename:
            return priority

    # Default priority for unspecified files
    return 5


def update_compilation_block(comp: dict, phase_title: str, phase_num: int) -> dict:
    """Add new fields to compilation block."""
    # Add agent_config (empty by default - phases can override)
    if "agent_config" not in comp:
        # Research phases get higher temperature
        if phase_num in [1, 2]:  # Research phases
            comp["agent_config"] = {
                "temperature": 0.5
            }
        elif phase_num in [9, 10]:  # Audit phases
            comp["agent_config"] = {
                "temperature": 0.25
            }
        else:
            comp["agent_config"] = {}

    # Add system_prompt_auto flags (all true by default)
    if "system_prompt_auto" not in comp:
        comp["system_prompt_auto"] = {
            "role_definition": True,
            "phase_objective": True,
            "failure_modes": True,
            "pre_check_guidance": True,
            "context_files": True,
            "handoff_requirements": True
        }

    # Add context_budget with priority mapping
    if "context_budget" not in comp:
        context_load = comp.get("context_load", [])
        priority_map = {}
        for item in context_load:
            # Normalize filename for priority mapping
            base = re.split(r"\s*\(", item)[0].strip()
            priority_map[base] = get_priority(base, phase_title)

        # Only set priority for files that exist in context_load
        comp["context_budget"] = {
            "max_tokens": 64000,
            "priority": priority_map
        }
    else:
        # Ensure priority only references files in context_load
        existing_priority = comp["context_budget"].get("priority", {})
        context_load = comp.get("context_load", [])
        valid_files = {re.split(r"\s*\(", item)[0].strip() for item in context_load}
        comp["context_budget"]["priority"] = {
            k: v for k, v in existing_priority.items() if k in valid_files
        }

    # Add skill_preparation if not present
    if "skill_preparation" not in comp:
        comp["skill_preparation"] = "none"

    return comp


def update_handoff_block(handoff: dict) -> dict:
    """Update handoff block with new fields."""
    # Rename excluded_context to excluded_files
    if "excluded_context" in handoff:
        handoff["excluded_files"] = handoff.pop("excluded_context")

    # Rename skill to skill_validation
    if "skill" in handoff:
        handoff["skill_validation"] = handoff.pop("skill")

    return handoff


def main():
    playbook_path = Path("playbook-creator-playbook.json")

    with open(playbook_path) as f:
        playbook = json.load(f)

    # Update checklists
    checklists = playbook.get("checklists", [])
    for i, phase in enumerate(checklists):
        phase_title = phase.get("title", f"Phase {i}")
        print(f"Processing {phase_title}...")

        # Update compilation block
        if "compilation" in phase:
            phase["compilation"] = update_compilation_block(
                phase["compilation"], phase_title, i
            )

        # Update handoff blocks in items
        for item in phase.get("items", []):
            if "handoff" in item:
                item["handoff"] = update_handoff_block(item["handoff"])

    # Write back
    with open(playbook_path, "w") as f:
        json.dump(playbook, f, indent=2)

    print("Playbook updated successfully!")


if __name__ == "__main__":
    main()