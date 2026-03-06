from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """统一响应体，所有接口都用这个包装"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
