# Playbook Creator Playbook (PBCPB)

A meta-playbook for creating domain-specific playbooks through 16 phases of research, knowledge base construction, architecture, task engineering, assembly, validation, and structured dry-run.

## What This Does

This playbook guides the creation of **domain-specific playbooks** — structured JSON files that encode complex multi-step processes. Whether you're building software, running audits, onboarding teams, or managing any repeatable process, this system helps you create a playbook that anyone (or any AI agent) can follow.

**Key Features:**
- 16-phase workflow from scoping to launch
- 6 functional roles (Stakeholder, Researcher, Architect, Builder, Auditor, Coordinator)
- Gate-based progression with explicit verification
- Knowledge base architecture for domain expertise
- Compilation blocks for agent context management
- Cross-cutting concerns and failure modes built-in

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/pbcpb.git
cd pbcpb

# The main playbook file
# Load this as context for your AI agent
playbook-creator-playbook.json
```

**With an AI Agent:**
1. Load `playbook-creator-playbook.json` as context
2. Tell the AI: "I want to create a playbook for [your domain]. Let's start Phase 0."
3. Answer the AI's questions about purpose, scope, and constraints
4. Work through phases sequentially

**Prerequisites:** Python 3, an AI agent (Claude, GPT, or similar)

## Documentation

| File | Purpose |
|------|---------|
| [`docs/USAGE.md`](docs/USAGE.md) | Comprehensive usage guide |
| [`CHANGELOG-v4.md`](CHANGELOG-v4.md) | Detailed changelog for v4 |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Full version history |
| [`playbook-creator-playbook.json`](playbook-creator-playbook.json) | The playbook itself |

## Structure

```
pbcpb/
├── playbook-creator-playbook.json  # Main playbook (37k tokens)
├── docs/
│   ├── USAGE.md                    # How to use the system
│   ├── CHANGELOG.md                # Version history
│   └── superpowers/                # Design docs and plans
├── scripts/                         # Validation and utility scripts
│   ├── validate_playbook.py        # Structural validation
│   ├── validate_semantic.py        # Logical consistency checks
│   └── compilation/                # Compilation block utilities
└── templates/
    └── output-schema.json          # JSON Schema for output playbooks
```

## The 16 Phases

| Stage | Phases | Focus |
|-------|--------|-------|
| Scoping | 0 | Configuration, purpose, scope, constraints, success criteria |
| Research & KB | 1-3 | Domain research, KB architecture, KB bootstrapping |
| Architecture | 4-8 | Process architecture, roles, tasks, outputs, metrics |
| Assembly & Validation | 9-12 | JSON assembly, validation, gap analysis, stress testing |
| Review & Launch | 13-15 | Stakeholder review, documentation, improvement |

## Phase 0 Configuration

Starting in v4.1, Phase 0 begins with a **configuration task** that establishes:
- **Output location**: Where the playbook will be saved (default: `~/playbooks/<playbook-name>/`)
- **External data permissions**: Which external sources (knowledge bases, playbooks, references) can be accessed

This ensures explicit consent before any external data is pulled, with batch options:
- `"none"` — Skip all external sources
- `"all"` — Include all available sources
- Specific selections — `"1 and 3"`, `"all except 2"`, etc.

## Validation

Run validation after Phase 9 (JSON Assembly) and any time you make changes:

```bash
# Structural validation
python3 scripts/validate_playbook.py your-playbook.json

# Semantic validation (optional, requires jsonschema)
python3 scripts/validate_playbook.py your-playbook.json --schema templates/output-schema.json

# Logical consistency checks
python3 scripts/validate_semantic.py your-playbook.json
```

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 4.1.0 | 2026-04-02 | Configuration task, CCC-CONFIG, audit fixes |
| 4.0.0 | 2026-03-31 | Phase inventory acknowledgment, FM-026, CCC-06 |
| 3.1.0 | 2026-03-31 | Context budget validation, execution feedback loop |
| 3.0.0 | 2026-03-31 | KB Bootstrapping phase, JSON assembly/validation split |

See [CHANGELOG-v4.md](CHANGELOG-v4.md) for detailed changes.

## Key Concepts

### Gates
Every phase ends with a gate — a checkpoint with explicit pass/fail conditions. Nothing advances until all conditions are met. This prevents compounding problems across phases.

### Roles
6 functional mindsets that switch per phase:
- **Stakeholder** — "What do we need and why?"
- **Researcher** — "What does the domain look like?"
- **Architect** — "How should we structure this?"
- **Builder** — "Let me assemble it precisely."
- **Auditor** — "What's broken or missing?"
- **Coordinator** — "Are we on track?"

### Tracking Files
Three files persist across all phases:
- `decisions-ledger.md` — Every decision and rationale
- `artifact-manifest.md` — Every file created
- `metrics-tracker.md` — Measurements at each gate

### Cross-Cutting Concerns
Quality standards that apply across multiple phases:
- CCC-01: Quality Standard
- CCC-02: Role Consistency
- CCC-03: Gate Enforcement
- CCC-04: Deliverable Tracking
- CCC-05: Context Preservation
- CCC-06: Gate Verification
- CCC-07: Path Configuration Compliance

## Troubleshooting

**"I'm stuck at a gate"** — Read the blocker examples. They describe exactly what "stuck" looks like.

**"Validation failed"** — Read the error message, fix the specific issue, re-run. See [docs/USAGE.md](docs/USAGE.md) for common fixes.

**"AI lost context"** — Re-load `decisions-ledger.md`, `artifact-manifest.md`, and the handoff artifacts from the last completed phase.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes
4. Run validation (`python3 scripts/validate_playbook.py playbook-creator-playbook.json`)
5. Commit with descriptive message
6. Push and create pull request

## License

MIT License — see [LICENSE](LICENSE) for details.

## Related Projects

- [JUCE Agent](https://github.com/yourusername/juce-agent) — VST plugin development playbook
- [Playbook Schema](templates/output-schema.json) — JSON Schema for output playbooks