# Interview MVP

智能体 + 数字人模拟面试平台（基于 LangGraph AI Agent）

## 技术栈

- 后端：FastAPI + SQLAlchemy + SQLite
- 前端：Vue 3 + Vite + Axios
- AI Agent：**LangGraph**（基于状态机的多轮对话系统）
- LLM：OpenAI GPT-4o（支持国内中转 API）
- 数字人：Edge TTS 语音合成 + Wav2Lip 唇形同步

## 核心特性

### AI Agent 架构（LangGraph）

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│introduction│────▶│ ask_question │────▶│ evaluate_answer │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    ▼                           ▼                           ▼
            ┌──────────┐               ┌──────────────┐             ┌───────────────┐
            │follow_up │               │ ask_question │             │generate_report│
            └──────────┘               └──────────────┘             └───────────────┘
                    │                       ▲
                    └───────────────────────┘
```

**节点说明：**
- `introduction`：开场 + 要求自我介绍
- `ask_question`：根据轮数生成不同类型问题（intro/behavioral/technical/situational）
- `evaluate_answer`：评估回答质量，决定是否追问
- `follow_up`：用 STAR 法则深挖细节
- `generate_report`：生成结构化反馈报告

**条件边路由：**
- 评估后：根据 should_follow_up 和 follow_up_count 决定路由
- 轮数达到上限 → generate_report
- 检测到结束关键词 → generate_report

## 快速启动

### 1. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入 API Key
```

`.env` 示例：
```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 或国内中转地址
LLM_MODEL=gpt-4o
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端

```bash
uvicorn app.main:app --reload --port 8000
```

后端运行后访问：http://localhost:8000/docs 查看 API 文档

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行后访问：http://localhost:3000

## MVP 功能

- [x] **LangGraph AI Agent**：基于状态机的面试流程控制
- [x] 岗位选择 + 简历上传
- [x] AI 面试官多轮对话（STAR 法则追问）
- [x] 消息历史记录
- [x] 面试结束生成反馈报告
- [x] 维度评分可视化

## 待集成

- [ ] Wav2Lip 数字人视频生成
- [ ] 语音输入（ASR）

## 项目结构

```
interview-mvp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── database.py           # 数据库配置
│   │   ├── models/               # 数据模型
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── routers/              # API 路由
│   │   └── services/
│   │       ├── interview_agent.py  # AI 面试官（外层接口）
│   │       ├── interview_graph.py  # LangGraph 工作流 ⭐
│   │       ├── llm_service.py     # LLM 调用
│   │       └── digital_human_service.py # 数字人
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.vue               # 主组件
│   │   └── api.js                # API 调用
│   └── package.json
└── README.md
```

## 简历撰写参考

### 项目描述

> **AI 模拟面试系统**
> - 基于 LangGraph 构建 AI Agent，实现状态机驱动的多轮面试对话流程
> - 支持多种问题类型（自我介绍/行为面试/技术面试/情景题）动态切换
> - 实现 STAR 法则追问机制，根据回答质量智能决定是否深挖细节
> - 面试结束自动生成结构化评估报告（整体评分 + 维度评分 + 优缺点分析）

### 技术亮点

1. **LangGraph 状态机**：用 StateGraph 定义面试流程，条件边实现动态路由
2. **多轮对话管理**：基于 conversation state 的上下文管理
3. **智能追问**：评估节点实时分析回答质量，决定是否 follow_up
4. **报告自动生成**：LLM 生成 JSON 格式结构化报告