#!/usr/bin/env python3
"""Generate a scaffold JSON for a new playbook.

Reads templates/output-schema.json and produces a valid skeleton with all
required fields, placeholder content, and correct ID formats. This prevents
Phase 9 (JSON Assembly) from being a wall — users start with a valid
structure and fill in content.

Usage:
    python3 scripts/generate_scaffold.py my-playbook.json
    python3 scripts/generate_scaffold.py my-playbook.json --title "My Playbook" --phases 8 --roles 3
    python3 scripts/generate_scaffold.py --help
"""

import argparse
import json
import sys
from pathlib import Path


def generate_scaffold(
    title: str = "My Playbook",
    num_phases: int = 5,
    num_roles: int = 3,
    workflow_model: str = "role-based-single-agent",
) -> dict:
    """Generate a scaffold playbook with all required fields."""

    # Default role names based on count
    default_role_names = [
        "Coordinator", "Builder", "Auditor",
        "Researcher", "Architect", "Stakeholder",
    ]
    role_names = default_role_names[:num_roles]

    # Build roles
    roles = {}
    for name in role_names:
        roles[name] = {
            "description": f"TODO: Describe the {name} role",
            "role_context": f"TODO: Baseline activation context for {name}",
            "defaults": {
                "model": "sonnet",
                "temperature": [0.3, 0.5],
            },
            "agent_assignment": "single",
        }

    # Build phases
    checklists = []
    for i in range(num_phases):
        role = role_names[i % len(role_names)]
        coordinator = role_names[0]  # First role is coordinator

        phase = {
            "title": f"Phase {i}: TODO Phase Name",
            "purpose": "TODO: Describe the purpose of this phase",
            "compilation": {
                "context_load": (
                    ["TODO: list files to load"]
                    if i == 0
                    else [
                        "decisions-ledger.md",
                        "artifact-manifest.md",
                        "TODO: add handoff files from previous phase",
                    ]
                ),
                "role_mindset": f"{role} — TODO: describe focus for this phase",
                "objective": "TODO: What this phase must accomplish",
                "pre_check": ["TODO: conditions that must be true before starting"],
                "failure_modes_relevant": [],
                "agent_config": {},
                "system_prompt_auto": {
                    "role_definition": True,
                    "phase_objective": True,
                    "failure_modes": True,
                    "pre_check_guidance": True,
                    "context_files": True,
                    "handoff_requirements": True,
                },
                "context_budget": {
                    "max_tokens": 64000,
                    "priority": {},
                },
                "skill_preparation": "none",
            },
            "items": [
                {
                    "title": f"[{role}] — TODO: First task of phase {i}",
                    "owner": f"[{role}]",
                    "description": "TODO: What to do",
                    "output": "TODO: output-file.md",
                },
                {
                    "title": f"[{coordinator}] — Phase gate: TODO gate description",
                    "owner": f"[{coordinator}]",
                    "gate_conditions": [
                        "TODO: measurable condition 1",
                        "TODO: measurable condition 2",
                    ],
                    "blocker_examples": [
                        "TODO: example of what failure looks like",
                    ],
                    "handoff": {
                        "output_artifacts": ["TODO: list output files"],
                        "next_phase_context": ["TODO: files needed by next phase"],
                        "excluded_files": [],
                        "context_update": {
                            "decisions-ledger.md": "append",
                            "artifact-manifest.md": "update",
                        },
                    },
                },
            ],
        }
        checklists.append(phase)

    # Build failure modes (minimum viable set)
    failure_modes = [
        {
            "id": "FM-001",
            "symptom": "TODO: What goes wrong",
            "root_cause": "TODO: Why it goes wrong",
            "fix": "TODO: How to fix it",
            "prevention": "TODO: How to prevent it",
            "phase": f"Phase 0: TODO Phase Name",
            "severity": "error",
            "source": "scaffold",
        },
    ]

    # Build metrics (one per required category)
    metrics = [
        {
            "id": "MET-01",
            "title": "TODO: Process Metric",
            "description": "TODO: Describe what this measures",
            "type": "metric_integer",
            "category": "process",
            "target": None,
            "measurement_method": "TODO: How to measure",
        },
        {
            "id": "MET-02",
            "title": "TODO: Quality Metric",
            "description": "TODO: Describe what this measures",
            "type": "metric_integer",
            "category": "output_quality",
            "target": None,
            "measurement_method": "TODO: How to measure",
        },
        {
            "id": "MET-03",
            "title": "TODO: Outcome Metric",
            "description": "TODO: Describe what this measures",
            "type": "metric_integer",
            "category": "domain_outcome",
            "target": None,
            "measurement_method": "TODO: How to measure",
        },
    ]

    # Build phase_kb_mapping and skill_activation
    phase_kb_mapping = {}
    skill_activation = {}
    for i in range(num_phases):
        phase_kb_mapping[f"Phase {i}"] = []
        skill_activation[f"Phase {i}"] = "none"

    playbook = {
        "title": title,
        "version": 1,
        "description": "TODO: 1-3 sentence overview of this playbook",
        "workflow_model": workflow_model,
        "defaults": {
            "model": "opus",
            "model_fallbacks": {
                "opus": ["sonnet", "haiku"],
                "sonnet": ["haiku"],
            },
            "context_budget_tokens": 64000,
            "system_prompt_budget": 2000,
            "critical_priority_threshold": 3,
            "temperature": 0.3,
            "max_tokens": 4096,
        },
        "roles": roles,
        "scope": {
            "in_scope": ["TODO: What this playbook covers"],
            "out_of_scope": ["TODO: What this playbook does NOT cover"],
            "adjacent": ["TODO: What it connects to but doesn't own"],
        },
        "cross_cutting_concerns": [
            {
                "id": "CCC-01",
                "title": "TODO: Quality Standard",
                "description": "TODO: Describe the standard",
                "enforcement_method": "checklist_items",
                "enforcement_rule": "TODO: How to enforce",
                "minimum_phases": 3,
                "phases_applied": list(range(min(3, num_phases))),
            },
        ],
        "knowledge_base": {
            "complexity": "flat",
            "layers": [],
            "entry_schema": {},
            "bridge_schema": {},
            "population_strategy": {
                "placeholder_seeding": "TODO",
                "harvesting_sources": [],
                "curation_rules": "TODO",
                "sync_rules": "TODO",
                "versioning_protocol": "TODO",
            },
            "directory_structure": "TODO: Describe folder structure",
        },
        "checklists": checklists,
        "metrics": metrics,
        "usage_instructions": {
            "how_to_run": [
                "Load this playbook as context for a planning session",
                "Work through phases sequentially",
            ],
            "session_strategy": [
                "TODO: Define session groupings",
            ],
            "cost_optimization": [
                "Use compilation blocks — only load what the phase needs",
            ],
            "post_run_review": {
                "assess": [
                    "What went well",
                    "What didn't go well",
                    "What should change",
                ],
            },
        },
        "failure_modes": failure_modes,
        "phase_kb_mapping": phase_kb_mapping,
        "skill_activation": skill_activation,
        "router": {
            "description": "TODO: How to route decisions",
            "decision_tree": ["TODO: Decision rules"],
            "default": "TODO: Default action",
        },
        "context_preservation": {
            "decisions_ledger": "decisions-ledger.md",
            "artifact_manifest": "artifact-manifest.md",
            "metrics_tracker": "metrics-tracker.md",
            "rules": [
                "Update decisions-ledger.md at every phase gate",
                "Update artifact-manifest.md at every phase gate",
            ],
        },
    }

    return playbook


