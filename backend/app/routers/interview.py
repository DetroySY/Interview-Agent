from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os

from app.database import get_db
from app.models.models import InterviewSession, InterviewMessage, InterviewReport
from app.schemas.schemas import (
    InterviewSessionCreate,
    InterviewSessionResponse,
    MessageResponse,
    ReportResponse,
)
from app.services.interview_agent import InterviewAgent
from app.services.digital_human_service import DigitalHumanService
from app.services.file_parser import save_upload_file, parse_resume

router = APIRouter(prefix="/api/interview", tags=["interview"])

# 存储活跃的 agent 实例（仅用于性能优化，服务重启后从 DB 恢复）
active_agents: dict[int, InterviewAgent] = {}


def get_or_create_agent(session: InterviewSession) -> InterviewAgent:
    """获取或创建 Agent（从 DB 恢复状态）"""
    session_id = session.id

    if session_id in active_agents:
        return active_agents[session_id]

    agent = InterviewAgent(session_id=session_id)
    # 从数据库恢复对话历史（同时恢复 position 和 resume_text）
    agent.load_history(
        history=session.conversation_history or [],
        current_round=session.current_round or 0,
        position=session.position or "",
        resume_text=session.resume_text or "",
    )
    active_agents[session_id] = agent
    return agent


@router.post("/sessions", response_model=InterviewSessionResponse)
async def create_session(
    user_id: str = Form(default="anonymous"),
    position: str = Form(...),
    resume_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """创建面试会话（支持简历文件上传）"""
    # 保存并解析简历
    file_path, file_ext = await save_upload_file(resume_file)
    resume_text = parse_resume(file_path, file_ext)

    if not resume_text or "不支持" in resume_text or "库未安装" in resume_text:
        raise HTTPException(status_code=400, detail=resume_text)

    session = InterviewSession(
        user_id=user_id,
        position=position,
        resume_text=resume_text,
        status="preparing",
        conversation_history=[],
        current_round=0,
        max_rounds=10,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/sessions/{session_id}/start")
async def start_interview(session_id: int, db: Session = Depends(get_db)):
    """开始面试"""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "in_progress":
        # 已经开始了，直接返回现有状态
        agent = get_or_create_agent(session)
        messages = db.query(InterviewMessage).filter(
            InterviewMessage.session_id == session_id
        ).order_by(InterviewMessage.timestamp).all()

        last_msg = messages[-1].content if messages else ""
        return {"message": last_msg, "status": "in_progress"}

    agent = InterviewAgent(session_id=session_id)
    greeting = await agent.start_interview(session.position, session.resume_text)

    # 保存开场白
    msg = InterviewMessage(
        session_id=session_id,
        role="interviewer",
        content=greeting,
    )
    db.add(msg)

    # 更新会话状态
    session.status = "in_progress"
    session.start_time = datetime.utcnow()
    session.conversation_history = agent.get_history()
    session.current_round = agent.get_current_round()

    db.commit()

    # 存储 agent
    active_agents[session_id] = agent

    return {"message": greeting}


@router.post("/sessions/{session_id}/answer")
async def submit_answer(session_id: int, answer: str, db: Session = Depends(get_db)):
    """用户提交回答"""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    # 保存用户回答
    user_msg = InterviewMessage(
        session_id=session_id,
        role="interviewee",
        content=answer,
    )
    db.add(user_msg)
    db.commit()

    # 获取 agent（从 DB 恢复或从内存获取）
    agent = get_or_create_agent(session)

    # 获取回复，第二个返回值表示是否应结束
    response, should_end = await agent.ask_question(answer)

    # 保存面试官回复
    interviewer_msg = InterviewMessage(
        session_id=session_id,
        role="interviewer",
        content=response,
    )
    db.add(interviewer_msg)

    # 更新会话状态
    session.conversation_history = agent.get_history()
    session.current_round = agent.get_current_round()

    if should_end:
        session.status = "completed"
        report_data = await agent.end_interview()
        report = InterviewReport(
            session_id=session_id,
            **report_data,
        )
        db.add(report)

    db.commit()

    return {"message": response, "is_end": should_end}


@router.post("/sessions/{session_id}/end")
async def end_interview(session_id: int, db: Session = Depends(get_db)):
    """主动结束面试"""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "completed":
        agent = get_or_create_agent(session)
        report_data = await agent.end_interview()
        report = InterviewReport(
            session_id=session_id,
            **report_data,
        )
        db.add(report)
        session.status = "completed"
        db.commit()

    return {"message": "面试已结束"}


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(session_id: int, db: Session = Depends(get_db)):
    """获取会话消息列表"""
    messages = (
        db.query(InterviewMessage)
        .filter(InterviewMessage.session_id == session_id)
        .order_by(InterviewMessage.timestamp)
        .all()
    )
    return messages


@router.get("/sessions/{session_id}/report", response_model=ReportResponse)
async def get_report(session_id: int, db: Session = Depends(get_db)):
    """获取面试报告"""
    report = (
        db.query(InterviewReport)
        .filter(InterviewReport.session_id == session_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: int, db: Session = Depends(get_db)):
    """获取面试状态（轮数、时长等）"""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 计算时长
    duration = None
    if session.start_time:
        duration = (datetime.utcnow() - session.start_time).total_seconds()

    return {
        "status": session.status,
        "current_round": session.current_round or 0,
        "max_rounds": session.max_rounds or 10,
        "duration": duration,
    }


# --- 历史会话 ---
@router.get("/sessions")
async def get_sessions(user_id: str = None, db: Session = Depends(get_db)):
    """获取用户的历史面试会话列表"""
    query = db.query(InterviewSession)
    if user_id:
        query = query.filter(InterviewSession.user_id == user_id)
    sessions = query.order_by(InterviewSession.created_at.desc()).limit(20).all()
    return sessions


# --- 数字人相关 ---
@router.post("/video/generate")
async def generate_video(text: str, avatar: Optional[str] = "default"):
    """生成数字人播报视频"""
    dh_service = DigitalHumanService()
    video_path = await dh_service.generate_video(text, avatar)
    return {"video_url": video_path}


@router.get("/audio/generate")
async def generate_audio(text: str):
    """生成 TTS 音频"""
    dh_service = DigitalHumanService()
    audio_path = await dh_service.generate_audio_only(text)
    if audio_path and os.path.exists(audio_path):
        return {"audio_url": f"/static/audio/{os.path.basename(audio_path)}"}
    return {"audio_url": ""}


@router.post("/avatar/upload")
async def upload_avatar(file: UploadFile = File(...)):
    """上传自定义 Avatar 图片"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片格式")

    dh_service = DigitalHumanService()
    content = await file.read()
    avatar_id = await dh_service.upload_avatar(content, file.filename)

    return {"avatar_id": avatar_id, "avatar_url": f"/static/avatars/{avatar_id}.png"}


# --- 语音识别 STT（Whisper 模型缓存）---
_whisper_model = None

def _get_whisper_model():
    """全局缓存 Whisper 模型，避免每次请求重新加载"""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model


@router.post("/audio/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """上传音频文件，使用 Whisper 转写为文本"""
    import tempfile
    import os as _os

    suffix = _os.path.splitext(file.filename)[1] if file.filename else ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        model = _get_whisper_model()
        result = model.transcribe(tmp_path, language="zh")
        return {"text": result["text"].strip()}
    finally:
        if _os.path.exists(tmp_path):
            _os.remove(tmp_path)