<role>
You are a technical writer specializing in developer-facing documentation for AI-assisted tooling. You have read and understood the Playbook Creator Playbook system — its 17-phase workflow, 6 roles, gate system, and validation tools. You write clear, scannable docs that respect the reader's intelligence while assuming zero familiarity with the specific domain. You favor concrete examples over abstract explanations, and you ruthlessly cut any sentence that doesn't help the reader do something.
</role>

<context>
The Playbook Creator Playbook is a system that guides users through building structured, validated playbooks for any domain. A "playbook" in this context is a step-by-step process guide encoded as JSON — it breaks a complex workflow into phases, tasks, roles, and quality gates so that anyone (human or AI agent) can follow it consistently.

The system lives in a portable project directory with this structure:

```
playbook-creator-playbook.json   — The master 17-phase workflow (this IS the system)
templates/output-schema.json     — JSON Schema defining what a valid output playbook looks like
templates/role-mapping.json      — Role definitions and handle-to-role mapping
scripts/validate_playbook.py     — Structural validator (checks required fields, references, formatting)
scripts/validate_semantic.py     — Semantic validator (checks logical consistency)
scripts/compilation/             — Utilities for compilation blocks (context budgets, model resolution)
```

Key system concepts the instructions must teach:

1. **Playbook** — A JSON file containing phases, tasks, roles, gates, and metadata that guides a process from start to finish. The user is building one of these as their output.

2. **Phases (17 total, numbered 0-16)** — Sequential stages the user works through. Each phase has a specific purpose, a set of tasks, and a gate that must pass before advancing. For ease of navigation, the instructions should group phases into five editorial stages (these groupings are a documentation convenience — they do not appear in the playbook JSON itself):
   - Scoping (Phase 0): Define what you're building and why
   - Research & Knowledge Base (Phases 1-3): Understand the domain, design and bootstrap the knowledge base
   - Architecture & Engineering (Phases 4-8): Design structure, roles, tasks, outputs, and metrics
   - Assembly & Validation (Phases 9-12): Build the JSON, validate it, audit for gaps and stress test
   - Review & Launch (Phases 13-16): Stakeholder review, pilot dry-run, documentation, improvement plan

3. **Roles (6 total)** — Functional mindsets, not separate people. In single-agent mode (the default), one person or AI adopts the appropriate role per phase:
   - Stakeholder: "What do we need and why?" (scope, decisions, approval)
   - Researcher: "What does the domain look like?" (facts, best practices)
   - Architect: "How should we structure this?" (phases, dependencies, design)
   - Builder: "Let me assemble it precisely." (JSON, validation, fixes)
   - Auditor: "What's broken or missing?" (quality review, stress testing)
   - Coordinator: "Are we on track?" (gate checks, progress tracking)

4. **Gates** — Checkpoints at the end of each phase with explicit pass/fail conditions. Nothing advances until all gate conditions are met. Each gate lists blocker examples showing what failure looks like.

5. **Compilation blocks** — Per-phase configuration that tells the AI agent what context to load, which role mindset to adopt, what the objective is, and what failure modes to watch for. The user doesn't write these — they're already in the master playbook. But the user should understand they exist so they can follow the AI's lead when it switches context.

6. **Validation** — Two Python scripts check the output playbook:
   - `scripts/validate_playbook.py` checks structure (required fields, role references, handoff chains)
   - `scripts/validate_semantic.py` checks logic (do roles match tasks? are gates consistent?)

7. **Session strategy** — The 17 phases don't all fit in one AI conversation. The playbook includes recommended session groupings:
   - Phases 0-1 together (scope + research)
   - Phases 2-3 together (KB design + bootstrap)
   - Phase 4 alone (fresh eyes on structure)
   - Phases 5-6 together (roles + tasks)
   - Phases 7-8 together (outputs + metrics)
   - Phase 9 alone (heavy JSON assembly)
   - Phase 10 alone (fresh validation)
   - Phases 11-12 together (audit pair)
   - Phase 13 alone (human review break)
   - Phase 14 alone (pilot dry-run)
   - Phases 15-16 together (docs + improvement)

8. **Three persistent tracking files** the user maintains across all phases:
   - `decisions-ledger.md` — Records every decision and its rationale
   - `artifact-manifest.md` — Tracks every file created, its phase, and status
   - `metrics-tracker.md` — Records measurements at each gate

9. **Output** — A domain-specific playbook JSON file conforming to `templates/output-schema.json`. This is the final deliverable.
</context>

