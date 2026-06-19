# 贡献指南

感谢你愿意为 **AI 模拟面试官系统** 贡献代码 / 文档 / Issue！

## 🐛 报告 Bug

1. 搜索 [已有 Issues](https://github.com/DetroySY/Interview-Agent/issues) 避免重复
2. 使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.md)
3. 提供完整的复现步骤、环境信息、相关日志
4. **请勿在 Issue 中粘贴 API Key**

## 💡 提出新功能

1. 先开 Issue 讨论，确认方向后再写代码
2. 使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.md)
3. 说明动机、提案方案、对现有模块的影响

## 🔧 提交 PR

### 工作流

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-name>/Interview-Agent.git
cd Interview-Agent

# 2. 创建特性分支
git checkout -b feat/your-feature

# 3. 开发 + 测试
pip install -r backend/requirements.txt
cd frontend && npm install && npm run dev

# 4. 提交
git add .
git commit -m "feat: 描述你的改动"
git push origin feat/your-feature

# 5. 在 GitHub 上创建 PR
```

### 提交信息规范

参考 [Conventional Commits](https://www.conventionalcommits.org/)：

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加实时语音输入` |
| `fix` | Bug 修复 | `fix: 修复简历解析空指针` |
| `docs` | 文档 | `docs: 完善 README 部署章节` |
| `test` | 测试 | `test: 补充 LangGraph 状态机测试` |
| `refactor` | 重构 | `refactor: 拆分 LLM Service` |
| `chore` | 杂项 | `chore: 升级 fastapi 到 0.110` |
| `perf` | 性能 | `perf: 缓存 LLM 响应` |

### 代码规范

- **Python**: 遵循 PEP 8，关键路径添加类型注解
- **Vue**: Composition API + `<script setup>`
- **格式化**: 推荐 `black` (Python) + `prettier` (Vue)
- **文档**: 公开函数必须写 docstring

### PR 检查清单

- [ ] 后端接口已本地测试
- [ ] 前端 UI 在主流浏览器表现正常
- [ ] 文档（README / CHANGELOG）已更新
- [ ] 没有引入新的 linter 警告
- [ ] PR 描述清楚说明了变更动机和实现方式

## 🏗️ 项目结构

```
Interview-Agent/
├── backend/                # FastAPI 后端
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models/
│       ├── schemas/
│       ├── routers/
│       │   └── interview.py
│       └── services/
│           ├── llm_service.py
│           ├── interview_graph.py  # ⭐ LangGraph
│           ├── interview_agent.py
│           ├── file_parser.py
│           └── digital_human_service.py
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── App.vue
│       ├── main.js
│       └── api.js
├── docs/                   # 架构文档（待补充）
├── prompt_summary.md       # Prompt 设计
├── README.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## 📜 许可证

提交代码即表示你同意以 [MIT License](LICENSE) 发布你的贡献。