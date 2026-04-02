"""
System prompt generator for compilation blocks.

Assembles system prompts from playbook components:
- Role definition from roles object
- Role mindset from compilation block
- Phase objective
- Pre-check guidance
- Failure modes (looked up from failure_modes array)
- Context file descriptions (from artifact-manifest.md)
- Success criteria (surfaced at phase start)
- Tools available (prevents role bleed)
- Behavioral profile (phase-specific tuning)
- Output requirements
"""

from typing import Any
from .constants import CHARS_PER_TOKEN


def generate_system_prompt(
    playbook: dict[str, Any],
    phase: dict[str, Any],
    loaded_files: dict[str, str],
    flags: dict[str, bool] | None = None,
) -> str:
    """
    Generate a system prompt for a phase execution.

    Args:
        playbook: Full playbook JSON
        phase: Phase checklist dict with compilation block
        loaded_files: Dict of filename -> content for context
        flags: Optional flags to control prompt sections

    Returns:
        Generated system prompt string
    """
    # Default flags
    if flags is None:
        flags = {
            "role_definition": True,
            "phase_objective": True,
            "failure_modes": True,
            "pre_check_guidance": True,
            "context_files": True,
            "handoff_requirements": True,
        }

    compilation = phase.get("compilation", {})
    role_mindset = compilation.get("role_mindset", "Coordinator")

    # Extract role name from "Role — description" format
    if " — " in role_mindset:
        role_name = role_mindset.split(" — ")[0].strip()
        mindset_text = role_mindset.split(" — ", 1)[1].strip() if " — " in role_mindset else ""
    else:
        role_name = role_mindset.strip()
        mindset_text = ""

    # Get role definition
    roles = playbook.get("roles", {})
    role_def = roles.get(role_name, "")

    # Handle both string and object role definitions
    if isinstance(role_def, dict):
        role_description = role_def.get("description", "")
        role_context = role_def.get("role_context", "")
    else:
        role_description = role_def
        role_context = ""

    workflow_model = playbook.get("workflow_model", "role-based-single-agent")

    # Build prompt sections
    sections = []

    # Header
    sections.append(f"You are a {role_name} in a {workflow_model} workflow.\n")

    # Role definition
    if flags.get("role_definition", True) and role_description:
        sections.append(f"{role_description}")
        if role_context:
            sections.append(f"{role_context}")
        sections.append("")

    # Role mindset with expansion
    sections.append("## Your Role")
    if mindset_text:
        sections.append(f"{role_name} — {mindset_text}")
        # Expanded mindset guidance
        sections.append(f"Your mindset is focused on {mindset_text.lower()}.")
    else:
        sections.append(f"{role_mindset}")
    sections.append("")

    # Phase objective
    if flags.get("phase_objective", True):
        objective = compilation.get("objective", "")
        if objective:
            sections.append("## Your Objective This Phase")
            sections.append(f"{objective}\n")

    # Pre-check guidance
    if flags.get("pre_check_guidance", True):
        pre_check = compilation.get("pre_check", [])
        if pre_check:
            sections.append("## Pre-Flight Checks")
            sections.append("Before starting, verify:")
            for check in pre_check:
                sections.append(f"- {check}")
            sections.append("")

    # Failure modes
    if flags.get("failure_modes", True):
        fm_ids = compilation.get("failure_modes_relevant", [])
        failure_modes = playbook.get("failure_modes", [])
        if fm_ids and failure_modes:
            fm_map = {fm.get("id"): fm for fm in failure_modes}
            relevant_fms = [fm_map.get(fid) for fid in fm_ids if fid in fm_map]
            relevant_fms = [fm for fm in relevant_fms if fm]
            if relevant_fms:
                sections.append("## Failure Modes to Watch For")
                for fm in relevant_fms:
                    symptom = fm.get("symptom", "")
                    prevention = fm.get("prevention", "")
                    fm_id = fm.get("id", "")
                    sections.append(f"- {fm_id}: {symptom}")
                    if prevention:
                        sections.append(f"  Prevention: {prevention}")
                sections.append("")

    # Context files
    if flags.get("context_files", True) and loaded_files:
        sections.append("## Context Files Loaded")
        # Get descriptions from artifact-manifest if available
        manifest = _parse_artifact_manifest(loaded_files)
        for filename in loaded_files:
            desc = manifest.get(filename, "")
            if desc:
                sections.append(f"- {filename}: {desc}")
            else:
                sections.append(f"- {filename}")
        sections.append("")

    # Success criteria (surfaced at phase START so agent works toward targets)
    success_criteria = compilation.get("success_criteria", [])
    if success_criteria:
        sections.append("## Success Criteria")
        sections.append("This phase is complete when ALL of the following are true:")
        for criterion in success_criteria:
            sections.append(f"- {criterion}")
        sections.append("")

    # Tools available (prevents role bleed)
    tools_available = compilation.get("tools_available", [])
    if tools_available:
        sections.append("## Allowed Tools & Capabilities")
        sections.append("For this phase, restrict yourself to:")
        for tool in tools_available:
            sections.append(f"- {tool}")
        sections.append("Do NOT use tools or capabilities outside this list.")
        sections.append("")

    # Behavioral profile (phase-specific tuning)
    behavioral = compilation.get("behavioral_profile", {})
    if behavioral:
        sections.append("## Behavioral Profile")
        if "risk_tolerance" in behavioral:
            risk_map = {
                "minimal": "Reject anything uncertain. Only proceed with verified information.",
                "low": "Prefer safe, proven approaches. Flag uncertainties before acting.",
                "moderate": "Accept reasonable risk when benefits are clear.",
                "high": "Explore freely. Propose alternatives even if unconventional.",
            }
            sections.append(f"- Risk tolerance: {behavioral['risk_tolerance']} — {risk_map.get(behavioral['risk_tolerance'], '')}")
        if "creativity_level" in behavioral:
            creativity_map = {
                "strict": "Follow specifications exactly. No creative interpretation.",
                "conservative": "Minor improvements allowed if clearly beneficial.",
                "moderate": "Suggest improvements alongside spec compliance.",
                "exploratory": "Actively propose alternatives and creative solutions.",
            }
            sections.append(f"- Creativity: {behavioral['creativity_level']} — {creativity_map.get(behavioral['creativity_level'], '')}")
        if "verbosity" in behavioral:
            verbosity_map = {
                "minimal": "Headings and bullets only. No prose.",
                "concise": "Brief, focused output. Key points only.",
                "detailed": "Balanced detail. Explain reasoning for non-obvious decisions.",
                "comprehensive": "Thorough coverage. Document all findings and rationale.",
            }
            sections.append(f"- Verbosity: {behavioral['verbosity']} — {verbosity_map.get(behavioral['verbosity'], '')}")
        if "stance" in behavioral:
            stance_map = {
                "supportive": "Help this work succeed. Constructive feedback only.",
                "neutral": "Objective assessment. Report findings without bias.",
                "critical": "Scrutinize everything. Flag issues proactively.",
                "adversarial": "Try to break it. Find what others missed.",
            }
            sections.append(f"- Stance: {behavioral['stance']} — {stance_map.get(behavioral['stance'], '')}")
        sections.append("")

    # Output requirements
    if flags.get("handoff_requirements", True):
        # Find handoff in gate task
        for item in phase.get("items", []):
            handoff = item.get("handoff", {})
            if handoff:
                output_artifacts = handoff.get("output_artifacts", [])
                if output_artifacts:
                    sections.append("## Output Requirements")
                    sections.append("This phase produces:")
                    for artifact in output_artifacts:
                        sections.append(f"- {artifact}")
                    break
        sections.append("")

    return "\n".join(sections)


def _parse_artifact_manifest(loaded_files: dict[str, str]) -> dict[str, str]:
    """
    Parse artifact-manifest.md to get file descriptions.

    Args:
        loaded_files: Dict of filename -> content

    Returns:
        Dict of filename -> description
    """
    descriptions = {}

    manifest_content = loaded_files.get("artifact-manifest.md", "")
    if not manifest_content:
        return descriptions

    # Parse markdown table
    # Format: | File | Phase | Status | Summary |
    lines = manifest_content.strip().split("\n")
    in_table = False

    for line in lines:
        if line.startswith("| File |"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                filename = parts[1]
                summary = parts[4]
                descriptions[filename] = summary

    return descriptions


def estimate_prompt_tokens(prompt: str) -> int:
    """
    Estimate token count for a prompt.

    Uses heuristic from constants.

    Args:
        prompt: Prompt string

    Returns:
        Estimated token count
    """
    return len(prompt) // CHARS_PER_TOKEN