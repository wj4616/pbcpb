# Playbook Creator — Usage Guide

## What is a Playbook?

A **playbook** is a structured, step-by-step guide that breaks a complex process into
phases, tasks, and quality checkpoints. It's encoded as a JSON file so that both
humans and AI agents can follow it consistently.

Think of it as a detailed recipe — but instead of cooking, it guides someone through
any multi-step process: building software, running an audit, onboarding a team,
designing a product, or anything else that benefits from repeatable structure.

**Why playbooks matter:**

- They capture expert knowledge so anyone can follow the process
- They prevent steps from being skipped or done out of order
- They define "done" at every stage with measurable criteria
- They work for solo operators, teams, and AI agents alike

**What you'll build:** A domain-specific playbook JSON file for *your* process,
whatever that process is. By the end, you'll have a validated, production-ready
playbook that anyone can follow.

**What you'll use:** This system — the Playbook Creator — which is itself a playbook
that guides you through building yours. You work through it with an AI agent that
handles the heavy lifting while you provide the domain knowledge.

---

## Quick Start

Get from zero to your first phase in under 2 minutes.

**Prerequisites:** Python 3, an AI agent (Claude, GPT, or similar), a terminal.

1. Open a terminal and `cd` into this project directory
2. Start a new AI agent session
3. Load `playbook-creator-playbook.json` as context for the session
4. Tell the AI: *"I want to create a playbook for [your domain]. Let's start Phase 0."*
5. Answer the AI's questions about your purpose, scope, and constraints
6. When Phase 0's gate passes, continue to Phase 1

That's it. The AI reads each phase's instructions and guides you through the tasks.
You provide the domain expertise; the AI provides the structure.

> **Tip:** Before starting, have a one-paragraph description ready of the process you
> want to turn into a playbook. This is your "commission brief" and Phase 0 needs it
> immediately.

---

## How the System Works

Three concepts make up the entire system: **phases**, **roles**, and **gates**.

### Phases

The playbook creator has 17 phases, numbered 0 through 16. You work through them
in order. Each phase has:

- A **purpose** — what this phase accomplishes
- A set of **tasks** — specific things to do
- A **gate** — conditions that must all pass before you move to the next phase

You don't need to memorize the phases. The AI reads them and tells you what to do.
For orientation, the 17 phases group into five stages:

| Stage | Phases | What Happens |
|-------|--------|-------------|
| Scoping | 0 | Define what you're building, for whom, and why |
| Research & KB | 1-3 | Research your domain, design a knowledge base, populate it |
| Architecture & Engineering | 4-8 | Design phases, roles, tasks, outputs, and metrics for your playbook |
| Assembly & Validation | 9-12 | Build the JSON file, validate it, audit for gaps, stress test |
| Review & Launch | 13-16 | Stakeholder review, pilot dry-run, documentation, improvement plan |

*These five stages are navigational groupings to help you track where you are —
they don't appear in the system itself.*

### Roles

The system uses 6 functional roles. These are **mindsets**, not separate people.
In single-agent mode (the default), you and the AI switch between them depending
on the phase:

| Role | Mindset | Primary Phases |
|------|---------|---------------|
| Stakeholder | "What do we need and why?" | 0, 13 |
| Researcher | "What does the domain look like?" | 1 |
| Architect | "How should we structure this?" | 2, 4-8 |
| Builder | "Let me assemble it precisely." | 3, 6-10 |
| Auditor | "What's broken or missing?" | 11-12 |
| Coordinator | "Are we on track?" | Every gate |

The AI tells you which role is active. You don't need to manage this manually.

### Gates

Every phase ends with a **gate** — a checkpoint with explicit pass/fail conditions.
Nothing advances until all conditions are met.

Each gate includes:

- **Conditions** — specific, measurable criteria (e.g., "Scope has explicit in/out/adjacent lists")
- **Blocker examples** — what failure looks like (e.g., "Purpose statement says 'improve the process' without specifying which process — too vague, rewrite")
- **Handoff artifacts** — files that carry forward to the next phase

