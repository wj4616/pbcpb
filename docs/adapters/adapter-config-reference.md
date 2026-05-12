# KB Adapter Config Reference

## Config File

Default: `pbcpb.config.json` in the pbcpb root directory.
Override: set `PBCPB_CONFIG_PATH` environment variable.

## kb_adapter Schema

```json
{
  "kb_adapter": {
    "adapter_type": "JSON_DB",
    "connection": { "...adapter-specific..." },
    "skill_ref": null,
    "bootstrap_tier_limit": 1,
    "bootstrap_tier_zero_threshold": 0
  }
}
```

### adapter_type (required)

Must be one of these exact strings (case-sensitive):
- `RAG_MCP`
- `MARKDOWN_FOLDER`
- `JSON_DB`
- `CUSTOM_API`

Any other value (RAGMCP, markdown-folder, json_db, etc.) raises ConfigError at bind()
naming the offending field `kb_adapter.adapter_type`.

### connection (required)

Adapter-specific. See per-adapter sections below.

### skill_ref (required for MARKDOWN_FOLDER, ignored for others)

Path or name of the delegating skill. Missing or empty raises ConfigError for
MARKDOWN_FOLDER adapter.

### bootstrap_tier_limit (default: 1)

Tier ceiling for populate_core step. Only entries at or below this tier are populated
during bootstrap. Default 1 = only Tier 1 (core-necessary) entries.

### bootstrap_tier_zero_threshold (default: 0)

in_degree threshold for Tier 0 promotion. Default 0 = Tier 0 disabled.
Set > 0 to opt entries with high in-degree into Tier 0 (highest priority).

---

## JSON_DB Adapter

For the original pbcpb local JSON knowledge base.

```json
{
  "kb_adapter": {
    "adapter_type": "JSON_DB",
    "connection": {
      "kb_root": "./kb",
      "default_layer": "general",
      "timeout": 60
    }
  }
}
```

| Field | Required | Default | Description |
|---|---|---|---|
| kb_root | Yes | — | Path to KB root directory |
| default_layer | No | "general" | Layer for writes without explicit layer |
| timeout | No | 60 | Filesystem operation timeout (seconds) |

**populate()** returns `kind="write_status"`.

---

## RAG_MCP Adapter

For Dify RAG accessed via MCP server.

```json
{
  "kb_adapter": {
    "adapter_type": "RAG_MCP",
    "connection": {
      "mcp_tool_name": "mcp__dify-cognitive-kb__cognitive-research-kb-dify",
      "dataset_name": "my-kb",
      "timeout": 60
    }
  }
}
```

| Field | Required | Default | Description |
|---|---|---|---|
| mcp_tool_name | Yes | — | MCP tool identifier |
| dataset_name | No | "pbcpb-kb" | Dify dataset name (used in manifest paths) |
| timeout | No | 60 | MCP call timeout (seconds) |

**populate()** returns `kind="manifest"` — NEVER writes to Dify directly.
See `rag-mcp-guide.md` for Dify upload procedure.

---

## MARKDOWN_FOLDER Adapter

Delegates all 3 methods to a user-provided skill.

```json
{
  "kb_adapter": {
    "adapter_type": "MARKDOWN_FOLDER",
    "skill_ref": "./skills/my-kb-skill.sh",
    "connection": {
      "folder_path": "./kb-markdown",
      "timeout": 60
    }
  }
}
```

| Field | Required | Default | Description |
|---|---|---|---|
| skill_ref | Yes (top-level) | — | Skill path/name. Missing = ConfigError |
| folder_path | No | "." | Markdown folder path (passed to skill) |
| timeout | No | 60 | Skill subprocess timeout (seconds) |

**Skill protocol:**
```
<skill_ref> query     --input '{"query_string": "...", "filters": {}, "folder_path": "..."}'
<skill_ref> populate  --input '{"content": "...", "tier": 1, "metadata": {}, "folder_path": "..."}'
<skill_ref> scan_gaps --input '{"schema_definition": {...}, "folder_path": "..."}'
```
Expected stdout: JSON. Non-zero exit → AdapterIOError.

---

## CUSTOM_API Adapter

Configurable HTTP passthrough to any external KB API.

```json
{
  "kb_adapter": {
    "adapter_type": "CUSTOM_API",
    "connection": {
      "base_url": "https://api.example.com/kb",
      "query_path": "/query",
      "populate_path": "/populate",
      "scan_gaps_path": "/scan_gaps",
      "api_key": "sk-...",
      "api_key_header": "X-API-Key",
      "method": "POST",
      "timeout": 60
    }
  }
}
```

| Field | Required | Default | Description |
|---|---|---|---|
| base_url | Yes | — | API base URL |
| query_path | No | "/query" | Query endpoint path |
| populate_path | No | "/populate" | Populate endpoint path |
| scan_gaps_path | No | "/scan_gaps" | Scan gaps endpoint path |
| api_key | No | null | API key value |
| api_key_header | No | "X-API-Key" | Header name for API key |
| method | No | "POST" | HTTP method for query |
| timeout | No | 60 | Per-request timeout (seconds) |

**CRITICAL:** populate() failure (non-2xx or network error) raises ConfigError
(recoverable: False) — HARD HALT. Fix API connectivity before using populate().
This is intentional — silent population failures corrupt KB state.