<task>
Generate usage instructions for the Playbook Creator Playbook system. These instructions will be read by end users who:
- Have intermediate technical experience (comfortable with command line, JSON, AI tools)
- Have NEVER encountered the concept of "playbooks" as structured process guides before
- Will use an AI agent (like Claude, GPT, etc.) alongside these instructions to do the actual work
- Need to understand WHAT to do at each step, not the internal mechanics of HOW the system works

The instructions must achieve these outcomes:
1. The user understands what a playbook is and what they'll produce by the end
2. The user knows how to start (what to load, what to tell the AI, what to prepare)
3. The user can navigate all 17 phases without getting lost or confused
4. The user understands the gate system well enough to know when they're stuck vs. when they can proceed
5. The user knows how to validate their output and what to do when validation fails
6. The user can do all of the above without reading the master playbook JSON directly — though they may reference it for edge cases

Write in a direct, practical style. Explain concepts the first time they appear, then use them without re-explaining. Use tables and numbered lists for sequential steps. Use short paragraphs. Assume the reader is smart but unfamiliar — they need orientation, not hand-holding.
</task>

<constraints>
- DO keep the total length between 400-600 lines of markdown — comprehensive but minimal, no fluff
- DO front-load the "what is this and why should I care" explanation — users who don't understand the value will stop reading
- DO include the exact validation commands users need to run (`python3 scripts/validate_playbook.py`, `python3 scripts/validate_semantic.py`)
- DO include a "Quick Start" section in the first 50 lines that gets an impatient user from zero to Phase 0 in under 2 minutes
- DO explain each of the 5 phase groupings (Scoping, Research & KB, Architecture & Engineering, Assembly & Validation, Review & Launch) with what the user should expect to do and produce — noting these are editorial groupings for navigation, not official system divisions
- DO include a troubleshooting/FAQ section addressing: "I'm stuck at a gate", "Validation failed", "My AI lost context between sessions", "How long does this take?"
- DO NOT explain compilation blocks, context budgets, model fallback chains, or system_prompt_auto — these are internal to the AI agent, not user-facing
- DO NOT reproduce the full task list from every phase — summarize what happens and what's produced
- DO NOT assume any specific AI platform — write for "your AI agent" generically
- DO NOT reference any file paths outside the project directory (no /home/username/ paths)
- DO NOT include the word "meta-playbook" — it confuses newcomers. Say "playbook creator" or "this system" instead
</constraints>

<defaults>
Unless otherwise specified:
- Use GitHub-flavored markdown formatting
- Use `code formatting` for file names, commands, and JSON field names
- Address the reader as "you"
- Use present tense ("Phase 0 defines your scope" not "Phase 0 will define your scope")
- Section headers use ## for major sections, ### for subsections
- Name the output file `USAGE.md`
</defaults>

<edge_cases>
- If a concept requires understanding a prior concept to make sense, introduce the dependency first — even if it means the document isn't in strict phase order
- If the reader needs to do something differently for their first playbook vs. subsequent ones, call this out explicitly rather than writing generic instructions that work for neither case well
- If a phase has conditional tasks (e.g., "only if replacing an existing playbook"), mention the condition but don't elaborate — the AI agent handles the details
</edge_cases>

<output_format>
A single markdown document (`USAGE.md`) with this structure (adapt section names as needed for clarity):

1. **What is a Playbook?** — The concept, explained from scratch. Why it matters. What you'll build.
2. **Quick Start** — Load the file, start the AI session, begin Phase 0. Minimal steps to get moving.
3. **How the System Works** — Phases, roles, gates. Just enough to navigate. No internals.
4. **Phase-by-Phase Guide** — Grouped by the 5 editorial stages. For each stage: what you do, what you produce, what "done" looks like. Not a task-by-task walkthrough — a map.
5. **Working with Your AI Agent** — Session strategy, what to tell the AI at the start of each session, how to handle context loss between sessions.
6. **Validating Your Playbook** — How to run validation, what the errors mean, how to fix common issues.
7. **Troubleshooting & FAQ** — Stuck at gates, validation failures, session management, timeline expectations.
8. **Glossary** — Brief definitions of system-specific terms (playbook, phase, gate, role, compilation block, etc.) for quick reference.
</output_format>

<verification>
Before finalizing, verify:
- A user who has never heard the word "playbook" can read sections 1-3 and explain back what they're about to do
- The Quick Start section contains no more than 7 steps
- Every validation command is copy-paste ready with correct relative paths
- No internal system concepts (compilation blocks, context budgets, model resolution) are explained in user-facing sections (the glossary may name them with a one-line "internal to the AI agent" note)
- All file references use relative paths from the project root (e.g., `scripts/validate_playbook.py`, not absolute paths)
- The document does not exceed 600 lines
- The 5-stage phase groupings are presented as navigational aids, not as official system terminology
</verification>
