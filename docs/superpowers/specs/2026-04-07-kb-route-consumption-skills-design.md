# KB-Route Consumption Skills Integration Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update consumption skills to use kb-route Resolution Procedure, expand bridge layer to 76 entries (71 new + 5 existing), populate technical layer, add 2 new skills.

**Architecture:** KB-first approach — populate bridge and technical layers before updating skills. Manual curation for all entries (kb-harvest and kb-validate skills not available). Interface preservation — skill invocations remain unchanged, internal behavior enhanced.

**Tech Stack:** kb-route skill, existing JUCE consumption skills, manual KB entry creation

**Prerequisite Check:**
- ✅ kb-route skill exists at `~/.claude/skills/kb-route/SKILL.md`
- ⚠️ kb-harvest skill NOT found — Phase 2 will use manual creation + kb-route validation
- ⚠️ kb-validate skill NOT found — Phase 2 will use manual validation via kb-route lookup
- ✅ vst-product-lifecycle KB exists with correct layer structure
- ✅ cross_layer_mappings already include bridge → technical

---

## Phase Overview

| Phase | Deliverable | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | Bridge Expansion: 71 new bridge entries | 17-23 hrs | None |
| 2 | Technical KB Population: 25 entries | 12-18 hrs | None |
| 3 | Registry Updates | 1-2 hrs | Phase 1, 2 |
| 4 | Consumption Skill Updates: 4 skills | 6-8 hrs | Phase 1, 2, 3 |
| 5 | New Consumption Skills: 2 skills | 2-4 hrs | Phase 4 |

**Total Effort:** 38-55 hours

---

## Phase 1: Bridge Expansion

### Pre-flight: Existing Entry Inventory

Before creating new entries, inventory existing entries to avoid collisions:

```bash
# Check existing bridge entries
ls $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/*/
```

**Existing entries (5):**
| Category | Entry ID | Status |
|----------|----------|--------|
| timbre | bridge_timbre_warm | EXISTS - skip in creation |
| dynamics | bridge_dynamics_punchy | EXISTS - skip in creation |
| space | bridge_space_wide | EXISTS - skip in creation |
| movement | bridge_movement_evolving | EXISTS - skip in creation |
| character | bridge_character_analog | EXISTS - skip in creation |

**Action:** Remove these from new entry lists. Update manifest to reflect existing entries.

### Categories & Entry Distribution (Adjusted)

| Category | New Entries | Total (New + Existing) |
|----------|-------------|------------------------|
| timbre | 14 (skip warm) | 15 |
| dynamics | 14 (skip punchy) | 15 |
| space | 15 (wide not in list) | 16 |
| movement | 14 (skip evolving) | 15 |
| character | 14 (skip analog) | 15 |

**Total: 71 new entries + 5 existing = 76 entries**

### New Entry Descriptors by Category

**timbre (14 new, skip warm):**
bright, dark, harsh, soft, nasal, plucky, metallic, glassy, wooden, breathy, buzzy, clean, distorted, thin

**dynamics (14 new, skip punchy):**
soft, aggressive, gentle, sharp, round, bouncy, flat, compressed, open, tight, loose, explosive, sustain, pluck

**space (15 new - wide already exists but not in list):**
intimate, cavernous, narrow, deep, shallow, distant, close, airy, dense, hollow, solid, ethereal, present, expansive, spacious

**movement (14 new, skip evolving):**
static, rhythmic, flowing, choppy, smooth, erratic, predictable, pulsing, swelling, fading, building, cycling, random, lfo

**character (14 new, skip analog):**
digital, lo-fi, hi-fi, vintage, modern, natural, synthetic, organic, mechanical, electric, acoustic, warm-digital, cold, hybrid

### Bridge Entry Schema

Each entry follows this structure:

