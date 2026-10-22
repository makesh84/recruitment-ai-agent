
import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.resume_parser import extract_resume_text
from app.skill_extractor import extract_skills

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/resume/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Upload a PDF resume.",
        )

    temp_path = None

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Resume must be 5 MB or smaller.",
            )

        # Check the PDF signature; this alone does not prove a PDF is valid.
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid PDF.",
            )

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        text = extract_resume_text(temp_path)
        skills = extract_skills(text)

        return {
            "filename": os.path.basename(file.filename),
            "text_length": len(text),
            "skills": skills,
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        await file.close()
