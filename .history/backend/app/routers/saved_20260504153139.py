from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, MatchAnalysis, Feedback
from app.security import get_current_user
from app.schemas import (SaveAnalysisRequest, SavedAnalysisResponse, FeedbackRequest, UpdateAnalysisRequest, ReorderAnalysisRequest)

router = APIRouter(prefix="/saved", tags=["saved"])
@router.post("/analysis", response_model=SavedAnalysisResponse)

def save_analysis(payload: SaveAnalysisRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = MatchAnalysis(
        user_id=current_user.id, 
        title=payload.title, 
        company=payload.company, 
        final_score=payload.final_score, 
        report_markdown=payload.report_markdown, 
        structured_report=payload.structured_report, 
        resume_text=payload.resume_text, 
        job_description=payload.job_description)
    db.add(row); db.commit(); db.refresh(row)
    return SavedAnalysisResponse(
        id=row.id, 
        title=row.title, 
        company=row.company, 
        final_score=row.final_score, 
        report_markdown=row.report_markdown)
@router.get("/analysis", response_model=list[SavedAnalysisResponse])

def list_saved(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(MatchAnalysis).filter(MatchAnalysis.user_id == current_user.id).order_by(MatchAnalysis.id.desc()).all()
    return [SavedAnalysisResponse(id=r.id, title=r.title, company=r.company, final_score=r.final_score, report_markdown=r.report_markdown) for r in rows]
@router.post("/feedback")

def create_feedback(payload: FeedbackRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = Feedback(user_id=current_user.id, match_analysis_id=payload.match_analysis_id, rating=payload.rating, applied=payload.applied, interview_received=payload.interview_received, user_notes=payload.user_notes)
    db.add(row); db.commit(); db.refresh(row); return {"id": row.id, "status": "saved"}
