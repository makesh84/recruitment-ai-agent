"""Explainable job ranking for the Recruitment AI Agent."""

import re


ROLE_PATTERNS = {
    "ai engineer": (
        r"\bai\b.*\b(engineer|developer)\b",
        r"\bartificial intelligence\b.*\b(engineer|developer)\b",
        r"\bapplied ai\b.*\b(engineer|developer)\b",
        r"\b(ai|artificial intelligence)\b.*\b(specialist|associate)\b",
    ),
    "machine learning engineer": (
        r"\bmachine learning\b.*\b(engineer|developer)\b",
        r"\bml\b.*\b(engineer|developer)\b",
        r"\bmachine learning\b.*\b(scientist|specialist|associate)\b",
    ),
    "genai developer": (
        r"\b(generative ai|genai|llm|large language model)\b.*\b(engineer|developer)\b",
        r"\b(engineer|developer)\b.*\b(generative ai|genai|llm)\b",
        r"\b(llm|generative ai)\b.*\b(specialist|associate)\b",
    ),
    "mlops engineer": (
        r"\bmlops\b.*\b(engineer|developer)\b",
        r"\bml platform\b.*\bengineer\b",
        r"\b(machine learning operations)\b.*\b(engineer|developer)\b",
    ),
    "python developer": (
        r"\bpython\b.*\b(developer|engineer)\b",
        r"\b(developer|engineer)\b.*\bpython\b",
    ),
}


SENIOR_TITLE_TERMS = (
    "senior", "sr.", "staff", "principal", "lead",
    "director", "head of", "vice president", "vp ",
    "chief", "architect", "distinguished",
)

ENTRY_TITLE_TERMS = (
    "junior", "entry level", "entry-level", "graduate",
    "intern", "internship", "associate",
)

SKILL_ALIASES = {
    "python": ("python",),
    "machine learning": ("machine learning", " ml ", "ml engineer"),
    "deep learning": ("deep learning",),
    "pytorch": ("pytorch",),
    "tensorflow": ("tensorflow",),
    "fastapi": ("fastapi",),
    "langchain": ("langchain",),
    "langgraph": ("langgraph",),
    "llm": ("llm", "large language model", "large language models"),
    "generative ai": ("generative ai", "genai"),
    "rag": ("rag", "retrieval augmented generation"),
    "docker": ("docker",),
    "kubernetes": ("kubernetes", "k8s"),
    "sql": ("sql", "postgresql", "mysql"),
    "aws": ("aws", "amazon web services"),
}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def _skill_matches(text: str, skill: str) -> bool:
    aliases = SKILL_ALIASES.get(skill, (skill,))
    padded = f" {text} "
    return any(alias in padded for alias in aliases)


def _job_score(
    job: dict,
    query: str = "",
    experience_level: str = "",
    candidate_skills: list[str] | None = None,
) -> tuple[int, list[str], list[str]]:
    title = _normalize(job.get("title", ""))
    description = _normalize(job.get("description", ""))
    location = _normalize(job.get("location", ""))
    skills_text = _normalize(" ".join(job.get("required_skills") or []))
    query_text = _normalize(query)
    level = _normalize(experience_level)
    candidate_skills = candidate_skills or []

    score = 0
    reasons = []
    matched_skills = []

    # Role relevance: up to 35 points.
    if query_text and query_text in title:
        score += 25
        reasons.append("Job title closely matches the search")

    for role_name, patterns in ROLE_PATTERNS.items():
        if role_name in query_text and any(
            re.search(pattern, title) for pattern in patterns
        ):
            score += 10
            reasons.append("Job title matches the requested role")
            break

    # Skill relevance: up to 40 points.
    if candidate_skills:
        unique_skills = list(dict.fromkeys(
            _normalize(skill) for skill in candidate_skills if _normalize(skill)
        ))
        for skill in unique_skills:
            if _skill_matches(f"{skills_text} {description}", skill):
                matched_skills.append(skill)

        if unique_skills:
            score += round(40 * len(matched_skills) / len(unique_skills))
            if matched_skills:
                reasons.append("Matching skills: " + ", ".join(matched_skills))
    else:
        # Without a candidate skill list, reward search terms found in the job.
        query_terms = [
            term for term in query_text.split()
            if term not in {"engineer", "developer"}
        ]
        if query_terms:
            matches = sum(
                term in f"{title} {skills_text} {description}"
                for term in query_terms
            )
            score += round(40 * matches / len(query_terms))
            if matches:
                reasons.append("Search terms appear in the job details")

    # Experience fit: up to 15 points, using title signals only.
    is_senior = any(term in title for term in SENIOR_TITLE_TERMS)
    is_entry = any(term in title for term in ENTRY_TITLE_TERMS)

    if level in {"entry", "entry-level", "0-3 years", "junior"}:
        if is_entry:
            score += 15
            reasons.append("Title indicates an entry-level role")
        elif not is_senior:
            score += 8
            reasons.append("Title has no explicit seniority indicator")
    elif level in {"senior", "experienced"}:
        if is_senior:
            score += 15
            reasons.append("Title indicates an experienced role")
        else:
            score += 5

    # Location relevance: up to 10 points.
    requested_location = _normalize(job.get("_requested_location", ""))
    if requested_location and requested_location in location:
        score += 10
        reasons.append("Job location matches the requested location")

    return min(score, 100), reasons, matched_skills


def rank_jobs(
    jobs: list[dict],
    query: str = "",
    experience_level: str = "",
    candidate_skills: list[str] | None = None,
    location: str = "",
) -> list[dict]:
    """Return jobs ranked by a transparent heuristic match score."""
    ranked = []

    for original_job in jobs:
        job = dict(original_job)
        job["_requested_location"] = location

        score, reasons, matched_skills = _job_score(
            job,
            query=query,
            experience_level=experience_level,
            candidate_skills=candidate_skills,
        )

        job.pop("_requested_location", None)
        job["match_score"] = score
        job["match_reasons"] = reasons
        job["matched_skills"] = matched_skills
        ranked.append(job)

    return sorted(
        ranked,
        key=lambda job: (
            job["match_score"],
            _normalize(job.get("title", "")),
        ),
        reverse=True,
    )
