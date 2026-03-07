from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.message import Message, RoleEnum
from app.services.llm_service import LLMService
from app.services.cache_service import get_context, set_context
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatService:

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    # 会话管理

    def create_conversation(self, user_id: int, title: str = "新对话") -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        logger.info("conversation_created", user_id=user_id, conversation_id=conv.id)
        return conv

    def get_conversation(self, conversation_id: int, user_id: int) -> Conversation | None:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    def list_conversations(self, user_id: int) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .all()
        )

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    # 消息管理

    def get_messages(self, conversation_id: int) -> list[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    def _save_message(
        self,
        conversation_id: int,
        role: RoleEnum,
        content: str,
        tokens_used: int = 0,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    # 核心对话逻辑

    async def send_message(
        self,
        user_id: int,
        conversation_id: int,
        user_content: str,
    ) -> tuple[str, int]:
        """
        发送消息并获取 AI 回复。
        流程：
          1. 从 Redis 读取上下文缓存
          2. 追加用户消息
          3. 调用 LLM API
          4. 保存用户消息和 AI 回复到 MySQL
          5. 更新 Redis 上下文缓存
        """
        # 1. 从 Redis 读取上下文，没有则从 MySQL 重建
        context = await get_context(user_id, conversation_id)
        if not context:
            context = self._build_context_from_db(conversation_id)

        # 2. 追加用户消息到上下文
        context.append({"role": "user", "content": user_content})

        # 3. 调用 LLM
        reply_content, tokens_used = await self.llm.chat(context)

        # 4. 持久化到 MySQL
        self._save_message(conversation_id, RoleEnum.user, user_content)
        self._save_message(conversation_id, RoleEnum.assistant, reply_content, tokens_used)

        # 5. 更新 Redis 上下文（追加 AI 回复）
        context.append({"role": "assistant", "content": reply_content})
        await set_context(user_id, conversation_id, context)

        # 自动更新会话标题（取第一条用户消息的前20个字）
        self._auto_update_title(conversation_id, user_id, user_content)

        logger.info(
            "message_sent",
            user_id=user_id,
            conversation_id=conversation_id,
            tokens_used=tokens_used,
        )
        return reply_content, tokens_used

    def _build_context_from_db(self, conversation_id: int) -> list[dict]:
        """Redis 缓存未命中时，从 MySQL 重建最近10条上下文"""
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(10)
            .all()
        )
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in reversed(messages)
        ]

    def _auto_update_title(
        self, conversation_id: int, user_id: int, first_content: str
    ) -> None:
        """会话只有一条消息时，自动用内容前20字作为标题"""
        conv = self.get_conversation(conversation_id, user_id)
        if conv and conv.title == "新对话":
            conv.title = first_content[:20]
            self.db.commit()
