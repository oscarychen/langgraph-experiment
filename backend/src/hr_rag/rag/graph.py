from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from hr_rag.rag.llm import get_llm
from hr_rag.rag.tools import HR_TOOLS


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def build_agent_graph():
    llm = get_llm().bind_tools(HR_TOOLS)
    agent_node = (
        RunnableLambda(lambda state: state["messages"])
        | llm
        | RunnableLambda(lambda msg: {"messages": [msg]})
    )

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(HR_TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


agent_graph = build_agent_graph()
