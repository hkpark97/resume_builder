from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, MatchAnalysis, Feedback
from app.security import get_current_user
from app.schemas import (
    SaveAnalysisRequest,
    SavedAnalysisResponse,
    FeedbackRequest,
    UpdateAnalysisRequest,
    ReorderAnalysisRequest,
)

router = APIRouter(prefix="/saved", tags=["saved"])


@router.post("/analysis", response_model=SavedAnalysisResponse)
def save_analysis(
    payload: SaveAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = MatchAnalysis(
        user_id=current_user.id,
        title=payload.title,
        company=payload.company,
        final_score=payload.final_score,
        report_markdown=payload.report_markdown,
        structured_report=payload.structured_report,
        resume_text=payload.resume_text,
        job_description=payload.job_description,
        sort_order=0,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return SavedAnalysisResponse(
        id=row.id,
        title=row.title,
        company=row.company,
        final_score=row.final_score,
        report_markdown=row.report_markdown,
        structured_report=row.structured_report,
        sort_order=row.sort_order,
    )


@router.get("/analysis", response_model=list[SavedAnalysisResponse])
def list_saved(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MatchAnalysis)
        .filter(MatchAnalysis.user_id == current_user.id)
        .order_by(MatchAnalysis.sort_order.asc(), MatchAnalysis.id.desc())
        .all()
    )

    return [
        SavedAnalysisResponse(
            id=row.id,
            title=row.title,
            company=row.company,
            final_score=row.final_score,
            report_markdown=row.report_markdown,
            structured_report=row.structured_report,
            sort_order=row.sort_order,
        )
        for row in rows
    ]


@router.patch("/analysis/{analysis_id}", response_model=SavedAnalysisResponse)
def update_saved_analysis(
    analysis_id: int,
    payload: UpdateAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(MatchAnalysis)
        .filter(
            MatchAnalysis.id == analysis_id,
            MatchAnalysis.user_id == current_user.id,
        )
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Saved analysis not found")

    if payload.title is not None:
        row.title = payload.title

    if payload.company is not None:
        row.company = payload.company

    db.commit()
    db.refresh(row)

    return SavedAnalysisResponse(
        id=row.id,
        title=row.title,
        company=row.company,
        final_score=row.final_score,
        report_markdown=row.report_markdown,
        structured_report=row.structured_report,
        sort_order=row.sort_order,
    )


@router.delete("/analysis/{analysis_id}")
def delete_saved_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(MatchAnalysis)
        .filter(
            MatchAnalysis.id == analysis_id,
            MatchAnalysis.user_id == current_user.id,
        )
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Saved analysis not found")

    db.delete(row)
    db.commit()

    return {"status": "deleted"}


@router.post("/analysis/reorder")
def reorder_saved_analysis(
    payload: ReorderAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MatchAnalysis)
        .filter(
            MatchAnalysis.user_id == current_user.id,
            MatchAnalysis.id.in_(payload.ordered_ids),
        )
        .all()
    )

    row_by_id = {row.id: row for row in rows}

    for index, analysis_id in enumerate(payload.ordered_ids):
        row = row_by_id.get(analysis_id)
        if row:
            row.sort_order = index

    db.commit()

    return {"status": "reordered"}


@router.post("/feedback")
def create_feedback(
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = Feedback(
        user_id=current_user.id,
        match_analysis_id=payload.match_analysis_id,
        rating=payload.rating,
        applied=payload.applied,
        interview_received=payload.interview_received,
        user_notes=payload.user_notes,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {"id": row.id, "status": "saved"}