import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

load_dotenv()

# --- Define State ---
class BlogState(TypedDict):
    topic: str
    research_notes: str
    draft: str
    feedback: str
    revision_count: int
    approved: bool

# --- Instantiate the Gemini model ---
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.7)

# --- Agent 1: Researcher ---
def researcher_node(state: BlogState) -> dict:
    try:
        print("--- RUNNING RESEARCHER ---")
        prompt = ChatPromptTemplate.from_template(
            "You are an expert tech researcher. Provide a detailed structural blueprint, "
            "core data, and sub-sections for a high-quality blog post on the topic: {topic}"
        )
        chain = prompt | llm
        response = chain.invoke({"topic": state["topic"]})
        # FIXED: Using .text to handle Gemini 3 string response properly
        return {"research_notes": response.text}
    except Exception as e:
        print(f"ERROR IN RESEARCHER NODE: {e}")
        raise e

# --- Agent 2: Writer ---
def writer_node(state: BlogState) -> dict:
    try:
        print("--- RUNNING WRITER ---")
        feedback_context = ""
        if state.get("feedback"):
            feedback_context = f"\n\nAn Editor reviewed your previous draft and provided this feedback: {state['feedback']}\n Please rewrite the draft addressing these exact notes."

        prompt = ChatPromptTemplate.from_template(
            "You are an engaging tech copywriter. Write a comprehensive, SEO-optimized blog post "
            "using these research notes:\n"
            "{research_notes}\n"
            "{feedback_context}\n\n"
            "Output ONLY the final article raw content formatted inside clean HTML tags (such as <h2>, <p>, <ul>, etc.) wrapped inside a main `<div>` block. Do not use markdown syntax code blocks like ```html."
        )
        chain = prompt | llm
        response = chain.invoke({
            "research_notes": state["research_notes"],
            "feedback_context": feedback_context
        })
        
        # FIXED: Using .text to ensure we strip a clean string object
        clean_content = response.text.strip()
        if clean_content.startswith("```html"):
            clean_content = clean_content.replace("```html", "", 1)
        if clean_content.startswith("```"):
            clean_content = clean_content.replace("```", "", 1)
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        clean_content = clean_content.strip()

        current_revisions = state.get("revision_count", 0)
        return {"draft": clean_content, "revision_count": current_revisions + 1}
    except Exception as e:
        print(f"ERROR IN WRITER NODE: {e}")
        raise e

# --- Agent 3: Editor ---
def editor_node(state: BlogState) -> dict:
    try:
        print("--- RUNNING EDITOR ---")
        prompt = ChatPromptTemplate.from_template(
            "You are a strict Editor-in-Chief. Evaluate this blog post draft:\n\n{draft}\n\n"
            "If it meets professional publishing standards, is engaging, and cleanly structured, reply with EXACTLY the word 'APPROVED'.\n"
            "If it needs changes, provide clear, constructive feedback on what the writer must fix."
        )
        chain = prompt | llm
        response = chain.invoke({"draft": state["draft"]})
        # FIXED: Using .text to normalize content formatting
        decision = response.text.strip()
        
        if "APPROVED" in decision.upper():
            return {"approved": True, "feedback": ""}
        else:
            return {"approved": False, "feedback": decision}
    except Exception as e:
        print(f"ERROR IN EDITOR NODE: {e}")
        raise e

# --- Conditional Router Routing ---
def should_continue(state: BlogState):
    if state["approved"] or state["revision_count"] >= 3:
        return "end"
    return "rewrite"

# --- Building the Orchestration Graph ---
workflow = StateGraph(BlogState)

# Add Nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("editor", editor_node)

# Connect Edges
workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "editor")

# Define conditional edge mapping standard string keys
workflow.add_conditional_edges(
    "editor",
    should_continue,
    {
        "end": END,
        "rewrite": "writer"
    }
)

# Export the compiled graph
app_graph = workflow.compile()