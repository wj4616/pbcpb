# KB-Route Consumption Skills Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update consumption skills to use kb-route Resolution Procedure, expand bridge layer to 76 entries, populate technical layer, add 2 new skills.

**Architecture:** KB-first approach — populate bridge and technical layers before updating skills. Manual curation for all entries. Interface preservation — skill invocations remain unchanged.

**Tech Stack:** kb-route skill, existing JUCE consumption skills, JSON entry files

---

## Task 1: Prerequisites Verification

**Files:**
- Verify: `$HOME/.claude/skills/kb-route/SKILL.md`
- Verify: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json`
- Verify: `$HOME/.claude/kb-registry.json`

- [ ] **Step 1: Verify kb-route skill exists**

Run: `ls -la $HOME/.claude/skills/kb-route/SKILL.md`
Expected: File exists

- [ ] **Step 2: Verify vst-product-lifecycle KB exists**

Run: `ls -la $HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json`
Expected: File exists

- [ ] **Step 3: Verify KB registry configured**

Run: `cat $HOME/.claude/kb-registry.json | grep "vst-product-lifecycle"`
Expected: Output contains "vst-product-lifecycle"

- [ ] **Step 4: Verify existing skills to update**

Run: `ls -la $HOME/.claude/skills/juce-sound-design-bridge/SKILL.md $HOME/.claude/skills/juce-dsp-implementation/SKILL.md $HOME/.claude/skills/juce-ui-bridge/SKILL.md $HOME/.claude/skills/juce-plugin-spec/SKILL.md`
Expected: All 4 files exist

---

## Task 2: Sync Existing Bridge Manifest

**Files:**
- Modify: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json`

- [ ] **Step 1: Read current manifest**

Run: `cat $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json`
Expected: JSON with empty entry arrays

- [ ] **Step 2: Update manifest with existing entries**

Edit the manifest to include the 5 existing bridge entries:

```json
{
  "kb_name": "bridge",
  "version": "1.0.0",
  "last_updated": "2026-04-07T00:00:00Z",
  "categories": [
    {
      "name": "timbre",
      "entry_count": 1,
      "entries": [
        {"id": "bridge_timbre_warm", "status": "curated", "file": "timbre/bridge_timbre_warm.json"}
      ]
    },
    {
      "name": "dynamics",
      "entry_count": 1,
      "entries": [
        {"id": "bridge_dynamics_punchy", "status": "curated", "file": "dynamics/bridge_dynamics_punchy.json"}
      ]
    },
    {
      "name": "space",
      "entry_count": 1,
      "entries": [
        {"id": "bridge_space_wide", "status": "curated", "file": "space/bridge_space_wide.json"}
      ]
    },
    {
      "name": "movement",
      "entry_count": 1,
      "entries": [
        {"id": "bridge_movement_evolving", "status": "curated", "file": "movement/bridge_movement_evolving.json"}
      ]
    },
    {
      "name": "character",
      "entry_count": 1,
      "entries": [
        {"id": "bridge_character_analog", "status": "curated", "file": "character/bridge_character_analog.json"}
      ]
    }
  ],
  "status_counts": {
    "placeholder": 0,
    "harvested": 0,
    "curated": 5,
    "synced": 0
  },
  "sync_history": []
}
```

- [ ] **Step 3: Verify JSON validity**

Run: `python3 -m json.tool $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json > /dev/null && echo "Valid JSON"`
Expected: "Valid JSON"

- [ ] **Step 4: Commit manifest sync**

```bash
git add $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json
git commit -m "chore: sync bridge manifest with existing entries"
```

---

## Task 3: Create Bridge Entry - timbre/bright