def main():
    parser = argparse.ArgumentParser(
        description="Generate a scaffold playbook JSON with all required fields.",
        epilog="Examples:\n"
               '  python3 scripts/generate_scaffold.py my-playbook.json\n'
               '  python3 scripts/generate_scaffold.py my-playbook.json --title "Deploy Pipeline" --phases 8\n'
               '  python3 scripts/generate_scaffold.py my-playbook.json --phases 5 --roles 3\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "output",
        help="Output file path for the scaffold JSON",
    )
    parser.add_argument(
        "--title",
        default="My Playbook",
        help='Playbook title (default: "My Playbook")',
    )
    parser.add_argument(
        "--phases",
        type=int,
        default=5,
        help="Number of phases to generate (default: 5)",
    )
    parser.add_argument(
        "--roles",
        type=int,
        default=3,
        help="Number of roles to generate (default: 3, max: 6)",
    )
    parser.add_argument(
        "--workflow",
        default="role-based-single-agent",
        choices=["human-in-the-loop", "fully-autonomous", "human-directed",
                 "role-based-single-agent", "role-based-multi-agent"],
        help="Workflow model (default: role-based-single-agent)",
    )
    args = parser.parse_args()

    if args.roles < 1 or args.roles > 6:
        print("Error: --roles must be between 1 and 6")
        sys.exit(1)
    if args.phases < 1:
        print("Error: --phases must be at least 1")
        sys.exit(1)

    output_path = Path(args.output)
    if output_path.exists():
        print(f"File already exists: {args.output}")
        print("Remove it first or choose a different name.")
        sys.exit(1)

    playbook = generate_scaffold(
        title=args.title,
        num_phases=args.phases,
        num_roles=min(args.roles, 6),
        workflow_model=args.workflow,
    )

    output_path.write_text(json.dumps(playbook, indent=2) + "\n")
    print(f"Scaffold written to {args.output}")
    print(f"  {args.phases} phases, {min(args.roles, 6)} roles")
    print(f"  Search for 'TODO' to find all placeholders that need filling in")
    print(f"  Validate with: python3 scripts/validate_playbook.py {args.output}")


if __name__ == "__main__":
    main()
