from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    SendMessageRequest,
    MessageResponse,
    ChatResponse,
)
from app.schemas.common import Response

router = APIRouter()


@router.post(
    "/conversations",
    response_model=Response[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="新建会话",
)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    conv = service.create_conversation(current_user.id, data.title)
    return Response(data=ConversationResponse.model_validate(conv))


@router.get(
    "/conversations",
    response_model=Response[list[ConversationResponse]],
    summary="获取会话列表",
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    convs = service.list_conversations(current_user.id)
    return Response(data=[ConversationResponse.model_validate(c) for c in convs])


@router.delete(
    "/conversations/{conversation_id}",
    response_model=Response,
    summary="删除会话",
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    ok = service.delete_conversation(conversation_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return Response(message="删除成功")


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=Response[ChatResponse],
    summary="发送消息",
)
async def send_message(
    conversation_id: int,
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)

    # 验证会话归属
    conv = service.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    reply, tokens_used = await service.send_message(
        user_id=current_user.id,
        conversation_id=conversation_id,
        user_content=data.content,
    )
    return Response(
        data=ChatResponse(
            conversation_id=conversation_id,
            reply=reply,
            tokens_used=tokens_used,
        )
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=Response[list[MessageResponse]],
    summary="获取消息历史",
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)

    conv = service.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    messages = service.get_messages(conversation_id)
    return Response(data=[MessageResponse.model_validate(m) for m in messages])
