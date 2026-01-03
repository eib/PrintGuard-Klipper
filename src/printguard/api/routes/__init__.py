from fastapi import APIRouter

from .websocket import router as ws_router
from .push import router as push_router

router = APIRouter()

router.include_router(ws_router)
router.include_router(push_router)
