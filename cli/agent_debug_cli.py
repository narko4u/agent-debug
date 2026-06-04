#!/usr/bin/env python3
"""AgentDebug CLI — Command-line tool for inspecting and replaying traces.

Usage:
    agent-debug replay <trace.json>         Interactive replay
    agent-debug inspect <trace.json>        Summary view
    agent-debug list                        List all traces
    agent-debug export <trace.json> --html  Export to HTML
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import the SDK
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))

from agent_debug import (
    load_trace,
    ReplayEngine,
    list_traces,
    export_to_html,
)


def cmd_replay(args: argparse.Namespace) -> None:
    """Interactive trace replay."""
    try:
        trace = load_trace(args.trace_path)
    except FileNotFoundError:
        print(f"Error: File not found: {args.trace_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in trace file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading trace: {e}")
        sys.exit(1)

    engine = ReplayEngine(trace)
    info = engine.trace_info

    print()
    print(f"  {'='*60}")
    print(f"  AgentDebug Replay — {info['agent_name']}")
    print(f"  {'='*60}")
    print(f"  Trace ID: {info['trace_id']}")
    print(f"  Timestamp: {info['timestamp']}")
    print(f"  Total Steps: {info['total_steps']}")
    print(f"  Model: {info.get('metadata', {}).get('model', 'N/A')}")
    print()

    if engine.total_steps == 0:
        print("  No steps recorded in this trace.")
        return

    print("  Commands: [enter]=next, [b]=back, [j]=jump, [v]=inspect")
    print("            [s]=summary, [q]=quit")
    print()

    while True:
        try:
            cmd = input(f"  [{engine.progress}] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting replay.")
            break

        if cmd == "" or cmd == "n":
            step = engine.step_forward()
            if step is None:
                if engine.is_at_end:
                    print("  [End of trace reached]")
                else:
                    print("  [No more steps]")
            else:
                _print_step(engine, step)
        elif cmd == "b":
            step = engine.step_backward()
            if step is None:
                print("  [At beginning of trace]")
            else:
                print(f"  [Back to step {engine.current_step_index + 1}]")
                _print_step(engine, step)
        elif cmd == "j":
            try:
                idx = int(input("  Jump to step #: ").strip())
                step = engine.go_to_step(idx - 1)  # Convert to 0-based
                if step is None:
                    print(f"  [Step {idx} out of range (1-{engine.total_steps})]")
                else:
                    _print_step(engine, step)
            except (ValueError, EOFError):
                print("  Invalid step number.")
        elif cmd == "v":
            vars_ = engine.inspect_variables()
            _print_variables(vars_)
        elif cmd == "s":
            _print_summary(engine)
        elif cmd == "q":
            print("  Exiting replay.")
            break
        else:
            print("  Unknown command. Use [enter], b, j, v, s, q.")


def _print_step(engine: ReplayEngine, step: dict) -> None:
    """Print a single step nicely."""
    phase = step.get("phase", "unknown").upper()
    step_idx = step.get("step_index", engine.current_step_index + 1)

    print(f"\n  --- Step {step_idx}: {phase} ---")

    thought = step.get("thought")
    if thought:
        print(f"  Thought: {_truncate(thought, 200)}")

    inp = step.get("input")
    if inp:
        print(f"  Input: {_truncate(str(inp), 200)}")

    tool_calls = step.get("tool_calls", [])
    if tool_calls:
        print(f"  Tool calls ({len(tool_calls)}):")
        for tc in tool_calls:
            tool_name = tc.get("tool", "?")
            duration = tc.get("duration_ms", 0)
            print(f"    🛠 {tool_name} ({duration}ms)")

    subagent = step.get("subagent_state")
    if subagent:
        print(f"  Subagent state: {_truncate(str(subagent), 150)}")

    print()


def _print_variables(vars_: dict) -> None:
    """Print variable inspection output."""
    print("\n  --- Variable Inspection ---")
    print(f"  Step: {vars_.get('step_index', 'N/A')}")
    print(f"  Phase: {vars_.get('phase', 'N/A')}")

    if vars_.get("input"):
        print(f"  Input: {json.dumps(vars_['input'], indent=2, default=str)[:300]}")

    if vars_.get("thought"):
        print(f"  Thought: {vars_['thought'][:300]}")

    tool_calls = vars_.get("tool_calls", [])
    if tool_calls:
        print(f"  Tool Calls ({len(tool_calls)}):")
        for tc in tool_calls:
            print(f"    Tool: {tc.get('tool', '?')}")
            print(f"    Args: {json.dumps(tc.get('arguments', {}), default=str)[:200]}")

    if vars_.get("subagent_state"):
        print(f"  Subagent: {json.dumps(vars_['subagent_state'], default=str)[:300]}")

    print()


def _print_summary(engine: ReplayEngine) -> None:
    """Print trace summary."""
    summary = engine.get_summary()
    print("\n  --- Trace Summary ---")
    print(f"  Agent: {summary['agent_name']}")
    print(f"  Trace: {summary['trace_id']}")
    print(f"  Steps: {summary['total_steps']}")
    print(f"  Tool Calls: {summary['total_tool_calls']}")
    print(f"  Duration: {summary['total_duration_ms']}ms")
    print(f"  Model: {summary['model']}")
    print(f"  Tokens: {summary['token_count']}")
    if summary["tool_usage"]:
        print(f"  Tool Usage:")
        for tool, count in summary["tool_usage"].items():
            print(f"    {tool}: {count}x")
    print()


def cmd_inspect(args: argparse.Namespace) -> None:
    """Print a summary of a trace file."""
    try:
        trace = load_trace(args.trace_path)
    except FileNotFoundError:
        print(f"Error: File not found: {args.trace_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    engine = ReplayEngine(trace)
    _print_summary(engine)


def cmd_list(args: argparse.Namespace) -> None:
    """List all traces in default or specified directory."""
    traces = list_traces(args.traces_dir)

    if not traces:
        print("No traces found.")
        return

    print(f"\n  Traces ({len(traces)} found):")
    print(f"  {'='*60}")
    for t in traces:
        print(f"  {t['agent_name']:20s} | {t['timestamp'][:19]:19s} | {t['steps']:3d} steps | {t['trace_id'][:8]}...")
        print(f"  {'':20s}   {t['path']}")
        print()


def cmd_export(args: argparse.Namespace) -> None:
    """Export a trace to HTML."""
    try:
        trace = load_trace(args.trace_path)
    except FileNotFoundError:
        print(f"Error: File not found: {args.trace_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    output_path = args.output or args.trace_path.replace(".json", ".html")

    try:
        export_to_html(trace, output_path)
        print(f"Exported to {output_path}")
    except Exception as e:
        print(f"Error exporting: {e}")
        sys.exit(1)


def _truncate(text: str, max_len: int) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AgentDebug CLI — Agent Execution Inspector & Replay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-debug replay trace.json          Interactive replay
  agent-debug inspect trace.json         Summary view
  agent-debug list                       List all traces
  agent-debug export trace.json --html   Export to HTML
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Interactive trace replay")
    replay_parser.add_argument("trace_path", help="Path to trace JSON file")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Trace summary view")
    inspect_parser.add_argument("trace_path", help="Path to trace JSON file")

    # List command
    list_parser = subparsers.add_parser("list", help="List all traces")
    list_parser.add_argument(
        "--traces-dir",
        "-d",
        help="Custom traces directory (default: ~/.agent_debug/traces/)",
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export trace to HTML")
    export_parser.add_argument("trace_path", help="Path to trace JSON file")
    export_parser.add_argument("--output", "-o", help="Output HTML path")
    export_parser.add_argument("--html", action="store_true", help="Export to HTML format", default=True)

    args = parser.parse_args()

    if args.command == "replay":
        cmd_replay(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
