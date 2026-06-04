"""AgentDebug SDK — Agent Execution Inspector & Replay SDK.

A lightweight Python package that wraps any agent call and captures
a structured trace — every input, output, intermediate thought, tool call,
tool result, timestamp, and subagent state snapshot.

Usage:
    from agent_debug import trace, TraceInspector

    @trace
    def my_agent(prompt):
        # ... agent logic ...
        return result

    with TraceInspector("my_agent") as inspector:
        inspector.log_step(1, "thinking", {"input": prompt})
        inspector.log_tool_call(1, "search", {"query": "..."}, {"results": [...]})
        inspector.log_output(result)
        inspector.save("trace.json")
"""

from .core import (
    trace,
    TraceInspector,
    load_trace,
    list_traces,
)
from .replay import ReplayEngine
from .schema import validate_trace, SchemaValidationError
from .export import export_to_html
from .utils import generate_trace_id, current_iso_timestamp, Timer
from .license import (
    LicenseError,
    is_licensed,
    activate_license,
    check_trial,
    format_trial_status,
    reset_trial,
)

__all__ = [
    "trace",
    "TraceInspector",
    "ReplayEngine",
    "load_trace",
    "SchemaValidationError",
    "ReplayEngine",
    "list_traces",
    "load_trace",
    "generate_trace_id",
    "current_iso_timestamp",
    "Timer",
    "LicenseError",
    "is_licensed",
    "activate_license",
    "check_trial",
    "format_trial_status",
    "reset_trial",
]

__version__ = "0.1.0"
