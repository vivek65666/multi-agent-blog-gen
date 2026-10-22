"""Run the full LangGraph workflow with a fake LLM, so no API keys or network are needed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import EditorVerdict, build_graph  # noqa: E402
from state import initial_state  # noqa: E402


class Msg:
    def __init__(self, text):
        self.text = text


class FakeStructured:
    def __init__(self, verdicts):
        self.verdicts = list(verdicts)
        self.calls = 0

    def invoke(self, _prompt):
        self.calls += 1
        return self.verdicts.pop(0)


class FakeLLM:
    def __init__(self, verdicts):
        self.prompts = []
        self.editor = FakeStructured(verdicts)

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if "tech researcher" in prompt:
            return Msg("RESEARCH NOTES")
        return Msg("```html\n<div><h2>Title</h2><p>Body</p></div>\n```")

    def with_structured_output(self, _schema):
        return self.editor


def test_approved_first_try():
    llm = FakeLLM([EditorVerdict(score=9, approved=True, feedback="")])
    result = build_graph(llm, search_fn=None).invoke(initial_state("RAG"))
    assert result["approved"] is True
    assert result["revision_count"] == 1
    assert result["draft"] == "<div><h2>Title</h2><p>Body</p></div>"  # fences stripped


def test_editor_feedback_loops_back_to_writer():
    llm = FakeLLM([
        EditorVerdict(score=5, approved=False, feedback="Add a conclusion"),
        EditorVerdict(score=9, approved=True, feedback=""),
    ])
    result = build_graph(llm, search_fn=None).invoke(initial_state("RAG"))
    assert result["revision_count"] == 2
    assert result["approved"] is True
    assert any("Add a conclusion" in p for p in llm.prompts)  # feedback reached the writer


def test_low_score_blocks_approval_even_if_editor_says_approved():
    llm = FakeLLM([
        EditorVerdict(score=6, approved=True, feedback="Tighten intro"),
        EditorVerdict(score=9, approved=True, feedback=""),
    ])
    result = build_graph(llm, search_fn=None).invoke(initial_state("RAG"))
    assert result["revision_count"] == 2


def test_stops_at_max_revisions():
    llm = FakeLLM([EditorVerdict(score=3, approved=False, feedback="bad")] * 10)
    result = build_graph(llm, search_fn=None).invoke(initial_state("RAG"))
    assert result["revision_count"] == 3
    assert result["approved"] is False


def test_search_results_feed_researcher_and_sources():
    llm = FakeLLM([EditorVerdict(score=9, approved=True, feedback="")])
    search = lambda q: ("Source: X\nfact about " + q, ["https://example.com"])  # noqa: E731
    result = build_graph(llm, search_fn=search).invoke(initial_state("RAG"))
    assert result["sources"] == ["https://example.com"]
    assert "fact about RAG" in llm.prompts[0]


def test_search_failure_falls_back_to_llm():
    llm = FakeLLM([EditorVerdict(score=9, approved=True, feedback="")])

    def boom(_q):
        raise RuntimeError("tavily down")

    result = build_graph(llm, search_fn=boom).invoke(initial_state("RAG"))
    assert result["approved"] is True
    assert result["sources"] == []
