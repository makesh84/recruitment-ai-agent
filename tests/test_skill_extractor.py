
from app.skill_extractor import extract_skills


def test_extracts_known_skills():
    text = """
    Skills: Python, FastAPI, LangChain, Docker, AWS
    Built a RAG application using large language models.
    """

    skills = extract_skills(text)

    assert "python" in skills
    assert "fastapi" in skills
    assert "langchain" in skills
    assert "docker" in skills
    assert "aws" in skills
    assert "rag" in skills
    assert "llm" in skills


def test_returns_unique_skills():
    skills = extract_skills("Python developer with Python experience")

    assert skills.count("python") == 1


def test_empty_resume_returns_empty_list():
    assert extract_skills("") == []
    assert extract_skills("   ") == []


def test_does_not_match_partial_words():
    assert extract_skills("I enjoy pythonista articles") == []
