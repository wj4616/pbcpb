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