**Files:**
- Create: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/timbre/bridge_timbre_bright.json`

- [ ] **Step 1: Create bridge_timbre_bright.json**

```json
{
  "id": "bridge_timbre_bright",
  "category": "timbre",
  "descriptor": "bright",
  "parameters": [
    {
      "parameter": "filter_cutoff",
      "value_range": [0.6, 1.0],
      "typical_default": 0.8,
      "unit": "normalized",
      "notes": "High-pass or bright EQ to emphasize high frequencies"
    },
    {
      "parameter": "filter_resonance",
      "value_range": [0.05, 0.2],
      "typical_default": 0.1,
      "unit": "normalized",
      "notes": "Subtle resonance adds sparkle without harshness"
    },
    {
      "parameter": "osc_detune",
      "value_range": [0.0, 0.05],
      "typical_default": 0.0,
      "unit": "normalized",
      "notes": "Minimal detune keeps brightness focused"
    }
  ],
  "confidence": 0.85,
  "source": {
    "type": "expert-knowledge",
    "reference": "Sound on Sound: Equalization Fundamentals"
  },
  "why": "Bright timbre is achieved by emphasizing high frequencies (2-8kHz range). High-pass filtering or boost EQ, combined with low resonance, creates clarity and presence without harshness.",
  "anti_patterns": [
    {
      "mistake": "Excessive resonance",
      "reason": "High resonance at high cutoff creates piercing, painful tones"
    },
    {
      "mistake": "No filter at all",
      "reason": "Without filtering, low frequencies mask brightness"
    }
  ],
  "combinations": [],
  "examples": [
    {
      "context": "Lead sound",
      "parameter_values": {
        "filter_cutoff": 0.85,
        "filter_resonance": 0.1
      },
      "result": "Bright lead that cuts through mix"
    }
  ],
  "created": "2026-04-07T00:00:00Z"
}
```

- [ ] **Step 2: Verify JSON validity**

Run: `python3 -m json.tool $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/timbre/bridge_timbre_bright.json > /dev/null && echo "Valid"`
Expected: "Valid"

---

## Task 4: Create Bridge Entry - timbre/dark

**Files:**
- Create: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/timbre/bridge_timbre_dark.json`

- [ ] **Step 1: Create bridge_timbre_dark.json**

```json
{
  "id": "bridge_timbre_dark",
  "category": "timbre",
  "descriptor": "dark",
  "parameters": [
    {
      "parameter": "filter_cutoff",
      "value_range": [0.1, 0.3],
      "typical_default": 0.2,
      "unit": "normalized",
      "notes": "Low-pass filter at low cutoff removes high frequencies"
    },
    {
      "parameter": "filter_resonance",
      "value_range": [0.05, 0.15],
      "typical_default": 0.1,
      "unit": "normalized",
      "notes": "Low resonance avoids emphasis at cutoff"
    }
  ],
  "confidence": 0.80,
  "source": {
    "type": "expert-knowledge",
    "reference": "Sound design fundamentals"
  },
  "why": "Dark timbre is the opposite of bright - achieved by attenuating high frequencies below 1kHz. The result is a mellow, bass-heavy tone suitable for atmospheric sounds.",
  "anti_patterns": [
    {
      "mistake": "Adding bass boost",
      "reason": "Excessive low frequencies cause muddiness, not darkness"
    },
    {
      "mistake": "High resonance",
      "reason": "Resonance at low cutoff creates unwanted emphasis"
    }
  ],
  "combinations": [],
  "created": "2026-04-07T00:00:00Z"
}
```

- [ ] **Step 2: Verify JSON validity**

Run: `python3 -m json.tool $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/timbre/bridge_timbre_dark.json > /dev/null && echo "Valid"`
Expected: "Valid"

---

## Task 5: Create Bridge Entry - timbre/harsh

