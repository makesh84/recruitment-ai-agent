
def match_resume(
    resume_skills: list[str],
    required_skills: list[str]
) -> dict:
    """
    Calculate skill overlap.

    This is a transparent baseline score, not a hiring probability.
    """
    candidate = {
        skill.strip().lower()
        for skill in resume_skills
        if skill.strip()
    }
    required = {
        skill.strip().lower()
        for skill in required_skills
        if skill.strip()
    }

    if not required:
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "message": "No required skills were provided."
        }

    matched = sorted(candidate & required)
    missing = sorted(required - candidate)
    score = round(len(matched) / len(required) * 100, 2)

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "message": (
            "Skill overlap calculated. Review experience and "
            "other job requirements separately."
        )
    }