```json
{
  "id": "bridge_timbre_warm",
  "category": "timbre",
  "descriptor": "warm",
  "parameters": [
    {
      "parameter": "filter_cutoff",
      "value_range": [0.2, 0.4],
      "typical_default": 0.3,
      "unit": "normalized",
      "notes": "Low-pass filter reduces high frequencies for warmth"
    },
    {
      "parameter": "filter_resonance",
      "value_range": [0.1, 0.2],
      "typical_default": 0.15,
      "unit": "normalized",
      "notes": "Subtle resonance adds character without harshness"
    }
  ],
  "confidence": 0.85,
  "why": "Warmth in audio is psychoacoustically associated with reduced high-frequency content. Low-pass filtering around 300-800Hz creates this perception.",
  "anti_patterns": [
    { "mistake": "Heavy saturation", "reason": "Too much saturation creates harshness, contradicting warmth" },
    { "mistake": "High resonance", "reason": "Resonance above 0.4 introduces ringing that breaks warmth" }
  ],
  "combinations": [
    {
      "compatible_with": "bridge_character_analog",
      "notes": "Analog character enhances warmth through drift and saturation",
      "confidence_modifier": 0.1
    },
    {
      "compatible_with": "bridge_dynamics_soft",
      "notes": "Soft dynamics complement warmth naturally",
      "confidence_modifier": 0.05
    }
  ]
}
```

### Entry Creation Method

Manual curation required for bridge entries due to subjective nature.

**Pre-flight: Sync Manifest**

Before creating entries, sync the manifest to reflect existing entries:

```bash
# Check current manifest state
cat $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json

# Manifest should show entry_count: 1 for each category with existing entry
# Current state: entry_count: 0 for all (out of sync)
```

Update manifest to include existing entries before creating new ones.

**Combination Ordering Strategy:**

New entries reference combinations (e.g., `bridge_character_analog`). To avoid circularity:
1. Create all entries WITHOUT `combinations[]` array first
2. After all entries exist, add `combinations[]` references to each entry
3. This ensures referenced entries exist before being referenced

**Process per entry:**
1. Define descriptor and category
2. Research typical parameter mappings from sound design literature
3. Define parameter ranges with typical defaults
4. Write "why" explanation (psychoacoustic/technical basis)
5. Identify anti-patterns (common mistakes)
6. Define compatible combinations with confidence modifiers
7. Assign initial confidence score (0.70-0.90 for curated entries)
8. **Check for ID collisions:** Glob `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/*/bridge_*.json` for existing IDs
9. Save to `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/<category>/bridge_<category>_<descriptor>.json`
10. **Update manifest cascade:**
    - Update topic/category manifest: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json`
    - Update master-index: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json`

### Quality Criteria

Each entry must satisfy:
- [ ] At least 2 parameters with ranges and defaults
- [ ] "why" explanation of at least 20 words
- [ ] At least 2 anti-patterns
- [ ] At least 1 combination reference
- [ ] Confidence score 0.70-0.90
- [ ] No ID collision with existing entries

### Manifest Cascade

After batch of entries (recommended: 5-10 per batch):

```bash
# 1. Update bridge manifest
# Edit: $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json
# Add entry to appropriate category's entries array

# 2. Update master-index
# Edit: $HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json
# Increment bridge entry_count

# 3. Verify via kb-route lookup
# Read kb-route skill and query for a newly created entry
```

---

## Phase 2: Technical KB Population

### Workflow Strategy

Since kb-harvest and kb-validate skills do not exist, Phase 2 uses manual creation with kb-route validation.

| Entry Type | Method | Workflow |
|------------|--------|----------|
| DSP fundamentals | Manual | Create from JUCE docs, DSP literature |
| JUCE APIs | Manual | Extract from JUCE documentation |
| Synthesis techniques | Manual | Curate from synthesis references |
| Implementation patterns | Manual | Curated from verified code patterns |

### 15 Curated Technical Entries (Manual)

1. `filter_design` — LPF/HPF/BPF types, resonance behavior, cutoff modulation
2. `envelope_design` — ADSR curves, stage transitions, curve shapes
3. `oscillator_design` — Waveforms, anti-aliasing, interpolation methods
4. `gain_staging` — dB relationships, headroom management, clipping prevention
5. `modulation_routing` — LFO targets, modulation depth, rate ranges
6. `time_stretching` — Phase vocoder, granular methods, quality tradeoffs
7. `reverb_design` — Early reflections, decay tail, room modeling
8. `distortion_types` — Saturation curves, waveshaping functions, bitcrush
9. `chorus_flanger` — Delay modulation, feedback, rate/depth interaction
10. `compressor_design` — Attack/release timing, ratio, knee characteristics
11. `eq_design` — Shelf types, peak filters, notch applications
12. `delay_design` — Tap patterns, feedback routing, sync methods
13. `stereo_processing` — Width control, mid/side, imaging
14. `preset_architecture` — State management, XML/value tree, preset format
15. `parameter_smoothing` — SmoothedValue usage, ramp times, artifact prevention

