"""Basic usage examples for AgentDebug SDK.

Demonstrates the two main API patterns:
1. @trace decorator - simple automatic tracing
2. TraceInspector context manager - fine-grained control
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk'))

from agent_debug import trace, TraceInspector


# ---- Pattern 1: @trace decorator ----

@trace
def search_agent(query: str) -> str:
    """Simulate a simple search agent."""
    # Simulate thinking
    thought = f"Searching for: {query}"
    result = f"Results for '{query}': Found 3 relevant documents."
    return result


# ---- Pattern 2: @trace with custom name ----

@trace(name="research_agent", model="deepseek-chat")
def research_agent(topic: str) -> dict:
    """Simulate a research agent with multiple steps."""
    # Step 1: Search
    search_results = [f"Source {i}: Information about {topic}" for i in range(3)]
    
    # Step 2: Analyze
    analysis = {
        "topic": topic,
        "key_findings": ["Finding A", "Finding B", "Finding C"],
        "confidence": 0.85,
    }
    
    # Step 3: Summarize
    summary = f"Comprehensive analysis of {topic} with {len(search_results)} sources."
    
    return {
        "summary": summary,
        "sources": search_results,
        "analysis": analysis,
    }


# ---- Pattern 3: TraceInspector with tool calls and subagent state ----

def full_pipeline_example() -> str:
    """Demonstrate fine-grained tracing with tool calls and subagent state."""
    inspector = TraceInspector(
        agent_name="multi_step_agent",
        model="deepseek-chat",
        metadata={"pipeline": "research-v2", "version": "1.0.0"},
    )
    
    try:
        # Step 1: Receive query
        inspector.log_step(1, phase="thinking", input_data={
            "query": "What is the latest AI research?",
            "context": {"user_id": "123", "session": "abc"},
        }, thought="Analyzing query intent and extracting key terms.")
        
        # Step 2: Search web
        search_logger = inspector.log_step(2, phase="tool_call")
        search_logger.log_tool_call(
            tool="web_search",
            arguments={"query": "latest AI research 2026", "num_results": 5},
            result={"results": [
                {"title": "Paper 1", "url": "https://example.com/1"},
                {"title": "Paper 2", "url": "https://example.com/2"},
            ]},
            duration_ms=450,
        )
        search_logger.log_subagent_state({
            "subagent": "search-agent",
            "status": "completed",
            "tokens_used": 150,
        })
        
        # Step 3: Analyze results
        inspector.log_step(3, phase="deciding", thought="Cross-referencing top papers and ranking by relevance.")
        
        # Step 4: Generate response
        final_output = {
            "answer": "Recent AI research focuses on multi-agent systems and improved reasoning.",
            "sources": 2,
            "confidence": 0.92,
        }
        inspector.log_output(final_output)
        
        inspector.save("trace_example.json")
        return final_output["answer"]
        
    except Exception as e:
        inspector.log_step(99, phase="output", thought=f"Error occurred: {e}")
        inspector.log_output({"error": str(e)})
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("AgentDebug SDK - Basic Usage Examples")
    print("=" * 60)
    
    print("\n[Example 1] @trace decorator (simple):")
    result = search_agent("AI safety guidelines")
    print(f"  Result: {result}")
    
    print("\n[Example 2] @trace decorator (named):")
    result = research_agent("multi-agent systems")
    print(f"  Result: {result['summary'][:60]}...")
    
    print("\n[Example 3] TraceInspector (fine-grained):")
    result = full_pipeline_example()
    print(f"  Result: {result}")
    
    print("\n[Example 4] List saved traces:")
    from agent_debug import list_traces
    traces = list_traces()
    for t in traces:
        print(f"  - {t['agent_name']:20s} | {t['steps']} steps | {t['timestamp'][:19]}")
    
    print("\nAll examples completed successfully.")
