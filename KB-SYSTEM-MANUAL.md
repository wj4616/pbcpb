# KB System Manual

Comprehensive operator's guide for the Knowledge Base infrastructure. Covers all KB skills, data structures, and operational procedures.

## System Overview

The KB system stores structured domain knowledge that AI agents query during playbook execution. Knowledge is organized in **layers** (e.g., technical, sound-design, bridge) containing **entries** (JSON files) grouped by **topic**.

### Architecture

```
~/.claude/kb-registry.json          ← Single source of truth for KB discovery
  │
  ├─ KB: juce-agent-prototype       ← Prototype KB (rich data, legacy format)
  │    └─ master-index.json
  │         ├─ dsp-kb/              ← Layer
  │         │    ├─ manifest.json
  │         │    ├─ filters/        ← Topic
  │         │    │    └─ *.json     ← Entries
  │         │    └─ synthesis/
  │         ├─ sound-design-kb/
  │         └─ juce-kb/
  │
  └─ KB: vst-product-lifecycle      ← New KB (current schema, sparse data)
       └─ master-index.json
            ├─ technical/
            ├─ sound-design/
            ├─ bridge/              ← Bridge layer (descriptor → parameters)
            │    ├─ timbre/
            │    │    └─ bridge_timbre_warm.json
            │    └─ dynamics/
            └─ ui-ux/
```

### Component Relationships

```
PBCPB (Playbook Creator Playbook)
  │ generates playbooks that define KB architecture
  ▼
kb-harvest ──── populates entries from web/local sources
  │               writes entries + runs cascade (manifest, master-index, cross-refs)
  ▼
kb-sync ─────── verifies consistency, repairs cascades
  │               populates entry-level cross-references
  │               promotes entry status (curated → synced)
  ▼
kb-validate ─── validates technical claims
  │               assigns confidence scores (5-factor formula)
  ▼
kb-route ────── Resolution Procedure for querying KBs
  │               consumption skills reference this inline
  ▼
Consumption Skills (sound-design-bridge, dsp-implementation, etc.)
  │ query KB via kb-route procedure during playbook execution
  ▼
Agent Output ── code, specs, designs informed by KB knowledge
```

## KB Registry

**Location:** `~/.claude/kb-registry.json`

The registry maps KB names to filesystem paths. Every KB skill reads this first.

**Structure:**
```json
{
  "version": "1.0.0",
  "registries": [
    {
      "name": "juce-agent-prototype",
      "path": "/home/myuser/agents/juce-agent/playbookdata",
      "layers": ["dsp-kb", "sound-design-kb", "juce-kb", ...],
      "bridge_eligible_layers": ["sound-design-kb"],
      "default_backend": "ddg+webfetch"
    }
  ],
  "default_kb": "juce-agent-prototype"
}
```

**Key fields:**
- `name`: Unique identifier for the KB
- `path`: Absolute path to the KB root directory
- `layers[]`: List of layer directory names
- `bridge_eligible_layers[]`: Layers that can participate in bridge translations
- `default_backend`: Default harvest backend for this KB

## Master Index

**Location:** `<kb.path>/master-index.json`

Cross-references entries across all layers. Two formats exist:

**New format (PBCPB-generated):**
```json
{
  "kb_layers": [
    { "name": "technical", "topics": [...], "authority_score": 1.0 }
  ],
  "cross_layer_mappings": [
    { "from": "bridge", "to": "technical", "relationship": "translates" }
  ]
}
```

**Prototype format:**
```json
{
  "knowledge_bases": {
    "dsp-kb": { "path": "dsp-kb", "topics": [...], "file_count": 53 }
  }
}
```

kb-route auto-detects the format at Step 1.

## Entry Lifecycle

Every KB entry progresses through a lifecycle:

```
placeholder → harvested → curated → synced
```

| Status | Meaning | How it gets here | Trust level |
|--------|---------|-----------------|-------------|
| `placeholder` | Empty shell — title and tags only, description starts with "TODO:" | PBCPB Phase 3 bootstrapping | None — triggers harvest or is skipped |
| `harvested` | Content populated from web/local sources | `kb-harvest` fills it | Check confidence score before using |
| `curated` | Human-reviewed and verified | Manual review + edit | High — use normally |
| `synced` | Promoted after passing validation | `kb-sync --promote` | Full trust |

**Entry file structure** (new KB schema):
```json
{
  "id": "vst_sound-design_subtractive",
  "kb": "sound-design",
  "topic": "synthesis-types",
  "status": "harvested",
  "version": "1.0.0",
  "title": "Subtractive Synthesis",
  "summary": "Rich oscillator → filter → amp envelope...",
  "description": "Full description text...",
  "source": { "type": "expert-tutorial", "reference": "...", "url": "..." },
  "concepts": [
    { "name": "Oscillator", "description": "Sound source generating raw waveforms" }
  ],
  "tags": ["synthesis", "subtractive", "analog"],
  "related_topics": ["parameter-mapping", "preset-methodology"],
  "cross_references": [
    { "kb": "technical", "entry_id": "vst_technical_filter-design", "relationship": "implements" }
  ],
  "domain_relevance": 9,
  "difficulty": "beginner"
}
```

