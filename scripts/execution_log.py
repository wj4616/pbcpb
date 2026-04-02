#!/usr/bin/env python3
"""Execution log management for playbook runs."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def create_execution_log(
    playbook_path: str,
    status: str,
    phases_completed: int,
    duration_seconds: int,
    failure_modes_discovered: list = None,
    metrics_actuals: dict = None,
    decisions_made: list = None,
    complexity_verification: dict = None,
) -> dict:
    """
    Create an execution log structure.

    Args:
        playbook_path: Path to the playbook file
        status: "completed", "failed", or "partial"
        phases_completed: Number of phases completed
        duration_seconds: Total duration in seconds
        failure_modes_discovered: List of new failure modes found
        metrics_actuals: Dict of metric actuals
        decisions_made: List of decisions made during run
        complexity_verification: Complexity verification result

    Returns:
        Execution log dict
    """
    playbook_path = Path(playbook_path)
    playbook = json.loads(playbook_path.read_text()) if playbook_path.exists() else {}

    return {
        "run_id": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "playbook_file": playbook_path.name,
        "playbook_version": playbook.get("version", 1),
        "playbook_title": playbook.get("title", "Unknown"),
        "status": status,
        "phases_completed": phases_completed,
        "duration_seconds": duration_seconds,
        "failure_modes_discovered": failure_modes_discovered or [],
        "metrics_actuals": metrics_actuals or {},
        "decisions_made": decisions_made or [],
        "complexity_verification": complexity_verification or {},
    }


def write_execution_log(log: dict, output_dir: Path = None) -> Path:
    """
    Write execution log to file.

    Args:
        log: Execution log dict
        output_dir: Directory for log file (default: current dir)

    Returns:
        Path to written log file
    """
    if output_dir is None:
        output_dir = Path.cwd()

    # Generate filename based on run_id
    run_id_safe = log["run_id"].replace(":", "-").replace("T", "_")
    filename = f"playbook-execution-log-{run_id_safe}.json"
    log_path = output_dir / filename

    log_path.write_text(json.dumps(log, indent=2))
    return log_path


def read_execution_log(log_path: Path) -> Optional[dict]:
    """Read execution log from file."""
    if not log_path.exists():
        return None
    return json.loads(log_path.read_text())


def get_latest_execution_log(directory: Path) -> Optional[Path]:
    """Find the most recent execution log in a directory."""
    logs = list(directory.glob("playbook-execution-log-*.json"))
    if not logs:
        return None
    return max(logs, key=lambda p: p.stat().st_mtime)


def main():
    """CLI for execution log operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage playbook execution logs")
    parser.add_argument("command", choices=["list", "show", "latest"])
    parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Directory to search")
    parser.add_argument("--file", type=Path, help="Specific log file")

    args = parser.parse_args()

    if args.command == "list":
        logs = list(args.dir.glob("playbook-execution-log-*.json"))
        for log in sorted(logs):
            data = json.loads(log.read_text())
            print(f"{log.name}: {data.get('status', 'unknown')} - {data.get('phases_completed', 0)} phases")

    elif args.command == "show" and args.file:
        log = read_execution_log(args.file)
        if log:
            print(json.dumps(log, indent=2))
        else:
            print(f"Log not found: {args.file}")

    elif args.command == "latest":
        latest = get_latest_execution_log(args.dir)
        if latest:
            log = read_execution_log(latest)
            print(json.dumps(log, indent=2))
        else:
            print("No execution logs found")


if __name__ == "__main__":
    main()