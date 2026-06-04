"""LangChain integration example for AgentDebug SDK.
Shows how to wrap a LangChain agent to capture full execution traces.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk'))

from agent_debug import TraceInspector


def simulate_langchain_agent(query: str) -> str:
    """Simulate a LangChain agent with tool calls.
    
    In real usage, you would:
    1. Create your LangChain agent as normal
    2. Wrap the .run() or .invoke() call in a TraceInspector
    3. Hook into LangChain's callback system to capture steps
    """
    inspector = TraceInspector(
        agent_name="langchain-research-agent",
        model="gpt-4",
        metadata={"framework": "langchain", "version": "0.3.0"},
    )
    
    with inspector:
        # Step 1: Receive and parse query
        inspector.log_step(1, phase="thinking", input_data={"query": query},
                          thought="Parsing query and selecting tools.")
        
        # Step 2: Tool call - web search
        inspector.log_step(2, phase="tool_call")
        inspector.log_tool_call(
            "web_search",
            {"query": query, "engine": "google"},
            {"results": [{"title": "Result 1", "snippet": "..."}]},
            duration_ms=1200,
        )
        
        # Step 3: Tool call - document retrieval
        search_logger = inspector.log_step(3, phase="tool_call",
                                          thought="Processing search results and fetching documents.")
        search_logger.log_tool_call(
            "retrieve_docs",
            {"urls": ["https://example.com/doc1"]},
            {"documents": ["Document content here..."]},
            duration_ms=800,
        )
        search_logger.log_subagent_state({
            "subagent": "retriever",
            "chunks_retrieved": 5,
            "strategy": "semantic_search",
        })
        
        # Step 4: Decide on answer
        inspector.log_step(4, phase="deciding",
                          thought="Synthesizing information from all sources into coherent answer.")
        
        # Step 5: Generate output
        final = f"Answer to '{query}': Based on the research, the key finding is..."
        inspector.log_output(final)
    
    # Save trace for later replay
    inspector.save("langchain_trace.json")
    
    # Also export HTML report
    inspector.export_html("langchain_trace_report.html")
    print(f"  Exported HTML report to langchain_trace_report.html")
    
    return final


if __name__ == "__main__":
    print("=" * 60)
    print("LangChain Integration Example")
    print("=" * 60)
    
    result = simulate_langchain_agent("What are the latest AI safety developments?")
    print(f"\n  Result: {result[:80]}...")
    
    print("\n  Run the CLI to replay this trace:")
    print("  python cli/agent_debug_cli.py replay langchain_trace.json")
