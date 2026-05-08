from pydantic import BaseModel, EmailStr
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None
class PublicAnalyzeResponse(BaseModel):
    final_score: float
    summary: str
    report_markdown: str
    structured_report: dict | None = None
class SaveAnalysisRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    final_score: float
    report_markdown: str
    structured_report: dict | None = None
    resume_text: str | None = None
    job_description: str | None = None
    
class SavedAnalysisResponse(BaseModel):
    id: int
    title: str | None = None
    company: str | None = None
    final_score: float
    report_markdown: str
    sort_order: int | None = 0
    
class FeedbackRequest(BaseModel):
    match_analysis_id: int | None = None
    rating: int | None = None
    applied: bool | None = None
    interview_received: bool | None = None
    user_notes: str | None = None

class UpdateAnalysisRequest(BaseModel):
    title: str | None = None
    company: str | None = None

class ReorderAnalysisRequest(BaseModel):
    ordered_ids: list[int]
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str    