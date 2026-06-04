"""Trace JSON schema validation for AgentDebug SDK."""

from typing import Any, Dict, List, Optional


REQUIRED_TOP_LEVEL_KEYS = {"trace_id", "agent_name", "timestamp", "steps"}
REQUIRED_STEP_KEYS = {"step_index", "phase", "timestamp"}
VALID_PHASES = {"thinking", "tool_call", "deciding", "output"}


class SchemaValidationError(ValueError):
    """Raised when a trace fails schema validation."""
    pass


def validate_trace(trace: Dict[str, Any]) -> None:
    """Validate a trace dictionary against the schema.

    Args:
        trace: Trace dictionary to validate.

    Raises:
        SchemaValidationError: If validation fails.
    """
    errors = []

    # Check top-level keys
    missing = REQUIRED_TOP_LEVEL_KEYS - set(trace.keys())
    if missing:
        errors.append(f"Missing required top-level keys: {missing}")

    if not isinstance(trace.get("trace_id"), str):
        errors.append("trace_id must be a string")
    if not isinstance(trace.get("agent_name"), str):
        errors.append("agent_name must be a string")
    if not isinstance(trace.get("timestamp"), str):
        errors.append("timestamp must be a string (ISO 8601)")

    # Validate steps
    steps = trace.get("steps", [])
    if not isinstance(steps, list):
        errors.append("steps must be a list")
        steps = []

    step_indices: set = set()
    for i, step in enumerate(steps):
        step_errors = _validate_step(step, i)
        errors.extend(step_errors)

        step_index = step.get("step_index")
        if step_index is not None:
            if step_index in step_indices:
                errors.append(f"Step {i}: duplicate step_index {step_index}")
            step_indices.add(step_index)

    # Validate metadata if present
    metadata = trace.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("metadata must be a dict or None")

    if errors:
        raise SchemaValidationError("\n".join(errors))


def _validate_step(step: Any, index: int) -> List[str]:
    """Validate a single step entry."""
    errors = []
    if not isinstance(step, dict):
        return [f"Step {index}: must be a dict, got {type(step).__name__}"]

    missing = REQUIRED_STEP_KEYS - set(step.keys())
    if missing:
        errors.append(f"Step {index}: missing required keys: {missing}")

    phase = step.get("phase")
    if phase is not None and phase not in VALID_PHASES:
        errors.append(f"Step {index}: invalid phase '{phase}'. Must be one of {VALID_PHASES}")

    step_index = step.get("step_index")
    if step_index is not None and not isinstance(step_index, int):
        errors.append(f"Step {index}: step_index must be an integer")

    timestamp = step.get("timestamp")
    if timestamp is not None and not isinstance(timestamp, str):
        errors.append(f"Step {index}: timestamp must be a string")

    # Validate tool_calls if present
    tool_calls = step.get("tool_calls")
    if tool_calls is not None:
        if not isinstance(tool_calls, list):
            errors.append(f"Step {index}: tool_calls must be a list")
        else:
            for j, tc in enumerate(tool_calls):
                if not isinstance(tc, dict):
                    errors.append(f"Step {index}, tool_call {j}: must be a dict")
                    continue
                if "tool" not in tc:
                    errors.append(f"Step {index}, tool_call {j}: missing 'tool' field")

    return errors


def validate_step_data(phase: str, data: Dict[str, Any]) -> None:
    """Validate data being logged into a step.

    Args:
        phase: Phase name ('thinking', 'tool_call', 'deciding', 'output').
        data: Data dict to validate.

    Raises:
        SchemaValidationError: If validation fails.
    """
    if phase not in VALID_PHASES:
        raise SchemaValidationError(
            f"Invalid phase '{phase}'. Must be one of {VALID_PHASES}"
        )
