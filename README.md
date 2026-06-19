<div align="center">

# 🤖 AI 模拟面试官系统

### 基于 LangGraph + 数字人 + 多模态交互的智能面试平台

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square)](https://www.python.org)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg?style=flat-square)](https://vuejs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat-square)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**让 AI 不只是回答问题，而是真正成为面试官**

[🚀 快速开始](#-快速开始) · [✨ 核心特性](#-核心特性) · [🏗️ 架构](#-架构) · [📖 文档](#-文档)

</div>

---

## 📖 项目简介

**AI 模拟面试官系统** 是一个面向求职场景的智能面试模拟平台，覆盖 **简历解析 → 多轮面试对话 → 数字人播报 → 结构化反馈报告** 全链路。

针对传统求职练习的三大痛点：

| 痛点 | 解决方案 |
|------|---------|
| 缺少实战机会 | AI 模拟真实面试官，6 阶段递进式提问 |
| 回答得不到专业反馈 | 面试结束自动生成 4 维度评估报告 |
| 面试过程单调 | 数字人形象 + 语音播报，沉浸式体验 |

**核心能力**：

- 🎯 **LangGraph 多阶段状态机**：introduction → ask → evaluate → follow_up → report
- 📄 **简历解析**：自动解析 TXT / PDF / Word 三种格式
- 🎤 **数字人播报**：Edge-TTS + ffmpeg 静态图合成，可接入 Wav2Lip 真模型
- 🧠 **STAR 追问**：候选人回答模糊时自动用 STAR 法则追问细节
- 📊 **结构化报告**：整体评分 + 优缺点 + 4 维度（沟通/逻辑/专业/应变）评分
- 💾 **会话持久化**：SQLite 存储对话历史，支持服务重启恢复

---

## ✨ 核心特性

### 🎯 LangGraph 多阶段状态机

基于 LangGraph 设计的面试工作流：

```
introduction → ask_question → evaluate_answer
                                    │
                       ┌────────────┼────────────┐
                       ▼            ▼            ▼
                   follow_up    ask_question   generate_report
                       │            │            │
                       └────────────┘            │
                                    │            ▼
                                    └──→ evaluate_answer
                                                 │
                                                 ▼
                                              END
```

**4 类题型**：开场介绍 → 行为面试（STAR） → 技术考察 → 情景题 → 自由提问 → 结束

**追问机制**：当候选人回答模糊（"不知道" / < 10 字）时自动追问，最多 2 次

### 📄 简历智能解析

支持三种主流格式：

| 格式 | 解析库 | 用途 |
|------|--------|------|
| `.txt` | 原生 | 纯文本简历 |
| `.pdf` | `pypdf` | PDF 简历 |
| `.docx` | `python-docx` | Word 简历 |

解析后的简历文本作为 Prompt 喂给 LLM，实现"基于候选人背景的个性化提问"。

### 🗣️ 数字人播报

面试官回复自动触发 TTS 合成 + 数字人形象生成：

```
LLM 回复文本
   ↓
Edge-TTS 合成音频（zh-CN-XiaoxiaoNeural）
   ↓
ffmpeg 合成视频（静态头像 + 音频）
   ↓
返回 /static/audio/*.mp3 + /static/videos/*.mp4
```

**可扩展**：预留 Wav2Lip 接入点，安装后自动启用真模型生成。

### 📊 结构化反馈报告

面试结束自动生成 JSON 报告：

```json
{
  "overall_score": 7.5,
  "strengths": ["表达清晰有条理", "项目经验真实", "逻辑思维好"],
  "weaknesses": ["对底层原理了解不深", "回答可更具体"],
  "detailed_feedback": {
    "沟通能力": 8,
    "逻辑思维": 7,
    "专业技能": 7,
    "应变能力": 7
  }
}
```

### 🛡️ 容错设计

- ✅ LLM 调用失败时返回 Mock 数据（无 API Key 也能跑通）
- ✅ 简历解析失败给出明确错误提示
- ✅ 报告 JSON 解析多策略兜底（直接解析 / ```json``` 包裹 / 正则匹配）
- ✅ Agent 内存缓存 + DB 持久化，服务重启自动恢复

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────┐
│                用户浏览器                        │
│          Vue 3 + Vite (前端单页应用)              │
└────────────────────┬────────────────────────────┘
                     │ REST API + JSON
                     ▼
┌─────────────────────────────────────────────────┐
│             FastAPI 后端 (8000)                  │
│  ┌──────────────────────────────────────────┐  │
│  │  /api/interview/sessions    会话管理     │  │
│  │  /api/interview/{id}/start  开始面试     │  │
│  │  /api/interview/{id}/answer 提交回答     │  │
│  │  /api/interview/{id}/report 获取报告     │  │
│  │  /api/interview/audio/*     语音相关     │  │
│  │  /api/interview/video/*     数字人       │  │
│  └──────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
  │ LangGraph│ │  LLM     │ │ 简历解析  │ │ 数字人服务    │
  │ 状态机   │ │ OpenAI   │ │ pypdf    │ │ Edge-TTS     │
  │          │ │ 兼容协议 │ │ python-  │ │ + ffmpeg     │
  │ intro→ask│ │          │ │ docx     │ │ + (可选)     │
  │ →eval→   │ │          │ │          │ │   Wav2Lip    │
  │ follow→  │ │          │ │          │ │              │
  │ report   │ │          │ │          │ │              │
  └──────────┘ └──────────┘ └──────────┘ └──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   SQLite     │
              │ (会话历史)    │
              └──────────────┘
```

**核心模块**：

```
backend/app/
├── main.py                    # FastAPI 入口
├── database.py                # SQLAlchemy ORM
├── models/models.py           # Session / Message / Report
├── schemas/schemas.py         # Pydantic Schema
├── routers/interview.py       # ⭐ 12 个 API 路由
└── services/
    ├── llm_service.py         # OpenAI 兼容 LLM 封装
    ├── interview_graph.py     # ⭐ LangGraph 状态机
    ├── interview_agent.py     # Agent 包装 + DB 持久化
    ├── file_parser.py         # 简历解析
    └── digital_human_service.py  # TTS + ffmpeg 数字人
```

---

## 🚀 快速开始

### 📋 环境要求

- **Python** 3.11+
- **Node.js** 18+
- **ffmpeg**（数字人视频合成需要）
- **4GB+ RAM**

### 🔧 安装

```bash
# 1. 克隆仓库
git clone https://github.com/DetroySY/Interview-Agent.git
cd Interview-Agent

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 安装前端依赖
cd ../frontend
npm install
```

### ⚙️ 配置

```bash
cd backend
cp .env.example .env
```

编辑 `.env`：

```env
# 必填：OpenAI 兼容 API Key（也可以用国内中转）
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 可选：模型参数
TEMPERATURE=0.7
MAX_TOKENS=1000

# 数字人配置（可选）
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural
```

> 💡 **没有 API Key 也能跑**：LLM 服务内置 Mock 模式，所有接口会返回固定测试数据，方便前端联调。

### ▶️ 启动

#### 方式 A：分别启动（开发推荐）

```bash
# 终端 1：启动后端（http://localhost:8000）
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 终端 2：启动前端（http://localhost:5173）
cd frontend
npm run dev
```

打开浏览器访问 http://localhost:5173 即可体验。

#### 方式 B：Docker 一键启动

```bash
docker-compose up -d
# 前端：http://localhost:5173
# 后端：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 🧪 测试

```bash
# 后端接口测试（需要先启动服务）
cd backend
curl http://localhost:8000/health
```

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [API 文档](http://localhost:8000/docs) | FastAPI 自动生成的 Swagger |
| [Prompt 设计](prompt_summary.md) | 面试官 Prompt 工程详解 |
| [更新日志](CHANGELOG.md) | 版本变更记录 |
| [贡献指南](CONTRIBUTING.md) | 如何参与项目开发 |

---

## 🎬 使用示例

### Python 调用

```python
import requests

BASE = "http://localhost:8000/api/interview"

# 1. 创建会话（上传简历）
with open("resume.pdf", "rb") as f:
    resp = requests.post(
        f"{BASE}/sessions",
        data={"position": "前端开发", "user_id": "alice"},
        files={"resume_file": f},
    )
session = resp.json()
session_id = session["id"]

# 2. 开始面试
resp = requests.post(f"{BASE}/sessions/{session_id}/start")
print("面试官：", resp.json()["message"])

# 3. 多轮对话
while True:
    answer = input("候选人：")
    resp = requests.post(
        f"{BASE}/sessions/{session_id}/answer",
        params={"answer": answer},
    )
    data = resp.json()
    print("面试官：", data["message"])
    if data["is_end"]:
        break

# 4. 获取报告
report = requests.get(f"{BASE}/sessions/{session_id}/report").json()
print("综合评分：", report["overall_score"])
print("优点：", report["strengths"])
```

### HTTP 调用

```bash
# 创建会话
curl -X POST http://localhost:8000/api/interview/sessions \
  -F "user_id=alice" \
  -F "position=前端开发" \
  -F "resume_file=@resume.pdf"

# 提交回答
curl -X POST http://localhost:8000/api/interview/sessions/1/answer \
  -d "answer=我毕业于北华航天工业学院..."

# 获取报告
curl http://localhost:8000/api/interview/sessions/1/report
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + Axios |
| **后端** | FastAPI + Uvicorn + Pydantic |
| **数据库** | SQLAlchemy + SQLite |
| **多智能体** | LangGraph |
| **LLM** | OpenAI 兼容协议（GPT-4o / 通义千问等） |
| **简历解析** | pypdf + python-docx |
| **语音合成** | Edge-TTS |
| **视频合成** | ffmpeg（可扩展 Wav2Lip） |
| **语音识别** | OpenAI Whisper |

---

## 🗺️ Roadmap

- [x] **v0.1.0** - 核心 MVP（2026.06）
  - [x] LangGraph 6 阶段面试流
  - [x] 简历解析（TXT / PDF / Word）
  - [x] STAR 法则追问
  - [x] 数字人 TTS + ffmpeg 合成
  - [x] 结构化反馈报告
  - [x] 会话持久化
  - [x] Vue 3 极简前端

- [ ] **v0.2** - 体验增强（计划中）
  - [ ] Wav2Lip 真模型接入
  - [ ] 实时语音输入（流式 Whisper）
  - [ ] 面试录像回放
  - [ ] 多语言切换

- [ ] **v0.3** - 智能升级
  - [ ] 基于简历的个性化题库
  - [ ] 多 Agent 协作评分（专家委员会模式）
  - [ ] 行业知识图谱接入
  - [ ] 历史面试对比分析

- [ ] **v1.0** - 生产化
  - [ ] 用户系统 + 鉴权
  - [ ] 付费订阅 / 会员体系
  - [ ] 数据看板（学习曲线 / 进步轨迹）
  - [ ] 移动端 H5

---

## 🤝 贡献

欢迎贡献代码、报告 Bug、提出新功能建议！

- 🐛 [报告 Bug](https://github.com/DetroySY/Interview-Agent/issues/new?template=bug_report.md)
- 💡 [提出新功能](https://github.com/DetroySY/Interview-Agent/issues/new?template=feature_request.md)
- 🔧 [提交 PR](https://github.com/DetroySY/Interview-Agent/compare)

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📜 License

本项目基于 [MIT License](LICENSE) 开源。

---

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 多智能体编排框架
- [FastAPI](https://fastapi.tiangolo.com) - 高性能 Python Web 框架
- [Vue.js](https://vuejs.org) - 渐进式前端框架
- [Edge-TTS](https://github.com/rany2/edge-tts) - 免费语音合成
- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别

---

## 📮 联系方式

- GitHub: [@DetroySY](https://github.com/DetroySY)
- Email: 1628960433@qq.com
- Issues: [GitHub Issues](https://github.com/DetroySY/Interview-Agent/issues)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

Made with ❤️ by [DetroySY](https://github.com/DetroySY)

</div>