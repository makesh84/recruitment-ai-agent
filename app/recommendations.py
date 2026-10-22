
from app.jobs import JOBS
from app.matching import match_resume


def recommend_jobs(
    resume_skills: list[str],
    location: str = "",
    top_k: int = 3,
) -> list[dict]:
    """Rank sample jobs by candidate skill overlap."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    normalized_location = location.strip().lower()
    recommendations = []

    for job in JOBS:
        if (
            normalized_location
            and normalized_location not in job["location"].lower()
        ):
            continue

        match = match_resume(
            resume_skills,
            job["required_skills"],
        )

        recommendations.append({
            "job_id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "match_score": match["match_score"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "description": job["description"],
        })

    recommendations.sort(
        key=lambda item: (-item["match_score"], item["job_id"])
    )

    return recommendations[:top_k]
