#!/usr/bin/env python3
"""Checkpoint management for session boundary resilience.

Usage:
    # Save checkpoint after phase completion
    python3 scripts/checkpoint_manager.py save --phase 3 --artifacts file1.md file2.md

    # Verify checkpoint on session resume
    python3 scripts/checkpoint_manager.py verify --phase 4 --artifacts file1.md file2.md

    # List all checkpoints
    python3 scripts/checkpoint_manager.py list --dir .checkpoints
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import tracing  # noqa: F401 — initialise Langfuse before decorators fire
from tracing import RunTrace
from langfuse import observe, get_client

RunTrace.attach("/home/myuser/.openclaw/workspace-pb-coordinator")

CHARS_PER_TOKEN = 4


def compute_checksum(content: str) -> str:
    """SHA-256 checksum of content (first 16 chars for readability)."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def save_checkpoint(phase: int, artifacts: dict[str, str], checkpoint_dir: Path) -> Path:
    """
    Save checksums for all artifacts after phase completion.

    Args:
        phase: Phase number (0-based)
        artifacts: Dict of filename -> content
        checkpoint_dir: Directory for checkpoint files

    Returns:
        Path to checkpoint file
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        "phase": phase,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifacts": {}
    }

    for name, content in artifacts.items():
        checkpoint["artifacts"][name] = {
            "checksum": compute_checksum(content),
            "size_bytes": len(content),
            "estimated_tokens": len(content) // CHARS_PER_TOKEN
        }

    checkpoint_file = checkpoint_dir / f"checkpoint-phase{phase:02d}.json"
    checkpoint_file.write_text(json.dumps(checkpoint, indent=2))
    return checkpoint_file


def verify_checkpoint(phase: int, artifacts: dict[str, str], checkpoint_dir: Path) -> tuple[bool, list[str]]:
    """
    Verify artifacts match checkpoint from previous phase.

    Args:
        phase: Current phase number (will verify against phase-1)
        artifacts: Dict of filename -> content
        checkpoint_dir: Directory containing checkpoint files

    Returns:
        Tuple of (passed, list of mismatch descriptions)
    """
    # Edge case: Phase 0 has no previous checkpoint
    if phase == 0:
        return True, []  # Nothing to verify

    # Look for checkpoint from previous phase
    checkpoint_file = checkpoint_dir / f"checkpoint-phase{phase-1:02d}.json"

    if not checkpoint_file.exists():
        return False, [f"No checkpoint found for previous phase {phase-1}"]

    checkpoint = json.loads(checkpoint_file.read_text())
    mismatches = []

    for name, content in artifacts.items():
        if name not in checkpoint["artifacts"]:
            mismatches.append(f"Artifact '{name}' not in checkpoint")
            continue

        expected = checkpoint["artifacts"][name]["checksum"]
        actual = compute_checksum(content)

        if expected != actual:
            mismatches.append(
                f"Artifact '{name}' checksum mismatch: "
                f"expected {expected}, got {actual}"
            )

    return len(mismatches) == 0, mismatches


def get_checkpoint(phase: int, checkpoint_dir: Path) -> dict | None:
    """Load checkpoint data for a phase."""
    checkpoint_file = checkpoint_dir / f"checkpoint-phase{phase:02d}.json"
    if not checkpoint_file.exists():
        return None
    return json.loads(checkpoint_file.read_text())


def list_checkpoints(checkpoint_dir: Path) -> list[dict]:
    """List all checkpoints in directory."""
    checkpoints = []
    for f in sorted(checkpoint_dir.glob("checkpoint-phase*.json")):
        data = json.loads(f.read_text())
        checkpoints.append({"file": str(f), "phase": data.get("phase"), "timestamp": data.get("timestamp")})
    return checkpoints


@observe(name="checkpoint-save", capture_input=False, capture_output=False)
def _traced_save(phase: int, artifact_files: list[str], checkpoint_dir: Path) -> Path:
    """Save checkpoint with tracing."""
    _lf = get_client()
    artifacts = {}
    for f in artifact_files:
        p = Path(f)
        if p.exists():
            artifacts[p.name] = p.read_text()
    _lf.update_current_span(input={"phase": phase, "artifact_count": len(artifacts)})
    path = save_checkpoint(phase, artifacts, checkpoint_dir)
    _lf.update_current_span(output={"checkpoint_path": str(path)})
    return path


@observe(name="checkpoint-verify", capture_input=False, capture_output=False)
def _traced_verify(phase: int, artifact_files: list[str], checkpoint_dir: Path) -> tuple[bool, list]:
    """Verify checkpoint with tracing."""
    _lf = get_client()
    artifacts = {}
    for f in artifact_files:
        p = Path(f)
        if p.exists():
            artifacts[p.name] = p.read_text()
    _lf.update_current_span(input={"phase": phase, "artifact_count": len(artifacts)})
    passed, mismatches = verify_checkpoint(phase, artifacts, checkpoint_dir)
    _lf.update_current_span(output={"passed": passed, "mismatch_count": len(mismatches)})
    return passed, mismatches


def main():
    parser = argparse.ArgumentParser(description="Manage phase checkpoints")
    parser.add_argument("command", choices=["save", "verify", "list", "get"])
    parser.add_argument("--phase", type=int, required=True, help="Phase number (0-based)")
    parser.add_argument("--artifacts", nargs="*", help="Artifact files to checkpoint")
    parser.add_argument("--dir", type=Path, default=Path(".checkpoints"), help="Checkpoint directory")

    args = parser.parse_args()

    trace_id = RunTrace.current_trace_id()

    if args.command == "save":
        if not args.artifacts:
            print("Error: --artifacts required for save")
            return
        path = _traced_save(args.phase, args.artifacts, args.dir, langfuse_trace_id=trace_id)
        print(f"Checkpoint saved: {path}")

    elif args.command == "verify":
        if not args.artifacts:
            print("Error: --artifacts required for verify")
            return
        passed, mismatches = _traced_verify(args.phase, args.artifacts, args.dir, langfuse_trace_id=trace_id)
        if passed:
            print("PASS: All artifacts match checkpoint")
        else:
            print("FAIL: Checksum mismatches detected")
            for m in mismatches:
                print(f"  - {m}")

    elif args.command == "list":
        checkpoints = list_checkpoints(args.dir)
        for cp in checkpoints:
            print(f"Phase {cp['phase']}: {cp['timestamp']}")

    elif args.command == "get":
        data = get_checkpoint(args.phase, args.dir)
        if data:
            print(json.dumps(data, indent=2))
        else:
            print(f"No checkpoint found for phase {args.phase}")


if __name__ == "__main__":
    main()