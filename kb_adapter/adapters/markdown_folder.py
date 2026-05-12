"""
MARKDOWN_FOLDER Adapter — delegates all 3 methods to a user-provided skill.

Key behaviors:
    All 3 methods (query, populate, scan_gaps) delegate to the skill_ref.
    If skill_ref is absent or empty, raises ConfigError at bind() time — no fallback.

The skill_ref is a path or name to a skill file/script that implements the
3-method contract. MARKDOWN_FOLDER never directly reads files itself.

CALLER_INVARIANCE: import this only from AdapterSession (session.py).
"""

import subprocess
import json
from pathlib import Path

from ..interface import BaseAdapter, QueryResult, PopulateResult, GapResult
from ..errors import AdapterIOError, ConfigError


class MarkdownFolderAdapter(BaseAdapter):
    """
    KB adapter backed by a markdown folder, delegating to a user-provided skill.

    Connection config fields:
        folder_path  — path to the markdown folder (passed to skill as context)
        timeout      — per-call timeout in seconds (default: 60)

    skill_ref (top-level kb_adapter config field, not in connection):
        Path or name of skill that handles query/populate/scan_gaps.
        REQUIRED — ConfigError raised at bind() if absent.

    Skill invocation protocol:
        The skill is called as a JSON-RPC-style CLI:
            <skill_ref> <method> --input '<json>'

        Expected stdout: JSON matching the method return type.
        Non-zero exit or malformed JSON → AdapterIOError.
    """

    def __init__(self, connection_config: dict, skill_ref: str):
        super().__init__("MARKDOWN_FOLDER", connection_config)
        # skill_ref MUST be present — ConfigError raised at bind() if absent
        # (validated before construction in session.py, but guard here too)
        if not skill_ref:
            raise ConfigError(
                "MARKDOWN_FOLDER adapter requires 'skill_ref' in config. "
                "Set kb_adapter.skill_ref to the path or name of the delegating skill.",
                offending_field="kb_adapter.skill_ref",
                adapter_type="MARKDOWN_FOLDER",
            )
        self._skill_ref = skill_ref
        self._folder_path = connection_config.get("folder_path", ".")
        self._timeout = connection_config.get("timeout", 60)

    def _invoke_skill(self, method: str, input_data: dict) -> dict:
        """
        Invoke the skill via CLI and return parsed JSON output.

        Raises:
            AdapterIOError on timeout, non-zero exit, or JSON parse failure
        """
        skill_path = Path(self._skill_ref)
        if not skill_path.exists():
            # Try as a name in PATH
            cmd = [self._skill_ref, method, "--input", json.dumps(input_data)]
        else:
            cmd = [str(skill_path), method, "--input", json.dumps(input_data)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired:
            raise AdapterIOError(
                f"MARKDOWN_FOLDER skill '{self._skill_ref}' timed out after {self._timeout}s "
                f"for method '{method}'",
                adapter_type="MARKDOWN_FOLDER",
            )
        except FileNotFoundError:
            raise AdapterIOError(
                f"MARKDOWN_FOLDER skill '{self._skill_ref}' not found. "
                "Set kb_adapter.skill_ref to a valid skill path or name.",
                adapter_type="MARKDOWN_FOLDER",
            )

        if result.returncode != 0:
            raise AdapterIOError(
                f"MARKDOWN_FOLDER skill '{self._skill_ref}' returned exit code {result.returncode} "
                f"for method '{method}'. stderr: {result.stderr.strip()[:200]}",
                adapter_type="MARKDOWN_FOLDER",
            )

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise AdapterIOError(
                f"MARKDOWN_FOLDER skill '{self._skill_ref}' returned non-JSON output "
                f"for method '{method}': {str(e)}",
                adapter_type="MARKDOWN_FOLDER",
            )

    def query(self, query_string: str, filters: dict = None) -> list:
        """
        Delegate query to skill_ref.

        Returns:
            list of QueryResult objects

        Raises:
            AdapterIOError: skill invocation failed
        """
        input_data = {
            "query_string": query_string,
            "filters": filters or {},
            "folder_path": self._folder_path,
        }
        raw = self._invoke_skill("query", input_data)
        results = raw.get("results", [])
        return [
            QueryResult(
                entry_id=r.get("entry_id", ""),
                content=r.get("content", ""),
                metadata=r.get("metadata", {}),
                source_adapter="MARKDOWN_FOLDER",
            )
            for r in results
        ]

    def populate(self, content: str, tier: int, metadata: dict = None) -> PopulateResult:
        """
        Delegate populate to skill_ref.

        Returns:
            PopulateResult(kind="write_status") — callers MUST check .kind

        Raises:
            AdapterIOError: skill invocation failed
        """
        input_data = {
            "content": content,
            "tier": tier,
            "metadata": metadata or {},
            "folder_path": self._folder_path,
        }
        raw = self._invoke_skill("populate", input_data)
        return PopulateResult(
            kind="write_status",
            success=raw.get("success", False),
            written_count=raw.get("written_count", 0),
            errors=raw.get("errors", []),
        )

    def scan_gaps(self, schema_definition: dict) -> list:
        """
        Delegate scan_gaps to skill_ref.

        Returns:
            list of GapResult objects

        Raises:
            AdapterIOError: skill invocation failed
        """
        input_data = {
            "schema_definition": schema_definition,
            "folder_path": self._folder_path,
        }
        raw = self._invoke_skill("scan_gaps", input_data)
        gaps_raw = raw.get("gaps", [])
        gaps = []
        for g in gaps_raw:
            try:
                gaps.append(GapResult(
                    gap_id=g["gap_id"],
                    location=g.get("location", ""),
                    gap_type=g.get("type", "missing"),
                    schema_node=g.get("schema_node", {}),
                ))
            except (KeyError, ValueError):
                continue  # Skip malformed gap entries from skill
        return gaps
