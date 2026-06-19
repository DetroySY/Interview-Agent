"""
AI 面试官 Agent - LangGraph 实现
基于状态机的多轮对话面试系统
"""
import json
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph import StateGraph, END
import operator


class InterviewState(TypedDict):
    """面试状态"""
    position: str                          # 面试岗位
    resume_text: str                       # 简历文本
    conversation: list[dict]               # 对话历史
    current_round: int                     # 当前轮数
    max_rounds: int                        # 最大轮数
    question_type: str                     # 当前问题类型
    should_follow_up: bool                # 是否需要追问
    follow_up_count: int                  # 连续追问次数
    score_candidates: list[float]          # 候选评分
    report: Optional[dict]                   # 最终报告
    last_question: str                     # 上一轮问题


def _build_system_prompt(position: str) -> str:
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


async def introduction(state: InterviewState, llm) -> InterviewState:
    """开场节点 - 发送开场白"""
    state["question_type"] = "intro"
    state["should_follow_up"] = False
    state["follow_up_count"] = 0

    messages = [
        {"role": "system", "content": _build_system_prompt(state["position"])},
        {"role": "user", "content": f"我的简历：\n{state['resume_text']}"},
    ]
    state["conversation"] = messages

    response = await llm.chat(messages)
    state["conversation"].append({"role": "assistant", "content": response})
    state["current_round"] = 1
    state["last_question"] = response

    return state


async def ask_question(state: InterviewState, llm) -> InterviewState:
    """提问节点 - 根据 question_type 生成问题"""
    messages = state["conversation"]

    # 根据轮数决定问题类型
    round_num = state["current_round"]

    if round_num == 1:
        # 第一轮：自我介绍
        state["question_type"] = "intro"
    elif round_num == 2:
        state["question_type"] = "behavioral"
    elif round_num == 3:
        state["question_type"] = "technical"
    elif round_num == 4:
        state["question_type"] = "situational"
    else:
        state["question_type"] = "follow_up"

    # 添加引导 prompt
    type_hints = {
        "intro": "请继续提问，但重点关注自我介绍中提到的经历进行深挖。",
        "behavioral": "请基于简历深挖一个具体项目经历，用STAR法则追问。**注意：如果候选人回答模糊或说不知道，必须追问细节，不能跳过。**",
        "technical": "请提出一个与岗位相关的技术问题。",
        "situational": "请提出一个情景问题，考察应变能力。",
    }

    # 检查上一轮回答是否需要追问（如果回答模糊或说不知道）
    last_answer = ""
    if len(state["conversation"]) >= 2:
        for msg in reversed(state["conversation"]):
            if msg["role"] == "interviewee" or msg["role"] == "user":
                last_answer = msg["content"].lower()
                break

    follow_up_trigger = ""
    if "不知道" in last_answer or len(last_answer) < 10:
        follow_up_trigger = "[重要] 候选人刚才说不知道或回答非常模糊，**必须追问**，请用 STAR 法则具体询问他负责了什么、具体做了什么、结果如何。不要换话题。"

    if state["current_round"] > 1:
        hint_msg = {
            "role": "user",
            "content": f"[面试官提示] 下一轮请问 {state['question_type']} 类型的问题。\n{type_hints.get(state['question_type'], '')}\n{follow_up_trigger}"
        }
        messages.append(hint_msg)

    response = await llm.chat(messages)
    state["conversation"].append({"role": "assistant", "content": response})
    state["current_round"] += 1
    state["last_question"] = response
    state["should_follow_up"] = False
    state["follow_up_count"] = 0

    return state


async def evaluate_answer(state: InterviewState, llm) -> InterviewState:
    """评估节点 - 评估回答质量，决定是否追问"""
    messages = state["conversation"]

    eval_prompt = {
        "role": "user",
        "content": """作为面试官助理，请评估候选人的回答：
1. 回答是否具体清晰？
2. 是否需要追问细节？
3. 是否可以进入下一话题？

请用 JSON 格式回答：
{"needs_follow_up": true/false, "reason": "原因", "suggestion": "追问建议"}"""
    }
    messages.append(eval_prompt)

    eval_response = await llm.chat(messages)

    # 解析评估结果
    try:
        # 尝试解析 JSON
        eval_data = json.loads(eval_response)
        state["should_follow_up"] = eval_data.get("needs_follow_up", False)
    except:
        # 解析失败，默认需要追问
        state["should_follow_up"] = True

    # 移除评估 prompt
    messages.pop()

    # 如果需要追问，增加 follow_up_count
    if state["should_follow_up"]:
        state["follow_up_count"] += 1

    return state


