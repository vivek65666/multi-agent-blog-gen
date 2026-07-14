from typing import TypedDict

class BlogState(TypedDict):
    topic: str
    research_notes: str
    draft: str
    feedback: str
    revision_count: int
    approved: bool