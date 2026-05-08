import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.parser import parse_upload
from app.services.analyzer import analyze_resume_job
from app.schemas import PublicAnalyzeResponse

router = APIRouter(prefix="/public", tags=["public"])


def _parse_uploaded_file(upload_file: UploadFile) -> str:
    suffix = Path(upload_file.filename or "upload.txt").suffix.lower() or ".txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload_file.file.read())
        tmp_path = tmp.name

    try:
        return parse_upload(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/analyze", response_model=PublicAnalyzeResponse)
def public_analyze(
    resume_file: UploadFile = File(...),
    job_file: UploadFile | None = File(None),
    job_title: str = Form(""),
    company: str = Form(""),
    job_description: str = Form(""),
):
    resume_text = _parse_uploaded_file(resume_file)

    if len(resume_text.strip()) < 30:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough text from resume.",
        )

    job_text = ""

    if job_file is not None:
        job_text = _parse_uploaded_file(job_file)

    if not job_text.strip():
        job_text = job_description.strip()

    if len(job_text.strip()) < 30:
        raise HTTPException(
            status_code=400,
            detail="Please paste a job description or upload a job posting file.",
        )

    result = analyze_resume_job(
        resume_text=resume_text,
        job_description=job_text,
        job_title=job_title,
        company=company,
    )

    return PublicAnalyzeResponse(
        final_score=result.get("final_score", 0),
        summary=result.get("summary", ""),
        report_markdown=result.get("report_markdown", ""),
        structured_report=result,
    )