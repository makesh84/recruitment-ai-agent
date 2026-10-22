
"""Fetch public job listings from configured Greenhouse and Lever boards."""

import html
import json
import os
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from app.job_ranking import rank_jobs


TIMEOUT_SECONDS = 15

CACHE_TTL_SECONDS = 300

_cache_lock = threading.Lock()
_jobs_cache = {
    "jobs": [],
    "expires_at": 0.0,
    "initialized": False,
}


def _get_cached_jobs() -> list[dict]:
    """Return cached provider listings, refreshing them every five minutes."""
    now = time.monotonic()

    with _cache_lock:
        if _jobs_cache["initialized"] and now < _jobs_cache["expires_at"]:
            return _jobs_cache["jobs"]

        jobs = _greenhouse_jobs() + _lever_jobs()

        # Retain the last successful cache if every provider fetch fails.
        if not jobs and _jobs_cache["jobs"]:
            _jobs_cache["expires_at"] = now + 30
            return _jobs_cache["jobs"]

        _jobs_cache["jobs"] = jobs
        _jobs_cache["expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
        _jobs_cache["initialized"] = True

        return _jobs_cache["jobs"]


def _get_json(url: str):
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "RecruitmentAI/1.0"},
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _plain_text(value) -> str:
    """Decode HTML entities and remove HTML tags from job descriptions."""
    text = str(value or "")

    # Decode HTML-encoded tags and entities.
    for _ in range(3):
        text = html.unescape(text)

    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace.
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()

def _greenhouse_jobs() -> list[dict]:
    results = []

    # Format: company-name:board-token,company-name:another-token
    boards = os.getenv("GREENHOUSE_BOARDS", "").split(",")

    for entry in filter(None, (item.strip() for item in boards)):
        if ":" not in entry:
            continue

        company, token = entry.split(":", 1)
        company, token = company.strip(), token.strip()
        if not company or not token:
            continue

        url = (
            "https://boards-api.greenhouse.io/v1/boards/"
            f"{quote(token, safe='')}/jobs?content=true"
        )

        try:
            payload = _get_json(url)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            continue

        for job in payload.get("jobs", []):
            location = (job.get("location") or {}).get("name", "")
            results.append({
                "id": f"greenhouse-{job.get('id')}",
                "title": job.get("title", ""),
                "company": company,
                "location": location,
                "required_skills": [],
                "description": _plain_text(job.get("content", "")),
                "url": job.get("absolute_url", ""),
                "source": "Greenhouse",
            })

    return results


def _lever_jobs() -> list[dict]:
    results = []

    # Format: company-name:site-name,company-name:another-site
    sites = os.getenv("LEVER_SITES", "").split(",")

    for entry in filter(None, (item.strip() for item in sites)):
        if ":" not in entry:
            continue

        company, site = entry.split(":", 1)
        company, site = company.strip(), site.strip()
        if not company or not site:
            continue

        url = f"https://api.lever.co/v0/postings/{quote(site, safe='')}?mode=json"

        try:
            payload = _get_json(url)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            continue

        if not isinstance(payload, list):
            continue

        for job in payload:
            categories = job.get("categories") or {}
            location = categories.get("location", "")
            description = job.get("descriptionPlain") or _plain_text(
                job.get("description", "")
            )

            results.append({
                "id": f"lever-{job.get('id')}",
                "title": job.get("text", ""),
                "company": company,
                "location": location,
                "required_skills": [],
                "description": description,
                "url": job.get("hostedUrl", ""),
                "source": "Lever",
            })

    return results





def exceeds_entry_level_experience(job: dict, max_years: int = 3) -> bool:
    """Return True when a job is senior or explicitly exceeds the experience limit."""
    import re

    title = str(job.get("title", "")).casefold()
    description = str(job.get("description", ""))
    text = f"{title}\n{description}".casefold()

    senior_terms = (
        "senior", "principal", "staff", "director", "head of",
        "vice president", "chief", "architect", "distinguished",
        "lead", "sr.",
    )

    if any(term in title for term in senior_terms):
        return True

    # Do not reject a job solely because experience is preferred.
    def is_preferred(match_start: int, match_end: int) -> bool:
        start = max(0, match_start - 100)
        end = min(len(text), match_end + 100)
        context = text[start:end]
        return bool(re.search(
            r"\b(preferred|preferably|ideally|bonus|nice to have)\b",
            context,
        ))

    # Ranges such as "0-2 years" or "2 to 5 years":
    # compare the upper end of the range with the limit.
    range_pattern = (
        r"\b(\d+)\s*(?:-|–|—|to)\s*(\d+)"
        r"\s*years?\s*(?:of\s+)?(?:relevant\s+|professional\s+)?"
        r"(?:experience|exp\b)"
    )

    for match in re.finditer(range_pattern, text):
        if is_preferred(match.start(), match.end()):
            continue
        if int(match.group(2)) > max_years:
            return True

    # Requirements such as "3+ years" and "4 years of experience".
    single_pattern = (
        r"\b(\d+)\s*(\+)?\s*years?\s+"
        r"(?:of\s+)?(?:relevant\s+|professional\s+|hands-on\s+)?"
        r"(?:experience|exp\b)"
    )

    for match in re.finditer(single_pattern, text):
        if is_preferred(match.start(), match.end()):
            continue

        years = int(match.group(1))
        has_plus = bool(match.group(2))

        if years > max_years:
            return True

    return False