**Harvested entries also have:**
```json
{
  "harvest_metadata": {
    "overall_confidence": 0.75,
    "field_provenance": { ... },
    "harvested_at": "2026-04-04T...",
    "backend": "ddg+webfetch"
  }
}
```

## Confidence Scoring

Entries carry confidence scores from two sources:

1. **harvest_metadata.overall_confidence** — assigned by kb-harvest during population, refined by kb-validate's 5-factor formula
2. **Top-level `confidence`** — present on bridge entries (manually assigned)

### Thresholds

| Confidence | Action |
|---|---|
| >= 0.60 | Use normally |
| 0.40 - 0.59 | Use with warning — verify before relying on this |
| < 0.40 | Exclude — too unreliable |
| Absent | Use with note — "No confidence score available" |

### kb-validate 5-Factor Formula

kb-validate scores claims using:
1. **Source authority** — is the source reputable?
2. **Recency** — how old is the information?
3. **Corroboration** — do multiple sources agree?
4. **Specificity** — is it concrete or vague?
5. **Internal consistency** — does it contradict other KB entries?

These factors blend into `harvest_metadata.overall_confidence`.

## Bridge System

Bridges translate between domains — mapping subjective descriptors (e.g., "warm", "punchy") to technical parameters (e.g., `filter_cutoff: [0.2, 0.4]`).

### Bridge Entry Structure