**Files:**
- Create: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/timbre/bridge_timbre_harsh.json`

- [ ] **Step 1: Create bridge_timbre_harsh.json**

```json
{
  "id": "bridge_timbre_harsh",
  "category": "timbre",
  "descriptor": "harsh",
  "parameters": [
    {
      "parameter": "filter_cutoff",
      "value_range": [0.8, 1.0],
      "typical_default": 0.95,
      "unit": "normalized",
      "notes": "Maximum high frequency content"
    },
    {
      "parameter": "filter_resonance",
      "value_range": [0.4, 0.8],
      "typical_default": 0.6,
      "unit": "normalized",
      "notes": "High resonance creates aggressive tone"
    },
    {
      "parameter": "distortion_amount",
      "value_range": [0.4, 0.8],
      "typical_default": 0.6,
      "unit": "normalized",
      "notes": "Distortion adds harmonics and grit"
    }
  ],
  "confidence": 0.75,
  "source": {
    "type": "expert-knowledge",
    "reference": "Industrial sound design techniques"
  },
  "why": "Harsh timbre is achieved through combination of high frequencies, aggressive resonance, and distortion. The result is intentionally abrasive and edgy.",
  "anti_patterns": [
    {
      "mistake": "Low filter cutoff",
      "reason": "Reduces high frequencies, making sound less harsh"
    },
    {
      "mistake": "No resonance",
      "reason": "Flat high frequencies are bright, not harsh"
    }
  ],
  "combinations": [],
  "created": "2026-04-07T00:00:00Z"
}
```

- [ ] **Step 2: Verify JSON validity**

Run: `python3 -m json.tool $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/timbre/bridge_timbre_harsh.json > /dev/null && echo "Valid"`
Expected: "Valid"

---

## Tasks 6-17: Remaining timbre entries (soft, nasal, plucky, metallic, glassy, wooden, breathy, buzzy, clean, distorted, thin)

**Pattern:** Same structure as Tasks 3-5. Create entry file, verify JSON.

- [ ] **Step 1:** Create bridge_timbre_soft.json
- [ ] **Step 2:** Verify JSON
- [ ] **Step 3:** Create bridge_timbre_nasal.json
- [ ] **Step 4:** Verify JSON
- [ ] **Step 5:** Create bridge_timbre_plucky.json
- [ ] **Step 6:** Verify JSON
- [ ] **Step 7:** Create bridge_timbre_metallic.json
- [ ] **Step 8:** Verify JSON
- [ ] **Step 9:** Create bridge_timbre_glassy.json
- [ ] **Step 10:** Verify JSON
- [ ] **Step 11:** Create bridge_timbre_wooden.json
- [ ] **Step 12:** Verify JSON
- [ ] **Step 13:** Create bridge_timbre_breathy.json
- [ ] **Step 14:** Verify JSON
- [ ] **Step 15:** Create bridge_timbre_buzzy.json
- [ ] **Step 16:** Verify JSON
- [ ] **Step 17:** Create bridge_timbre_clean.json
- [ ] **Step 18:** Verify JSON
- [ ] **Step 19:** Create bridge_timbre_distorted.json
- [ ] **Step 20:** Verify JSON
- [ ] **Step 21:** Create bridge_timbre_thin.json
- [ ] **Step 22:** Verify JSON

---

## Task 18: Create Bridge Entry - dynamics/soft (first dynamics entry)

**Files:**
- Create: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/dynamics/bridge_dynamics_soft.json`

- [ ] **Step 1: Create bridge_dynamics_soft.json**

```json
{
  "id": "bridge_dynamics_soft",
  "category": "dynamics",
  "descriptor": "soft",
  "parameters": [
    {
      "parameter": "amp_attack",
      "value_range": [0.1, 0.5],
      "typical_default": 0.3,
      "unit": "seconds",
      "notes": "Slow attack creates gentle onset"
    },
    {
      "parameter": "amp_release",
      "value_range": [0.3, 1.0],
      "typical_default": 0.5,
      "unit": "seconds",
      "notes": "Medium to long release for smooth fade"
    },
    {
      "parameter": "filter_env_amount",
      "value_range": [0.0, 0.2],
      "typical_default": 0.1,
      "unit": "normalized",
      "notes": "Minimal filter envelope for subtle movement"
    }
  ],
  "confidence": 0.85,
  "source": {
    "type": "expert-knowledge",
    "reference": "Synthesis envelope design"
  },
  "why": "Soft dynamics are achieved through slow attacks, gentle releases, and minimal filter modulation. The result is a gentle, non-aggressive sound.",
  "anti_patterns": [
    {
      "mistake": "Fast attack",
      "reason": "Creates percussive, not soft, onset"
    },
    {
      "mistake": "High filter envelope",
      "reason": "Creates aggressive brightness sweep"
    }
  ],
  "combinations": [],
  "created": "2026-04-07T00:00:00Z"
}
```

- [ ] **Step 2: Verify JSON validity**

---

## Tasks 19-31: Remaining dynamics entries (aggressive, gentle, sharp, round, bouncy, flat, compressed, open, tight, loose, explosive, sustain, pluck)

