"""Core TraceInspector and trace decorator for AgentDebug SDK."""

import functools
import json
import os
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    overload,
)

from .utils import generate_trace_id, current_iso_timestamp, Timer, estimate_token_count
from .schema import validate_trace, validate_step_data
from .replay import ReplayEngine
from .export import export_to_html

F = TypeVar("F", bound=Callable[..., Any])

_DEFAULT_TRACES_DIR = Path.home() / ".agent_debug" / "traces"


class _StepLogger:
    """Internal step builder used by TraceInspector."""

    def __init__(self, step_index: int):
        self.step_index = step_index
        self.phase: str = "thinking"
        self.input: Any = None
        self.thought: Optional[str] = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.subagent_state: Optional[Dict[str, Any]] = None
        self.timestamp: str = current_iso_timestamp()

    def set_phase(self, phase: str) -> "_StepLogger":
        validate_step_data(phase, {})
        self.phase = phase
        return self

    def log_input(self, data: Any) -> "_StepLogger":
        self.input = data
        return self

    def log_thought(self, thought: str) -> "_StepLogger":
        self.thought = thought
        return self

    def log_tool_call(
        self,
        tool: str,
        arguments: Dict[str, Any],
        result: Any = None,
        duration_ms: int = 0,
    ) -> "_StepLogger":
        self.tool_calls.append({
            "tool": tool,
            "arguments": arguments,
            "result": result,
            "duration_ms": duration_ms,
        })
        return self

    def log_subagent_state(self, state: Dict[str, Any]) -> "_StepLogger":
        self.subagent_state = state
        return self

    def build(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "phase": self.phase,
            "input": self.input,
            "thought": self.thought,
            "tool_calls": self.tool_calls,
            "subagent_state": self.subagent_state,
            "timestamp": self.timestamp,
        }


