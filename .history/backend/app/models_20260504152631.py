from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON, Boolean
from sqlalchemy.sql import func
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MatchAnalysis(Base):
    __tablename__ = "match_analyses"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    
    final_score = Column(Float, nullable=False)
    report_markdown = Column(Text, nullable=False)
    structured_report = Column(JSON, nullable=True)
    
    sort_order = Column(Integer, default=0)
    
    resume_text = Column(Text, nullable=True)
    job_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_analysis_id = Column(Integer, ForeignKey("match_analyses.id"), nullable=True)
    rating = Column(Integer, nullable=True)
    applied = Column(Boolean, nullable=True)
    interview_received = Column(Boolean, nullable=True)
    user_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
