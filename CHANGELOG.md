# 更新日志

本项目所有重要变更都会记录在此文件。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [Unreleased]

### 计划中
- Wav2Lip 真模型接入
- 实时流式语音输入
- 面试录像回放
- 多语言支持

## [0.1.0] - 2026-06-19

### ✨ 新增
- **LangGraph 多阶段面试工作流**：introduction → ask → evaluate → (follow_up | ask) → generate_report
- **6 阶段面试流程**：开场 → STAR 行为面试 → 技术考察 → 情景题 → 自由提问 → 结束
- **STAR 法则追问**：候选人回答模糊或 < 10 字时自动追问，最多 2 次
- **简历智能解析**：TXT / PDF (pypdf) / Word (python-docx) 三种格式
- **数字人播报服务**：Edge-TTS + ffmpeg 静态图合成，预留 Wav2Lip 接口
- **结构化反馈报告**：JSON 格式（overall_score + strengths/weaknesses + 4 维度评分）
- **LLM 兼容层**：支持 OpenAI 协议 + 国内中转 API，内置 Mock 兜底
- **会话持久化**：SQLite + SQLAlchemy 存储对话历史，支持服务重启恢复
- **12 个 API 路由**：RESTful 风格 + 静态文件服务
- **Vue 3 极简前端**：3 阶段切换（准备/面试/报告），干净设计语言
- **完整文档**：README + CHANGELOG + CONTRIBUTING + Issue/PR 模板

### 🐛 修复
- 报告 JSON 解析失败时回退到默认报告
- 简历文件扩展名推断（大小写、特殊字符）
- LLM 调用失败时返回友好提示而非 500

### 🎨 改进
- 前端 UI 大幅精简：从 974 行 App.vue 拆分为单一职责组件
- 移除冗余的 MediaRecorder 录音逻辑（保留为可扩展点）
- 移除复杂数字人视频/音频控制（保留 TTS 音频播放）
- 配色方案统一：主色 `#2563EB`，背景 `#F8FAFC`

### 📦 依赖
**后端**：
- `fastapi` ≥ 0.100
- `uvicorn[standard]` ≥ 0.23
- `sqlalchemy` ≥ 2.0
- `pydantic` ≥ 2.0
- `openai` ≥ 1.0
- `langgraph` ≥ 0.0.15
- `pypdf` / `python-docx`
- `edge-tts` ≥ 6.0
- `python-multipart`
- `Pillow`
- `openai-whisper`（可选）

**前端**：
- `vue` ^3.4
- `axios` ^1.6
- `vite` ^5.0

---

## [0.0.1] - 2026-05-15

### ✨ 新增
- 项目初始化
- FastAPI 基础框架
- 简单对话接口