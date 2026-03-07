from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.logging import get_logger
from app.schemas.user import UserRegisterRequest

logger = get_logger(__name__)


class AuthService:

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def register(self, data: UserRegisterRequest) -> User:
        """
        注册新用户。
        调用前需确认 username 和 email 不重复。
        """
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("user_registered", user_id=user.id, username=user.username)
        return user

    def login(self, username: str, password: str) -> tuple[str, str] | None:
        """
        验证用户名密码，返回 (access_token, refresh_token)。
        验证失败返回 None。
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        logger.info("user_login", user_id=user.id, username=user.username)
        return access_token, refresh_token
