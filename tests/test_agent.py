
from app.agent import run_agent


def test_agent_routes_to_semantic_search(monkeypatch):
    expected = [{"job": {"id": "JOB001"}, "similarity": 0.9}]
    monkeypatch.setattr("app.agent.semantic_search", lambda query, top_k: expected)

    result = run_agent({
        "action": "semantic_search",
        "query": "machine learning engineer",
    })

    assert result == expected


def test_agent_search_routes_to_job_tool():
    result = run_agent({
        "action": "search",
        "message": "langchain",
        "location": "",
    })

    assert result["action"] == "search"
    assert result["count"] == 1
    assert result["jobs"][0]["id"] == "JOB002"


def test_agent_routes_to_matching_tool():
    result = run_agent({
        "action": "match",
        "resume_skills": ["Python", "FastAPI"],
        "required_skills": ["Python", "FastAPI", "Docker"],
    })

    assert result["action"] == "match"
    assert result["match_score"] == 66.67
    assert result["missing_skills"] == ["docker"]
