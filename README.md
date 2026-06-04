<div align="center">
  <h1>🔍 AgentDebug</h1>
  <p><strong>Agent Execution Inspector &amp; Replay SDK</strong></p>
  <p>Open-core agent debugging — instrument any agent, capture full execution traces, replay step-by-step.</p>
  <p>
    <a href="#quick-start">Quick Start</a> ·
    <a href="#features">Features</a> ·
    <a href="#api-reference">API</a> ·
    <a href="#cli">CLI</a> ·
    <a href="#pricing">Pricing</a>
  </p>
  <p>
    <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
    <img alt="Python" src="https://img.shields.io/badge/python-3.9+-blue">
    <img alt="Status" src="https://img.shields.io/badge/status-alpha-yellow">
  </p>
</div>

---

## 💀 The Problem

AI agents are a black box. When they fail — and they will — you have no idea *why*. Was it a bad search result? A hallucinated thought? A tool call with the wrong arguments?

LangSmith locks you into LangChain. Langfuse gives you dashboards, not debuggers. Nobody offers *"turn back time and see exactly what the agent was thinking at step 23."*

## ✅ The Solution

AgentDebug is a lightweight SDK that instruments any agent — LangChain, CrewAI, AutoGen, or custom — and captures a structured **execution trace** of every thought, tool call, decision, and subagent state. Then replays it step-by-step, forward and backward, so you can inspect exactly what happened.

```python
from agent_debug import trace

@trace
def my_agent(prompt):
    return search(prompt) + analyze(prompt)
```

## Quick Start

```bash
pip install agent-debug
```

**Pattern 1: Decorator** — Zero-code-change tracing:

```python
from agent_debug import trace

@trace(name="research_agent", model="deepseek-chat")
def research(topic: str) -> dict:
    results = search(topic)
    analysis = analyze(results)
    return {"summary": analysis, "sources": results}
```

**Pattern 2: Context Manager** — Fine-grained control:

```python
from agent_debug import TraceInspector

with TraceInspector("my_agent") as inspector:
    inspector.log_step(1, "thinking", {"query": prompt})
    inspector.log_tool_call(1, "web_search", {"q": query}, results, duration_ms=450)
    inspector.log_output(final_result)
    inspector.save("trace.json")
```

**Pattern 3: CLI Replay:**

```bash
# Interactive replay
python -m agent_debug replay trace.json
# Commands: [Enter]=next, b=back, j=jump, v=inspect, s=summary, q=quit

# Quick summary
python -m agent_debug inspect trace.json

# Export to HTML report
python -m agent_debug export trace.json --html
```

**Pattern 4: Visual Dashboard:**

Open `dashboard/index.html` directly in any browser — no server needed.

## Features

| Feature | Description |
|---------|-------------|
| **🎯 Any Framework** | LangChain, CrewAI, AutoGen, custom agents. No lock-in. |
| **⏪ Step Back in Time** | Replay forward/backward. Jump to any step. |
| **🛠 Tool Call Inspection** | Every call captured: arguments, results, duration. |
| **🧩 Subagent State** | Full subagent state snapshots at each step. |
| **🌐 HTML Export** | Self-contained report for sharing and bug reports. |
| **⌨️ CLI + Dashboard** | Terminal or browser — your choice, no build step. |
| **📊 Token Tracking** | Automatic cost estimation per trace. |
| **📋 Schema Validation** | Every trace validated — no silent corruption. |

## Trace JSON Schema

```json
{
  "trace_id": "uuid",
  "agent_name": "research_agent",
  "timestamp": "2026-06-04T12:00:00+00:00",
  "steps": [
    {
      "step_index": 1,
      "phase": "thinking",
      "input": {"query": "AI safety"},
      "thought": "Parsing query and selecting search strategy.",
      "tool_calls": [],
      "subagent_state": null,
      "timestamp": "2026-06-04T12:00:01+00:00"
    },
    {
      "step_index": 2,
      "phase": "tool_call",
      "tool_calls": [
        {
          "tool": "web_search",
          "arguments": {"q": "AI safety 2026"},
          "result": {"results": [...]},
          "duration_ms": 450
        }
      ]
    }
  ],
  "output": {"answer": "..."},
  "metadata": {
    "model": "deepseek-chat",
    "total_duration_ms": 2850,
    "token_count": 1520
  }
}
```

## API Reference

### `@trace`

Decorator that wraps any function and captures execution traces.

```python
@trace                               # Auto-named from function name
@trace(name="agent", model="gpt-4")  # Custom name and model
@trace(save=True)                     # Auto-save trace after execution
```

