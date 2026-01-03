from fastapi import APIRouter

from .websocket import router as ws_router
from .push import router as push_router
from .auth import router as auth_router
from .printer_subscriptions import router as printer_sub_router

router = APIRouter()

router.include_router(ws_router)
router.include_router(push_router)
router.include_router(auth_router)
router.include_router(printer_sub_router)
