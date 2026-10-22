
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
    """Search jobs using flexible keyword and location matching."""
    query_terms = query.strip().lower().split()
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

        # Every query term must match somewhere in the job text.
        if query_terms and not all(
            term in searchable_text for term in query_terms
        ):
            continue

        if location and location not in job["location"].lower():
            continue

        results.append(job)

    return results