from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import interview_router

# 创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview MVP API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(interview_router)

# 静态文件服务（音频、视频、头像）
import os
os.makedirs("static/audio", exist_ok=True)
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/avatars", exist_ok=True)
app.mount("/static/audio", StaticFiles(directory="static/audio"), name="audio")
app.mount("/static/videos", StaticFiles(directory="static/videos"), name="videos")
app.mount("/static/avatars", StaticFiles(directory="static/avatars"), name="avatars")


@app.get("/")
async def root():
    return {"message": "Interview MVP API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