If a gate condition fails, the AI tells you what's wrong and what to fix. You don't
advance until it passes. This is intentional — it prevents compounding problems
across phases.

### Tracking Files

Three files persist across all 17 phases. The AI creates them in Phase 0 and
updates them at every gate:

| File | Purpose |
|------|---------|
| `decisions-ledger.md` | Records every decision and its rationale |
| `artifact-manifest.md` | Tracks every file created, its phase, and status |
| `metrics-tracker.md` | Records measurements at each gate |

These are your continuity mechanism. When you start a new AI session, load these
files so the AI knows what happened in prior phases.

---

## Phase-by-Phase Guide

This section maps what you do, produce, and verify at each stage. The AI handles
the detailed task list — this is your high-level orientation.

### Stage 1: Scoping (Phase 0)

**What you do:** Define exactly what playbook you're building. Answer questions
about purpose, target users, scope boundaries, success criteria, and constraints.
Classify your domain's complexity (simple, standard, or complex) across three
dimensions: process, knowledge, and roles.

**What you produce:**

| File | Content |
|------|---------|
| `README.md` | Purpose statement and project overview |
| `scope.md` | What's in scope, out of scope, and adjacent |
| `constraints.md` | Technology, methodology, timeline, and compliance constraints |
| `success-criteria.md` | Measurable criteria for the finished playbook |
| `decisions-ledger.md` | Initialized (empty, with headers) |
| `artifact-manifest.md` | Initialized (empty, with headers) |
| `metrics-tracker.md` | Initialized (empty, with headers) |

**Done when:** Purpose is one unambiguous paragraph. Scope has explicit in/out/adjacent
lists. Success criteria are measurable. Constraints are documented. Complexity profile
is recorded.

### Stage 2: Research & Knowledge Base (Phases 1-3)

**Phase 1 — Domain Research:** Research the domain your playbook serves. Produce
documents covering standard processes, best practices, competitive templates,
cross-cutting concerns, and (if applicable) an audit of any existing playbook
you're replacing. The AI may use web search to gather information.

**Phase 2 — KB Architecture:** Design the knowledge base structure for your
playbook. Define layers (if the domain needs multiple knowledge types), entry
schemas, bridge schemas (for translating between knowledge types), and a
population strategy.

**Phase 3 — KB Bootstrapping:** Build the knowledge base directory structure,
seed it with placeholder entries, harvest initial content from Phase 1 research,
and create bridge entries if applicable.

**What you produce:**

| Phase | Key Outputs |
|-------|------------|
| 1 | `research/domain-analysis.md`, `research/best-practices.md`, `research/competitive-templates.md`, `research/requirements.md` |
| 2 | `kb-architecture.md`, `entry-schema.json`, `bridge-schema.json`, `population-strategy.md`, `directory-structure.md` |
| 3 | `kb/` directory tree with entries, `kb/master-index.json` |

**Done when:** Research covers the domain comprehensively. KB architecture matches
the complexity profile from Phase 0. KB directory exists with at least placeholder
entries for every topic in every layer.

### Stage 3: Architecture & Engineering (Phases 4-8)

This is the design core. You're defining the structure of the playbook you'll build.

**Phase 4 — Process Architecture:** Break the real-world process into phases.
Define task granularity, dependency maps, and gate criteria for each phase.

**Phase 5 — Role Engineering:** Define the roles your playbook needs, their
responsibilities, handoff points between roles, and escalation paths.

**Phase 6 — Task Engineering:** Write every task for every phase. Each task gets
a title (prefixed with `[Role]`), owner, and description. Define all gates with
conditions, blocker examples, and handoff blocks.

**Phase 7 — Output Configuration:** Define what your playbook produces — output
format, schemas, templates, checklists, and cross-cutting concern enforcement.

**Phase 8 — Metrics & KPI Definition:** Define the metrics your playbook tracks,
collection methods, targets, and how they appear in `metrics-tracker.md`.

**What you produce:**

