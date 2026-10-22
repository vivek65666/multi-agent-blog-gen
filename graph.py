"""LangGraph workflow: Researcher -> Writer -> Editor (with a self-correcting loop).

The graph is built by `build_graph()` so the LLM and the search function can be
swapped out (used by the unit tests to run the whole workflow without API keys).
"""
import logging
import os
from typing import Callable, List, Optional, Tuple

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from state import BlogState

load_dotenv()
logger = logging.getLogger("blog_graph")

MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", "3"))
APPROVAL_SCORE = int(os.getenv("APPROVAL_SCORE", "8"))

# A search function takes a query and returns (notes_text, source_urls).
SearchFn = Callable[[str], Tuple[str, List[str]]]


class EditorVerdict(BaseModel):
    """Structured output the Editor agent must return."""

    score: int = Field(ge=1, le=10, description="Overall quality score from 1 (poor) to 10 (excellent)")
    approved: bool = Field(description="True only if the draft is ready to publish as-is")
    feedback: str = Field(description="Specific, actionable fixes for the writer. Empty if approved.")


def _text(response) -> str:
    """Return plain text from a LangChain message, across library versions."""
    text = getattr(response, "text", None)
    if callable(text):
        text = text()
    if isinstance(text, str):
        return text
    content = getattr(response, "content", response)
    if isinstance(content, list):  # list of content blocks
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


def _strip_code_fences(html: str) -> str:
    html = html.strip()
    if html.startswith("```html"):
        html = html[len("```html"):]
    elif html.startswith("```"):
        html = html[3:]
    if html.endswith("```"):
        html = html[:-3]
    return html.strip()


def default_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"), temperature=0.7
    )


def tavily_search(query: str) -> Tuple[str, List[str]]:
    """Search the live web with Tavily. Returns (notes, urls)."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    results = client.search(query=query, max_results=5, search_depth="basic").get("results", [])
    notes = "\n\n".join(f"Source: {r['title']} ({r['url']})\n{r['content']}" for r in results)
    return notes, [r["url"] for r in results]


def build_graph(llm=None, search_fn: Optional[SearchFn] = None):
    llm = llm or default_llm()
    if search_fn is None and os.getenv("TAVILY_API_KEY"):
        search_fn = tavily_search
    editor_llm = llm.with_structured_output(EditorVerdict)

    # --- Agent 1: Researcher -------------------------------------------------
    def researcher_node(state: BlogState) -> dict:
        logger.info("Researcher running for topic: %s", state["topic"])
        web_notes, sources = "", []
        if search_fn is not None:
            try:
                web_notes, sources = search_fn(state["topic"])
            except Exception:
                # Search is an enhancement, not a hard dependency: fall back to the LLM alone.
                logger.exception("Web search failed; continuing without live sources")

        grounding = (
            f"Use these live web search results as your factual basis:\n{web_notes}\n\n"
            if web_notes
            else ""
        )
        response = llm.invoke(
            "You are an expert tech researcher. Produce a detailed structural blueprint, "
            "core facts, and sub-sections for a high-quality blog post on the topic: "
            f"{state['topic']}\n\n{grounding}"
            "Do not invent statistics or sources."
        )
        return {"research_notes": _text(response), "sources": sources}

    # --- Agent 2: Writer -----------------------------------------------------
    def writer_node(state: BlogState) -> dict:
        logger.info("Writer running (revision %d)", state.get("revision_count", 0) + 1)
        feedback_context = ""
        if state.get("feedback"):
            feedback_context = (
                "\n\nAn Editor reviewed your previous draft and gave this feedback:\n"
                f"{state['feedback']}\nRewrite the draft addressing these exact notes."
            )
        response = llm.invoke(
            "You are an engaging tech copywriter. Write a comprehensive, SEO-optimized blog "
            f"post using these research notes:\n{state['research_notes']}\n{feedback_context}\n\n"
            "Output ONLY the final article as clean HTML tags (<h2>, <p>, <ul>, etc.) wrapped "
            "in a single <div>. Do not use markdown or code fences."
        )
        return {
            "draft": _strip_code_fences(_text(response)),
            "revision_count": state.get("revision_count", 0) + 1,
        }

    # --- Agent 3: Editor -----------------------------------------------------
    def editor_node(state: BlogState) -> dict:
        logger.info("Editor reviewing draft")
        verdict: EditorVerdict = editor_llm.invoke(
            "You are a strict Editor-in-Chief. Review this blog post draft for accuracy, "
            "structure, engagement and SEO. Score it 1-10, set approved=true only if it is "
            f"ready to publish, and otherwise give specific fixes.\n\n{state['draft']}"
        )
        approved = verdict.approved and verdict.score >= APPROVAL_SCORE
        return {
            "approved": approved,
            "score": verdict.score,
            "feedback": "" if approved else verdict.feedback,
        }

    # --- Conditional routing -------------------------------------------------
    def should_continue(state: BlogState) -> str:
        if state["approved"] or state["revision_count"] >= MAX_REVISIONS:
            return "end"
        return "rewrite"

    workflow = StateGraph(BlogState)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("editor", editor_node)

    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "editor")
    workflow.add_conditional_edges("editor", should_continue, {"end": END, "rewrite": "writer"})
    return workflow.compile()


_graph = None


def get_graph():
    """Build the production graph lazily so importing this module needs no API keys."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
