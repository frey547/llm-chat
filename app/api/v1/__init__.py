from fastapi import APIRouter
from app.api.v1 import health, auth

router = APIRouter()
router.include_router(health.router, tags=["Infrastructure"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])

