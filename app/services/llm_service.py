import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    DeepSeek API 封装，兼容 OpenAI 格式。
    支持多轮对话，返回回复内容和 token 消耗。
    """

    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.deepseek_model

    async def chat(self, messages: list[dict]) -> tuple[str, int]:
        """
        发送多轮对话请求。
        messages 格式：[{"role": "user", "content": "..."}, ...]
        返回：(回复内容, 消耗token数)
        """
        if not self.api_key:
            logger.warning("llm_api_key_not_set")
            return self._mock_response(messages), 0

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)

            logger.info(
                "llm_request_success",
                model=self.model,
                tokens_used=tokens,
                messages_count=len(messages),
            )
            return content, tokens

        except httpx.TimeoutException:
            logger.error("llm_request_timeout")
            raise
        except httpx.HTTPStatusError as e:
            logger.error("llm_request_failed", status_code=e.response.status_code)
            raise
        except Exception as e:
            logger.error("llm_request_error", error=str(e))
            raise

    @staticmethod
    def _mock_response(messages: list[dict]) -> str:
        """
        未配置 API Key 时返回 mock 回复，方便本地开发测试。
        """
        last_msg = messages[-1]["content"] if messages else ""
        return f"[Mock 回复] 你说的是：{last_msg}"
