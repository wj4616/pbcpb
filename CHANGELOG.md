# Changelog

All notable changes to the Playbook Creator Playbook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [3.1.0] - 2026-03-31

### Added
- **Context Budget Validation** - Feasibility check at playbook creation time
  - `estimate_context_tokens()` and `estimate_critical_tokens()` in context_budget.py
  - Warnings when context_load exceeds budget
- **Execution Feedback Loop** - Captured runs feed back into creator
  - `execution_log.py` with CLI for list/show/latest
  - Separate JSON file per run with failure modes and metrics
- **Session Boundary Resilience** - Checksum verification across breaks
  - `checkpoint_manager.py` with CLI for save/verify/list/get
  - Phase 0 edge case handling
- **Semantic Validation** - Logical consistency checks
  - `validate_semantic.py` for role mindset references
  - Failure mode phase reference validation
  - Complexity profile validation
- **Complexity Gate** - Scoring-based verification
  - `complexity_gate.py` with classify/verify commands
  - 0-12 scoring system with variance thresholds
  - Phase 0 and final phase integration
- **Constants Module** - Configurable thresholds
  - `DEFAULT_FILE_TOKENS_ESTIMATE`, `COMPLEXITY_LIMITS`, `COMPLEXITY_VARIANCE_THRESHOLD`

### Changed
- `validate_playbook.py` integrates context budget feasibility
- `output-schema.json` adds `complexity_profile` definition
- `compilation/__init__.py` exports new functions

### Tests
- `scripts/compilation/test_validate_semantic.py` - Role extraction and semantic checks
- `scripts/compilation/test_complexity_gate.py` - Scoring and verification
- `scripts/compilation/test_checkpoint_manager.py` - Checksum save/verify, phase 0 edge case
- `scripts/compilation/test_execution_log.py` - Log creation and reading

## [3.0.0] - 2026-03-31

### Added
- **KB Bootstrapping Phase** - New Phase 3 for initial KB population (FP1, FP12)
  - Populates KB from Phase 1 research before Phase 4 architecture
  - Enables progressive KB population throughout workflow
- **JSON Assembly/Validation Split** - Phase 8 split into Phases 9-10 (FP2)
  - Phase 9: JSON Assembly (structure, schema validation)
  - Phase 10: JSON Validation & Consistency (cross-reference checks)
- **Complexity Classifier** - Phase 0 task for domain complexity governance (FP15)
  - Classifies domain as simple/moderate/complex/structured
  - Informs phase scope and checklist depth
- **Pilot Restructure** - Phase 14 restructured for AI agent context (FP4)
  - Structured dry-run replaces open-ended pilot testing
  - Specific test scenarios with pass/fail criteria
- **Role Enhancements**
  - `agent_assignment` field for multi-agent systems
  - `role_context` field for baseline activation prompt
- **Metrics ID Field** - Metrics gain required `id` field (MET-NN format)
- **Cross-Cutting Concerns Objects** - CCC can be objects with `id`, `enforcement_method`, `phases_applied`
- **20 Seeded Failure Modes** - Pre-populated failure modes from JUCE VST execution (FP7)

### Changed
- Version bumped from 2 to 3
- Phase count increased from 15 to 17
- Role Engineering phase updated with agent_assignment
- Task Engineering phase updated with CCC enforcement_method weaving
- Gap Analysis phase updated with phases_applied audit
- Documentation phase updated with metrics report task

### Fixed
- Session strategy revised (11 sessions vs 8)
- Handoff chain redesigned for KB bootstrapping flow

## [2.0.0] - 2026-03-31

### Added
- **Compilation Block Enhancements** - Major new feature for agent configuration
  - `defaults` section at playbook level with model, temperature, max_tokens, context_budget_tokens, system_prompt_budget, critical_priority_threshold, model_fallbacks
  - `agent_config` in compilation blocks for phase-level model parameter overrides
  - `system_prompt_auto` flags to control system prompt generation sections
  - `context_budget` with priority-based file loading (1=highest, 10=lowest)
  - `skill_preparation` field for pre-phase skill execution
- **Role Object Format** - Roles can now be objects with `description` and `defaults` fields
  - Role-level model defaults
  - Role-level temperature ranges (min/max array format)
- **Handoff Enhancements**
  - `excluded_files` replaces deprecated `excluded_context`
  - `skill_validation` replaces deprecated `skill`
  - `context_update` field for tracking persistent file changes
- **Model Fallback System** - Graceful degradation when models unavailable
  - Three-level resolution: phase > role > playbook > default
  - Fallback chain logging for transparency
- **Context Budget Loading** - Priority-based file loading with critical protection
  - Files at priority 1-N (threshold) cannot be skipped
  - Token budget enforcement before loading
- **System Prompt Generation** - Automatic assembly from role, objective, failure modes
- **Compilation Module** - `scripts/compilation/` with utilities:
  - `constants.py` - Default values for all parameters
  - `model_fallback.py` - Model resolution with fallback chains
  - `context_budget.py` - Priority-based context loading
  - `system_prompt.py` - System prompt generation
- **Integration Tests** - Comprehensive test suite in `scripts/compilation/test_integration.py`
- **Validation Updates** - Enhanced `validate_playbook.py` for all new fields

### Changed
- Roles converted from simple strings to object format with defaults
- Version bumped from 1 to 2
- All 15 phases updated with complete compilation blocks
- README.md updated with compilation block documentation

### Deprecated
- `excluded_context` in handoff blocks - use `excluded_files` instead
- `skill` in handoff blocks - use `skill_validation` instead

### Security
- Input validation for all new numeric fields (ranges, minimums)
- Priority value validation (1-10 range)
- Orphaned priority file detection (files in priority but not context_load)

## [1.0.0] - 2025-03-27

### Added
- Initial 15-phase playbook structure
- Core phases: Commission, Research, KB Construction, Architecture, Role Engineering, Task Engineering, Output Configuration, Metrics, JSON Assembly, Quality Audit (Gap Analysis, Stress Testing), Stakeholder Review, Pilot Test, Documentation, Continuous Improvement
- Role-based single-agent workflow model
- Phase gates with explicit conditions and blocker examples
- Handoff chain continuity validation
- Artifact provenance tracking
- Knowledge base architecture specification
- Failure modes cataloging
- Cross-cutting concerns documentation
- Metrics and KPI definition framework
- JSON Schema validation (output-schema.json)
- Role mapping reference (role-mapping.json)
- Structural validation script (validate_playbook.py)

[Unreleased]: https://github.com/anthropics/claude-code/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/anthropics/claude-code/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/anthropics/claude-code/releases/tag/v1.0.0