class TraceInspector:
    """Context manager for fine-grained control over trace capture.

    Usage:
        with TraceInspector("my_agent") as inspector:
            inspector.log_step(1, "thinking", {"input": prompt})
            inspector.log_tool_call(1, "search", {...}, {...})
            inspector.log_output(result)
            inspector.save("trace.json")
    """

    def __init__(
        self,
        agent_name: str = "agent",
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ):
        self._trace: Dict[str, Any] = {
            "trace_id": trace_id or generate_trace_id(),
            "agent_name": agent_name,
            "timestamp": current_iso_timestamp(),
            "steps": [],
            "output": None,
            "metadata": metadata or {},
        }
        self._step_loggers: Dict[int, _StepLogger] = {}
        self._timer = Timer()
        self._total_token_count = 0

        if model:
            self._trace["metadata"]["model"] = model

    @property
    def trace_id(self) -> str:
        return self._trace["trace_id"]

    @property
    def agent_name(self) -> str:
        return self._trace["agent_name"]

    def log_step(
        self,
        step_index: int,
        phase: str = "thinking",
        input_data: Any = None,
        thought: Optional[str] = None,
    ) -> "_StepLogger":
        """Log a step in the agent execution.

        Args:
            step_index: The step number (1-based or 0-based, consistent throughout).
            phase: One of 'thinking', 'tool_call', 'deciding', 'output'.
            input_data: The input received at this step.
            thought: The agent's thought/reasoning at this step.

        Returns:
            A _StepLogger that can be further customized.
        """
        logger = _StepLogger(step_index)
        logger.set_phase(phase)
        if input_data is not None:
            logger.log_input(input_data)
        if thought is not None:
            logger.log_thought(thought)
        self._step_loggers[step_index] = logger
        return logger

    def log_tool_call(
        self,
        step_index: int,
        tool: str,
        arguments: Dict[str, Any],
        result: Any = None,
        duration_ms: int = 0,
    ) -> None:
        """Log a tool call for an existing step.

        Args:
            step_index: The step index the tool call belongs to.
            tool: Tool name.
            arguments: Tool arguments.
            result: Tool result.
            duration_ms: Tool execution duration in ms.
        """
        if step_index not in self._step_loggers:
            self.log_step(step_index, phase="tool_call")
        self._step_loggers[step_index].log_tool_call(tool, arguments, result, duration_ms)

    def log_output(self, output: Any) -> None:
        """Log the final output of the agent.

        Args:
            output: The final output value.
        """
        self._trace["output"] = output

    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata to the trace.

        Args:
            key: Metadata key.
            value: Metadata value.
        """
        self._trace["metadata"][key] = value

    def snapshot(self) -> Dict[str, Any]:
        """Build and return the trace as a dictionary.

        Returns:
            Complete trace dict with all logged steps.
        """
        self._finalize()
        return self._trace

    def save(self, path: Optional[str] = None) -> str:
        """Save the trace to a JSON file.

        Args:
            path: File path. If None, saves to ~/.agent_debug/traces/<trace_id>.json.

        Returns:
            The path the trace was saved to.
        """
        self._finalize()

        if path is None:
            traces_dir = _DEFAULT_TRACES_DIR
            traces_dir.mkdir(parents=True, exist_ok=True)
            path = str(traces_dir / f"{self._trace['trace_id']}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._trace, f, indent=2, default=str)

        return path

    def to_json(self) -> str:
        """Return the trace as a JSON string.

        Returns:
            JSON string of the trace.
        """
        self._finalize()
        return json.dumps(self._trace, indent=2, default=str)

    def replay(self) -> "ReplayEngine":
        """Create a ReplayEngine from the current trace.

        Returns:
            A ReplayEngine instance ready for step-by-step replay.
        """
        self._finalize()
        return ReplayEngine(self._trace)

    def export_html(self, path: Optional[str] = None) -> str:
        """Export the trace as a self-contained HTML report.

        Args:
            path: Optional file path to write the HTML to.

        Returns:
            The HTML content as a string.
        """
        self._finalize()
        return export_to_html(self._trace, output_path=path)

    def summary(self) -> Dict[str, Any]:
        """Get a summary of the trace.

        Returns:
            Dict with step count, tool usage, duration, etc.
        """
        self._finalize()
        engine = ReplayEngine(self._trace)
        return engine.get_summary()

    def _finalize(self) -> None:
        """Finalize the trace by flushing step loggers into steps list."""
        if self._step_loggers:
            self._trace["steps"] = [
                logger.build()
                for idx, logger in sorted(self._step_loggers.items())
            ]
            self._step_loggers.clear()

        # Calculate total tokens from all text content
        total_tokens = 0
        for step in self._trace.get("steps", []):
            thought = step.get("thought", "")
            if thought:
                total_tokens += estimate_token_count(str(thought))
            inp = step.get("input")
            if inp:
                total_tokens += estimate_token_count(str(inp))
            for tc in step.get("tool_calls", []):
                for key in ("arguments", "result"):
                    val = tc.get(key)
                    if val:
                        total_tokens += estimate_token_count(str(val))

        self._trace["metadata"]["token_count"] = (
            self._trace["metadata"].get("token_count", 0) + total_tokens
        )

        if self._timer._running:
            self._timer.stop()

        if "total_duration_ms" not in self._trace["metadata"]:
            self._trace["metadata"]["total_duration_ms"] = self._timer.elapsed_ms()

    def __enter__(self) -> "TraceInspector":
        self._timer.start()
        return self

    def __exit__(self, *args) -> None:
        self._finalize()


# ---- Decorator-based usage ----

@overload
def trace(
    func: F,
) -> F: ...


@overload
def trace(
    *,
    name: Optional[str] = None,
    save: bool = False,
    save_path: Optional[str] = None,
    model: Optional[str] = None,
) -> Callable[[F], F]: ...


def trace(
    func: Optional[F] = None,
    *,
    name: Optional[str] = None,
    save: bool = False,
    save_path: Optional[str] = None,
    model: Optional[str] = None,
):
    """Decorator that wraps any agent function to capture execution traces.

    Can be used with or without arguments:

    @trace
    def my_agent(prompt): ...

    @trace(name="research_agent", model="gpt-4")
    def my_agent(prompt): ...

    Args:
        func: The agent function to wrap.
        name: Custom agent name for the trace.
        save: If True, auto-save the trace after execution.
        save_path: Specific path to save the trace to.
        model: Model identifier for metadata.

    Returns:
        The wrapped function, or a decorator factory.
    """
    if func is not None:
        # Used as @trace without arguments
        return _TraceDecorator(name=func.__name__, save=False, model=model)(func)

    # Used as @trace(name=..., save=True) with arguments
    return _TraceDecorator(
        name=name,
        save=save,
        save_path=save_path,
        model=model,
    )


class _TraceDecorator:
    """Internal decorator implementation."""

    def __init__(
        self,
        name: Optional[str] = None,
        save: bool = False,
        save_path: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._name = name
        self._save = save
        self._save_path = save_path
        self._model = model

    def __call__(self, func: F) -> F:
        name = self._name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with TraceInspector(
                agent_name=name,
                model=self._model,
            ) as inspector:
                inspector.log_step(
                    1,
                    phase="thinking",
                    input_data={"args": _truncate_args(args), "kwargs": _truncate_args(kwargs)},
                    thought=f"Calling {func.__name__}",
                )

                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    inspector.log_step(2, phase="output", input_data=None, thought=f"Error: {e}")
                    inspector.log_output({"error": str(e)})
                    inspector.add_metadata("status", "error")
                    if self._save:
                        inspector.save(self._save_path)
                    raise

                inspector.log_step(2, phase="output", input_data=None, thought="Completed")
                inspector.log_output(result)
                inspector.add_metadata("status", "success")

                if self._save:
                    inspector.save(self._save_path)

                return result

        return wrapper  # type: ignore


def _truncate_args(args: Any) -> Any:
    """Truncate large arguments for storage."""
    if isinstance(args, dict):
        return {k: _truncate_value(v) for k, v in args.items()}
    if isinstance(args, (list, tuple)):
        return [_truncate_value(v) for v in args[:10]]  # max 10 items
    return _truncate_value(args)


def _truncate_value(value: Any) -> Any:
    """Truncate long strings."""
    if isinstance(value, str) and len(value) > 1000:
        return value[:997] + "..."
    return value


# ---- Module-level helpers ----

def load_trace(path: str) -> Dict[str, Any]:
    """Load a trace from a JSON file.

    Args:
        path: Path to the trace JSON file.

    Returns:
        The trace dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        SchemaValidationError: If the trace fails schema validation.
    """
    with open(path, "r", encoding="utf-8") as f:
        trace = json.load(f)
    validate_trace(trace)
    return trace


def list_traces(traces_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all traces in a directory.

    Args:
        traces_dir: Directory to search. Defaults to ~/.agent_debug/traces/.

    Returns:
        List of dicts with 'path', 'trace_id', 'agent_name', 'timestamp', 'steps'.
    """
    if traces_dir is None:
        search_dir = _DEFAULT_TRACES_DIR
    else:
        search_dir = Path(traces_dir)

    if not search_dir.exists():
        return []

    results = []
    for fpath in sorted(search_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            trace = json.loads(fpath.read_text(encoding="utf-8"))
            results.append({
                "path": str(fpath),
                "trace_id": trace.get("trace_id", "unknown"),
                "agent_name": trace.get("agent_name", "unknown"),
                "timestamp": trace.get("timestamp", "unknown"),
                "steps": len(trace.get("steps", [])),
            })
        except (json.JSONDecodeError, IOError):
            continue

    return results
