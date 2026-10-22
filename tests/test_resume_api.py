
import io

import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_pdf_bytes(text="Python FastAPI LangChain Docker AWS RAG"):
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def test_resume_analyze_success():
    pdf_content = create_pdf_bytes()

    response = client.post(
        "/resume/analyze",
        files={
            "file": (
                "resume.pdf",
                io.BytesIO(pdf_content),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "resume.pdf"
    assert data["text_length"] > 0
    assert "python" in data["skills"]
    assert "fastapi" in data["skills"]
    assert "langchain" in data["skills"]


def test_resume_analyze_rejects_non_pdf():
    response = client.post(
        "/resume/analyze",
        files={
            "file": (
                "resume.txt",
                io.BytesIO(b"not a PDF"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_resume_analyze_rejects_invalid_pdf():
    response = client.post(
        "/resume/analyze",
        files={
            "file": (
                "resume.pdf",
                io.BytesIO(b"not a real PDF"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