| Phase | Key Outputs |
|-------|------------|
| 4 | `architecture/phase-structure.md`, `architecture/dependency-map.md`, `architecture/phase-gates.md` |
| 5 | `architecture/role-definitions.md`, `architecture/handoff-points.md` |
| 6 | `drafts/task-list-v0.1.md` (all tasks, all gates) |
| 7 | `output-config.md` |
| 8 | `metrics-definition.md` |

**Done when:** Every phase has tasks. Every task has an owner. Every phase has a
gate with verifiable conditions. Roles are used consistently. Metrics are measurable.

### Stage 4: Assembly & Validation (Phases 9-12)

Now you build the actual JSON and verify it works.

**Phase 9 — JSON Assembly:** Assemble everything from Phases 0-8 into a single
playbook JSON file conforming to `templates/output-schema.json`. This is the
heaviest phase — the AI does most of the mechanical work.

**Phase 10 — JSON Validation:** Run the validation scripts. Fix every error. Check
internal consistency: do roles in tasks match defined roles? Are handoff chains
continuous? Does every phase have a gate?

**Phase 11 — Gap Analysis:** Audit the playbook for missing requirements, cross-cutting
concern gaps, phase coverage holes, contradictions, and failure modes.

**Phase 12 — Stress Testing:** Walk through the playbook as if you were running it.
Test scenarios: happy path, domain novice, knowledge base construction, blockers,
edge cases, and multi-session continuity. Catalog any failure modes discovered.

**What you produce:**

| Phase | Key Outputs |
|-------|------------|
| 9 | `drafts/playbook-v0.1.json` |
| 10 | `drafts/playbook-v0.1.json` (validated and fixed) |
| 11 | `audits/requirements-gap-analysis.md`, `audits/cross-cutting-audit.md`, `audits/phase-gap-analysis.md`, `audits/contradiction-audit.md`, and others (see phase tasks for full list) |
| 12 | `testing/scenario-happy-path.md`, `testing/scenario-domain-novice.md`, `testing/scenario-blockers.md`, `drafts/playbook-v0.2.json`, and others (see phase tasks for full list) |

**Done when:** Validation scripts pass with zero errors. Gap analysis surfaces no
critical issues. All stress test scenarios complete without unresolvable blockers.

### Stage 5: Review & Launch (Phases 13-16)

Final polish, testing, and documentation.

**Phase 13 — Stakeholder Review:** Step back and review the playbook as if you
were the person who commissioned it. Does it meet the success criteria from Phase 0?
Iterate until satisfied. This is a human decision point — take a break from the AI
if needed.

**Phase 14 — Pilot Dry-Run:** Run through the playbook as if it were real.
Build a scenario matrix, trace every handoff chain, identify friction points,
and apply fixes. Produce the final `playbook-v1.0.json`.

**Phase 15 — Documentation:** Write a CHANGELOG, a QUICKSTART guide for users
of your playbook, and a metrics report summarizing the creation process.

**Phase 16 — Continuous Improvement:** Define the improvement process for your
playbook. How will future feedback be collected? How will updates be applied?

**What you produce:**

| Phase | Key Outputs |
|-------|------------|
| 13 | `stakeholder-feedback.md`, `drafts/playbook-v{latest}.json` |
| 14 | `final/playbook-v1.0.json`, `testing/scenario-matrix.md`, `testing/handoff-chain-trace.md`, `testing/pilot-friction.md`, `audits/final-verification.md` |
| 15 | `final/CHANGELOG.md`, `final/QUICKSTART.md`, `final/metrics-report.md` |
| 16 | Updated `decisions-ledger.md` and `artifact-manifest.md` |

**Done when:** Stakeholder approves. Pilot dry-run passes. Documentation complete.
`final/playbook-v1.0.json` validates cleanly. You have a playbook.

---

## Working with Your AI Agent

### Session Strategy

The 17 phases don't fit in one AI conversation. Split them across sessions using
this recommended grouping:

