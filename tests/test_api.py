
from fastapi.testclient import TestClient

from app.main import app
from app.matching import match_resume

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_search_jobs_by_skill():
    response = client.post(
        "/jobs/search",
        json={"query": "langchain", "location": ""}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert data["jobs"][0]["id"] == "JOB002"


def test_location_filter():
    response = client.post(
        "/jobs/search",
        json={"query": "", "location": "Chennai"}
    )

    assert response.status_code == 200
    assert all(
        job["location"] == "Chennai"
        for job in response.json()["jobs"]
    )


def test_resume_match():
    result = match_resume(
        ["Python", "FastAPI", "SQL"],
        ["Python", "FastAPI", "SQL", "Docker"]
    )

    assert result["match_score"] == 75.0
    assert result["matched_skills"] == [
        "fastapi", "python", "sql"
    ]
    assert result["missing_skills"] == ["docker"]


def test_empty_required_skills():
    result = match_resume(["Python"], [])
    assert result["match_score"] == 0.0
    assert result["missing_skills"] == []


def test_agent_chat_accepts_semantic_search(monkeypatch):
    expected = [{"job": {"id": "JOB001"}, "similarity": 0.9}]
    monkeypatch.setattr("app.agent.semantic_search", lambda query, top_k: expected)

    response = client.post(
        "/agent/chat",
        json={"action": "semantic_search", "query": "machine learning engineer"},
    )

    assert response.status_code == 200
    assert response.json() == expected