### 10 Migrated Entries from juce-agent-prototype KB

Pull existing entries from `/home/myuser/agents/juce-agent/playbookdata/` with:
- Provenance preserved (note original source)
- Reformat to new schema if needed
- Cross-reference to bridge entries where applicable
- **Verify path exists before migration:** `ls /home/myuser/agents/juce-agent/playbookdata/`

### Technical Entry Schema

```json
{
  "id": "vst_technical_filter-design",
  "kb": "technical",
  "topic": "dsp-algorithms",
  "status": "curated",
  "version": "1.0.0",
  "title": "Filter Design",
  "summary": "Low-pass, high-pass, and band-pass filter implementations with resonance control",
  "description": "Full description text...",
  "source": { "type": "documentation", "reference": "JUCE DSP module", "url": "https://docs.juce.com/master/classdsp_1_1Filter.html" },
  "concepts": [
    { "name": "Cutoff frequency", "description": "Frequency at which filter begins attenuating" },
    { "name": "Resonance", "description": "Emphasis at cutoff frequency" }
  ],
  "tags": ["filter", "dsp", "low-pass", "high-pass", "resonance"],
  "related_topics": ["envelope_design", "modulation_routing"],
  "cross_references": [
    { "kb": "bridge", "entry_id": "bridge_timbre_warm", "relationship": "implements" }
  ],
  "domain_relevance": 9,
  "difficulty": "intermediate"
}
```

### Entry Creation Process

