import os
import json
from openai import AsyncOpenAI


class LLMService:
    """LLM 服务 - 支持 OpenAI 兼容 API"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

        # 支持国内中转 API
        if self.api_key and self.base_url != "https://api.openai.com/v1":
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        elif self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """发送对话请求到 LLM"""
        if not self.client:
            return self._mock_response(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return f"抱歉，服务暂时不可用。请稍后重试。"

    def _mock_response(self, messages: list[dict]) -> str:
        """Mock 回复（未配置 API Key 时）"""
        last_msg = messages[-1]["content"] if messages else ""

        if "简历" in last_msg:
            return "你好！请先做一个简短的自我介绍吧，重点说说你的教育背景和最近的工作经历。"
        elif "面试结束" in last_msg or "JSON" in last_msg:
            return json.dumps({
                "overall_score": 7.5,
                "strengths": ["表达清晰有条理", "有实际项目经验", "逻辑思维较好"],
                "weaknesses": ["对底层原理了解不够深入", "有些回答过于笼统", "需要多练习STAR法则"],
                "detailed_feedback": {
                    "沟通能力": 8,
                    "逻辑思维": 7,
                    "专业技能": 7,
                    "应变能力": 7
                }
            })
        else:
            return "这个问题问得很好。请你结合具体案例说说你是如何解决这类问题的？"

    def build_system_prompt(self, position: str) -> str:
        """构建面试官 system prompt"""
        return f"""你是一位专业面试官，面试岗位是 **{position}**。

## 面试原则
1. 先让候选人自我介绍（1-2分钟）
2. 根据简历深挖经历，用 STAR 法则（情境-任务-行动-结果）追问
3. 考察岗位相关技能、专业知识和解决问题的能力
4. 每轮提问不超过 2 个问题，保持对话节奏
5. 注意倾听，适时追问细节
6. 保持专业、友好、鼓励的语气

## 面试流程
1. 开场介绍 + 要求自我介绍
2. 深挖简历中的项目/经历
3. 考察专业技能和知识
4. 行为面试题（应变、团队协作等）
5. 候选人提问环节
6. 感谢并告知后续流程

## 结束语
面试结束时，说"今天的面试到此结束，感谢你的参与。稍后你会收到详细的反馈报告。"

请开始面试。"""
