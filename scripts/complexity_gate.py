#!/usr/bin/env python3
"""Complexity gate verification for playbooks.

Usage:
    # Classify complexity (Phase 0)
    python3 scripts/complexity_gate.py classify playbook.json

    # Verify complexity match (Final phase)
    python3 scripts/complexity_gate.py verify playbook.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple, List

import tracing  # noqa: F401 — initialise Langfuse before decorators fire
from tracing import RunTrace
from langfuse import observe, get_client

RunTrace.attach("/home/myuser/.openclaw/workspace-pb-coordinator")

# Import from compilation module (add scripts to path)
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))

from compilation.constants import COMPLEXITY_LIMITS, COMPLEXITY_VARIANCE_THRESHOLD


def calculate_complexity_score(
    phases: int,
    roles: int,
    cccs: int,
    integrations: int = 0
) -> int:
    """
    Calculate complexity score (0-12).

    Args:
        phases: Number of phases
        roles: Number of roles
        cccs: Number of cross-cutting concerns
        integrations: Number of external integrations (0-2)

    Returns:
        Complexity score
    """
    phases_score = min(phases // 4, 4)
    roles_score = min(roles - 1, 3)
    cccs_score = min(cccs // 3, 3)
    integrations_score = min(integrations, 2)
    return phases_score + roles_score + cccs_score + integrations_score


def classify_from_score(score: int) -> str:
    """Convert score to classification."""
    if score <= 2:
        return "simple"
    elif score <= 5:
        return "moderate"
    elif score <= 8:
        return "complex"
    else:
        return "structured"


def classify_complexity(playbook: dict) -> dict:
    """
    Classify playbook complexity based on scoring.

    Returns dict with classification, score, and details.
    """
    phases = len(playbook.get("checklists", []))
    roles = len(playbook.get("roles", {}))
    cccs = len(playbook.get("cross_cutting_concerns", []))

    # Estimate integrations from context or defaults to 0
    integrations = 0  # Could be inferred from domain analysis

    score = calculate_complexity_score(phases, roles, cccs, integrations)
    classification = classify_from_score(score)
    limits = COMPLEXITY_LIMITS[classification]

    return {
        "classification": classification,
        "complexity_score": score,
        "actual_phases": phases,
        "actual_roles": roles,
        "actual_cccs": cccs,
        "limits": limits
    }


def verify_complexity_match(playbook: dict) -> Tuple[bool, List[str]]:
    """
    Verify produced playbook matches Phase 0 complexity profile.

    Returns:
        Tuple of (passed, list of issues)
    """
    profile = playbook.get("complexity_profile", {})

    if not profile:
        return False, ["No complexity_profile found - Phase 0 incomplete"]

    classification = profile.get("classification")
    if classification not in COMPLEXITY_LIMITS:
        return False, [f"Unknown classification: {classification}"]

    limits = COMPLEXITY_LIMITS[classification]

    actual_phases = len(playbook.get("checklists", []))
    actual_roles = len(playbook.get("roles", {}))
    actual_cccs = len(playbook.get("cross_cutting_concerns", []))

    expected_phases = profile.get("expected_phases", limits["phases"])
    expected_roles = profile.get("expected_roles", limits["roles"])
    expected_cccs = profile.get("expected_ccc_count", limits["cccs"])

    issues = []

    # Check variance (allow threshold % over)
    if actual_phases > expected_phases * (1 + COMPLEXITY_VARIANCE_THRESHOLD):
        variance_pct = int((actual_phases - expected_phases) / expected_phases * 100)
        issues.append(
            f"Phases ({actual_phases}) exceed expected ({expected_phases}) by {variance_pct}%"
        )

    if actual_roles > expected_roles * (1 + COMPLEXITY_VARIANCE_THRESHOLD):
        variance_pct = int((actual_roles - expected_roles) / expected_roles * 100)
        issues.append(
            f"Roles ({actual_roles}) exceed expected ({expected_roles}) by {variance_pct}%"
        )

    if actual_cccs > expected_cccs * (1 + COMPLEXITY_VARIANCE_THRESHOLD):
        variance_pct = int((actual_cccs - expected_cccs) / expected_cccs * 100)
        issues.append(
            f"CCCs ({actual_cccs}) exceed expected ({expected_cccs}) by {variance_pct}%"
        )

    # Check against classification limits (hard limit)
    if actual_phases > limits["phases"]:
        issues.append(
            f"Phases ({actual_phases}) exceed '{classification}' limit ({limits['phases']})"
        )

    return len(issues) == 0, issues


@observe(name="complexity-classify", capture_input=False, capture_output=False)
def _run_classify(playbook_path: str) -> dict:
    _lf = get_client()
    _lf.update_current_span(input={"playbook": playbook_path})
    playbook = json.loads(Path(playbook_path).read_text())
    result = classify_complexity(playbook)
    _lf.update_current_span(output=result)
    return result


@observe(name="complexity-verify", capture_input=False, capture_output=False)
def _run_verify(playbook_path: str) -> tuple[bool, list]:
    _lf = get_client()
    _lf.update_current_span(input={"playbook": playbook_path})
    playbook = json.loads(Path(playbook_path).read_text())
    passed, issues = verify_complexity_match(playbook)
    _lf.update_current_span(output={"passed": passed, "issue_count": len(issues)})
    return passed, issues


def main():
    parser = argparse.ArgumentParser(description="Complexity gate verification")
    parser.add_argument("command", choices=["classify", "verify"], help="Operation")
    parser.add_argument("playbook", type=Path, help="Playbook JSON file")

    args = parser.parse_args()

    trace_id = RunTrace.current_trace_id()

    if args.command == "classify":
        result = _run_classify(str(args.playbook), langfuse_trace_id=trace_id)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    elif args.command == "verify":
        passed, issues = _run_verify(str(args.playbook), langfuse_trace_id=trace_id)
        if passed:
            print("PASS: Complexity matches profile")
            sys.exit(0)
        else:
            print("FAIL: Complexity mismatch")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)


if __name__ == "__main__":
    main()