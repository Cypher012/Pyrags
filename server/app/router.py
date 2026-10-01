from fastapi import APIRouter

from app.chat.router import router as chat_router
from app.embeddings.router import router as embeddings_router
from app.health.router import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
