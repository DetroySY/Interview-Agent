from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    position = Column(String)  # 面试岗位
    resume_text = Column(Text)  # 简历文本
    status = Column(String, default="preparing")  # preparing | in_progress | completed
    conversation_history = Column(JSON, default=list)  # 持久化对话历史
    current_round = Column(Integer, default=0)  # 当前轮数
    max_rounds = Column(Integer, default=10)  # 最大轮数
    start_time = Column(DateTime, nullable=True)  # 面试开始时间
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("InterviewMessage", back_populates="session")
    report = relationship("InterviewReport", back_populates="session", uselist=False)


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    role = Column(String)  # interviewer | interviewee
    content = Column(Text)
    audio_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="messages")


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), unique=True)
    overall_score = Column(Float)
    strengths = Column(JSON)  # [str]
    weaknesses = Column(JSON)  # [str]
    detailed_feedback = Column(JSON)  # {维度: 分数}
    generated_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="report")