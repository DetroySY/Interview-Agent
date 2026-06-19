import json
import re
from typing import Optional, List
from app.services.llm_service import LLMService
from app.services.interview_graph import InterviewGraph, InterviewState


class InterviewAgent:
    """AI 面试官 Agent（内部基于 LangGraph 工作流）"""

    MAX_ROUNDS = 10
    END_KEYWORDS = ["面试结束", "结束面试", "感谢参与", "今天到此结束", "稍后你会收到", "反馈报告"]

    def __init__(self, session_id: int = None):
        self.llm = LLMService()
        self.session_id = session_id
        self.graph = InterviewGraph(self.llm)
        self.state: Optional[InterviewState] = None

    def load_history(self, history: list[dict], current_round: int, position: str = "", resume_text: str = ""):
        """从数据库加载对话历史"""
        if self.state is None:
            self.state = {
                "position": position,
                "resume_text": resume_text,
                "conversation": [],
                "current_round": 0,
                "max_rounds": self.MAX_ROUNDS,
                "question_type": "",
                "should_follow_up": False,
                "follow_up_count": 0,
                "score_candidates": [],
                "report": None,
                "last_question": "",
            }
        else:
            # 已存在状态时也更新 position 和 resume_text
            self.state["position"] = position or self.state.get("position", "")
            self.state["resume_text"] = resume_text or self.state.get("resume_text", "")
        self.state["conversation"] = history or []
        self.state["current_round"] = current_round or 0

    def get_history(self) -> list[dict]:
        return self.state["conversation"] if self.state else []

    def get_current_round(self) -> int:
        return self.state["current_round"] if self.state else 0

    async def start_interview(self, position: str, resume_text: str) -> str:
        """开始面试，返回开场白"""
        # 初始化状态
        self.state = {
            "position": position,
            "resume_text": resume_text,
            "conversation": [
                {"role": "system", "content": self._build_system_prompt(position)},
                {"role": "user", "content": f"我的简历：\n{resume_text}"},
            ],
            "current_round": 0,
            "max_rounds": self.MAX_ROUNDS,
            "question_type": "intro",
            "should_follow_up": False,
            "follow_up_count": 0,
            "score_candidates": [],
            "report": None,
            "last_question": "",
        }

        # 执行 introduction 节点
        from app.services.interview_graph import introduction
        self.state = await introduction(self.state, self.llm)

        # 返回开场白
        return self.state["last_question"]

    async def ask_question(self, user_answer: str) -> tuple[str, bool]:
        """
        用户回答后，追问下一个问题
        返回 (回复内容, 是否应该结束面试)
        """
        if self.state is None:
            raise ValueError("面试未开始，请先调用 start_interview")

        # 添加用户回答到对话历史
        self.state["conversation"].append({"role": "user", "content": user_answer})

        # 获取当前轮数
        current_round = self.state["current_round"]

        # 根据轮数决定问题类型
        if current_round == 1:
            self.state["question_type"] = "intro"
        elif current_round == 2:
            self.state["question_type"] = "behavioral"
        elif current_round == 3:
            self.state["question_type"] = "technical"
        elif current_round == 4:
            self.state["question_type"] = "situational"
        else:
            self.state["question_type"] = "follow_up"

        # 执行提问节点
        from app.services.interview_graph import ask_question
        self.state = await ask_question(self.state, self.llm)

        # 检查是否应该结束
        should_end = self._should_end_interview(self.state)

        return self.state["last_question"], should_end

    def _should_end_interview(self, state: InterviewState) -> bool:
        """判断面试是否应该结束"""
        if state["current_round"] >= state["max_rounds"]:
            return True

        last_msg = state["last_question"].lower() if state["last_question"] else ""
        for keyword in self.END_KEYWORDS:
            if keyword in last_msg:
                return True

        return False

    async def end_interview(self) -> dict:
        """结束面试，生成报告"""
        if self.state is None:
            raise ValueError("面试未开始")

        # 执行报告生成
        from app.services.interview_graph import generate_report
        self.state = await generate_report(self.state, self.llm)

        return self.state["report"] if self.state["report"] else self._default_report()

    def _default_report(self) -> dict:
        """默认报告（当报告生成失败时）"""
        return {
            "overall_score": 7.0,
            "strengths": ["表达较清晰", "有参与项目经验"],
            "weaknesses": ["需要更多实战锻炼", "部分回答可更具体"],
            "detailed_feedback": {
                "沟通能力": 7,
                "逻辑思维": 7,
                "专业技能": 6,
                "应变能力": 6,
            },
        }

    def _build_system_prompt(self, position: str) -> str:
        """构建面试官 system prompt"""
        return f"""你是一位专业面试官，面试岗位是 **{position}**。

## 回答格式要求
- **只输出纯文本，不要使用任何 Markdown 格式**（不要用 ###、**、- 等标记）
- 每条消息只问 1-2 个问题，简短自然，像真人对话

## 面试原则
1. 先让候选人自我介绍（1-2分钟）
2. 根据简历深挖经历，用 STAR 法则（情境-任务-行动-结果）追问
3. 考察岗位相关技能、专业知识和解决问题的能力
4. 注意倾听，适时追问细节
5. 保持专业、友好、鼓励的语气
6. **不接受"不知道"回答**：如果候选人说不知道，要追问"请回忆一下"或"能否说说大概的思路"

## 追问规则
- 当候选人回答模糊或说"不知道"时，**必须追问**，不能跳过
- 每次面试最多追问 2 次
- 追问用 STAR 法则：具体情境、你负责什么、具体行动、结果如何

## 结束语
面试结束时，说"今天的面试到此结束，感谢你的参与。稍后你会收到详细的反馈报告。"

请开始面试。"""