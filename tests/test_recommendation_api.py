
import io

import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_pdf_bytes(text="Python FastAPI LangChain RAG"):
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def test_recommendations_from_resume():
    response = client.post(
        "/resume/recommendations",
        data={"location": "", "top_k": "3"},
        files={
            "file": (
                "resume.pdf",
                io.BytesIO(create_pdf_bytes()),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "python" in data["extracted_skills"]
    assert data["recommendation_count"] == 3

    recommendations = data["recommendations"]
    assert recommendations[0]["job_id"] == "JOB002"
    assert recommendations[0]["match_score"] == 100.0


def test_recommendations_filter_by_location():
    response = client.post(
        "/resume/recommendations",
        data={"location": "Chennai", "top_k": "3"},
        files={
            "file": (
                "resume.pdf",
                io.BytesIO(create_pdf_bytes()),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["recommendation_count"] == 1
    assert data["recommendations"][0]["location"] == "Chennai"


def test_recommendations_reject_non_pdf():
    response = client.post(
        "/resume/recommendations",
        data={"location": "", "top_k": "3"},
        files={
            "file": (
                "resume.txt",
                io.BytesIO(b"not a PDF"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_recommendations_reject_invalid_pdf():
    response = client.post(
        "/resume/recommendations",
        data={"location": "", "top_k": "3"},
        files={
            "file": (
                "resume.pdf",
                io.BytesIO(b"not a valid PDF"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400


def test_recommendations_reject_invalid_top_k():
    response = client.post(
        "/resume/recommendations",
        data={"location": "", "top_k": "0"},
        files={
            "file": (
                "resume.pdf",
                io.BytesIO(create_pdf_bytes()),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
