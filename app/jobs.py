
JOBS = [
    {
        "id": "JOB001",
        "title": "Junior AI Engineer",
        "company": "Sample AI Labs",
        "location": "Chennai",
        "required_skills": ["python", "fastapi", "machine learning", "sql"],
        "description": "Build and integrate machine learning applications."
    },
    {
        "id": "JOB002",
        "title": "Generative AI Developer",
        "company": "Sample GenAI Systems",
        "location": "Remote",
        "required_skills": ["python", "langchain", "rag", "fastapi"],
        "description": "Develop LLM applications and retrieval systems."
    },
    {
        "id": "JOB003",
        "title": "MLOps Engineer",
        "company": "Sample Cloud AI",
        "location": "Coimbatore",
        "required_skills": ["python", "docker", "mlflow", "aws"],
        "description": "Build model deployment and experiment tracking pipelines."
    }
]


def search_jobs(query: str = "", location: str = "") -> list[dict]:
    """Search sample jobs by title, description, skill, company or location."""
    query = query.strip().lower()
    location = location.strip().lower()
    results = []

    for job in JOBS:
        searchable_text = " ".join([
            job["title"],
            job["company"],
            job["description"],
            " ".join(job["required_skills"]),
            job["location"],
        ]).lower()

        if query and query not in searchable_text:
            continue

        if location and location not in job["location"].lower():
            continue

        results.append(job)

    return results