| Session | Phases | Focus |
|---------|--------|-------|
| 1 | 0-1 | Scoping + domain research |
| 2 | 2-3 | KB design + bootstrapping |
| 3 | 4 | Process architecture (fresh eyes) |
| 4 | 5-6 | Role + task engineering |
| 5 | 7-8 | Output config + metrics |
| 6 | 9 | JSON assembly (heavy context) |
| 7 | 10 | Validation (fresh eyes) |
| 8 | 11-12 | Audit pair (gap analysis + stress testing) |
| 9 | 13 | Stakeholder review (human break) |
| 10 | 14 | Pilot dry-run |
| 11 | 15-16 | Documentation + improvement |

### Starting a New Session

At the beginning of each AI session, give the AI:

1. `playbook-creator-playbook.json` — the master playbook (load as context)
2. `decisions-ledger.md` — so it knows prior decisions
3. `artifact-manifest.md` — so it knows what files exist
4. Any output artifacts from the previous phase (listed in its gate's handoff)

Then say: *"We're starting Phase [N]. Here are the tracking files and handoff
artifacts from Phase [N-1]."*

**Shortcut:** Run this to see exactly what to load:

```bash
python3 scripts/show_handoff.py --phase N
```

Replace `N` with the phase you just completed. It prints the files to load,
the next phase's objective, and a suggested session opener.

### When the AI Loses Context

If the AI seems confused or forgets prior work:

- Re-load `decisions-ledger.md` and `artifact-manifest.md`
- Summarize where you left off in 2-3 sentences
- Point it to the specific phase in `playbook-creator-playbook.json`

The tracking files are your continuity mechanism. As long as they're up to date,
you can recover from any context loss.

---

## Validating Your Playbook

Run validation from the project root after JSON Assembly (Phase 9) and any time
you make changes. All scripts support `--help` for usage details.

### Generate a Scaffold (Before Phase 9)

Don't start Phase 9 from a blank file. Generate a valid skeleton first:

```bash
python3 scripts/generate_scaffold.py drafts/my-playbook.json --title "My Playbook" --phases 8 --roles 4
```

This produces a JSON file with all 16 required top-level fields, placeholder
content, and correctly formatted IDs. Search for `TODO` to find every placeholder
that needs real content. The AI agent fills these in during Phase 9.

### Structural Validation

```bash
python3 scripts/validate_playbook.py your-playbook.json
```

Checks: required fields present, roles used in tasks match defined roles, handoff
chains are continuous, gate conditions exist, file references are valid.

To also validate against the JSON Schema:

```bash
python3 scripts/validate_playbook.py your-playbook.json --schema templates/output-schema.json
```

(Requires `pip install jsonschema` — optional but recommended.)

### Semantic Validation

```bash
python3 scripts/validate_semantic.py your-playbook.json
```

Checks: logical consistency between phases, role usage patterns, gate condition
completeness, cross-cutting concern coverage.

### Unit Tests (Optional)

```bash
python3 -m pytest scripts/compilation/ -q
```

Tests the compilation block utilities. Run this if you've modified any scripts.

### Reading Validation Output

- **PASS** — All checks passed. Move forward.
- **PASS with N warning(s)** — Passed, but review the `WARN:` lines. Fix if easy, otherwise note in `decisions-ledger.md`.
- **FAIL** with specific error(s) — Fix exactly what it says. Re-run.

Common fixes:

| Error | Fix |
|-------|-----|
| "Role X used in task but not defined in roles" | Add the role to your playbook's `roles` section, or fix the task's `[Role]` prefix |
| "Phase N has no gate" | Add a gate item with `gate_conditions` to the end of that phase |
| "Handoff artifact X not in context_load of next phase" | Add the missing file to the next phase's `context_load` |
| "Required field missing: Y" | Add field Y — check `templates/output-schema.json` for the expected format |
| "id must match FM-NNN format" | Failure mode IDs need three digits: `FM-001`, `FM-025`, not `FM-1` |
| "id must match MET-NN format" | Metric IDs need two digits: `MET-01`, `MET-12`, not `MET-1` |

---

## Troubleshooting & FAQ

### "I'm stuck at a gate"

Every gate lists its conditions and blocker examples. Read the blocker examples —
they describe exactly what "stuck" looks like and imply what "unstuck" requires.

Common causes:
- Vague language ("improve things" instead of a specific measurable goal)
- Missing scope boundaries (no out-of-scope list)
- Subjective success criteria ("playbook is good" — define what "good" means)

Fix the underlying issue, don't try to skip the gate. Gates exist to prevent
problems from compounding across phases.

### "Validation failed"

1. Read the error message — it tells you which check failed and why
2. Fix the specific issue (see the common fixes table above)
3. Re-run validation
4. Repeat until clean

If an error is unclear, paste it to your AI agent and ask for an explanation.

### "My AI lost context between sessions"

Load these files at the start of every session:
- `playbook-creator-playbook.json` (the master playbook)
- `decisions-ledger.md` (all decisions so far)
- `artifact-manifest.md` (all files so far)
- Handoff artifacts from the most recent completed phase

Tell the AI which phase you're starting. It will pick up from there.

### "How long does this take?"

Depends on domain complexity. These are rough estimates based on the session
strategy, not guarantees:

| Complexity | Estimated Sessions | Approximate Time |
|-----------|-------------------|-----------------|
| Simple (1-4 phase process, flat KB, 2 roles) | 5-7 | 1-2 days |
| Standard (5-10 phases, layered KB, 3-4 roles) | 8-11 | 2-4 days |
| Complex (11+ phases, bridged KB, 5+ roles) | 11-15 | 4-7 days |

Your mileage will vary. Phase 0 (scoping) and Phases 11-12 (auditing) typically
take the most thought. Phase 9 (JSON assembly) takes the most AI time.

### "Do I need to read the playbook JSON?"

For normal usage, no. The AI reads it and guides you. You may want to reference
it directly if:
- You're curious what a specific phase contains
- You need to debug an unusual validation error
- You want to understand why the AI is asking a particular question

### "Can I skip phases?"

No. Each phase produces artifacts that later phases depend on. Skipping Phase 2
(KB Architecture) means Phase 3 (KB Bootstrapping) has nothing to build, and
Phase 9 (JSON Assembly) will produce an incomplete playbook. The gates enforce
this — you can't pass a gate for work you haven't done.

### "This is my first playbook. Any tips?"

- Start with a process you know well — you'll spend less time researching (Phase 1)
  and more time learning the system
- Keep scope small for your first attempt — a 5-8 phase playbook with 3-4 roles
- Don't overthink Phase 2 (KB Architecture) — a flat knowledge base is fine for
  simpler domains
- Phase 0 is the most important phase. A clear scope prevents rework everywhere else

---

## Glossary

| Term | Definition |
|------|-----------|
| **Playbook** | A JSON file containing phases, tasks, roles, gates, and metadata that guides a process from start to finish |
| **Phase** | One of 17 sequential stages in the creation process (numbered 0-16), each with tasks and a gate |
| **Gate** | A checkpoint at the end of a phase with explicit pass/fail conditions; nothing advances until all conditions pass |
| **Role** | A functional mindset (Stakeholder, Researcher, Architect, Builder, Auditor, Coordinator) adopted per phase — not a separate person |
| **Task** | A specific piece of work within a phase, prefixed with `[Role]` to indicate who owns it |
| **Handoff** | The set of artifacts passed from one phase to the next, ensuring continuity |
| **Knowledge base (KB)** | A structured collection of domain knowledge your playbook references; designed in Phase 2, built in Phase 3 |
| **Commission brief** | Your initial description of what playbook you want to build — input for Phase 0 |
| **Compilation block** | Internal per-phase configuration used by the AI agent (context loading, role mindset, objectives). You don't write or manage these. |
| **Cross-cutting concern** | A quality standard that applies across multiple phases (e.g., "every task must have an owner") |
| **Decisions ledger** | `decisions-ledger.md` — persistent file tracking every decision and its rationale across all phases |
| **Artifact manifest** | `artifact-manifest.md` — persistent file tracking every file created across all phases |
| **Output schema** | `templates/output-schema.json` — the JSON Schema your finished playbook must conform to |
