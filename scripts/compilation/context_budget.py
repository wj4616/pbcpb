"""
Context budget loader with priority-based file selection.

Implements the context budget algorithm:
1. Validate priority files exist in context_load
2. Assign default priority to files without explicit priority
3. Sort files by priority (1=highest, 10=lowest)
4. Load files until budget exhausted
5. Error if critical files cannot fit
"""

from dataclasses import dataclass
from typing import Any

from .constants import (
    CHARS_PER_TOKEN,
    DEFAULT_PRIORITY,
    DEFAULT_SYSTEM_PROMPT_BUDGET,
    DEFAULT_FILE_TOKENS_ESTIMATE,
    MIN_PRIORITY,
    MAX_PRIORITY,
)


@dataclass
class ContextLoadResult:
    """Result of context loading."""
    loaded_files: dict[str, str]
    loaded_tokens: int
    skipped_files: list[str]
    skipped_tokens: int
    errors: list[str]
    warnings: list[str]


def load_context_with_budget(
    files: dict[str, str],  # filename -> content
    priority: dict[str, int] | None,
    max_tokens: int,
    critical_threshold: int = 3,
    system_prompt_budget: int = DEFAULT_SYSTEM_PROMPT_BUDGET,
    response_budget: int = 4096,
) -> ContextLoadResult:
    """
    Load files with priority-based budget management.

    Args:
        files: Dict of filename -> file content
        priority: Dict of filename -> priority (1-10), or None
        max_tokens: Maximum tokens for context
        critical_threshold: Files at priority <= this cannot be skipped
        system_prompt_budget: Tokens reserved for system prompt
        response_budget: Tokens reserved for response

    Returns:
        ContextLoadResult with loaded/skipped files and stats
    """
    errors = []
    warnings = []

    # Step 1: Validate priority files exist in files dict
    if priority:
        orphaned = [f for f in priority if f not in files]
        if orphaned:
            errors.append(
                f"Priority files not in context_load: {orphaned}. "
                f"All files in priority must exist in context_load."
            )
            return ContextLoadResult({}, 0, list(files.keys()), 0, errors, warnings)

    # Step 2: Validate priority values in range
    if priority:
        for filename, pri in priority.items():
            if pri < MIN_PRIORITY or pri > MAX_PRIORITY:
                errors.append(
                    f"Invalid priority {pri} for '{filename}' (must be {MIN_PRIORITY}-{MAX_PRIORITY})"
                )
        if errors:
            return ContextLoadResult({}, 0, list(files.keys()), 0, errors, warnings)

    # Step 3: Calculate available budget
    available_tokens = max_tokens - system_prompt_budget - response_budget
    if available_tokens < 1000:
        errors.append(
            f"Insufficient budget: {max_tokens} tokens total, "
            f"need at least {system_prompt_budget + response_budget + 1000}"
        )
        return ContextLoadResult({}, 0, list(files.keys()), 0, errors, warnings)

    # Step 4: Assign default priorities
    file_priorities = {}
    for filename in files:
        if priority and filename in priority:
            file_priorities[filename] = priority[filename]
        else:
            file_priorities[filename] = DEFAULT_PRIORITY

    # Step 5: Estimate token counts
    file_tokens = {}
    for filename, content in files.items():
        file_tokens[filename] = len(content) // CHARS_PER_TOKEN

    # Step 6: Group files by priority
    by_priority: dict[int, list[str]] = {}
    for filename, pri in file_priorities.items():
        if pri not in by_priority:
            by_priority[pri] = []
        by_priority[pri].append(filename)

    # Step 7: Sort priorities (1 = highest)
    sorted_priorities = sorted(by_priority.keys())

    # Step 8: Load files until budget exhausted
    loaded_files = {}
    loaded_tokens = 0
    skipped_files = []
    skipped_tokens = 0

    for pri in sorted_priorities:
        files_at_priority = by_priority[pri]
        tokens_at_priority = sum(file_tokens[f] for f in files_at_priority)

        if loaded_tokens + tokens_at_priority <= available_tokens:
            # All files at this priority fit
            for filename in files_at_priority:
                loaded_files[filename] = files[filename]
            loaded_tokens += tokens_at_priority
        else:
            # Budget exceeded
            if pri <= critical_threshold:
                # Critical files cannot be skipped
                errors.append(
                    f"Insufficient budget for critical files (priority {pri}). "
                    f"Need {tokens_at_priority} tokens, have {available_tokens - loaded_tokens} available. "
                    f"Files: {files_at_priority}"
                )
                return ContextLoadResult(loaded_files, loaded_tokens, skipped_files, skipped_tokens, errors, warnings)
            else:
                # Skip non-critical files
                for filename in files_at_priority:
                    skipped_files.append(filename)
                    skipped_tokens += file_tokens[filename]

                warnings.append(
                    f"[CONTEXT BUDGET WARNING] Skipped priority {pri} files: {files_at_priority}"
                )

    # Step 9: Generate summary warning if files were skipped
    if skipped_files:
        warnings.insert(0, (
            f"[CONTEXT BUDGET WARNING]\n"
            f"Budget: {available_tokens} tokens available\n"
            f"Loaded: {loaded_tokens} tokens ({len(loaded_files)} files)\n"
            f"Skipped: {skipped_tokens} tokens ({len(skipped_files)} files)"
        ))

    return ContextLoadResult(loaded_files, loaded_tokens, skipped_files, skipped_tokens, errors, warnings)


def estimate_file_tokens(content: str) -> int:
    """Estimate token count for content."""
    return len(content) // CHARS_PER_TOKEN


def estimate_context_tokens(context_load: list, file_contents: dict = None) -> int:
    """
    Estimate total tokens for context_load list.

    Args:
        context_load: List of filenames (may include annotations)
        file_contents: Optional dict of filename -> content for accurate estimation

    Returns:
        Estimated token count
    """
    total = 0
    for item in context_load:
        # Extract filename from "filename (annotation)" format
        filename = item.split("(")[0].strip()
        if file_contents and filename in file_contents:
            total += estimate_file_tokens(file_contents[filename])
        else:
            # Use heuristic for unknown files
            total += DEFAULT_FILE_TOKENS_ESTIMATE
    return total


def estimate_critical_tokens(context_load: list, priority: dict, threshold: int) -> int:
    """
    Estimate tokens for critical files (priority <= threshold).

    Args:
        context_load: List of filenames
        priority: Dict of filename -> priority (1-10)
        threshold: Critical threshold (files with priority <= threshold)

    Returns:
        Estimated token count for critical files
    """
    total = 0
    for item in context_load:
        filename = item.split("(")[0].strip()
        prio = priority.get(filename, 5)  # default priority
        if prio <= threshold:
            total += DEFAULT_FILE_TOKENS_ESTIMATE
    return total