### `TraceInspector`

Context manager for fine-grained trace capture.

```python
inspector = TraceInspector(
    agent_name="agent",
    trace_id="custom-id",  # Optional, auto-generated if omitted
    model="deepseek-chat",
    metadata={"key": "value"},  # Custom metadata
)
```

Methods:
- `log_step(step_index, phase, input_data=None, thought=None)` — Log a step. Returns a `_StepLogger` for chaining.
- `log_tool_call(step_index, tool, arguments, result=None, duration_ms=0)` — Log a tool call to a step.
- `log_output(output)` — Set the final output.
- `add_metadata(key, value)` — Add custom metadata.
- `save(path=None)` — Save trace to JSON. Defaults to `~/.agent_debug/traces/<trace_id>.json`.
- `to_json()` — Return trace as JSON string.
- `replay()` — Create a `ReplayEngine`.
- `export_html(path=None)` — Export as HTML report.
- `summary()` — Get summary dict.

### `ReplayEngine`

Step through a trace forward and backward.

```python
engine = ReplayEngine(trace)
engine.step_forward()          # Next step
engine.step_backward()         # Previous step
engine.go_to_step(5)           # Jump to step 5 (0-indexed)
engine.inspect_variables()     # Full state at current position
engine.get_summary()           # Trace statistics
engine.trace_info              # Metadata
```

### `load_trace(path)` / `list_traces()`

Load a trace from JSON or list all saved traces.

### `export_to_html(trace, output_path=None)`

Export a trace as a self-contained HTML report.

## CLI

```bash
# Interactive replay
agent-debug replay trace.json

# Quick summary
agent-debug inspect trace.json

# List all saved traces
agent-debug list

# Export to HTML
agent-debug export trace.json --html
```

Replay commands:

| Key | Action |
|-----|--------|
| `[Enter]` or `n` | Step forward |
| `b` | Step backward |
| `j` | Jump to a specific step |
| `v` | Inspect variables at current step |
| `s` | Show trace summary |
| `q` | Quit |

## Dashboard

Open `dashboard/index.html` directly in any browser. Features:

- **Trace file browser** — Open any `.json` trace from your filesystem
- **Replay view** — Step-by-step with forward/back/jump controls
- **Timeline view** — Full execution sequence in chronological order
- **Summary view** — Statistics, tool usage breakdown, final output
- **Keyboard shortcuts** — Arrow keys, Home/End for fast navigation

No server, no build step, no npm.

## Project Structure

```
AgentDebug/
├── sdk/
│   ├── agent_debug/           # Python package
│   │   ├── __init__.py        # Public API exports
│   │   ├── core.py            # @trace decorator + TraceInspector
│   │   ├── schema.py          # JSON schema validation
│   │   ├── replay.py          # ReplayEngine
│   │   ├── export.py          # HTML export
│   │   └── utils.py           # Timer, UUID, helpers
│   ├── setup.py               # PyPI setup
│   ├── pyproject.toml         # Modern packaging
│   └── README.md              # SDK docs
├── cli/
│   ├── agent_debug_cli.py     # CLI tool
│   └── README.md
├── dashboard/
│   └── index.html             # Single-file dashboard UI
├── examples/
│   ├── basic_usage.py         # @trace + TraceInspector examples
│   └── langchain_integration.py  # LangChain example
├── gumroad/
│   ├── description.html       # Gumroad listing description
│   └── cover_prompt.txt       # Cover image prompt for DALL-E
├── README.md                  # This file
└── LICENSE                    # MIT License
```

## Pricing

**$95 one-time. No subscriptions. No per-seat fees.**

| Tier | Price | Features |
|------|-------|----------|
| **Try Free** | $0 | 50 trace runs, full @trace + TraceInspector, replay forward/back, CLI, trial watermark |
| **AgentDebug SDK** | **$95** | **Unlimited tracing, HTML/JSON export, no watermark, all future updates** |

⚡ Try it 50 times for free. If you like it, buy once ($95) and own it forever.
License key delivered instantly after purchase — activate with `agent-debug activate <key>`.

[Buy on Gumroad →](https://empirelabs1.gumroad.com/l/agent-debug)

---

<div align="center">
  <p>Built by <a href="https://empirelabs.com.au"><strong>Empire Labs Pty Ltd</strong></a></p>
  <p>
    <a href="https://github.com/narko4u/agent-debug">GitHub</a> ·
    <a href="https://empirelabs1.gumroad.com/l/agent-debug">Gumroad</a> ·
    <a href="https://empirelabs.com.au">empirelabs.com.au</a>
  </p>
</div>
