
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

from app.jobs import search_jobs
from app.matching import match_resume

from app.agent import run_agent

from fastapi import HTTPException
from app.llm_parser import parse_recruitment_request

from app.semantic_search import semantic_search
from app.resume_api import router as resume_router
from app.recommendation_api import router as recommendation_router

app = FastAPI(
    title="Recruitment AI Agent API",
    description="Local recruitment search and skill-matching baseline",
    version="0.1.0",
    
)
app.include_router(resume_router)
app.include_router(recommendation_router)


class JobSearchRequest(BaseModel):
    query: str = ""
    location: str = ""


class MatchRequest(BaseModel):
    resume_skills: list[str] = Field(min_length=1)
    required_skills: list[str] = Field(min_length=1)

class AgentRequest(BaseModel):
    action: Literal["search", "match", "semantic_search"]
    query: str = ""
    location: str = ""
    resume_skills: list[str] = []
    required_skills: list[str] = []

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 3

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "project": "Recruitment AI Agent API",
        "stage": "baseline"
    }


@app.post("/jobs/search")
def jobs_search(request: JobSearchRequest):
    results = search_jobs(request.query, request.location)
    return {
        "count": len(results),
        "jobs": results
    }


@app.post("/jobs/match")
def jobs_match(request: MatchRequest):
    return match_resume(
        request.resume_skills,
        request.required_skills
    )

@app.post("/agent/chat")
def agent_chat(request: AgentRequest):
    return run_agent({
        "action": request.action,
        "message": request.query,
        "query": request.query,
        "location": request.location,
        "resume_skills": request.resume_skills,
        "required_skills": request.required_skills,
    })


@app.post("/agent/ask")
def agent_ask(request: dict):
    user_message = request.get("message", "")

    if not isinstance(user_message, str):
        raise HTTPException(
            status_code=422,
            detail="message must be a string."
        )

    try:
        intent = parse_recruitment_request(user_message)

        result = run_agent({
            "action": intent.action,
            "message": intent.query,
            "location": intent.location,
            "resume_skills": intent.resume_skills,
            "required_skills": intent.required_skills,
        })

        return {
            "interpreted_intent": intent.model_dump(),
            "result": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Do not expose internal exception details to API clients.
        raise HTTPException(
            status_code=502,
            detail="The local AI service or recruitment workflow failed."
        ) from exc


@app.post("/jobs/semantic-search")
def jobs_semantic_search(request: SemanticSearchRequest):
    try:
        results = semantic_search(
            query=request.query,
            top_k=request.top_k,
        )
        return {
            "count": len(results),
            "results": results,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
