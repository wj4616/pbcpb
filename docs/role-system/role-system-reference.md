# Role System Reference

## Overview

The PBCPB role system abstracts how tasks are assigned and executed across different
deployment models (multi-agent, human-only, AI-assisted, or mixed).

Placeholders (like @architect) are defined at design-time in the config.
linked_agent values are bound at runtime — config edit only, no rebuild required.

## role_system Config Block

```json
{
  "role_system": {
    "syntax_mode": "@name",
    "syntax_pattern": "@{name}",
    "roles": [
      {
        "placeholder_name": "@architect",
        "role_type": "MULTI_AGENT",
        "linked_agent": null
      }
    ]
  }
}
```

### syntax_mode

`@name` (default) — placeholders use @name format (e.g., @architect, @reviewer)
`custom` — use syntax_pattern to define custom format

### syntax_pattern

Used when syntax_mode == "custom". Example: `{name}`, `[role:name]`.

### roles array

Each role object:

| Field | Required | Description |
|---|---|---|
| placeholder_name | Yes | Design-time identifier (e.g., "@architect") |
| role_type | Yes | Exact string: "MULTI_AGENT", "HUMAN", or "AI_ASSISTED" |
| linked_agent | No | Runtime agent binding (string or null) |

null linked_agent is ALWAYS valid — means human executes manually.

## role_type Values

All three exact strings coexist without conflict in the same config block.

| role_type | Meaning | linked_agent |
|---|---|---|
| `MULTI_AGENT` | Executed by an AI agent swarm | Required for automated execution; null = unbound |
| `HUMAN` | Human executes manually | Always optional; null = expected |
| `AI_ASSISTED` | Human+AI collaboration | Optional; null = human-only mode |

Pseudo-values like HUMAN_ONLY, MULTIAGENT, ai-assisted raise ConfigError at bind()
naming the offending field role_system.roles[N].role_type.

## Three Validated Config Variants

### (a) Multi-agent

```json
{
  "role_system": {
    "roles": [
      { "placeholder_name": "@planner",  "role_type": "MULTI_AGENT", "linked_agent": "planner-v1" },
      { "placeholder_name": "@executor", "role_type": "MULTI_AGENT", "linked_agent": "executor-v1" },
      { "placeholder_name": "@reviewer", "role_type": "MULTI_AGENT", "linked_agent": null }
    ]
  }
}
```

### (b) Human-only

```json
{
  "role_system": {
    "roles": [
      { "placeholder_name": "@lead",    "role_type": "HUMAN", "linked_agent": null },
      { "placeholder_name": "@analyst", "role_type": "HUMAN", "linked_agent": null },
      { "placeholder_name": "@qa",      "role_type": "HUMAN", "linked_agent": null }
    ]
  }
}
```

### (c) AI-assisted (mixed HUMAN + AI_ASSISTED)

```json
{
  "role_system": {
    "roles": [
      { "placeholder_name": "@human",     "role_type": "HUMAN",      "linked_agent": null },
      { "placeholder_name": "@assistant", "role_type": "AI_ASSISTED", "linked_agent": null }
    ]
  }
}
```

## Updating linked_agent (config-edit only, no rebuild)

To bind or update a linked_agent, edit pbcpb.config.json and re-call bind():

```json
// Before: null linked_agent
{ "placeholder_name": "@planner", "role_type": "MULTI_AGENT", "linked_agent": null }

// After: bind planner-agent-v2
{ "placeholder_name": "@planner", "role_type": "MULTI_AGENT", "linked_agent": "planner-agent-v2" }
```

No code change. No rebuild. Re-run AdapterSession.bind() to pick up the new binding.

## Python Usage

```python
from role_system import RoleSystem
import json

config = json.loads(open("pbcpb.config.json").read())
role_sys = RoleSystem.from_config(config["role_system"])

# Look up a role
role = role_sys.get_role("@architect")
print(role.role_type)          # "MULTI_AGENT"
print(role.linked_agent)       # None (valid — not an error)
print(role.has_agent_binding()) # False
print(role.resolve_executor())  # "[multi-agent] @architect → (unbound — requires linked_agent in config)"

# All roles
for r in role_sys.all_roles():
    print(r.placeholder_name, r.role_type, r.linked_agent)

# Filter by type
human_roles = role_sys.roles_by_type("HUMAN")
ai_roles = role_sys.roles_by_type("MULTI_AGENT")

# Resolve placeholders in text
text = "@architect designs the system, @reviewer checks it"
resolved = role_sys.resolve_placeholder(text)
print(resolved)

# Bind at runtime (equivalent to config edit + re-bind)
role_sys.bind_agent("@architect", "planner-agent-v2")

# Summary
print(role_sys.summary())
```
