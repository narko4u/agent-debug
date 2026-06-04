# AgentDebug CLI

Command-line tool for inspecting and replaying agent traces without a UI.

## Usage

```bash
# Interactive replay of a trace
python agent_debug_cli.py replay trace.json

# Quick summary of a trace
python agent_debug_cli.py inspect trace.json

# List all traces in the default directory
python agent_debug_cli.py list

# Export trace to HTML report
python agent_debug_cli.py export trace.json --output report.html
```

## Interactive Replay Commands

| Key | Action |
|-----|--------|
| `[Enter]` or `n` | Step forward |
| `b` | Step backward |
| `j` | Jump to a specific step |
| `v` | Inspect variables at current step |
| `s` | Show trace summary |
| `q` | Quit |

## Installation

The CLI depends on the `agent_debug` SDK package. Either:

1. Install the SDK: `pip install agent-debug` (when published), or
2. Run from the repo: the CLI auto-adds `../sdk` to the Python path.
