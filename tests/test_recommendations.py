
import pytest

from app.recommendations import recommend_jobs


def test_recommendations_rank_best_skill_match_first():
    results = recommend_jobs(
        ["python", "fastapi", "langchain", "rag"],
    )

    assert len(results) == 3
    assert results[0]["job_id"] == "JOB002"
    assert results[0]["match_score"] == 100.0


def test_recommendations_return_missing_skills():
    results = recommend_jobs(["python"])

    first_job = next(
        job for job in results if job["job_id"] == "JOB001"
    )

    assert first_job["matched_skills"] == ["python"]
    assert first_job["missing_skills"] == [
        "fastapi",
        "machine learning",
        "sql",
    ]
    assert first_job["match_score"] == 25.0


def test_recommendations_filter_by_location():
    results = recommend_jobs(["python"], location="Chennai")

    assert len(results) == 1
    assert results[0]["job_id"] == "JOB001"


def test_recommendations_respect_top_k():
    results = recommend_jobs(["python"], top_k=2)

    assert len(results) == 2


def test_recommendations_reject_invalid_top_k():
    with pytest.raises(ValueError):
        recommend_jobs(["python"], top_k=0)
