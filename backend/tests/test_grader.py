import pytest
from langchain_core.messages import HumanMessage

from hr_rag.rag import grader as grader_module
from hr_rag.rag import nodes as nodes_module
from hr_rag.rag.grader import GradeVerdict


class _FakeLLM:
    def __init__(self, verdict: GradeVerdict):
        self._verdict = verdict

    async def ainvoke(self, _prompt):
        return self._verdict


@pytest.fixture
def patch_grader(monkeypatch):
    def _set(verdict: GradeVerdict):
        monkeypatch.setattr(grader_module, "get_grader_llm", lambda: _FakeLLM(verdict))

    return _set


async def test_grade_node_sufficient_propagates_verdict(patch_grader):
    patch_grader(GradeVerdict(verdict="sufficient", reasoning="ok"))
    state = {
        "messages": [HumanMessage(content="How many vacation days?")],
        "retrieved_chunks": [{"chunk_text": "x", "title": "Leave", "similarity": 0.9}],
    }
    delta = await nodes_module.grade_node(state)
    assert delta["grade_verdict"] == "sufficient"
    assert delta["clarification_question"] is None


async def test_grade_node_insufficient_writes_refined_query(patch_grader):
    patch_grader(
        GradeVerdict(
            verdict="insufficient",
            refined_query="vacation accrual rate per month",
            reasoning="need rate",
        )
    )
    state = {
        "messages": [HumanMessage(content="How many vacation days?")],
        "retrieved_chunks": [],
    }
    delta = await nodes_module.grade_node(state)
    assert delta["grade_verdict"] == "insufficient"
    assert delta["last_query"] == "vacation accrual rate per month"
    assert delta["retrieval_origin"] == "retry"


async def test_grade_node_ambiguous_writes_clarification(patch_grader):
    patch_grader(
        GradeVerdict(
            verdict="ambiguous",
            clarification_question="Are you asking about vacation or sick leave?",
            reasoning="too vague",
        )
    )
    state = {
        "messages": [HumanMessage(content="What about leave?")],
        "retrieved_chunks": [],
    }
    delta = await nodes_module.grade_node(state)
    assert delta["grade_verdict"] == "ambiguous"
    assert "vacation" in delta["clarification_question"]


async def test_grade_retrieval_fails_open_on_llm_error(monkeypatch):
    class _BrokenLLM:
        async def ainvoke(self, _prompt):
            raise RuntimeError("boom")

    monkeypatch.setattr(grader_module, "get_grader_llm", lambda: _BrokenLLM())
    verdict = await grader_module.grade_retrieval("q", [])
    assert verdict.verdict == "sufficient"
    assert verdict.reasoning == "grader_error"