**Pattern:** Same structure. Create entry file, verify JSON.

---

## Tasks 32-46: space entries (intimate, cavernous, narrow, deep, shallow, distant, close, airy, dense, hollow, solid, ethereal, present, expansive, spacious)

**Pattern:** Same structure. Create entry file, verify JSON.

---

## Tasks 47-60: movement entries (static, rhythmic, flowing, choppy, smooth, erratic, predictable, pulsing, swelling, fading, building, cycling, random, lfo)

**Note:** "evolving" already exists.

**Pattern:** Same structure. Create entry file, verify JSON.

---

## Tasks 61-74: character entries (digital, lo-fi, hi-fi, vintage, modern, natural, synthetic, organic, mechanical, electric, acoustic, warm-digital, cold, hybrid)

**Note:** "analog" already exists.

**Pattern:** Same structure. Create entry file, verify JSON.

---

## Task 75: Update Bridge Manifest with All New Entries

**Files:**
- Modify: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json`

- [ ] **Step 1: Read current manifest**

Run: `cat $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json`

- [ ] **Step 2: Update manifest with all new entries**

Update each category's entries array to include all new entries. Entry count should be 15 per category.

- [ ] **Step 3: Update status_counts**

```json
"status_counts": {
  "placeholder": 0,
  "harvested": 0,
  "curated": 76,
  "synced": 0
}
```

- [ ] **Step 4: Verify JSON validity**

- [ ] **Step 5: Commit bridge manifest update**

```bash
git add $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/manifest.json
git commit -m "feat: add 71 new bridge entries to manifest"
```

---

## Task 76: Update Master Index

**Files:**
- Modify: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json`

- [ ] **Step 1: Update bridge entry count in master-index**

Change `"entry_count": 5` to `"entry_count": 76` for the bridge layer.

- [ ] **Step 2: Update placeholder_entries count**

- [ ] **Step 3: Commit master-index update**

```bash
git add $HOME/playbooks/vst-product-lifecycle-playbook/kb/master-index.json
git commit -m "feat: update master-index for 76 bridge entries"
```

---

## Task 77: Add Combinations to Bridge Entries

**Files:**
- Modify: All bridge entry files

- [ ] **Step 1: Add combinations to timbre entries**

For each timbre entry, add compatible combinations referencing other categories.

- [ ] **Step 2: Add combinations to dynamics entries**

- [ ] **Step 3: Add combinations to space entries**

- [ ] **Step 4: Add combinations to movement entries**

- [ ] **Step 5: Add combinations to character entries**

- [ ] **Step 6: Commit combinations update**

```bash
git add $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/
git commit -m "feat: add combination references to bridge entries"
```

---

## Task 78: Create Technical Entry - filter_design

