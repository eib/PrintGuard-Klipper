from fastapi import APIRouter

from .websocket import router as ws_router
from .push import router as push_router
from .auth import router as auth_router
from .printer_subscriptions import router as printer_sub_router
from .printers import router as printers_router
from .components import router as components_router
from .connections import router as connections_router
from .control import router as control_router
from .streams import router as streams_router

router = APIRouter()

router.include_router(ws_router)
router.include_router(push_router)
router.include_router(auth_router)
router.include_router(printer_sub_router)
router.include_router(printers_router)
router.include_router(components_router)
router.include_router(connections_router)
router.include_router(control_router)
router.include_router(streams_router)
