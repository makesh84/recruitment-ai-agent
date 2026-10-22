
import re


SKILL_ALIASES = {
    "python": ["python"],
    "fastapi": ["fastapi"],
    "sql": ["sql", "mysql", "postgresql", "postgres"],
    "machine learning": ["machine learning", "scikit-learn", "sklearn"],
    "deep learning": ["deep learning", "pytorch", "tensorflow", "keras"],
    "generative ai": ["generative ai", "genai"],
    "llm": ["llm", "llms", "large language model", "large language models"],
    "rag": ["rag", "retrieval augmented generation"],
    "langchain": ["langchain"],
    "faiss": ["faiss"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes"],
    "mlflow": ["mlflow"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud platform"],
    "opencv": ["opencv"],
    "computer vision": ["computer vision"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
}


def extract_skills(resume_text: str) -> list[str]:
    """Return recognized canonical skill names from resume text."""
    if not resume_text or not resume_text.strip():
        return []

    normalized_text = resume_text.lower()
    found = []

    for canonical_name, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = rf"(?<!\w){re.escape(alias.lower())}(?!\w)"

            if re.search(pattern, normalized_text):
                found.append(canonical_name)
                break

    return sorted(found)