async def follow_up(state: InterviewState, llm) -> InterviewState:
    """追问节点 - 用 STAR 法则深挖细节"""
    messages = state["conversation"]

    follow_up_prompt = {
        "role": "user",
        "content": """请根据候选人刚才的回答，用 STAR 法则深挖细节：
- S (Situation): 当时的具体情境是什么？
- T (Task): 你负责的任务/角色是什么？
- A (Action): 你具体采取了什么行动？
- R (Result): 最终结果如何？有什么数据指标？

请问一个具体的追问问题。"""
    }
    messages.append(follow_up_prompt)

    response = await llm.chat(messages)
    state["conversation"].append({"role": "assistant", "content": response})
    state["last_question"] = response
    state["should_follow_up"] = False

    return state


async def generate_report(state: InterviewState, llm) -> InterviewState:
    """报告生成节点 - 生成结构化反馈报告"""
    messages = state["conversation"]

    report_prompt = {
        "role": "user",
        "content": """你是一位专业的面试评估师。请根据这场面试对话，生成结构化反馈报告。

要求：
1. 整体评分（1-10分，保留1位小数）
2. 优点列表（3-5条，每条20字以内）
3. 需要改进的地方（3-5条，每条20字以内）
4. 各维度评分（每项1-10分）：
   - 沟通能力
   - 逻辑思维
   - 专业技能
   - 应变能力

请直接输出 JSON 格式，不要任何其他内容：
{"overall_score": 7.5, "strengths": ["...", "..."], "weaknesses": ["...", "..."], "detailed_feedback": {"沟通能力": 8, "逻辑思维": 7, "专业技能": 7, "应变能力": 7}}"""
    }
    messages.append(report_prompt)

    report_text = await llm.chat(messages)

    # 移除报告 prompt，避免污染对话历史
    messages.pop()

    # 解析 JSON 报告
    state["report"] = _parse_report(report_text)

    return state


def _parse_report(report_text: str) -> dict:
    """解析 LLM 返回的报告文本"""
    import re

    default_report = {
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

    if not report_text:
        return default_report

    # 尝试提取 JSON
    try:
        return json.loads(report_text)
    except json.JSONDecodeError:
        pass

    try:
        # 提取 ```json ... ``` 包裹的内容
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", report_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        # 查找 {...} 模式（非贪婪，匹配到第一个合理的 JSON 对象）
        match = re.search(r"\{[\s\S]*?\}", report_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass

    print(f"无法解析报告 JSON，使用默认报告。原始内容: {report_text[:200]}")
    return default_report


def should_end_early(state: InterviewState) -> bool:
    """检查是否应该提前结束面试"""
    if state["current_round"] > 0:
        last_msg = state["conversation"][-1]["content"].lower() if state["conversation"] else ""
        end_keywords = ["面试结束", "结束面试", "感谢参与", "今天到此结束", "稍后你会收到", "反馈报告"]
        for keyword in end_keywords:
            if keyword in last_msg:
                return True
    return False


def create_interview_graph(llm):
    """创建面试工作流图"""

    # 定义条件边
    def conditional_route(state: InterviewState) -> str:
        """路由决策"""
        # 检查是否需要生成报告
        if should_end_early(state):
            return "generate_report"

        # 评估后路由
        if state.get("should_follow_up") and state.get("follow_up_count", 0) < 2:
            return "follow_up"

        if state["current_round"] >= state["max_rounds"]:
            return "generate_report"

        return "ask_question"

    # 构建图
    workflow = StateGraph(InterviewState)

    # 添加节点
    workflow.add_node("introduction", lambda state: introduction(state, llm))
    workflow.add_node("ask_question", lambda state: ask_question(state, llm))
    workflow.add_node("evaluate_answer", lambda state: evaluate_answer(state, llm))
    workflow.add_node("follow_up", lambda state: follow_up(state, llm))
    workflow.add_node("generate_report", lambda state: generate_report(state, llm))

    # 设置入口
    workflow.set_entry_point("introduction")

    # 添加边
    workflow.add_edge("introduction", "ask_question")
    workflow.add_edge("ask_question", "evaluate_answer")

    # 条件边：评估后路由
    workflow.add_conditional_edges(
        "evaluate_answer",
        conditional_route,
        {
            "follow_up": "follow_up",
            "ask_question": "ask_question",
            "generate_report": "generate_report",
        }
    )

    # 追问后回到评估
    workflow.add_edge("follow_up", "evaluate_answer")

    # 报告生成后结束
    workflow.add_edge("generate_report", END)

    return workflow.compile()


class InterviewGraph:
    """面试 Agent（基于 LangGraph）"""

    def __init__(self, llm):
        self.graph = create_interview_graph(llm)
        self.llm = llm

    async def ainvoke(self, state: InterviewState):
        """异步执行工作流"""
        return await self.graph.ainvoke(state)