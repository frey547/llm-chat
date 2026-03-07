from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.schemas.common import Response
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/register",
    response_model=Response[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
def register(data: UserRegisterRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)

    if auth_service.get_user_by_username(data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )
    if auth_service.get_user_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册",
        )

    user = auth_service.register(data)
    return Response(data=UserResponse.model_validate(user))


@router.post(
    "/login",
    response_model=Response[TokenResponse],
    summary="用户登录",
)
def login(data: UserLoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    result = auth_service.login(data.username, data.password)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token, refresh_token = result
    return Response(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    )


@router.get(
    "/me",
    response_model=Response[UserResponse],
    summary="获取当前用户信息",
)
def get_me(current_user: User = Depends(get_current_user)):
    """需要 Bearer token 才能访问，验证 JWT 是否生效"""
    return Response(data=UserResponse.model_validate(current_user))
