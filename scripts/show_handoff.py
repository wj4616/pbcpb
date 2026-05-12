#!/usr/bin/env python3
"""Show handoff information for a specific phase.

Prints exactly what files to load when starting the next AI session after
completing a given phase. Eliminates the manual handoff problem.

Usage:
    python3 scripts/show_handoff.py --phase 3
    python3 scripts/show_handoff.py --phase 3 --playbook my-playbook.json
    python3 scripts/show_handoff.py --all
    python3 scripts/show_handoff.py --help
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import tracing  # noqa: F401 — initialise Langfuse before decorators fire
from tracing import RunTrace
from langfuse import observe, get_client

RunTrace.attach("/home/myuser/.openclaw/workspace-pb-coordinator")


def get_phase_handoff(playbook: dict, phase_num: int) -> dict | None:
    """Extract handoff info from a phase's gate item."""
    checklists = playbook.get("checklists", [])
    if phase_num < 0 or phase_num >= len(checklists):
        return None

    phase = checklists[phase_num]
    for item in phase.get("items", []):
        if "gate_conditions" in item and "handoff" in item:
            return item["handoff"]
    return None


def get_next_phase_info(playbook: dict, phase_num: int) -> dict | None:
    """Get compilation info for the phase AFTER the given one."""
    checklists = playbook.get("checklists", [])
    next_num = phase_num + 1
    if next_num >= len(checklists):
        return None
    return checklists[next_num]


def print_handoff(playbook: dict, phase_num: int):
    """Print handoff details for a phase."""
    checklists = playbook.get("checklists", [])
    if phase_num < 0 or phase_num >= len(checklists):
        print(f"Error: Phase {phase_num} does not exist (valid: 0-{len(checklists) - 1})")
        sys.exit(1)

    phase = checklists[phase_num]
    phase_title = phase.get("title", f"Phase {phase_num}")
    handoff = get_phase_handoff(playbook, phase_num)

    print(f"=== Handoff from {phase_title} ===\n")

    if not handoff:
        print("  No gate/handoff found for this phase.")
        return

    # Output artifacts (what this phase produced)
    artifacts = handoff.get("output_artifacts", [])
    if artifacts:
        print("Files produced by this phase:")
        for a in artifacts:
            print(f"  - {a}")
        print()

    # What to load next
    next_ctx = handoff.get("next_phase_context", [])
    if next_ctx:
        print("Files to load in next session:")
        print("  (Always load these first:)")
        print("  - playbook-creator-playbook.json")
        print("  - decisions-ledger.md")
        print("  - artifact-manifest.md")
        print("  - metrics-tracker.md")
        print()
        print("  (Then load these handoff files:)")
        for f in next_ctx:
            print(f"  - {f}")
        print()

    # What to exclude
    excluded = handoff.get("excluded_files", [])
    if excluded:
        print("Files to NOT load (resolved/superseded):")
        for f in excluded:
            print(f"  - {f}")
        print()

    # Next phase info
    next_phase = get_next_phase_info(playbook, phase_num)
    if next_phase:
        next_title = next_phase.get("title", "?")
        comp = next_phase.get("compilation", {})
        role = comp.get("role_mindset", "?")
        objective = comp.get("objective", "?")
        print(f"Next phase: {next_title}")
        print(f"  Role mindset: {role}")
        print(f"  Objective: {objective}")
        print()
        print("Suggested session opener:")
        print(f'  "We\'re starting {next_title}. I\'ve loaded the tracking files')
        print(f'   and handoff artifacts from Phase {phase_num}."')
    else:
        print("This is the final phase. No next session needed.")


def print_all_handoffs(playbook: dict):
    """Print a summary of all phase handoffs."""
    checklists = playbook.get("checklists", [])
    print(f"=== All Phase Handoffs ({len(checklists)} phases) ===\n")

    for i, phase in enumerate(checklists):
        title = phase.get("title", f"Phase {i}")
        handoff = get_phase_handoff(playbook, i)

        if handoff:
            artifacts = handoff.get("output_artifacts", [])
            next_ctx = handoff.get("next_phase_context", [])
            print(f"Phase {i}: {title}")
            print(f"  Produces: {len(artifacts)} file(s)")
            print(f"  Passes forward: {len(next_ctx)} file(s)")
        else:
            print(f"Phase {i}: {title}")
            print(f"  (no gate/handoff)")
        print()


@observe(name="show-handoff", capture_input=False, capture_output=False)
def _run_show_handoff(playbook_path: str, phase: int | None, show_all: bool) -> None:
    _lf = get_client()
    _lf.update_current_span(input={"playbook": playbook_path, "phase": phase, "all": show_all})
    playbook = json.loads(Path(playbook_path).read_text())
    if show_all:
        print_all_handoffs(playbook)
    else:
        print_handoff(playbook, phase)
    _lf.update_current_span(output={"done": True})


def main():
    parser = argparse.ArgumentParser(
        description="Show handoff information for playbook phases.",
        epilog="Examples:\n"
               "  python3 scripts/show_handoff.py --phase 3\n"
               "  python3 scripts/show_handoff.py --phase 0 --playbook my-playbook.json\n"
               "  python3 scripts/show_handoff.py --all\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        type=int,
        default=None,
        help="Phase number to show handoff for (e.g., --phase 3)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show summary of all phase handoffs",
    )
    parser.add_argument(
        "--playbook",
        default="playbook-creator-playbook.json",
        help="Path to playbook JSON (default: playbook-creator-playbook.json)",
    )
    args = parser.parse_args()

    if args.phase is None and not args.all:
        parser.print_help()
        print("\nError: Specify --phase N or --all")
        sys.exit(1)

    path = Path(args.playbook)
    if not path.exists():
        print(f"File not found: {args.playbook}")
        sys.exit(1)

    _run_show_handoff(str(path), args.phase, args.all, langfuse_trace_id=RunTrace.current_trace_id())


if __name__ == "__main__":
    main()
