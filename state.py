from typing import List, TypedDict


class BlogState(TypedDict):
    """Shared state passed between the Researcher, Writer and Editor agents."""

    topic: str
    research_notes: str
    sources: List[str]  # URLs used by the researcher (empty if search was unavailable)
    draft: str
    feedback: str
    score: int  # editor quality score, 1-10
    revision_count: int
    approved: bool


def initial_state(topic: str) -> BlogState:
    return {
        "topic": topic,
        "research_notes": "",
        "sources": [],
        "draft": "",
        "feedback": "",
        "score": 0,
        "revision_count": 0,
        "approved": False,
    }
