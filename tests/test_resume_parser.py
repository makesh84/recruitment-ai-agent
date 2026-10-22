
import fitz
import pytest

from app.resume_parser import extract_resume_text


def create_pdf(path, text="Python FastAPI Machine Learning"):
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_extract_resume_text(tmp_path):
    pdf_path = tmp_path / "resume.pdf"
    create_pdf(pdf_path)

    text = extract_resume_text(str(pdf_path))

    assert "Python" in text
    assert "FastAPI" in text


def test_reject_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_resume_text(str(tmp_path / "missing.pdf"))


def test_reject_non_pdf(tmp_path):
    file_path = tmp_path / "resume.txt"
    file_path.write_text("Sample resume")

    with pytest.raises(ValueError, match="Only PDF"):
        extract_resume_text(str(file_path))


def test_reject_empty_text_pdf(tmp_path):
    pdf_path = tmp_path / "blank.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    with pytest.raises(ValueError, match="No selectable text"):
        extract_resume_text(str(pdf_path))