1. Create entry file: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/technical/<topic>/<entry_id>.json`
2. **Check for ID collisions:** Glob `$HOME/playbooks/vst-product-lifecycle-playbook/kb/technical/*/*.json`
3. Populate content from source material
4. Set status: "curated"
5. Add cross-references to bridge entries
6. **Update manifest cascade:**
   - Update topic manifest
   - Update layer manifest
   - Update master-index

### Validation

Since kb-validate doesn't exist, validate manually:

```bash
# Verify entry is readable via kb-route
# Read kb-route skill and query for the concept

# Check JSON validity
cat <entry_file> | python3 -m json.tool > /dev/null && echo "Valid JSON"
```

---

## Phase 3: Registry Updates

### Registry Modification

Update `$HOME/.claude/kb-registry.json`:

```json
{
  "name": "vst-product-lifecycle",
  "path": "/home/myuser/playbooks/vst-product-lifecycle-playbook/kb",
  "layers": ["technical", "sound-design", "ui-ux", "commercial", "reference", "bridge"],
  "bridge_eligible_layers": ["sound-design", "technical"],
  "default_backend": "ddg+webfetch"
}
```

**Note:** `bridge_eligible_layers` already includes "sound-design" in the current registry. This update adds "technical" to enable bridge → technical translations.

### Cross-Layer Mappings

**Already exists in master-index.json:**
```json
{
  "cross_layer_mappings": [
    { "from": "bridge", "to": "sound-design", "relationship": "translates" },
    { "from": "bridge", "to": "technical", "relationship": "translates" }
  ]
}
```

No update needed — mappings are already in place.

### Entry Count Summary

- **Before Phase 1:** 5 bridge entries (verified on disk)
- **After Phase 1:** 76 bridge entries (71 new + 5 existing)
- **Distribution:** ~15 per category

### Combination Handling

Bridge compositions use existing `combinations[]` array in each entry. No new files needed.

The kb-route Resolution Procedure handles composition logic:
1. Read each bridge entry separately
2. Check `combinations[]` for compatibility
3. Apply confidence modifiers
4. Merge parameter lists or use default 0.8 multiplier for unknown combinations

---

## Phase 4: Consumption Skill Updates

### Scope

- **Updated:** juce-sound-design-bridge, juce-dsp-implementation, juce-ui-bridge, juce-plugin-spec
- **Unchanged:** juce-daw-testing (human-only testing phase)

### Interface Preservation

- Skill invocation syntax unchanged
- Output format unchanged
- Internal behavior gains KB-backed intelligence + fallback

### juce-sound-design-bridge Update

**Current behavior:** Hardcoded translation table with 5 entries (warm, bright, punchy, fat, movement)

**Updated behavior:**

```markdown
1. Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
   with parameters: bridge_descriptor="<user_input>", kb="vst-product-lifecycle"

2. If kb-route returns results with confidence >= 0.60:
   - Use parameters from bridge entry
   - Apply anti_patterns warnings to output
   - Note source: "KB: bridge/<category>/<descriptor>"

3. If confidence 0.40-0.59:
   - Use with warning: "Medium confidence (X.XX) — verify before applying"

4. If no results or confidence < 0.40:
   - Fall back to built-in translation table (existing logic)
   - Note: "Using fallback translation (no KB entry found)"

5. Present translation with source attribution and confidence
```

**Fallback table preserved (from existing skill):**
```json
{
  "warm": {"filter_cutoff": [0.2, 0.4], "filter_resonance": [0.1, 0.2]},
  "bright": {"filter_cutoff": [0.6, 1.0]},
  "punchy": {"amp_attack": [0.0, 0.01], "filter_env_amount": [0.3, 0.7]},
  "fat": {"osc_detune": [0.05, 0.15], "stereo_width": [0.6, 0.9], "saturation": [0.2, 0.4]},
  "movement": {"lfo_rate": [0.1, 2.0], "lfo_depth": [0.3, 0.7], "filter_env_amount": [0.2, 0.5]}
}
```

### juce-dsp-implementation Update

**Current behavior:** Minimal KB integration

**Updated behavior:**

```markdown
Pre-flight Check (existing):
  - Plugin spec exists?
  - Build passes?

NEW Step: KB Technical Lookup
  - Read kb-route with parameters: concept="<dsp_topic>", kb="vst-product-lifecycle"
  - If results with confidence >= 0.60: validate against existing code patterns
  - If no results: proceed with built-in DSP knowledge
```

### juce-ui-bridge Update

**Current behavior:** Direct playbook path references

**Updated behavior:**

```markdown
1. Read kb-route with parameters: concept="UI pattern <type>", kb="vst-product-lifecycle"

2. If results:
   - Apply UI patterns from technical layer
   - Cross-reference with sound-design bridge for cohesive design

3. If no results:
   - Fall back to existing playbook path references
```

### juce-plugin-spec Update

**Current behavior:** Built-in fallback translations

**Updated behavior:**

```markdown
Concept Lookup:
  - Read kb-route with parameters: concept="<user_concept>", kb="vst-product-lifecycle"
  - If results: incorporate technical context into spec
  - If no results: use built-in fallback translations (existing)
```

### Verification: Test Scripts

Create test script verifying kb-route integration:

```bash
#!/bin/bash
# File: $HOME/.claude/skills/juce-sound-design-bridge/test-kb-route-integration.sh
# Purpose: Verify kb-route integration in juce-sound-design-bridge

set -e

echo "=== KB-Route Integration Test ==="

# Test 1: Known descriptor returns KB result
echo "Test 1: Known descriptor (warm)..."
# This test verifies kb-route can find bridge_timbre_warm entry
# Expected: Returns parameter mappings with confidence >= 0.60
# Run: Read kb-route skill with bridge_descriptor="warm"

# Test 2: Unknown descriptor falls back to built-in table
echo "Test 2: Unknown descriptor fallback..."
# This test verifies fallback when descriptor not in KB
# Expected: Uses fallback table and notes "Using fallback translation"
# Run: Read kb-route skill with bridge_descriptor="unknown_descriptor_xyz"

# Test 3: Medium confidence entry returns warning
echo "Test 3: Medium confidence warning..."
# This test verifies warning for confidence 0.40-0.59
# Expected: Warning message "Medium confidence - verify before applying"
# Run: Read kb-route skill with bridge_descriptor having confidence 0.50

echo "=== Tests Complete ==="
```

---

## Phase 5: New Consumption Skills

### juce-preset-methodology

**Purpose:** Apply preset design methodology from KB

**Skill definition:**

```markdown
---
name: juce-preset-methodology
description: Apply preset design methodology from KB
---

1. Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
   with parameters: concept="preset methodology", kb="vst-product-lifecycle"

2. If results found with confidence >= 0.60:
   - Extract methodology steps from entry
   - Present to user: "Found preset methodology with confidence X.XX"

3. If confidence 0.40-0.59:
   - Present with warning: "Medium confidence - verify before applying"

4. If no results:
   - Fall back to GROUND_TRUTH_PRESETS.md patterns at:
     $HOME/agents/juce-agent/validation-logs/GROUND_TRUTH_PRESETS.md

5. Apply methodology:
   - User provides sound goal
   - Generate parameter starting points
   - Cross-reference with bridge entries for descriptor alignment
```

### juce-testing-methodology

**Purpose:** Query testing best practices from KB

**Skill definition:**

```markdown
---
name: juce-testing-methodology
description: Query testing best practices from KB
---

1. Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
   with parameters: concept="testing methodology", kb="vst-product-lifecycle"

2. If results found:
   - Extract testing procedures
   - Present checklist for DAW testing phase

3. If no results:
   - Fall back to built-in testing principles:
     - Audio thread safety verification
     - Parameter smoothing validation
     - Preset load/save roundtrip
     - Real-time performance check

4. Generate testing checklist for user review
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Bridge entries too subjective | Manual curation + confidence scoring + fallback tables |
| Technical entries low quality | Manual creation from verified sources + cross-reference validation |
| Skills break existing behavior | Interface preservation + fallback retention + test scripts |
| kb-route queries return nothing | Fallback logic preserved in all skills |
| kb-harvest/kb-validate missing | Manual creation workflow with JSON validation |

---

## Prerequisites Verification

Before starting implementation, verify:

```bash
# 1. kb-route skill exists
ls -la $HOME/.claude/skills/kb-route/SKILL.md

# 2. vst-product-lifecycle KB exists
ls -la $HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json

# 3. KB registry configured
cat $HOME/.claude/kb-registry.json | grep "vst-product-lifecycle"

# 4. Existing skills to update
ls -la $HOME/.claude/skills/juce-sound-design-bridge/SKILL.md
ls -la $HOME/.claude/skills/juce-dsp-implementation/SKILL.md
ls -la $HOME/.claude/skills/juce-ui-bridge/SKILL.md
ls -la $HOME/.claude/skills/juce-plugin-spec/SKILL.md
```

---

## Success Criteria

- [ ] 76 bridge entries exist (71 new + 5 existing) with confidence ≥ 0.70
- [ ] 25 technical entries exist with status "curated"
- [ ] Registry updated with bridge_eligible_layers including "technical"
- [ ] 4 consumption skills updated with kb-route integration
- [ ] 2 new consumption skills created
- [ ] Test scripts pass verification
- [ ] Manifest cascade verified for all new entries

---

## Appendix A: Manifest Structure

**Bridge manifest.json structure:**
```json
{
  "kb_name": "bridge",
  "version": "1.0.0",
  "last_updated": "2026-04-07T...",
  "categories": [
    {
      "name": "timbre",
      "entry_count": 15,
      "entries": [
        {"id": "bridge_timbre_warm", "status": "curated", "file": "timbre/bridge_timbre_warm.json"}
      ]
    }
  ],
  "status_counts": {
    "placeholder": 0,
    "harvested": 0,
    "curated": 15,
    "synced": 0
  }
}
```

**Technical manifest.json structure:**
```json
{
  "kb_name": "technical",
  "version": "1.0.0",
  "topics": [
    {
      "name": "dsp-algorithms",
      "entry_count": 5,
      "entries": [
        {"id": "vst_technical_filter-design", "status": "curated"}
      ]
    }
  ],
  "status_counts": {...}
}
```

---

## Appendix B: Skill Update Method

Each consumption skill update follows this process:

1. **Read existing skill file:**
   ```bash
   cat $HOME/.claude/skills/juce-sound-design-bridge/SKILL.md
   ```

2. **Identify insertion point:**
   - For juce-sound-design-bridge: Insert after "Step 3: Query Sound Design KB"
   - For juce-dsp-implementation: Insert after "Pre-flight Check"
   - For juce-ui-bridge: Insert at start of procedure
   - For juce-plugin-spec: Insert in "Concept Lookup" section

3. **Add kb-route integration:**
   - Add the kb-route invocation block
   - Add confidence handling logic
   - Preserve existing fallback logic

4. **Verify syntax:**
   - Ensure YAML frontmatter intact
   - Check markdown formatting