Bridge entries live in `<kb.path>/bridge/<category>/bridge_<category>_<descriptor>.json`:

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
    }
  ],
  "confidence": 0.85,
  "why": "Human-readable rationale for this mapping",
  "anti_patterns": [
    { "mistake": "Heavy saturation", "reason": "Too much saturation creates harshness" }
  ],
  "combinations": [
    {
      "compatible_with": "bridge_character_analog",
      "notes": "Analog character enhances warmth through drift",
      "confidence_modifier": 0.1
    }
  ]
}
```

### Bridge Categories

Categories group related descriptors. Current categories in the new KB:

| Category | Example descriptors |
|----------|-------------------|
| timbre | warm, bright, dark |
| dynamics | punchy, soft, aggressive |
| space | wide, intimate, cavernous |
| movement | evolving, static, rhythmic |
| character | analog, digital, lo-fi |

### Bridge Composition

When a consumption skill needs multiple descriptors (e.g., "warm analog"), kb-route composes them:

1. Read each bridge entry separately
2. Check `combinations[]` for `compatible_with` references
3. **If compatible:** merge parameter lists, apply `confidence_modifier`, intersection of `anti_patterns`
4. **If not listed as compatible:** compose with lowered confidence (multiply each by 0.8), union of `anti_patterns`

### Bridge Manifest

The bridge layer uses `categories` (not `topics`) in its manifest:
```json
{
  "categories": [
    { "name": "timbre", "entry_count": 1, "entries": [...] }
  ]
}
```

### Bridge-Eligible Layers

The registry's `bridge_eligible_layers[]` identifies which layers can participate in bridge translations. The master-index's `cross_layer_mappings` with `"relationship": "translates"` connects bridge layers to their source/target layers.

## KB Skills Reference

### kb-harvest — Populate Entries

Populates KB entries from web sources, local files, or user-provided URLs. Every harvest operation maintains all KB infrastructure (manifests, master-index, cross-references).

**Common commands:**
```
kb-harvest --kb <name>                     # Interactive harvest session
kb-harvest --kb <name> --auto              # Auto-fill all placeholders
kb-harvest --kb <name> --auto --refresh    # Re-harvest below confidence threshold
kb-harvest --kb <name> --auto --entry <id> # Fill specific entry
kb-harvest --kb <name> --urls <url1> ...   # Harvest specific URLs
kb-harvest --kb <name> --layer <layer>     # Target specific layer
kb-harvest --kb <name> --topic <topic>     # Target specific topic
kb-harvest --kb <name> --batch <N>         # Set batch size (default 5)
kb-harvest --kb <name> --import <path>     # Import external KB
kb-harvest --kb <name> --rebuild-manifest  # Reconstruct manifests from files
kb-harvest --status                        # Show harvest status across all KBs
kb-harvest --list                          # List registered KBs
```

**Cascade:** After each batch, kb-harvest automatically updates: manifest → master-index → cross-references → bridge detection → search terms.

### kb-sync — Verify and Repair

Verifies KB consistency, repairs incomplete cascades, populates entry-level cross-references, promotes entry status.

**Common commands:**
```
kb-sync --verify                              # Full consistency check (all KBs)
kb-sync --verify --kb <name>                  # Verify specific KB
kb-sync --repair                              # Fix inconsistencies
kb-sync --repair --kb <name>                  # Repair specific KB
kb-sync --promote --kb <name> --entry <id>    # Promote curated → synced
kb-sync --status                              # Show sync status
```

**Scheduled:** Runs every 30 minutes via cron, checking for cascade journals from recent harvests.

### kb-validate — Validate Claims

Validates technical knowledge claims before implementation. Assigns confidence scores using the 5-factor formula.

**Common commands:**
```
kb-validate --claim "JUCE SmoothedValue uses getNextValue() per sample"
kb-validate --auto --source ${last_skill_output}
kb-validate --gate --check-session
kb-validate --report
```

**Triggers:** Auto-triggers after kb-harvest and firecrawl operations. Also runs as pre-implementation gate.

### kb-route — Query Resolution

Shared Resolution Procedure for querying KBs. Not invoked directly — consumption skills reference it inline.

**How consumption skills use it:**
```
Read and follow the Resolution Procedure in ~/.claude/skills/kb-route/SKILL.md
with parameters: concept="filter resonance"
```

**Steps:** Setup → Concept Lookup → Explore → Cross-Ref Follow → Bridge Resolution → Confidence Filter → Gap Detection → Result Summary

See `~/.claude/skills/kb-route/SKILL.md` for the full procedure.

## How-To Guides

### Add a New KB

1. Create the KB directory structure with layers:
   ```
   mkdir -p /path/to/new-kb/{layer1,layer2}/
   ```
2. Create a `master-index.json` at the KB root (use new format with `kb_layers[]`)
3. Register in `~/.claude/kb-registry.json` — add entry to `registries[]`:
   ```json
   {
     "name": "my-new-kb",
     "path": "/path/to/new-kb",
     "layers": ["layer1", "layer2"],
     "bridge_eligible_layers": [],
     "default_backend": "ddg+webfetch"
   }
   ```
4. Run `kb-sync --verify --kb my-new-kb` to validate structure

### Add a Layer to an Existing KB

1. Create the layer directory: `mkdir -p <kb.path>/new-layer/`
2. Create a manifest.json in the layer directory:
   ```json
   { "kb_name": "new-layer", "version": "1.0.0", "topics": [], "status_counts": {} }
   ```
3. Update `master-index.json` — add layer to `kb_layers[]` (or `knowledge_bases{}` for prototype format)
4. Update `~/.claude/kb-registry.json` — add layer name to the KB's `layers[]`
5. Run `kb-sync --verify --kb <name>` to validate

### Populate Entries

**Fill all placeholders in a KB:**
```
kb-harvest --kb <name> --auto
```

**Fill a specific entry:**
```
kb-harvest --kb <name> --auto --entry <entry-id> --batch 1
```

**Fill a specific topic:**
```
kb-harvest --kb <name> --topic <topic-name>
```

**Import from external source:**
```
kb-harvest --kb <name> --import /path/to/data --dry-run   # Preview first
kb-harvest --kb <name> --import /path/to/data              # Execute
```

### Promote Entry Status

Entries progress: `placeholder` → `harvested` → `curated` → `synced`.

- `placeholder → harvested`: Automatic via kb-harvest
- `harvested → curated`: Manual review — edit the entry file, set `"status": "curated"`
- `curated → synced`: Via kb-sync: `kb-sync --promote --kb <name> --entry <id>`

### Add a Bridge Direction

1. Create bridge entries in `<kb.path>/bridge/<category>/bridge_<category>_<descriptor>.json`
2. Add `cross_layer_mappings` to master-index.json:
   ```json
   { "from": "bridge", "to": "<target-layer>", "relationship": "translates" }
   ```
3. Add the source layer to `bridge_eligible_layers[]` in the registry
4. Run `kb-sync --verify` to validate

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "No KB registry found" | `~/.claude/kb-registry.json` missing | Run `kb-harvest --kb <name>` to create, or create manually |
| "KB [name] registered but master-index.json not found" | Master-index deleted or KB path wrong | Check `path` in registry, run `kb-sync --repair` |
| "KB [name] master-index format not recognized" | Corrupted or incompatible master-index | Regenerate master-index from layer directories |
| Manifest shows 0 entries but files exist on disk | Manifest out of date | Run `kb-sync --repair --kb <name>` or `kb-harvest --kb <name> --rebuild-manifest` |
| "Entry [filename] invalid JSON" | Corrupted entry file | Fix JSON syntax or delete and re-harvest |
| Confidence scores all 0 or missing | Entries not validated after harvest | Run `kb-validate --auto` on harvested entries |
| Cross-references point to missing entries | Entry deleted or renamed | Run `kb-sync --verify` then `kb-sync --repair` |
| Bridge lookup returns nothing | Bridge entries not created for this descriptor | Create bridge entry or run `kb-harvest` targeting bridge layer |
| "Harvest failed for [entry_id]" | Backend unavailable or rate-limited | Retry with different backend: `kb-harvest --kb <name> --backend websearch+webfetch --entry <id>` |