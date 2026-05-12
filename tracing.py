"""Langfuse tracing init for PBCPB. Import before any langfuse usage in scripts.

Usage in entry-point scripts:
    import tracing  # noqa: F401 — must be first import before langfuse decorators fire

Root trace usage (coordinator):
    from tracing import RunTrace
    trace = RunTrace.start(run_id="my-run", playbook="my-playbook.json", workspace_dir=".")
    # ... all @observe spans now attach to this root trace ...
    trace.finish(status="success")

Role agent attachment:
    from tracing import RunTrace
    RunTrace.attach(workspace_dir="/path/to/coordinator/workspace")
    # ... all @observe spans in this process now share the root trace_id ...
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_dotenv() -> None:
    """Load .env from project root into os.environ (setdefault — won't overwrite existing vars)."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()

# Import Langfuse AFTER env vars are set — required per SDK docs.
from langfuse import Langfuse as _Langfuse, get_client as _get_client  # noqa: E402

_langfuse = _Langfuse()

# Filename written to the coordinator workspace so role agents can attach.
_RUN_TRACE_FILENAME = "run-trace.json"


class RunTrace:
    """Root trace for a PBCPB run.

    Creates one Langfuse trace that spans the full lifecycle of a playbook run.
    Writes the trace_id to ``<workspace_dir>/run-trace.json`` so that role agents
    running in separate processes can attach their spans to the same root trace.

    Typical coordinator flow::

        trace = RunTrace.start(run_id="2026-...", playbook="my.json", workspace_dir=".")
        # execute phases — each @observe span is a child of this trace
        trace.finish(status="success")

    Typical role agent flow (called once at agent startup)::

        RunTrace.attach(workspace_dir="/home/myuser/.openclaw/workspace-pb-coordinator")

    After ``attach()`` any ``@observe``-decorated function called with
    ``langfuse_trace_id=RunTrace.current_trace_id()`` will appear as a child span
    of the root trace.  Use ``RunTrace.current_trace_id()`` to retrieve the id.
    """

    # Module-level storage so helpers don't need an instance reference.
    _active_trace_id: str | None = None

    def __init__(self, trace_id: str, workspace_dir: Path) -> None:
        self._trace_id = trace_id
        self._workspace_dir = workspace_dir
        RunTrace._active_trace_id = trace_id

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def start(
        cls,
        run_id: str,
        playbook: str,
        workspace_dir: str | Path = ".",
        metadata: dict[str, Any] | None = None,
    ) -> "RunTrace":
        """Create a new root trace for a PBCPB run and persist it to disk.

        Args:
            run_id: Unique identifier for this run (e.g. ISO timestamp string).
            playbook: Playbook filename or path (for display in Langfuse UI).
            workspace_dir: Directory to write ``run-trace.json`` into.
                Use the pb-coordinator workspace so role agents can find it.
            metadata: Optional extra metadata attached to the trace.

        Returns:
            RunTrace instance with ``trace_id`` ready for propagation.
        """
        lf = _get_client()
        trace_id = lf.create_trace_id(seed=run_id)

        # Open the root span so Langfuse registers the trace.
        with lf.start_as_current_observation(
            trace_context={"trace_id": trace_id},
            name="pbcpb-run",
            as_type="agent",
            input={
                "run_id": run_id,
                "playbook": playbook,
                **(metadata or {}),
            },
        ):
            pass  # The span will be updated via finish() below.

        workspace_path = Path(workspace_dir)
        workspace_path.mkdir(parents=True, exist_ok=True)

        run_trace_file = workspace_path / _RUN_TRACE_FILENAME
        run_trace_file.write_text(
            json.dumps(
                {
                    "trace_id": trace_id,
                    "run_id": run_id,
                    "playbook": playbook,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "status": "running",
                },
                indent=2,
            )
        )

        instance = cls(trace_id=trace_id, workspace_dir=workspace_path)
        return instance

    @classmethod
    def attach(cls, workspace_dir: str | Path) -> str | None:
        """Attach this process to an existing root trace from a coordinator workspace.

        Looks for ``trace_id`` in (in priority order):
        1. ``run-trace.json`` — written by :meth:`start`
        2. ``executor-state.json`` — written by the pb-coordinator agent; the
           coordinator should include a ``"trace_id"`` key when it starts a run.

        Sets the module-level trace_id so that subsequent calls to
        :meth:`current_trace_id` return it.  Callers pass that value as
        ``langfuse_trace_id=RunTrace.current_trace_id()`` when calling any
        ``@observe``-decorated function that should appear under the shared root
        trace.

        Args:
            workspace_dir: Path to the coordinator's workspace directory.

        Returns:
            The trace_id string, or None if no trace_id was found in either file.
        """
        workspace_path = Path(workspace_dir)

        # 1. Primary: run-trace.json
        run_trace_file = workspace_path / _RUN_TRACE_FILENAME
        if run_trace_file.exists():
            try:
                data = json.loads(run_trace_file.read_text())
                trace_id = data.get("trace_id")
                if trace_id:
                    cls._active_trace_id = trace_id
                    return trace_id
            except (json.JSONDecodeError, OSError):
                pass

        # 2. Fallback: executor-state.json (coordinator writes trace_id here)
        executor_state_file = workspace_path / "executor-state.json"
        if executor_state_file.exists():
            try:
                data = json.loads(executor_state_file.read_text())
                trace_id = data.get("trace_id")
                if trace_id:
                    cls._active_trace_id = trace_id
                    return trace_id
            except (json.JSONDecodeError, OSError):
                pass

        return None

    @classmethod
    def load(cls, workspace_dir: str | Path) -> "RunTrace | None":
        """Load an existing RunTrace from disk (coordinator convenience method).

        Returns None if no run-trace file is present.
        """
        trace_id = cls.attach(workspace_dir)
        if trace_id is None:
            return None
        return cls(trace_id=trace_id, workspace_dir=Path(workspace_dir))

    # ------------------------------------------------------------------
    # Instance methods
    # ------------------------------------------------------------------

    @property
    def trace_id(self) -> str:
        return self._trace_id

    def finish(self, status: str = "success", summary: dict[str, Any] | None = None) -> None:
        """Mark the run as finished and update run-trace.json.

        Args:
            status: "success", "failed", or "partial".
            summary: Optional dict of summary metrics to record.
        """
        lf = _get_client()
        lf.score_current_trace(
            name="run-status",
            value=1.0 if status == "success" else 0.0,
            data_type="NUMERIC",
            comment=status,
        )

        run_trace_file = self._workspace_dir / _RUN_TRACE_FILENAME
        if run_trace_file.exists():
            try:
                data = json.loads(run_trace_file.read_text())
            except (json.JSONDecodeError, OSError):
                data = {}
            data.update(
                {
                    "status": status,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    **({"summary": summary} if summary else {}),
                }
            )
            run_trace_file.write_text(json.dumps(data, indent=2))

        lf.flush()

    # ------------------------------------------------------------------
    # Module-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def current_trace_id(cls) -> str | None:
        """Return the active run trace_id for this process, or None.

        Use this when calling @observe-decorated functions that should be
        children of the root trace::

            result = my_func(arg, langfuse_trace_id=RunTrace.current_trace_id())
        """
        return cls._active_trace_id


def get_trace_id() -> str | None:
    """Module-level helper — returns the active run trace_id, or None.

    Equivalent to ``RunTrace.current_trace_id()``.  Import and use wherever
    a concise reference is preferred::

        from tracing import get_trace_id
        result = my_func(arg, langfuse_trace_id=get_trace_id())
    """
    return RunTrace.current_trace_id()
