from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# --- Session ---
class InterviewSessionCreate(BaseModel):
    user_id: str
    position: str
    resume_text: str


class InterviewSessionResponse(BaseModel):
    id: int
    user_id: str
    position: str
    resume_text: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Message ---
class MessageCreate(BaseModel):
    session_id: int
    role: str
    content: str


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Report ---
class ReportResponse(BaseModel):
    id: int
    session_id: int
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    detailed_feedback: dict
    generated_at: datetime

    class Config:
        from_attributes = True
