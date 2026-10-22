
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END

from app.jobs import search_jobs
from app.matching import match_resume
from app.semantic_search import semantic_search


class AgentState(TypedDict, total=False):
    action: str
    message: str
    query: str
    location: str
    resume_skills: list[str]
    required_skills: list[str]
    result: dict | list
    route: str


def route_request(state: AgentState) -> AgentState:
    """Choose a recruitment tool using explicit request data."""
    action = state.get("action", "").strip().lower()

    if action == "match":
        return {"route": "match"}

    if action == "search":
        return {"route": "search"}

    if action == "semantic_search":
        return {"route": "semantic_search"}

    # Safe default: search unless matching inputs were supplied.
    if state.get("resume_skills") and state.get("required_skills"):
        return {"route": "match"}

    return {"route": "search"}


def search_node(state: AgentState) -> AgentState:
    """Search the sample job catalogue."""
    jobs = search_jobs(
        query=state.get("message", ""),
        location=state.get("location", ""),
    )

    return {
        "result": {
            "action": "search",
            "count": len(jobs),
            "jobs": jobs,
            "explanation": "Results returned by the job search tool."
        }
    }


def match_node(state: AgentState) -> AgentState:
    """Compare candidate skills with required job skills."""
    result = match_resume(
        resume_skills=state.get("resume_skills", []),
        required_skills=state.get("required_skills", []),
    )

    return {
        "result": {
            "action": "match",
            **result,
        }
    }


def semantic_search_node(state: AgentState) -> dict:
    query = state.get("query", "").strip()

    if not query:
        return {
            "result": [],
            "message": "Please provide a job search query.",
        }

    results = semantic_search(query, top_k=3)

    return {
        "result": results,
        "message": f"Found {len(results)} semantically relevant jobs.",
    }


def choose_tool(
    state: AgentState,
) -> Literal["search", "match", "semantic_search"]:
    return state["route"]


builder = StateGraph(AgentState)

builder.add_node("router", route_request)
builder.add_node("search", search_node)
builder.add_node("match", match_node)
builder.add_node("semantic_search", semantic_search_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    choose_tool,
    {
        "search": "search",
        "match": "match",
        "semantic_search": "semantic_search",
    },
)

builder.add_edge("search", END)
builder.add_edge("match", END)
builder.add_edge("semantic_search", END)

recruitment_agent = builder.compile()


def run_agent(request: dict) -> dict:
    """Run the recruitment workflow and return its result."""
    state = recruitment_agent.invoke(request)
    return state["result"]