**Files:**
- Create: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/technical/dsp-algorithms/vst_technical_filter-design.json`

- [ ] **Step 1: Create vst_technical_filter-design.json**

```json
{
  "id": "vst_technical_filter-design",
  "kb": "technical",
  "topic": "dsp-algorithms",
  "status": "curated",
  "version": "1.0.0",
  "title": "Filter Design",
  "summary": "Low-pass, high-pass, and band-pass filter implementations with resonance control",
  "description": "Digital filter design for audio applications. Covers IIR and FIR approaches, biquad implementations, coefficient calculation, and resonance behavior.",
  "source": {
    "type": "documentation",
    "reference": "JUCE DSP module",
    "url": "https://docs.juce.com/master/classdsp_1_1Filter.html"
  },
  "concepts": [
    {"name": "Cutoff frequency", "description": "Frequency at which filter begins attenuating"},
    {"name": "Resonance", "description": "Emphasis at cutoff frequency"},
    {"name": "Filter slope", "description": "Attenuation per octave (12dB, 24dB, etc.)"}
  ],
  "tags": ["filter", "dsp", "low-pass", "high-pass", "resonance", "biquad"],
  "related_topics": ["envelope_design", "modulation_routing"],
  "cross_references": [
    {"kb": "bridge", "entry_id": "bridge_timbre_warm", "relationship": "implements"},
    {"kb": "bridge", "entry_id": "bridge_timbre_bright", "relationship": "implements"}
  ],
  "domain_relevance": 9,
  "difficulty": "intermediate",
  "created": "2026-04-07T00:00:00Z"
}
```

- [ ] **Step 2: Verify JSON validity**

---

## Tasks 79-92: Remaining technical entries

**Pattern:** Same structure. Create entry file, verify JSON, update topic manifest.

Entries: envelope_design, oscillator_design, gain_staging, modulation_routing, time_stretching, reverb_design, distortion_types, chorus_flanger, compressor_design, eq_design, delay_design, stereo_processing, preset_architecture, parameter_smoothing

---

## Task 93: Update Technical Manifest

**Files:**
- Modify: `$HOME/playbooks/vst-product-lifecycle-playbook/kb/technical/manifest.json`

- [ ] **Step 1: Update manifest with all new technical entries**

- [ ] **Step 2: Update status_counts**

- [ ] **Step 3: Commit technical manifest**

---

## Task 94: Update Registry

**Files:**
- Modify: `$HOME/.claude/kb-registry.json`

- [ ] **Step 1: Add technical to bridge_eligible_layers**

```json
{
  "name": "vst-product-lifecycle",
  "path": "/home/myuser/playbooks/vst-product-lifecycle-playbook/kb",
  "layers": ["technical", "sound-design", "ui-ux", "commercial", "reference", "bridge"],
  "bridge_eligible_layers": ["sound-design", "technical"],
  "default_backend": "ddg+webfetch"
}
```

- [ ] **Step 2: Commit registry update**

```bash
git add $HOME/.claude/kb-registry.json
git commit -m "feat: add technical to bridge_eligible_layers"
```

---

## Task 95: Update juce-sound-design-bridge Skill

**Files:**
- Modify: `$HOME/.claude/skills/juce-sound-design-bridge/SKILL.md`

- [ ] **Step 1: Read current skill file**

Run: `cat $HOME/.claude/skills/juce-sound-design-bridge/SKILL.md | head -100`

- [ ] **Step 2: Find insertion point after "Step 3: Query Sound Design KB"**

- [ ] **Step 3: Add kb-route integration block**

Add after the existing KB lookup section:

```markdown
### Step 3b: KB-Route Integration

Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: bridge_descriptor="<user_input>", kb="vst-product-lifecycle"

If kb-route returns results with confidence >= 0.60:
  - Use parameters from bridge entry
  - Apply anti_patterns warnings to output
  - Note source: "KB: bridge/<category>/<descriptor>"

If confidence 0.40-0.59:
  - Use with warning: "Medium confidence (X.XX) — verify before applying"

If no results or confidence < 0.40:
  - Fall back to built-in translation table (existing logic)
  - Note: "Using fallback translation (no KB entry found)"
```

- [ ] **Step 4: Verify YAML frontmatter intact**

- [ ] **Step 5: Commit skill update**

```bash
git add $HOME/.claude/skills/juce-sound-design-bridge/SKILL.md
git commit -m "feat: add kb-route integration to juce-sound-design-bridge"
```

---

## Task 96: Update juce-dsp-implementation Skill

**Files:**
- Modify: `$HOME/.claude/skills/juce-dsp-implementation/SKILL.md`

- [ ] **Step 1: Read current skill file**

- [ ] **Step 2: Find insertion point after "Pre-flight Check"**

- [ ] **Step 3: Add KB Technical Lookup block**

```markdown
### KB Technical Lookup

Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: concept="<dsp_topic>", kb="vst-product-lifecycle"

If results with confidence >= 0.60:
  - Extract technical guidance from entry
  - Validate against existing code patterns

If no results:
  - Proceed with built-in DSP knowledge
```

- [ ] **Step 4: Commit skill update**

---

## Task 97: Update juce-ui-bridge Skill

**Files:**
- Modify: `$HOME/.claude/skills/juce-ui-bridge/SKILL.md`

- [ ] **Step 1: Read current skill file**

- [ ] **Step 2: Add kb-route integration at start of procedure**

```markdown
### KB UI Pattern Lookup

Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: concept="UI pattern <type>", kb="vst-product-lifecycle"