def search_live_jobs(
    query: str = "",
    location: str = "",
    limit: int = 20,
    experience_level: str = "",
) -> dict:
    """Search live jobs and return a limited number of matches."""
    jobs = _greenhouse_jobs() + _lever_jobs()

    normalized_query = query.casefold().strip()
    terms = normalized_query.split()
    requested_location = location.strip().casefold()


    role_patterns = None

    if "ai engineer" in normalized_query or "artificial intelligence engineer" in normalized_query:
        role_patterns = (
            r"\bai\b.*\b(engineer|developer)\b",
            r"\bartificial intelligence\b.*\b(engineer|developer)\b",
            r"\bapplied ai\b.*\b(engineer|developer)\b",
            r"\b(ai|artificial intelligence)\b.*\b(specialist|associate)\b",
        )
    elif "machine learning" in normalized_query or normalized_query == "ml engineer":
        role_patterns = (
            r"\bmachine learning\b.*\b(engineer|developer|scientist|specialist|associate)\b",
            r"\bml\b.*\b(engineer|developer)\b",
        )
    elif any(term in normalized_query for term in ("genai", "generative ai", "llm")):
        role_patterns = (
            r"\b(generative ai|genai|llm|large language model)\b.*\b(engineer|developer|specialist|associate)\b",
            r"\b(engineer|developer)\b.*\b(generative ai|genai|llm)\b",
        )
    elif "mlops" in normalized_query:
        role_patterns = (
            r"\bmlops\b.*\b(engineer|developer)\b",
            r"\bml platform\b.*\bengineer\b",
            r"\bmachine learning operations\b.*\b(engineer|developer)\b",
        )
    elif "python" in normalized_query and any(
        term in normalized_query for term in ("developer", "engineer")
    ):
        role_patterns = (
            r"\bpython\b.*\b(developer|engineer)\b",
            r"\b(developer|engineer)\b.*\bpython\b",
        )


    if "ai engineer" in normalized_query or "artificial intelligence engineer" in normalized_query:
        role_patterns = (
            r"\bai\b.*\b(engineer|developer)\b",
            r"\bartificial intelligence\b.*\b(engineer|developer)\b",
            r"\bapplied ai\b.*\b(engineer|developer)\b",
        )
    elif "machine learning" in normalized_query or normalized_query == "ml engineer":
        role_patterns = (
            r"\bmachine learning\b.*\b(engineer|developer)\b",
            r"\bml\b.*\b(engineer|developer)\b",
        )
    elif "genai" in normalized_query or "generative ai" in normalized_query or "llm" in normalized_query:
        role_patterns = (
            r"\b(generative ai|genai|llm)\b.*\b(engineer|developer)\b",
            r"\b(engineer|developer)\b.*\b(generative ai|genai|llm)\b",
        )
    elif "mlops" in normalized_query:
        role_patterns = (
            r"\bmlops\b.*\bengineer\b",
            r"\bml platform\b.*\bengineer\b",
        )

    filtered = []

    for job in jobs:
        title = str(job.get("title", "")).casefold()
        searchable = " ".join([
            title,
            job.get("company", ""),
            job.get("location", ""),
            job.get("description", ""),
        ]).casefold()

        if role_patterns:
            if not any(re.search(pattern, title) for pattern in role_patterns):
                continue
        elif terms and not all(term in searchable for term in terms):
            continue

        
        job_location = str(job.get("location", "")).casefold()

        if requested_location:
            india_locations = (
                "india",
                "chennai",
                "coimbatore",
                "bengaluru",
                "bangalore",
                "hyderabad",
                "pune",
                "mumbai",
                "gurugram",
                "gurgaon",
                "noida",
                "new delhi",
            )

            if requested_location in {"india", "in"}:
                location_matches = any(
                    city in job_location for city in india_locations
                )
            else:
                location_matches = requested_location in job_location

            india_remote = (
                "remote" in job_location and "india" in job_location
            )

            if not location_matches and not india_remote:
                continue


        filtered.append(job)

    safe_limit = max(1, min(int(limit), 100))
    filtered = rank_jobs(
        filtered,
        query,
        experience_level=experience_level,
        location=location,
    )

    level = experience_level.casefold().strip()

    if level in {"entry", "entry-level", "0-3 years", "junior"}:
        filtered = [
            job for job in filtered
            if not exceeds_entry_level_experience(job, max_years=3)
        ]

    return {
        "source": "employer_ats",
        "count": len(filtered),
        "returned": min(len(filtered), safe_limit),
        "limit": safe_limit,
        "jobs": filtered[:safe_limit],
        "configured_boards": (
            len([
                x for x in os.getenv("GREENHOUSE_BOARDS", "").split(",")
                if x.strip()
            ])
            + len([
                x for x in os.getenv("LEVER_SITES", "").split(",")
                if x.strip()
            ])
        ),
    }
