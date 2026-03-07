from pydantic import BaseModel
from datetime import datetime


class ConversationCreate(BaseModel):
    title: str = "新对话"


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    tokens_used: int
