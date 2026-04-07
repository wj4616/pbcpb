# KB-Route Consumption Skills Integration Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update consumption skills to use kb-route Resolution Procedure, expand bridge layer to 76 entries, populate technical layer, add 2 new skills.

**Architecture:** KB-first approach — populate bridge and technical layers before updating skills. Hybrid harvesting: automated kb-harvest for technical entries, manual curation for subjective bridge entries. Interface preservation — skill invocations remain unchanged, internal behavior enhanced.

**Tech Stack:** kb-route skill, kb-harvest skill, kb-validate skill, existing JUCE consumption skills

---

## Phase Overview

| Phase | Deliverable | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | Bridge Expansion: 75 new bridge entries | 18-25 hrs | None |
| 2 | Technical KB Population: 25 entries | 12-18 hrs | None |
| 3 | New Bridge Directions & Registry Updates | 2-3 hrs | Phase 1, 2 |
| 4 | Consumption Skill Updates: 4 skills | 6-8 hrs | Phase 1, 2, 3 |
| 5 | New Consumption Skills: 2 skills | 3-3 hrs | Phase 4 |

**Total Effort:** 41-57 hours

---

## Phase 1: Bridge Expansion

### Categories & Entry Distribution

| Category | Count | Example Descriptors |
|----------|-------|---------------------|
| timbre | 15 | warm, bright, dark, harsh, soft, nasal, plucky, metallic, glassy, wooden, breathy, buzzy, clean, distorted, thin |
| dynamics | 15 | punchy, soft, aggressive, gentle, sharp, round, bouncy, flat, compressed, open, tight, loose, explosive, sustain, pluck |
| space | 15 | wide, intimate, cavernous, narrow, deep, shallow, distant, close, airy, dense, hollow, solid, ethereal, present, distant |
| movement | 15 | evolving, static, rhythmic, flowing, choppy, smooth, erratic, predictable, pulsing, swelling, fading, building, cycling, random, lfo |
| character | 15 | analog, digital, lo-fi, hi-fi, vintage, modern, natural, synthetic, organic, mechanical, electric, acoustic, warm-digital, cold, hybrid |

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

**Process per entry:**
1. Define descriptor and category
2. Research typical parameter mappings from sound design literature
3. Define parameter ranges with typical defaults
4. Write "why" explanation (psychoacoustic/technical basis)
5. Identify anti-patterns (common mistakes)
6. Define compatible combinations with confidence modifiers
7. Assign initial confidence score (0.70-0.90 for curated entries)
8. Save to `~/playbooks/vst-product-lifecycle-playbook/kb/bridge/<category>/bridge_<category>_<descriptor>.json`

### Quality Criteria

Each entry must satisfy:
- [ ] At least 2 parameters with ranges and defaults
- [ ] "why" explanation of at least 20 words
- [ ] At least 2 anti-patterns
- [ ] At least 1 combination reference
- [ ] Confidence score 0.70-0.90

---

## Phase 2: Technical KB Population

### Hybrid Workflow Strategy

| Entry Type | Method | Workflow |
|------------|--------|----------|
| DSP fundamentals | kb-harvest | Auto-populate from JUCE docs, validate confidence ≥0.60 |
| JUCE APIs | kb-harvest | Auto-populate from JUCE documentation |
| Synthesis techniques | Hybrid | Harvest + manual curation (subjective aspects) |
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

### kb-harvest Commands

```bash
# Auto-populate DSP fundamentals
kb-harvest --kb vst-product-lifecycle --layer technical --auto \
  --backend ddg+webfetch --min-confidence 0.40

# Validate after harvest
kb-validate --auto --kb vst-product-lifecycle --layer technical

# Flag entries needing curation (confidence < 0.60)
kb-sync --verify --kb vst-product-lifecycle
```

### Technical Entry Schema

```json
{
  "id": "vst_technical_filter-design",
  "kb": "vst-product-lifecycle",
  "topic": "dsp-fundamentals",
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

---

## Phase 3: New Bridge Directions & Registry Updates

### Registry Modification

Update `~/.claude/kb-registry.json`:

```json
{
  "name": "vst-product-lifecycle",
  "bridge_eligible_layers": ["sound-design", "technical"],
  ...
}
```

### Cross-Layer Mappings

Add to `~/playbooks/vst-product-lifecycle-playbook/kb/master-index.json`:

```json
{
  "cross_layer_mappings": [
    { "from": "bridge", "to": "sound-design", "relationship": "translates" },
    { "from": "bridge", "to": "technical", "relationship": "translates" }
  ]
}
```

### Entry Count Summary

- **Before Phase 1:** 1 bridge entry (`bridge_timbre_warm`)
- **After Phase 1:** 76 bridge entries (75 new + 1 existing)
- **Distribution:** 15 per category × 5 categories + 1 existing = 76

### Combination Handling

Bridge compositions use existing `combinations[]` array in each entry. No new files needed.

The kb-route Resolution Procedure handles composition logic:
1. Read each bridge entry separately
2. Check `combinations[]` for compatibility
3. Apply confidence modifiers
4. Merge parameter lists or use default 0.8 multiplier for unknown combinations

### UI-UX Layer

Deferred to future work. Not blocking bridge functionality.

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

**Current behavior:** Hardcoded translation table

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

**Fallback table preserved:**
```json
{
  "warm": {"filter_cutoff": [0.2, 0.4], "filter_resonance": [0.1, 0.2]},
  "bright": {"filter_cutoff": [0.6, 1.0]},
  "punchy": {"amp_attack": [0.0, 0.01], "filter_env_amount": [0.3, 0.7]}
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
# ~/.claude/skills/juce-sound-design-bridge/test-kb-route-integration.sh

# Test 1: Known descriptor returns KB result
# Test 2: Unknown descriptor falls back to built-in table
# Test 3: Medium confidence entry returns warning
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
   - Fall back to GROUND_TRUTH_PRESETS.md patterns

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
| Technical entries low quality | kb-harvest confidence thresholds + manual review pass |
| Skills break existing behavior | Interface preservation + fallback retention + test scripts |
| kb-route queries return nothing | Fallback logic preserved in all skills |

---

## Success Criteria

- [ ] 76 bridge entries exist with confidence ≥ 0.70
- [ ] 25 technical entries exist with confidence ≥ 0.60
- [ ] Registry updated with bridge_eligible_layers
- [ ] 4 consumption skills updated with kb-route integration
- [ ] 2 new consumption skills created
- [ ] All test scripts pass