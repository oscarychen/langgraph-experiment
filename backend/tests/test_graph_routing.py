from langchain_core.messages import AIMessage, HumanMessage

from hr_rag.config import settings
from hr_rag.rag.nodes import route_after_agent, route_after_grade, route_entry
from hr_rag.rag.state import _dedup_sources


def _ai_with_tool_calls(*tool_calls):
    msg = AIMessage(content="", tool_calls=list(tool_calls))
    return msg


def _tool_call(name: str, args: dict | None = None, call_id: str = "tc1"):
    return {"name": name, "args": args or {}, "id": call_id, "type": "tool_call"}


# ---- route_after_agent ----


def test_route_after_agent_no_tool_calls_returns_end():
    state = {"messages": [HumanMessage(content="hi"), AIMessage(content="hello")]}
    assert route_after_agent(state) == "end"


def test_route_after_agent_search_tool_routes_to_retrieve():
    state = {
        "messages": [
            HumanMessage(content="x"),
            _ai_with_tool_calls(
                _tool_call("search_hr_documents", {"query": "leave policy"})
            ),
        ]
    }
    assert route_after_agent(state) == "retrieve"


def test_route_after_agent_hr_tool_routes_to_tools():
    state = {
        "messages": [
            HumanMessage(content="x"),
            _ai_with_tool_calls(_tool_call("get_leave_balance", {"employee_id": "E"})),
        ]
    }
    assert route_after_agent(state) == "tools"


def test_route_after_agent_mixed_prioritizes_retrieve():
    state = {
        "messages": [
            HumanMessage(content="x"),
            _ai_with_tool_calls(
                _tool_call("get_leave_balance", {"employee_id": "E"}, "tc1"),
                _tool_call("search_hr_documents", {"query": "remote"}, "tc2"),
            ),
        ]
    }
    assert route_after_agent(state) == "retrieve"


def test_route_after_agent_empty_messages_returns_end():
    assert route_after_agent({"messages": []}) == "end"


# ---- route_after_grade ----


def test_route_after_grade_sufficient_to_agent():
    state = {
        "grade_verdict": "sufficient",
        "retrieval_attempts": 1,
        "retrieval_origin": "initial",
    }
    assert route_after_grade(state) == "agent"


def test_route_after_grade_insufficient_under_cap_retries():
    state = {
        "grade_verdict": "insufficient",
        "retrieval_attempts": 1,
        "retrieval_origin": "initial",
    }
    assert route_after_grade(state) == "retrieve"


def test_route_after_grade_insufficient_at_cap_falls_back_to_agent():
    state = {
        "grade_verdict": "insufficient",
        "retrieval_attempts": settings.max_retrieval_attempts,
        "retrieval_origin": "initial",
    }
    assert route_after_grade(state) == "agent"


def test_route_after_grade_ambiguous_on_initial_clarifies():
    state = {
        "grade_verdict": "ambiguous",
        "retrieval_attempts": 1,
        "retrieval_origin": "initial",
    }
    assert route_after_grade(state) == "clarify"


def test_route_after_grade_ambiguous_mid_conversation_downgrades_to_agent():
    state = {
        "grade_verdict": "ambiguous",
        "retrieval_attempts": 2,
        "retrieval_origin": "agent",
    }
    assert route_after_grade(state) == "agent"


def test_route_after_grade_attempts_cap_takes_priority_over_ambiguous():
    state = {
        "grade_verdict": "ambiguous",
        "retrieval_attempts": settings.max_retrieval_attempts,
        "retrieval_origin": "initial",
    }
    assert route_after_grade(state) == "agent"


# ---- route_entry ----


def test_route_entry_first_turn_goes_to_retrieve():
    state = {"messages": [HumanMessage(content="what's the leave policy?")]}
    assert route_entry(state) == "retrieve"


def test_route_entry_followup_skips_to_agent():
    state = {
        "messages": [
            HumanMessage(content="submit a vacation request"),
            AIMessage(content="That's less than 2 weeks notice. Submit anyway?"),
            HumanMessage(content="yes"),
        ]
    }
    assert route_entry(state) == "agent"


def test_route_entry_empty_messages_goes_to_retrieve():
    assert route_entry({"messages": []}) == "retrieve"


# ---- _dedup_sources reducer ----


def test_dedup_sources_appends_new():
    left = [{"source_uri": "a", "title": "A"}]
    right = [{"source_uri": "b", "title": "B"}]
    merged = _dedup_sources(left, right)
    assert [s["source_uri"] for s in merged] == ["a", "b"]


def test_dedup_sources_skips_existing():
    left = [{"source_uri": "a", "title": "A"}]
    right = [{"source_uri": "a", "title": "A-dup"}, {"source_uri": "c", "title": "C"}]
    merged = _dedup_sources(left, right)
    assert [s["source_uri"] for s in merged] == ["a", "c"]


def test_dedup_sources_handles_empty_right():
    left = [{"source_uri": "a", "title": "A"}]
    assert _dedup_sources(left, None) == left
    assert _dedup_sources(left, []) == left
