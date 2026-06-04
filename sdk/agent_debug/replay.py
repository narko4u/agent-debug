"""Replay engine for AgentDebug SDK.

Allows stepping forward/backward through a trace and inspecting
the agent state at any step.
"""

from typing import Any, Dict, List, Optional


class ReplayEngine:
    """Iterate through a trace step by step, forward and backward.

    Provides variable inspection at any step to see what the agent
    was thinking, what tools it called, and what results it got.
    """

    def __init__(self, trace: Dict[str, Any]):
        """Initialize the replay engine with a trace.

        Args:
            trace: A valid trace dictionary.
        """
        self._trace = trace
        self._steps: List[Dict[str, Any]] = trace.get("steps", [])
        self._current_step: int = -1  # -1 means before first step
        self._history: List[Dict[str, Any]] = []
        self._max_steps = len(self._steps)

    @property
    def current_step_index(self) -> int:
        """Return the current step index (0-based), or -1 if before first step."""
        return self._current_step

    @property
    def total_steps(self) -> int:
        """Return total number of steps in the trace."""
        return self._max_steps

    @property
    def is_at_start(self) -> bool:
        """True if before the first step."""
        return self._current_step < 0

    @property
    def is_at_end(self) -> bool:
        """True if past the last step."""
        return self._current_step >= self._max_steps

    @property
    def progress(self) -> str:
        """Return progress string like '3/12'."""
        return f"{self._current_step + 1}/{self._max_steps}"

    @property
    def trace_info(self) -> Dict[str, Any]:
        """Return trace metadata (agent name, duration, etc.)."""
        return {
            "trace_id": self._trace.get("trace_id"),
            "agent_name": self._trace.get("agent_name"),
            "timestamp": self._trace.get("timestamp"),
            "total_steps": self._max_steps,
            "output": self._trace.get("output"),
            "metadata": self._trace.get("metadata", {}),
        }

    def step_forward(self) -> Optional[Dict[str, Any]]:
        """Advance one step forward.

        Returns:
            The current step data, or None if already past the end.
        """
        if self._current_step >= self._max_steps - 1:
            if self._current_step >= self._max_steps:
                return None
            self._current_step += 1
            self._history.append({})
            return None  # past end — trace is done

        self._current_step += 1
        step_data = self._steps[self._current_step]
        self._history.append(step_data)
        return step_data

    def step_backward(self) -> Optional[Dict[str, Any]]:
        """Go back one step.

        Returns:
            The step data at the new current position, or None
            if already at the start.
        """
        if self._current_step < 0:
            return None

        self._current_step -= 1
        if self._current_step >= 0:
            return self._steps[self._current_step]

        # Pop from history
        if self._history:
            self._history.pop()
        return None

    def go_to_step(self, step_index: int) -> Optional[Dict[str, Any]]:
        """Jump to a specific step index (0-based).

        Args:
            step_index: The step to jump to.

        Returns:
            The step data at that index, or None if out of range.
        """
        if step_index < 0 or step_index >= self._max_steps:
            return None

        self._current_step = step_index
        # Rebuild history up to this point
        self._history = self._steps[: step_index + 1]
        return self._steps[self._current_step]

    def inspect_variables(self) -> Dict[str, Any]:
        """Inspect the agent state at the current step.

        Returns:
            A dict with:
            - step_index: current step (0-based)
            - phase: current phase
            - input: step input if available
            - thought: agent thought if available
            - tool_calls: tool calls at this step
            - subagent_state: subagent state snapshot
            - step_data: the full raw step data
        """
        if self._current_step < 0 or self._current_step >= self._max_steps:
            return {
                "step_index": self._current_step,
                "phase": None,
                "input": None,
                "thought": None,
                "tool_calls": [],
                "subagent_state": None,
                "step_data": None,
                "message": "No step selected"
            }

        step = self._steps[self._current_step]
        return {
            "step_index": self._current_step,
            "phase": step.get("phase"),
            "input": step.get("input"),
            "thought": step.get("thought"),
            "tool_calls": step.get("tool_calls", []),
            "subagent_state": step.get("subagent_state"),
            "step_data": step,
        }

    def get_step(self, step_index: int) -> Optional[Dict[str, Any]]:
        """Get raw step data by index without changing position.

        Args:
            step_index: The step index (0-based).

        Returns:
            The step data dict, or None if out of range.
        """
        if 0 <= step_index < self._max_steps:
            return self._steps[step_index]
        return None

    def get_all_steps(self) -> List[Dict[str, Any]]:
        """Return all steps in the trace."""
        return self._steps

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the trace.

        Returns:
            Dict with step count, duration, tool usage, etc.
        """
        metadata = self._trace.get("metadata", {})
        tool_usage: Dict[str, int] = {}
        total_tool_calls = 0

        for step in self._steps:
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                tool_name = tc.get("tool", "unknown")
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
                total_tool_calls += 1

        return {
            "trace_id": self._trace.get("trace_id"),
            "agent_name": self._trace.get("agent_name"),
            "total_steps": self._max_steps,
            "total_tool_calls": total_tool_calls,
            "tool_usage": tool_usage,
            "total_duration_ms": metadata.get("total_duration_ms", 0),
            "model": metadata.get("model", "unknown"),
            "token_count": metadata.get("token_count", 0),
        }
