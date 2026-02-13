"""Guest agent — personality-driven discussion contributor."""

from __future__ import annotations

import json
import logging

from backend.agents.base import BaseAgent
from backend.agents.personas import build_system_prompt
from backend.models import DialogueLine, PersonaConfig
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class GuestAgent(BaseAgent):
    """A podcast guest with a distinct MBTI personality and expertise."""

    def __init__(self, persona: PersonaConfig, llm_service: LLMService) -> None:
        super().__init__(
            name=persona.name,
            system_prompt=build_system_prompt(persona, is_host=False),
            llm_service=llm_service,
        )
        self.persona = persona

    # ------------------------------------------------------------------
    # Line generation
    # ------------------------------------------------------------------

    async def generate_line(
        self,
        context: list[dict[str, str]],
        instruction: str,
    ) -> DialogueLine:
        """Generate a single guest line within the podcast conversation.

        *context* is the shared conversation history visible to all agents.
        *instruction* tells the guest what to respond to / focus on.
        """
        prompt = f"""【嘉宾发言指令】{instruction}

请生成你（{self.name}，{self.persona.mbti}，{self.persona.occupation}）在这个位置的发言。

要求：
- 一段自然的口语化发言，50-200字左右
- 体现你{self.persona.mbti}的性格内核和{self.persona.occupation}的独特视角
- 像在朋友聚会上分享自己真实想法那样说话：可以犹豫、可以激动、可以吐槽
- 给出有深度的洞见——不是泛泛而谈，而是基于你的专业经验和个人判断
- 遇到复杂概念用类比拆解："这就好比……"；引用你经历过的具体案例
- 可以大胆反驳前面的观点——"我倒不这么看"、"这里面有个问题被忽略了"
- 按照语音标注规则自然地加入停顿标记 `<#X#>` 和语气词标签

严禁出现：
- "非常好的问题"、"正如你所说"之类的谄媚语
- "此外"、"值得注意的是"、"综上所述"等AI痕迹词
- "不仅……而且……"、"一方面……另一方面……"等公式结构
- 三段式排列（除非你是赵明远且在做技术拆解）
- "赋能"、"打造"、"引领"等宣传体

请以JSON格式返回（不要包含markdown代码块标记）：
{{
    "text": "用于展示的纯净文本（不含标注）",
    "ssml_text": "带语音标注的文本（含 <#X#> 停顿和情感语气词）",
    "emotion": "当前情感状态（如 happy, neutral, excited, thoughtful, skeptical）"
}}"""

        response = await self.think(prompt, conversation_history=context, temperature=0.85, max_tokens=800)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            return DialogueLine(
                speaker=self.name,
                text=data.get("text", ""),
                ssml_text=data.get("ssml_text", data.get("text", "")),
                emotion=data.get("emotion", "neutral"),
                voice_id=self.persona.voice_id,
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.error("Failed to parse guest line from %s: %s",
                         self.name, exc)
            return DialogueLine(
                speaker=self.name,
                text=response,
                ssml_text=response,
                emotion="neutral",
                voice_id=self.persona.voice_id,
            )
