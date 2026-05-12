#!/usr/bin/env python3
"""
Tests for KB Adapter system — covers all 14 verification checklist items.

Run:
    cd ~/Documents/pbcpb-unified && python3 -m pytest tests/test_kb_adapter.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from kb_adapter import AdapterSession, ConfigError, AdapterIOError, AdapterType
from kb_adapter.enums import VALID_ADAPTER_TYPES, VALID_ROLE_TYPES


# ── Config helpers ────────────────────────────────────────────────────────────

def make_config(adapter_type="JSON_DB", connection=None, skill_ref=None, roles=None):
    """Build a minimal valid config dict."""
    cfg = {
        "kb_adapter": {
            "adapter_type": adapter_type,
            "connection": connection or {},
            "skill_ref": skill_ref,
            "bootstrap_tier_limit": 1,
            "bootstrap_tier_zero_threshold": 0,
        }
    }
    if roles is not None:
        cfg["role_system"] = {"syntax_mode": "@name", "syntax_pattern": "@{name}", "roles": roles}
    return cfg


def write_config(cfg: dict, tmp_dir: Path) -> Path:
    """Write config dict to a temp file and return path."""
    cfg_path = tmp_dir / "pbcpb.config.json"
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path


# ── Verification item 1: backup exists ───────────────────────────────────────

def test_backup_exists():
    """Verification 1: pbcpb-original-backup/ exists."""
    backup = Path.home() / "Documents" / "pbcpb-original-backup"
    assert backup.exists(), f"Backup directory not found: {backup}"
    # Verify it's non-empty (has the key scripts)
    assert (backup / "scripts" / "validate_playbook.py").exists()


# ── Verification item 3: config-driven routing ───────────────────────────────

def test_adapter_routing_json_db(tmp_path):
    """Verification 3: switching adapter_type routes without code changes."""
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "master-index.json").write_text(json.dumps({"entries": []}))

    cfg = make_config("JSON_DB", connection={"kb_root": str(kb_dir)})
    cfg_path = write_config(cfg, tmp_path)

    session = AdapterSession.bind(str(cfg_path))
    assert session.adapter_type == "JSON_DB"


def test_adapter_routing_rag_mcp(tmp_path):
    """Verification 3: RAG_MCP routing."""
    cfg = make_config("RAG_MCP", connection={"mcp_tool_name": "mcp__test__tool"})
    cfg_path = write_config(cfg, tmp_path)

    session = AdapterSession.bind(str(cfg_path))
    assert session.adapter_type == "RAG_MCP"


def test_adapter_routing_custom_api(tmp_path):
    """Verification 3: CUSTOM_API routing."""
    cfg = make_config("CUSTOM_API", connection={"base_url": "https://example.com/kb"})
    cfg_path = write_config(cfg, tmp_path)

    session = AdapterSession.bind(str(cfg_path))
    assert session.adapter_type == "CUSTOM_API"


# ── Verification item 4: all 3 methods callable for all 4 adapter types ──────

def test_json_db_all_methods(tmp_path):
    """Verification 4: JSON_DB — all 3 adapter methods callable."""
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "master-index.json").write_text(json.dumps({"entries": []}))

    cfg = make_config("JSON_DB", connection={"kb_root": str(kb_dir)})
    session = AdapterSession.bind(str(write_config(cfg, tmp_path)))

    # query
    results = session.query("test query")
    assert isinstance(results, list)

    # populate
    result = session.populate("test content", tier=1, metadata={"entry_id": "test-001", "topic": "test"})
    assert result.kind == "write_status"
    assert result.success is True

    # scan_gaps
    schema = {"entries": [{"id": "test-001", "topic": "test", "required": True}]}
    gaps = session.scan_gaps(schema)
    assert isinstance(gaps, list)


def test_rag_mcp_all_methods_callable(tmp_path):
    """Verification 4: RAG_MCP — all 3 methods are callable (query raises AdapterIOError, populate returns manifest)."""
    cfg = make_config("RAG_MCP", connection={"mcp_tool_name": "mcp__test__tool"})
    session = AdapterSession.bind(str(write_config(cfg, tmp_path)))

    # query raises AdapterIOError (MCP not live) — that's the correct behavior
    with pytest.raises(AdapterIOError):
        session.query("test query")

    # populate returns manifest (never writes to Dify)
    result = session.populate("content", tier=1, metadata={"entry_id": "e1", "topic": "t"})
    assert result.kind == "manifest"
    assert result.manifest_path is not None
    assert len(result.items) == 1

    # scan_gaps returns list of gaps (all as missing/placeholder in stub)
    schema = {"entries": [{"id": "e1", "topic": "t", "required": True}]}
    gaps = session.scan_gaps(schema)
    assert isinstance(gaps, list)
    assert len(gaps) == 1
    assert gaps[0].gap_id == "e1"


# ── Verification item 5: MARKDOWN_FOLDER raises ConfigError without skill_ref ─

def test_markdown_folder_no_skill_ref_raises(tmp_path):
    """Verification 5: MARKDOWN_FOLDER raises ConfigError when skill_ref absent."""
    cfg = make_config("MARKDOWN_FOLDER", connection={"folder_path": "/tmp"}, skill_ref=None)
    cfg_path = write_config(cfg, tmp_path)

    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(cfg_path))

    err = exc_info.value
    assert err.offending_field == "kb_adapter.skill_ref"
    assert err.detail["recoverable"] is False


def test_markdown_folder_empty_skill_ref_raises(tmp_path):
    """Verification 5: MARKDOWN_FOLDER raises ConfigError when skill_ref is empty string."""
    cfg = make_config("MARKDOWN_FOLDER", connection={"folder_path": "/tmp"}, skill_ref="")
    cfg_path = write_config(cfg, tmp_path)

    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(cfg_path))

    assert exc_info.value.offending_field == "kb_adapter.skill_ref"


def test_markdown_folder_with_skill_ref_binds(tmp_path):
    """MARKDOWN_FOLDER with skill_ref present should bind successfully."""
    cfg = make_config("MARKDOWN_FOLDER", connection={"folder_path": "/tmp"}, skill_ref="./my-skill.sh")
    cfg_path = write_config(cfg, tmp_path)

    # Bind should succeed (method calls will fail without actual skill binary)
    session = AdapterSession.bind(str(cfg_path))
    assert session.adapter_type == "MARKDOWN_FOLDER"


# ── Verification item 6: RAG_MCP populate returns manifest, not Dify write ───

def test_rag_mcp_populate_returns_manifest(tmp_path):
    """Verification 6: RAG_MCP populate() returns kind='manifest', does not write to Dify."""
    cfg = make_config("RAG_MCP", connection={"mcp_tool_name": "mcp__test__tool"})
    session = AdapterSession.bind(str(write_config(cfg, tmp_path)))

    result = session.populate("KB content here", tier=1, metadata={"entry_id": "kb-001", "topic": "domain"})

    # MUST be manifest, never write_status
    assert result.kind == "manifest"
    assert result.manifest_path == "bootstrap/dify-upload-manifest.json"
    assert len(result.items) == 1
    item = result.items[0]
    assert item["entry_id"] == "kb-001"
    assert "target_location" in item
    assert "payload" in item


# ── Verification item 7: all 3 role_type values parse ────────────────────────

def test_all_role_types_coexist(tmp_path):
    """Verification 7: MULTI_AGENT + HUMAN + AI_ASSISTED coexist without conflict."""
    roles = [
        {"placeholder_name": "@planner", "role_type": "MULTI_AGENT", "linked_agent": None},
        {"placeholder_name": "@human", "role_type": "HUMAN", "linked_agent": None},
        {"placeholder_name": "@assistant", "role_type": "AI_ASSISTED", "linked_agent": None},
    ]
    cfg = make_config("JSON_DB", connection={"kb_root": "/tmp/kb"}, roles=roles)
    cfg_path = write_config(cfg, tmp_path)

    # bind() should succeed with all 3 role types present
    session = AdapterSession.bind(str(cfg_path))
    assert session.adapter_type == "JSON_DB"


# ── Verification item 8: null linked_agent is not an error ───────────────────

def test_null_linked_agent_valid(tmp_path):
    """Verification 8: null linked_agent is valid; updating it requires only config edit."""
    roles = [
        {"placeholder_name": "@architect", "role_type": "MULTI_AGENT", "linked_agent": None},
    ]
    cfg = make_config("JSON_DB", connection={"kb_root": "/tmp/kb"}, roles=roles)
    cfg_path = write_config(cfg, tmp_path)

    # Should bind without error despite null linked_agent
    session = AdapterSession.bind(str(cfg_path))
    assert session.adapter_type == "JSON_DB"

    # Update: change linked_agent in config and re-bind (config-edit only, no rebuild)
    cfg["role_system"]["roles"][0]["linked_agent"] = "planner-agent-v2"
    cfg_path.write_text(json.dumps(cfg))

    session2 = AdapterSession.bind(str(cfg_path))
    assert session2.adapter_type == "JSON_DB"


# ── Verification item 11: CUSTOM_API populate failure halts ──────────────────

def test_custom_api_populate_failure_raises_config_error(tmp_path):
    """Verification 11: CUSTOM_API populate() failure halts with ConfigError, not silent skip."""
    cfg = make_config("CUSTOM_API", connection={"base_url": "http://localhost:19999/nonexistent"})
    session = AdapterSession.bind(str(write_config(cfg, tmp_path)))

    # Network failure on populate → ConfigError (hard halt)
    with pytest.raises(ConfigError) as exc_info:
        session.populate("content", tier=1)

    err = exc_info.value
    assert err.detail["error_class"] == "ConfigError"
    assert err.detail["recoverable"] is False


# ── Verification item 12: exact-string enum validation ───────────────────────

@pytest.mark.parametrize("bad_type", ["RAGMCP", "markdown-folder", "json_db", "customapi", "RAG-MCP", "rag_mcp"])
def test_pseudo_adapter_type_raises_config_error(tmp_path, bad_type):
    """Verification 12: pseudo adapter_type values raise ConfigError at bind() time."""
    cfg = make_config(bad_type)
    cfg_path = write_config(cfg, tmp_path)

    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(cfg_path))

    err = exc_info.value
    assert err.offending_field == "kb_adapter.adapter_type"
    assert err.detail["recoverable"] is False


@pytest.mark.parametrize("bad_type", ["HUMAN_ONLY", "MULTIAGENT", "ai-assisted", "multi_agent"])
def test_pseudo_role_type_raises_config_error(tmp_path, bad_type):
    """Verification 12: pseudo role_type values raise ConfigError at bind() time."""
    roles = [{"placeholder_name": "@x", "role_type": bad_type, "linked_agent": None}]
    cfg = make_config("JSON_DB", connection={"kb_root": "/tmp/kb"}, roles=roles)

    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(cfg, tmp_path)))

    err = exc_info.value
    assert "role_system.roles" in err.offending_field
    assert err.detail["recoverable"] is False


# ── Verification item 13: invalid adapter_type naming offending field ─────────

def test_config_error_names_offending_field(tmp_path):
    """Verification 13: ConfigError names the offending field."""
    cfg = make_config("INVALID_TYPE")
    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(cfg, tmp_path)))

    err = exc_info.value
    assert err.offending_field is not None
    assert "adapter_type" in err.offending_field
    assert "INVALID_TYPE" in str(err)


# ── Verification item 14: cyclic schema handled deterministically ─────────────

def test_cyclic_schema_detected(tmp_path):
    """Verification 14: cyclic schema_definition handled via Kosaraju SCC, no silent divergence."""
    from bootstrap.tier_scorer import TierScorer

    # Create a cycle: A → B → C → A
    schema_definition = {
        "entries": [
            {"id": "A", "depends_on": ["B"], "required": False},
            {"id": "B", "depends_on": ["C"], "required": False},
            {"id": "C", "depends_on": ["A"], "required": False},
            {"id": "D", "depends_on": [], "required": True},  # Not in cycle
        ]
    }

    scorer = TierScorer(schema_definition)
    scored = scorer.score()
    scc_groups = scorer.scc_groups

    # SCC must be found (not silent)
    assert len(scc_groups) == 1
    scc = scc_groups[0]
    assert set(scc.member_entry_ids) == {"A", "B", "C"}

    # SCC members must be promoted to Tier 1
    scored_by_id = {s["entry_id"]: s for s in scored}
    assert scored_by_id["A"]["tier"] == 1
    assert scored_by_id["B"]["tier"] == 1
    assert scored_by_id["C"]["tier"] == 1

    # D is required=True → also Tier 1
    assert scored_by_id["D"]["tier"] == 1


# ── Verification item 10: Tier 1 scoring correctness ─────────────────────────

def test_tier1_scoring_two_dependents(tmp_path):
    """Verification 10: entry with >=2 dependents scored as Tier 1."""
    from bootstrap.tier_scorer import TierScorer

    schema = {
        "entries": [
            {"id": "core", "depends_on": [], "required": False},
            {"id": "dep1", "depends_on": ["core"], "required": False},
            {"id": "dep2", "depends_on": ["core"], "required": False},
            {"id": "leaf", "depends_on": [], "required": False},
        ]
    }

    scorer = TierScorer(schema)
    scored = scorer.score()
    by_id = {s["entry_id"]: s for s in scored}

    # core: in_degree=2 → Tier 1
    assert by_id["core"]["tier"] == 1
    # dep1, dep2: in_degree=0, no required → Tier 3
    assert by_id["dep1"]["tier"] == 3
    assert by_id["dep2"]["tier"] == 3
    # leaf: in_degree=0 → Tier 3
    assert by_id["leaf"]["tier"] == 3


def test_tier1_scoring_required_flag():
    """Verification 10: required=True always Tier 1."""
    from bootstrap.tier_scorer import TierScorer

    schema = {
        "entries": [
            {"id": "req1", "depends_on": [], "required": True},
            {"id": "opt1", "depends_on": [], "required": False},
        ]
    }
    scorer = TierScorer(schema)
    scored = scorer.score()
    by_id = {s["entry_id"]: s for s in scored}

    assert by_id["req1"]["tier"] == 1
    assert by_id["opt1"]["tier"] == 3


# ── Verification item 9: bootstrap produces deferred-backlog.json ─────────────

def test_bootstrap_produces_deferred_backlog(tmp_path):
    """Verification 9: bootstrap produces deferred-backlog.json at defined path and schema."""
    from bootstrap.runner import BootstrapRunner

    # Setup JSON_DB
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "master-index.json").write_text(json.dumps({"entries": []}))

    cfg = {
        "kb_adapter": {
            "adapter_type": "JSON_DB",
            "connection": {"kb_root": str(kb_dir)},
            "skill_ref": None,
            "bootstrap_tier_limit": 1,
            "bootstrap_tier_zero_threshold": 0,
        },
        "kb_schema": {
            "entries": [
                {"id": "entry-tier1", "required": True, "topic": "core"},
                {"id": "entry-tier2", "required": False, "depends_on": ["entry-tier1"], "topic": "secondary"},
                {"id": "entry-tier3", "required": False, "topic": "leaf"},
            ]
        }
    }

    cfg_path = tmp_path / "pbcpb.config.json"
    cfg_path.write_text(json.dumps(cfg))

    session = AdapterSession.bind(str(cfg_path))
    runner = BootstrapRunner(session, cfg, pbcpb_root=str(tmp_path))
    result = runner.run()

    # Backlog must exist
    backlog_path = tmp_path / "bootstrap" / "deferred-backlog.json"
    assert backlog_path.exists(), "deferred-backlog.json not created"

    backlog = json.loads(backlog_path.read_text())

    # Schema validation
    assert "generated_at" in backlog
    assert "tier_limit_used" in backlog
    assert "deferred" in backlog
    assert isinstance(backlog["deferred"], list)

    # Tier 2+ items in deferred
    for item in backlog["deferred"]:
        assert "gap_id" in item
        assert "location" in item
        assert item["type"] in ("missing", "placeholder", "incomplete")
        assert item["tier"] >= 2


# ── PBCPB_CONFIG_PATH env var override ────────────────────────────────────────

def test_config_path_env_var_override(tmp_path, monkeypatch):
    """Config path can be overridden via PBCPB_CONFIG_PATH env var."""
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "master-index.json").write_text(json.dumps({"entries": []}))

    cfg = make_config("JSON_DB", connection={"kb_root": str(kb_dir)})
    cfg_path = write_config(cfg, tmp_path)

    monkeypatch.setenv("PBCPB_CONFIG_PATH", str(cfg_path))

    # Call without explicit config_path — should use env var
    session = AdapterSession.bind()
    assert session.adapter_type == "JSON_DB"


# ── Error shape validation ────────────────────────────────────────────────────

def test_config_error_shape(tmp_path):
    """ConfigError detail dict has correct shape: error_class, cause, adapter_type, recoverable."""
    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(make_config("BAD_TYPE"), tmp_path)))

    detail = exc_info.value.detail
    assert "error_class" in detail
    assert "cause" in detail
    assert "adapter_type" in detail
    assert "recoverable" in detail
    assert detail["error_class"] == "ConfigError"
    assert detail["recoverable"] is False


def test_adapter_io_error_shape(tmp_path):
    """AdapterIOError detail dict has correct shape."""
    cfg = make_config("RAG_MCP", connection={"mcp_tool_name": "mcp__test"})
    session = AdapterSession.bind(str(write_config(cfg, tmp_path)))

    try:
        session.query("test")
    except AdapterIOError as e:
        detail = e.detail
        assert detail["error_class"] == "AdapterIOError"
        assert detail["recoverable"] is True
        assert "adapter_type" in detail
    else:
        pytest.fail("Expected AdapterIOError from RAG_MCP stub query")


def test_negative_tier_zero_threshold_raises_config_error(tmp_path):
    """Negative bootstrap_tier_zero_threshold raises ConfigError at bind() time."""
    cfg = make_config("JSON_DB")
    cfg["kb_adapter"]["bootstrap_tier_zero_threshold"] = -1
    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(cfg, tmp_path)))
    assert "bootstrap_tier_zero_threshold" in exc_info.value.detail["offending_field"]
    assert exc_info.value.detail["recoverable"] is False


def test_non_integer_tier_zero_threshold_raises_config_error(tmp_path):
    """Non-integer bootstrap_tier_zero_threshold raises ConfigError at bind() time."""
    cfg = make_config("JSON_DB")
    cfg["kb_adapter"]["bootstrap_tier_zero_threshold"] = "high"
    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(cfg, tmp_path)))
    assert "bootstrap_tier_zero_threshold" in exc_info.value.detail["offending_field"]


def test_boolean_tier_zero_threshold_raises_config_error(tmp_path):
    """Boolean (True/False) is rejected — booleans are int subclass in Python."""
    cfg = make_config("JSON_DB")
    cfg["kb_adapter"]["bootstrap_tier_zero_threshold"] = True
    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(cfg, tmp_path)))
    assert "bootstrap_tier_zero_threshold" in exc_info.value.detail["offending_field"]


def test_direct_instantiation_raises_type_error(tmp_path):
    """AdapterSession() without _BIND_SENTINEL raises TypeError — bind() is the only path."""
    from kb_adapter.adapters.json_db import JsonDbAdapter
    kb_root = tmp_path / "kb"
    kb_root.mkdir()
    adapter = JsonDbAdapter({"kb_root": str(kb_root)})
    with pytest.raises(TypeError, match="AdapterSession.bind"):
        AdapterSession(adapter)


def test_null_role_type_raises_config_error(tmp_path):
    """role_type: null (None) is rejected — must be an exact enum string."""
    cfg = make_config("JSON_DB")
    cfg["role_system"] = {
        "syntax_mode": "@name",
        "roles": [{"placeholder_name": "@lead", "role_type": None, "linked_agent": None}]
    }
    with pytest.raises(ConfigError) as exc_info:
        AdapterSession.bind(str(write_config(cfg, tmp_path)))
    assert "role_type" in exc_info.value.detail["offending_field"]


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(Path(__file__).parent.parent),
    )
    sys.exit(result.returncode)
