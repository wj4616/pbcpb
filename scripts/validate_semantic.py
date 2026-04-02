#!/usr/bin/env python3
"""Semantic validation for playbook logical consistency."""

import json
import sys
from pathlib import Path
from typing import Tuple, List


def extract_role_name(role_mindset: str) -> str:
    """
    Extract role name from role_mindset string.

    Handles both em-dash (—) and regular dash (-) separators.
    """
    # Try em-dash first
    if " — " in role_mindset:
        return role_mindset.split(" — ")[0].strip()
    # Try regular dash
    if " - " in role_mindset:
        return role_mindset.split(" - ")[0].strip()
    # No separator, return as-is
    return role_mindset.strip()


def validate_semantic(playbook: dict) -> Tuple[List[str], List[str]]:
    """
    Validate semantic consistency of playbook.

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # 1. Role mindset references existing role
    roles = playbook.get("roles", {})
    defined_roles = set(roles.keys())

    for i, phase in enumerate(playbook.get("checklists", [])):
        comp = phase.get("compilation", {})
        role_mindset = comp.get("role_mindset", "")
        phase_title = phase.get("title", f"Phase {i}")

        if not role_mindset:
            continue

        role_name = extract_role_name(role_mindset)

        if role_name and role_name not in defined_roles:
            errors.append(
                f"{phase_title}: role_mindset '{role_mindset}' references undefined role '{role_name}'"
            )

    # 2. Failure mode phase references exist
    failure_modes = playbook.get("failure_modes", [])
    phase_titles = set(p.get("title", "") for p in playbook.get("checklists", []))

    for fm in failure_modes:
        fm_id = fm.get("id", "Unknown")
        fm_phase = fm.get("phase", "")

        if fm_phase and fm_phase not in phase_titles:
            errors.append(
                f"Failure mode {fm_id}: references non-existent phase '{fm_phase}'"
            )

    # 3. Phase ordering follows convention
    for i, phase in enumerate(playbook.get("checklists", [])):
        title = phase.get("title", "")
        expected_prefix = f"Phase {i}"

        if not title.startswith(expected_prefix):
            warnings.append(
                f"Phase {i} title '{title}' doesn't follow 'Phase N: Name' pattern"
            )

    # 4. Complexity profile validation (if present)
    profile = playbook.get("complexity_profile", {})
    if profile:
        classification = profile.get("classification")
        valid_classifications = {"simple", "moderate", "complex", "structured"}
        if classification and classification not in valid_classifications:
            errors.append(
                f"complexity_profile.classification '{classification}' not in {valid_classifications}"
            )

        expected_phases = profile.get("expected_phases")
        if expected_phases is not None:
            if not isinstance(expected_phases, int) or expected_phases < 1:
                errors.append("complexity_profile.expected_phases must be positive integer")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_semantic.py <playbook.json>")
        sys.exit(1)

    path = sys.argv[1]
    playbook = json.loads(Path(path).read_text())

    errors, warnings = validate_semantic(playbook)

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN: {w}")
        sys.exit(1)
    elif warnings:
        print(f"PASS with {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  WARN: {w}")
        sys.exit(0)
    else:
        print("PASS: All semantic checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()