If results:
  - Apply UI patterns from technical layer
  - Cross-reference with sound-design bridge for cohesive design

If no results:
  - Fall back to existing playbook path references
```

- [ ] **Step 3: Commit skill update**

---

## Task 98: Update juce-plugin-spec Skill

**Files:**
- Modify: `$HOME/.claude/skills/juce-plugin-spec/SKILL.md`

- [ ] **Step 1: Read current skill file**

- [ ] **Step 2: Find "Concept Lookup" section**

- [ ] **Step 3: Add kb-route integration**

```markdown
### Concept Lookup via KB-Route

Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: concept="<user_concept>", kb="vst-product-lifecycle"

If results:
  - Incorporate technical context into spec
If no results:
  - Use built-in fallback translations (existing)
```

- [ ] **Step 4: Commit skill update**

---

## Task 99: Create juce-preset-methodology Skill

**Files:**
- Create: `$HOME/.claude/skills/juce-preset-methodology/SKILL.md`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p $HOME/.claude/skills/juce-preset-methodology
```

- [ ] **Step 2: Create SKILL.md**

```markdown
---
name: juce-preset-methodology
description: Apply preset design methodology from KB
---

# JUCE Preset Methodology

Apply preset design methodology from the Knowledge Base to create parameter starting points for sound design goals.

## When to Use

Invoke this skill when:
- User requests preset creation guidance
- User asks "how do I create a X sound?"
- During Phase 9 (DAW testing) for preset refinement

## Process

### Step 1: KB-Route Concept Lookup

Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: concept="preset methodology", kb="vst-product-lifecycle"

### Step 2: Handle Results

If results found with confidence >= 0.60:
  - Extract methodology steps from entry
  - Present to user: "Found preset methodology with confidence X.XX"

If confidence 0.40-0.59:
  - Present with warning: "Medium confidence - verify before applying"

If no results:
  - Fall back to GROUND_TRUTH_PRESETS.md patterns at:
    $HOME/agents/juce-agent/validation-logs/GROUND_TRUTH_PRESETS.md

### Step 3: Apply Methodology

- User provides sound goal
- Generate parameter starting points based on methodology
- Cross-reference with bridge entries for descriptor alignment

### Step 4: Present Results

Output parameter suggestions in a structured format:

```markdown
**Preset Starting Point:** <sound_goal>
**Confidence:** X.XX
**Source:** KB/fallback

**Parameters:**
| Parameter | Value | Range | Why |
|-----------|-------|-------|-----|
| ... | ... | ... | ... |

**Next Steps:**
- Refine during DAW testing
- Log results for validation
```

## Fallback

If KB unavailable, use built-in principles:
- Start with filter cutoff around 0.5 for most sounds
- Use moderate attack/release for pads
- Use fast attack for percussive sounds
```

- [ ] **Step 3: Commit new skill**

```bash
git add $HOME/.claude/skills/juce-preset-methodology/
git commit -m "feat: create juce-preset-methodology skill with kb-route integration"
```

---

## Task 100: Create juce-testing-methodology Skill

**Files:**
- Create: `$HOME/.claude/skills/juce-testing-methodology/SKILL.md`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p $HOME/.claude/skills/juce-testing-methodology
```

- [ ] **Step 2: Create SKILL.md**

```markdown
---
name: juce-testing-methodology
description: Query testing best practices from KB
---

# JUCE Testing Methodology

Query testing best practices from the Knowledge Base for DAW testing phase.

## When to Use

Invoke this skill when:
- Entering Phase 9 (DAW testing)
- User asks about testing procedures
- Debugging audio issues

## Process

### Step 1: KB-Route Concept Lookup

Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: concept="testing methodology", kb="vst-product-lifecycle"

### Step 2: Handle Results

If results found:
  - Extract testing procedures
  - Present checklist for DAW testing phase

If no results:
  - Fall back to built-in testing principles:
    - Audio thread safety verification
    - Parameter smoothing validation
    - Preset load/save roundtrip
    - Real-time performance check

### Step 3: Generate Testing Checklist

Present as:

