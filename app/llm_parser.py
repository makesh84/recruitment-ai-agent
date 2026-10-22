
import json
import os
import re
import ollama

from pydantic import BaseModel, Field, ValidationError
from typing import Literal


class RecruitmentIntent(BaseModel):
    action: Literal["search", "match"]
    query: str = ""
    location: str = ""
    resume_skills: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)


def parse_recruitment_request(
    user_message: str,
) -> RecruitmentIntent:
    """Convert a natural-language request into validated fields."""

    if not user_message.strip():
        raise ValueError("Request cannot be empty.")

    if len(user_message) > 2000:
        raise ValueError("Request is too long (maximum 2000 characters).")

    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    prompt = f"""
You convert recruitment requests into structured JSON.

Choose exactly one action:
- search: find jobs by role, skill, keyword, or location.
- match: compare candidate skills with explicit job requirements.

Rules:
- Do not answer the user's question.
- Do not invent jobs, skills, or candidate qualifications.
- For search, put a concise role or skill keyword in query.
- Extract a location only if the user specifies one.
- For match, extract candidate skills and required skills only
  when they are explicitly supplied.
- Return empty strings or empty lists for unknown fields.
- Return JSON matching the supplied schema.

User request:
{user_message}
"""

    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Extract recruitment intent. Return structured data only."
            },
            {"role": "user", "content": prompt},
        ],
        format=RecruitmentIntent.model_json_schema(),
        options={"temperature": 0},
    )

    content = response["message"]["content"]

    try:
        intent = RecruitmentIntent.model_validate_json(content)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        # Do not pass malformed LLM output to the workflow.
        raise ValueError("The model returned invalid intent data.") from exc

    # Search must have a usable query. A location-only request is valid.
    if intent.action == "search":
        if not intent.query.strip() and not intent.location.strip():
            raise ValueError("Please specify a job role, skill, or location.")

    if intent.action == "match":
        if not intent.resume_skills or not intent.required_skills:
            raise ValueError(
                "Matching requires candidate skills and job requirements."
            )

    return intent
