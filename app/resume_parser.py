
from pathlib import Path

import pymupdf


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def extract_resume_text(file_path: str) -> str:
    """Extract selectable text from a PDF resume stored on disk."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("Resume file was not found.")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF resumes are supported.")

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("Resume PDF must be 5 MB or smaller.")

    if path.stat().st_size == 0:
        raise ValueError("Resume PDF is empty.")

    try:
        with pymupdf.open(path) as document:
            if document.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            text = "\n".join(
                page.get_text() for page in document
            )

    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("The PDF could not be read.") from exc

    if not text.strip():
        raise ValueError(
            "No selectable text found. Scanned PDFs need OCR."
        )

    return text.strip()
