from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from hr_rag.config import settings
from hr_rag.rag.nodes import (
    agent_node,
    clarify_node,
    grade_node,
    retrieve_node,
    route_after_agent,
    route_after_grade,
    route_entry,
)
from hr_rag.rag.state import AgentState
from hr_rag.rag.tools import HR_TOOLS


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("agent", agent_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("tools", ToolNode(HR_TOOLS))

    graph.add_conditional_edges(
        START,
        route_entry,
        {"retrieve": "retrieve", "agent": "agent"},
    )
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        route_after_grade,
        {"agent": "agent", "retrieve": "retrieve", "clarify": "clarify"},
    )
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {"retrieve": "retrieve", "tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("clarify", END)

    compiled = graph.compile()
    compiled = compiled.with_config(
        recursion_limit=settings.max_retrieval_attempts * 4 + 16
    )
    return compiled


agent_graph = build_agent_graph()
