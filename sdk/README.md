# AgentDebug SDK

**Agent Execution Inspector & Replay SDK**

Instrument any AI agent to capture full execution traces and replay them step-by-step for debugging. The #1 complaint about AI agents is they're impossible to debug — AgentDebug fixes that.

## Installation

```bash
pip install agent-debug
```

## Quick Start

### Decorator-based tracing

```python
from agent_debug import trace

@trace(name="my_agent", save=True)
def my_agent(prompt: str) -> str:
    # Your agent logic here
    thought = f"Processing: {prompt}"
    result = f"Answer to: {prompt}"
    return result

result = my_agent("What is the capital of France?")
```

### Context manager for fine-grained control

```python
from agent_debug import TraceInspector

inspector = TraceInspector("research_agent", model="gpt-4")

# Step 1: Agent thinks
inspector.log_step(
    1, 
    phase="thinking", 
    input_data={"prompt": "Research quantum computing"},
    thought="I need to search for recent quantum computing breakthroughs"
)

# Step 2: Tool call
inspector.log_tool_call(
    1,
    tool="web_search",
    arguments={"query": "quantum computing breakthroughs 2024"},
    result={"results": ["Quantum supremacy achieved..."]},
    duration_ms=450
)

# Step 3: Decision
inspector.log_step(
    2,
    phase="deciding",
    input_data={"search_results": "..."},
    thought="Based on the results, the key breakthrough is..."
)

# Step 4: Output
inspector.log_output("Quantum computing has achieved...")

# Save for later replay
saved_path = inspector.save("my_trace.json")
print(f"Trace saved to {saved_path}")

# Export to HTML report
inspector.export_html("my_report.html")
```

### Replaying a trace

```python
from agent_debug import load_trace, ReplayEngine

trace = load_trace("my_trace.json")
replay = ReplayEngine(trace)

# Step forward
step_1 = replay.step_forward()
print(f"Step {replay.current_step_index + 1}: {step_1['phase']}")

# Inspect variables at current step
vars = replay.inspect_variables()
print(f"Thought: {vars['thought']}")
print(f"Tool calls: {len(vars['tool_calls'])}")

# Step backward
step_0 = replay.step_backward()

# Get summary
summary = replay.get_summary()
print(f"Total steps: {summary['total_steps']}")
print(f"Tool usage: {summary['tool_usage']}")
```

## API Reference

### `@trace` decorator

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Function name | Agent name for traces |
| `save` | `bool` | `False` | Auto-save trace after execution |
| `save_path` | `str` | `None` | Custom save path |
| `model` | `str` | `None` | Model identifier for metadata |

### `TraceInspector`

| Method | Description |
|--------|-------------|
| `log_step(step_index, phase, input_data, thought)` | Log an execution step |
| `log_tool_call(step_index, tool, arguments, result, duration_ms)` | Log a tool call |
| `log_output(output)` | Set the final output |
| `save(path)` | Save trace to JSON file |
| `replay()` | Create ReplayEngine from trace |
| `export_html(path)` | Export to HTML report |
| `summary()` | Get trace summary |
| `snapshot()` | Get trace as dict |
| `to_json()` | Get trace as JSON string |

### `ReplayEngine`

| Method | Description |
|--------|-------------|
| `step_forward()` | Advance one step |
| `step_backward()` | Go back one step |
| `go_to_step(index)` | Jump to specific step |
| `inspect_variables()` | See agent state at current step |
| `get_summary()` | Get execution summary |
| `get_step(index)` | Get raw step data |
| `get_all_steps()` | Get all steps |

## Trace JSON Schema

```json
{
  "trace_id": "uuid",
  "agent_name": "string",
  "timestamp": "ISO8601",
  "steps": [
    {
      "step_index": 1,
      "phase": "thinking|tool_call|deciding|output",
      "input": {},
      "thought": "string",
      "tool_calls": [
        {"tool": "name", "arguments": {}, "result": {}, "duration_ms": 150}
      ],
      "subagent_state": {},
      "timestamp": "ISO8601"
    }
  ],
  "output": {},
  "metadata": {
    "model": "string",
    "total_duration_ms": 1234,
    "token_count": 567
  }
}
```

## License

MIT License — free for local use. Cloud features available at [agentdebug.dev](https://agentdebug.dev).

## Related

- [AgentDebug Dashboard](https://agentdebug.dev/dashboard) — Browser-based trace inspector
- [AgentDebug CLI](https://agentdebug.dev/cli) — Command-line trace inspection