```markdown
**Testing Checklist:**

- [ ] Audio thread safety: No allocations in processBlock
- [ ] Parameter smoothing: Verify ramp times
- [ ] Preset roundtrip: Save and load correctly
- [ ] Real-time performance: CPU under 5%
- [ ] Edge cases: Parameter at 0, 0.5, 1.0
- [ ] Sample rates: 44.1k, 48k, 96k
```

## Fallback Testing Principles

1. Audio thread safety verification
2. Parameter smoothing validation
3. Preset load/save roundtrip
4. Real-time performance check
```

- [ ] **Step 3: Commit new skill**

```bash
git add $HOME/.claude/skills/juce-testing-methodology/
git commit -m "feat: create juce-testing-methodology skill with kb-route integration"
```

---

## Task 101: Create Test Script for KB-Route Integration

**Files:**
- Create: `$HOME/.claude/skills/juce-sound-design-bridge/test-kb-route-integration.sh`

- [ ] **Step 1: Create test script**

```bash
#!/bin/bash
# Test: KB-Route Integration for juce-sound-design-bridge
# This script verifies kb-route integration works correctly

set -e

echo "=== KB-Route Integration Test ==="

# Test 1: Known descriptor returns KB result
echo "Test 1: Known descriptor (warm)..."
# Expected: Returns parameter mappings with confidence >= 0.60
# This test is manual - verify by reading kb-route with bridge_descriptor="warm"

# Test 2: Unknown descriptor falls back to built-in table
echo "Test 2: Unknown descriptor fallback..."
# Expected: Uses fallback table
# This test is manual - verify fallback is preserved

# Test 3: Medium confidence entry returns warning
echo "Test 3: Medium confidence warning..."
# Expected: Warning message for confidence 0.40-0.59
# This test is manual - verify warning logic exists

echo "=== Tests Complete ==="
echo "NOTE: These are manual verification tests."
echo "Run: Read kb-route skill and query with bridge_descriptor parameter"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x $HOME/.claude/skills/juce-sound-design-bridge/test-kb-route-integration.sh
```

- [ ] **Step 3: Commit test script**

---

## Task 102: Final Verification

- [ ] **Step 1: Verify bridge entry count**

Run: `ls $HOME/playbooks/vst-product-lifecycle-playbook/kb/bridge/*/ | wc -l`
Expected: 76 files

- [ ] **Step 2: Verify technical entry count**

Run: `ls $HOME/playbooks/vst-product-lifecycle-playbook/kb/technical/*/*.json 2>/dev/null | wc -l`
Expected: 25+ files

- [ ] **Step 3: Verify registry has bridge_eligible_layers with technical**

Run: `cat $HOME/.claude/kb-registry.json | grep "bridge_eligible_layers"`
Expected: Contains "technical"

- [ ] **Step 4: Verify 4 skills updated**

Run: `grep -l "kb-route" $HOME/.claude/skills/juce-sound-design-bridge/SKILL.md $HOME/.claude/skills/juce-dsp-implementation/SKILL.md $HOME/.claude/skills/juce-ui-bridge/SKILL.md $HOME/.claude/skills/juce-plugin-spec/SKILL.md | wc -l`
Expected: 4

- [ ] **Step 5: Verify 2 new skills created**

Run: `ls $HOME/.claude/skills/juce-preset-methodology/SKILL.md $HOME/.claude/skills/juce-testing-methodology/SKILL.md 2>/dev/null | wc -l`
Expected: 2

- [ ] **Step 6: Final commit with all changes**

```bash
git add -A
git commit -m "feat: complete KB-route consumption skills integration

- Add 71 new bridge entries across 5 categories
- Add 25 technical entries
- Update registry with bridge_eligible_layers
- Update 4 consumption skills with kb-route integration
- Create 2 new consumption skills (preset-methodology, testing-methodology)
- Add test script for kb-route integration"
```

---

## Success Criteria

- [ ] 76 bridge entries exist (71 new + 5 existing) with confidence >= 0.70
- [ ] 25 technical entries exist with status "curated"
- [ ] Registry updated with bridge_eligible_layers including "technical"
- [ ] 4 consumption skills updated with kb-route integration
- [ ] 2 new consumption skills created
- [ ] Test scripts exist
- [ ] Manifest cascade verified for all new entries