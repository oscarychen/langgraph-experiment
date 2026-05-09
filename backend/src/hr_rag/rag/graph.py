from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class RAGState(TypedDict):
    question: str
    context: list[str]
    answer: str


def retrieve(state: RAGState) -> RAGState:
    # TODO: Implement retrieval from pgvector
    return {**state, "context": []}


def generate(state: RAGState) -> RAGState:
    # TODO: Implement LLM generation with context
    return {**state, "answer": "Not implemented"}


def build_rag_graph():
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


rag_chain = build_rag_graph()
